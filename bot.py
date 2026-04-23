import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_user, subscribe_anime, unsubscribe_anime, get_user_subscriptions
from api import search_anime, get_today_schedule, get_anime_by_id, get_random_anime, search_character, get_top_anime
from ai import get_ai_response, translate_batch, generate_quiz
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
    quiz_data = generate_quiz()
    
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
    about_vn = get_ai_response(f"Hãy tóm tắt ngắn gọn (khoảng 100 từ) thông tin nhân vật này bằng tiếng Việt: {char['about']}")
    
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
        # Gọi API trace.moe
        response = requests.get(f"https://api.trace.moe/search?url={image_url}")
        data = response.json()
        
        if not data.get('result'):
            await msg.edit_text("Hic, tớ không tìm thấy phim nào giống ảnh này cả.")
            return
            
        result = data['result'][0]
        # Trace.moe trả về anilist ID và filename, nhưng thường filename chứa tên phim
        # Ở đây ta lấy tên từ result['filename'] hoặc result['anilist']
        # Để đơn giản và chính xác, ta hiển thị kết quả đầu tiên
        episode = result.get('episode')
        similarity = result.get('similarity')
        
        if similarity < 0.8:
            await msg.edit_text("Ảnh này mờ quá hoặc không phải anime rồi, tớ không chắc chắn lắm!")
            return

        # Lấy tên phim từ field anilist (thường là object nếu dùng query, nhưng trace.moe v2 trả về ID)
        # Ta sẽ dùng title_romaji nếu có
        title = result.get('filename', 'Unknown Anime')
        
        res_text = (
            f"✅ <b>TÌM THẤY RỒI!</b>\n\n"
            f"📌 Phim: <b>{title}</b>\n"
            f"📺 Tập: {episode}\n"
            f"🎯 Độ chính xác: {similarity*100:.1f}%\n\n"
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
    vietnamese_synopses = translate_batch(english_synopses)
    
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
    text = update.message.text
    response = get_ai_response(text)
    await update.message.reply_text(response)

# Note: Scheduler logic will be in main.py or a separate handler
