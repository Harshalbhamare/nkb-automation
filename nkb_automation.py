#!/usr/bin/env python3
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import pytz
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

def get_gspread_client():
    creds_json = os.getenv("GOOGLE_SHEETS_CREDS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return gspread.authorize(creds)

def safe_float(value):
    """Safely convert value to float"""
    try:
        if value is None or value == "":
            return 0.0
        val_str = str(value).strip()
        if not val_str:
            return 0.0
        return float(val_str)
    except:
        return 0.0

def parse_date(date_str):
    """Parse date in DD/MM/YYYY format"""
    try:
        date_str = str(date_str).strip()
        if not date_str or len(date_str) < 8:
            return None
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except:
        return None

def date_in_range(date_str, start_date, end_date):
    """Check if date falls in range (DD/MM/YYYY vs DD-MM-YYYY format)"""
    parsed_date = parse_date(date_str)
    if parsed_date is None:
        return False
    
    try:
        start_obj = datetime.strptime(start_date, '%d-%m-%Y').date()
        end_obj = datetime.strptime(end_date, '%d-%m-%Y').date()
        return start_obj <= parsed_date <= end_obj
    except:
        return False

def fetch_stores_by_date(start_date, end_date):
    """Fetch data from all stores for given date range using positional column indexing"""
    cache_key = f"{start_date}_{end_date}"
    
    if cache_key in CACHE:
        cached_time, cached_data = CACHE[cache_key]
        if time.time() - cached_time < 3600:
            return cached_data
    
    print(f"\n🔄 Fetching data for {start_date} to {end_date}...")
    
    report_data = []
    total_cash = total_card = total_upi = total_sale = total_expense = 0
    
    gc = get_gspread_client()
    
    for idx, (store_name, sheet_id) in enumerate(STORES.items(), 1):
        try:
            print(f"  [{idx}/13] {store_name}...", end="", flush=True)
            
            spreadsheet = gc.open_by_key(sheet_id)
            all_values = spreadsheet.sheet1.get_all_values()
            
            if not all_values or len(all_values) < 2:
                print(f" (no data)")
                report_data.append({
                    "store": store_name,
                    "cash": 0, "card": 0, "upi": 0, "sale": 0, "expense": 0,
                    "entries": 0
                })
                if idx < len(STORES):
                    time.sleep(0.5)
                continue
            
            store_cash = store_card = store_upi = store_sale = store_expense = 0
            store_entries = 0
            
            # Skip header row (row 0), process all data rows
            for row in all_values[1:]:
                if len(row) < 9:
                    continue
                
                date_val = row[0]
                
                if date_in_range(date_val, start_date, end_date):
                    # Column positions: A=0(date), B=1(op.bal), C=2(cash), D=3(card), E=4(upi), F=5(sale), G=6(bank), H=7(expense)
                    cash = safe_float(row[2])
                    card = safe_float(row[3])
                    upi = safe_float(row[4])
                    sale = safe_float(row[5])
                    expense = safe_float(row[7])
                    
                    store_cash += cash
                    store_card += card
                    store_upi += upi
                    store_sale += sale
                    store_expense += expense
                    store_entries += 1
            
            total_cash += store_cash
            total_card += store_card
            total_upi += store_upi
            total_sale += store_sale
            total_expense += store_expense
            
            if store_entries > 0:
                print(f" ✓ {store_entries} entries: ₹{store_sale:,.0f}")
            else:
                print(f" (no data)")
            
            report_data.append({
                "store": store_name,
                "cash": store_cash,
                "card": store_card,
                "upi": store_upi,
                "sale": store_sale,
                "expense": store_expense,
                "entries": store_entries
            })
            
            if idx < len(STORES):
                time.sleep(0.5)
        
        except Exception as e:
            print(f" ❌ Error: {str(e)}")
            report_data.append({
                "store": store_name,
                "cash": 0, "card": 0, "upi": 0, "sale": 0, "expense": 0,
                "entries": 0
            })
    
    result = (start_date, report_data, total_cash, total_card, total_upi, total_sale, total_expense)
    CACHE[cache_key] = (time.time(), result)
    
    return result
