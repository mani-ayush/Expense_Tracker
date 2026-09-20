# Expense Tracker Pro 📊

A complete, modern, and user-friendly Expense Tracking application with rich financial analytics, daily/weekly aggregation, interactive visualizations, and automated CSV & JPEG reports.

Built with Python (Pandas, Matplotlib, Flask) and modern web technologies (Tailwind CSS, Chart.js, Lucide Icons), plus an included Native Desktop GUI (Tkinter).

🌐 **[Access the Live Web Application Here](https://budger-craft.onrender.com)**

---

## 🌟 Key Features

1. **4 Core Expense Categories + Custom Support**:
   - 🍔 **Food**: Groceries, dining, snacks
   - 🏠 **Household**: Utilities, bills, maintenance, repairs
   - 🚗 **Transportation**: Fuel, transit passes, taxis
   - 🎓 **School Fee**: Tuition, books, courses, exam fees
   - 📦 **Custom Categories**: Support for any custom category name

2. **Real-Time Financial Dashboard**:
   - **Total Expenses** (Rs.)
   - **Today's Expenses**
   - **This Week's Expenses**
   - **Total Transaction Count**

3. **Complete Usability & Management (CRUD)**:
   - **Quick Add Buttons**: 1-click category pre-selection
   - **Interactive Data Table**: Instant search, category filters, date filters, and reset
   - **Edit Data**: Update any expense in-place (resolves missing options 10 & 11)
   - **Delete Data**: Remove entries with safety confirmation
   - **Auto-Persistence**: All transactions are automatically saved to `expenses_data.csv`

4. **Visual Analytics & Exports**:
   - **Daily Bar Chart**: Day-by-day spending breakdown
   - **Weekly / Category Doughnut Chart**: Percentage breakdown across categories
   - **Save as JPEG**: Exports high-resolution JPEG charts matching `save_data_to_jpeg`
   - **Export CSV**: Download complete data, daily reports, or weekly reports as CSV
   - **Import CSV**: Easily upload previously exported or existing CSV expense sheets

---

## 🚀 How to Run Locally

### Option 1: Modern Web Dashboard (Recommended)
Double-click `run_web.bat` OR run:
```bash
python app.py
Then open your browser at:
👉 http://127.0.0.1:5000

Option 2: Standalone Desktop GUI
Double-click run_desktop.bat OR run:

Bash
python gui_desktop.py
This launches a native Windows desktop application window with live interactive tables and embedded Matplotlib charts.

📁 Project Structure
expense-tracker/
├── backend.py            # Core engine: Pandas calculations, Matplotlib JPEG export, auto-save
├── app.py                # Flask Web Server & REST API endpoints
├── gui_desktop.py        # Standalone Native Windows Tkinter GUI
├── templates/
│   └── index.html        # Modern dashboard layout with Tailwind CSS & Chart.js
├── static/
│   ├── css/style.css     # Badges, animations, styling
│   └── js/app.js         # Client-side reactivity, chart rendering, API hooks
├── expenses_data.csv     # Auto-saved transaction database
├── run_web.bat           # 1-click launcher for Web UI
├── run_desktop.bat       # 1-click launcher for Desktop GUI
└── README.md             # Documentation & guide






