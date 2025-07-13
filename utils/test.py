from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

# 从环境变量读取 API 密钥
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# 打印出 API 密钥，确认是否正确加载
print(f"Loaded API_KEY: {API_KEY}")

# 创建 OpenAI 客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 测试与 OpenAI API 的连接
try:
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",  # 使用你提供的模型
        messages=[{"role": "system", "content": "Hello, how are you?"}, 
                  {"role": "user", "content": "I'm good, thanks!"}],
        response_format={"type": "json_object"}
    )
    print("API Response:", response)  # 打印返回的响应
except Exception as e:
    print("❌ OpenAI API request failed:", e)

