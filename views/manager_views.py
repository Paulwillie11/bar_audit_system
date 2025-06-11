import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import json  # For serializing/deserializing item_sales_snapshot
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import traceback  # For detailed error printing

from views.base_ui import BaseUI
from database import db_session
from models import User, InventoryItem, DailyStockEntry, StaffSaleEntry, CashRegisterEntry, SalaryDeduction
from helpers import log_action

# Import ReportLab components
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


class ManagerViews(BaseUI):
    def __init__(self, master, app_instance):
        super().__init__(master, app_instance)

    def show_manager_inventory(self):
        """Displays the inventory management panel for managers (and admins)."""
        self.clear_frame()
        manager_inventory_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        manager_inventory_frame.pack(expand=True, fill="both")
        manager_inventory_frame.grid_columnconfigure(0, weight=1)
        manager_inventory_frame.grid_rowconfigure(3, weight=1)

        ttk.Label(manager_inventory_frame, text="Inventory Management", style="Header.TLabel").grid(row=0, column=0,
                                                                                                    pady=15)

        add_item_frame = ttk.LabelFrame(manager_inventory_frame, text="Add New Inventory Item", padding="15")
        add_item_frame.grid(row=1, column=0, pady=10, sticky="ew", padx=10)
        add_item_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(add_item_frame, text="Item Name:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.new_item_name_entry = ttk.Entry(add_item_frame, style="TEntry")
        self.new_item_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(add_item_frame, text="Price Per Unit (₦):", style="TLabel").grid(row=1, column=0, sticky="w", padx=5,
                                                                                   pady=3)
        self.new_item_price_entry = ttk.Entry(add_item_frame, style="TEntry")
        self.new_item_price_entry.insert(0, "0.00")
        self.new_item_price_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Label(add_item_frame, text="Initial Supply Quantity:", style="TLabel").grid(row=2, column=0, sticky="w",
                                                                                        padx=5, pady=3)
        self.new_item_supply_qty_entry = ttk.Entry(add_item_frame, style="TEntry")
        self.new_item_supply_qty_entry.insert(0, "0")
        self.new_item_supply_qty_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=3, ipady=2)

        ttk.Button(add_item_frame, text="Add Item", command=self.add_inventory_item, style="TButton").grid(row=3,
                                                                                                           column=0,
                                                                                                           columnspan=2,
                                                                                                           pady=15,
                                                                                                           ipadx=10,
                                                                                                           ipady=5)

        ttk.Label(manager_inventory_frame, text="Existing Inventory Items", style="SectionHeader.TLabel").grid(row=2,
                                                                                                               column=0,
                                                                                                               pady=10)

        columns = ('ID', 'Item Name', 'Price/Unit', 'Supply Qty', 'Opening Stock')
        self.inventory_tree = ttk.Treeview(manager_inventory_frame, columns=columns, show='headings')
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, anchor='center')
        self.inventory_tree.column('ID', width=50, stretch=False)
        self.inventory_tree.column('Item Name', width=150, stretch=True)
        self.inventory_tree.column('Price/Unit', width=100, stretch=False)
        self.inventory_tree.column('Supply Qty', width=80, stretch=False)
        self.inventory_tree.column('Opening Stock', width=100, stretch=False)

        inventory_scroll = ttk.Scrollbar(manager_inventory_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=inventory_scroll.set)
        inventory_scroll.grid(row=3, column=1, sticky="ns", padx=(0, 10))
        self.inventory_tree.grid(row=3, column=0, sticky="nsew", padx=(10, 0), pady=5)
        self.inventory_tree.bind('<<TreeviewSelect>>', self.on_inventory_selection_change)

        buttons_frame = ttk.Frame(manager_inventory_frame, style="TFrame")
        buttons_frame.grid(row=4, column=0, pady=15)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)

        self.edit_item_button = ttk.Button(buttons_frame, text="Edit Selected Item",
                                           command=self.edit_selected_inventory_item, style="TButton", state='disabled')
        self.edit_item_button.grid(row=0, column=0, padx=10, ipadx=5, ipady=3)

        self.supply_item_button = ttk.Button(buttons_frame, text="Supply Selected Item",
                                             command=self.supply_selected_inventory_item, style="TButton",
                                             state='disabled')
        self.supply_item_button.grid(row=0, column=1, padx=10, ipadx=5, ipady=3)

        self.delete_item_button = ttk.Button(buttons_frame, text="Delete Selected Item",
                                             command=self.delete_selected_inventory_item, style="Danger.TButton",
                                             state='disabled')
        self.delete_item_button.grid(row=0, column=2, padx=10, ipadx=5, ipady=3)

        ttk.Button(manager_inventory_frame, text="Back to Dashboard", command=self.app.show_dashboard,
                   style="TButton").grid(
            row=5, column=0, pady=20, ipadx=10, ipady=5)

        self.load_inventory_items()

    def on_inventory_selection_change(self, event):
        selected_item = self.inventory_tree.focus()
        if selected_item:
            self.edit_item_button.config(state='!disabled')
            self.supply_item_button.config(state='!disabled')
            self.delete_item_button.config(state='!disabled')
        else:
            self.edit_item_button.config(state='disabled')
            self.supply_item_button.config(state='disabled')
            self.delete_item_button.config(state='disabled')

    def load_inventory_items(self):
        for i in self.inventory_tree.get_children():
            self.inventory_tree.delete(i)
        items = db_session.query(InventoryItem).all()
        for item in items:
            self.inventory_tree.insert('', 'end', values=(
                item.id, item.name, f"₦{item.price_per_unit:.2f}", item.supply_qty, item.opening_stock
            ), iid=item.id)
        self.on_inventory_selection_change(None)

    def add_inventory_item(self):
        name = self.new_item_name_entry.get()
        try:
            price = float(self.new_item_price_entry.get())
            initial_supply_qty = int(self.new_item_supply_qty_entry.get())
            if initial_supply_qty < 0:
                messagebox.showerror("Validation Error", "Initial supply quantity cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Price per unit and initial supply quantity must be valid numbers.")
            return

        if not name:
            messagebox.showerror("Input Error", "Item Name cannot be empty.")
            return

        if db_session.query(InventoryItem).filter_by(name=name).first():
            messagebox.showerror("Error", "Item with this name already exists.")
            return

        new_item = InventoryItem(name=name, price_per_unit=price,
                                 supply_qty=initial_supply_qty, opening_stock=initial_supply_qty,
                                 closing_stock=initial_supply_qty)
        db_session.add(new_item)
        db_session.commit()
        messagebox.showinfo("Success", f"Item '{name}' added successfully with initial supply of {initial_supply_qty}!")
        log_action(self.app.current_user.username, self.app.current_user.role, 'Add Inventory Item',
                   new_value=f"Name:{name}, Price:{price}, Initial Supply:{initial_supply_qty}")
        self.new_item_name_entry.delete(0, tk.END)
        self.new_item_price_entry.delete(0, tk.END)
        self.new_item_price_entry.insert(0, "0.00")
        self.new_item_supply_qty_entry.delete(0, tk.END)
        self.new_item_supply_qty_entry.insert(0, "0")
        self.load_inventory_items()

    def open_edit_inventory_modal(self):
        """Opens a modal window to edit details of a selected inventory item."""
        selected_item = self.inventory_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to edit.")
            return

        item_id = int(self.inventory_tree.item(selected_item, 'iid'))
        item_to_edit = db_session.query(InventoryItem).get(item_id)

        if not item_to_edit:
            messagebox.showerror("Error", "Item not found.")
            return

        edit_window = tk.Toplevel(self.master)
        edit_window.title(f"Edit {item_to_edit.name}")
        edit_window.transient(self.master)
        edit_window.grab_set()
        edit_window.protocol("WM_DELETE_WINDOW",
                             lambda: self._on_modal_close_inventory(edit_window))

        edit_frame = ttk.Frame(edit_window, padding="20", style="TFrame")
        edit_frame.pack(expand=True, fill="both")
        edit_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(edit_frame, text="Item Name:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        name_entry = ttk.Entry(edit_frame, style="TEntry")
        name_entry.insert(0, item_to_edit.name)
        name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2, ipady=2)

        ttk.Label(edit_frame, text="Price Per Unit (₦):", style="TLabel").grid(row=1, column=0, sticky="w", padx=5,
                                                                               pady=2)
        price_entry = ttk.Entry(edit_frame, style="TEntry")
        price_entry.insert(0, f"{item_to_edit.price_per_unit:.2f}")
        price_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2, ipady=2)

        def save_changes():
            old_values = f"Name:{item_to_edit.name}, Price:{item_to_edit.price_per_unit}"
            item_to_edit.name = name_entry.get()
            try:
                item_to_edit.price_per_unit = float(price_entry.get())
            except ValueError:
                messagebox.showerror("Input Error", "Price must be a number.")
                return

            db_session.commit()
            messagebox.showinfo("Success", "Item updated successfully!")
            log_action(self.app.current_user.username, self.app.current_user.role, 'Update Inventory Item',
                       old_value=old_values, new_value=f"Name:{item_to_edit.name}, Price:{item_to_edit.price_per_unit}")
            self.load_inventory_items()
            edit_window.destroy()

        button_frame = ttk.Frame(edit_frame, style="TFrame")
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save Changes", command=save_changes, style="TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=lambda: self._on_modal_close_inventory(edit_window),
                   style="TButton").pack(side="left", padx=5)

    def _on_modal_close_inventory(self, window):
        """Helper to ensure grab_release is called when modal is closed for inventory."""
        window.grab_release()
        window.destroy()
        self.on_inventory_selection_change(None)

    def edit_selected_inventory_item(self):
        self.open_edit_inventory_modal()

    def supply_selected_inventory_item(self):
        """Opens a modal window to supply (add stock to) a selected inventory item."""
        selected_item = self.inventory_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to supply.")
            return

        item_id = int(self.inventory_tree.item(selected_item, 'iid'))
        item_to_supply = db_session.query(InventoryItem).get(item_id)

        if not item_to_supply:
            messagebox.showerror("Error", "Item not found.")
            return

        supply_window = tk.Toplevel(self.master)
        supply_window.title(f"Supply {item_to_supply.name}")
        supply_window.transient(self.master)
        supply_window.grab_set()
        supply_window.protocol("WM_DELETE_WINDOW",
                               lambda: self._on_modal_close_inventory(supply_window))

        supply_frame = ttk.Frame(supply_window, padding="20", style="TFrame")
        supply_frame.pack(expand=True, fill="both")

        ttk.Label(supply_frame, text=f"Supplying: {item_to_supply.name}", style="SectionHeader.TLabel").pack(pady=10)

        ttk.Label(supply_frame, text="Quantity to Supply:", style="TLabel").pack(pady=5)
        supply_qty_entry = ttk.Entry(supply_frame, style="TEntry")
        supply_qty_entry.pack(pady=5, ipady=2)

        def perform_supply():
            try:
                qty = int(supply_qty_entry.get())
                if qty <= 0:
                    raise ValueError("Quantity must be positive.")
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid positive number for quantity.")
                return

            old_supply_qty = item_to_supply.supply_qty
            old_opening_stock = item_to_supply.opening_stock
            old_closing_stock = item_to_supply.closing_stock

            item_to_supply.supply_qty += qty
            item_to_supply.opening_stock += qty
            item_to_supply.closing_stock += qty

            db_session.commit()
            messagebox.showinfo("Success", f"Successfully supplied {qty} of {item_to_supply.name}.")
            log_action(self.app.current_user.username, self.app.current_user.role, 'Supply Inventory Item',
                       old_value=f"Item:{item_to_supply.name}, Old Supply:{old_supply_qty}, Old Opening:{old_opening_stock}, Old Closing:{old_closing_stock}",
                       new_value=f"New Supply:{item_to_supply.supply_qty}, New Opening:{item_to_supply.opening_stock}, New Closing:{item_to_supply.closing_stock}")
            self.load_inventory_items()
            supply_window.destroy()
            self.on_inventory_selection_change(None)

        ttk.Button(supply_frame, text="Supply", command=perform_supply, style="TButton").pack(pady=10, ipadx=10,
                                                                                              ipady=5)
        ttk.Button(supply_frame, text="Cancel", command=lambda: self._on_modal_close_inventory(supply_window),
                   style="TButton").pack(pady=5, ipadx=10, ipady=5)

    def delete_selected_inventory_item(self):
        """Deletes the selected inventory item from the database."""
        selected_item = self.inventory_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to delete.")
            return

        item_id = int(self.inventory_tree.item(selected_item, 'iid'))
        item_to_delete = db_session.query(InventoryItem).get(item_id)

        if not item_to_delete:
            messagebox.showerror("Error", "Selected item not found in database. The list will now be refreshed.")
            self.load_inventory_items()
            return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete item {item_to_delete.name}? This cannot be undone."):
            try:
                db_session.delete(item_to_delete)
                db_session.commit()
                messagebox.showinfo("Success", f"Item {item_to_delete.name} deleted.")
                log_action(self.app.current_user.username, self.app.current_user.role, 'Delete Inventory Item',
                           old_value=item_to_delete.name)
            except Exception as e:
                db_session.rollback()
                messagebox.showerror("Error", f"Could not delete item: {e}\n{traceback.format_exc()}")
                print(f"Error during item deletion: {traceback.format_exc()}")
            finally:
                self.load_inventory_items()

    def show_manager_daily_stock(self):
        """Displays the manager's daily stock and sales entry panel."""
        self.clear_frame()
        daily_stock_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        daily_stock_frame.pack(expand=True, fill="both")
        daily_stock_frame.grid_columnconfigure(0, weight=1)
        daily_stock_frame.grid_rowconfigure(2, weight=1)

        ttk.Label(daily_stock_frame, text="Manager: Daily Stock & Sales Entry", style="Header.TLabel").grid(row=0,
                                                                                                            column=0,
                                                                                                            pady=15)
        ttk.Label(daily_stock_frame, text=f"Date: {date.today().strftime('%Y-%m-%d')}", style="SubHeader.TLabel").grid(
            row=1, column=0, pady=5)

        today = date.today()
        daily_entry = db_session.query(DailyStockEntry).filter_by(manager_id=self.app.current_user.id,
                                                                  entry_date=today).first()

        last_daily_entry = db_session.query(DailyStockEntry).filter_by(manager_id=self.app.current_user.id).order_by(
            DailyStockEntry.entry_date.desc()).first()
        if last_daily_entry and (today - last_daily_entry.entry_date).days > 1:
            skipped_days = (today - last_daily_entry.entry_date).days - 1
            messagebox.showwarning("Warning",
                                   f"It appears you have skipped {skipped_days} daily stock entr{'y' if skipped_days == 1 else 'ies'}. Please ensure all previous days are recorded if necessary.")

        stock_entry_content_frame = ttk.Frame(daily_stock_frame, style="TFrame")
        stock_entry_content_frame.grid(row=2, column=0, expand=True, fill="both", padx=10, pady=10)
        stock_entry_content_frame.grid_columnconfigure(0, weight=1)

        if not daily_entry or not daily_entry.is_finalized:
            closing_stock_frame = ttk.LabelFrame(stock_entry_content_frame, text="Enter Closing Stock", padding="15")
            closing_stock_frame.grid(row=0, column=0, pady=10, sticky="ew", padx=10)
            closing_stock_frame.grid_columnconfigure(1, weight=1)

            inventory_items = db_session.query(InventoryItem).all()
            self.closing_stock_entries = {}
            for i, item in enumerate(inventory_items):
                closing_stock_frame.grid_rowconfigure(i, weight=0)
                ttk.Label(closing_stock_frame,
                          text=f"{item.name} (Opening: {item.opening_stock}, Supply: {item.supply_qty}):",
                          style="TLabel").grid(row=i, column=0, sticky="w", padx=5, pady=3)
                entry = ttk.Entry(closing_stock_frame, style="TEntry")

                if daily_entry and daily_entry.item_sales_snapshot:
                    try:
                        snapshot_data = json.loads(daily_entry.item_sales_snapshot)
                        if item.name in snapshot_data:
                            entry.insert(0, str(snapshot_data[item.name].get('closing_stock', '')))
                        else:
                            entry.insert(0, str(item.opening_stock))
                        entry.config(state='readonly')
                    except json.JSONDecodeError:
                        entry.insert(0, str(item.opening_stock))
                        entry.config(state='!readonly')
                else:
                    entry.insert(0, str(item.opening_stock))
                    entry.config(state='!readonly')
                entry.grid(row=i, column=1, sticky="ew", padx=5, pady=3, ipady=2)
                self.closing_stock_entries[item.id] = entry

            self.save_stock_button = ttk.Button(closing_stock_frame, text="Save Stock & Calculate Expected Sales",
                                                command=self.save_daily_stock, style="TButton")
            self.save_stock_button.grid(row=len(inventory_items), column=0, columnspan=2, pady=15, ipadx=10, ipady=5)
            if daily_entry and daily_entry.item_sales_snapshot:
                self.save_stock_button.config(state='disabled')

            if daily_entry and daily_entry.item_sales_snapshot:
                pos_cash_frame = ttk.LabelFrame(stock_entry_content_frame, text="Confirm POS and Cash Declaration",
                                                padding="15")
                pos_cash_frame.grid(row=1, column=0, pady=10, sticky="ew", padx=10)
                pos_cash_frame.grid_columnconfigure(0, weight=1)

                staff_sales_today = db_session.query(StaffSaleEntry).filter(StaffSaleEntry.entry_date == today,
                                                                            StaffSaleEntry.is_submitted == True).all()
                total_system_sales_from_staff = sum(sale.total_cost for sale in staff_sales_today)

                ttk.Label(pos_cash_frame, text=f"Total System Sales from Staff: ₦{total_system_sales_from_staff:.2f}",
                          style="Info.TLabel").pack(pady=5)

                ttk.Label(pos_cash_frame, text="Declared Cash (₦):", style="TLabel").pack(pady=5)
                self.declared_cash_entry = ttk.Entry(pos_cash_frame, style="TEntry")
                if daily_entry.total_pos_cash_declared:
                    self.declared_cash_entry.insert(0,
                                                    f"{(daily_entry.total_pos_cash_declared - daily_entry.declared_pos):.2f}")
                self.declared_cash_entry.pack(pady=5, ipady=2)

                ttk.Label(pos_cash_frame, text="Declared POS (₦):", style="TLabel").pack(pady=5)
                self.declared_pos_entry = ttk.Entry(pos_cash_frame, style="TEntry")
                if daily_entry.total_pos_cash_declared:
                    self.declared_pos_entry.insert(0, f"{daily_entry.declared_pos:.2f}")
                self.declared_pos_entry.pack(pady=5, ipady=2)

                ttk.Button(pos_cash_frame, text="Submit POS + Cash Declaration", command=self.submit_pos_cash,
                           style="TButton").pack(pady=15, ipadx=10, ipady=5)
        else:
            finalized_frame = ttk.LabelFrame(stock_entry_content_frame, text="Daily Stock Entry Finalized",
                                             padding="15")
            finalized_frame.grid(row=0, column=0, pady=10, sticky="ew", padx=10)
            finalized_frame.grid_columnconfigure(0, weight=1)

            ttk.Label(finalized_frame, text="Daily Stock Entry Finalized for Today!",
                      style="Info.TLabel").grid(row=0, column=0, pady=10)
            ttk.Label(finalized_frame,
                      text=f"Expected Sales from Stock Movement: ₦{daily_entry.total_sales_expected:.2f}",
                      style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(finalized_frame, text=f"Declared POS + Cash: ₦{daily_entry.total_pos_cash_declared:.2f}",
                      style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=2)
            mismatch_color_style = "Warning.TLabel" if daily_entry.mismatch_amount != 0 else "Info.TLabel"
            ttk.Label(finalized_frame, text=f"Mismatch Amount: ₦{daily_entry.mismatch_amount:.2f}",
                      style=mismatch_color_style).grid(row=3, column=0, sticky="w", padx=5, pady=2)
            if daily_entry.deduction_amount > 0:
                ttk.Label(finalized_frame,
                          text=f"Deduction Applied: ₦{daily_entry.deduction_amount:.2f} from your salary.",
                          style="Warning.TLabel").grid(row=4, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(finalized_frame, text="You have completed your daily stock and cash declarations.",
                      style="SmallInfo.TLabel").grid(row=5, column=0, pady=5)

        ttk.Button(daily_stock_frame, text="Back to Dashboard", command=self.app.show_dashboard, style="TButton").grid(
            row=3, column=0, pady=20, ipadx=10, ipady=5)

    def save_daily_stock(self):
        """Saves the entered closing stock and calculates expected sales."""
        today = date.today()
        current_user = self.app.current_user
        daily_entry = db_session.query(DailyStockEntry).filter_by(manager_id=current_user.id, entry_date=today).first()
        inventory_items = db_session.query(InventoryItem).all()

        closing_stocks_data = {}
        for item_id, entry_widget in self.closing_stock_entries.items():
            try:
                closing_stock = int(entry_widget.get())
                if closing_stock < 0:
                    messagebox.showerror("Validation Error", f"Closing stock for item ID {item_id} cannot be negative.")
                    return
                closing_stocks_data[item_id] = closing_stock
            except ValueError:
                messagebox.showerror("Input Error",
                                     f"Invalid closing stock for item ID {item_id}. Please enter a number.")
                return

        calculated_total_sales_expected = 0.0
        item_sales_details = {}

        for item in inventory_items:
            current_item = db_session.query(InventoryItem).get(item.id)
            if not current_item: continue

            closing_stock = closing_stocks_data.get(current_item.id, current_item.closing_stock)

            quantity_sold = current_item.opening_stock + current_item.supply_qty - closing_stock
            if quantity_sold < 0:
                messagebox.showerror("Validation Error",
                                     f"Closing stock for {current_item.name} ({closing_stock}) is higher than available stock ({current_item.opening_stock + current_item.supply_qty}). Cannot proceed.")
                return

            item_sales_details[current_item.name] = {
                'opening_stock': current_item.opening_stock,
                'supply_qty': current_item.supply_qty,
                'closing_stock': closing_stock,
                'quantity_sold': quantity_sold,
                'price_per_unit': current_item.price_per_unit,
                'profit': quantity_sold * current_item.price_per_unit
            }
            calculated_total_sales_expected += (quantity_sold * current_item.price_per_unit)

            current_item.opening_stock = closing_stock
            current_item.closing_stock = closing_stock
            current_item.supply_qty = 0

        if not daily_entry:
            daily_entry = DailyStockEntry(manager_id=current_user.id, entry_date=today)
            db_session.add(daily_entry)
            log_action(current_user.username, current_user.role, 'Created Daily Stock Entry', new_value=f"Date:{today}")

        daily_entry.total_sales_expected = calculated_total_sales_expected
        daily_entry.item_sales_snapshot = json.dumps(item_sales_details)

        db_session.commit()
        messagebox.showinfo("Success", "Daily stock entry saved successfully. Now proceed to enter POS and Cash.")
        self.show_manager_daily_stock()

    def submit_pos_cash(self):
        """Submits the manager's POS and cash declaration, calculates mismatch, and applies deductions."""
        today = date.today()
        current_user = self.app.current_user

        daily_entry = db_session.query(DailyStockEntry).filter_by(manager_id=current_user.id, entry_date=today).first()
        if not daily_entry or not daily_entry.item_sales_snapshot:
            messagebox.showerror("Error", "Please save daily stock entries first.")
            return

        try:
            declared_cash = float(self.declared_cash_entry.get())
            declared_pos = float(self.declared_pos_entry.get())
            if declared_cash < 0 or declared_pos < 0:
                raise ValueError("Declared amounts cannot be negative.")
        except ValueError:
            messagebox.showerror("Input Error", "Declared Cash and POS must be numbers.")
            return

        staff_sales_today = db_session.query(StaffSaleEntry).filter(StaffSaleEntry.entry_date == today,
                                                                    StaffSaleEntry.is_submitted == True).all()
        total_system_sales_from_staff = sum(sale.total_cost for sale in staff_sales_today)

        if not messagebox.askyesno("Confirm Submission",
                                   "Are you sure you want to finalize today's POS and Cash declaration? This cannot be changed later."):
            return

        manager_cash_entry = db_session.query(CashRegisterEntry).filter_by(user_id=current_user.id,
                                                                           entry_date=today).first()
        if not manager_cash_entry:
            manager_cash_entry = CashRegisterEntry(user_id=current_user.id, entry_date=today)
            db_session.add(manager_cash_entry)

        total_declared = declared_cash + declared_pos
        manager_cash_entry.system_total_sales = total_system_sales_from_staff
        manager_cash_entry.declared_cash = declared_cash
        manager_cash_entry.declared_pos = declared_pos
        manager_cash_entry.is_finalized = True

        mismatch = total_declared - manager_cash_entry.system_total_sales
        deduction = 0.0

        if mismatch != 0:
            deduction = abs(mismatch)
            manager_cash_entry.mismatch_amount = mismatch
            manager_cash_entry.deduction_amount = deduction

            old_balance = current_user.current_salary_balance
            current_user.current_salary_balance -= deduction
            db_session.add(SalaryDeduction(
                user_id=current_user.id,
                amount=deduction,
                reason=f"Manager POS/Cash Mismatch for {today}. Expected: ₦{manager_cash_entry.system_total_sales:.2f}, Declared: ₦{total_declared:.2f}"
            ))
            messagebox.showwarning("Mismatch Detected",
                                   f"Mismatch: ₦{mismatch:.2f}. ₦{deduction:.2f} deducted from your salary.")
            log_action(current_user.username, current_user.role, 'Manager Cash/POS Mismatch Deduction',
                       old_value=f"Old Balance:{old_balance}",
                       new_value=f"New Balance:{current_user.current_salary_balance}, Deduction:{deduction}")
        else:
            messagebox.showinfo("Success", "POS and Cash balance tally. No deduction.")

        daily_entry.total_pos_cash_declared = total_declared
        daily_entry.mismatch_amount = mismatch
        daily_entry.deduction_amount = deduction
        daily_entry.is_finalized = True

        db_session.commit()
        self.app.dashboard_view.update_user_info_label()
        self.show_manager_daily_stock()

    def show_manager_reports(self):
        """Displays the manager's report generation panel."""
        self.clear_frame()
        reports_frame = ttk.Frame(self.master, padding="20", style="TFrame")
        reports_frame.pack(expand=True, fill="both")
        reports_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(reports_frame, text="Manager: Generate Reports", style="Header.TLabel").grid(row=0, column=0, pady=15)

        ttk.Label(reports_frame, text="Select Date for Report:", style="TLabel").grid(row=1, column=0, pady=5)
        self.report_date_entry = ttk.Entry(reports_frame, style="TEntry")
        self.report_date_entry.insert(0, date.today().strftime('%Y-%m-%d'))
        self.report_date_entry.grid(row=2, column=0, pady=5, ipady=2, sticky="ew", padx=100)
        ttk.Label(reports_frame, text="(Format:YYYY-MM-DD)", style="SmallInfo.TLabel").grid(row=3, column=0, pady=2)

        ttk.Button(reports_frame, text="Generate & Email Report", command=self.generate_and_email_report,
                   style="TButton").grid(row=4, column=0, pady=15, ipadx=10, ipady=5)

        ttk.Label(reports_frame, text="""
        Report Generation Notes:
        - Reports are generated in PDF format.
        - The generated report will be automatically emailed to 'paulwillie27@gmail.com'.
        - Important: You MUST configure your email sending credentials in this Python script (sender_email and sender_password variables) for email functionality to work.
        - The PDF report is saved locally temporarily and then deleted after emailing.
        """, justify="left", style="TLabel", wraplength=900).grid(row=5, column=0, pady=20, sticky="ew", padx=100)

        ttk.Button(reports_frame, text="Back to Dashboard", command=self.app.show_dashboard, style="TButton").grid(
            row=6, column=0,
            pady=20,
            ipadx=10,
            ipady=5)

    def generate_and_email_report(self):
        """Generates a PDF report for the selected date and attempts to email it."""
        report_date_str = self.report_date_entry.get()
        try:
            report_date_obj = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        daily_entry = db_session.query(DailyStockEntry).filter_by(entry_date=report_date_obj).first()
        staff_sales_for_day = db_session.query(StaffSaleEntry).filter_by(entry_date=report_date_obj).all()
        cash_register_entries_for_day = db_session.query(CashRegisterEntry).filter_by(entry_date=report_date_obj).all()
        salary_deductions_for_day = db_session.query(SalaryDeduction).filter(
            SalaryDeduction.deduction_date == report_date_obj,
            SalaryDeduction.user_id == self.app.current_user.id
        ).all()

        report_filename = f"Bar_Audit_Report_{report_date_str}.pdf"
        doc = SimpleDocTemplate(report_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<h2>Bar Audit Daily Report - {report_date_str}</h2>", styles['h2']))
        story.append(Spacer(1, 0.2 * 10))

        if daily_entry:
            story.append(Paragraph("<h3>Daily Stock Summary:</h3>", styles['h3']))
            data = [['Metric', 'Value']]
            data.append(['Expected Sales from Stock Movement', f"₦{daily_entry.total_sales_expected:.2f}"])
            data.append(['Declared POS + Cash', f"₦{daily_entry.total_pos_cash_declared:.2f}"])
            data.append(['Mismatch Amount', f"₦{daily_entry.mismatch_amount:.2f}"])
            data.append(['Deduction Amount', f"₦{daily_entry.deduction_amount:.2f}"])

            table = Table(data, colWidths=[200, 200])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2 * 10))

            if daily_entry.item_sales_snapshot:
                try:
                    item_sales_details = json.loads(daily_entry.item_sales_snapshot)
                    story.append(Paragraph("<h3>Inventory Movement:</h3>", styles['h3']))
                    item_data = [
                        ['Item Name', 'Opening Stock', 'Closing Stock', 'Qty Sold', 'Price/Unit', 'Total Sales']]
                    sorted_item_names = sorted(item_sales_details.keys())
                    for item_name in sorted_item_names:
                        details = item_sales_details[item_name]
                        item_data.append([
                            item_name,
                            details.get('opening_stock', 0),
                            details.get('closing_stock', 0),
                            details.get('quantity_sold', 0),
                            f"₦{details.get('price_per_unit', 0):.2f}",
                            f"₦{details.get('profit', 0):.2f}"
                        ])
                    item_table = Table(item_data, colWidths=[100, 80, 80, 60, 60, 80])
                    item_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(item_table)
                    story.append(Spacer(1, 0.2 * 10))
                except json.JSONDecodeError:
                    story.append(Paragraph("<i>Error loading item sales snapshot.</i>", styles['Normal']))
                    story.append(Spacer(1, 0.2 * 10))
        else:
            story.append(Paragraph(f"No Daily Stock Entry found for {report_date_str}.", styles['Normal']))
            story.append(Spacer(1, 0.2 * 10))

        if staff_sales_for_day:
            story.append(Paragraph("<h3>Staff Sales Entries:</h3>", styles['h3']))
            sales_data = [['Staff', 'Item', 'Quantity', 'Price/Unit', 'Total Cost']]
            sorted_staff_sales = sorted(staff_sales_for_day, key=lambda s: (
            db_session.query(User).get(s.staff_id).username if db_session.query(User).get(s.staff_id) else 'Unknown',
            s.item_name))
            for sale in sorted_staff_sales:
                staff_user = db_session.query(User).get(sale.staff_id)
                staff_name = staff_user.username if staff_user else 'Unknown'
                sales_data.append([
                    staff_name,
                    sale.item_name,
                    sale.quantity,
                    f"₦{sale.price_per_unit:.2f}",
                    f"₦{sale.total_cost:.2f}"
                ])
            sales_table = Table(sales_data, colWidths=[100, 100, 60, 80, 80])
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(sales_table)
            story.append(Spacer(1, 0.2 * 10))
        else:
            story.append(Paragraph(f"No Staff Sales Entries found for {report_date_str}.", styles['Normal']))
            story.append(Spacer(1, 0.2 * 10))

        if cash_register_entries_for_day:
            story.append(Paragraph("<h3>Cash Register Declarations:</h3>", styles['h3']))
            cash_data = [['User', 'Declared Cash', 'Declared POS', 'System Total', 'Mismatch', 'Deduction']]
            sorted_cash_entries = sorted(cash_register_entries_for_day, key=lambda c: (
                db_session.query(User).get(c.user_id).username if db_session.query(User).get(c.user_id) else 'Unknown'))
            for entry in sorted_cash_entries:
                declaring_user = db_session.query(User).get(entry.user_id)
                user_name = declaring_user.username if declaring_user else 'Unknown'
                cash_data.append([
                    user_name,
                    f"₦{entry.declared_cash:.2f}",
                    f"₦{entry.declared_pos:.2f}",
                    f"₦{entry.system_total_sales:.2f}",
                    f"₦{entry.mismatch_amount:.2f}",
                    f"₦{entry.deduction_amount:.2f}"
                ])
            cash_table = Table(cash_data, colWidths=[80, 80, 80, 80, 80, 80])
            cash_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(cash_table)
            story.append(Spacer(1, 0.2 * 10))
        else:
            story.append(Paragraph(f"No Cash Register Declarations found for {report_date_str}.", styles['Normal']))
            story.append(Spacer(1, 0.2 * 10))

        if salary_deductions_for_day:
            story.append(Paragraph("<h3>Salary Deductions (for Manager):</h3>", styles['h3']))
            deduction_data = [['Date', 'Amount', 'Reason']]
            for ded in salary_deductions_for_day:
                deduction_data.append([
                    ded.deduction_date.strftime('%Y-%m-%d'),
                    f"₦{ded.amount:.2f}",
                    ded.reason
                ])
            deduction_table = Table(deduction_data, colWidths=[80, 80, 200])
            deduction_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(deduction_table)
            story.append(Spacer(1, 0.2 * 10))
        else:
            story.append(Paragraph(f"No Salary Deductions for you on {report_date_str}.", styles['Normal']))
            story.append(Spacer(1, 0.2 * 10))

        try:
            doc.build(story)
            messagebox.showinfo("Report Generated", f"Report saved as {report_filename}")
            log_action(self.app.current_user.username, self.app.current_user.role, 'Generated Report',
                       new_value=report_filename)

            recipient_email = 'paulwillie27@gmail.com'
            sender_email = 'your_email@example.com'  # <--- IMPORTANT: CHANGE THIS TO YOUR SENDER EMAIL
            sender_password = 'your_email_password'  # <--- IMPORTANT: CHANGE THIS TO YOUR EMAIL PASSWORD
            smtp_server = 'smtp.gmail.com'
            smtp_port = 465

            if sender_email == 'your_email@example.com' or sender_password == 'your_email_password':
                messagebox.showwarning("Email Setup Required",
                                       "Email sending is not configured. Please edit the script to set your sender_email and sender_password variables, then try again.")
            else:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                msg['Subject'] = f"Bar Audit Daily Report - {report_date_str}"

                body = f"Dear recipient,\n\nPlease find attached the daily bar audit report for {report_date_str}.\n\nRegards,\nYour Bar Audit System"
                msg.attach(MIMEText(body, 'plain'))

                with open(report_filename, 'rb') as f:
                    attach = MIMEApplication(f.read(), _subtype="pdf")
                    attach.add_header('Content-Disposition', 'attachment', filename=str(report_filename))
                    msg.attach(attach)

                try:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                    server.quit()
                    messagebox.showinfo("Email Sent", f'Report emailed to {recipient_email} successfully!')
                    log_action(self.app.current_user.username, self.app.current_user.role, 'Emailed Report',
                               new_value=report_filename)
                except Exception as e:
                    messagebox.showwarning("Email Error",
                                           f"Error sending email: {e}.\n\nPlease check your email configuration (sender_email, sender_password, smtp_server, smtp_port) and internet connection.\nFor Gmail, you might need to enable 'App Passwords' in your Google Account security settings if 2-Step Verification is on.")
                    log_action(self.app.current_user.username, self.app.current_user.role, 'Failed to Email Report',
                               new_value=f"Error:{e}")

            if os.path.exists(report_filename):
                os.remove(report_filename)

        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report: {e}\n{traceback.format_exc()}")
            print(f"Error generating report: {traceback.format_exc()}")
            log_action(self.app.current_user.username, self.app.current_user.role, 'Report Generation Failed',
                       new_value=f"Error:{e}")
