import os
import logging
import asyncio
import datetime
from datetime import timedelta
import pytz
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Import handlers from bot.py
from bot import start, search, today, chat, button_handler, mylist, gacha, quiz, char_search, top_anime, handle_photo, persona, follow, artist, unfollow
from database import init_db, get_all_subscriptions_for_day, get_all_discord_subscriptions_for_day, get_all_users_with_interests, get_user_interests, get_user_persona
from discord_bot import bot as discord_bot
from api import get_anime_by_id
from ai import get_ai_response

load_dotenv()

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def telegram_daily_reminder(context):
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vn = datetime.datetime.now(vn_tz)
    eng_day = now_vn.strftime('%A')
    
    day_map = {
        "Monday": "Thứ Hai", "Tuesday": "Thứ Ba", "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm", "Friday": "Thứ Sáu", "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật"
    }
    vn_day_name = day_map.get(eng_day, eng_day)
    
    subs = get_all_subscriptions_for_day(vn_day_name)
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
            print(f"Không thể gửi thông báo Telegram cho {chat_id}: {e}")

async def telegram_check_airing_now(context):
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vn = datetime.datetime.now(vn_tz)
    eng_day = now_vn.strftime('%A')
    
    day_map = {
        "Monday": "Thứ Hai", "Tuesday": "Thứ Ba", "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm", "Friday": "Thứ Sáu", "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật"
    }
    vn_day_name = day_map.get(eng_day, eng_day)
    
    subs = get_all_subscriptions_for_day(vn_day_name)
    for sub in subs:
        try:
            h, m = map(int, sub['airing_time'].split(':'))
            air_time = now_vn.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (now_vn - air_time).total_seconds() / 60.0
            
            if 0 <= diff < 10:
                chat_id = sub['chat_id']
                text = f"🔥 <b>CÓ TẬP MỚI!</b>\n\nPhim <b>{sub['anime_title']}</b> vừa mới lên sóng rồi nè cậu ơi. Lấy bắp rang ra xem thôi! 🍿🏃‍♂️"
                
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                reply_markup = None
                detail = get_anime_by_id(sub['anime_id'])
                if detail and detail.get('trailer_url'):
                    reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("📺 Xem Trailer (Trong lúc chờ Vietsub)", url=detail['trailer_url'])
                    ]])

                await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            pass

async def discord_reminders_task():
    """Tương tự Telegram nhưng dành cho Discord, chạy độc lập"""
    await discord_bot.wait_until_ready()
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    
    while not discord_bot.is_closed():
        now_vn = datetime.datetime.now(vn_tz)
        
        # 1. Nhắc lịch hàng ngày lúc 08:00
        if now_vn.hour == 8 and now_vn.minute < 10:
            eng_day = now_vn.strftime('%A')
            day_map = {
                "Monday": "Thứ Hai", "Tuesday": "Thứ Ba", "Wednesday": "Thứ Tư",
                "Thursday": "Thứ Năm", "Friday": "Thứ Sáu", "Saturday": "Thứ Bảy",
                "Sunday": "Chủ Nhật"
            }
            vn_day_name = day_map.get(eng_day, eng_day)
            
            subs = get_all_discord_subscriptions_for_day(vn_day_name)
            user_reminders = {}
            for sub in subs:
                uid = sub['user_id']
                if uid not in user_reminders:
                    user_reminders[uid] = []
                user_reminders[uid].append(sub)
                
            for user_id, anime_list in user_reminders.items():
                try:
                    user = await discord_bot.fetch_user(user_id)
                    if user:
                        text = f"🔔 **Hôm nay ({vn_day_name}) có anime bạn theo dõi nè!**\n\n"
                        for anime in anime_list:
                            text += f"• **{anime['anime_title']}** - Chiếu lúc: {anime['airing_time']}\n"
                        await user.send(text)
                except Exception as e:
                    print(f"Không thể gửi thông báo Discord cho {user_id}: {e}")
            
            # Chờ 10 phút để không gửi lặp lại trong cùng 1 tiếng
            await asyncio.sleep(600)
            
        # 2. Check airing now (mỗi 10 phút)
        eng_day = now_vn.strftime('%A')
        day_map = {
            "Monday": "Thứ Hai", "Tuesday": "Thứ Ba", "Wednesday": "Thứ Tư",
            "Thursday": "Thứ Năm", "Friday": "Thứ Sáu", "Saturday": "Thứ Bảy",
            "Sunday": "Chủ Nhật"
        }
        vn_day_name = day_map.get(eng_day, eng_day)
        subs = get_all_discord_subscriptions_for_day(vn_day_name)
        
        for sub in subs:
            try:
                h, m = map(int, sub['airing_time'].split(':'))
                air_time = now_vn.replace(hour=h, minute=m, second=0, microsecond=0)
                diff = (now_vn - air_time).total_seconds() / 60.0
                
                if 0 <= diff < 10:
                    user_id = sub['user_id']
                    user = await discord_bot.fetch_user(user_id)
                    if user:
                        text = f"🔥 **CÓ TẬP MỚI!**\n\nPhim **{sub['anime_title']}** vừa mới lên sóng rồi nè cậu ơi. Lấy bắp rang ra xem thôi! 🍿🏃‍♂️"
                        await user.send(text)
            except:
                pass
        
        await asyncio.sleep(600) # Quét mỗi 10 phút

async def smart_concierge_task(application):
    """Nhiệm vụ quản gia: Gửi bản tin tóm tắt dựa trên sở thích lúc 09:00 sáng"""
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    
    while True:
        now_vn = datetime.datetime.now(vn_tz)
        if now_vn.hour == 9 and now_vn.minute < 10:
            users = get_all_users_with_interests()
            for u in users:
                chat_id = u['chat_id']
                platform = u['platform']
                interests = get_user_interests(chat_id, platform)
                
                if not interests: continue
                
                # Tạo tóm tắt bằng AI
                topics = ", ".join([f"{i['topic_name']} ({i['topic_type']})" for i in interests])
                persona_name = get_user_persona(chat_id, platform)
                
                prompt = f"Hôm nay có tin tức gì mới về các chủ đề này không: {topics}? Đặc biệt lưu ý Arsenal nếu có bóng đá. Hãy tóm tắt ngắn gọn và thú vị."
                briefing = get_ai_response(prompt, persona=persona_name)
                
                text = f"☕ **BẢN TIN QUẢN GIA SÁNG NAY**\n\n{briefing}"
                
                try:
                    if platform == 'telegram':
                        await application.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
                    elif platform == 'discord':
                        user = await discord_bot.fetch_user(chat_id)
                        if user:
                            await user.send(text)
                except Exception as e:
                    print(f"Lỗi gửi bản tin quản gia cho {chat_id} ({platform}): {e}")
            
            await asyncio.sleep(600) # Tránh gửi lặp lại
            
        await asyncio.sleep(60) # Kiểm tra mỗi phút

def run_health_check():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import threading
    
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")

    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

async def main():
    init_db()
    run_health_check()
    
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    ds_token = os.getenv("DISCORD_BOT_TOKEN")
    
    tasks = []
    
    # Setup Telegram
    if tg_token and tg_token != "your_telegram_token_here":
        application = ApplicationBuilder().token(tg_token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("today", today))
        application.add_handler(CommandHandler("search", search))
        application.add_handler(CommandHandler("mylist", mylist))
        application.add_handler(CommandHandler("gacha", gacha))
        application.add_handler(CommandHandler("quiz", quiz))
        application.add_handler(CommandHandler("char", char_search))
        application.add_handler(CommandHandler("top", top_anime))
        application.add_handler(CommandHandler("persona", persona))
        application.add_handler(CommandHandler("follow", follow))
        application.add_handler(CommandHandler("artist", artist))
        application.add_handler(CommandHandler("unfollow", unfollow))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
        
        # Telegram Jobs
        vn_tz_offset = datetime.timezone(timedelta(hours=7))
        application.job_queue.run_daily(telegram_daily_reminder, time=datetime.time(hour=8, minute=0, tzinfo=vn_tz_offset))
        application.job_queue.run_repeating(telegram_check_airing_now, interval=600, first=10)
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print("Telegram Bot is starting...")
    else:
        print("Bỏ qua Telegram Bot (Token thiếu)")

    # Setup Discord
    if ds_token and ds_token != "your_discord_token_here":
        print("Discord Bot is starting...")
        if tg_token and tg_token != "your_telegram_token_here":
             asyncio.create_task(smart_concierge_task(application))
        tasks.append(discord_bot.start(ds_token))
    else:
        print("Bỏ qua Discord Bot (Token thiếu)")

    if tasks:
        await asyncio.gather(*tasks)
    else:
        # Nếu chỉ có Telegram chạy
        if tg_token and tg_token != "your_telegram_token_here":
            asyncio.create_task(smart_concierge_task(application))
            while True:
                await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
