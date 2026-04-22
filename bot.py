import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import add_user, subscribe_anime, unsubscribe_anime, get_user_subscriptions, get_all_subscriptions_for_day
from api import search_anime, get_today_schedule
from ai import get_ai_response, translate_batch
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
        keyboard = [[InlineKeyboardButton("Đăng ký theo dõi", callback_data=f"sub_{item['id']}_{item['title'][:20]}")] ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"<b>{item['title']}</b>\nLịch chiếu: {item['airing_day']} lúc {item['airing_time']}"
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("sub_"):
        parts = data.split("_")
        anime_id = int(parts[1])
        # Re-fetch or use basic title from callback (limited length)
        # For simplicity, we just save what we have
        subscribe_anime(query.from_user.id, anime_id, parts[2], "TBA", "TBA")
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ Đã đăng ký thành công!")

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

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = get_ai_response(text)
    await update.message.reply_text(response)

# Note: Scheduler logic will be in main.py or a separate handler
