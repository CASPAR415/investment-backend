from flask import Flask, request, jsonify
from flask import Response
from flask_cors import CORS
from utils.prompt import Prompts
from utils.functions import (
    init_state, buy_stock, sell_stock,
    chat, get_news, get_holdings, get_price
)
import os, json

app = Flask(__name__)
CORS(app)


# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(BASE_DIR, "data", "holding_state.json")
DATA_FILE = os.path.join(BASE_DIR, "data", "company_data.json")

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
    data = request.json
    date = data.get("date")
    personality = data.get("personality")

    news = get_news(DATA_FILE, date)
    holdings = get_holdings(HOLDINGS_FILE)
    system_prompt = Prompts.get_personality(personality)
    advice_prompt = Prompts.get_advice_prompt(news, holdings)
    response = chat(system_prompt, advice_prompt)

    try:
        result = json.loads(response.choices[0].message.content)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Response parse error: {str(e)}"})

# 执行交易
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

# 查看持仓
@app.route('/holdings', methods=['GET'])
def holdings():
    holdings = get_holdings(HOLDINGS_FILE)
    return Response(holdings, mimetype="text/plain")

# 查看价格数据
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

