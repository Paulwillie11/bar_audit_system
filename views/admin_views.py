import tkinter as tk
from tkinter import ttk, messagebox
import traceback  # For detailed error printing
from views.base_ui import BaseUI
from database import db_session
from models import User, SalaryDeduction, AuditLog
from helpers import log_action


class AdminViews(BaseUI):
    def __init__(self, master, app_instance):
        super().__init__(master, app_instance)

    def show_admin_users(self):
        """Displays the admin panel for managing users."""
        self.clear_frame()
        admin_users_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        admin_users_frame.pack(expand=True, fill="both")
        admin_users_frame.grid_columnconfigure(0, weight=1)
        admin_users_frame.grid_rowconfigure(3, weight=1)

        ttk.Label(admin_users_frame, text="Admin: Manage Users", style="Header.TLabel").grid(row=0, column=0, pady=15)

        add_user_frame = ttk.LabelFrame(admin_users_frame, text="Add New User", padding="15")
        add_user_frame.grid(row=1, column=0, pady=10, sticky="ew", padx=10)
        add_user_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(add_user_frame, text="Username:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.new_username_entry = ttk.Entry(add_user_frame, style="TEntry")
        self.new_username_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(add_user_frame, text="Password:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.new_password_entry = ttk.Entry(add_user_frame, show="*", style="TEntry")
        self.new_password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(add_user_frame, text="Role:", style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.new_role_combobox = ttk.Combobox(add_user_frame, values=["Staff", "Manager", "Admin"], style="TCombobox")
        self.new_role_combobox.set("Staff")
        self.new_role_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(add_user_frame, text="Monthly Salary (₦):", style="TLabel").grid(row=3, column=0, sticky="w", padx=5,
                                                                                   pady=3)
        self.new_monthly_salary_entry = ttk.Entry(add_user_frame, style="TEntry")
        self.new_monthly_salary_entry.insert(0, "0.00")
        self.new_monthly_salary_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Button(add_user_frame, text="Add User", command=self.add_user_action, style="TButton").grid(row=4, column=0,
                                                                                                        columnspan=2,
                                                                                                        pady=15,
                                                                                                        ipadx=10,
                                                                                                        ipady=5)

        ttk.Label(admin_users_frame, text="Existing Users", style="SectionHeader.TLabel").grid(row=2, column=0, pady=10)

        columns = ('ID', 'Username', 'Role', 'Monthly Salary', 'Current Balance', 'Active')
        self.users_tree = ttk.Treeview(admin_users_frame, columns=columns, show='headings')
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, anchor='center')
        self.users_tree.column('ID', width=50, stretch=False)
        self.users_tree.column('Username', width=150, stretch=True)
        self.users_tree.column('Role', width=80, stretch=False)
        self.users_tree.column('Monthly Salary', width=120, stretch=False)
        self.users_tree.column('Current Balance', width=120, stretch=False)
        self.users_tree.column('Active', width=70, stretch=False)

        tree_scroll = ttk.Scrollbar(admin_users_frame, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.grid(row=3, column=1, sticky="ns", padx=(0, 10))
        self.users_tree.grid(row=3, column=0, sticky="nsew", padx=(10, 0), pady=5)

        self.users_tree.bind('<<TreeviewSelect>>', self.on_user_selection_change)

        buttons_frame = ttk.Frame(admin_users_frame, style="TFrame")
        buttons_frame.grid(row=4, column=0, pady=15)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        self.delete_user_button = ttk.Button(buttons_frame, text="Delete Selected User",
                                             command=self.delete_selected_user, style="Danger.TButton",
                                             state='disabled')
        self.delete_user_button.grid(row=0, column=0, padx=10, ipadx=5, ipady=3)

        ttk.Button(admin_users_frame, text="Back to Dashboard", command=self.app.show_dashboard, style="TButton").grid(
            row=5, column=0, pady=20, ipadx=10, ipady=5)

        self.load_users()

    def on_user_selection_change(self, event):
        selected_item = self.users_tree.focus()
        if selected_item:
            self.delete_user_button.config(state='!disabled')
        else:
            self.delete_user_button.config(state='disabled')

    def load_users(self):
        for i in self.users_tree.get_children():
            self.users_tree.delete(i)
        users = db_session.query(User).all()
        for user in users:
            active_status = "Yes" if user.is_active else "No"
            self.users_tree.insert('', 'end', values=(
                user.id, user.username, user.role, f"₦{user.monthly_salary:.2f}",
                f"₦{user.current_salary_balance:.2f}", active_status
            ), iid=user.id)
        self.on_user_selection_change(None)

    def add_user_action(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        role = self.new_role_combobox.get()
        try:
            monthly_salary = float(self.new_monthly_salary_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Monthly Salary must be a number.")
            return

        if not username or not password:
            messagebox.showerror("Input Error", "Username and Password cannot be empty.")
            return

        if db_session.query(User).filter_by(username=username).first():
            messagebox.showerror("Error", "Username already exists.")
            return

        new_user = User(username=username, role=role, monthly_salary=monthly_salary,
                        current_salary_balance=monthly_salary)
        new_user.set_password(password)
        db_session.add(new_user)
        db_session.commit()
        messagebox.showinfo("Success", f"User {username} ({role}) created successfully!")
        log_action(self.app.current_user.username, self.app.current_user.role, 'Add User',
                   new_value=f"Username:{username}, Role:{role}, Monthly Salary:{monthly_salary}")
        self.new_username_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)
        self.new_monthly_salary_entry.delete(0, tk.END)
        self.new_monthly_salary_entry.insert(0, "0.00")
        self.load_users()

    def delete_selected_user(self):
        selected_item = self.users_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to delete.")
            return

        user_id = int(self.users_tree.item(selected_item, 'iid'))
        user_to_delete = db_session.query(User).get(user_id)

        if not user_to_delete:
            messagebox.showerror("Error", "Selected user not found in database. The list will now be refreshed.")
            self.load_users()
            return

        if user_to_delete.id == self.app.current_user.id:
            messagebox.showerror("Error", "You cannot delete your own active account.")
            return

        if user_to_delete.role == 'Admin' and db_session.query(User).filter_by(role='Admin').count() == 1:
            messagebox.showerror("Deletion Error", "Cannot delete the last Admin user in the system.")
            return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to permanently delete user {user_to_delete.username}? This action cannot be undone and will delete all related records."):
            try:
                db_session.delete(user_to_delete)
                db_session.commit()
                messagebox.showinfo("Success", f"User {user_to_delete.username} deleted successfully.")
                log_action(self.app.current_user.username, self.app.current_user.role, 'Delete User',
                           old_value=user_to_delete.username)
            except Exception as e:
                db_session.rollback()
                messagebox.showerror("Error", f"Could not delete user: {e}\n{traceback.format_exc()}")
                print(f"Error during user deletion: {traceback.format_exc()}")
            finally:
                self.load_users()

    def show_admin_salaries(self):
        """Displays the admin panel for managing user salaries and viewing deduction history."""
        self.clear_frame()
        admin_salaries_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        admin_salaries_frame.pack(expand=True, fill="both")
        admin_salaries_frame.grid_columnconfigure(0, weight=1)
        admin_salaries_frame.grid_rowconfigure(3, weight=1)
        admin_salaries_frame.grid_rowconfigure(5, weight=1)

        ttk.Label(admin_salaries_frame, text="Admin: Manage Salaries", style="Header.TLabel").grid(row=0, column=0,
                                                                                                   pady=15)

        adjust_salary_frame = ttk.LabelFrame(admin_salaries_frame, text="Adjust Salary / Clear Debt", padding="15")
        adjust_salary_frame.grid(row=1, column=0, pady=10, sticky="ew", padx=10)
        adjust_salary_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(adjust_salary_frame, text="Select User:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5,
                                                                                 pady=3)
        users_for_salary = db_session.query(User).all()
        self.salary_user_combobox = ttk.Combobox(adjust_salary_frame,
                                                 values=[f"{u.username} (ID: {u.id})" for u in users_for_salary],
                                                 style="TCombobox")
        self.salary_user_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(adjust_salary_frame, text="Amount (₦):", style="TLabel").grid(row=1, column=0, sticky="w", padx=5,
                                                                                pady=3)
        self.salary_amount_entry = ttk.Entry(adjust_salary_frame, style="TEntry")
        self.salary_amount_entry.insert(0, "0.00")
        self.salary_amount_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(adjust_salary_frame, text="Reason:", style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.salary_reason_entry = ttk.Entry(adjust_salary_frame, style="TEntry")
        self.salary_reason_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        button_frame = ttk.Frame(adjust_salary_frame, style="TFrame")
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(button_frame, text="Add Bonus", command=lambda: self.adjust_salary_action('add_bonus'),
                   style="TButton").pack(side="left", padx=5, ipadx=5, ipady=3)
        ttk.Button(button_frame, text="Deduct Penalty", command=lambda: self.adjust_salary_action('deduct_penalty'),
                   style="Danger.TButton").pack(side="left", padx=5, ipadx=5, ipady=3)
        ttk.Button(button_frame, text="Clear Debt", command=lambda: self.adjust_salary_action('clear_debt'),
                   style="TButton").pack(side="left", padx=5, ipadx=5, ipady=3)

        ttk.Label(admin_salaries_frame, text="Current Salary Balances", style="SectionHeader.TLabel").grid(row=2,
                                                                                                           column=0,
                                                                                                           pady=10)
        balance_columns = ('Username', 'Role', 'Monthly Salary', 'Current Balance')
        self.balance_tree = ttk.Treeview(admin_salaries_frame, columns=balance_columns, show='headings')
        for col in balance_columns:
            self.balance_tree.heading(col, text=col)
            self.balance_tree.column(col, anchor='center')
        self.balance_tree.column('Username', width=120, stretch=True)
        self.balance_tree.column('Role', width=80, stretch=False)
        self.balance_tree.column('Monthly Salary', width=120, stretch=False)
        self.balance_tree.column('Current Balance', width=150, stretch=False)

        balance_scroll = ttk.Scrollbar(admin_salaries_frame, orient="vertical", command=self.balance_tree.yview)
        self.balance_tree.configure(yscrollcommand=balance_scroll.set)
        balance_scroll.grid(row=3, column=1, sticky="ns", padx=(0, 10))
        self.balance_tree.grid(row=3, column=0, sticky="nsew", padx=(10, 0), pady=5)
        self.load_salary_balances()

        ttk.Label(admin_salaries_frame, text="Deduction History", style="SectionHeader.TLabel").grid(row=4, column=0,
                                                                                                     pady=10)
        deduction_columns = ('User', 'Date', 'Amount (₦)', 'Reason', 'Timestamp')
        self.deduction_tree = ttk.Treeview(admin_salaries_frame, columns=deduction_columns, show='headings')
        for col in deduction_columns:
            self.deduction_tree.heading(col, text=col)
            self.deduction_tree.column(col, anchor='center')
        self.deduction_tree.column('User', width=100, stretch=False)
        self.deduction_tree.column('Date', width=100, stretch=False)
        self.deduction_tree.column('Amount (₦)', width=100, stretch=False)
        self.deduction_tree.column('Reason', width=200, stretch=True)
        self.deduction_tree.column('Timestamp', width=150, stretch=False)

        deduction_scroll = ttk.Scrollbar(admin_salaries_frame, orient="vertical", command=self.deduction_tree.yview)
        self.deduction_tree.configure(yscrollcommand=deduction_scroll.set)
        deduction_scroll.grid(row=5, column=1, sticky="ns", padx=(0, 10))
        self.deduction_tree.grid(row=5, column=0, sticky="nsew", padx=(10, 0), pady=5)
        self.load_deduction_history()

        ttk.Button(admin_salaries_frame, text="Back to Dashboard", command=self.app.show_dashboard,
                   style="TButton").grid(
            row=6, column=0, pady=20, ipadx=10, ipady=5)

    def load_salary_balances(self):
        for i in self.balance_tree.get_children():
            self.balance_tree.delete(i)
        users = db_session.query(User).all()
        for user in users:
            self.balance_tree.insert('', 'end', values=(
                user.username, user.role, f"₦{user.monthly_salary:.2f}",
                f"₦{user.current_salary_balance:.2f}"
            ))

    def load_deduction_history(self):
        for i in self.deduction_tree.get_children():
            self.deduction_tree.delete(i)
        deductions = db_session.query(SalaryDeduction).order_by(SalaryDeduction.timestamp.desc()).all()
        for ded in deductions:
            user = db_session.query(User).get(ded.user_id)
            username = user.username if user else "N/A"
            self.deduction_tree.insert('', 'end', values=(
                username, ded.deduction_date.strftime('%Y-%m-%d'),
                f"₦{ded.amount:.2f}", ded.reason, ded.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ))

    def adjust_salary_action(self, action_type):
        selected_user_str = self.salary_user_combobox.get()
        if not selected_user_str:
            messagebox.showerror("Input Error", "Please select a user.")
            return

        try:
            user_id_str = selected_user_str.split('(ID: ')[1][:-1]
            user_id = int(user_id_str)
        except (IndexError, ValueError):
            messagebox.showerror("Input Error", "Invalid user selection format. Please select from the dropdown.")
            return

        target_user = db_session.query(User).get(user_id)

        if not target_user:
            messagebox.showerror("Error", "Selected user not found.")
            self.load_salary_balances()
            return

        try:
            amount = float(self.salary_amount_entry.get())
            if amount < 0:
                raise ValueError("Amount cannot be negative.")
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a non-negative number.")
            return

        reason = self.salary_reason_entry.get()
        if not reason:
            messagebox.showerror("Input Error", "Reason cannot be empty.")
            return

        try:
            old_balance = target_user.current_salary_balance
            if action_type == 'add_bonus':
                target_user.current_salary_balance += amount
                messagebox.showinfo("Success", f"Bonus of ₦{amount:.2f} added to {target_user.username}.")
                log_action(self.app.current_user.username, self.app.current_user.role, 'Add Bonus',
                           old_value=f"User:{target_user.username}, Old Balance:{old_balance}",
                           new_value=f"New Balance:{target_user.current_salary_balance}, Reason:{reason}")
            elif action_type == 'deduct_penalty':
                target_user.current_salary_balance -= amount
                deduction = SalaryDeduction(user_id=target_user.id, amount=amount, reason=f"Manual Penalty: {reason}")
                db_session.add(deduction)
                messagebox.showinfo("Success", f"Penalty of ₦{amount:.2f} deducted from {target_user.username}.")
                log_action(self.app.current_user.username, self.app.current_user.role, 'Deduct Penalty',
                           old_value=f"User:{target_user.username}, Old Balance:{old_balance}",
                           new_value=f"New Balance:{target_user.current_salary_balance}, Reason:{reason}")
            elif action_type == 'clear_debt':
                if target_user.current_salary_balance < 0:
                    if amount >= abs(target_user.current_salary_balance):
                        target_user.current_salary_balance = 0.0
                        messagebox.showinfo("Success", f"Debt for {target_user.username} fully cleared.")
                    else:
                        target_user.current_salary_balance += amount
                        messagebox.showinfo("Success", f"₦{amount:.2f} reduced from {target_user.username}'s debt.")
                    log_action(self.app.current_user.username, self.app.current_user.role, 'Clear Debt',
                               old_value=f"User:{target_user.username}, Old Balance:{old_balance}",
                               new_value=f"New Balance:{target_user.current_salary_balance}, Amount Cleared:{amount}, Reason:{reason}")
                else:
                    messagebox.showinfo("Info", f"{target_user.username} does not have a negative balance.")
            db_session.commit()
            self.salary_amount_entry.delete(0, tk.END)
            self.salary_reason_entry.delete(0, tk.END)
            self.load_salary_balances()
            self.load_deduction_history()
            self.app.dashboard_view.update_user_info_label()  # Update header if current user's salary was adjusted
        except Exception as e:
            db_session.rollback()
            messagebox.showerror("Error", f"An error occurred during salary adjustment: {e}\n{traceback.format_exc()}")
            print(f"Error during salary adjustment: {traceback.format_exc()}")

    def show_admin_audit_logs(self):
        """Displays the audit log history for all system actions."""
        self.clear_frame()
        audit_logs_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        audit_logs_frame.pack(expand=True, fill="both")
        audit_logs_frame.grid_columnconfigure(0, weight=1)
        audit_logs_frame.grid_rowconfigure(1, weight=1)

        ttk.Label(audit_logs_frame, text="Admin: Audit Logs", style="Header.TLabel").grid(row=0, column=0, pady=15)

        columns = ('Timestamp', 'User', 'Role', 'Action Type', 'Old Value', 'New Value')
        self.logs_tree = ttk.Treeview(audit_logs_frame, columns=columns, show='headings')
        for col in columns:
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, anchor='center')
        self.logs_tree.column('Timestamp', width=150, stretch=False)
        self.logs_tree.column('User', width=100, stretch=False)
        self.logs_tree.column('Role', width=80, stretch=False)
        self.logs_tree.column('Action Type', width=150, stretch=False)
        self.logs_tree.column('Old Value', width=200, stretch=True)
        self.logs_tree.column('New Value', width=200, stretch=True)

        logs_scroll = ttk.Scrollbar(audit_logs_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=logs_scroll.set)
        logs_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 10))
        self.logs_tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5)

        self.load_audit_logs()

        ttk.Button(audit_logs_frame, text="Back to Dashboard", command=self.app.show_dashboard, style="TButton").grid(
            row=2, column=0, pady=20, ipadx=10, ipady=5)

    def load_audit_logs(self):
        for i in self.logs_tree.get_children():
            self.logs_tree.delete(i)
        logs = db_session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        for log in logs:
            self.logs_tree.insert('', 'end', values=(
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), log.username, log.user_role,
                log.action_type, log.old_value if log.old_value else 'N/A',
                log.new_value if log.new_value else 'N/A'
            ))
