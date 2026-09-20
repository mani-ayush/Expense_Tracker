@echo off
echo ========================================================
echo Starting Expense Tracker Pro - Modern Web Interface
echo ========================================================
cd /d "%~dp0"
start http://127.0.0.1:5000
python app.py
pause
