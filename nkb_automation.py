#!/usr/bin/env python3
"""
NKB Close Cash Report Generator - PRODUCTION
Reads from 13 individual Google Sheets → Claude API → Sends email
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
    try:
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        rows = worksheet.get_all_records()
        
        if not rows:
            return None
        
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).strftime("%d-%m-%Y")
        
        today_data = None
        for row in rows:
            if row.get("DATE", "").strip() == today:
                today_data = row
                break
        
        if not today_data:
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
        print(f"❌ {store_name}: Error fetching data - {e}")
        return None

def fetch_all_stores_data(gc):
    all_data = []
    
    for store_name, sheet_id in STORES.items():
        print(f"📄 Reading {store_name}...")
        data = fetch_store_data(gc, store_name, sheet_id)
        if data:
            all_data.append(data)
    
    return all_data

def generate_report_with_claude(stores_data):
    client = Anthropic()
    
    data_text = "CLOSE CASH REPORT - " + datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y") + "\n\n"
    
    for store in stores_data:
        data_text += f"{store['store_name']}:\n"
        data_text += f"  Cash: ₹{store['cash']} | Card: ₹{store['card']} | UPI: ₹{store['upi']}\n"
        data_text += f"  Sale: ₹{store['sale']} | Expense: ₹{store['expense']}\n"
        if store['remark']:
            data_text += f"  Remark: {store['remark']}\n"
        data_text += "\n"
    
    prompt = f"""You are Harshal's business operations assistant. You have received close cash data from 13 retail stores.

{data_text}

Create a professional, concise DAILY REPORT for the directors (Harshal, Kapil, Kamlakar) in this format:

📊 DAILY CLOSE CASH REPORT
Date: [today]

🏪 STORE SUMMARY
[List all 13 stores with their key metrics in a clean format]

⚠️ FLAGS & ALERTS
[Note any stores with unusually high/low sales, missing data, or high expenses]

💰 TOTALS
[Sum of all cash, card, UPI, sales, expenses]

📝 KEY NOTES
[Any patterns or observations worth noting]

Keep it professional, clear, and actionable. Use emojis sparingly for emphasis."""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

def send_email(report_text):
    sender_email = "nkblifestylebrands@gmail.com"
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    
    recipients = [
        "nkblifestylebrands@gmail.com",
        "harshal@nkb.in",
        "kapil@nkb.in",
        "kamlakar@nkb.in"
    ]
    
    if not app_password:
        print("❌ GMAIL_APP_PASSWORD not set")
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"NKB Daily Close Cash Report - {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y')}"
        
        msg.attach(MIMEText(report_text, "plain"))
        
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {len(recipients)} recipients")
        return True
    
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def generate_report():
    print("\n🚀 Starting NKB Close Cash Report Generation...\n")
    
    try:
        print("🔗 Connecting to Google Sheets...")
        gc = get_gspread_client()
        print("✅ Connected to Google Sheets\n")
        
        print("📚 Fetching data from all 13 stores...\n")
        stores_data = fetch_all_stores_data(gc)
        
        if not stores_data:
            print("❌ No data fetched from any store")
            return False
        
        print(f"✅ Fetched data from {len(stores_data)} stores\n")
        
        print("🤖 Generating report with Claude AI...\n")
        report = generate_report_with_claude(stores_data)
        print("✅ Report generated\n")
        print("------- REPORT PREVIEW -------")
        print(report)
        print("------------------------------\n")
        
        print("📧 Sending email...\n")
        result = send_email(report)
        
        if result:
            print("\n✅ Daily report generation and email complete!")
        else:
            print("\n⚠️  Report generated but email failed")
        
        return result
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_report()
