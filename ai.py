import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def get_ai_response(user_input, chat_history=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Xin lỗi, mình chưa được cấu hình API Key để trò chuyện. Vui lòng liên hệ admin!"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # System prompt to give context
        prompt = f"Bạn là một trợ lý ảo yêu thích anime trên Telegram. Hãy trả lời câu hỏi sau của người dùng một cách thân thiện: {user_input}"
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in Gemini API: {e}")
        return "Đã có lỗi xảy ra khi kết nối với bộ não AI của mình."

def translate_batch(texts):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not texts:
        return texts
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Gộp các đoạn văn bản lại với dấu phân cách rõ ràng
        combined_text = "\n---\n".join(texts)
        prompt = f"Hãy dịch danh sách các đoạn tóm tắt anime sau sang tiếng Việt. Giữ nguyên định dạng và phân tách các đoạn bằng dấu '---':\n\n{combined_text}"
        
        response = model.generate_content(prompt)
        translated_results = response.text.split("---")
        
        # Làm sạch kết quả
        return [res.strip() for res in translated_results]
    except Exception as e:
        print(f"Batch Translation Error: {e}")
        return texts
    finally:
        print("--- Kết thúc hàm dịch ---")

if __name__ == "__main__":
    # Test if key is present
    print(get_ai_response("Chào bạn!"))
