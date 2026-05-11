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
        print(f"⏰ Daily pre-fetch for {yesterday}...")
        fetch_stores_by_date(yesterday, yesterday)
        print(f"✅ Daily pre-fetch complete")
    except Exception as e:
        print(f"❌ Pre-fetch failed: {str(e)}")

scheduler.add_job(daily_pre_fetch, 'cron', hour=0, minute=1, timezone='Asia/Kolkata')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    return """<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NKB Close Cash</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; margin: 0; }
.container { max-width: 1200px; margin: 0 auto; background: white; min-height: 100vh; }
.header { background: linear-gradient(135deg, #8b6914, #c99a6e); color: white; padding: 24px 16px; text-align: center; }
.header h1 { margin: 0; font-size: 28px; }
.controls { padding: 20px 16px; background: #fafafa; border-bottom: 1px solid #e0e0e0; }
.button-group { display: flex; gap: 8px; flex-wrap: wrap; }
button { padding: 10px 16px; border: 1px solid #d4a574; background: white; color: #8b6914; border-radius: 6px; font-weight: 600; cursor: pointer; }
button:hover { background: #f0f0f0; }
button.active { background: #8b6914; color: white; }
input[type="date"] { padding: 10px 12px; border: 1px solid #d0d0d0; border-radius: 6px; }
#report { padding: 20px 16px; min-height: 300px; }
.empty-state { text-align: center; padding: 60px 20px; color: #999; }
.store-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin: 20px 0; }
.store-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 14px; }
.store-name { font-weight: 600; margin-bottom: 12px; }
.data-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }
.summary-item { background: #fafafa; padding: 16px; border-radius: 8px; text-align: center; }
.summary-value { font-size: 18px; font-weight: 700; color: #2d5016; }
.loading { text-align: center; padding: 40px; }
.error { background: #ffebee; color: #c62828; padding: 16px; border-radius: 6px; margin: 20px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>📊 NKB Close Cash</h1>
<p>Real-time sales & expense report</p>
</div>

<div class="controls">
<div style="font-size: 11px; font-weight: 600; color: #666; margin-bottom: 12px; text-transform: uppercase;">Select Date Range</div>
<div class="button-group">
<button id="btn-yesterday" onclick="loadReport('yesterday')">📅 Yesterday</button>
<button id="btn-mtd" onclick="loadReport('mtd')">📊 Month to Date</button>
<input type="date" id="customDate" onchange="loadReport('custom')" />
</div>
</div>

<div id="report">
<div class="empty-state">
<div style="font-size: 48px; margin-bottom: 16px;">📋</div>
<div style="font-size: 18px; font-weight: 600; color: #666;">Select a date range</div>
</div>
</div>
</div>

<script>
function loadReport(range) {
    const rep = document.getElementById('report');
    rep.innerHTML = '<div class="loading">Fetching data...</div>';
    
    let url = '/report?range=' + range;
    if (range === 'custom') {
        const d = document.getElementById('customDate').value;
        if (!d) {
            rep.innerHTML = '<div class="empty-state">Please select a date</div>';
            return;
        }
        url = '/report?range=custom&date=' + d;
    }
    
    document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    if (range === 'yesterday') document.getElementById('btn-yesterday').classList.add('active');
    if (range === 'mtd') document.getElementById('btn-mtd').classList.add('active');
    
    fetch(url)
        .then(r => r.json())
        .then(d => {
            rep.innerHTML = d.html;
        })
        .catch(e => {
            rep.innerHTML = '<div class="error">Error: ' + e.message + '</div>';
        });
}
</script>
</body>
</html>"""

@app.route('/report')
def report():
    try:
        range_type = request.args.get('range', 'yesterday')
        custom_date = request.args.get('date')
        
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).strftime('%d-%m-%Y')
        
        if range_type == 'yesterday':
            yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%d-%m-%Y')
            start_date = end_date = yesterday
        elif range_type == 'mtd':
            today_obj = datetime.now(ist)
            start_date = f"01-{today_obj.strftime('%m-%Y')}"
            end_date = today
        elif range_type == 'custom' and custom_date:
            custom_date_obj = datetime.strptime(custom_date, '%Y-%m-%d')
            start_date = end_date = custom_date_obj.strftime('%d-%m-%Y')
        else:
            yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%d-%m-%Y')
            start_date = end_date = yesterday
        
        _, report_data, total_cash, total_card, total_upi, total_sale, total_expense = fetch_stores_by_date(start_date, end_date)
        
        display_date = start_date if start_date == end_date else f"{start_date} to {end_date}"
        
        html = f"<div style='text-align: center; margin-bottom: 20px; border-bottom: 2px solid #8b6914; padding-bottom: 16px;'><div style='font-size: 20px; font-weight: 600;'>Close Cash Report</div><div style='font-size: 13px; color: #666;'>{display_date}</div></div>"
        
        html += "<div class='store-grid'>"
        for item in report_data:
            remark = item.get('remark', '-') or '-'
            html += f"""<div class="store-card">
<div class="store-name">{item['store']}</div>
<div class="data-row"><span>Cash</span><span style="font-weight: 600;">₹{item['cash']:,.0f}</span></div>
<div class="data-row"><span>Card</span><span style="font-weight: 600;">₹{item['card']:,.0f}</span></div>
<div class="data-row"><span>UPI</span><span style="font-weight: 600;">₹{item['upi']:,.0f}</span></div>
<div class="data-row"><span>Sale</span><span style="font-weight: 600; color: #8b6914;">₹{item['sale']:,.0f}</span></div>
<div class="data-row"><span>Expense</span><span style="font-weight: 600;">₹{item['expense']:,.0f}</span></div>
<div style="margin-top: 8px; font-size: 11px; color: #666; background: #f9f9f9; padding: 6px; border-radius: 4px;">Remark: {remark}</div>
</div>"""
        html += "</div>"
        
        net = total_cash + total_card + total_upi
        exp_pct = (total_expense / total_sale * 100) if total_sale > 0 else 0
        
        html += f"""<div class="summary">
<div class="summary-item"><div style="font-size: 11px; color: #999; text-transform: uppercase; margin-bottom: 6px;">Total Cash</div><div class="summary-value">₹{total_cash:,.0f}</div></div>
<div class="summary-item"><div style="font-size: 11px; color: #999; text-transform: uppercase; margin-bottom: 6px;">Total Card</div><div class="summary-value">₹{total_card:,.0f}</div></div>
<div class="summary-item"><div style="font-size: 11px; color: #999; text-transform: uppercase; margin-bottom: 6px;">Total UPI</div><div class="summary-value">₹{total_upi:,.0f}</div></div>
<div class="summary-item"><div style="font-size: 11px; color: #999; text-transform: uppercase; margin-bottom: 6px;">Net Collection</div><div class="summary-value">₹{net:,.0f}</div></div>
<div class="summary-item"><div style="font-size: 11px; color: #999; text-transform: uppercase; margin-bottom: 6px;">Total Expense</div><div class="summary-value" style="color: #c62828;">₹{total_expense:,.0f} ({exp_pct:.1f}%)</div></div>
</div>"""
        
        return jsonify({"html": html})
    except Exception as e:
        return jsonify({"html": f"<div class='error'>Error: {str(e)}</div>"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
