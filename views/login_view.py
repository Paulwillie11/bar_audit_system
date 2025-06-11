import tkinter as tk
from tkinter import ttk, messagebox
from views.base_ui import BaseUI # Import BaseUI for common methods
from database import db_session # Import db_session to interact with the database
from models import User # Import User model
from helpers import log_action # Import logging utility

class LoginView(BaseUI):
    def __init__(self, master, app_instance):
        super().__init__(master, app_instance)
        self.setup_styles() # Call setup_styles from BaseUI

    def create_login_ui(self):
        """Creates the login user interface."""
        self.clear_frame()
        self.login_frame = ttk.Frame(self.master, padding="50", style="TFrame")
        self.login_frame.pack(expand=True, fill="both")

        # Center content using grid weights for responsiveness
        self.login_frame.grid_rowconfigure(0, weight=1)
        self.login_frame.grid_rowconfigure(7, weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_columnconfigure(2, weight=1)

        login_label = ttk.Label(self.login_frame, text="Login to Bar Audit System", style="Header.TLabel")
        login_label.grid(row=1, column=1, pady=30)

        username_label = ttk.Label(self.login_frame, text="Username:", style="TLabel")
        username_label.grid(row=2, column=1, sticky="w", pady=5)
        self.username_entry = ttk.Entry(self.login_frame, width=35, style="TEntry")
        self.username_entry.grid(row=3, column=1, pady=5, ipady=3)
        self.username_entry.focus_set()

        password_label = ttk.Label(self.login_frame, text="Password:", style="TLabel")
        password_label.grid(row=4, column=1, sticky="w", pady=5)
        self.password_entry = ttk.Entry(self.login_frame, width=35, show="*", style="TEntry")
        self.password_entry.grid(row=5, column=1, pady=5, ipady=3)
        self.password_entry.bind("<Return>", lambda event: self.attempt_login()) # Allow Enter key to login

        login_button = ttk.Button(self.login_frame, text="Login", command=self.attempt_login, style="TButton")
        login_button.grid(row=6, column=1, pady=25, ipadx=20, ipady=8)

        ttk.Label(self.login_frame, text="Try: admin/admin123, manager/password, staff1/password", style="SmallInfo.TLabel").grid(row=7, column=1, pady=10)

    def attempt_login(self):
        """Authenticates user credentials and navigates to dashboard on success."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        user = db_session.query(User).filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            self.app.current_user = user # Set current_user in the main app instance
            log_action(user.username, user.role, 'User Login')
            self.app.show_dashboard() # Call show_dashboard on the main app instance
        else:
            messagebox.showerror("Login Failed", "Invalid username or password, or account is inactive.")
            log_action(username, "Unknown", 'Login Failed')
