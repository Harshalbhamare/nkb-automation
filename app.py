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
