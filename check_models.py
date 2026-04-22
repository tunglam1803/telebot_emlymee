import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    print("Danh sách các model bạn có thể dùng:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Lỗi khi lấy danh sách: {e}")

if __name__ == "__main__":
    list_models()
