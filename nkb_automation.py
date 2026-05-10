#!/usr/bin/env python3
"""
NKB Style Brands - Close Cash Report Automation (Simplified)
Reads all 13 Google Sheets, analyzes with Claude, sends email
"""

import gspread
from google.oauth2.service_account import Credentials
import os
from anthropic import Anthropic
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
import json
import pytz
from io import BytesIO
from datetime import datetime

# ============ CONFIGURATION ============
GOOGLE_SHEETS_CREDS_JSON = os.getenv('GOOGLE_SHEETS_CREDS')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
GMAIL_EMAIL = 'nkblifestylebrands@gmail.com'
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# 13 Store sheets
STORE_SHEETS = [
    'COTTONKING Dadar E',
    'CK Capital Mall',
    'CK Maxus Mall',
    'CK MN (S)',
    'CK Nalasopara W',
    'Cottonking Dhule',
    'COTTONKING Indiranagar',
    'COTTONKING Panchwati',
    'Cottonking Pathdi. Ph.',
    'DADAR West',
    'Tyzer IndiraNagar',
    'Tyzer Panchwati',
    'Tyzer Shalimar'
]

MASTER_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1P6bn4_dG08OWFBixI8Jv4IlOZ87ahB_u4byWZwXAYRg/edit'

# ============ GOOGLE SHEETS CONNECTION ============
def connect_google_sheets():
    """Connect to Google Sheets using service account"""
    creds_dict = json.loads(GOOGLE_SHEETS_CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return gspread.authorize(creds)

# ============ FETCH DATA FROM SHEETS ============
def fetch_store_data(gc, spreadsheet_url):
    """Fetch today's close cash data from all 13 stores"""
    try:
        spreadsheet = gc.open_by_url(spreadsheet_url)
    except:
        sheet_key = spreadsheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = gc.open_by_key(sheet_key)
    
    stores_data = []
    
    for store_name in STORE_SHEETS:
        try:
            worksheet = spreadsheet.worksheet(store_name)
            all_data = worksheet.get_all_values()
            
            # Find header row
            header_row = None
            for i, row in enumerate(all_data):
                if 'DATE' in [cell.upper() for cell in row] or 'date' in [cell.lower() for cell in row]:
                    header_row = i
                    headers = [cell.strip() for cell in row]
                    break
            
            if header_row is None:
                continue
            
            # Get latest row
            latest_row = None
            for row in reversed(all_data[header_row+1:]):
                if row and row[0].strip():
                    latest_row = row
                    break
            
            if not latest_row:
                continue
            
            # Parse row
            row_dict = {}
            for j, header in enumerate(headers):
                if j < len(latest_row):
                    row_dict[header.strip()] = latest_row[j].strip()
            
            # Extract values
            cash = float(row_dict.get('CASH', '0').replace(',', '')) if row_dict.get('CASH') else 0
            card = float(row_dict.get('Swip m/c', '0').replace(',', '')) if row_dict.get('Swip m/c') else 0
            upi = float(row_dict.get('UPI', '0').replace(',', '')) if row_dict.get('UPI') else 0
            sale = float(row_dict.get('SALE', '0').replace(',', '')) if row_dict.get('SALE') else 0
            exp = float(row_dict.get('EXP.', '0').replace(',', '')) if row_dict.get('EXP.') else 0
            exp_remark = row_dict.get('Exp REMARK', '')
            
            stores_data.append({
                'store': store_name,
                'cash': cash,
                'card': card,
                'upi': upi,
                'sale': sale,
                'exp': exp,
                'exp_remark': exp_remark,
                'date': row_dict.get('DATE', '')
            })
        
        except Exception as e:
            print(f"Error fetching {store_name}: {str(e)}")
            continue
    
    return stores_data

# ============ GENERATE HTML TABLE ============
def generate_html_table(stores_data):
    """Generate HTML table of close cash data"""
    if not stores_data:
        return ""
    
    total_cash = sum(s['cash'] for s in stores_data)
    total_card = sum(s['card'] for s in stores_data)
    total_upi = sum(s['upi'] for s in stores_data)
    total_sale = sum(s['sale'] for s in stores_data)
    total_exp = sum(s['exp'] for s in stores_data)
    
    html = """
    <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
    <tr style="background: #B8690A; color: white;">
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">STORE</th>
        <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">CASH</th>
        <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">CARD</th>
        <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">UPI</th>
        <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">SALE</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">EXP / REMARK</th>
    </tr>
    """
    
    for store in stores_data:
        html += f"""
    <tr style="background: #f9f9f9;">
        <td style="padding: 8px; border: 1px solid #ddd;">{store['store']}</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">₹{store['cash']:,.0f}</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">₹{store['card']:,.0f}</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">₹{store['upi']:,.0f}</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right; color: green; font-weight: bold;">₹{store['sale']:,.0f}</td>
        <td style="padding: 8px; border: 1px solid #ddd; color: #d9534f;">-₹{store['exp']:,.0f} {store['exp_remark']}</td>
    </tr>
    """
    
    html += f"""
    <tr style="background: #B8690A; color: white; font-weight: bold;">
        <td style="padding: 10px; border: 1px solid #ddd;">TOTAL</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">₹{total_cash:,.0f}</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">₹{total_card:,.0f}</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">₹{total_upi:,.0f}</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">₹{total_sale:,.0f}</td>
        <td style="padding: 10px; border: 1px solid #ddd;">-₹{total_exp:,.0f}</td>
    </tr>
    </table>
    """
    
    return html

# ============ CLAUDE ANALYSIS ============
def analyze_with_claude(stores_data):
    """Use Claude API to analyze store performance"""
    client = Anthropic()
    
    data_text = "Store Performance Data:\n\n"
    for store in sorted(stores_data, key=lambda x: x['sale'], reverse=True):
        data_text += f"{store['store']}: Sale ₹{store['sale']:,.0f} | Cash ₹{store['cash']:,.0f} | Card ₹{store['card']:,.0f} | UPI ₹{store['upi']:,.0f} | Expense ₹{store['exp']:,.0f}\n"
    
    prompt = f"""{data_text}

Please provide analysis with:
1. **Top 5 & Bottom 5 stores** by sales
2. **Underperformance alerts** (stores below average)
3. **Expense analysis** (unusual spikes)
4. **Payment methods** (cash vs card vs UPI breakdown)
5. **Key insights** (3-4 actionable points)

Keep it concise and professional."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

# ============ EMAIL DELIVERY ============
def send_email_report(stores_data, analysis):
    """Send email with report and analysis"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"NKB Close Cash Report - {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y')}"
        msg['From'] = GMAIL_EMAIL
        msg['To'] = 'nkblifestylebrands@gmail.com'
        msg['Date'] = formatdate(localtime=True)
        
        # Generate HTML table
        html_table = generate_html_table(stores_data)
        
        # Summary stats
        total_sale = sum(s['sale'] for s in stores_data)
        total_cash = sum(s['cash'] for s in stores_data)
        total_card = sum(s['card'] for s in stores_data)
        total_upi = sum(s['upi'] for s in stores_data)
        total_exp = sum(s['exp'] for s in stores_data)
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; background: #f5f5f5;">
        <div style="max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px;">
        
        <h2 style="color: #B8690A; border-bottom: 3px solid #B8690A; padding-bottom: 10px;">
            📊 NKB Style Brands - Daily Close Cash Report
        </h2>
        
        <p style="color: #666; font-size: 14px;">
            <strong>Report Date:</strong> {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%A, %d %b %Y at %I:%M %p IST')}
        </p>
        
        <div style="background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3 style="color: #B8690A; margin-top: 0;">📈 Quick Summary</h3>
        <p>
            <strong>Total Sale:</strong> ₹{total_sale:,.0f}<br>
            <strong>Cash Collected:</strong> ₹{total_cash:,.0f}<br>
            <strong>Card:</strong> ₹{total_card:,.0f}<br>
            <strong>UPI:</strong> ₹{total_upi:,.0f}<br>
            <strong>Total Expenses:</strong> ₹{total_exp:,.0f}
        </p>
        </div>
        
        <h3 style="color: #B8690A;">📋 All Stores Report</h3>
        {html_table}
        
        <h3 style="color: #B8690A; margin-top: 30px;">🔍 Claude AI Analysis</h3>
        <div style="background: #f9f9f9; padding: 15px; border-left: 4px solid #B8690A; border-radius: 3px;">
        <pre style="white-space: pre-wrap; font-family: Arial; font-size: 13px; color: #333;">{analysis}</pre>
        </div>
        
        <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px;">
            <em>Automated report generated by NKB Close Cash Report System</em>
        </p>
        </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False

# ============ MAIN EXECUTION ============
def generate_report():
    """Main function"""
    print("🚀 Starting NKB Close Cash Report Generation...")
    
    try:
        gc = connect_google_sheets()
        print("✅ Connected to Google Sheets")
        
        stores_data = fetch_store_data(gc, MASTER_SHEET_URL)
        if not stores_data:
            print("❌ No data found!")
            return False
        
        print(f"✅ Fetched data from {len(stores_data)} stores")
        
        analysis = analyze_with_claude(stores_data)
        print("✅ Claude analysis complete")
        
        send_email_report(stores_data, analysis)
        print("✅ Report generation complete!")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    generate_report()
