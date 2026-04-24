from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("LỖI: Chưa có GEMINI_API_KEY trong file .env!")
        return

    try:
        client = genai.Client(api_key=api_key)
        print("🔎 Đang kiểm tra danh sách các model khả dụng...")
        
        # Liệt kê các model hỗ trợ generate_content
        for model in client.models.list():
            # Trong SDK mới, chúng ta có thể kiểm tra trực tiếp tên model
            print(f"✅ Model: {model.name}")
            
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách: {e}")

if __name__ == "__main__":
    list_models()
