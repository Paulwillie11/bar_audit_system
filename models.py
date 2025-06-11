from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Import Base from your database module
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)  # 'Admin', 'Manager', 'Staff'
    monthly_salary = Column(Float, default=0.0)
    current_salary_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    # Relationships (for SQLAlchemy: backref creates a reverse relationship on the other side)
    stock_entries = relationship('DailyStockEntry', backref='manager', lazy=True, cascade="all, delete-orphan")
    staff_sales = relationship('StaffSaleEntry', backref='staff', lazy=True, cascade="all, delete-orphan")
    cash_registers = relationship('CashRegisterEntry', backref='user', lazy=True, cascade="all, delete-orphan")
    salary_deductions = relationship('SalaryDeduction', backref='user_rel', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    supply_qty = Column(Integer, default=0)
    opening_stock = Column(Integer, default=0)
    closing_stock = Column(Integer, default=0)
    price_per_unit = Column(Float, default=0.0)
    date_recorded = Column(Date, nullable=False, default=date.today)

    def __repr__(self):
        return f"<InventoryItem {self.name}>"


class DailyStockEntry(Base):
    __tablename__ = 'daily_stock_entries'
    id = Column(Integer, primary_key=True)
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    entry_date = Column(Date, nullable=False, default=date.today, unique=True)
    total_sales_expected = Column(Float, default=0.0)
    total_pos_cash_declared = Column(Float, default=0.0)
    mismatch_amount = Column(Float, default=0.0)
    deduction_amount = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_finalized = Column(Boolean, default=False)
    item_sales_snapshot = Column(String)  # Storing JSON string of item sales details

    def __repr__(self):
        return f"<DailyStockEntry {self.entry_date} by {self.manager_id}>"


class StaffSaleEntry(Base):
    __tablename__ = 'staff_sale_entries'
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    entry_date = Column(Date, nullable=False, default=date.today)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_submitted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<StaffSaleEntry {self.item_name} x{self.quantity} by {self.staff_id} on {self.entry_date}>"


class CashRegisterEntry(Base):
    __tablename__ = 'cash_register_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    entry_date = Column(Date, nullable=False, default=date.today)
    declared_cash = Column(Float, default=0.0)
    declared_pos = Column(Float, default=0.0)
    system_total_sales = Column(Float, default=0.0)
    mismatch_amount = Column(Float, default=0.0)
    deduction_amount = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_finalized = Column(Boolean, default=False)

    def __repr__(self):
        return f"<CashRegisterEntry {self.user_id} on {self.entry_date}>"


class SalaryDeduction(Base):
    __tablename__ = 'salary_deductions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    deduction_date = Column(Date, nullable=False, default=date.today)
    amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', backref='user_deductions_rel', lazy=True) # Renamed backref for clarity, backref='user_rel' already exists on User side.

    def __repr__(self):
        return f"<SalaryDeduction {self.amount} for {self.user_id} on {self.deduction_date}>"


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    user_role = Column(String(20), nullable=False)
    action_type = Column(String(100), nullable=False)
    old_value = Column(String)
    new_value = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action_type} by {self.username} at {self.timestamp}>"
