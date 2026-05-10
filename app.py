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
                return '<div class="error">❌ Error: No date provided</div>'
            try:
                # custom_date comes as YYYY-MM-DD from HTML date picker
                custom_date_obj = datetime.strptime(custom_date, '%Y-%m-%d')
                start_date = end_date = custom_date_obj.strftime('%d-%m-%Y')
            except Exception as e:
                return f'<div class="error">❌ Invalid date format: {str(e)}</div>'
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
                    <td colspan="6" style="text-align: center; color: #aaa;">No data for this date</td>
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
        import traceback
        return f'<div class="error">❌ Error: {str(e)}</div>'
