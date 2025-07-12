# 在 Render 项目根目录下创建 test.py（临时文件）
import os
print("ENV KEY:", os.getenv("OPENROUTER_API_KEY"))
