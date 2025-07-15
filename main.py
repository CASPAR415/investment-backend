import json
from utils.prompt import Prompts
import os
from utils.functions import (
    init_state,
    buy_stock,
    sell_stock,
    chat,
    get_news,
    get_holdings,
    get_price,
    update_date
)

def main():
    # Initialize paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    HOLDINGS_FILE = os.path.join(BASE_DIR, "data", "holding_state.json")
    DATA_FILE = os.path.join(BASE_DIR, "data", "company_data.json")
    
    # Get user's investment personality
    personality = input("Enter your investment personality/style (e.g. 'conservative long-term investor'): ")
    system_prompt = Prompts.get_personality(personality)
    date = input("Enter initial month-year (YYYY-MM): ")
    
    # Initialize portfolio with $10,000
    if not os.path.exists(HOLDINGS_FILE):
        init_state(HOLDINGS_FILE, 10000.00)
        print("Portfolio initialized with $10,000")
    
    while True:
        print("\n--- Investment Advisor Menu ---")
        print(f"Current Date: {date}")
        print("\n1. Get investment advice for a month")
        print("2. Execute trade")
        print("3. View current holdings")
        print("4. View monthly price data for all companies")
        print("5. Update to next month")
        print("6. Exit")
        choice = input("Select an option: ")
        
        if choice == "1":
            # Get advice for specific month
            news = get_news(DATA_FILE, date)
            holdings = get_holdings(HOLDINGS_FILE)
            
            advice_prompt = Prompts.get_advice_prompt(news, holdings)
            response = chat(system_prompt, advice_prompt)
            
            try:
                recommendations = json.loads(response.choices[0].message.content)
                print("\nInvestment Recommendations:")
                for rec in recommendations.get("recommendations", []):
                    print(f"{rec['company']}: {rec['action'].upper()} {rec['shares_to_transact']} shares")
                    print(f"Reason: {rec['reason']}")
                    print(f"Confidence: {rec['confidence']}\n")
            except Exception as e:
                print(f"Error processing recommendations: {e}")
                
        elif choice == "2":
            # Execute a trade
            symbol = input("Enter stock symbol: ").upper()
            action = input("Buy or Sell? ").lower()
            quantity = int(input("Number of shares: "))
            
            # Get latest price
            price_data = get_price(symbol, date)
            if not price_data:
                print("Could not find price data for this stock")
                continue
                
            price = float(price_data['price'])
            
            try:
                if action == "buy":
                    buy_stock(HOLDINGS_FILE, symbol, quantity, price, date)
                    print(f"Bought {quantity} shares of {symbol} at ${price:.2f}")
                elif action == "sell":
                    sell_stock(HOLDINGS_FILE, symbol, quantity, price, date)
                    print(f"Sold {quantity} shares of {symbol} at ${price:.2f}")
                else:
                    print("Invalid action")
            except ValueError as e:
                print(f"Error executing trade: {e}")
                
        elif choice == "3":
            # View current holdings
            print("\nCurrent Portfolio:")
            print(get_holdings(HOLDINGS_FILE))
            
        elif choice == "4":
            # View monthly price data for all companies
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                if date not in data:
                    print(f"No data found for {date}")
                    continue
                
                print(f"\nMonthly Price Data for {date}:")
                for company, info in data[date].items():
                    price = info.get('stock', {}).get('price', 'N/A')
                    change = info.get('stock', {}).get('change', 'N/A')
                    volume = info.get('stock', {}).get('volume', 'N/A')
                    print(f"{company}:\n  price: ${price}\n  change: {change}\n  volume: {volume}")

            except Exception as e:
                print(f"Error loading price data: {e}")
        
        elif choice == "5":
            date = update_date(date)
            print(f"Updated date to {date}")
            if date >= "2024-12":
                print("You have reached the end of the simulation period.")
                break

        elif choice == "6":
            break
            
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()

