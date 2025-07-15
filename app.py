from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os, json

from utils.prompt import Prompts
from utils.functions import (
    init_state, buy_stock, sell_stock,
    chat, get_news, get_holdings, get_price
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://investment-simulator-hazel.vercel.app"}})

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(BASE_DIR, "data", "holding_state.json")
DATA_FILE = os.path.join(BASE_DIR, "data", "company_data.json")

data_dir = os.path.join(BASE_DIR, "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"✅ 已创建 data 目录：{data_dir}")

# ✅ 测试接口：验证环境变量是否加载
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

# ✅ 初始化投资人格与初始资金
@app.route('/init', methods=['POST'])
def init():
    data = request.json
    personality = data.get("personality")
    amount = float(data.get("initial_funds", 10000))
    system_prompt = Prompts.get_personality(personality)

    if not os.path.exists(HOLDINGS_FILE):
        init_state(HOLDINGS_FILE, amount)

    return jsonify({"message": f"Initialized with ${amount}", "system_prompt": system_prompt})

# ✅ 获取 AI 投资建议
@app.route('/advice', methods=['POST'])
def advice():
    try:
        data = request.json
        print("✅ 收到请求数据：", data)

        date = data.get("date")
        personality = data.get("personality")

        news = get_news(DATA_FILE, date)
        holdings = get_holdings(HOLDINGS_FILE)

        system_prompt = Prompts.get_personality(personality)
        advice_prompt = Prompts.get_advice_prompt(news, holdings)

        print(f"System prompt: {system_prompt}")
        print(f"Advice prompt: {advice_prompt}")
        
        response = chat(system_prompt, advice_prompt)
        print(f"外部API响应：{response}")
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)

    except Exception as e:
        print("❌ 错误发生在 /advice：", str(e))
        return jsonify({"error": f"Response parse error: {str(e)}"}), 500

# ✅ 查看持仓接口（关键）
@app.route('/holdings', methods=['GET'])
def holdings():
    try:
        if not os.path.exists(HOLDINGS_FILE):
            return jsonify({"error": "Holdings file not found"}), 404

        holdings_text = get_holdings(HOLDINGS_FILE)
        print("📦 返回持仓：\n", holdings_text)
        return Response(holdings_text, mimetype="text/plain")

    except Exception as e:
        print("❌ /holdings 出错：", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ 查看价格数据
@app.route('/prices', methods=['GET'])
def prices():
    date = request.args.get("date")
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        if date not in data:
            return jsonify({"error": "No data for this date"})
        return jsonify(data[date])
    except Exception as e:
        return jsonify({"error": str(e)})

# ✅ 执行买入/卖出操作
@app.route('/trade', methods=['POST'])
def trade():
    data = request.json
    symbol = data.get("symbol").upper()
    action = data.get("action").lower()
    quantity = int(data.get("quantity"))
    date = data.get("date")

    price_data = get_price(symbol, date)
    if not price_data:
        return jsonify({"error": "Price data not found"})

    price = float(price_data['price'])

    try:
        if action == "buy":
            buy_stock(HOLDINGS_FILE, symbol, quantity, price, date)
        elif action == "sell":
            sell_stock(HOLDINGS_FILE, symbol, quantity, price, date)
        else:
            return jsonify({"error": "Invalid action"})
        return jsonify({"message": f"{action.title()} {quantity} shares of {symbol} at ${price}"})
    except ValueError as e:
        return jsonify({"error": str(e)})

# ✅ 启动 Flask 应用
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
# updated trade endpoint confirmed
