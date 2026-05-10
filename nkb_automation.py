#!/usr/bin/env python3
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()

STORES = {
    "CK Capital Mall": "1TGHLTtylkANWkWClWBigP0d3Cb0wAoHm3aHIYKJ48Hg",
    "CK Maxus Mall": "1ZFOt95ZM97F2BSxtgNW_8ScNlGQH26ZKSh3spYa53jM",
    "CK MN (S)": "1fOg47nqANKUlE25I3bP1cY-mYrrNETTSStvDiXbXpXU",
    "CK Nalasopara W": "1tKbIWs4ipKFLCsW5tnBoHd2YRERXKGG0WuLUi8Yyq7U",
    "COTTONKING Dadar E": "1P6bn4_dG08OWFBixI8Jv4IlOZ87ahB_u4byWZwXAYRg",
    "Cottonking Dhule": "1IcUsFEtd9BsvIbvt-82enDyaS-Z2M4whvIWQfl5Gzgg",
    "COTTONKING Indiranagar": "19Jfi1O8OuRTjEGMHKQgecFwSTLhVYa8RqA6y5ZUXARg",
    "COTTONKING Panchwati": "1QN53i3T85yTAOz0bDQb6m9yIXf_i-9Avce_t1SxnIno",
    "Cottonking Pathdi. Ph.": "1MnwPX5LS-E4BCHJVl7IyWsGh5JNiWLEnZa4ShgY3R98",
    "DADAR West": "1cxwUXz7AQadsHPDoA7zbsGFWmFXGN4iodwh1kTq3ais",
    "Tyzer IndiraNagar": "1g25Mp8rLs-u_Wno_LePx-3FY8knvjgCxT1gqtNXMiGs",
    "Tyzer Panchwati": "1yd0w8xEQOdrP2BWK5B3jmGSW_mgO2lbTU1T1h0gOPHk",
    "Tyzer Shalimar": "1xKoldJMdxjBaExMPNRVpEznWkutkaUHX-B7ml2GGCXQ"
}

CACHE = {}
CACHE_EXPIRY = 600  # 10 minutes

def get_gspread_client():
    creds_json = os.getenv("GOOGLE_SHEETS_CREDS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return gspread.authorize(creds)

def date_in_range(date_str, start_date, end_date):
    try:
        date_obj = datetime.strptime(date_str.strip(), '%d/%m/%Y')
        start_obj = datetime.strptime(start_date, '%d-%m-%Y')
        end_obj = datetime.strptime(end_date, '%d-%m-%Y')
        return start_obj <= date_obj <= end_obj
    except:
        return False

def fetch_single_store(store_name, sheet_id, start_date, end_date):
    """Fetch data from a single store - used for concurrent execution"""
    try:
        gc = get_gspread_client()
        spreadsheet = gc.open_by_key(sheet_id)
        rows = spreadsheet.sheet1.get_all_records()
        
        store_cash = store_card = store_upi = store_sale = store_expense = 0
        store_entries = 0
        
        for row in rows:
            date_val = row.get("DATE", "").strip()
            if date_in_range(date_val, start_date, end_date):
                try:
                    cash = float(row.get("CASH", 0) or 0)
                    card = float(row.get("Swip m/c", row.get("Card", 0)) or 0)
                    upi = float(row.get("UPI", 0) or 0)
                    sale = float(row.get("SALE", 0) or 0)
                    expense = float(row.get("EXP.", row.get("Expense", 0)) or 0)
                    
                    store_cash += cash
                    store_card += card
                    store_upi += upi
                    store_sale += sale
                    store_expense += expense
                    store_entries += 1
                except:
                    pass
        
        return {
            "store": store_name,
            "cash": store_cash,
            "card": store_card,
            "upi": store_upi,
            "sale": store_sale,
            "expense": store_expense,
            "entries": store_entries
        }
    except Exception as e:
        print(f"Error reading {store_name}: {str(e)[:100]}")
        return {
            "store": store_name,
            "cash": 0, "card": 0, "upi": 0, "sale": 0, "expense": 0,
            "entries": 0
        }

def fetch_stores_by_date(start_date, end_date):
    """Fetch all stores concurrently - MUCH faster"""
    
    # Check cache
    cache_key = f"{start_date}_{end_date}"
    if cache_key in CACHE:
        cached_time, cached_data = CACHE[cache_key]
        if time.time() - cached_time < CACHE_EXPIRY:
            print(f"✓ Using cached data for {cache_key}")
            return cached_data
    
    print(f"⏳ Fetching fresh data for {cache_key}...")
    
    report_data = []
    total_cash = total_card = total_upi = total_sale = total_expense = 0
    
    # Use ThreadPoolExecutor for concurrent reads (all 13 at once)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(fetch_single_store, store_name, sheet_id, start_date, end_date): store_name
            for store_name, sheet_id in STORES.items()
        }
        
        for future in as_completed(futures):
            try:
                item = future.result(timeout=30)
                report_data.append(item)
                total_cash += item['cash']
                total_card += item['card']
                total_upi += item['upi']
                total_sale += item['sale']
                total_expense += item['expense']
            except Exception as e:
                print(f"Error: {e}")
    
    # Sort by store name for consistency
    report_data.sort(key=lambda x: x['store'])
    
    result = (start_date, report_data, total_cash, total_card, total_upi, total_sale, total_expense)
    
    # Cache it
    CACHE[cache_key] = (time.time(), result)
    print(f"✓ Data cached for {cache_key}")
    
    return result

def generate_report_text(start_date, end_date, report_data, total_cash, total_card, total_upi, total_sale, total_expense):
    date_range = start_date if start_date == end_date else f"{start_date} to {end_date}"
    
    report = f"""📊 NKB DAILY CLOSE CASH REPORT
Date Range: {date_range}

{"="*80}

STORE-BY-STORE BREAKDOWN:

"""
    
    for item in report_data:
        report += f"{item['store']}\n"
        if item['entries'] > 0:
            report += f"  Cash: ₹{item['cash']:,.0f} | Card: ₹{item['card']:,.0f} | UPI: ₹{item['upi']:,.0f}\n"
            report += f"  Sale: ₹{item['sale']:,.0f} | Expense: ₹{item['expense']:,.0f}\n"
        else:
            report += f"  No data for this date\n"
        report += "\n"
    
    report += f"""{"="*80}

TOTALS:
  Total Cash: ₹{total_cash:,.0f}
  Total Card: ₹{total_card:,.0f}
  Total UPI: ₹{total_upi:,.0f}
  Total Sale: ₹{total_sale:,.0f}
  Total Expense: ₹{total_expense:,.0f}

Net Collection: ₹{(total_cash + total_card + total_upi):,.0f}

{"="*80}

Report generated at: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M:%S IST')}
"""
    
    return report
