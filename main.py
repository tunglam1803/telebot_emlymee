import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Import handlers from bot.py
from bot import start, search, today, chat, button_handler, mylist
from database import init_db

load_dotenv()

def main():
    # Initialize database
    init_db()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_token_here":
        print("LỖI: Chưa có TELEGRAM_BOT_TOKEN trong file .env!")
        return

    application = ApplicationBuilder().token(token).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("mylist", mylist))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # AI Chat handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    
    # --- Hệ thống nhắc lịch tự động ---
    import datetime
    from datetime import timedelta
    import pytz
    from database import get_all_subscriptions_for_day

    async def daily_reminder(context):
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_vn = datetime.datetime.now(vn_tz)
        eng_day = now_vn.strftime('%A') # Monday, Tuesday...
        
        # Map sang tiếng Việt để khớp với database
        day_map = {
            "Monday": "Thứ Hai", "Tuesday": "Thứ Ba", "Wednesday": "Thứ Tư",
            "Thursday": "Thứ Năm", "Friday": "Thứ Sáu", "Saturday": "Thứ Bảy",
            "Sunday": "Chủ Nhật"
        }
        vn_day_name = day_map.get(eng_day, eng_day)
        
        # Lấy tất cả đăng ký cho ngày hôm nay
        subs = get_all_subscriptions_for_day(vn_day_name)
        
        # Nhóm theo chat_id để gửi 1 tin nhắn tổng hợp cho mỗi người
        user_reminders = {}
        for sub in subs:
            cid = sub['chat_id']
            if cid not in user_reminders:
                user_reminders[cid] = []
            user_reminders[cid].append(sub)
            
        for chat_id, anime_list in user_reminders.items():
            text = f"🔔 <b>Hôm nay ({vn_day_name}) có anime bạn theo dõi nè!</b>\n\n"
            for anime in anime_list:
                text += f"• <b>{anime['anime_title']}</b> - Chiếu lúc: {anime['airing_time']}\n"
            
            try:
                await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            except Exception as e:
                print(f"Không thể gửi thông báo cho {chat_id}: {e}")

    # Lên lịch chạy lúc 08:00 sáng hàng ngày (Giờ VN = UTC+7)
    vn_tz = datetime.timezone(timedelta(hours=7))
    job_queue = application.job_queue
    job_queue.run_daily(
        daily_reminder, 
        time=datetime.time(hour=8, minute=0, tzinfo=vn_tz)
    )
    # ---------------------------------
    # Chạy một server web đơn giản để Render không tắt bot (Dành cho bản Free)
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")

    def run_health_check():
        port = int(os.environ.get("PORT", 8080))
        httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        httpd.serve_forever()

    threading.Thread(target=run_health_check, daemon=True).start()

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
