import tkinter as tk
from tkinter import ttk, messagebox
from views.base_ui import BaseUI
from database import db_session # For refreshing user
from helpers import log_action

class DashboardView(BaseUI):
    def __init__(self, master, app_instance):
        super().__init__(master, app_instance)

    def show_dashboard(self):
        """Displays the main dashboard with navigation options based on user role."""
        self.clear_frame()

        # Create a header bar at the top
        self.header_frame = ttk.Frame(self.master, style="TFrame", height=60)
        self.header_frame.pack(fill='x', side='top')
        self.header_frame.grid_propagate(False)

        # Left side: App title
        ttk.Label(self.header_frame, text="Bar Audit System", style="Header.TLabel").pack(side='left', padx=20, pady=5)

        # Right side: User info and logout button
        logout_button = ttk.Button(self.header_frame, text="Logout", command=self.logout, style="TButton")
        logout_button.pack(side='right', padx=10, pady=5)

        self.user_info_label = ttk.Label(self.header_frame, text="", style="SubHeader.TLabel")
        self.user_info_label.pack(side='right', padx=20, pady=5)
        self.update_user_info_label()

        # Create main content frame for dashboard options
        self.dashboard_content_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        self.dashboard_content_frame.pack(expand=True, fill="both")
        self.dashboard_content_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_content_frame.grid_rowconfigure(0, weight=1)
        self.dashboard_content_frame.grid_rowconfigure(2, weight=1)

        # Welcome message
        welcome_label = ttk.Label(self.dashboard_content_frame,
                                  text=f"Welcome, {self.app.current_user.username} ({self.app.current_user.role})!",
                                  style="SubHeader.TLabel")
        welcome_label.grid(row=1, column=0, pady=15)

        # Container for navigation buttons
        button_container = ttk.Frame(self.dashboard_content_frame, style="TFrame")
        button_container.grid(row=2, column=0, pady=30, sticky="nsew")
        button_container.grid_columnconfigure(0, weight=1)

        # Add buttons dynamically based on user role
        buttons_data = []
        if self.app.current_user.role == 'Admin':
            buttons_data.append(("Manage Users", self.app.admin_view.show_admin_users))
            buttons_data.append(("Manage Salaries", self.app.admin_view.show_admin_salaries))
            buttons_data.append(("View Audit Logs", self.app.admin_view.show_admin_audit_logs))
            buttons_data.append(("Inventory Management (Admin)", self.app.manager_view.show_manager_inventory))
        elif self.app.current_user.role == 'Manager':
            buttons_data.append(("Inventory Management", self.app.manager_view.show_manager_inventory))
            buttons_data.append(("Daily Stock & Sales Entry", self.app.manager_view.show_manager_daily_stock))
            buttons_data.append(("Generate Reports", self.app.manager_view.show_manager_reports))
        elif self.app.current_user.role == 'Staff':
            buttons_data.append(("My Sales & Cash Declaration", self.app.staff_view.show_staff_sales_entry))

        # Create buttons in a grid layout
        for i, (text, command) in enumerate(buttons_data):
            ttk.Button(button_container, text=text, command=command, style="TButton").grid(row=i, column=0,
                                                                                            pady=7, ipadx=10, ipady=5, sticky="ew")

    def update_user_info_label(self):
        """Updates the user info label in the header with current salary if applicable."""
        db_session.refresh(self.app.current_user)
        if self.app.current_user.role in ['Staff', 'Manager']:
            self.user_info_label.config(text=f"User: {self.app.current_user.username} ({self.app.current_user.role}) | Salary: ₦{self.app.current_user.current_salary_balance:.2f}")
        else:
            self.user_info_label.config(text=f"User: {self.app.current_user.username} ({self.app.current_user.role})")

    def logout(self):
        """Logs out the current user and returns to the login screen."""
        log_action(self.app.current_user.username, self.app.current_user.role, 'User Logout')
        self.app.current_user = None
        messagebox.showinfo("Logout", "You have been logged out.")
        if self.header_frame:
            self.header_frame.destroy()
        if self.dashboard_content_frame:
            self.dashboard_content_frame.destroy()
        self.app.login_view.create_login_ui() # Call create_login_ui on the login view instance
