import json
from openai import OpenAI
import yfinance as yf
from datetime import datetime

PARAMS = {
    "OpenRouter":{
        "API_KEY": "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",
        "BASE_URL": "https://openrouter.ai/api/v1",
        "MODEL": "deepseek/deepseek-chat-v3-0324:free"
    },
    "DeepSeek":{
        "API_KEY": "sk-b214c9c9ee884811bfef511a11b34fb7",
        "BASE_URL": "https://api.deepseek.com",
        "MODEL": "deepseek-chat"
    }
}
PROVIDER = "OpenRouter"
API_KEY = PARAMS[PROVIDER]["API_KEY"]
BASE_URL = PARAMS[PROVIDER]["BASE_URL"]
MODEL = PARAMS[PROVIDER]["MODEL"]

def init_state(file_path: str, amount: float):
    """Initialize the investor state"""
    data = {
        "cash": amount,
        "total_value": amount,
        "holdings": {}
    }
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def buy_stock(file_path: str, symbol: str, quantity: int, price: float, datetime: str):
    """Buy stock and update holdings state"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    total_cost = quantity * price
    if data["cash"] < total_cost:
        raise ValueError("Insufficient funds")
    
    data["cash"] -= total_cost
    
    if symbol not in data["holdings"]:
        data["holdings"][symbol] = {
            "total_quantity": 0,
            "transactions": []
        }
    
    data["holdings"][symbol]["total_quantity"] += quantity
    data["holdings"][symbol]["transactions"].append({
        "date": datetime,
        "price": price,
        "quantity": quantity
    })
    
    data["total_value"] = data["cash"] + sum(
        holding["total_quantity"] * (holding["transactions"][-1]["price"] if holding["transactions"] else 0)
        for holding in data["holdings"].values()
    )
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def sell_stock(file_path: str, symbol: str, quantity: int, price: float, datetime: str):
    """Sell stock and update holdings state"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if symbol not in data["holdings"]:
        raise ValueError("Stock not in portfolio")
    
    if data["holdings"][symbol]["total_quantity"] < quantity:
        raise ValueError("Insufficient shares")
    
    total_value = quantity * price
    data["cash"] += total_value
    
    # FIFO sell logic
    remaining = quantity
    transactions = data["holdings"][symbol]["transactions"]
    for i in range(len(transactions)):
        if remaining <= 0:
            break
        sell_qty = min(remaining, transactions[i]["quantity"])
        transactions[i]["quantity"] -= sell_qty
        remaining -= sell_qty
    
    data["holdings"][symbol]["total_quantity"] -= quantity
    
    # Remove empty transactions
    data["holdings"][symbol]["transactions"] = [
        t for t in transactions 
        if t["quantity"] > 0
    ]
    
    data["total_value"] = data["cash"] + sum(
        holding["total_quantity"] * (holding["transactions"][-1]["price"] if holding["transactions"] else 0)
        for holding in data["holdings"].values()
    )
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def chat(system_prompt: str, user_prompt: str):
    """Send a chat message to the deepseek API and return the response"""
    client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    )
    messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={
            'type': 'json_object'
        }
    )
    return response

def get_news(file_path: str, datetime: str):
    """Get news from the file for a specific datetime"""
    with open(file_path, 'r') as file:
        data = json.load(file)
        
        # Check if the specified datetime exists in the data
        if datetime not in data:
            return f"No data found for {datetime}."
        
        # Initialize the output string
        output = f"Company News and Stock Information for {datetime}:\n\n"
        
        # Iterate through companies in the specified month
        for company, info in data[datetime].items():
            output += f"Company: {company}\n"
            
            # Add stock information
            stock = info.get('stock', {})
            price = stock.get('price', 'N/A')
            change = stock.get('change', 'N/A')
            volume = stock.get('volume', 'N/A')
            output += "Stock Information:\n"
            output += f"  Price: ${price}\n"
            output += f"  Change: {change}%\n" if isinstance(change, (int, float)) else f"  Change: {change}%\n"
            output += f"  Volume: {volume}\n" if isinstance(volume, (int, float)) else f"  Volume: {volume}\n"
            
            # Add news information
            news_list = info.get('news', [])
            output += "News:\n"
            if not news_list:
                output += "  No news available.\n"
            else:
                for news_item in news_list:
                    title = news_item.get('title', 'N/A')
                    date = news_item.get('date', 'N/A')
                    #source = news_item.get('source', 'N/A')
                    output += f"  - {title}\n"
                    output += f"    Date: {date}\n"
                    #output += f"    Source: {source}\n"
            
            output += "\n"  # Separator between companies
        
        return output.strip()  # Remove trailing newline

def get_holdings(file_path: str):
    """Get current holdings from the file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    cash = data.get("cash", 0.0)
    total_value = data.get("total_value", 0.0)
    holdings = data.get("holdings", {})
    
    output = f"Current cash: ${cash:.2f}\nTotal portfolio value: ${total_value:.2f}\nCurrent Holdings:\n"
    for symbol, info in holdings.items():
        total_quantity = info["total_quantity"]
        output += f"{symbol}: {total_quantity} shares\n"
    
    return output.strip()  # Remove trailing newline


def get_price(symbol: str, year_month: str) -> dict:
    """Get monthly stock price and market data for a company"""
    try:
        # Parse year and month from input
        year, month = map(int, year_month.split('-'))
        
        # Calculate month start and end dates
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Fetch data from Yahoo Finance
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date.strftime('%Y-%m-%d'), 
                            end=end_date.strftime('%Y-%m-%d'))
        
        if hist.empty:
            return {}
        
        # Calculate monthly metrics
        monthly_open = hist['Open'].iloc[0]
        monthly_close = hist['Close'].iloc[-1]
        monthly_high = hist['High'].max()
        monthly_low = hist['Low'].min()
        monthly_volume = hist['Volume'].sum()
        monthly_change = (monthly_close - monthly_open) / monthly_open * 100
        
        return {
            "price": float(monthly_close),
            "change": float(monthly_change),
            "volume": int(monthly_volume)
        }
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return {}

def update_stock_data(file_path: str):
    # Read the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Iterate through each month and stock
    for month, stocks in data.items():
        for symbol in stocks.keys():
            # Get stock data
            stock_data = get_price(symbol, month)
            
            if stock_data:
                # Update existing data, keep original news
                data[month][symbol]["stock"] = stock_data
    
    # Write back to the JSON file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)