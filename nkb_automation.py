#!/usr/bin/env python3
"""
NKB Close Cash Report Generator v2 - DEBUG VERSION
Shows full error details
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import traceback

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

def get_gspread_client():
    """Authenticate with Google Sheets"""
    creds_json = os.getenv("GOOGLE_SHEETS_CREDS")
    if not creds_json:
        raise ValueError("GOOGLE_SHEETS_CREDS not set")
    
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return gspread.authorize(creds)

def fetch_store_data(gc, store_name, sheet_id):
    """Fetch today's close cash data from one store's Google Sheet"""
    try:
        print(f"  🔑 Using sheet ID: {sheet_id}")
        spreadsheet = gc.open_by_key(sheet_id)
        print(f"  ✅ Opened sheet successfully")
        
        worksheet = spreadsheet.sheet1
        rows = worksheet.get_all_records()
        
        if not rows:
            print(f"⚠️  {store_name}: No data in sheet")
            return None
        
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).strftime("%d-%m-%Y")
        
        today_data = None
        for row in rows:
            if row.get("DATE", "").strip() == today:
                today_data = row
                break
        
        if not today_data:
            print(f"⚠️  {store_name}: No entry for {today}")
            return {
                "store_name": store_name,
                "date": today,
                "cash": "—",
                "card": "—",
                "upi": "—",
                "sale": "—",
                "expense": "—",
                "remark": "No entry"
            }
        
        return {
            "store_name": store_name,
            "date": today,
            "cash": today_data.get("CASH", "") or "0",
            "card": today_data.get("Swip m/c", "") or today_data.get("Card", "") or "0",
            "upi": today_data.get("UPI", "") or "0",
            "sale": today_data.get("SALE", "") or "0",
            "expense": today_data.get("EXP.", "") or today_data.get("Expense", "") or "0",
            "remark": today_data.get("Exp REMARK", "") or today_data.get("Remark", "") or ""
        }
    
    except Exception as e:
        print(f"❌ {store_name}: DETAILED ERROR")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        traceback.print_exc()
        return None

def fetch_all_stores_data(gc):
    """Fetch data from all 13 stores"""
    all_data = []
    
    for store_name, sheet_id in STORES.items():
        print(f"\n📄 Reading {store_name}...")
        data = fetch_store_data(gc, store_name, sheet_id)
        if data:
            all_data.append(data)
    
    return all_data

def generate_report():
    """Main function to generate and send report"""
    print("\n🚀 Starting NKB Close Cash Report Generation...\n")
    
    try:
        print("🔗 Connecting to Google Sheets...")
        gc = get_gspread_client()
        print("✅ Connected to Google Sheets\n")
        
        print("📚 Fetching data from all 13 stores...\n")
        stores_data = fetch_all_stores_data(gc)
        
        print(f"\n✅ Fetched data from {len(stores_data)} stores")
        
        if not stores_data:
            print("❌ No data fetched from any store")
            return False
        
        print("\n✅ Report generation complete!")
        return True
    
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_report()
