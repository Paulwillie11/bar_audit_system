# 🧾 Bar Audit & Inventory Management System

## 📌 Overview
A professional, desktop-based inventory and audit management system tailored for bar operations. This system empowers bar owners with complete visibility and control over stock flow, sales, and staff accountability. Designed with real-world Nigerian bar use-cases in mind, it tackles inefficiencies in stock handling, revenue tracking, and role-based operations.

---

## 🎯 Key Features

- **🔐 Role-Based Access Control**
  - Admin, Manager, and Staff access levels with permission-based views and actions

- **📊 Daily Inventory & Stock Management**
  - Tracks Opening, Supplied, and Closing stock daily
  - Automatically computes Sold quantity and Profit

- **🧾 Immutable Core Values**
  - Sold quantity, profit, and previous-day data cannot be edited post submission

- **🕵️‍♂️ Full Audit Logging**
  - All user actions (add/edit/delete) are logged with timestamp, action type, and username

- **📄 PDF Report Generation**
  - Generate structured daily or weekly reports for audit or review purposes

- **👥 Staff-Specific Record Keeping**
  - Each waiter/waitress has their own tab to record customer transactions

---

## 🧠 What I Built

- A complete GUI-based system using **Python + Tkinter**
- Embedded local database with **SQLite**
- PDF generation with **ReportLab**
- Auto-updating stock logic (Opening = Yesterday’s Closing)
- Real-time, per-session activity tracking
- Clean, professional UI built for usability in bar environments

---

## ⚙️ Tech Stack

| Layer        | Tools Used           |
|--------------|----------------------|
| GUI Frontend | Tkinter (Python)     |
| Database     | SQLite               |
| Reporting    | ReportLab (PDF)      |
| Packaging    | PyInstaller (.exe)   |

---

## 🔐 Access Control

| Feature                          | Admin | Manager | Staff |
|----------------------------------|-------|---------|-------|
| Add/Edit/Delete Users           | ✅    | ❌      | ❌    |
| Edit Cost Price                 | ✅    | ✅      | ❌    |
| Edit Closing Stock (Post Entry) | ✅    | ❌      | ❌    |
| View Reports                    | ✅    | ✅      | ✅    |
| View Logs                       | ✅    | ❌      | ❌    |

---

## 📸 Screenshots

> *[Insert screenshots of login page, stock entry form, audit logs, and PDF report here]*

---

## 🔍 Real-World Impact

- Built for Nigerian bar environments with limited digital tools
- Replaces manual entry books with a transparent, auditable system
- Prevents stock loss, theft, and misreporting
- Currently in use by real bar owners for daily inventory operations

---

## 📈 Next Improvements

- 🌐 Web-based version using Django or Flask
- ☁️ Cloud backup and synchronization
- 📱 SMS/Email alerts for irregular entries
- 📊 Analytics dashboard for trends and forecasting

---

## 📥 Run the Project

> Prerequisites:
- Python 3.8+
- Tkinter
- SQLite (bundled with Python)
- ReportLab

```bash
pip install reportlab
python main.py
