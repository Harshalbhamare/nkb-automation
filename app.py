#!/usr/bin/env python3
from flask import Flask, request
from nkb_automation import fetch_stores_by_date, generate_report_text
import os
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NKB Close Cash Report</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #d4a574; }
            .filters { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
            button { background: #d4a574; color: white; border: none; padding: 10px 20px; font-size: 14px; border-radius: 4px; cursor: pointer; transition: background 0.3s; }
            button:hover { background: #b8905f; }
            button.active { background: #8b5a00; }
            #report { background: #f9f9f9; padding: 20px; border-radius: 4px; margin-top: 20px; font-family: monospace; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; max-height: 600px; overflow-y: auto; border: 1px solid #ddd; text-align: center; }
            .loading { color: #666; }
            input[type="date"] { padding: 8px; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 NKB Close Cash Report</h1>
            <p>Select date range and view report</p>
            
            <div class="filters">
                <button onclick="generateReport('today')" class="active">📅 Today</button>
                <button onclick="generateReport('yesterday')">📅 Yesterday</button>
                <button onclick="generateReport('mtd')">📊 Month to Date</button>
                <input type="date" id="customDate" onchange="generateReport('custom')">
            </div>
            
            <div id="report" class="loading">Loading report...</div>
        </div>
        
        <script>
            async function generateReport(range) {
                const report = document.getElementById('report');
                report.textContent = '⏳ Generating report...';
                
                let url = '/report?range=' + range;
                if (range === 'custom') {
                    const date = document.getElementById('customDate').value;
                    if (!date) {
                        report.textContent = 'Please select a date';
                        return;
                    }
                    url = '/report?range=custom&date=' + date;
                }
                
                try {
                    const response = await fetch(url);
                    const text = await response.text();
                    report.textContent = text;
                } catch (e) {
                    report.textContent = '❌ Error: ' + e.message;
                }
            }
            
            generateReport('today');
        </script>
    </body>
    </html>
    """

@app.route('/report', methods=['GET'])
def view_report():
    try:
        range_type = request.args.get('range', 'today')
        custom_date = request.args.get('date', None)
        
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).strftime('%d-%m-%Y')
        
        if range_type == 'today':
            start_date = end_date = today
        elif range_type == 'yesterday':
            yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%d-%m-%Y')
            start_date = end_date = yesterday
        elif range_type == 'mtd':
            today_obj = datetime.now(ist)
            start_date = f"01-{today_obj.strftime('%m-%Y')}"
            end_date = today
        elif range_type == 'custom':
            if not custom_date:
                return "Error: No date provided", 400
            parts = custom_date.split('-')
            start_date = end_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            start_date = end_date = today
        
        _, report_data, total_cash, total_card, total_upi, total_sale, total_expense = fetch_stores_by_date(start_date, end_date)
        report_text = generate_report_text(start_date, end_date, report_data, total_cash, total_card, total_upi, total_sale, total_expense)
        
        return report_text
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
