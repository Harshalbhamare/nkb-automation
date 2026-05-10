#!/usr/bin/env python3
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import requests

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
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return gspread.authorize(creds)

def fetch_store_data(gc, store_name, sheet_id):
    try:
        spreadsheet = gc.open_by_key(sheet_id)
        rows = spreadsheet.sheet1.get_all_records()
        
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).strftime("%d-%m-%Y")
        
        today_data = next((row for row in rows if row.get("DATE", "").strip() == today), None)
        
        if not today_data:
            return {"store_name": store_name, "date": today, "cash": "—", "card": "—", "upi": "—", "sale": "—", "expense": "—", "remark": "No entry"}
        
        return {
            "store_name": store_name,
            "date": today,
            "cash": str(today_data.get("CASH", "") or "0"),
            "card": str(today_data.get("Swip m/c", "") or today_data.get("Card", "") or "0"),
            "upi": str(today_data.get("UPI", "") or "0"),
            "sale": str(today_data.get("SALE", "") or "0"),
            "expense": str(today_data.get("EXP.", "") or today_data.get("Expense", "") or "0"),
            "remark": str(today_data.get("Exp REMARK", "") or today_data.get("Remark", "") or "")
        }
    except Exception as e:
        print(f"❌ {store_name}: {e}")
        return None

def fetch_all_stores_data(gc):
    all_data = []
    for store_name, sheet_id in STORES.items():
        print(f"📄 {store_name}")
        data = fetch_store_data(gc, store_name, sheet_id)
        if data:
            all_data.append(data)
    return all_data

def generate_report_with_claude(stores_data):
    api_key = os.getenv("CLAUDE_API_KEY")
    
    data_text = f"CLOSE CASH REPORT - {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y')}\n\n"
    for store in stores_data:
        data_text += f"{store['store_name']}: Cash ₹{store['cash']} | Card ₹{store['card']} | UPI ₹{store['upi']} | Sale ₹{store['sale']} | Expense ₹{store['expense']}\n"
    
    prompt = f"Analyze this close cash data and create a brief professional report:\n\n{data_text}"
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    
    if response.status_code == 200:
        return response.json()["content"][0]["text"]
    else:
        print(f"Claude API Error: {response.status_code} - {response.text}")
        return "Report generation failed"

def send_email(report_text):
    sender = "nkblifestylebrands@gmail.com"
    password = os.getenv("GMAIL_APP_PASSWORD")
    recipients = ["nkblifestylebrands@gmail.com", "harshal@nkb.in", "kapil@nkb.in", "kamlakar@nkb.in"]
    
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"NKB Daily Close Cash - {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y')}"
        msg.attach(MIMEText(report_text, "plain"))
        
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent")
        return True
    except Exception as e:
        print(f"❌ Email: {e}")
        return False

def generate_report():
    print("\n🚀 Starting Report Generation...\n")
    try:
        gc = get_gspread_client()
        stores_data = fetch_all_stores_data(gc)
        report = generate_report_with_claude(stores_data)
        print(report)
        send_email(report)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    generate_report()
