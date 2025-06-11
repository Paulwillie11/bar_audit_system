import tkinter as tk
from tkinter import messagebox
import traceback
from datetime import date

# Import modules
from database import engine, db_session, Base
from models import User, InventoryItem # Import models for initial data
from helpers import log_action

# Import view classes
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.admin_views import AdminViews
from views.manager_views import ManagerViews
from views.staff_views import StaffViews

class BarAuditApp:
    def __init__(self, master):
        self.master = master
        master.title("Bar Audit System")
        master.geometry("1200x800")
        master.state('zoomed')
        master.resizable(True, True)

        self.current_user = None

        # Initialize view instances
        self.login_view = LoginView(master, self)
        self.dashboard_view = DashboardView(master, self)
        self.admin_view = AdminViews(master, self)
        self.manager_view = ManagerViews(master, self)
        self.staff_view = StaffViews(master, self)

        # Call setup_styles from one of the view instances (they share BaseUI)
        # or directly from a common utility if preferred. Keeping it here for initial setup.
        self.login_view.setup_styles() # Any view object derived from BaseUI can call this

        # Create initial data and display login UI
        self.create_initial_data()
        self.login_view.create_login_ui()

    def create_initial_data(self):
        """Creates initial admin, manager, staff users and inventory items if DB is empty."""
        try:
            Base.metadata.create_all(engine)

            if db_session.query(User).count() == 0:
                admin_user = User(username='admin', role='Admin', monthly_salary=500000.0,
                                  current_salary_balance=500000.0)
                admin_user.set_password('admin123')
                db_session.add(admin_user)
                db_session.commit()
                messagebox.showinfo("Initial Setup",
                                    "Initial Admin user 'admin' created with password 'admin123'. Please change it immediately after first login!",
                                    icon="info")
                log_action('System', 'System', 'Initial Admin User Created')

                manager_user = User(username='manager', role='Manager', monthly_salary=300000.0, current_salary_balance=300000.0)
                manager_user.set_password('password')
                db_session.add(manager_user)
                log_action('System', 'System', 'Sample Manager User Created')

                staff_user1 = User(username='staff1', role='Staff', monthly_salary=150000.0, current_salary_balance=150000.0)
                staff_user1.set_password('password')
                db_session.add(staff_user1)
                log_action('System', 'System', 'Sample Staff1 User Created')

                staff_user2 = User(username='staff2', role='Staff', monthly_salary=150000.0, current_salary_balance=150000.0)
                staff_user2.set_password('password')
                db_session.add(staff_user2)
                log_action('System', 'System', 'Sample Staff2 User Created')

                db_session.commit()

            if db_session.query(InventoryItem).count() == 0:
                item1 = InventoryItem(name='Beer Bottle', price_per_unit=1000.0, opening_stock=50, closing_stock=50, supply_qty=0)
                item2 = InventoryItem(name='Wine Glass', price_per_unit=2500.0, opening_stock=30, closing_stock=30, supply_qty=0)
                item3 = InventoryItem(name='Soda Can', price_per_unit=500.0, opening_stock=100, closing_stock=100, supply_qty=0)
                db_session.add_all([item1, item2, item3])
                db_session.commit()
                log_action('System', 'System', 'Initial Inventory Items Created')

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}", icon="error")
            traceback.print_exc()

    def show_dashboard(self):
        """Delegates to the dashboard view to display the main dashboard."""
        self.dashboard_view.show_dashboard()

# Entry point of the application
if __name__ == '__main__':
    root = tk.Tk()
    app = BarAuditApp(root)
    root.mainloop()
