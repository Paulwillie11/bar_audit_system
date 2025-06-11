import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from views.base_ui import BaseUI
from database import db_session
from models import User, InventoryItem, StaffSaleEntry, CashRegisterEntry, SalaryDeduction
from helpers import log_action


class StaffViews(BaseUI):
    def __init__(self, master, app_instance):
        super().__init__(master, app_instance)

    def show_staff_sales_entry(self):
        """Displays the staff's sales and cash declaration panel."""
        self.clear_frame()
        staff_sales_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        staff_sales_frame.pack(expand=True, fill="both")
        staff_sales_frame.grid_columnconfigure(0, weight=1)  # Make column expandable
        staff_sales_frame.grid_rowconfigure(3, weight=1)  # Allow sales tree to expand

        ttk.Label(staff_sales_frame, text="Staff: My Sales & Cash Declaration", style="Header.TLabel").grid(row=0,
                                                                                                            column=0,
                                                                                                            pady=15)
        ttk.Label(staff_sales_frame, text=f"Date: {date.today().strftime('%Y-%m-%d')}", style="SubHeader.TLabel").grid(
            row=1, column=0, pady=5)

        today = date.today()
        staff_sales_today = db_session.query(StaffSaleEntry).filter_by(staff_id=self.app.current_user.id,
                                                                       entry_date=today).all()
        inventory_items = db_session.query(InventoryItem).all()  # Get all inventory items for combobox
        cash_entry_today = db_session.query(CashRegisterEntry).filter_by(user_id=self.app.current_user.id,
                                                                         entry_date=today).first()

        # Conditionally display UI sections based on completion status
        if not cash_entry_today or not cash_entry_today.is_finalized:
            # Section for Entering Sales
            add_sale_frame = ttk.LabelFrame(staff_sales_frame, text="Enter Items Sold", padding="15")
            add_sale_frame.grid(row=2, column=0, pady=10, sticky="ew", padx=10)
            add_sale_frame.grid_columnconfigure(1, weight=1)  # Make entry column expandable

            ttk.Label(add_sale_frame, text="Select Item:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5,
                                                                                pady=3)
            self.sale_item_combobox = ttk.Combobox(add_sale_frame, values=[item.name for item in inventory_items],
                                                   style="TCombobox")
            self.sale_item_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=3, ipady=2)

            ttk.Label(add_sale_frame, text="Quantity:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5,
                                                                             pady=3)
            self.sale_quantity_entry = ttk.Entry(add_sale_frame, style="TEntry")
            self.sale_quantity_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3, ipady=2)

            ttk.Button(add_sale_frame, text="Add Sale", command=self.add_staff_sale, style="TButton").grid(row=2,
                                                                                                           column=0,
                                                                                                           columnspan=2,
                                                                                                           pady=15,
                                                                                                           ipadx=10,
                                                                                                           ipady=5)

            # Section for displaying today's sales
            sales_display_frame = ttk.LabelFrame(staff_sales_frame, text="Your Sales for Today", padding="15")
            sales_display_frame.grid(row=3, column=0, pady=10, sticky="nsew", padx=10)  # Made sticky nsew
            sales_display_frame.grid_columnconfigure(0, weight=1)  # Center total sales label and button
            sales_display_frame.grid_rowconfigure(0, weight=1)  # Allow treeview to expand

            sales_columns = ('Item', 'Quantity', 'Price/Unit', 'Total Cost', 'Status')
            self.staff_sales_tree = ttk.Treeview(sales_display_frame, columns=sales_columns, show='headings')
            for col in sales_columns:
                self.staff_sales_tree.heading(col, text=col)
                self.staff_sales_tree.column(col, anchor='center')
            self.staff_sales_tree.column('Item', width=150, stretch=True)
            self.staff_sales_tree.column('Quantity', width=80, stretch=False)
            self.staff_sales_tree.column('Price/Unit', width=100, stretch=False)
            self.staff_sales_tree.column('Total Cost', width=100, stretch=False)
            self.staff_sales_tree.column('Status', width=80, stretch=False)

            # Add scrollbar for staff sales tree
            staff_sales_scroll = ttk.Scrollbar(sales_display_frame, orient="vertical",
                                               command=self.staff_sales_tree.yview)
            self.staff_sales_tree.configure(yscrollcommand=staff_sales_scroll.set)
            staff_sales_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 5))
            self.staff_sales_tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)  # Made sticky nsew
            self.load_staff_sales()

            system_total_sales = sum(sale.total_cost for sale in staff_sales_today)
            self.total_sales_label = ttk.Label(sales_display_frame,
                                               text=f"Total System Sales: ₦{system_total_sales:.2f}",
                                               style="Info.TLabel")
            self.total_sales_label.grid(row=1, column=0, pady=10, sticky="e", padx=5)  # Use grid for alignment

            # Conditionally display "Submit All Sales" button
            all_sales_submitted = all(sale.is_submitted for sale in staff_sales_today)
            if not all_sales_submitted and staff_sales_today:
                ttk.Button(sales_display_frame, text="Submit All Today's Sales", command=self.submit_all_staff_sales,
                           style="TButton").grid(row=2, column=0, pady=15, sticky="ew", ipadx=10, ipady=5)  # Use grid
            elif staff_sales_today:  # All sales submitted, but cash declaration is pending
                ttk.Label(sales_display_frame, text="All your sales for today have been submitted.",
                          style="SmallInfo.TLabel").grid(row=2, column=0, pady=5)  # Use grid
            elif not staff_sales_today:  # No sales recorded for today
                ttk.Label(sales_display_frame, text="You have no sales recorded for today yet.",
                          style="SmallInfo.TLabel").grid(row=2, column=0, pady=5)  # Use grid

            # Cash & POS Declaration Section (only visible if all sales are submitted)
            if all_sales_submitted and staff_sales_today:
                cash_pos_declaration_frame = ttk.LabelFrame(staff_sales_frame, text="Declare End-of-Shift Cash & POS",
                                                            padding="15")
                cash_pos_declaration_frame.grid(row=4, column=0, pady=10, sticky="ew", padx=10)
                cash_pos_declaration_frame.grid_columnconfigure(0, weight=1)  # Center content

                ttk.Label(cash_pos_declaration_frame,
                          text=f"Your total system sales for today is: ₦{system_total_sales:.2f}",
                          style="Info.TLabel").pack(pady=5)

                ttk.Label(cash_pos_declaration_frame, text="Declared Cash (₦):", style="TLabel").pack(pady=5)
                self.declared_cash_entry = ttk.Entry(cash_pos_declaration_frame, style="TEntry")
                if cash_entry_today:  # Pre-fill if a previous declaration was attempted
                    self.declared_cash_entry.insert(0, f"{cash_entry_today.declared_cash:.2f}")
                self.declared_cash_entry.pack(pady=5, ipady=2)

                ttk.Label(cash_pos_declaration_frame, text="Declared POS (₦):", style="TLabel").pack(pady=5)
                self.declared_pos_entry = ttk.Entry(cash_pos_declaration_frame, style="TEntry")
                if cash_entry_today:  # Pre-fill if a previous declaration was attempted
                    self.declared_pos_entry.insert(0, f"{cash_entry_today.declared_pos:.2f}")
                self.declared_pos_entry.pack(pady=5, ipady=2)

                ttk.Button(cash_pos_declaration_frame, text="Submit Cash & POS Declaration",
                           command=self.submit_staff_cash_pos, style="TButton").pack(pady=15, ipadx=10, ipady=5)

        else:  # Cash entry has been finalized for today
            finalized_declaration_frame = ttk.LabelFrame(staff_sales_frame, text="Your Finalized Declaration",
                                                         padding="15")
            finalized_declaration_frame.grid(row=2, column=0, pady=10, sticky="ew", padx=10)
            finalized_declaration_frame.grid_columnconfigure(0, weight=1)

            ttk.Label(finalized_declaration_frame, text="Your Cash & POS Declaration Finalized!",
                      style="Info.TLabel").grid(row=0, column=0, pady=10)
            ttk.Label(finalized_declaration_frame, text=f"Declared Cash: ₦{cash_entry_today.declared_cash:.2f}",
                      style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(finalized_declaration_frame, text=f"Declared POS: ₦{cash_entry_today.declared_pos:.2f}",
                      style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(finalized_declaration_frame,
                      text=f"System Total Sales: ₦{cash_entry_today.system_total_sales:.2f}",
                      style="TLabel").grid(row=3, column=0, sticky="w", padx=5, pady=2)
            mismatch_color_style = "Warning.TLabel" if cash_entry_today.mismatch_amount != 0 else "Info.TLabel"
            ttk.Label(finalized_declaration_frame, text=f"Mismatch Amount: ₦{cash_entry_today.mismatch_amount:.2f}",
                      style=mismatch_color_style).grid(row=4, column=0, sticky="w", padx=5, pady=2)
            if cash_entry_today.deduction_amount > 0:
                ttk.Label(finalized_declaration_frame,
                          text=f"Deduction Applied: ₦{cash_entry_today.deduction_amount:.2f} from your salary.",
                          style="Warning.TLabel").grid(row=5, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(finalized_declaration_frame, text="You have completed your declarations for today.",
                      style="SmallInfo.TLabel").grid(row=6, column=0, pady=5)

        ttk.Button(staff_sales_frame, text="Back to Dashboard", command=self.app.show_dashboard, style="TButton").grid(
            row=5, column=0, pady=20, ipadx=10, ipady=5)

    def load_staff_sales(self):
        """Loads and displays the current staff's sales entries for today."""
        for i in self.staff_sales_tree.get_children():
            self.staff_sales_tree.delete(i)
        today = date.today()
        sales = db_session.query(StaffSaleEntry).filter_by(staff_id=self.app.current_user.id, entry_date=today).all()
        for sale in sales:
            status = "Submitted" if sale.is_submitted else "Pending"
            self.staff_sales_tree.insert('', 'end', values=(
                sale.item_name, sale.quantity, f"₦{sale.price_per_unit:.2f}", f"₦{sale.total_cost:.2f}", status
            ))

    def add_staff_sale(self):
        """Adds a new sales entry for the current staff."""
        item_name = self.sale_item_combobox.get()
        try:
            quantity = int(self.sale_quantity_entry.get())
            if quantity <= 0:
                messagebox.showerror("Input Error", "Quantity must be positive.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid positive number for quantity.")
            return

        item = db_session.query(InventoryItem).filter_by(name=item_name).first()
        if not item:
            messagebox.showerror("Error", "Selected item not found in inventory. Please choose an existing item.")
            return

        total_cost = item.price_per_unit * quantity
        new_sale = StaffSaleEntry(
            staff_id=self.app.current_user.id,
            entry_date=date.today(),
            item_name=item.name,
            quantity=quantity,
            price_per_unit=item.price_per_unit,
            total_cost=total_cost,
            is_submitted=False  # Initially, not submitted until "Submit All Today's Sales" is clicked
        )
        db_session.add(new_sale)
        db_session.commit()
        messagebox.showinfo("Success",
                            f"Sale of {quantity} x {item.name} recorded. Don't forget to Submit All Today's Sales!")
        log_action(self.app.current_user.username, self.app.current_user.role, 'Staff Add Sale',
                   new_value=f"{item.name} x {quantity}")
        self.sale_quantity_entry.delete(0, tk.END)  # Clear quantity entry
        self.load_staff_sales()  # Refresh sales list
        self.update_staff_total_sales_label()  # Update total sales display

    def update_staff_total_sales_label(self):
        """Updates the label displaying the current staff's total system sales for today."""
        today = date.today()
        staff_sales_today = db_session.query(StaffSaleEntry).filter_by(staff_id=self.app.current_user.id,
                                                                       entry_date=today).all()
        system_total_sales = sum(sale.total_cost for sale in staff_sales_today)
        # Check if the label object exists and is still part of the UI
        if hasattr(self, 'total_sales_label') and self.total_sales_label.winfo_exists():
            self.total_sales_label.config(text=f"Total System Sales: ₦{system_total_sales:.2f}")

    def submit_all_staff_sales(self):
        """Submits all pending sales entries for the current staff for today."""
        today = date.today()
        staff_sales_today = db_session.query(StaffSaleEntry).filter_by(staff_id=self.app.current_user.id,
                                                                       entry_date=today,
                                                                       is_submitted=False).all()

        if not staff_sales_today:
            messagebox.showinfo("Info", "No pending sales to submit for today.")
            return

        if not messagebox.askyesno("Confirm Submission",
                                   "Are you sure you want to submit all your pending sales for today? This cannot be changed later."):
            return

        for sale in staff_sales_today:
            sale.is_submitted = True  # Mark sales as submitted
        db_session.commit()
        messagebox.showinfo("Success", "Your sales for today have been submitted. Now proceed to Declare Cash & POS.")
        log_action(self.app.current_user.username, self.app.current_user.role, 'Staff Submit Sales',
                   new_value=f"Sales for {today}")
        self.show_staff_sales_entry()  # Reload UI to show next step (cash declaration)

    def submit_staff_cash_pos(self):
        """Submits the staff's cash and POS declaration, calculates mismatch, and applies deductions."""
        today = date.today()
        current_user = self.app.current_user

        staff_sales_today = db_session.query(StaffSaleEntry).filter_by(staff_id=current_user.id, entry_date=today,
                                                                       is_submitted=True).all()
        if not staff_sales_today:
            messagebox.showerror("Error",
                                 "No submitted sales to declare cash/POS for today. Please submit sales first.")
            return

        try:
            declared_cash = float(self.declared_cash_entry.get())
            declared_pos = float(self.declared_pos_entry.get())
            if declared_cash < 0 or declared_pos < 0:
                raise ValueError("Declared amounts cannot be negative.")
        except ValueError:
            messagebox.showerror("Input Error", "Declared Cash and POS must be numbers.")
            return

        system_total_sales = sum(sale.total_cost for sale in staff_sales_today)

        if not messagebox.askyesno("Confirm Declaration",
                                   "Are you sure you want to submit your cash and POS declaration for today? This action is final."):
            return

        # Create or update CashRegisterEntry for staff
        cash_register_entry = db_session.query(CashRegisterEntry).filter_by(user_id=current_user.id,
                                                                            entry_date=today).first()
        if not cash_register_entry:
            cash_register_entry = CashRegisterEntry(user_id=current_user.id, entry_date=today)
            db_session.add(cash_register_entry)

        cash_register_entry.declared_cash = declared_cash
        cash_register_entry.declared_pos = declared_pos
        cash_register_entry.system_total_sales = system_total_sales
        cash_register_entry.is_finalized = True  # Mark cash entry as finalized

        total_declared = declared_cash + declared_pos
        mismatch = total_declared - system_total_sales
        deduction_amount = 0.0

        if mismatch != 0:
            deduction_amount = abs(mismatch)
            cash_register_entry.mismatch_amount = mismatch
            cash_register_entry.deduction_amount = deduction_amount

            old_balance = current_user.current_salary_balance
            current_user.current_salary_balance -= deduction_amount  # Deduct from staff's salary
            db_session.add(SalaryDeduction(  # Record the deduction
                user_id=current_user.id,
                amount=deduction_amount,
                reason=f"Staff Cash/POS Mismatch for {today}. Expected: ₦{system_total_sales:.2f}, Declared: ₦{total_declared:.2f}"
            ))
            messagebox.showwarning("Mismatch Detected",
                                   f"Mismatch: ₦{mismatch:.2f}. ₦{deduction_amount:.2f} deducted from your salary.")
            log_action(current_user.username, current_user.role, 'Staff Cash/POS Mismatch Deduction',
                       old_value=f"Old Balance:{old_balance}",
                       new_value=f"New Balance:{current_user.current_salary_balance}, Deduction:{deduction_amount}")
        else:
            messagebox.showinfo("Success", "Cash and POS declaration tally with system sales. No deduction.")

        db_session.commit()
        self.app.dashboard_view.update_user_info_label()  # Update header salary display
        self.show_staff_sales_entry()  # Reload UI to show finalized state
