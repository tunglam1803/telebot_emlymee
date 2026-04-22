import google.generativeai as genai
import os
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

def get_ai_response(user_input, chat_history=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Xin lỗi, mình chưa được cấu hình API Key để trò chuyện. Vui lòng liên hệ admin!"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        
        # Lấy ngày giờ hiện tại theo giờ VN
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_vn = datetime.now(vn_tz)
        current_date = now_vn.strftime('%d/%m/%Y')
        current_time = now_vn.strftime('%H:%M')
        season_map = {1: "Đông", 2: "Đông", 3: "Đông", 4: "Xuân", 5: "Xuân", 6: "Xuân", 7: "Hè", 8: "Hè", 9: "Hè", 10: "Thu", 11: "Thu", 12: "Thu"}
        current_season = f"mùa {season_map[now_vn.month]} {now_vn.year}"
        
        # Lấy lịch chiếu thật từ API để AI có dữ liệu chính xác
        from api import get_today_schedule
        real_schedule = ""
        try:
            schedule = get_today_schedule()
            if schedule:
                top_anime = schedule[:5]
                real_schedule = "\n## Lịch chiếu THẬT hôm nay (từ API)\n"
                for anime in top_anime:
                    real_schedule += f"- {anime['title']} (chiếu lúc {anime['time']} giờ VN)\n"
        except:
            pass
        
        prompt = f"""## Vai trò
Bạn là "Em Ly Me" — một trợ lý anime trên Telegram. Bạn là một otaku thực thụ, am hiểu sâu về anime, manga, light novel và văn hóa Nhật Bản.

## Thông tin thời gian
- Ngày hiện tại: {current_date}
- Giờ hiện tại: {current_time} (giờ Việt Nam, GMT+7)
- Mùa anime hiện tại: {current_season}
{real_schedule}
## GIỚI HẠN QUAN TRỌNG
- Dữ liệu huấn luyện của bạn chỉ đến khoảng năm 2024. Bạn KHÔNG biết chính xác anime nào đang chiếu trong năm {now_vn.year}.
- TUYỆT ĐỐI KHÔNG được bịa tên anime, mùa phim, hoặc thông tin phát sóng mà bạn không chắc chắn.
- Nếu được hỏi về anime đang hot / mới nhất / đang chiếu → Hãy tham khảo "Lịch chiếu THẬT hôm nay" ở trên (nếu có), và hướng dẫn dùng lệnh /today để xem lịch chiếu đầy đủ.
- Bạn CÓ THỂ tự tin nói về các anime đã phát sóng trước năm 2025 (ví dụ: gợi ý anime kinh điển, giải thích cốt truyện cũ...).

## Phong cách trả lời
- Xưng "tớ", gọi người dùng là "cậu"
- Thân thiện, vui vẻ, dùng emoji vừa phải (1-3 emoji mỗi tin nhắn)
- Trả lời NGẮN GỌN vì đây là Telegram, không phải bài viết blog. Tối đa 150 từ trừ khi cần liệt kê danh sách.
- Dùng từ ngữ tự nhiên của giới trẻ Việt Nam (ví dụ: "cày phim", "hot", "gánh team", "hype")
- Giữ tên anime bằng tiếng Nhật/Anh gốc, KHÔNG dịch tên phim sang tiếng Việt

## Khả năng
- Gợi ý anime KINH ĐIỂN theo thể loại, tâm trạng, hoặc sở thích
- So sánh các bộ anime
- Giải thích cốt truyện, nhân vật
- Tán gẫu chủ đề anime và ngoài anime đều được

## Câu hỏi của người dùng
{user_input}"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = f"Lỗi Gemini: {str(e)}"
        print(error_msg)
        return f"Đã có lỗi xảy ra: {error_msg}"

def translate_batch(texts):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not texts:
        return texts
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        
        # Đánh số từng đoạn để AI không bị nhầm lẫn
        numbered_texts = []
        for i, text in enumerate(texts, 1):
            numbered_texts.append(f"[{i}] {text}")
        combined_text = "\n".join(numbered_texts)
        
        prompt = f"""Dịch các đoạn tóm tắt anime dưới đây sang tiếng Việt tự nhiên.

QUY TẮC:
- Giữ nguyên số thứ tự [{'{số}'}] ở đầu mỗi đoạn
- Giữ tên riêng (tên nhân vật, địa danh) bằng tiếng gốc
- Dịch tự nhiên, không dịch máy móc
- KHÔNG thêm, bớt hoặc gộp đoạn. Có bao nhiêu đoạn đầu vào thì trả về đúng bấy nhiêu đoạn.

NỘI DUNG CẦN DỊCH:
{combined_text}"""
        
        response = model.generate_content(prompt)
        
        # Parse kết quả theo số thứ tự
        result_text = response.text
        translated = []
        for i in range(1, len(texts) + 1):
            # Tìm đoạn text giữa [i] và [i+1] (hoặc cuối chuỗi)
            if i < len(texts):
                pattern = rf'\[{i}\]\s*(.*?)(?=\[{i+1}\])'
            else:
                pattern = rf'\[{i}\]\s*(.*)'
            match = re.search(pattern, result_text, re.DOTALL)
            if match:
                translated.append(match.group(1).strip())
            else:
                # Fallback: giữ nguyên text gốc nếu parse thất bại
                translated.append(texts[i-1])
        
        return translated
    except Exception as e:
        print(f"Batch Translation Error: {e}")
        return texts


if __name__ == "__main__":
    # Test if key is present
    print(get_ai_response("Chào bạn!"))
