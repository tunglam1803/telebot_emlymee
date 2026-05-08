import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_user, subscribe_anime, unsubscribe_anime, get_user_subscriptions, set_user_persona, get_user_persona, add_user_interest, remove_user_interest, get_user_interests
from api import search_anime, get_today_schedule, get_anime_by_id, get_random_anime, search_character, get_top_anime
from ai import get_ai_response, translate_batch, generate_quiz, PERSONAS
import requests
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    await update.message.reply_text(
        f"Chào {user.first_name}! Mình là Bot Thông Báo Anime.\n\n"
        "Các lệnh mình có:\n"
        "/today - Xem lịch chiếu hôm nay\n"
        "/search <tên> - Tìm phim để đăng ký nhận thông báo\n"
        "/mylist - Xem danh sách phim đã đăng ký\n"
        "/gacha - Tìm siêu phẩm ngẫu nhiên để cày\n"
        "/quiz - Thử thách kiến thức Anime\n"
        "/top - Xem Top 10 anime hot nhất hiện nay\n"
        "/char <tên> - Tìm thông tin nhân vật\n"
        "💡 Mẹo: Gửi một tấm ảnh anime cho tớ để tìm tên phim nhé!\n"
        "Hoặc bạn cứ chat bình thường để tán gẫu với mình nhé!"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Vui lòng nhập tên anime cần tìm. VD: /search Naruto")
        return
    
    results = search_anime(query)
    if not results:
        await update.message.reply_text("Không tìm thấy anime nào với tên đó.")
        return
    
    for item in results:
        # Tạo hàng nút bấm
        buttons = [InlineKeyboardButton("✅ Đăng ký theo dõi", callback_data=f"sub_{item['id']}_{item['title'][:20]}")]
        
        # Nếu có link trailer thì thêm nút Xem Trailer
        if item.get('trailer_url'):
            buttons.append(InlineKeyboardButton("📺 Xem Trailer", url=item['trailer_url']))
            
        keyboard = [buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        score_text = f"⭐ {item['score']}/10" if item['score'] != 'N/A' else "⭐ Chưa có điểm"
        text = f"<b>{item['title']}</b>\n{score_text}\nLịch chiếu: {item['airing_day']} lúc {item['airing_time']}"
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

async def gacha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎲 Đang quay gacha tìm siêu phẩm cho bạn...")
    item = get_random_anime()
    
    if not item:
        await update.message.reply_text("Máy gacha đang bị kẹt, thử lại sau nhé!")
        return
        
    buttons = [InlineKeyboardButton("✅ Đăng ký theo dõi", callback_data=f"sub_{item['id']}_{item['title'][:20]}")]
    if item.get('trailer_url'):
        buttons.append(InlineKeyboardButton("📺 Xem Trailer", url=item['trailer_url']))
        
    reply_markup = InlineKeyboardMarkup([buttons])
    score_text = f"⭐ {item['score']}/10" if item['score'] != 'N/A' else "⭐ Chưa có điểm"
    
    text = (
        f"🎲 <b>SIÊU PHẨM GACHA CỦA BẠN LÀ:</b>\n\n"
        f"<b>{item['title']}</b>\n"
        f"{score_text} | Thể loại: {item['genres']}\n"
        f"Số tập: {item['episodes']}\n\n"
        f"<i>{item['synopsis']}</i>"
    )
    
    if item.get('image'):
        await update.message.reply_photo(photo=item['image'], caption=text[:1024], reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🧠 Đang vắt óc nghĩ ra một câu đố anime siêu hóc búa cho bạn đây...")
    quiz_data = await generate_quiz()
    
    if not quiz_data:
        await msg.edit_text("AI đang mệt, không nghĩ ra câu hỏi nào. Bạn thử lại sau nhé!")
        return
        
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=quiz_data['question'],
        options=quiz_data['options'],
        type='quiz',
        correct_option_id=quiz_data['correct_index'],
        explanation=quiz_data['explanation']
    )

async def char_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = " ".join(context.args)
    if not name:
        await update.message.reply_text("Vui lòng nhập tên nhân vật. VD: /char Luffy")
        return
        
    char = search_character(name)
    if not char:
        await update.message.reply_text("Hic, tớ không tìm thấy nhân vật nào tên này cả.")
        return
        
    # Dịch thông tin nhân vật bằng AI
    about_vn = await get_ai_response(f"Hãy tóm tắt ngắn gọn (khoảng 100 từ) thông tin nhân vật này bằng tiếng Việt: {char['about']}")
    
    text = f"👤 <b>NHÂN VẬT: {char['name']}</b>\n\n{about_vn}\n\n🔗 <a href='{char['url']}'>Xem thêm trên MyAnimeList</a>"
    
    if char['image']:
        await update.message.reply_photo(photo=char['image'], caption=text[:1024], parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def top_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Đang lấy danh sách Top 10 Anime hot nhất mùa này...")
    top_list = get_top_anime()
    
    if not top_list:
        await update.message.reply_text("Không lấy được danh sách Top. Thử lại sau nhé!")
        return
        
    text = "🏆 <b>TOP 10 ANIME HOT NHẤT HIỆN NAY:</b>\n\n"
    for i, item in enumerate(top_list, 1):
        text += f"{i}. <b>{item['title']}</b> - ⭐ {item['score']}\n   /search {item['id']} (Để xem chi tiết)\n\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    image_url = photo_file.file_path
    
    msg = await update.message.reply_text("🔍 Đang truy tìm dấu vết bộ anime này qua ảnh... Chờ tớ xíu!")
    
    try:
        import requests
        import re
        
        # Gọi API trace.moe với anilistInfo=true để lấy tên phim tiếng Anh/Romaji siêu sạch
        response = requests.get(f"https://api.trace.moe/search?anilistInfo=true&url={image_url}")
        data = response.json()
        
        if not data.get('result'):
            await msg.edit_text("Hic, tớ không tìm thấy phim nào giống ảnh này cả.")
            return
            
        result = data['result'][0]
        episode = result.get('episode')
        similarity = result.get('similarity', 0)
        
        # Hạ ngưỡng xuống 0.70 và thêm thông báo mềm dẻo để hỗ trợ ảnh crop/nén từ điện thoại
        if similarity < 0.70:
            await msg.edit_text("Ảnh này mờ quá hoặc không phải anime rồi, tớ không chắc chắn lắm!")
            return
            
        # Lấy tên anime sạch từ field anilist
        title = "Unknown Anime"
        anilist = result.get('anilist')
        if isinstance(anilist, dict):
            title_obj = anilist.get('title', {})
            title = title_obj.get('english') or title_obj.get('romaji') or title_obj.get('native') or title
            
        if title == "Unknown Anime":
            raw_filename = result.get('filename', '')
            # Làm sạch filename thô nếu không lấy được từ anilist
            title = re.sub(r'\[.*?\]|\(.*?\)', '', raw_filename).split('.')[0].strip() or raw_filename

        accuracy_note = ""
        if similarity < 0.80:
            accuracy_note = " ⚠️ <i>(Độ chính xác tương đối do ảnh bị crop hoặc nén, sếp check lại thử nhé!)</i>"
            
        res_text = (
            f"✅ <b>TÌM THẤY RỒI!</b>\n\n"
            f"📌 Phim: <b>{title}</b>\n"
            f"📺 Tập: {episode}\n"
            f"🎯 Độ chính xác: {similarity*100:.1f}%{accuracy_note}\n\n"
            f"<i>Mẹo: Bạn có thể copy tên phim và dùng lệnh /search để đăng ký theo dõi nhé!</i>"
        )
        await msg.edit_text(res_text, parse_mode='HTML')
        
    except Exception as e:
        await msg.edit_text(f"Lỗi khi tìm kiếm ảnh: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("sub_"):
        parts = data.split("_")
        anime_id = int(parts[1])
        
        # Lấy thông tin chi tiết để có ngày giờ chiếu chuẩn
        detail = get_anime_by_id(anime_id)
        if detail:
            # Đảm bảo user đã có trong database (vì lỡ họ chưa gõ /start từ khi đổi qua Supabase)
            add_user(query.from_user.id, query.from_user.username)
            
            is_new = subscribe_anime(query.from_user.id, anime_id, detail['title'], detail['airing_day'], detail['airing_time'])
            if is_new:
                await query.edit_message_text(text=f"<b>{detail['title']}</b>\n\n✅ Đã đăng ký theo dõi thành công!", parse_mode='HTML')
            else:
                await query.edit_message_text(text=f"<b>{detail['title']}</b>\n\nℹ️ Bạn đã đăng ký phim này rồi nhé!", parse_mode='HTML')
        else:
            await query.edit_message_text(text="Có lỗi xảy ra khi lấy thông tin phim. Thử lại sau nhé!")

    elif data.startswith("unsub_"):
        parts = data.split("_")
        anime_id = int(parts[1])
        unsubscribe_anime(query.from_user.id, anime_id)
        await query.edit_message_text(text="❌ Đã hủy theo dõi thành công!")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đang lấy và dịch lịch chiếu hôm nay...")
    schedule = get_today_schedule()
    if not schedule:
        await update.message.reply_text("Hôm nay không có lịch chiếu nào hoặc lỗi kết nối.")
        return
    
    # Lấy danh sách 8 bộ đầu tiên
    today_list = schedule[:8]
    
    # Gom các mô tả lại để dịch 1 lần
    english_synopses = [item.get('synopsis') or "No description." for item in today_list]
    vietnamese_synopses = await translate_batch(english_synopses)
    
    for i, item in enumerate(today_list):
        # Đảm bảo index không bị vượt quá nếu AI trả về thiếu kết quả
        synopsis_vn = vietnamese_synopses[i] if i < len(vietnamese_synopses) else "Không có mô tả."
        
        text = f"📌 <b>{item['title']}</b>\n⏰ Giờ chiếu: {item['time']}\n\n📝 {synopsis_vn}"
        await update.message.reply_text(text=text, parse_mode='HTML')

async def mylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subs = get_user_subscriptions(user_id)
    
    if not subs:
        await update.message.reply_text("Bạn chưa đăng ký theo dõi anime nào cả. Hãy dùng /search để tìm phim nhé!")
        return

    for sub in subs:
        keyboard = [[InlineKeyboardButton("❌ Hủy theo dõi", callback_data=f"unsub_{sub['anime_id']}")] ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = f"• <b>{sub['anime_title']}</b>\nLịch chiếu: {sub['airing_day']} lúc {sub['airing_time']}"
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='HTML')

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message
    chat_type = update.effective_chat.type
    bot_username = (await context.bot.get_me()).username
    
    # Logic kiểm tra:
    # 1. Chat riêng (private)
    # 2. Được mention trong group (@bot_username)
    # 3. Trả lời (reply) vào tin nhắn của bot
    is_private = chat_type == 'private'
    is_mentioned = message.text and f"@{bot_username}" in message.text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    
    if is_private or is_mentioned or is_reply_to_bot:
        persona_name = get_user_persona(user_id, 'telegram')
        # Làm sạch nội dung (xóa username bot nếu có)
        clean_text = message.text.replace(f"@{bot_username}", "").strip()
        
        if clean_text:
            response = await get_ai_response(clean_text, persona=persona_name)
            await update.message.reply_text(response)

async def persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    available = ", ".join(f"`{p}`" for p in PERSONAS.keys())
    
    if not context.args:
        current = get_user_persona(user_id, 'telegram')
        await update.message.reply_text(f"🎭 Nhân cách hiện tại của tớ là: `{current}`\nCác nhân cách có sẵn: {available}\nDùng /persona <tên> để đổi nhé!", parse_mode='Markdown')
        return
    
    name = context.args[0].lower()
    if name in PERSONAS:
        set_user_persona(user_id, 'telegram', name)
        await update.message.reply_text(f"✅ Đã đổi nhân cách sang: `{name}`. Từ giờ tớ sẽ nói chuyện kiểu này nhé!")
    else:
        await update.message.reply_text(f"❌ Không tìm thấy nhân cách đó. Hãy chọn: {available}", parse_mode='Markdown')

async def follow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    topic = " ".join(context.args)
    
    if not topic:
        interests = get_user_interests(user_id, 'telegram')
        if not interests:
            await update.message.reply_text("Bạn chưa theo dõi chủ đề nào. Dùng /follow <tên chủ đề> nhé!")
        else:
            list_text = "\n".join([f"• {i['topic_name']} ({i['topic_type']})" for i in interests])
            await update.message.reply_text(f"🔔 **Các chủ đề bạn đang theo dõi:**\n{list_text}", parse_mode='Markdown')
        return
    
    add_user_interest(user_id, 'telegram', 'general', topic)
    await update.message.reply_text(f"✅ Đã thêm **{topic}** vào danh sách theo dõi của bạn!", parse_mode='Markdown')

async def artist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = " ".join(context.args)
    
    if not name:
        await update.message.reply_text("Vui lòng nhập tên ca sĩ. VD: /artist Sơn Tùng M-TP")
        return
    
    add_user_interest(user_id, 'telegram', 'artist', name)
    await update.message.reply_text(f"✅ Đã thêm ca sĩ **{name}** vào danh sách theo dõi của bạn!", parse_mode='Markdown')

async def unfollow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    topic = " ".join(context.args)
    
    if not topic:
        await update.message.reply_text("Vui lòng nhập tên chủ đề cần hủy theo dõi.")
        return
    
    remove_user_interest(user_id, 'telegram', topic)
    await update.message.reply_text(f"❌ Đã xóa **{topic}** khỏi danh sách theo dõi.")

# Note: Scheduler logic will be in main.py or a separate handler
