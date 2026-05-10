#!/usr/bin/env python3
from flask import Flask, jsonify
from nkb_automation import generate_report
import os

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
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #d4a574; }
            .section { background: #f9f9f9; padding: 15px; margin: 15px 0; border-left: 4px solid #d4a574; }
            button { background: #d4a574; color: white; border: none; padding: 12px 30px; font-size: 16px; border-radius: 4px; cursor: pointer; width: 100%; }
            button:hover { background: #b8905f; }
            button:disabled { background: #ccc; }
            .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 4px; margin: 15px 0; }
            .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px; margin: 15px 0; }
            .info { font-size: 12px; color: #666; text-align: center; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 NKB Close Cash Report</h1>
            <p>Generate daily report with AI analysis</p>
            
            <div class="section">
                <h3>🕐 Automatic Schedule</h3>
                <p>Report automatically generates daily at <strong>12:00 AM IST</strong></p>
                <p>Results emailed to: <strong>nkblifestylebrands@gmail.com</strong></p>
            </div>
            
            <div id="message"></div>
            
            <button id="btn" onclick="generateReport()">🎯 Generate Report Now</button>
            
            <div class="info">
                ✅ Reads all 13 stores | 📊 Analyzes data | 📧 Sends email
            </div>
        </div>
        
        <script>
            async function generateReport() {
                const btn = document.getElementById('btn');
                const msg = document.getElementById('message');
                
                btn.disabled = true;
                btn.textContent = '⏳ Generating...';
                msg.innerHTML = '';
                
                try {
                    const response = await fetch('/generate', {method: 'POST'});
                    const text = await response.text();
                    
                    if (response.ok) {
                        msg.innerHTML = '<div class="success">✅ Report generated and email sent!</div>';
                    } else {
                        msg.innerHTML = '<div class="error">❌ Error: ' + text + '</div>';
                    }
                } catch (e) {
                    msg.innerHTML = '<div class="error">❌ Error: ' + e.message + '</div>';
                }
                
                btn.disabled = false;
                btn.textContent = '🎯 Generate Report Now';
            }
        </script>
    </body>
    </html>
    """

@app.route('/generate', methods=['POST'])
def api_generate():
    try:
        result = generate_report()
        if result:
            return "Success", 200
        else:
            return "Generation failed", 500
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
