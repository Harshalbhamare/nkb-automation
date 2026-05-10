#!/usr/bin/env python3
from flask import Flask, jsonify
from nkb_automation import generate_report
import os
from datetime import datetime
import pytz

app = Flask(__name__)
last_run_time = None

@app.route('/', methods=['GET'])
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NKB Close Cash Report</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #333;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                border-radius: 12px;
                padding: 40px;
                max-width: 600px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            h1 {
                color: #d4a574;
                font-size: 32px;
                margin: 0 0 10px 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 16px;
            }
            .section {
                background: #f8f8f8;
                border-left: 4px solid #d4a574;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }
            .section h3 {
                margin: 0 0 10px 0;
                color: #333;
                font-size: 16px;
            }
            .section p {
                margin: 5px 0;
                font-size: 14px;
                color: #666;
            }
            .error {
                background: #fee;
                border-color: #f44;
                color: #c00;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid #f44;
            }
            .success {
                background: #efe;
                border-color: #4f4;
                color: #040;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid #4f4;
            }
            button {
                background: #d4a574;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
                font-weight: 600;
                transition: background 0.3s;
                margin: 20px 0;
            }
            button:hover {
                background: #b8905f;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .info-box {
                background: #fef3e6;
                border: 1px solid #f0c674;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }
            .info-box h4 {
                margin: 0 0 10px 0;
                color: #8b6914;
            }
            .info-box ul {
                margin: 0;
                padding-left: 20px;
            }
            .info-box li {
                margin: 5px 0;
                color: #666;
                font-size: 14px;
            }
            .loading {
                display: inline-block;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .last-run {
                text-align: center;
                color: #999;
                font-size: 12px;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 NKB Close Cash Report</h1>
            <p class="subtitle">Generate daily report with AI analysis</p>
            
            <div class="section">
                <h3>🕐 Automatic Schedule</h3>
                <p>Report automatically generates daily at <strong>12:00 AM IST</strong></p>
                <p>Results emailed to: <strong>nkblifestylebrands@gmail.com</strong></p>
            </div>
            
            <div class="section">
                <h3>🚀 Manual Trigger</h3>
                <p>Click below to generate report immediately</p>
            </div>
            
            <div id="message"></div>
            
            <button id="generateBtn" onclick="generateReport()">🎯 Generate Report Now</button>
            
            <div class="info-box">
                <h4>✅ What This Does:</h4>
                <ul>
                    <li>Reads all 13 store close cash sheets</li>
                    <li>Analyzes performance with Claude AI</li>
                    <li>Identifies underperformance & expense spikes</li>
                    <li>Generates professional report</li>
                    <li>Sends via email</li>
                </ul>
            </div>
            
            <div class="last-run">
                <p>⏰ Last report: <span id="lastRun">Never</span></p>
            </div>
        </div>
        
        <script>
            async function generateReport() {
                const btn = document.getElementById('generateBtn');
                const msg = document.getElementById('message');
                
                btn.disabled = true;
                btn.innerHTML = '<span class="loading">⏳</span> Generating...';
                msg.innerHTML = '';
                
                try {
                    const response = await fetch('/api/generate-report', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        msg.innerHTML = '<div class="success">✅ Report generated successfully and email sent!</div>';
                        document.getElementById('lastRun').textContent = new Date().toLocaleString();
                    } else {
                        msg.innerHTML = '<div class="error">❌ Error: ' + (data.error || 'Failed to generate report') + '</div>';
                    }
                } catch (error) {
                    msg.innerHTML = '<div class="error">❌ Error: ' + error.message + '</div>';
                }
                
                btn.disabled = false;
                btn.innerHTML = '🎯 Generate Report Now';
            }
            
            fetch('/api/last-run')
                .then(r => r.json())
                .then(d => {
                    document.getElementById('lastRun').textContent = d.last_run || 'Never';
                });
        </script>
    </body>
    </html>
    """

@app.route('/api/generate-report', methods=['POST'])
def api_generate_report():
    try:
        result = generate_report()
        return jsonify({
            "success": result,
            "message": "Report generated and emailed" if result else "Report generation failed"
        })
    except Exception as e:
        print(f"Error in API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/last-run', methods=['GET'])
def api_last_run():
    return jsonify({"last_run": "See email inbox"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
