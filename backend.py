import os
import csv
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Headless backend for web/API compatibility
import matplotlib.pyplot as plt

# Default in-memory lists (preserving user's original architecture)
GOODS_OR_SERVICES = []
PRICES = []
DATES = []
EXPENSE_TYPE = []
WEEKLY_EXPENSE_REPORTS = {}
DAILY_EXPENSE_REPORTS = {}

DATA_FILE = os.path.join(os.path.dirname(__file__), 'expenses_data.csv')

def clear_all_data():
    """Clear all expenses from memory and storage for a fresh start."""
    global GOODS_OR_SERVICES, PRICES, DATES, EXPENSE_TYPE
    GOODS_OR_SERVICES.clear()
    PRICES.clear()
    DATES.clear()
    EXPENSE_TYPE.clear()
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

def add_expense(good_or_service, price, date, expense_type, persist=True):
    """Add a new expense item and optionally save to CSV."""
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    GOODS_OR_SERVICES.append(good_or_service)
    PRICES.append(float(price))
    DATES.append(date)
    EXPENSE_TYPE.append(expense_type.upper().strip())
    
    if persist:
        auto_save()

def edit_expense(index, good_or_service, price, date, expense_type):
    """Edit an existing expense by index."""
    if 0 <= index < len(GOODS_OR_SERVICES):
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        GOODS_OR_SERVICES[index] = good_or_service
        PRICES[index] = float(price)
        DATES[index] = date
        EXPENSE_TYPE[index] = expense_type.upper().strip()
        auto_save()
        return True
    return False

def delete_expense(index):
    """Delete an expense by index."""
    if 0 <= index < len(GOODS_OR_SERVICES):
        GOODS_OR_SERVICES.pop(index)
        PRICES.pop(index)
        DATES.pop(index)
        EXPENSE_TYPE.pop(index)
        auto_save()
        return True
    return False

def calculate_total_expense():
    """Calculate total expenses."""
    return float(sum(PRICES))

def get_expense_dataframe():
    """Return current expenses as a pandas DataFrame."""
    if not GOODS_OR_SERVICES:
        return pd.DataFrame(columns=['GOODS_OR_SERVICES', 'PRICES', 'DATES', 'EXPENSE_TYPE'])
    
    df = pd.DataFrame({
        'GOODS_OR_SERVICES': GOODS_OR_SERVICES,
        'PRICES': PRICES,
        'DATES': DATES,
        'EXPENSE_TYPE': EXPENSE_TYPE
    })
    df['DATES'] = pd.to_datetime(df['DATES'])
    return df

def calculate_weekly_expense(expense_report=None):
    """Calculate weekly expenses by grouping by week and summing the prices."""
    if expense_report is None:
        expense_report = get_expense_dataframe()
    if expense_report.empty:
        return pd.Series(dtype=float)
    
    weekly_expense = expense_report.groupby(pd.Grouper(key='DATES', freq='W'))['PRICES'].sum()
    return weekly_expense

def calculate_daily_expense(expense_report=None):
    """Calculate daily expenses by grouping by day and summing the prices."""
    if expense_report is None:
        expense_report = get_expense_dataframe()
    if expense_report.empty:
        return pd.Series(dtype=float)
    
    daily_expense = expense_report.groupby(pd.Grouper(key='DATES', freq='D'))['PRICES'].sum()
    return daily_expense

def calculate_category_expense(expense_report=None):
    """Calculate expense totals grouped by category."""
    if expense_report is None:
        expense_report = get_expense_dataframe()
    if expense_report.empty:
        return pd.Series(dtype=float)
    return expense_report.groupby('EXPENSE_TYPE')['PRICES'].sum()

def save_data_to_jpeg(expense_report, title, filename):
    """Save data visualization as a high-quality JPEG image."""
    plt.figure(figsize=(9, 5), dpi=150)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    if 'WEEKLY' in title:
        if 'EXPENSE_TYPE' in expense_report.columns:
            cat_totals = expense_report.groupby('EXPENSE_TYPE')['PRICES'].sum()
            labels = cat_totals.index
            sizes = cat_totals.values
        else:
            labels = [str(x) for x in expense_report.index]
            sizes = expense_report['PRICES'].values
            
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, 
                colors=colors[:len(sizes)], wedgeprops=dict(width=0.7, edgecolor='w'))
        plt.title(title, fontsize=14, pad=15, fontweight='bold')
    elif 'DAILY' in title:
        if 'DATES' in expense_report.columns:
            daily_grouped = expense_report.groupby(pd.Grouper(key='DATES', freq='D'))['PRICES'].sum()
            daily_grouped = daily_grouped[daily_grouped > 0]
            dates_formatted = [d.strftime('%b %d') for d in daily_grouped.index]
            prices = daily_grouped.values
        else:
            dates_formatted = [str(x) for x in expense_report.index]
            prices = expense_report['PRICES'].values
        bars = plt.bar(dates_formatted, prices, color='#3b82f6', edgecolor='#1d4ed8', width=0.55)
        plt.xlabel('Date', fontweight='bold', labelpad=8)
        plt.ylabel('Price (Rs)', fontweight='bold', labelpad=8)
        plt.xticks(rotation=45, ha='right')
        plt.title(title, fontsize=14, pad=15, fontweight='bold')
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.annotate(f'{height:.0f}',
                             xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 3),
                             textcoords="offset points",
                             ha='center', va='bottom', fontsize=9)
    else:
        plt.bar(expense_report.index.astype(str), expense_report['PRICES'], color='#10b981')
        plt.title(title)
    plt.tight_layout()
    plt.savefig(filename, format='jpeg')
    plt.close()

def save_data_to_csv(data, filename):
    """Save DataFrame to CSV."""
    if isinstance(data, pd.DataFrame):
        data.to_csv(filename, index=False)
    elif isinstance(data, pd.Series):
        data.reset_index().to_csv(filename, index=False)

def load_data_from_csv(filename):
    """Load expenses from CSV file into memory."""
    global GOODS_OR_SERVICES, PRICES, DATES, EXPENSE_TYPE
    if not os.path.exists(filename):
        return None
    try:
        data = pd.read_csv(filename)
        required = {'GOODS_OR_SERVICES', 'PRICES', 'DATES', 'EXPENSE_TYPE'}
        if not required.issubset(set(data.columns)):
            return None
        
        data['DATES'] = pd.to_datetime(data['DATES'])
        GOODS_OR_SERVICES.clear()
        PRICES.clear()
        DATES.clear()
        EXPENSE_TYPE.clear()
        
        for _, row in data.iterrows():
            GOODS_OR_SERVICES.append(str(row['GOODS_OR_SERVICES']))
            PRICES.append(float(row['PRICES']))
            DATES.append(row['DATES'].to_pydatetime() if hasattr(row['DATES'], 'to_pydatetime') else row['DATES'])
            EXPENSE_TYPE.append(str(row['EXPENSE_TYPE']).upper().strip())
        return data
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def auto_save():
    """Auto-persist memory state to DATA_FILE."""
    df = get_expense_dataframe()
    if not df.empty:
        df_to_save = df.copy()
        df_to_save['DATES'] = df_to_save['DATES'].dt.strftime('%Y-%m-%d')
        save_data_to_csv(df_to_save, DATA_FILE)

def init_tracker():
    """Initialize tracker on start: load existing saved file or create defaults."""
    if os.path.exists(DATA_FILE):
        load_data_from_csv(DATA_FILE)
    else:
        load_sample_data()

def load_sample_data():
    """Populate realistic sample expenses spanning previous and current months."""
    today = datetime.now()
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - pd.Timedelta(days=1)
    
    sample_items = [
        ("Monthly Grocery Supplies", 3800.0, (last_month_end - pd.Timedelta(days=15)).strftime('%Y-%m-%d'), "FOOD"),
        ("Electricity & Maintenance", 2600.0, (last_month_end - pd.Timedelta(days=12)).strftime('%Y-%m-%d'), "HOUSEHOLD"),
        ("Cab Rides & Metro Card", 950.0, (last_month_end - pd.Timedelta(days=10)).strftime('%Y-%m-%d'), "TRANSPORTATION"),
        ("School Semester Fee", 4000.0, (last_month_end - pd.Timedelta(days=5)).strftime('%Y-%m-%d'), "SCHOOL FEE"),
        ("Weekend Cafe & Dining", 1400.0, (last_month_end - pd.Timedelta(days=2)).strftime('%Y-%m-%d'), "FOOD"),
        ("Supermarket Weekly Grocery", 850.0, (today - pd.Timedelta(days=4)).strftime('%Y-%m-%d'), "FOOD"),
        ("High-speed Fiber & Utility", 2400.0, (today - pd.Timedelta(days=3)).strftime('%Y-%m-%d'), "HOUSEHOLD"),
        ("Fuel & Metro Recharge", 650.0, (today - pd.Timedelta(days=2)).strftime('%Y-%m-%d'), "TRANSPORTATION"),
        ("Tuition Materials & Books", 3500.0, (today - pd.Timedelta(days=1)).strftime('%Y-%m-%d'), "SCHOOL FEE"),
        ("Special Family Dinner", 1200.0, today.strftime('%Y-%m-%d'), "FOOD"),
        ("Home Sanitization Supplies", 350.0, today.strftime('%Y-%m-%d'), "HOUSEHOLD"),
    ]
    for good, price, dt, exp_type in sample_items:
        add_expense(good, price, dt, exp_type, persist=False)
    auto_save()

# AI DRIVEN ANALYTICS & WEALTH ADVISORY
def get_monthly_comparison(df=None):
    if df is None:
        df = get_expense_dataframe()
    if df.empty:
        return {'has_data': False}
    now = datetime.now()
    cur_year, cur_month = now.year, now.month
    if cur_month == 1:
        prev_year, prev_month = cur_year - 1, 12
    else:
        prev_year, prev_month = cur_year, cur_month - 1
    df_cur = df[(df['DATES'].dt.year == cur_year) & (df['DATES'].dt.month == cur_month)]
    df_prev = df[(df['DATES'].dt.year == prev_year) & (df['DATES'].dt.month == prev_month)]
    cur_total = float(df_cur['PRICES'].sum())
    prev_total = float(df_prev['PRICES'].sum())
    pct_change = round(((cur_total - prev_total) / prev_total) * 100, 1) if prev_total > 0 else 0.0
    
    cur_cat = df_cur.groupby('EXPENSE_TYPE')['PRICES'].sum().to_dict()
    prev_cat = df_prev.groupby('EXPENSE_TYPE')['PRICES'].sum().to_dict()
    cat_comparison = {}
    all_cats = set(cur_cat.keys()).union(set(prev_cat.keys()))
    for cat in all_cats:
        c_val = cur_cat.get(cat, 0.0)
        p_val = prev_cat.get(cat, 0.0)
        diff_pct = round(((c_val - p_val) / p_val * 100), 1) if p_val > 0 else (100.0 if c_val > 0 else 0.0)
        cat_comparison[cat] = {
            'current': round(c_val, 2),
            'previous': round(p_val, 2),
            'diff_pct': diff_pct,
            'direction': 'UP' if diff_pct > 0 else ('DOWN' if diff_pct < 0 else 'FLAT')
        }
    return {
        'has_data': True,
        'current_month_name': now.strftime('%B %Y'),
        'previous_month_name': datetime(prev_year, prev_month, 1).strftime('%B %Y'),
        'current_total': round(cur_total, 2),
        'previous_total': round(prev_total, 2),
        'pct_change': pct_change,
        'direction': 'HIGHER' if pct_change > 0 else ('LOWER' if pct_change < 0 else 'UNCHANGED'),
        'categories': cat_comparison
    }

def get_peer_benchmarking(df=None):
    if df is None:
        df = get_expense_dataframe()
    if df.empty:
        return []
    total_spent = df['PRICES'].sum()
    if total_spent <= 0:
        return []
    cat_totals = df.groupby('EXPENSE_TYPE')['PRICES'].sum()
    peer_benchmarks = {
        'FOOD': 32.0,
        'HOUSEHOLD': 34.0,
        'TRANSPORTATION': 16.0,
        'SCHOOL FEE': 18.0
    }
    results = []
    for cat, peer_pct in peer_benchmarks.items():
        user_amt = float(cat_totals.get(cat, 0.0))
        user_pct = round((user_amt / total_spent) * 100, 1)
        variance = round(user_pct - peer_pct, 1)
        if variance > 5.0:
            status, color, badge = 'Overspending', 'amber', f"+{variance}% higher than peers"
        elif variance < -5.0:
            status, color, badge = 'Super Saver', 'emerald', f"{abs(variance)}% leaner than peers"
        else:
            status, color, badge = 'Balanced', 'blue', "Matches peer standard"
        results.append({
            'category': cat, 'user_pct': user_pct, 'peer_pct': peer_pct,
            'variance': variance, 'status': status, 'color': color, 'badge': badge
        })
    return results

def generate_ai_investment_suggestions(surplus_amount, risk_profile='BALANCED'):
    surplus = max(0.0, float(surplus_amount))
    risk = (risk_profile or 'BALANCED').upper()
    if risk == 'CONSERVATIVE':
        strategy_name = "Capital Preservation & Inflation Hedge"
        weights = {
            'GOLD': {'pct': 25, 'title': 'Sovereign Gold Bonds & Digital Gold', 'cagr': '10-12%', 'icon': 'coins', 'risk': 'Low-Medium'},
            'INFRA': {'pct': 30, 'title': 'Infrastructure InvITs & High-Yield Debt', 'cagr': '8.5-10%', 'icon': 'building-2', 'risk': 'Low'},
            'STOCKS': {'pct': 20, 'title': 'Nifty 50 Index Fund & Blue-Chips', 'cagr': '12-14%', 'icon': 'trending-up', 'risk': 'Medium'},
            'EMERGENCY': {'pct': 25, 'title': 'Liquid Funds / High-Yield Savings', 'cagr': '6.5-7.5%', 'icon': 'shield-check', 'risk': 'Very Low'}
        }
        ai_summary = "Prioritizes capital safety with substantial gold and high-grade infrastructure debt."
    elif risk == 'AGGRESSIVE':
        strategy_name = "Aggressive Wealth Compounding"
        weights = {
            'GOLD': {'pct': 10, 'title': 'Gold ETFs & Commodities', 'cagr': '10-12%', 'icon': 'coins', 'risk': 'Low-Medium'},
            'INFRA': {'pct': 15, 'title': 'Public Infrastructure Real Assets / REITs', 'cagr': '9-11%', 'icon': 'building-2', 'risk': 'Medium'},
            'STOCKS': {'pct': 65, 'title': 'Equities, Flexi-Cap & Mid-Cap Growth', 'cagr': '14-18%', 'icon': 'trending-up', 'risk': 'High'},
            'EMERGENCY': {'pct': 10, 'title': 'Liquid Emergency Cushion', 'cagr': '6.5-7.5%', 'icon': 'shield-check', 'risk': 'Very Low'}
        }
        ai_summary = "Maximizes equity exposure in high-growth index and mid-cap funds."
    else:
        strategy_name = "Balanced Wealth & Growth Engine"
        weights = {
            'GOLD': {'pct': 15, 'title': 'Digital Gold & Sovereign Gold Bonds', 'cagr': '10-12%', 'icon': 'coins', 'risk': 'Low-Medium'},
            'INFRA': {'pct': 25, 'title': 'Infrastructure Trusts (InvITs) & Commercial REITs', 'cagr': '9-10.5%', 'icon': 'building-2', 'risk': 'Medium'},
            'STOCKS': {'pct': 45, 'title': 'Broad Market Index (Nifty 50) + Flexi-Cap', 'cagr': '13-15%', 'icon': 'trending-up', 'risk': 'Medium-High'},
            'EMERGENCY': {'pct': 15, 'title': 'High-Yield Liquid Emergency Fund', 'cagr': '6.5-7.5%', 'icon': 'shield-check', 'risk': 'Very Low'}
        }
        ai_summary = "Optimal balance between growth equities, steady commercial infrastructure dividends, and gold stability."
    
    allocations = []
    for key, info in weights.items():
        allocated_amt = round((surplus * info['pct']) / 100.0, 2)
        allocations.append({
            'asset_class': key, 'name': info['title'], 'percentage': info['pct'],
            'amount': allocated_amt, 'expected_cagr': info['cagr'], 'risk_level': info['risk'], 'icon': info['icon']
        })
    blended_cagr = 0.12
    monthly_sip = surplus if surplus > 0 else 5000.0
    ten_year_corpus = monthly_sip * (((1 + blended_cagr/12)**(120) - 1) / (blended_cagr/12)) * (1 + blended_cagr/12)
    return {
        'surplus_budget': round(surplus, 2), 'risk_profile': risk, 'strategy_name': strategy_name,
        'ai_rationale': ai_summary, 'allocations': allocations, 'projected_10yr_wealth': round(ten_year_corpus, 2)
    }

def get_ai_smart_insights(df=None, monthly_budget=25000.0):
    if df is None:
        df = get_expense_dataframe()
    if df.empty:
        return ["Add your initial expenses to activate AI intelligence."]
    insights = []
    now = datetime.now()
    cur_month_prefix = f"{now.year}-{str(now.month).zfill(2)}"
    df_cur = df[df['DATES'].dt.strftime('%Y-%m') == cur_month_prefix]
    cur_spent = float(df_cur['PRICES'].sum()) if not df_cur.empty else 0.0
    surplus = max(0.0, monthly_budget - cur_spent)
    
    day_of_month = now.day
    days_in_month = 30
    month_progress_pct = (day_of_month / days_in_month) * 100
    spent_pct = (cur_spent / monthly_budget * 100) if monthly_budget > 0 else 0
    if spent_pct < month_progress_pct - 10:
        insights.append({'type': 'praise', 'title': 'High Savings Efficiency', 'icon': 'sparkles', 'text': f"You have used only {spent_pct:.0f}% of your budget."})
    elif spent_pct > month_progress_pct + 15:
        insights.append({'type': 'warning', 'title': 'Pacing Alert', 'icon': 'alert-triangle', 'text': f"Burn rate is elevated at {spent_pct:.0f}%."})
    else:
        insights.append({'type': 'info', 'title': 'Steady Budget Cadence', 'icon': 'gauge', 'text': f"Spending trajectory closely matches timeline."})
    
    if surplus > 2000:
        insights.append({'type': 'investment', 'title': 'Surplus Investment Signal', 'icon': 'trending-up', 'text': f"You have Rs {surplus:,.0f} in unspent budget!"})
    
    cat_series = df.groupby('EXPENSE_TYPE')['PRICES'].sum()
    if not cat_series.empty:
        top_cat = cat_series.idxmax()
        top_amt = cat_series.max()
        pct_of_total = (top_amt / df['PRICES'].sum()) * 100
        insights.append({'type': 'optimization', 'title': f'{top_cat.title()} Optimization', 'icon': 'lightbulb', 'text': f"{top_cat.title()} accounts for {pct_of_total:.0f}% of your expenses."})
    return insights