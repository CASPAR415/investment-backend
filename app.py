from flask import Flask, request, jsonify
from flask import Response
from flask_cors import CORS
from utils.prompt import Prompts
from utils.functions import (
    init_state, buy_stock, sell_stock,
    chat, get_news, get_holdings, get_price
)
import os
import json

app = Flask(__name__)
CORS(app)

# 打印环境变量，方便调试（可部署后再删掉）
import utils.functions as uf
print(f"✅ Loaded API_KEY prefix: {uf.API_KEY[:10]}...")
print(f"✅ Loaded BASE_URL: {uf.BASE_URL}")

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(BASE_DIR, "data", "holding_state.json")
DATA_FILE = os.path.join(BASE_DIR, "data", "company_data.json")

# 测试环境变量是否加载
@app.route('/test', methods=['GET'])
def test_env():
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return jsonify({
            "status": "✅ Success",
            "key_prefix": key[:12] + "..."
        })
    else:
        return jsonify({
            "status": "❌ Failed",
            "error": "OPENROUTER_API_KEY not found"
        })

# 下面是你之前的接口，保持不变...

# 初始化投资人格 & 资金
@app.route('/init', methods=['POST'])
def init():
    data = request.json
    personality = data.get("personality")
    amount = float(data.get("initial_funds", 10000))
    system_prompt = Prompts.get_personality(personality)

    if not os.path.exists(HOLDINGS_FILE):
        init_state(HOLDINGS_FILE, amount)

    return jsonify({"message": f"Initialized with ${amount}", "system_prompt": system_prompt})

# 获取建议
@app.route('/advice', methods=['POST'])
def advice():
    try:
        data = request.json
        print("✅ 收到请求数据：", data)

        date = data.get("date")
        personality = data.get("personality")

        news = get_news(DATA_FILE, date)
        holdings = get_holdings(HOLDINGS_FILE)
        print("📄 News 摘要：", news[:200])
        print("📊 Holdings 摘要：", holdings)

        system_prompt = Prompts.get_personality(personality)
        advice_prompt = Prompts.get_advice_prompt(news, holdings)
        print("🤖 Prompt 生成完成")

        response = chat(system_prompt, advice_prompt)
        print("✅ AI 响应完成")

        result = json.loads(response.choices[0].message.content)
        return jsonify(result)

    except Exception as e:
        print("❌ 错误发生在 /advice：", str(e))
        return jsonify({"error": f"Response parse error: {str(e)}"}), 500

# 其他接口同之前的代码...

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

