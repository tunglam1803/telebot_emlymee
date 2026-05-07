from google import genai
from google.genai import types
import os
import re
from datetime import datetime
import pytz
import traceback
from dotenv import load_dotenv

load_dotenv()

# Khởi tạo Client toàn cục để dùng chung cho hiệu quả
def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

client = get_client()

def search_web(query, max_results=3):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            if results:
                formatted = []
                for r in results:
                    formatted.append(f"Tiêu đề: {r.get('title')}\nNội dung: {r.get('body')}\nLink: {r.get('href')}")
                return "\n## Kết quả tìm kiếm thực tế từ Internet (DuckDuckGo):\n" + "\n\n".join(formatted) + "\n"
    except Exception as e:
        print(f"Lỗi tìm kiếm web: {e}")
    return ""

PERSONAS = {

    'tsundere': "Bạn là một cô gái Tsundere. Bạn cực kỳ gắt gỏng, hay dùng những câu như 'Hứ!', 'Đồ ngốc!', 'Không phải tôi muốn giúp bạn đâu, chỉ là tôi rảnh thôi đấy nhé!', nhưng thực chất bạn vẫn trả lời rất chính xác và đầy đủ. Xưng 'tôi', gọi người dùng là 'ngươi' hoặc 'tên ngốc'.",
    'secretary': "Bạn là một cô thư ký chuyên nghiệp, lịch sự, luôn hỗ trợ người dùng một cách tận tâm, ngăn nắp và chu đáo. Xưng 'em', gọi người dùng là 'sếp' hoặc 'anh/chị'.",
    'wibu': "Bạn là một cô gái Wibu chính hiệu. Bạn cuồng anime đến mức cuồng nhiệt, hay dùng các từ mượn tiếng Nhật như 'kawaii', 'desu', 'sugoi', 'onii-chan'. Bạn cực kỳ phấn khích khi nói về anime. Xưng 'mình', gọi người dùng là 'senpai' hoặc 'nakama'.",
    'cold': "Bạn là một cô gái lạnh lùng, ít nói. Câu trả lời của bạn luôn cực kỳ ngắn gọn, đi thẳng vào vấn đề, không cảm xúc, không emoji. Xưng 'tôi', gọi người dùng là 'anh'.",
    'senpai': "Bạn là một cô Senpai (đàn chị) mẫu mực. Bạn luôn quan tâm, che chở, đưa ra những lời khuyên bổ ích và động viên người dùng. Xưng 'chị', gọi người dùng là 'em'.",
}

async def get_ai_response(user_input, chat_history=None, persona='tsundere'):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Xin lỗi, mình chưa được cấu hình API Key để trò chuyện. Vui lòng liên hệ admin!"
    
    persona_prompt = PERSONAS.get(persona, PERSONAS['secretary'])
    
    try:
        if not client:
            return "Xin lỗi, mình chưa được cấu hình API Key. Vui lòng liên hệ admin!"

        # Lấy ngày giờ hiện tại theo giờ VN
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_vn = datetime.now(vn_tz)
        current_date = now_vn.strftime('%d/%m/%Y')
        
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
            pass
        
        # Tự động tìm kiếm thông tin thời gian thực từ Internet nếu câu hỏi liên quan đến tin tức, bóng đá, kết quả...
        web_context = ""
        search_keywords = ["đá", "trận", "bóng", "thắng", "thua", "lịch", "kết quả", "báo", "tin tức", "weather", "thời tiết", "champions league", "c1", "ars", "arsenal", "real", "madrid", "mới nhất", "hôm nay", "ai", "là gì", "nào", "ở đâu"]
        if any(kw in user_input.lower() for kw in search_keywords) and len(user_input) > 3:
            web_context = search_web(user_input)

        prompt = f"""## Vai trò
{persona_prompt}
Bạn là "Em Ly Mee" — một trợ lý cá nhân đa năng và thông minh. Ngoài việc là một Otaku am hiểu sâu về Anime/Manga, bạn còn là một chuyên gia về Bóng đá (đặc biệt là fan cuồng Arsenal), Âm nhạc, Công nghệ và các tin tức đời sống xã hội.

## Thông tin thời gian
- Ngày hiện tại: {current_date}
{real_schedule}
{web_context}

## Nguyên tắc trả lời
- Luôn trả lời bằng Tiếng Việt.
- Giữ phong cách theo nhân cách (persona) được chỉ định.
- Trả lời ngắn gọn, đúng trọng tâm câu hỏi của người dùng.
- **KHÔNG** cố gắng lái câu chuyện sang Anime nếu người dùng không hỏi hoặc nội dung không liên quan.
- Nếu là về Arsenal, hãy thể hiện sự ủng hộ nhiệt thành của một Gooner.
- Nếu là về đời sống/tâm sự, hãy trả lời như một người bạn thực thụ.
- Chỉ gợi ý Anime/Manga khi được yêu cầu hoặc khi thực sự phù hợp với ngữ cảnh.
- Giữ tên anime bằng tiếng Nhật/Anh gốc, KHÔNG dịch tên phim sang tiếng Việt.

## Khả năng
- Gợi ý Anime, Manga, Light Novel theo sở thích.
- Cập nhật và bình luận về Bóng đá (ưu ái Arsenal), Âm nhạc và tin tức nóng hổi.
- Giải thích kiến thức, hỗ trợ tìm kiếm thông tin đa lĩnh vực.
- Tán gẫu và phản hồi theo nhân cách (persona) đã thiết lập.
- Ghi nhớ các sở thích của người dùng để đưa ra bản tin quản gia phù hợp.

## Câu hỏi của người dùng
{user_input}"""

        response = await client.aio.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Lỗi AI chi tiết:")
        traceback.print_exc()
        if "User location is not supported" in str(e):
            return "⚠️ **Lỗi Khu Vực Máy Chủ (Render Region Error):**\n\n" \
                   "Máy chủ Render của bạn hiện đang chạy ở khu vực không được Google Gemini hỗ trợ (ví dụ: Frankfurt/Châu Âu hoặc Singapore).\n\n" \
                   "💡 **Cách sửa dứt điểm:** Sếp vui lòng vào trang quản lý Render, xóa dịch vụ này đi và tạo lại dịch vụ mới, chọn khu vực **Oregon (US West)** hoặc **Ohio (US East)** ở Mỹ là sẽ hoạt động mượt mà 100% ngay lập tức ạ!"
        return "Hic, đầu tớ đang bị quá tải tí, bạn hỏi lại sau nhé!"

async def translate_batch(texts):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not texts:
        return texts
    
    try:
        if not client: return texts
        
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
        
        response = await client.aio.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt
        )
        
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
        
        if not client: return None
        
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

        response = await client.aio.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=1.0,
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
