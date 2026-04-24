import os
import discord
from discord import Embed, ui, app_commands
from discord.ext import commands
import yt_dlp
import asyncio
from database import add_discord_user, subscribe_discord_anime, unsubscribe_discord_anime, get_discord_user_subscriptions, set_user_persona, get_user_persona, add_user_interest, remove_user_interest, get_user_interests
from api import search_anime, get_today_schedule, get_anime_by_id, get_random_anime, search_character, get_top_anime
from ai import get_ai_response, translate_batch, generate_quiz, PERSONAS
import requests
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
# Cấu hình YouTube DL & FFmpeg
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

bot = commands.Bot(command_prefix='!', intents=intents)

class AnimeSearchView(ui.View):
    def __init__(self, anime_id, title, airing_day, airing_time, trailer_url=None):
        super().__init__(timeout=None)
        self.anime_id = anime_id
        self.title = title
        self.airing_day = airing_day
        self.airing_time = airing_time
        
        if trailer_url:
            self.add_item(ui.Button(label="📺 Xem Trailer", url=trailer_url))

    @ui.button(label="✅ Đăng ký theo dõi", style=discord.ButtonStyle.green)
    async def subscribe(self, interaction: discord.Interaction, button: ui.Button):
        add_discord_user(interaction.user.id, interaction.user.name)
        is_new = subscribe_discord_anime(interaction.user.id, self.anime_id, self.title, self.airing_day, self.airing_time)
        
        if is_new:
            await interaction.response.send_message(f"✅ Đã đăng ký theo dõi **{self.title}** thành công!", ephemeral=True)
        else:
            await interaction.response.send_message(f"ℹ️ Bạn đã đăng ký phim **{self.title}** rồi nhé!", ephemeral=True)

class UnsubscribeView(ui.View):
    def __init__(self, anime_id, title):
        super().__init__(timeout=None)
        self.anime_id = anime_id
        self.title = title

    @ui.button(label="❌ Hủy theo dõi", style=discord.ButtonStyle.red)
    async def unsubscribe(self, interaction: discord.Interaction, button: ui.Button):
        unsubscribe_discord_anime(interaction.user.id, self.anime_id)
        await interaction.response.send_message(f"❌ Đã hủy theo dõi **{self.title}** thành công!", ephemeral=True)
        # Optionally delete or update the message
        await interaction.message.delete()

class QuizView(ui.View):
    def __init__(self, quiz_data):
        super().__init__(timeout=60) # Câu hỏi có hiệu lực trong 60 giây
        self.quiz_data = quiz_data
        self.correct_index = quiz_data['correct_index']
        
    async def check_answer(self, interaction: discord.Interaction, index: int):
        # Vô hiệu hóa tất cả các nút sau khi trả lời
        for child in self.children:
            child.disabled = True
        
        if index == self.correct_index:
            color = discord.Color.green()
            result_text = "✅ **CHÍNH XÁC!** Bạn giỏi quá đi!"
        else:
            correct_label = chr(65 + self.correct_index)
            color = discord.Color.red()
            result_text = f"❌ **SAI RỒI!** Đáp án đúng phải là **{correct_label}** mới đúng."
            
        embed = Embed(
            title="🧠 KẾT QUẢ CÂU ĐỐ",
            description=f"{result_text}\n\n💡 **Giải thích:** {self.quiz_data['explanation']}",
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="A", style=discord.ButtonStyle.blurple)
    async def opt_a(self, interaction: discord.Interaction, button: ui.Button):
        await self.check_answer(interaction, 0)

    @ui.button(label="B", style=discord.ButtonStyle.blurple)
    async def opt_b(self, interaction: discord.Interaction, button: ui.Button):
        await self.check_answer(interaction, 1)

    @ui.button(label="C", style=discord.ButtonStyle.blurple)
    async def opt_c(self, interaction: discord.Interaction, button: ui.Button):
        await self.check_answer(interaction, 2)

    @ui.button(label="D", style=discord.ButtonStyle.blurple)
    async def opt_d(self, interaction: discord.Interaction, button: ui.Button):
        await self.check_answer(interaction, 3)

@bot.event
async def on_ready():
    print(f'Discord Bot logged in as {bot.user}')
    # Đồng bộ Slash Commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
    # Khởi động hệ thống nhắc lịch khi bot đã sẵn sàng
    from main import discord_reminders_task
    bot.loop.create_task(discord_reminders_task())

@bot.tree.command(name="start", description="Khởi động bot và xem hướng dẫn")
async def start(interaction: discord.Interaction):
    embed = Embed(
        title="Chào mừng bạn đến với Bot Thông Báo Anime!",
        description=(
            "Các lệnh mình có:\n"
            "`/today` - Xem lịch chiếu hôm nay\n"
            "`/search <tên>` - Tìm phim để đăng ký nhận thông báo\n"
            "`/mylist` - Xem danh sách phim đã đăng ký\n"
            "`/gacha` - Tìm siêu phẩm ngẫu nhiên để cày\n"
            "`/quiz` - Thử thách kiến thức Anime\n"
            "`/top` - Xem Top 10 anime hot nhất hiện nay\n"
            "`/char <tên>` - Tìm thông tin nhân vật\n\n"
            "💡 **Mẹo:** Gửi một tấm ảnh anime cho tớ để tìm tên phim nhé!\n"
            "Hoặc bạn cứ chat bình thường để tán gẫu với mình!"
        ),
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="search", description="Tìm kiếm anime theo tên")
async def search(interaction: discord.Interaction, query: str):
    await interaction.response.defer() # Cần defer vì API Jikan đôi khi chậm
    results = search_anime(query)
    if not results:
        await interaction.followup.send("Không tìm thấy anime nào với tên đó.")
        return
    
    for item in results[:5]:  # Giới hạn 5 kết quả đầu tiên
        score_text = f"⭐ {item['score']}/10" if item['score'] != 'N/A' else "⭐ Chưa có điểm"
        
        embed = Embed(
            title=item['title'],
            description=f"{score_text}\nLịch chiếu: {item['airing_day']} lúc {item['airing_time']}",
            color=discord.Color.green()
        )
        if item.get('image'):
            embed.set_thumbnail(url=item['image'])
            
        view = AnimeSearchView(item['id'], item['title'], item['airing_day'], item['airing_time'], item.get('trailer_url'))
        await interaction.followup.send(embed=embed, view=view)

@bot.tree.command(name="today", description="Xem lịch chiếu anime hôm nay")
async def today(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Đang lấy và dịch lịch chiếu hôm nay...")
    schedule = get_today_schedule()
    if not schedule:
        await interaction.edit_original_response(content="Hôm nay không có lịch chiếu nào hoặc lỗi kết nối.")
        return
    
    today_list = schedule[:8]
    english_synopses = [item.get('synopsis') or "No description." for item in today_list]
    vietnamese_synopses = await translate_batch(english_synopses)
    
    # Xóa thông báo chờ
    await interaction.delete_original_response()
    
    for i, item in enumerate(today_list):
        synopsis_vn = vietnamese_synopses[i] if i < len(vietnamese_synopses) else "Không có mô tả."
        embed = Embed(
            title=item['title'],
            description=f"⏰ Giờ chiếu: {item['time']}\n\n📝 {synopsis_vn}",
            color=discord.Color.orange()
        )
        if item.get('image'):
            embed.set_image(url=item['image'])
        await interaction.channel.send(embed=embed)

@bot.tree.command(name="mylist", description="Xem danh sách phim đã đăng ký")
async def mylist(interaction: discord.Interaction):
    subs = get_discord_user_subscriptions(interaction.user.id)
    if not subs:
        await interaction.response.send_message("Bạn chưa đăng ký theo dõi anime nào cả. Hãy dùng `/search` để tìm phim nhé!")
        return

    await interaction.response.send_message(f"📋 **Danh sách anime bạn đã đăng ký ({len(subs)}):**")
    for sub in subs:
        embed = Embed(
            title=sub['anime_title'],
            description=f"Lịch chiếu: {sub['airing_day']} lúc {sub['airing_time']}",
            color=discord.Color.blue()
        )
        view = UnsubscribeView(sub['anime_id'], sub['anime_title'])
        await interaction.channel.send(embed=embed, view=view)

@bot.tree.command(name="gacha", description="Tìm siêu phẩm ngẫu nhiên để cày")
async def gacha(interaction: discord.Interaction):
    await interaction.response.send_message("🎲 Đang quay gacha tìm siêu phẩm cho bạn...")
    item = get_random_anime()
    if not item:
        await interaction.edit_original_response(content="Máy gacha đang bị kẹt, thử lại sau nhé!")
        return
        
    score_text = f"⭐ {item['score']}/10" if item['score'] != 'N/A' else "⭐ Chưa có điểm"
    embed = Embed(
        title=f"🎲 SIÊU PHẨM GACHA CỦA BẠN LÀ: {item['title']}",
        description=(
            f"{score_text} | Thể loại: {item['genres']}\n"
            f"Số tập: {item['episodes']}\n\n"
            f"*{item['synopsis']}*"
        ),
        color=discord.Color.gold()
    )
    if item.get('image'):
        embed.set_image(url=item['image'])
    view = AnimeSearchView(item['id'], item['title'], item['airing_day'], item['airing_time'], item.get('trailer_url'))
    await interaction.edit_original_response(content=None, embed=embed, view=view)

@bot.tree.command(name="quiz", description="Thử thách kiến thức Anime")
async def quiz(interaction: discord.Interaction):
    await interaction.response.send_message("🧠 Đang vắt óc nghĩ ra một câu đố anime siêu hóc búa cho bạn đây...")
    quiz_data = await generate_quiz()
    if not quiz_data:
        await interaction.edit_original_response(content="AI đang mệt, không nghĩ ra câu hỏi nào. Bạn thử lại sau nhé!")
        return
        
    options_text = "\n".join([f"**{chr(65+i)}.** {opt}" for i, opt in enumerate(quiz_data['options'])])
    embed = Embed(
        title="🧠 THỬ THÁCH KIẾN THỨC ANIME",
        description=f"### {quiz_data['question']}\n\n{options_text}\n\n*Hãy chọn đáp án đúng bên dưới!*",
        color=discord.Color.purple()
    )
    view = QuizView(quiz_data)
    await interaction.edit_original_response(content=None, embed=embed, view=view)

@bot.tree.command(name="char", description="Tìm thông tin nhân vật anime")
async def char(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(f"⏳ Đang tìm thông tin nhân vật `{name}`...")
    char_data = search_character(name)
    if not char_data:
        await interaction.edit_original_response(content="Hic, tớ không tìm thấy nhân vật nào tên này cả.")
        return
        
    about_vn = await get_ai_response(f"Hãy tóm tắt ngắn gọn (khoảng 100 từ) thông tin nhân vật này bằng tiếng Việt: {char_data['about']}")
    embed = Embed(
        title=f"👤 NHÂN VẬT: {char_data['name']}",
        description=f"{about_vn}\n\n🔗 [Xem thêm trên MyAnimeList]({char_data['url']})",
        color=discord.Color.light_grey()
    )
    if char_data['image']:
        embed.set_image(url=char_data['image'])
    await interaction.edit_original_response(content=None, embed=embed)

@bot.tree.command(name="top", description="Xem Top 10 anime hot nhất mùa này")
async def top(interaction: discord.Interaction):
    await interaction.response.send_message("🔥 Đang lấy danh sách Top 10 Anime hot nhất mùa này...")
    top_list = get_top_anime()
    if not top_list:
        await interaction.edit_original_response(content="Không lấy được danh sách Top. Thử lại sau nhé!")
        return
        
    description = ""
    for i, item in enumerate(top_list, 1):
        description += f"{i}. **{item['title']}** - ⭐ {item['score']}\n   `/search {item['id']}`\n\n"
    
    embed = Embed(
        title="🏆 TOP 10 ANIME HOT NHẤT HIỆN NAY",
        description=description,
        color=discord.Color.dark_red()
    )
    await interaction.edit_original_response(content=None, embed=embed)

@bot.tree.command(name="persona", description="Thay đổi nhân cách cho trợ lý")
async def persona(interaction: discord.Interaction, name: str = None):
    available = ", ".join(f"`{p}`" for p in PERSONAS.keys())
    if not name:
        current = get_user_persona(interaction.user.id, 'discord')
        await interaction.response.send_message(f"🎭 Nhân cách hiện tại của tớ là: `{current}`\nCác nhân cách có sẵn: {available}\nDùng `/persona <tên>` để đổi nhé!")
        return
    
    name = name.lower()
    if name in PERSONAS:
        set_user_persona(interaction.user.id, 'discord', name)
        await interaction.response.send_message(f"✅ Đã đổi nhân cách sang: `{name}`. Từ giờ tớ sẽ nói chuyện kiểu này nhé!")
    else:
        await interaction.response.send_message(f"❌ Không tìm thấy nhân cách đó. Hãy chọn: {available}")

@bot.tree.command(name="follow", description="Theo dõi tin tức về một chủ đề")
async def follow(interaction: discord.Interaction, topic: str = None):
    if not topic:
        interests = get_user_interests(interaction.user.id, 'discord')
        if not interests:
            await interaction.response.send_message("Bạn chưa theo dõi chủ đề nào. Dùng `/follow <tên chủ đề>` nhé!")
        else:
            list_text = "\n".join([f"• {i['topic_name']} ({i['topic_type']})" for i in interests])
            await interaction.response.send_message(f"🔔 **Các chủ đề bạn đang theo dõi:**\n{list_text}")
        return
    
    add_user_interest(interaction.user.id, 'discord', 'general', topic)
    await interaction.response.send_message(f"✅ Đã thêm **{topic}** vào danh sách theo dõi của bạn!")

@bot.tree.command(name="artist", description="Theo dõi tin tức về một ca sĩ/nghệ sĩ")
async def artist(interaction: discord.Interaction, name: str):
    add_user_interest(interaction.user.id, 'discord', 'artist', name)
    await interaction.response.send_message(f"✅ Đã thêm ca sĩ **{name}** vào danh sách theo dõi của bạn!")

@bot.tree.command(name="unfollow", description="Hủy theo dõi một chủ đề")
async def unfollow(interaction: discord.Interaction, topic: str):
    remove_user_interest(interaction.user.id, 'discord', topic)
    await interaction.response.send_message(f"❌ Đã xóa **{topic}** khỏi danh sách theo dõi.")

@bot.tree.command(name="join", description="Mời bot vào kênh thoại của bạn")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"✅ Đã kết nối vào kênh `{channel.name}`")
    else:
        await interaction.response.send_message("❌ Bạn cần vào một kênh thoại trước!")

@bot.tree.command(name="leave", description="Đuổi bot khỏi kênh thoại")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Tạm biệt, tớ đi đây!")
    else:
        await interaction.response.send_message("❌ Tớ có ở trong kênh nào đâu?")

@bot.tree.command(name="play", description="Phát nhạc từ YouTube (tên bài hát hoặc link)")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    
    # Kiểm tra voice
    if not interaction.user.voice:
        await interaction.followup.send("❌ Bạn cần vào một kênh thoại trước!")
        return

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    voice_client = interaction.guild.voice_client

    try:
        # Tìm kiếm và lấy thông tin
        if not search.startswith("http"):
            search = f"ytsearch:{search}"
            
        player = await YTDLSource.from_url(search, loop=bot.loop, stream=True)
        
        if voice_client.is_playing():
            voice_client.stop()
            
        voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        
        embed = Embed(
            title="🎵 Đang phát nhạc",
            description=f"**{player.title}**\nNgười yêu cầu: {interaction.user.mention}",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Có lỗi xảy ra: {e}")

@bot.tree.command(name="stop", description="Dừng phát nhạc")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏹️ Đã dừng phát nhạc.")
    else:
        await interaction.response.send_message("❌ Hiện tại không có nhạc nào đang phát.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Photo search handler
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                msg = await message.channel.send("🔍 Đang truy tìm dấu vết bộ anime này qua ảnh... Chờ tớ xíu!")
                try:
                    response = requests.get(f"https://api.trace.moe/search?url={attachment.url}")
                    data = response.json()
                    
                    if not data.get('result'):
                        await msg.edit(content="Hic, tớ không tìm thấy phim nào giống ảnh này cả.")
                        continue
                        
                    result = data['result'][0]
                    episode = result.get('episode')
                    similarity = result.get('similarity')
                    
                    if similarity < 0.8:
                        await msg.edit(content="Ảnh này mờ quá hoặc không phải anime rồi, tớ không chắc chắn lắm!")
                        continue

                    title = result.get('filename', 'Unknown Anime')
                    
                    res_text = (
                        f"✅ **TÌM THẤY RỒI!**\n\n"
                        f"📌 Phim: **{title}**\n"
                        f"📺 Tập: {episode}\n"
                        f"🎯 Độ chính xác: {similarity*100:.1f}%\n\n"
                        f"*Mẹo: Bạn có thể copy tên phim và dùng lệnh `/search` để đăng ký theo dõi nhé!*"
                    )
                    await msg.edit(content=res_text)
                except Exception as e:
                    await msg.edit(content=f"Lỗi khi tìm kiếm ảnh: {e}")
                return

    # Process commands
    await bot.process_commands(message)

    # AI Chat handler: Chỉ trả lời nếu được Mention hoặc nhắn tin riêng (DM)
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user.mentioned_in(message)
    
    if (is_dm or is_mentioned) and not message.content.startswith('!'):
        persona_name = get_user_persona(message.author.id, 'discord')
        # Loại bỏ phần mention trong tin nhắn để AI không bị nhầm lẫn
        clean_content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()
        
        if clean_content:
            response = await get_ai_response(clean_content, persona=persona_name)
            await message.channel.send(response)

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token and token != "your_discord_token_here":
        bot.run(token)
    else:
        print("LỖI: Chưa có DISCORD_BOT_TOKEN trong file .env!")
