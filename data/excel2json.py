import json
import pandas as pd
from datetime import datetime
import os

def update_news_from_excel(json_file_path, excel_file_path):
    # Read the existing JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Read the Excel file
    try:
        df = pd.read_excel(excel_file_path)
        print(f"Successfully read Excel file: {excel_file_path}")
        print(f"Found {len(df)} news records")
    except Exception as e:
        print(f"Failed to read Excel file: {e}")
        return
    
    # Process each row of news data
    for index, row in df.iterrows():
        enterprise = row['Enterprise']
        title = row['Title']
        date = row['Date']
        link = row['Link']
        
        # Ensure the date is in string format
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = str(date)
        
        # Extract year and month from the date as the key
        year_month = date_str[:7]  # Format: "YYYY-MM"
        
        # Create news object
        news_item = {
            "title": title,
            "date": date_str,
            "source": link
        }
        
        # Check if the month already exists in the JSON data
        if year_month not in data:
            data[year_month] = {}
        
        # Check if the enterprise already exists in that month
        if enterprise not in data[year_month]:
            data[year_month][enterprise] = {
                "news": [],
                "stock": {}  # Initialize as empty dict
            }
        
        # Check for duplicate news (avoid duplicates)
        existing_news = data[year_month][enterprise]["news"]
        duplicate = False
        for item in existing_news:
            if item["title"] == title and item["source"] == link:
                duplicate = True
                break
        
        # Add new news if not duplicate
        if not duplicate:
            existing_news.append(news_item)
            print(f"Added news: {year_month} | {enterprise} | {title}")
    
    # Write the updated data back to the JSON file
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Successfully updated JSON file: {json_file_path}")
    print(f"Total number of months: {len(data)}")
    
    # Count total number of news
    total_news = 0
    for month_data in data.values():
        for company_data in month_data.values():
            total_news += len(company_data["news"])
    
    print(f"Total number of news: {total_news}")

# Example usage
if __name__ == "__main__":
    # Define file paths
    excel_name = "tesla_news_2020_verified.xlsx"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXCEL_FILE = os.path.join(BASE_DIR, excel_name)
    JSON_FILE = os.path.join(BASE_DIR, "company_data.json")
    update_news_from_excel(JSON_FILE, EXCEL_FILE)