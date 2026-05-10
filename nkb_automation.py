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

def fetch_all_stores():
    gc = get_gspread_client()
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.now(ist).strftime("%d-%m-%Y")
    
    report_data = []
    total_cash = total_card = total_upi = total_sale = total_expense = 0
    
    for store_name, sheet_id in STORES.items():
        try:
            spreadsheet = gc.open_by_key(sheet_id)
            rows = spreadsheet.sheet1.get_all_records()
            today_row = next((r for r in rows if r.get("DATE", "").strip() == today), None)
            
            if today_row:
                cash = float(today_row.get("CASH", 0) or 0)
                card = float(today_row.get("Swip m/c", today_row.get("Card", 0)) or 0)
                upi = float(today_row.get("UPI", 0) or 0)
                sale = float(today_row.get("SALE", 0) or 0)
                expense = float(today_row.get("EXP.", today_row.get("Expense", 0)) or 0)
                remark = today_row.get("Exp REMARK", today_row.get("Remark", ""))
                
                total_cash += cash
                total_card += card
                total_upi += upi
                total_sale += sale
                total_expense += expense
                
                report_data.append({
                    "store": store_name,
                    "cash": cash,
                    "card": card,
                    "upi": upi,
                    "sale": sale,
                    "expense": expense,
                    "remark": remark
                })
            else:
                report_data.append({"store": store_name, "cash": 0, "card": 0, "upi": 0, "sale": 0, "expense": 0, "remark": "No entry"})
        except Exception as e:
            print(f"Error reading {store_name}: {e}")
            report_data.append({"store": store_name, "cash": 0, "card": 0, "upi": 0, "sale": 0, "expense": 0, "remark": f"Error: {str(e)[:30]}"})
    
    return today, report_data, total_cash, total_card, total_upi, total_sale, total_expense

def generate_report_text(today, report_data, total_cash, total_card, total_upi, total_sale, total_expense):
    report = f"""📊 NKB DAILY CLOSE CASH REPORT
Date: {today}

{"="*80}

STORE-BY-STORE BREAKDOWN:

"""
    
    for item in report_data:
        report += f"{item['store']}\n"
        report += f"  Cash: ₹{item['cash']:.0f} | Card: ₹{item['card']:.0f} | UPI: ₹{item['upi']:.0f}\n"
        report += f"  Sale: ₹{item['sale']:.0f} | Expense: ₹{item['expense']:.0f}\n"
        if item['remark']:
            report += f"  Note: {item['remark']}\n"
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
        
        print("✅ Email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def generate_report():
    print("\n🚀 Generating Report...\n")
    try:
        today, report_data, total_cash, total_card, total_upi, total_sale, total_expense = fetch_all_stores()
        report_text = generate_report_text(today, report_data, total_cash, total_card, total_upi, total_sale, total_expense)
        print(report_text)
        send_email(report_text)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_report()
