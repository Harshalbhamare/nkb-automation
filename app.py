#!/usr/bin/env python3
from flask import Flask, request, jsonify
from nkb_automation import fetch_stores_by_date
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import datetime, timedelta
import pytz
import atexit

app = Flask(__name__)

scheduler = BackgroundScheduler()

def daily_pre_fetch():
    try:
        ist = pytz.timezone('Asia/Kolkata')
        yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%d-%m-%Y')
        print(f"\n⏰ [SCHEDULER] Starting daily pre-fetch for {yesterday}...")
        fetch_stores_by_date(yesterday, yesterday)
        print(f"✅ [SCHEDULER] Daily pre-fetch complete - data cached for instant access")
    except Exception as e:
        print(f"❌ [SCHEDULER] Pre-fetch failed: {str(e)}")

scheduler.add_job(daily_pre_fetch, 'cron', hour=0, minute=1, timezone='Asia/Kolkata')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

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
            html, body { height: 100%; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                color: #1a1a1a;
            }
            .container { 
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .header {
                background: linear-gradient(135deg, #8b6914 0%, #c99a6e 100%);
                padding: 24px 16px;
                color: white;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .header h1 { 
                font-size: 28px;
                margin-bottom: 4px;
                font-weight: 600;
                letter-spacing: -0.5px;
            }
            .header p {
                font-size: 13px;
                opacity: 0.9;
            }
            .controls {
                padding: 20px 16px;
                background: #fafafa;
                border-bottom: 1px solid #e0e0e0;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            .controls-title {
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                color: #666;
                margin-bottom: 12px;
            }
            .button-group {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                align-items: center;
            }
            button {
                padding: 10px 16px;
                border: 1px solid #d4a574;
                background: white;
                color: #8b6914;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                flex: 1;
                min-width: 100px;
            }
            button:hover {
                background: #f5f5f5;
                border-color: #8b6914;
            }
            button:active {
                background: #efefef;
            }
            button.active {
                background: #8b6914;
                color: white;
                border-color: #8b6914;
            }
            input[type="date"] {
                padding: 10px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 12px;
                flex: 1;
                min-width: 130px;
            }
            input[type="date"]:focus {
                outline: none;
                border-color: #8b6914;
                box-shadow: 0 0 0 2px rgba(139, 105, 20, 0.1);
            }
            .report-container {
                flex: 1;
                padding: 20px 16px;
                overflow: auto;
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #999;
            }
            .empty-state-icon {
                font-size: 48px;
                margin-bottom: 16px;
            }
            .empty-state-title {
                font-size: 18px;
                font-weight: 600;
                color: #666;
                margin-bottom: 8px;
            }
            .empty-state-text {
                font-size: 13px;
                color: #999;
            }
            .report-header {
                text-align: center;
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 2px solid #8b6914;
            }
            .report-title {
                font-size: 20px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 4px;
            }
            .report-date {
                font-size: 13px;
                color: #666;
                font-weight: 500;
            }
            .cache-badge {
                display: inline-block;
                background: #d4edda;
                color: #155724;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                margin-top: 8px;
                font-weight: 600;
            }
            .store-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 12px;
                margin-bottom: 24px;
            }
            @media (min-width: 640px) {
                .store-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            @media (min-width: 1024px) {
                .store-grid {
                    grid-template-columns: repeat(3, 1fr);
                }
                .report-container {
                    padding: 30px;
                }
            }
            .store-card {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                overflow: hidden;
                transition: all 0.2s ease;
            }
            .store-card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                border-color: #d4a574;
            }
            .store-card.no-data {
                opacity: 0.6;
            }
            .store-header {
                background: #f9f9f9;
                padding: 12px 14px;
                border-bottom: 1px solid #e0e0e0;
            }
            .store-name {
                font-weight: 600;
                font-size: 14px;
                color: #1a1a1a;
                margin: 0;
            }
            .store-body {
                padding: 14px;
            }
            .data-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #f5f5f5;
                font-size: 13px;
            }
            .data-row:last-child {
                border-bottom: none;
                padding-bottom: 0;
            }
            .data-label {
                color: #666;
                font-weight: 500;
            }
            .data-value {
                color: #2d5016;
                font-weight: 600;
                font-family: 'Courier New', monospace;
                text-align: right;
            }
            .data-value.highlight {
                color: #8b6914;
                font-size: 14px;
            }
            .remark-section {
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid #f5f5f5;
            }
            .remark-label {
                font-size: 11px;
                color: #999;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
                font-weight: 600;
            }
            .remark-text {
                font-size: 12px;
                color: #666;
                background: #fafafa;
                padding: 8px;
                border-radius: 4px;
                word-break: break-word;
            }
            .no-data-text {
                text-align: center;
                color: #aaa;
                padding: 20px 14px;
                font-size: 13px;
            }
            .summary {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-bottom: 24px;
            }
            @media (min-width: 768px) {
                .summary {
                    grid-template-columns: repeat(5, 1fr);
                }
            }
            .summary-item {
                padding: 16px;
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                text-align: center;
            }
            .summary-label {
                font-size: 11px;
                color: #999;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 6px;
                font-weight: 600;
            }
            .summary-value {
                font-size: 18px;
                font-weight: 700;
                color: #2d5016;
                font-family: 'Courier New', monospace;
            }
            .summary-item:last-child .summary-value {
                color: #c62828;
            }
            .ai-section {
                margin-top: 24px;
                padding: 20px;
                background: linear-gradient(135deg, #f0f4ff 0%, #f9f5ff 100%);
                border: 1px solid #e0d5ff;
                border-radius: 8px;
            }
            .ai-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }
            .ai-header h3 {
                font-size: 14px;
                font-weight: 600;
                color: #5b21b6;
                margin: 0;
            }
            .ai-button {
                background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                width: auto;
            }
            .ai-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
            }
            .ai-loading {
                text-align: center;
                padding: 20px;
                color: #666;
            }
            .ai-spinner {
                border: 3px solid #f0f0f0;
                border-top: 3px solid #7c3aed;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 12px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .ai-content {
                font-size: 13px;
                line-height: 1.6;
                color: #444;
            }
            .ai-content h4 {
                color: #7c3aed;
                margin: 12px 0 6px 0;
                font-size: 13px;
                font-weight: 600;
            }
            .ai-content ul {
                margin: 6px 0 12px 18px;
                padding: 0;
            }
            .ai-content li {
                margin: 4px 0;
            }
            .ai-error {
                background: #fee2e2;
                color: #991b1b;
                padding: 12px;
                border-radius: 6px;
                font-size: 12px;
                margin-top: 12px;
            }
            .loading {
                text-align: center;
                padding: 40px 20px;
                color: #666;
            }
            .spinner {
                border: 3px solid #f0f0f0;
                border-top: 3px solid #8b6914;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 16px;
            }
            .timestamp {
                text-align: center;
                padding: 20px 16px;
                border-top: 1px solid #e0e0e0;
                color: #999;
                font-size: 12px;
            }
            .error {
                background: #ffebee;
                color: #c62828;
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 16px;
                border-left: 4px solid #c62828;
                font-size: 13px;
            }
            .info {
                background: #e3f2fd;
                color: #1565c0;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 16px;
                border-left: 4px solid #1565c0;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 NKB Close Cash</h1>
                <p>Real-time sales & expense report</p>
            </div>

            <div class="controls">
                <div class="controls-title">Select Date Range</div>
                <div class="button-group">
                    <button onclick="generateReport('yesterday')" id="btn-yesterday">📅 Yesterday</button>
                    <button onclick="generateReport('mtd')" id="btn-mtd">📊 Month to Date</button>
                    <input type="date" id="customDate" onchange="generateReport('custom')" />
                </div>
            </div>

            <div class="report-container" id="report">
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-title">Select a date range</div>
                    <div class="empty-state-text">Click a button above to view close cash report</div>
                </div>
            </div>
        </div>

        <script>
            let currentReportData = null;
            
            function updateButtons(active) {
                document.querySelectorAll('button').forEach(btn => {
                    btn.classList.remove('active');
                });
                if (active === 'yesterday') document.getElementById('btn-yesterday').classList.add('active');
                if (active === 'mtd') document.getElementById('btn-mtd').classList.add('active');
            }
            
            async function generateReport(range) {
                const report = document.getElementById('report');
                report.innerHTML = '<div class="loading"><div class="spinner"></div><p>Fetching from 13 stores...</p></div>';
                
                let url = '/report?range=' + range;
                if (range === 'custom') {
                    const date = document.getElementById('customDate').value;
                    if (!date) {
                        report.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-title">Please select a date</div></div>';
                        return;
                    }
                    url = '/report?range=custom&date=' + date;
                }
                
                updateButtons(range);
                
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    currentReportData = data;
                    report.innerHTML = data.html;
                } catch (e) {
                    report.innerHTML = '<div class="error">Error: ' + e.message + '</div>';
                }
            }
            
            function shareWithClaude() {
                if (!currentReportData) {
                    alert('Please load a report first');
                    return;
                }
                
                const totals = currentReportData['data']['totals'];
                const stores = currentReportData['data']['stores'];
                const date = currentReportData['data']['date'];
                
                let storesText = stores.map(s => {
                    if (s['entries'] > 0) {
                        return `${s['store']}: Sale ₹${s['sale'].toLocaleString('en-IN')}, Expense ₹${s['expense'].toLocaleString('en-IN')}, Cash ₹${s['cash'].toLocaleString('en-IN')}, Card ₹${s['card'].toLocaleString('en-IN')}, UPI ₹${s['upi'].toLocaleString('en-IN')}`;
                    }
                    return null;
                }).filter(s => s !== null).join('\n');
                
                const prompt = `Analyze this NKB Store Close Cash report for ${date}:

SUMMARY:
- Total Sale: ₹${totals['sale'].toLocaleString('en-IN')}
- Total Expense: ₹${totals['expense'].toLocaleString('en-IN')} (${((totals['expense'] / totals['sale']) * 100).toFixed(1)}% of sales)
- Net Collection: ₹${totals['net_collection'].toLocaleString('en-IN')}
  - Cash: ₹${totals['cash'].toLocaleString('en-IN')}
  - Card: ₹${totals['card'].toLocaleString('en-IN')}
  - UPI: ₹${totals['upi'].toLocaleString('en-IN')}

STORE-WISE BREAKDOWN:
${storesText}

Please provide:
1. Key findings (2-3 points about performance)
2. Stores that need attention (if any underperforming)
3. Expense observations
4. Recommendations (2-3 actionable items)`;
                
                // Copy to clipboard
                navigator.clipboard.writeText(prompt).then(() => {
                    // Open Claude in new tab
                    window.open('https://claude.ai', '_blank');
                    alert('Report data copied to clipboard!\nPaste it into Claude to get AI insights.');
                }).catch(() => {
                    // Fallback: just open Claude
                    window.open('https://claude.ai', '_blank');
                    alert('Open Claude and paste this data:\n\n' + prompt);
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/report', methods=['GET'])
def view_report():
    try:
        range_type = request.args.get('range', 'yesterday')
        custom_date = request.args.get('date', None)
        
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).strftime('%d-%m-%Y')
        
        if range_type == 'yesterday':
            yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%d-%m-%Y')
            start_date = end_date = yesterday
        elif range_type == 'mtd':
            today_obj = datetime.now(ist)
            start_date = f"01-{today_obj.strftime('%m-%Y')}"
            end_date = today
        elif range_type == 'custom':
            if not custom_date:
                return jsonify({"error": "No date provided"})
            try:
                custom_date_obj = datetime.strptime(custom_date, '%Y-%m-%d')
                start_date = end_date = custom_date_obj.strftime('%d-%m-%Y')
            except:
                return jsonify({"error": "Invalid date format"})
        else:
            yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%d-%m-%Y')
            start_date = end_date = yesterday
        
        _, report_data, total_cash, total_card, total_upi, total_sale, total_expense = fetch_stores_by_date(start_date, end_date)
        
        display_date = start_date if start_date == end_date else f"{start_date} to {end_date}"
        
        html = f'''
        <div class="report-header">
            <div class="report-title">Close Cash Report</div>
            <div class="report-date">{display_date}</div>
        </div>
        '''
        
        successful = sum(1 for item in report_data if item['entries'] > 0)
        
        if successful < 13:
            html += f'''
            <div class="info">
                ⚠️ Partial data: {successful}/13 stores loaded.
            </div>
            '''
        else:
            html += '''
            <div class="cache-badge">✅ Complete data cached</div>
            '''
        
        html += '''
        <div class="store-grid">
        '''
        
        for item in report_data:
            remark = item.get('remark', '-') or '-'
            if item['entries'] > 0:
                html += f'''
                <div class="store-card">
                    <div class="store-header">
                        <p class="store-name">{item['store']}</p>
                    </div>
                    <div class="store-body">
                        <div class="data-row">
                            <span class="data-label">Cash</span>
                            <span class="data-value">₹{item['cash']:,.0f}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">Card</span>
                            <span class="data-value">₹{item['card']:,.0f}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">UPI</span>
                            <span class="data-value">₹{item['upi']:,.0f}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">Sale</span>
                            <span class="data-value highlight">₹{item['sale']:,.0f}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">Expense</span>
                            <span class="data-value">₹{item['expense']:,.0f}</span>
                        </div>
                        <div class="remark-section">
                            <div class="remark-label">Remark</div>
                            <div class="remark-text">{remark}</div>
                        </div>
                    </div>
                </div>
                '''
            else:
                html += f'''
                <div class="store-card no-data">
                    <div class="store-header">
                        <p class="store-name">{item['store']}</p>
                    </div>
                    <div class="no-data-text">No data</div>
                </div>
                '''
        
        html += '</div>'
        
        net_collection = total_cash + total_card + total_upi
        expense_pct = (total_expense / total_sale * 100) if total_sale > 0 else 0
        
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
            <div class="summary-item">
                <div class="summary-label">Total Expense</div>
                <div class="summary-value">₹{total_expense:,.0f} ({expense_pct:.1f}%)</div>
            </div>
        </div>
        
        <div class="ai-section">
            <div class="ai-header">
                <h3>✨ Claude AI Analysis</h3>
                <button class="ai-button" onclick="shareWithClaude()">Share with Claude</button>
            </div>
            <p style="font-size: 11px; color: #666; margin-top: 8px;">Click above to send this report to Claude for AI-powered insights on sales performance, expense trends, and recommendations.</p>
        </div>
        
        <div class="timestamp">
            Generated: {datetime.now(ist).strftime('%d-%m-%Y %H:%M IST')}
        </div>
        '''
        
        return jsonify({
            "html": html,
            "data": {
                "date": display_date,
                "stores": report_data,
                "totals": {
                    "cash": total_cash,
                    "card": total_card,
                    "upi": total_upi,
                    "sale": total_sale,
                    "expense": total_expense,
                    "net_collection": net_collection
                }
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
