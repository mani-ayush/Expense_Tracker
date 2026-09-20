import os
import io
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import pandas as pd
import backend

app = Flask(__name__)
CORS(app)

# Initialize backend data
backend.init_tracker()

REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    df = backend.get_expense_dataframe()
    if df.empty:
        return jsonify([])
    
    expenses = []
    for idx, row in df.iterrows():
        dt_str = row['DATES'].strftime('%Y-%m-%d') if hasattr(row['DATES'], 'strftime') else str(row['DATES'])[:10]
        expenses.append({
            'id': int(idx),
            'good_or_service': row['GOODS_OR_SERVICES'],
            'price': float(row['PRICES']),
            'date': dt_str,
            'expense_type': row['EXPENSE_TYPE']
        })
    # Most recent first
    expenses.reverse()
    return jsonify(expenses)

@app.route('/api/add', methods=['POST'])
def add_expense_api():
    data = request.json or request.form
    good_or_service = data.get('good_or_service', '').strip()
    price_val = data.get('price')
    date_str = data.get('date', '').strip()
    expense_type = data.get('expense_type', '').strip()

    if not good_or_service:
        return jsonify({'success': False, 'error': 'Item/Service name is required'}), 400
    try:
        price = float(price_val)
        if price <= 0:
            return jsonify({'success': False, 'error': 'Price must be greater than 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Valid price is required'}), 400

    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'Date must be in YYYY-MM-DD format'}), 400

    if not expense_type:
        expense_type = 'FOOD'

    backend.add_expense(good_or_service, price, dt, expense_type)
    return jsonify({'success': True, 'message': 'Expense added successfully'})

@app.route('/api/edit', methods=['POST'])
def edit_expense_api():
    data = request.json or request.form
    try:
        idx = int(data.get('id'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid expense ID'}), 400

    good_or_service = data.get('good_or_service', '').strip()
    price_val = data.get('price')
    date_str = data.get('date', '').strip()
    expense_type = data.get('expense_type', '').strip()

    if not good_or_service:
        return jsonify({'success': False, 'error': 'Item/Service name is required'}), 400
    try:
        price = float(price_val)
        if price <= 0:
            return jsonify({'success': False, 'error': 'Price must be greater than 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Valid price is required'}), 400

    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'Date must be in YYYY-MM-DD format'}), 400

    success = backend.edit_expense(idx, good_or_service, price, dt, expense_type)
    if success:
        return jsonify({'success': True, 'message': 'Expense updated successfully'})
    else:
        return jsonify({'success': False, 'error': 'Expense not found'}), 404

@app.route('/api/delete', methods=['POST'])
def delete_expense_api():
    data = request.json or request.form
    try:
        idx = int(data.get('id'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid expense ID'}), 400

    success = backend.delete_expense(idx)
    if success:
        return jsonify({'success': True, 'message': 'Expense deleted successfully'})
    else:
        return jsonify({'success': False, 'error': 'Expense not found'}), 404

@app.route('/api/summary', methods=['GET'])
def get_summary():
    df = backend.get_expense_dataframe()
    total_expense = backend.calculate_total_expense()
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_expense = 0.0
    this_week_expense = 0.0
    
    category_totals = {}
    daily_totals = {}
    weekly_totals = {}

    if not df.empty:
        # Today's expense
        df_today = df[df['DATES'].dt.strftime('%Y-%m-%d') == today_str]
        today_expense = float(df_today['PRICES'].sum())

        # This week's expense (last 7 days or current ISO week)
        start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        df_this_week = df[df['DATES'] >= start_of_week]
        this_week_expense = float(df_this_week['PRICES'].sum())

        # Category breakdown
        cat_series = backend.calculate_category_expense(df)
        category_totals = {k: float(v) for k, v in cat_series.items()}

        # Daily breakdown (grouped by day, non-zero)
        daily_series = backend.calculate_daily_expense(df)
        for d, amt in daily_series.items():
            if amt > 0:
                daily_totals[d.strftime('%Y-%m-%d')] = float(amt)

        # Weekly breakdown
        weekly_series = backend.calculate_weekly_expense(df)
        for w, amt in weekly_series.items():
            if amt > 0:
                weekly_totals[f"Week of {w.strftime('%b %d, %Y')}"] = float(amt)

    return jsonify({
        'total_expense': round(total_expense, 2),
        'today_expense': round(today_expense, 2),
        'this_week_expense': round(this_week_expense, 2),
        'total_transactions': len(backend.GOODS_OR_SERVICES),
        'category_breakdown': category_totals,
        'daily_breakdown': daily_totals,
        'weekly_breakdown': weekly_totals
    })

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    report_type = request.args.get('type', 'all').upper()
    df = backend.get_expense_dataframe()
    now_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')

    if df.empty:
        return "No expenses to export", 400

    filename = f"expense_report_{report_type}_{now_str}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)

    if report_type == 'DAILY':
        daily_series = backend.calculate_daily_expense(df)
        daily_df = daily_series[daily_series > 0].reset_index()
        daily_df.columns = ['DATE', 'TOTAL_EXPENSE']
        daily_df['DATE'] = daily_df['DATE'].dt.strftime('%Y-%m-%d')
        backend.save_data_to_csv(daily_df, filepath)
    elif report_type == 'WEEKLY':
        weekly_series = backend.calculate_weekly_expense(df)
        weekly_df = weekly_series[weekly_series > 0].reset_index()
        weekly_df.columns = ['WEEK_ENDING', 'TOTAL_EXPENSE']
        weekly_df['WEEK_ENDING'] = weekly_df['WEEK_ENDING'].dt.strftime('%Y-%m-%d')
        backend.save_data_to_csv(weekly_df, filepath)
    else:
        df_export = df.copy()
        df_export['DATES'] = df_export['DATES'].dt.strftime('%Y-%m-%d')
        backend.save_data_to_csv(df_export, filepath)

    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/csv')

@app.route('/api/export/jpeg', methods=['GET'])
def export_jpeg():
    report_type = request.args.get('type', 'DAILY').upper()
    df = backend.get_expense_dataframe()
    if df.empty:
        return "No expenses to generate chart", 400

    now_str = datetime.now().strftime("%Y-%m-%d")
    title = f"{now_str}_{report_type}"
    filename = f"{report_type.lower()}_expense_report_{now_str}.jpeg"
    filepath = os.path.join(REPORTS_DIR, filename)

    backend.save_data_to_jpeg(df, title, filepath)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='image/jpeg')

@app.route('/api/import/csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    try:
        temp_path = os.path.join(REPORTS_DIR, 'uploaded_temp.csv')
        file.save(temp_path)
        data = backend.load_data_from_csv(temp_path)
        if data is not None:
            backend.auto_save()
            return jsonify({'success': True, 'message': f'Successfully imported {len(backend.GOODS_OR_SERVICES)} expenses'})
        else:
            return jsonify({'success': False, 'error': 'Invalid CSV format. Must contain: GOODS_OR_SERVICES, PRICES, DATES, EXPENSE_TYPE'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# AI DRIVEN ANALYTICS & WEALTH ADVISORY APIS
# ==========================================

@app.route('/api/ai/insights', methods=['GET'])
def get_ai_insights():
    df = backend.get_expense_dataframe()
    budget = float(request.args.get('budget', 25000.0))
    risk_profile = request.args.get('risk', 'BALANCED').upper()

    now = datetime.now()
    cur_month_prefix = f"{now.year}-{str(now.month).zfill(2)}"
    df_cur = df[df['DATES'].dt.strftime('%Y-%m') == cur_month_prefix] if not df.empty else df
    cur_spent = float(df_cur['PRICES'].sum()) if not df_cur.empty else 0.0
    surplus = max(0.0, budget - cur_spent)

    comparison = backend.get_monthly_comparison(df)
    peer_benchmarks = backend.get_peer_benchmarking(df)
    investment_plan = backend.generate_ai_investment_suggestions(surplus, risk_profile)
    smart_insights = backend.get_ai_smart_insights(df, budget)

    return jsonify({
        'success': True,
        'surplus': surplus,
        'current_month_spent': cur_spent,
        'budget': budget,
        'monthly_comparison': comparison,
        'peer_benchmarking': peer_benchmarks,
        'investment_plan': investment_plan,
        'smart_insights': smart_insights
    })

@app.route('/api/ai/advisor', methods=['POST'])
def ai_advisor_query():
    data = request.json or {}
    query = data.get('query', '').lower().strip()
    budget = float(data.get('budget', 25000.0))
    risk_profile = data.get('risk', 'BALANCED').upper()

    df = backend.get_expense_dataframe()
    now = datetime.now()
    cur_month_prefix = f"{now.year}-{str(now.month).zfill(2)}"
    df_cur = df[df['DATES'].dt.strftime('%Y-%m') == cur_month_prefix] if not df.empty else df
    cur_spent = float(df_cur['PRICES'].sum()) if not df_cur.empty else 0.0
    surplus = max(0.0, budget - cur_spent)
    comparison = backend.get_monthly_comparison(df)
    plan = backend.generate_ai_investment_suggestions(surplus, risk_profile)

    # Intelligent financial AI bot responses
    if 'invest' in query or 'gold' in query or 'stock' in query or 'infra' in query or 'market' in query:
        response_text = (
            f"🤖 **FinWise AI Investment Bot Analysis:**\n\n"
            f"With your current monthly surplus of **Rs {surplus:,.0f}** and a **{risk_profile.title()}** risk profile, "
            f"the AI Wealth Engine recommends:\n\n"
            f"• 🪙 **Gold (SGBs / Digital Gold - {plan['allocations'][0]['percentage']}%):** Invest **Rs {plan['allocations'][0]['amount']:,.0f}** to hedge against macroeconomic volatility.\n"
            f"• 🏗️ **Infrastructure / REITs ({plan['allocations'][1]['percentage']}%):** Deploy **Rs {plan['allocations'][1]['amount']:,.0f}** into public infrastructure trusts yielding ~{plan['allocations'][1]['expected_cagr']} steady returns.\n"
            f"• 📈 **Equities & Stock Market ({plan['allocations'][2]['percentage']}%):** Channel **Rs {plan['allocations'][2]['amount']:,.0f}** into broad market index (Nifty 50) and high-quality flexi-cap funds for ~{plan['allocations'][2]['expected_cagr']} growth.\n"
            f"• 🛡️ **Liquid Emergency Buffer ({plan['allocations'][3]['percentage']}%):** Keep **Rs {plan['allocations'][3]['amount']:,.0f}** in high-yield liquid funds for liquidity.\n\n"
            f"💡 **10-Year Compounding Projection:** Sustaining this SIP could grow into **Rs {plan['projected_10yr_wealth']:,.0f}** over 10 years at ~12% CAGR!"
        )
    elif 'peer' in query or 'other user' in query or 'compare' in query or 'average' in query:
        benchmarks = backend.get_peer_benchmarking(df)
        b_text = "\n".join([f"• **{b['category']}**: You allocate **{b['user_pct']}%** vs peer benchmark **{b['peer_pct']}%** ({b['badge']})" for b in benchmarks])
        response_text = (
            f"🤖 **FinWise AI Peer Benchmarking Intelligence:**\n\n"
            f"Here is how your spending distribution compares against thousands of peer profiles:\n\n"
            f"{b_text}\n\n"
            f"💡 **AI Takeaway:** Your financial profile shows strong discipline in non-discretionary sectors, giving you higher capacity for capital compounding."
        )
    elif 'reduce' in query or 'save' in query or 'budget' in query or 'cut' in query:
        cat_series = df.groupby('EXPENSE_TYPE')['PRICES'].sum()
        top_cat = cat_series.idxmax() if not cat_series.empty else 'Expenses'
        top_amt = cat_series.max() if not cat_series.empty else 0
        response_text = (
            f"🤖 **FinWise AI Cost-Cutting & Savings Strategy:**\n\n"
            f"1. **Primary Target:** Your largest spending center is **{top_cat}** (Rs {top_amt:,.0f}). Reducing this by just 10% unlocks **Rs {(top_amt * 0.1):,.0f}** extra every month.\n"
            f"2. **Pacing:** Month-over-month, your spend trajectory is **{comparison.get('pct_change', 0)}% {comparison.get('direction', 'FLAT').lower()}** compared to last month.\n"
            f"3. **Micro-Habit Rule:** Redirect 50% of any daily discretionary savings straight into your automated gold/index investment bucket before spending."
        )
    else:
        response_text = (
            f"🤖 **FinWise AI Bot Financial Status:**\n\n"
            f"• Current Month Spend: **Rs {cur_spent:,.0f}** of **Rs {budget:,.0f}** ({round(cur_spent/budget*100 if budget else 0)}% utilized)\n"
            f"• Available Surplus for Investment: **Rs {surplus:,.0f}**\n"
            f"• Month-over-Month Delta: **{comparison.get('pct_change', 0)}%** ({comparison.get('direction', 'FLAT')})\n"
            f"• Recommendation: You have positive surplus bandwidth. Allocate into the **{plan['strategy_name']}** to maximize your compounding rate!"
        )

    return jsonify({
        'success': True,
        'response': response_text,
        'plan': plan
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

