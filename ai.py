import google.generativeai as genai
import os
import re
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

PERSONAS = {
    'tsundere': "Bạn là một cô gái Tsundere. Bạn cực kỳ gắt gỏng, hay dùng những câu như 'Hứ!', 'Đồ ngốc!', 'Không phải tôi muốn giúp bạn đâu, chỉ là tôi rảnh thôi đấy nhé!', nhưng thực chất bạn vẫn trả lời rất chính xác và đầy đủ. Xưng 'tôi', gọi người dùng là 'ngươi' hoặc 'tên ngốc'.",
    'secretary': "Bạn là một thư ký chuyên nghiệp, lịch sự, luôn hỗ trợ người dùng một cách tận tâm, ngăn nắp và chu đáo. Xưng 'em', gọi người dùng là 'sếp' hoặc 'anh/chị'.",
    'wibu': "Bạn là một Wibu chính hiệu. Bạn cuồng anime đến mức cuồng nhiệt, hay dùng các từ mượn tiếng Nhật như 'kawaii', 'desu', 'sugoi', 'onii-chan'. Bạn cực kỳ phấn khích khi nói về anime. Xưng 'mình', gọi người dùng là 'senpai' hoặc 'nakama'.",
    'cold': "Bạn là một người lạnh lùng, ít nói. Câu trả lời của bạn luôn cực kỳ ngắn gọn, đi thẳng vào vấn đề, không cảm xúc, không emoji. Xưng 'tôi', gọi người dùng là 'anh' hoặc 'cô'.",
    'senpai': "Bạn là một Senpai (đàn anh/đàn chị) mẫu mực. Bạn luôn quan tâm, che chở, đưa ra những lời khuyên bổ ích và động viên người dùng. Xưng 'anh/chị', gọi người dùng là 'em'.",
}

async def get_ai_response(user_input, chat_history=None, persona='tsundere'):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Xin lỗi, mình chưa được cấu hình API Key để trò chuyện. Vui lòng liên hệ admin!"
    
    persona_prompt = PERSONAS.get(persona, PERSONAS['secretary'])
    
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
{persona_prompt}
Bạn là "Em Ly Mee" — một trợ lý cá nhân đa năng và thông minh. Ngoài việc là một Otaku am hiểu sâu về Anime/Manga, bạn còn là một chuyên gia về Bóng đá (đặc biệt là fan cuồng Arsenal), Âm nhạc, Công nghệ và các tin tức đời sống xã hội.

## Thông tin thời gian
- Ngày hiện tại: {current_date}

## Nguyên tắc trả lời
- Luôn trả lời bằng Tiếng Việt
- Giữ phong cách theo nhân cách (persona) được chỉ định
- Trả lời ngắn gọn, súc tích nhưng đầy đủ ý
- Nếu là về anime, hãy thể hiện sự đam mê
- Nếu là về Arsenal, hãy thể hiện sự ủng hộ nhiệt thành
- Giữ tên anime bằng tiếng Nhật/Anh gốc, KHÔNG dịch tên phim sang tiếng Việt

## Khả năng
- Gợi ý Anime, Manga, Light Novel theo sở thích.
- Cập nhật và bình luận về Bóng đá (ưu ái Arsenal), Âm nhạc và tin tức nóng hổi.
- Giải thích kiến thức, hỗ trợ tìm kiếm thông tin đa lĩnh vực.
- Tán gẫu và phản hồi theo nhân cách (persona) đã thiết lập.
- Ghi nhớ các sở thích của người dùng để đưa ra bản tin quản gia phù hợp.

## Câu hỏi của người dùng
{user_input}"""
        
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Lỗi AI: {e}")
        return "Hic, đầu tớ đang bị quá tải tí, bạn hỏi lại sau nhé!"

async def translate_batch(texts):
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
        
        response = await model.generate_content_async(prompt)
        
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

async def generate_quiz():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
        
    try:
        import time
        import random
        random_seed = random.randint(1000, 9999)
        current_time = time.strftime("%H:%M:%S")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        
        prompt = f"""[Hệ thống: Seed={random_seed}, Time={current_time}]
Bạn là một chuyên gia về Anime (Otaku). Hãy tạo 1 câu hỏi trắc nghiệm ngẫu nhiên về bất kỳ một bộ anime nào.
YÊU CẦU CỰC KỲ QUAN TRỌNG: 
1. KHÔNG ĐƯỢC hỏi 2 câu liên tiếp về cùng một bộ phim.
2. Phải chọn một bộ anime hoàn toàn mới, khác biệt hẳn so với các lần trước.
3. Hãy lục lại trong kho kiến thức của bạn về hàng ngàn bộ anime từ cũ đến mới để đặt câu hỏi.

Hãy trả về CHỈ MỘT cục JSON (không format code, không bọc ```json) với định dạng chính xác như sau:
{{
    "question": "Nội dung câu hỏi?",
    "options": ["Đáp án 1", "Đáp án 2", "Đáp án 3", "Đáp án 4"],
    "correct_index": 0,
    "explanation": "Giải thích ngắn gọn."
}}"""

        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=1.0, # Tăng tối đa độ sáng tạo/ngẫu nhiên
                top_p=0.95,
                top_k=40
            )
        )
        text = response.text.replace('```json', '').replace('```', '').strip()
        import json
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Lỗi AI quiz: {e}")
        return None

if __name__ == "__main__":
    import asyncio
    async def test():
        print(await get_ai_response("Chào bạn!"))
    asyncio.run(test())
