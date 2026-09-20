// Expense Tracker UI JavaScript - v2.0
let allExpenses = [];
let filteredExpenses = [];
let dailyChartInstance = null;
let categoryChartInstance = null;
let currentSummaryData = null;

// State management (persisted in localStorage)
let currentCurrency = localStorage.getItem('currency') || 'Rs';
let monthlyBudget = parseFloat(localStorage.getItem('monthlyBudget')) || 25000;
let currentQuickRange = 'ALL';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Theme
    initTheme();

    // 2. Initialize Currency Dropdown
    const currencySelect = document.getElementById('currencySelect');
    if (currencySelect) currencySelect.value = currentCurrency;
    updateCurrencyLabels();

    // 3. Lucide icons init
    lucide.createIcons();

    // 4. Set Default modal date to today
    const todayStr = new Date().toISOString().split('T')[0];
    document.getElementById('dateInput').value = todayStr;
    document.getElementById('today-date-label').innerText = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    // 5. Initial data load
    loadAllData();

    // 6. Keyboard Shortcuts: 'N' to open Add Modal, 'Escape' to close
    document.addEventListener('keydown', (e) => {
        const isTyping = ['input', 'textarea', 'select'].includes(document.activeElement.tagName.toLowerCase());
        if (!isTyping) {
            if (e.key === 'n' || e.key === 'N') {
                e.preventDefault();
                openAddModal();
            }
        }
        if (e.key === 'Escape') {
            closeAddModal();
            closeImportModal();
            closeBudgetModal();
        }
    });
});

// --- THEME MANAGEMENT ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(savedTheme);
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    applyTheme(isDark ? 'light' : 'dark');
}

function applyTheme(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
        localStorage.setItem('theme', 'dark');
        if (themeIcon) themeIcon.setAttribute('data-lucide', 'sun');
    } else {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        if (themeIcon) themeIcon.setAttribute('data-lucide', 'moon');
    }
    lucide.createIcons();

    // Re-render charts with appropriate dark/light grid and text colors
    if (currentSummaryData) {
        renderDailyChart(currentSummaryData.daily_breakdown);
        renderCategoryChart(currentSummaryData.category_breakdown);
    }
}

// --- CURRENCY MANAGEMENT ---
function changeCurrency(newCurr) {
    currentCurrency = newCurr;
    localStorage.setItem('currency', newCurr);
    updateCurrencyLabels();
    renderExpenseTable(filteredExpenses);
    if (currentSummaryData) {
        updateSummaryUI(currentSummaryData);
    }
    showToast(`Currency changed to ${newCurr}`);
}

function updateCurrencyLabels() {
    document.querySelectorAll('.currency-label').forEach(el => {
        el.innerText = currentCurrency;
    });
}

function formatMoney(amount) {
    const num = Number(amount) || 0;
    return `${currentCurrency} ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// --- BUDGET MANAGEMENT ---
function openBudgetModal() {
    document.getElementById('budgetLimitInput').value = monthlyBudget;
    document.getElementById('budgetModal').classList.remove('hidden');
    document.getElementById('budgetLimitInput').focus();
}

function closeBudgetModal() {
    document.getElementById('budgetModal').classList.add('hidden');
}

function submitBudget(e) {
    e.preventDefault();
    const val = parseFloat(document.getElementById('budgetLimitInput').value);
    if (val > 0) {
        monthlyBudget = val;
        localStorage.setItem('monthlyBudget', val);
        closeBudgetModal();
        if (currentSummaryData) updateBudgetUI(currentSummaryData);
        showToast('Monthly budget updated!');
    }
}

function updateBudgetUI(summary) {
    // Calculate current month's expenses
    const now = new Date();
    const currentMonthPrefix = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    
    let monthSpent = 0;
    allExpenses.forEach(exp => {
        if (exp.date && exp.date.startsWith(currentMonthPrefix)) {
            monthSpent += exp.price;
        }
    });

    const percent = monthlyBudget > 0 ? Math.min(100, Math.round((monthSpent / monthlyBudget) * 100)) : 0;
    const remaining = Math.max(0, monthlyBudget - monthSpent);

    document.getElementById('budgetValuesText').innerText = `${formatMoney(monthSpent)} / ${formatMoney(monthlyBudget)}`;
    document.getElementById('budgetRemainingText').innerText = `${formatMoney(remaining)} remaining`;
    
    const pctLabel = document.getElementById('budgetPercentageText');
    pctLabel.innerText = `${percent}% Used`;

    const bar = document.getElementById('budgetProgressBar');
    bar.style.width = `${percent}%`;

    // Dynamic color coding based on threshold
    if (percent >= 90) {
        bar.className = 'bg-rose-500 h-3 rounded-full transition-all duration-500 ease-out';
        pctLabel.className = 'font-bold text-rose-600 dark:text-rose-400';
    } else if (percent >= 70) {
        bar.className = 'bg-amber-500 h-3 rounded-full transition-all duration-500 ease-out';
        pctLabel.className = 'font-bold text-amber-600 dark:text-amber-400';
    } else {
        bar.className = 'bg-emerald-500 h-3 rounded-full transition-all duration-500 ease-out';
        pctLabel.className = 'font-bold text-emerald-600 dark:text-emerald-400';
    }
}

// --- DATA FETCHING & SYNCHRONIZATION ---
async function loadAllData() {
    await Promise.all([fetchExpenses(), fetchSummary(), loadAIInsights()]);
}


async function fetchExpenses() {
    try {
        const res = await fetch('/api/expenses');
        allExpenses = await res.json();
        filteredExpenses = [...allExpenses];
        applyFilters();
    } catch (err) {
        console.error('Error fetching expenses:', err);
    }
}

async function fetchSummary() {
    try {
        const res = await fetch('/api/summary');
        currentSummaryData = await res.json();
        updateSummaryUI(currentSummaryData);
    } catch (err) {
        console.error('Error fetching summary:', err);
    }
}

function updateSummaryUI(data) {
    // Update KPIs
    document.getElementById('kpi-total').innerText = formatMoney(data.total_expense);
    document.getElementById('kpi-today').innerText = formatMoney(data.today_expense);
    document.getElementById('kpi-week').innerText = formatMoney(data.this_week_expense);
    document.getElementById('kpi-transactions').innerText = data.total_transactions;

    // Calculate Average expense & Top category
    const avg = data.total_transactions > 0 ? (data.total_expense / data.total_transactions) : 0;
    document.getElementById('kpi-avg').innerText = `Avg: ${formatMoney(avg)}`;

    const catBreakdown = data.category_breakdown || {};
    let topCat = '-';
    let maxVal = -1;
    for (const [cat, val] of Object.entries(catBreakdown)) {
        if (val > maxVal) {
            maxVal = val;
            topCat = cat;
        }
    }
    document.getElementById('kpi-top-cat').innerText = `Top Category: ${topCat}`;

    // Update Budget Tracker
    updateBudgetUI(data);

    // Render Summary Tables
    renderDailySummary(data.daily_breakdown);
    renderWeeklySummary(data.weekly_breakdown);

    // Render Charts
    renderDailyChart(data.daily_breakdown);
    renderCategoryChart(data.category_breakdown);
}

// --- TABLE RENDERING ---
function renderExpenseTable(expenses) {
    const tbody = document.getElementById('expensesTableBody');
    const emptyState = document.getElementById('emptyState');
    tbody.innerHTML = '';

    if (!expenses || expenses.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    emptyState.classList.add('hidden');

    expenses.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition group';

        const badgeClass = getBadgeClass(item.expense_type);

        tr.innerHTML = `
            <td class="py-3.5 px-5 text-slate-500 dark:text-slate-400 font-medium whitespace-nowrap">${formatDisplayDate(item.date)}</td>
            <td class="py-3.5 px-5 font-semibold text-slate-800 dark:text-slate-200">${escapeHtml(item.good_or_service)}</td>
            <td class="py-3.5 px-5">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${badgeClass}">
                    ${getCategoryIcon(item.expense_type)} ${escapeHtml(item.expense_type)}
                </span>
            </td>
            <td class="py-3.5 px-5 text-right font-bold text-slate-900 dark:text-white whitespace-nowrap">
                ${formatMoney(item.price)}
            </td>
            <td class="py-3.5 px-5 text-center whitespace-nowrap">
                <div class="flex items-center justify-center space-x-1">
                    <button onclick="editExpense(${item.id})" class="p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 rounded-lg transition" title="Edit Expense">
                        <i data-lucide="edit-3" class="w-4 h-4"></i>
                    </button>
                    <button onclick="deleteExpense(${item.id})" class="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/50 rounded-lg transition" title="Delete Expense">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    lucide.createIcons();
}

// Category Badge Helper
function getBadgeClass(category) {
    const cat = (category || '').toUpperCase();
    if (cat.includes('FOOD')) return 'badge-food';
    if (cat.includes('HOUSEHOLD')) return 'badge-household';
    if (cat.includes('TRANSPORT')) return 'badge-transportation';
    if (cat.includes('SCHOOL')) return 'badge-school-fee';
    return 'badge-default';
}

function getCategoryIcon(category) {
    const cat = (category || '').toUpperCase();
    if (cat.includes('FOOD')) return '🍔';
    if (cat.includes('HOUSEHOLD')) return '🏠';
    if (cat.includes('TRANSPORT')) return '🚗';
    if (cat.includes('SCHOOL')) return '🎓';
    return '📦';
}

function formatDisplayDate(dateStr) {
    if (!dateStr) return '';
    try {
        const parts = dateStr.split('-');
        const d = new Date(parts[0], parts[1] - 1, parts[2]);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

// --- QUICK RANGE FILTER PILLS ---
function setQuickRange(range) {
    currentQuickRange = range;
    document.querySelectorAll('.range-pill').forEach(btn => {
        btn.className = 'range-pill px-2.5 py-1 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white';
    });
    const activeBtn = document.getElementById(`range-pill-${range.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.className = 'range-pill px-2.5 py-1 rounded-lg font-bold bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-xs';
    }
    applyFilters();
}

// Filter and Search
function filterExpenses() {
    applyFilters();
}

function applyFilters() {
    const search = document.getElementById('searchInput').value.toLowerCase().trim();
    const cat = document.getElementById('categoryFilter').value;
    const explicitDate = document.getElementById('dateFilter').value;

    const todayStr = new Date().toISOString().split('T')[0];
    const now = new Date();
    const currentMonthPrefix = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    
    // Start of current week (Monday)
    const dayOfWeek = now.getDay() || 7;
    const monday = new Date(now);
    monday.setDate(now.getDate() - dayOfWeek + 1);
    monday.setHours(0, 0, 0, 0);

    filteredExpenses = allExpenses.filter(item => {
        const matchesSearch = !search || 
            item.good_or_service.toLowerCase().includes(search) || 
            item.expense_type.toLowerCase().includes(search);
        
        const matchesCat = cat === 'ALL' || item.expense_type.toUpperCase() === cat.toUpperCase();
        
        let matchesRange = true;
        if (explicitDate) {
            matchesRange = item.date === explicitDate;
        } else if (currentQuickRange === 'TODAY') {
            matchesRange = item.date === todayStr;
        } else if (currentQuickRange === 'WEEK') {
            const itemDate = new Date(item.date);
            matchesRange = itemDate >= monday;
        } else if (currentQuickRange === 'MONTH') {
            matchesRange = item.date && item.date.startsWith(currentMonthPrefix);
        }

        return matchesSearch && matchesCat && matchesRange;
    });

    renderExpenseTable(filteredExpenses);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = 'ALL';
    document.getElementById('dateFilter').value = '';
    setQuickRange('ALL');
}

// --- TAB SWITCHING ---
function switchTab(tabId) {
    const tabExpenses = document.getElementById('tab-content-expenses');
    const tabAnalytics = document.getElementById('tab-content-analytics');
    const tabAI = document.getElementById('tab-content-ai');

    const btnExpenses = document.getElementById('tab-btn-expenses');
    const btnAnalytics = document.getElementById('tab-btn-analytics');
    const btnAI = document.getElementById('tab-btn-ai');

    // Reset all tabs
    tabExpenses.classList.add('hidden');
    tabAnalytics.classList.add('hidden');
    if (tabAI) tabAI.classList.add('hidden');

    btnExpenses.className = 'tab-btn px-4 py-2 text-sm font-semibold rounded-xl bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 flex items-center space-x-2';
    btnAnalytics.className = 'tab-btn px-4 py-2 text-sm font-semibold rounded-xl bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 flex items-center space-x-2';
    if (btnAI) btnAI.className = 'tab-btn px-4 py-2 text-sm font-semibold rounded-xl bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 flex items-center space-x-2';

    if (tabId === 'expenses') {
        tabExpenses.classList.remove('hidden');
        btnExpenses.className = 'tab-btn active px-4 py-2 text-sm font-semibold rounded-xl bg-blue-600 text-white shadow-sm flex items-center space-x-2';
    } else if (tabId === 'analytics') {
        tabAnalytics.classList.remove('hidden');
        btnAnalytics.className = 'tab-btn active px-4 py-2 text-sm font-semibold rounded-xl bg-blue-600 text-white shadow-sm flex items-center space-x-2';
        if (dailyChartInstance) dailyChartInstance.resize();
        if (categoryChartInstance) categoryChartInstance.resize();
    } else if (tabId === 'ai') {
        if (tabAI) tabAI.classList.remove('hidden');
        if (btnAI) btnAI.className = 'tab-btn active px-4 py-2 text-sm font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-300 dark:shadow-none flex items-center space-x-2';
        loadAIInsights();
    }
}


// --- QUICK ADD HANDLER ---
function quickAdd(category) {
    openAddModal();
    const radio = document.querySelector(`input[name="expense_type"][value="${category}"]`);
    if (radio) radio.checked = true;
    document.getElementById('goodOrService').focus();
}

// --- ADD/EDIT MODAL ---
function openAddModal() {
    document.getElementById('modalTitle').innerText = 'Add New Expense';
    document.getElementById('saveBtn').innerText = 'Save Expense';
    document.getElementById('editIndex').value = '-1';
    document.getElementById('expenseForm').reset();
    document.getElementById('dateInput').value = new Date().toISOString().split('T')[0];
    document.querySelector('input[name="expense_type"][value="FOOD"]').checked = true;
    document.getElementById('addModal').classList.remove('hidden');
    document.getElementById('goodOrService').focus();
}

function closeAddModal() {
    document.getElementById('addModal').classList.add('hidden');
}

function editExpense(id) {
    const item = allExpenses.find(x => x.id === id);
    if (!item) return;

    document.getElementById('modalTitle').innerText = 'Edit Expense';
    document.getElementById('saveBtn').innerText = 'Update Expense';
    document.getElementById('editIndex').value = item.id;
    document.getElementById('goodOrService').value = item.good_or_service;
    document.getElementById('priceInput').value = item.price;
    document.getElementById('dateInput').value = item.date;

    const radio = document.querySelector(`input[name="expense_type"][value="${item.expense_type}"]`);
    if (radio) {
        radio.checked = true;
    } else {
        const foodRadio = document.querySelector('input[name="expense_type"][value="FOOD"]');
        if (foodRadio) foodRadio.checked = true;
    }

    document.getElementById('addModal').classList.remove('hidden');
    document.getElementById('goodOrService').focus();
}

// Submit Add / Edit
async function submitExpense(event) {
    event.preventDefault();

    const id = parseInt(document.getElementById('editIndex').value);
    const good_or_service = document.getElementById('goodOrService').value.trim();
    const price = parseFloat(document.getElementById('priceInput').value);
    const date = document.getElementById('dateInput').value;
    const expense_type = document.querySelector('input[name="expense_type"]:checked').value;

    const endpoint = id >= 0 ? '/api/edit' : '/api/add';
    const payload = { id, good_or_service, price, date, expense_type };

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.success) {
            closeAddModal();
            showToast(id >= 0 ? 'Expense updated successfully!' : 'Expense added successfully!');
            await loadAllData();
        } else {
            alert(result.error || 'Failed to save expense');
        }
    } catch (err) {
        console.error('Error saving expense:', err);
        alert('Server error occurred while saving.');
    }
}

// Delete Expense
async function deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense?')) return;

    try {
        const res = await fetch('/api/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        const result = await res.json();
        if (result.success) {
            showToast('Expense deleted');
            await loadAllData();
        } else {
            alert(result.error || 'Failed to delete expense');
        }
    } catch (err) {
        console.error('Error deleting expense:', err);
    }
}

// CSV Import Modal
function openImportModal() {
    document.getElementById('importModal').classList.remove('hidden');
}

function closeImportModal() {
    document.getElementById('importModal').classList.add('hidden');
}

async function submitImport(event) {
    event.preventDefault();
    const fileInput = document.getElementById('csvFileInput');
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/api/import/csv', {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        if (result.success) {
            closeImportModal();
            showToast(result.message);
            await loadAllData();
        } else {
            alert(result.error || 'Import failed');
        }
    } catch (err) {
        console.error('Error importing CSV:', err);
        alert('Error uploading file');
    }
}

// Summary Tables Rendering
function renderDailySummary(dailyData) {
    const tbody = document.getElementById('dailySummaryBody');
    tbody.innerHTML = '';
    const entries = Object.entries(dailyData || {}).reverse();

    if (entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="2" class="p-4 text-center text-slate-400 text-xs">No daily records yet</td></tr>`;
        return;
    }

    entries.forEach(([dateStr, total]) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="py-2.5 px-4 font-medium text-slate-700 dark:text-slate-300">${formatDisplayDate(dateStr)}</td>
            <td class="py-2.5 px-4 text-right font-bold text-slate-900 dark:text-white">${formatMoney(total)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderWeeklySummary(weeklyData) {
    const tbody = document.getElementById('weeklySummaryBody');
    tbody.innerHTML = '';
    const entries = Object.entries(weeklyData || {}).reverse();

    if (entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="2" class="p-4 text-center text-slate-400 text-xs">No weekly records yet</td></tr>`;
        return;
    }

    entries.forEach(([weekLabel, total]) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="py-2.5 px-4 font-medium text-slate-700 dark:text-slate-300">${escapeHtml(weekLabel)}</td>
            <td class="py-2.5 px-4 text-right font-bold text-slate-900 dark:text-white">${formatMoney(total)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- CHART.JS VISUALIZATIONS WITH THEME ADAPTATION ---
function isDarkMode() {
    return document.documentElement.classList.contains('dark');
}

function renderDailyChart(dailyData) {
    const ctx = document.getElementById('dailyChart');
    if (!ctx) return;

    const dark = isDarkMode();
    const gridColor = dark ? '#1e293b' : '#f1f5f9';
    const textColor = dark ? '#94a3b8' : '#64748b';

    const labels = Object.keys(dailyData || {});
    const formattedLabels = labels.map(l => formatDisplayDate(l));
    const values = Object.values(dailyData || {});

    if (dailyChartInstance) {
        dailyChartInstance.destroy();
    }

    dailyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: formattedLabels,
            datasets: [{
                label: 'Expenses',
                data: values,
                backgroundColor: '#3b82f6',
                borderRadius: 6,
                maxBarThickness: 45
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${formatMoney(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(val) { return `${currentCurrency} ${val}`; },
                        font: { size: 10 },
                        color: textColor
                    },
                    grid: { color: gridColor }
                },
                x: {
                    ticks: { font: { size: 10 }, color: textColor },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderCategoryChart(categoryData) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    const dark = isDarkMode();
    const textColor = dark ? '#cbd5e1' : '#475569';
    const borderColor = dark ? '#0f172a' : '#ffffff';

    const labels = Object.keys(categoryData || {});
    const values = Object.values(categoryData || {});

    const palette = {
        'FOOD': '#10b981',
        'HOUSEHOLD': '#0284c7',
        'TRANSPORTATION': '#f59e0b',
        'SCHOOL FEE': '#8b5cf6'
    };
    const defaultColors = ['#ec4899', '#06b6d4', '#64748b', '#6366f1'];
    const bgColors = labels.map((l, i) => palette[l.toUpperCase()] || defaultColors[i % defaultColors.length]);

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: bgColors,
                borderWidth: 2,
                borderColor: borderColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, font: { size: 11 }, padding: 12, color: textColor }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = values.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${formatMoney(context.raw)} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// Toast helper
function showToast(msg) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMessage');
    toastMsg.innerText = msg;
    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
        toast.classList.remove('translate-y-0', 'opacity-100');
    }, 2800);
}

// HTML escape
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ====================================================
// FINWISE AI WEALTH BOT & ADVISORY LOGIC
// ====================================================

let currentRiskProfile = 'BALANCED';
let currentAIData = null;

async function loadAIInsights() {
    try {
        const res = await fetch(`/api/ai/insights?budget=${monthlyBudget}&risk=${currentRiskProfile}`);
        const data = await res.json();
        if (data.success) {
            currentAIData = data;
            
            // Update Header Surplus Indicator
            const surplusHeader = document.getElementById('aiSurplusHeader');
            if (surplusHeader) surplusHeader.innerText = formatMoney(data.surplus);

            // Render sub-components
            renderAIInsights(data.smart_insights);
            renderMoMComparison(data.monthly_comparison);
            renderPeerBenchmarking(data.peer_benchmarking);
            renderInvestmentAdvisor(data.investment_plan);
        }
    } catch (err) {
        console.error('Error loading AI insights:', err);
    }
}

// 1. Dynamic AI Insights Cards
function renderAIInsights(insights) {
    const container = document.getElementById('aiInsightsContainer');
    if (!container) return;
    container.innerHTML = '';

    if (!insights || insights.length === 0) {
        container.innerHTML = `<div class="col-span-3 text-center text-xs text-slate-400 py-3">Log more expenses to generate deeper AI heuristics.</div>`;
        return;
    }

    const colorMap = {
        'praise': { bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-200 dark:border-emerald-800', text: 'text-emerald-900 dark:text-emerald-200', icon: 'sparkles', iconColor: 'text-emerald-600 dark:text-emerald-400' },
        'warning': { bg: 'bg-rose-50 dark:bg-rose-950/40', border: 'border-rose-200 dark:border-rose-800', text: 'text-rose-900 dark:text-rose-200', icon: 'alert-triangle', iconColor: 'text-rose-600 dark:text-rose-400' },
        'investment': { bg: 'bg-indigo-50 dark:bg-indigo-950/40', border: 'border-indigo-200 dark:border-indigo-800', text: 'text-indigo-900 dark:text-indigo-200', icon: 'trending-up', iconColor: 'text-indigo-600 dark:text-indigo-400' },
        'optimization': { bg: 'bg-amber-50 dark:bg-amber-950/40', border: 'border-amber-200 dark:border-amber-800', text: 'text-amber-900 dark:text-amber-200', icon: 'lightbulb', iconColor: 'text-amber-600 dark:text-amber-400' },
        'info': { bg: 'bg-blue-50 dark:bg-blue-950/40', border: 'border-blue-200 dark:border-blue-800', text: 'text-blue-900 dark:text-blue-200', icon: 'gauge', iconColor: 'text-blue-600 dark:text-blue-400' }
    };

    insights.forEach(item => {
        const style = colorMap[item.type] || colorMap['info'];
        const card = document.createElement('div');
        card.className = `${style.bg} ${style.border} border rounded-2xl p-4 flex items-start space-x-3 shadow-xs transition`;
        card.innerHTML = `
            <span class="p-2 rounded-xl bg-white/70 dark:bg-slate-900/60 ${style.iconColor} shrink-0 mt-0.5">
                <i data-lucide="${style.icon}" class="w-4 h-4"></i>
            </span>
            <div>
                <h5 class="font-bold text-xs ${style.text}">${escapeHtml(item.title)}</h5>
                <p class="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5 leading-snug">${escapeHtml(item.text)}</p>
            </div>
        `;
        container.appendChild(card);
    });

    lucide.createIcons();
}

// 2. Month-over-Month Velocity Comparison
function renderMoMComparison(comparison) {
    if (!comparison || !comparison.has_data) return;

    document.getElementById('momPrevLabel').innerText = comparison.previous_month_name || 'Previous Month';
    document.getElementById('momCurLabel').innerText = comparison.current_month_name || 'Current Month';
    document.getElementById('momPrevVal').innerText = formatMoney(comparison.previous_total);
    document.getElementById('momCurVal').innerText = formatMoney(comparison.current_total);

    const deltaBadge = document.getElementById('momDeltaBadge');
    const diff = comparison.pct_change || 0;

    if (diff > 0) {
        deltaBadge.className = 'text-xs font-bold px-2.5 py-1 rounded-full bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 flex items-center space-x-1';
        deltaBadge.innerHTML = `<span>▲ +${diff}% vs last month</span>`;
    } else if (diff < 0) {
        deltaBadge.className = 'text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 flex items-center space-x-1';
        deltaBadge.innerHTML = `<span>▼ ${diff}% vs last month</span>`;
    } else {
        deltaBadge.className = 'text-xs font-bold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700';
        deltaBadge.innerText = '0% (Equal spend)';
    }

    // Category Level Shift
    const catList = document.getElementById('momCategoryList');
    catList.innerHTML = '';
    const cats = Object.entries(comparison.categories || {});
    
    if (cats.length === 0) {
        catList.innerHTML = `<div class="text-slate-400 text-xs">No category delta available.</div>`;
        return;
    }

    cats.forEach(([catName, catData]) => {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-2 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/80';
        
        let shiftColor = 'text-slate-500';
        let shiftSymbol = '';
        if (catData.diff_pct > 0) {
            shiftColor = 'text-rose-600 dark:text-rose-400 font-bold';
            shiftSymbol = `+${catData.diff_pct}% ▲`;
        } else if (catData.diff_pct < 0) {
            shiftColor = 'text-emerald-600 dark:text-emerald-400 font-bold';
            shiftSymbol = `${catData.diff_pct}% ▼`;
        } else {
            shiftSymbol = '0%';
        }

        item.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>${getCategoryIcon(catName)}</span>
                <span class="font-medium text-slate-700 dark:text-slate-300">${escapeHtml(catName)}</span>
            </div>
            <div class="flex items-center space-x-3 text-right">
                <span class="text-slate-500 dark:text-slate-400 font-mono">${formatMoney(catData.current)}</span>
                <span class="${shiftColor} text-[11px] font-mono min-w-[60px]">${shiftSymbol}</span>
            </div>
        `;
        catList.appendChild(item);
    });
}

// 3. Peer Community Benchmarking
function renderPeerBenchmarking(benchmarks) {
    const container = document.getElementById('peerBenchmarkList');
    if (!container) return;
    container.innerHTML = '';

    if (!benchmarks || benchmarks.length === 0) {
        container.innerHTML = `<div class="text-slate-400 text-xs py-4">Add your expenses to generate peer percentile comparisons.</div>`;
        return;
    }

    benchmarks.forEach(item => {
        const row = document.createElement('div');
        row.className = 'space-y-1.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800';

        let badgeBg = 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
        if (item.color === 'emerald') {
            badgeBg = 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
        } else if (item.color === 'amber') {
            badgeBg = 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800';
        }

        row.innerHTML = `
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                    <span class="font-bold text-slate-800 dark:text-slate-200">${getCategoryIcon(item.category)} ${escapeHtml(item.category)}</span>
                </div>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeBg}">${escapeHtml(item.badge)}</span>
            </div>

            <!-- Double Bar Comparison: User vs Peer -->
            <div class="space-y-1 pt-1">
                <div class="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400">
                    <span>You: <strong class="text-blue-600 dark:text-blue-400">${item.user_pct}%</strong></span>
                    <span>Peer Avg: <strong class="text-slate-600 dark:text-slate-300">${item.peer_pct}%</strong></span>
                </div>
                <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 relative overflow-hidden">
                    <div class="bg-blue-500 h-2 rounded-full absolute left-0" style="width: ${Math.min(100, item.user_pct)}%"></div>
                    <!-- Marker for peer avg -->
                    <div class="absolute top-0 bottom-0 w-1 bg-slate-800 dark:bg-white z-10" style="left: ${Math.min(99, item.peer_pct)}%" title="Peer Average ${item.peer_pct}%"></div>
                </div>
            </div>
        `;
        container.appendChild(row);
    });
}

// 4. Surplus Investment Advisor
function renderInvestmentAdvisor(plan) {
    if (!plan) return;

    document.getElementById('aiStrategyTitle').innerText = plan.strategy_name;
    document.getElementById('aiStrategyRationale').innerText = plan.ai_rationale;
    document.getElementById('ai10YrProjectionVal').innerText = formatMoney(plan.projected_10yr_wealth);

    const grid = document.getElementById('investmentCardsGrid');
    grid.innerHTML = '';

    const assetThemes = {
        'GOLD': { bg: 'bg-amber-50/60 dark:bg-amber-950/20', border: 'border-amber-200 dark:border-amber-800', iconBg: 'bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300' },
        'INFRA': { bg: 'bg-sky-50/60 dark:bg-sky-950/20', border: 'border-sky-200 dark:border-sky-800', iconBg: 'bg-sky-100 text-sky-700 dark:bg-sky-900/60 dark:text-sky-300' },
        'STOCKS': { bg: 'bg-emerald-50/60 dark:bg-emerald-950/20', border: 'border-emerald-200 dark:border-emerald-800', iconBg: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300' },
        'EMERGENCY': { bg: 'bg-purple-50/60 dark:bg-purple-950/20', border: 'border-purple-200 dark:border-purple-800', iconBg: 'bg-purple-100 text-purple-700 dark:bg-purple-900/60 dark:text-purple-300' }
    };

    plan.allocations.forEach(alloc => {
        const theme = assetThemes[alloc.asset_class] || assetThemes['GOLD'];
        const card = document.createElement('div');
        card.className = `${theme.bg} ${theme.border} border rounded-2xl p-4 space-y-3 shadow-xs flex flex-col justify-between`;

        card.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="p-2 rounded-xl ${theme.iconBg} font-bold">
                    <i data-lucide="${alloc.icon}" class="w-4 h-4"></i>
                </span>
                <span class="text-xs font-black px-2 py-0.5 rounded-full bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-slate-700">
                    ${alloc.percentage}%
                </span>
            </div>

            <div>
                <h5 class="font-bold text-xs text-slate-900 dark:text-slate-100 leading-snug">${escapeHtml(alloc.name)}</h5>
                <div class="text-base font-black text-slate-900 dark:text-white mt-1">
                    ${formatMoney(alloc.amount)}
                </div>
            </div>

            <div class="pt-2 border-t border-slate-200/60 dark:border-slate-800/80 flex items-center justify-between text-[11px]">
                <span class="text-slate-400">CAGR: <strong class="text-emerald-600 dark:text-emerald-400">${alloc.expected_cagr}</strong></span>
                <span class="text-slate-400">Risk: <strong class="text-slate-600 dark:text-slate-300">${alloc.risk_level}</strong></span>
            </div>
        `;
        grid.appendChild(card);
    });

    lucide.createIcons();
}

// Risk Profile Change
function changeRiskProfile(profile) {
    currentRiskProfile = profile;
    document.querySelectorAll('.risk-pill').forEach(btn => {
        btn.className = 'risk-pill px-3 py-1 text-xs rounded-lg text-slate-500 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition';
    });
    const activeBtn = document.getElementById(`risk-btn-${profile.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.className = 'risk-pill px-3 py-1 text-xs rounded-lg font-bold bg-white dark:bg-slate-700 text-blue-600 dark:text-white shadow-xs transition';
    }
    loadAIInsights();
    showToast(`Switched to ${profile.toLowerCase()} risk allocation`);
}

// 5. Ask from AI Bot Interactive Assistant
function askAIQuick(query) {
    document.getElementById('aiChatInput').value = query;
    submitAIChat();
}

async function submitAIChat(event) {
    if (event) event.preventDefault();
    const input = document.getElementById('aiChatInput');
    const query = input.value.trim();
    if (!query) return;

    const responseBox = document.getElementById('aiResponseBox');
    const responseContent = document.getElementById('aiResponseContent');
    const sendBtn = document.getElementById('aiSendBtn');

    responseBox.classList.remove('hidden');
    responseContent.innerHTML = `<div class="flex items-center space-x-2 text-indigo-500"><i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Analyzing your finances and market yields...</span></div>`;
    lucide.createIcons();

    if (sendBtn) sendBtn.disabled = true;

    try {
        const res = await fetch('/api/ai/advisor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, budget: monthlyBudget, risk: currentRiskProfile })
        });
        const data = await res.json();
        
        if (data.success) {
            // Format bold text and bullet points nicely
            let formatted = data.response
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/• (.*)/g, '<li class="ml-3 my-0.5">$1</li>');

            responseContent.innerHTML = formatted;
        } else {
            responseContent.innerText = "Error consulting AI advisor. Please try again.";
        }
    } catch (err) {
        console.error('AI chat error:', err);
        responseContent.innerText = "Connection error while reaching the AI engine.";
    } finally {
        if (sendBtn) sendBtn.disabled = false;
        lucide.createIcons();
    }
}

