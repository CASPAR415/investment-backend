import json
import yfinance as yf
from datetime import datetime
import os

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
    
def main():
    # Update stock data in the JSON file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    JSON_FILE = os.path.join(BASE_DIR, "company_data.json")
    update_stock_data(JSON_FILE)
if __name__ == "__main__":
    main()