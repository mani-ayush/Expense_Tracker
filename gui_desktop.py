import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import backend

class ExpenseTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker Pro - Desktop Edition")
        self.root.geometry("1120x740")
        self.root.minsize(980, 620)

        # Initialize backend
        backend.init_tracker()

        # State
        self.editing_id = None
        self.is_dark_mode = False
        self.current_currency = "Rs"

        # Build UI layout & styles
        self.setup_styles()
        self.build_ui()

        # Load initial data
        self.refresh_all()

    def setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self.apply_theme_colors()

    def apply_theme_colors(self):
        if self.is_dark_mode:
            bg = '#0f172a'
            card_bg = '#1e293b'
            fg = '#f8fafc'
            muted_fg = '#94a3b8'
            tree_bg = '#1e293b'
            tree_head = '#334155'
            sel_bg = '#3b82f6'
        else:
            bg = '#f8fafc'
            card_bg = '#ffffff'
            fg = '#0f172a'
            muted_fg = '#64748b'
            tree_bg = '#ffffff'
            tree_head = '#f1f5f9'
            sel_bg = '#e0e7ff'

        self.root.configure(background=bg)
        self.style.configure('.', font=('Segoe UI', 9), background=bg, foreground=fg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('Card.TFrame', background=card_bg, relief='flat')
        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('Header.TLabel', font=('Segoe UI', 15, 'bold'), foreground=fg, background=bg)
        self.style.configure('Subheader.TLabel', font=('Segoe UI', 9), foreground=muted_fg, background=bg)

        # KPI labels
        self.style.configure('KpiTitle.TLabel', font=('Segoe UI', 8, 'bold'), foreground=muted_fg, background=card_bg)
        self.style.configure('KpiVal.TLabel', font=('Segoe UI', 14, 'bold'), foreground=fg, background=card_bg)

        # Buttons
        self.style.configure('Primary.TButton', font=('Segoe UI', 9, 'bold'), background='#2563eb', foreground='#ffffff')
        self.style.map('Primary.TButton', background=[('active', '#1d4ed8')])

        # Treeview
        self.style.configure('Treeview', font=('Segoe UI', 9), rowheight=28, background=tree_bg, foreground=fg, fieldbackground=tree_bg)
        self.style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'), background=tree_head, foreground=fg)
        self.style.map('Treeview', background=[('selected', sel_bg)], foreground=[('selected', '#ffffff' if self.is_dark_mode else '#1e1b4b')])

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.theme_btn.config(text="☀️ Light Mode" if self.is_dark_mode else "🌙 Dark Mode")
        self.apply_theme_colors()
        self.refresh_all()

    def build_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding=16)
        self.main_frame.pack(fill='both', expand=True)

        # 1. Top Header & Actions
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', pady=(0, 14))

        title_box = ttk.Frame(header_frame)
        title_box.pack(side='left')
        ttk.Label(title_box, text="Expense Tracker Pro", style='Header.TLabel').pack(anchor='w')
        ttk.Label(title_box, text="Daily & Weekly Expense Analytics (v2.0)", style='Subheader.TLabel').pack(anchor='w')

        # Top Action buttons
        btn_box = ttk.Frame(header_frame)
        btn_box.pack(side='right')

        self.theme_btn = ttk.Button(btn_box, text="🌙 Dark Mode", command=self.toggle_theme)
        self.theme_btn.pack(side='left', padx=4)

        ttk.Button(btn_box, text="Import CSV", command=self.import_csv).pack(side='left', padx=4)
        ttk.Button(btn_box, text="Export CSV", command=self.export_csv).pack(side='left', padx=4)

        # 2. KPI Cards Frame
        kpi_frame = ttk.Frame(self.main_frame)
        kpi_frame.pack(fill='x', pady=(0, 14))

        self.card_total = self.create_kpi_card(kpi_frame, "TOTAL EXPENSE", "Rs 0.00")
        self.card_today = self.create_kpi_card(kpi_frame, "TODAY'S EXPENSE", "Rs 0.00")
        self.card_week = self.create_kpi_card(kpi_frame, "THIS WEEK", "Rs 0.00")
        self.card_count = self.create_kpi_card(kpi_frame, "TRANSACTIONS", "0")

        # 3. Middle Content (Left: Form, Right: Tabs with Table & Charts)
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill='both', expand=True)

        # Left Form Frame
        form_card = ttk.LabelFrame(content_frame, text=" Add / Edit Expense ", padding=14)
        form_card.pack(side='left', fill='y', padx=(0, 12))

        ttk.Label(form_card, text="Category:", font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(4, 2))
        self.category_var = tk.StringVar(value='FOOD')
        self.category_cb = ttk.Combobox(form_card, textvariable=self.category_var, 
                                        values=['FOOD', 'HOUSEHOLD', 'TRANSPORTATION', 'SCHOOL FEE'],
                                        state='readonly', width=22)
        self.category_cb.pack(fill='x', pady=(0, 8))

        ttk.Label(form_card, text="Item / Service:", font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(4, 2))
        self.item_entry = ttk.Entry(form_card, width=24)
        self.item_entry.pack(fill='x', pady=(0, 8))

        ttk.Label(form_card, text="Price (Rs):", font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(4, 2))
        self.price_entry = ttk.Entry(form_card, width=24)
        self.price_entry.pack(fill='x', pady=(0, 8))

        ttk.Label(form_card, text="Date (YYYY-MM-DD):", font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(4, 2))
        self.date_entry = ttk.Entry(form_card, width=24)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_entry.pack(fill='x', pady=(0, 14))

        # Buttons
        self.save_btn = ttk.Button(form_card, text="Add Expense", style='Primary.TButton', command=self.save_expense)
        self.save_btn.pack(fill='x', pady=(0, 6))

        self.cancel_btn = ttk.Button(form_card, text="Clear / Cancel", command=self.reset_form)
        self.cancel_btn.pack(fill='x')

        # Right Notebook Tabs (Expenses Table vs Charts)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(side='right', fill='both', expand=True)

        # Tab 1: Table
        table_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(table_tab, text=" All Expenses ")

        # Search Bar
        search_frame = ttk.Frame(table_tab)
        search_frame.pack(fill='x', pady=(0, 8))
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_table())
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side='left')

        # Table & Scrollbar
        tree_frame = ttk.Frame(table_tab)
        tree_frame.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=('ID', 'Date', 'Item', 'Category', 'Price'), show='headings')
        self.tree.heading('ID', text='#')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Item', text='Good / Service')
        self.tree.heading('Category', text='Category')
        self.tree.heading('Price', text='Price')

        self.tree.column('ID', width=40, anchor='center')
        self.tree.column('Date', width=100, anchor='center')
        self.tree.column('Item', width=220, anchor='w')
        self.tree.column('Category', width=130, anchor='center')
        self.tree.column('Price', width=100, anchor='e')

        tree_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')

        # Table buttons
        tbl_btn_frame = ttk.Frame(table_tab)
        tbl_btn_frame.pack(fill='x', pady=(8, 0))
        ttk.Button(tbl_btn_frame, text="Edit Selected", command=self.edit_selected).pack(side='left', padx=(0, 6))
        ttk.Button(tbl_btn_frame, text="Delete Selected", command=self.delete_selected).pack(side='left')

        # Tab 2: Reports & Charts
        chart_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(chart_tab, text=" Visual Charts & Reports ")

        chart_ctrl_frame = ttk.Frame(chart_tab)
        chart_ctrl_frame.pack(fill='x', pady=(0, 8))
        ttk.Button(chart_ctrl_frame, text="Daily Bar Chart", command=lambda: self.render_chart('DAILY')).pack(side='left', padx=4)
        ttk.Button(chart_ctrl_frame, text="Weekly / Category Pie Chart", command=lambda: self.render_chart('WEEKLY')).pack(side='left', padx=4)
        ttk.Button(chart_ctrl_frame, text="Save Chart as JPEG", command=self.save_jpeg).pack(side='right', padx=4)

        # Matplotlib Canvas Frame
        self.chart_canvas_frame = ttk.Frame(chart_tab)
        self.chart_canvas_frame.pack(fill='both', expand=True)
        self.current_chart_type = 'DAILY'
        self.fig, self.ax = plt.subplots(figsize=(7, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_canvas_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_kpi_card(self, parent, title, initial_val):
        card = ttk.Frame(parent, style='Card.TFrame', padding=12)
        card.pack(side='left', fill='x', expand=True, padx=4)
        ttk.Label(card, text=title, style='KpiTitle.TLabel').pack(anchor='w')
        val_lbl = ttk.Label(card, text=initial_val, style='KpiVal.TLabel')
        val_lbl.pack(anchor='w', pady=(4, 0))
        return val_lbl

    def refresh_all(self):
        self.populate_table()
        self.update_kpis()
        self.render_chart(self.current_chart_type)

    def populate_table(self):
        self.tree.delete(*self.tree.get_children())
        df = backend.get_expense_dataframe()
        if df.empty:
            return

        for idx, row in df.iterrows():
            dt_str = row['DATES'].strftime('%Y-%m-%d') if hasattr(row['DATES'], 'strftime') else str(row['DATES'])[:10]
            self.tree.insert('', 'end', values=(
                idx,
                dt_str,
                row['GOODS_OR_SERVICES'],
                row['EXPENSE_TYPE'],
                f"Rs {float(row['PRICES']):.2f}"
            ))

    def filter_table(self):
        query = self.search_var.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        df = backend.get_expense_dataframe()
        if df.empty:
            return

        for idx, row in df.iterrows():
            dt_str = row['DATES'].strftime('%Y-%m-%d') if hasattr(row['DATES'], 'strftime') else str(row['DATES'])[:10]
            item_str = str(row['GOODS_OR_SERVICES']).lower()
            cat_str = str(row['EXPENSE_TYPE']).lower()

            if not query or query in item_str or query in cat_str or query in dt_str:
                self.tree.insert('', 'end', values=(
                    idx,
                    dt_str,
                    row['GOODS_OR_SERVICES'],
                    row['EXPENSE_TYPE'],
                    f"Rs {float(row['PRICES']):.2f}"
                ))

    def update_kpis(self):
        df = backend.get_expense_dataframe()
        total = backend.calculate_total_expense()
        self.card_total.config(text=f"Rs {total:,.2f}")
        self.card_count.config(text=str(len(backend.GOODS_OR_SERVICES)))

        today_str = datetime.now().strftime('%Y-%m-%d')
        if not df.empty:
            df_today = df[df['DATES'].dt.strftime('%Y-%m-%d') == today_str]
            today_tot = df_today['PRICES'].sum()
            self.card_today.config(text=f"Rs {today_tot:,.2f}")

            weekly = backend.calculate_weekly_expense(df)
            week_tot = weekly.iloc[-1] if not weekly.empty else 0.0
            self.card_week.config(text=f"Rs {week_tot:,.2f}")
        else:
            self.card_today.config(text="Rs 0.00")
            self.card_week.config(text="Rs 0.00")

    def save_expense(self):
        cat = self.category_var.get().strip().upper()
        item = self.item_entry.get().strip()
        price_str = self.price_entry.get().strip()
        date_str = self.date_entry.get().strip()

        if not item:
            messagebox.showwarning("Validation Error", "Please enter item or service name.")
            return

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Validation Error", "Please enter a valid price greater than 0.")
            return

        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showwarning("Validation Error", "Date format must be YYYY-MM-DD.")
            return

        if self.editing_id is not None:
            backend.edit_expense(self.editing_id, item, price, dt, cat)
            messagebox.showinfo("Updated", "Expense updated successfully.")
        else:
            backend.add_expense(item, price, dt, cat)
            messagebox.showinfo("Added", "Expense added successfully.")

        self.reset_form()
        self.refresh_all()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select an expense from the table to edit.")
            return

        values = self.tree.item(selected[0])['values']
        idx = int(values[0])
        self.editing_id = idx

        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, values[1])

        self.item_entry.delete(0, tk.END)
        self.item_entry.insert(0, values[2])

        self.category_var.set(values[3])

        self.price_entry.delete(0, tk.END)
        price_num = str(values[4]).replace('Rs', '').replace(',', '').strip()
        self.price_entry.insert(0, price_num)

        self.save_btn.config(text="Update Expense")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select an expense to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this expense?"):
            values = self.tree.item(selected[0])['values']
            idx = int(values[0])
            backend.delete_expense(idx)
            self.reset_form()
            self.refresh_all()

    def reset_form(self):
        self.editing_id = None
        self.item_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.category_var.set('FOOD')
        self.save_btn.config(text="Add Expense")

    def render_chart(self, chart_type):
        self.current_chart_type = chart_type
        self.ax.clear()

        # Adapt colors to Dark/Light mode
        bg_color = '#1e293b' if self.is_dark_mode else '#ffffff'
        text_color = '#f8fafc' if self.is_dark_mode else '#1e293b'
        grid_color = '#334155' if self.is_dark_mode else '#e2e8f0'

        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        df = backend.get_expense_dataframe()
        if df.empty:
            self.ax.text(0.5, 0.5, "No Expense Data Available", ha='center', va='center', fontsize=12, color='#94a3b8')
            self.canvas.draw()
            return

        if chart_type == 'WEEKLY':
            cat_totals = backend.calculate_category_expense(df)
            labels = list(cat_totals.index)
            sizes = list(cat_totals.values)
            colors = ['#10b981', '#0284c7', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
            wedges, texts, autotexts = self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140,
                        colors=colors[:len(sizes)], wedgeprops=dict(width=0.6, edgecolor=bg_color))
            for t in texts:
                t.set_color(text_color)
            for at in autotexts:
                at.set_color('#ffffff')
            self.ax.set_title("Category / Weekly Breakdown", fontsize=12, fontweight='bold', pad=12, color=text_color)
        else:
            daily = backend.calculate_daily_expense(df)
            daily = daily[daily > 0]
            dates = [d.strftime('%b %d') for d in daily.index]
            prices = daily.values

            bars = self.ax.bar(dates, prices, color='#3b82f6', width=0.55, edgecolor='#1d4ed8')
            self.ax.set_title("Daily Expenses", fontsize=12, fontweight='bold', pad=12, color=text_color)
            self.ax.set_ylabel("Price (Rs)", fontsize=9, fontweight='bold', color=text_color)
            self.ax.tick_params(axis='x', rotation=30, colors=text_color)
            self.ax.tick_params(axis='y', colors=text_color)
            self.ax.grid(axis='y', linestyle='--', alpha=0.5, color=grid_color)

            for spine in self.ax.spines.values():
                spine.set_color(grid_color)

            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    self.ax.annotate(f"{h:.0f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                                    xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=8, color=text_color)

        self.fig.tight_layout()
        self.canvas.draw()

    def save_jpeg(self):
        df = backend.get_expense_dataframe()
        if df.empty:
            messagebox.showwarning("Warning", "No expenses to generate chart.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".jpeg",
            filetypes=[("JPEG Image", "*.jpeg"), ("JPG Image", "*.jpg")],
            initialfile=f"{self.current_chart_type.lower()}_report_{datetime.now().strftime('%Y-%m-%d')}.jpeg"
        )
        if filename:
            title = f"{datetime.now().strftime('%Y-%m-%d')}_{self.current_chart_type}"
            backend.save_data_to_jpeg(df, title, filename)
            messagebox.showinfo("Saved", f"Chart successfully saved to:\n{filename}")

    def export_csv(self):
        df = backend.get_expense_dataframe()
        if df.empty:
            messagebox.showwarning("Warning", "No expenses to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"expenses_{datetime.now().strftime('%Y-%m-%d')}.csv"
        )
        if filename:
            df_to_save = df.copy()
            df_to_save['DATES'] = df_to_save['DATES'].dt.strftime('%Y-%m-%d')
            backend.save_data_to_csv(df_to_save, filename)
            messagebox.showinfo("Exported", f"Data exported successfully to:\n{filename}")

    def import_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filename:
            data = backend.load_data_from_csv(filename)
            if data is not None:
                backend.auto_save()
                self.refresh_all()
                messagebox.showinfo("Success", f"Successfully imported {len(data)} expenses!")
            else:
                messagebox.showerror("Error", "Invalid CSV format. Must contain columns: GOODS_OR_SERVICES, PRICES, DATES, EXPENSE_TYPE")

if __name__ == '__main__':
    root = tk.Tk()
    app = ExpenseTrackerGUI(root)
    root.mainloop()
