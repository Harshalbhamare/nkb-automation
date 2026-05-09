#!/usr/bin/env python3
"""
NKB Report Web App - Flask backend for on-demand reporting
Can be triggered from any device via web link
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pytz
from datetime import datetime
import logging

# Import the main automation function
from nkb_automation import generate_report

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ WEB INTERFACE ============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NKB Close Cash Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            max-width: 600px;
            width: 100%;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #B8690A;
            font-size: 32px;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #666;
            font-size: 16px;
        }
        
        .info-box {
            background: #f5f5f5;
            border-left: 4px solid #B8690A;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 6px;
        }
        
        .info-box h3 {
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .info-box p {
            color: #666;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #B8690A;
            color: white;
        }
        
        .btn-primary:hover {
            background: #9a5508;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(184, 107, 10, 0.2);
        }
        
        .btn-primary:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            display: none;
        }
        
        .status.success {
            display: block;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .status.error {
            display: block;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .status.loading {
            display: block;
            background: #e2e3e5;
            border: 1px solid #d6d8db;
            color: #383d41;
        }
        
        .schedule-info {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .schedule-info h4 {
            color: #856404;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .schedule-info p {
            color: #856404;
            font-size: 13px;
            line-height: 1.6;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0,0,0,0.1);
            border-radius: 50%;
            border-top-color: #B8690A;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .last-run {
            color: #666;
            font-size: 12px;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>📊 NKB Close Cash Report</h1>
                <p>Generate daily report with AI analysis</p>
            </div>
            
            <div class="info-box">
                <h3>📅 Automatic Schedule</h3>
                <p>Report automatically generates daily at <strong>12:00 AM IST</strong></p>
                <p>Results emailed to: <strong>nkblifestylebrands@gmail.com</strong></p>
            </div>
            
            <div class="info-box">
                <h3>🚀 Manual Trigger</h3>
                <p>Click below to generate report immediately</p>
            </div>
            
            <div id="status" class="status"></div>
            
            <div class="button-group">
                <button class="btn-primary" id="generateBtn" onclick="generateReport()">
                    🔄 Generate Report Now
                </button>
            </div>
            
            <div class="schedule-info">
                <h4>✅ What This Does:</h4>
                <p>
                    • Reads all 13 store close cash sheets<br>
                    • Analyzes performance with Claude AI<br>
                    • Identifies underperformance & expense spikes<br>
                    • Generates professional report<br>
                    • Sends via email with Excel attachment
                </p>
            </div>
            
            <div class="last-run" id="lastRun"></div>
        </div>
    </div>
    
    <script>
        async function generateReport() {
            const btn = document.getElementById('generateBtn');
            const status = document.getElementById('status');
            
            btn.disabled = true;
            status.className = 'status loading';
            status.innerHTML = '<span class="spinner"></span>Generating report...';
            
            try {
                const response = await fetch('/api/generate-report', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    status.className = 'status success';
                    status.innerHTML = '✅ Report generated successfully! Check email in 2-3 minutes.';
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 5000);
                } else {
                    status.className = 'status error';
                    status.innerHTML = '❌ Error: ' + (data.error || 'Unknown error');
                }
            } catch (error) {
                status.className = 'status error';
                status.innerHTML = '❌ Error: ' + error.message;
            } finally {
                btn.disabled = false;
            }
        }
        
        // Update last run time
        function updateLastRun() {
            fetch('/api/last-run')
                .then(r => r.json())
                .then(data => {
                    if (data.last_run) {
                        document.getElementById('lastRun').innerHTML = 
                            '⏱️ Last report: ' + data.last_run;
                    }
                });
        }
        
        updateLastRun();
        setInterval(updateLastRun, 30000);
    </script>
</body>
</html>
"""

# ============ API ENDPOINTS ============
@app.route('/')
def index():
    """Serve the web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/generate-report', methods=['POST'])
def api_generate_report():
    """API endpoint to trigger report generation"""
    try:
        logger.info("Report generation triggered via API")
        success = generate_report()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Report generated and sent successfully!',
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to generate report'
            }), 500
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/status')
def api_status():
    """Check if service is running"""
    return jsonify({
        'status': 'ok',
        'service': 'NKB Close Cash Report Automation',
        'time': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
    }), 200

@app.route('/api/last-run')
def api_last_run():
    """Get last report run time"""
    last_run_file = '/tmp/nkb_last_run.txt'
    last_run = 'Never'
    
    if os.path.exists(last_run_file):
        try:
            with open(last_run_file, 'r') as f:
                last_run = f.read().strip()
        except:
            pass
    
    return jsonify({'last_run': last_run}), 200

# ============ SCHEDULER ============
def scheduled_report():
    """Run report on schedule"""
    logger.info("⏰ Scheduled report generation started")
    
    try:
        generate_report()
        # Save last run time
        with open('/tmp/nkb_last_run.txt', 'w') as f:
            f.write(datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p IST'))
        logger.info("✅ Scheduled report completed")
    except Exception as e:
        logger.error(f"❌ Scheduled report error: {str(e)}")

def start_scheduler():
    """Start background scheduler"""
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    
    # Schedule daily at 12:00 AM IST (00:00)
    scheduler.add_job(
        scheduled_report,
        'cron',
        hour=0,
        minute=0,
        id='nkb_daily_report'
    )
    
    scheduler.start()
    logger.info("✅ Scheduler started - reports will run daily at 12:00 AM IST")

# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

# ============ STARTUP ============
if __name__ == '__main__':
    # Start scheduler
    start_scheduler()
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
