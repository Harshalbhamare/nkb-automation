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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NKB Close Cash Report</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #d4a574 0%, #b8905f 100%);
                padding: 30px;
                color: white;
                text-align: center;
            }
            .header h1 { 
                font-size: 36px;
                margin-bottom: 5px;
                font-weight: 700;
            }
            .header p {
                font-size: 14px;
                opacity: 0.9;
            }
            .controls {
                padding: 30px;
                background: #f9f9f9;
                border-bottom: 2px solid #f0f0f0;
            }
            .controls-title {
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #888;
                margin-bottom: 15px;
            }
            .button-group {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                margin-bottom: 20px;
                align-items: center;
            }
            button {
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #d4a574;
                color: white;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 15px rgba(212, 165, 116, 0.3);
            }
            button:hover {
                background: #b8905f;
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(212, 165, 116, 0.4);
            }
            button:active {
                transform: translateY(0);
                box-shadow: 0 2px 10px rgba(212, 165, 116, 0.2);
            }
            button.active {
                background: #8b5a00;
                box-shadow: 0 4px 15px rgba(139, 90, 0, 0.4);
            }
            input[type="date"] {
                padding: 10px 15px;
                border: 2px solid #d4a574;
                border-radius: 6px;
                font-size: 14px;
                transition: all 0.3s ease;
            }
            input[type="date"]:focus {
                outline: none;
                border-color: #b8905f;
                box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.1);
            }
            .report-container {
                padding: 30px;
                background: white;
            }
            .report-header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px solid #d4a574;
                padding-bottom: 20px;
            }
            .report-title {
                font-size: 24px;
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 5px;
            }
            .report-date {
                font-size: 14px;
                color: #888;
                font-weight: 500;
            }
            .store-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }
            .store-table thead {
                background: #2d2d2d;
                color: white;
            }
            .store-table th {
                padding: 15px;
                text-align: left;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 3px solid #d4a574;
            }
            .store-table td {
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
                font-size: 14px;
            }
            .store-table tbody tr {
                transition: background 0.2s ease;
            }
            .store-table tbody tr:hover {
                background: #f9f9f9;
            }
            .store-table tbody tr:nth-child(even) {
                background: #fafafa;
            }
            .store-name {
                font-weight: 600;
                color: #1a1a1a;
            }
            .amount {
                text-align: right;
                font-weight: 500;
                color: #d4a574;
                font-family: 'Courier New', monospace;
            }
            .totals-row {
                background: #2d2d2d;
                color: white;
                font-weight: 700;
            }
            .totals-row td {
                padding: 18px 15px;
                border-bottom: none;
            }
            .remark {
                font-size: 12px;
                color: #666;
                max-width: 300px;
                white-space: normal;
            }
            .summary {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            .summary-item {
                padding: 15px;
                background: white;
                border-left: 4px solid #d4a574;
                border-radius: 4px;
            }
            .summary-label {
                font-size: 12px;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }
            .summary-value {
                font-size: 20px;
                font-weight: 700;
                color: #d4a574;
                font-family: 'Courier New', monospace;
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #888;
            }
            .spinner {
                border: 3px solid #f0f0f0;
                border-top: 3px solid #d4a574;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .timestamp {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #f0f0f0;
                color: #888;
                font-size: 12px;
            }
            .error {
                background: #ffe0e0;
                color: #d32f2f;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                border-left: 4px solid #d32f2f;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 NKB Close Cash Report</h1>
                <p>Daily sales & expense tracking across all 13 stores</p>
            </div>

            <div class="controls">
                <div class="controls-title">Select Date Range</div>
                <div class="button-group">
                    <button onclick="generateReport('today')" class="active" id="btn-today">📅 Today</button>
                    <button onclick="generateReport('yesterday')" id="btn-yesterday">📅 Yesterday</button>
                    <button onclick="generateReport('mtd')" id="btn-mtd">📊 Month to Date</button>
                    <input type="date" id="customDate" onchange="generateReport('custom')" />
                </div>
            </div>

            <div class="report-container" id="report">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading report...</p>
                </div>
            </div>
        </div>

        <script>
            let lastReport = 'today';
            
            function updateButtons(active) {
                document.querySelectorAll('button').forEach(btn => {
                    btn.classList.remove('active');
                });
                if (active === 'today') document.getElementById('btn-today').classList.add('active');
                if (active === 'yesterday') document.getElementById('btn-yesterday').classList.add('active');
                if (active === 'mtd') document.getElementById('btn-mtd').classList.add('active');
            }
            
            async function generateReport(range) {
                lastReport = range;
                const report = document.getElementById('report');
                report.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating report...</p></div>';
                
                let url = '/report?range=' + range;
                if (range === 'custom') {
                    const date = document.getElementById('customDate').value;
                    if (!date) {
                        report.innerHTML = '<div class="error">Please select a date</div>';
                        return;
                    }
                    url = '/report?range=custom&date=' + date;
                }
                
                updateButtons(range);
                
                try {
                    const response = await fetch(url);
                    const html = await response.text();
                    report.innerHTML = html;
                } catch (e) {
                    report.innerHTML = '<div class="error">Error loading report: ' + e.message + '</div>';
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
                return '<div class="error">Error: No date provided</div>'
            parts = custom_date.split('-')
            start_date = end_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            start_date = end_date = today
        
        _, report_data, total_cash, total_card, total_upi, total_sale, total_expense = fetch_stores_by_date(start_date, end_date)
        
        display_date = start_date if start_date == end_date else f"{start_date} to {end_date}"
        
        html = f'''
        <div class="report-header">
            <div class="report-title">📊 NKB Daily Close Cash Report</div>
            <div class="report-date">Date Range: {display_date}</div>
        </div>
        
        <table class="store-table">
            <thead>
                <tr>
                    <th>Store Name</th>
                    <th>Cash</th>
                    <th>Card</th>
                    <th>UPI</th>
                    <th>Total Sale</th>
                    <th>Expense</th>
                    <th>Expense Remark</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for item in report_data:
            if item['entries'] > 0:
                html += f'''
                <tr>
                    <td class="store-name">{item['store']}</td>
                    <td class="amount">₹{item['cash']:,.0f}</td>
                    <td class="amount">₹{item['card']:,.0f}</td>
                    <td class="amount">₹{item['upi']:,.0f}</td>
                    <td class="amount">₹{item['sale']:,.0f}</td>
                    <td class="amount">₹{item['expense']:,.0f}</td>
                    <td class="remark">-</td>
                </tr>
                '''
            else:
                html += f'''
                <tr style="opacity: 0.5;">
                    <td class="store-name">{item['store']}</td>
                    <td colspan="6" style="text-align: center; color: #aaa;">No data</td>
                </tr>
                '''
        
        html += f'''
                <tr class="totals-row">
                    <td>TOTALS</td>
                    <td class="amount">₹{total_cash:,.0f}</td>
                    <td class="amount">₹{total_card:,.0f}</td>
                    <td class="amount">₹{total_upi:,.0f}</td>
                    <td class="amount">₹{total_sale:,.0f}</td>
                    <td class="amount">₹{total_expense:,.0f}</td>
                    <td></td>
                </tr>
            </tbody>
        </table>
        '''
        
        net_collection = total_cash + total_card + total_upi
        html += f'''
        <div class="summary">
            <div class="summary-item">
                <div class="summary-label">Total Cash</div>
                <div class="summary-value">₹{total_cash:,.0f}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Total Card</div>
                <div class="summary-value">₹{total_card:,.0f}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Total UPI</div>
                <div class="summary-value">₹{total_upi:,.0f}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Net Collection</div>
                <div class="summary-value">₹{net_collection:,.0f}</div>
            </div>
        </div>
        
        <div class="timestamp">
            Report generated at: {datetime.now(ist).strftime('%d-%m-%Y %H:%M:%S IST')}
        </div>
        '''
        
        return html
    
    except Exception as e:
        return f'<div class="error">Error: {str(e)}</div>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
