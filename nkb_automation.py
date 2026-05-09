#!/usr/bin/env python3
"""
NKB Style Brands - Close Cash Report Automation
Reads all 13 Google Sheets, generates report, analyzes with Claude, sends email
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
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
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ============ CONFIGURATION ============
GOOGLE_SHEETS_CREDS_JSON = os.getenv('GOOGLE_SHEETS_CREDS')  # Paste JSON as env var
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')  # Your API key
GMAIL_EMAIL = 'nkblifestylebrands@gmail.com'
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')  # Generate at myaccount.google.com/apppasswords

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
        # Fallback: try opening by key
        sheet_key = spreadsheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = gc.open_by_key(sheet_key)
    
    stores_data = []
    today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d/%m/%Y')
    
    for store_name in STORE_SHEETS:
        try:
            worksheet = spreadsheet.worksheet(store_name)
            all_data = worksheet.get_all_values()
            
            # Find header row (contains "DATE", "CASH", "UPI", "SALE", etc.)
            header_row = None
            data_rows = []
            for i, row in enumerate(all_data):
                if 'DATE' in [cell.upper() for cell in row] or 'date' in [cell.lower() for cell in row]:
                    header_row = i
                    headers = [cell.strip() for cell in row]
                    break
            
            if header_row is None:
                continue
            
            # Get today's data (last row with data, or search for today's date)
            latest_row = None
            for row in reversed(all_data[header_row+1:]):
                if row and row[0].strip():  # Has date
                    latest_row = row
                    break
            
            if not latest_row:
                continue
            
            # Parse row
            row_dict = {}
            for j, header in enumerate(headers):
                if j < len(latest_row):
                    row_dict[header.strip()] = latest_row[j].strip()
            
            # Extract key fields
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

# ============ GENERATE REPORT IMAGE ============
def generate_report_image(stores_data):
    """Generate professional close cash report image (amber/gold theme)"""
    if not stores_data:
        return None
    
    # Calculate totals
    total_cash = sum(s['cash'] for s in stores_data)
    total_card = sum(s['card'] for s in stores_data)
    total_upi = sum(s['upi'] for s in stores_data)
    total_sale = sum(s['sale'] for s in stores_data)
    total_exp = sum(s['exp'] for s in stores_data)
    
    # Create image
    img = Image.new('RGB', (1200, 1400), color=(30, 30, 30))  # Dark background
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font, fallback to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        data_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        data_font = ImageFont.load_default()
    
    # Colors
    amber = (184, 107, 10)
    gold = (255, 193, 7)
    white = (255, 255, 255)
    light_gray = (200, 200, 200)
    green = (76, 175, 80)
    
    y_offset = 20
    
    # Title
    draw.text((30, y_offset), "NKB STYLE BRANDS", fill=amber, font=title_font)
    draw.text((30, y_offset + 40), "Close Cash Report", fill=light_gray, font=header_font)
    today_date = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%A, %d %b %Y')
    draw.text((30, y_offset + 65), today_date, fill=light_gray, font=data_font)
    
    # Badge
    draw.rectangle([1050, y_offset, 1170, y_offset + 40], fill=amber)
    draw.text((1070, y_offset + 10), "13 STORES", fill=(30, 30, 30), font=header_font)
    
    y_offset += 120
    
    # Table header
    draw.rectangle([25, y_offset, 1175, y_offset + 35], fill=amber)
    headers = ["STORE", "CASH", "CARD", "UPI", "SALE", "EXP / REMARK"]
    col_widths = [250, 140, 140, 140, 140, 365]
    x_pos = 30
    for i, header in enumerate(headers):
        draw.text((x_pos, y_offset + 8), header, fill=(30, 30, 30), font=header_font)
        x_pos += col_widths[i]
    
    y_offset += 40
    
    # Store rows
    for store in stores_data:
        draw.text((30, y_offset), store['store'][:25], fill=white, font=data_font)
        draw.text((280, y_offset), f"₹{store['cash']:,.0f}", fill=white, font=data_font)
        draw.text((420, y_offset), f"₹{store['card']:,.0f}", fill=white, font=data_font)
        draw.text((560, y_offset), f"₹{store['upi']:,.0f}", fill=white, font=data_font)
        draw.text((700, y_offset), f"₹{store['sale']:,.0f}", fill=green, font=data_font)
        
        exp_text = f"-₹{store['exp']:,.0f}"
        if store['exp_remark']:
            exp_text += f" {store['exp_remark'][:30]}"
        draw.text((840, y_offset), exp_text, fill=(255, 100, 100), font=data_font)
        
        y_offset += 28
    
    # Total row
    y_offset += 5
    draw.line([(25, y_offset), (1175, y_offset)], fill=amber, width=2)
    y_offset += 15
    
    draw.text((30, y_offset), "TOTAL", fill=white, font=header_font)
    draw.text((280, y_offset), f"₹{total_cash:,.0f}", fill=white, font=header_font)
    draw.text((420, y_offset), f"₹{total_card:,.0f}", fill=white, font=header_font)
    draw.text((560, y_offset), f"₹{total_upi:,.0f}", fill=white, font=header_font)
    draw.text((700, y_offset), f"₹{total_sale:,.0f}", fill=gold, font=header_font)
    draw.text((840, y_offset), f"-₹{total_exp:,.0f}", fill=(255, 100, 100), font=header_font)
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

# ============ CLAUDE ANALYSIS ============
def analyze_with_claude(stores_data):
    """Use Claude API to analyze store performance"""
    client = Anthropic()
    
    # Prepare data for analysis
    data_text = "Store Performance Data:\n\n"
    for store in sorted(stores_data, key=lambda x: x['sale'], reverse=True):
        data_text += f"{store['store']}: Sale ₹{store['sale']:,.0f} | Cash ₹{store['cash']:,.0f} | Card ₹{store['card']:,.0f} | UPI ₹{store['upi']:,.0f} | Expense ₹{store['exp']:,.0f}\n"
    
    prompt = f"""{data_text}

Please provide a detailed analysis with:
1. **Store Performance Ranking** - Top 5 and Bottom 5 stores by sales
2. **Underperformance Alert** - Stores significantly below average
3. **Expense Analysis** - Unusual expense spikes (expenses > 10% of sales)
4. **Payment Methods** - Cash vs Card vs UPI ratio analysis
5. **Key Insights** - 3-4 actionable insights for management

Keep it concise, professional, and actionable. Use bullet points."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

# ============ EMAIL DELIVERY ============
def send_email_report(stores_data, analysis, report_image):
    """Send email with report and analysis"""
    try:
        # Create Excel file
        df = pd.DataFrame(stores_data)
        excel_bytes = BytesIO()
        with pd.ExcelWriter(excel_bytes, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Close Cash Report', index=False)
        excel_bytes.seek(0)
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"NKB Close Cash Report - {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y')}"
        msg['From'] = GMAIL_EMAIL
        msg['To'] = 'nkblifestylebrands@gmail.com'
        msg['Date'] = formatdate(localtime=True)
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #B8690A;">NKB Style Brands - Daily Close Cash Report</h2>
        <p>Report Date: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%A, %d %b %Y at %I:%M %p IST')}</p>
        
        <h3 style="color: #B8690A;">📊 QUICK SUMMARY</h3>
        <p>
            <strong>Total Sale:</strong> ₹{sum(s['sale'] for s in stores_data):,.0f}<br>
            <strong>Total Cash:</strong> ₹{sum(s['cash'] for s in stores_data):,.0f}<br>
            <strong>Total Card:</strong> ₹{sum(s['card'] for s in stores_data):,.0f}<br>
            <strong>Total UPI:</strong> ₹{sum(s['upi'] for s in stores_data):,.0f}<br>
            <strong>Total Expenses:</strong> ₹{sum(s['exp'] for s in stores_data):,.0f}
        </p>
        
        <h3 style="color: #B8690A;">🔍 CLAUDE AI ANALYSIS</h3>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">{analysis}</pre>
        
        <p style="margin-top: 20px; font-size: 12px; color: #666;">
            <em>This is an automated report. Excel file with detailed data is attached.</em>
        </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach Excel
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(excel_bytes.getvalue())
        part.add_header('Content-Disposition', 'attachment', 
                       filename=f"NKB_Close_Cash_{datetime.now().strftime('%Y%m%d')}.xlsx")
        msg.attach(part)
        
        # Attach report image
        if report_image:
            img_part = MIMEBase('image', 'png')
            img_part.set_payload(report_image.getvalue())
            img_part.add_header('Content-Disposition', 'attachment',
                               filename='close_cash_report.png')
            msg.attach(img_part)
        
        # Send via Gmail
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
    """Main function - fetch data, generate report, analyze, send email"""
    print("🚀 Starting NKB Close Cash Report Generation...")
    
    try:
        # Connect to Google Sheets
        gc = connect_google_sheets()
        print("✅ Connected to Google Sheets")
        
        # Fetch data
        stores_data = fetch_store_data(gc, MASTER_SHEET_URL)
        if not stores_data:
            print("❌ No data found!")
            return False
        
        print(f"✅ Fetched data from {len(stores_data)} stores")
        
        # Generate report image
        report_image = generate_report_image(stores_data)
        print("✅ Generated report image")
        
        # Analyze with Claude
        analysis = analyze_with_claude(stores_data)
        print("✅ Claude analysis complete")
        
        # Send email
        send_email_report(stores_data, analysis, report_image)
        print("✅ Report generation complete!")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    generate_report()
