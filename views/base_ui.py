import tkinter as tk
from tkinter import ttk

class BaseUI:
    def __init__(self, master, app_instance):
        self.master = master
        self.app = app_instance # Reference to the main BarAuditApp instance

    def clear_frame(self):
        """Clears all widgets from the current frame."""
        for widget in self.master.winfo_children():
            widget.destroy()

    def setup_styles(self):
        """Configures the modern theme and styles for ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')

        # Define a professional color palette
        COLOR_PRIMARY = "#3498db"
        COLOR_ACCENT = "#2980b9"
        COLOR_BACKGROUND = "#f4f7f6"
        COLOR_HEADER_BG = "#2c3e50"
        COLOR_TEXT_DARK = "#34495e"
        COLOR_TEXT_LIGHT = "#ffffff"
        COLOR_SUCCESS = "#28a745"
        COLOR_DANGER = "#dc3545"
        COLOR_LIGHT_GREY = "#e0e0e0"

        # General frame style for background consistency
        style.configure("TFrame", background=COLOR_BACKGROUND)
        style.configure("TLabelFrame", background=COLOR_BACKGROUND, borderwidth=1, relief="flat",
                        foreground=COLOR_TEXT_DARK, font=('Inter', 10, 'bold'))
        style.configure("TLabelframe.Label", background=COLOR_BACKGROUND, foreground=COLOR_TEXT_DARK)

        # Label styles
        style.configure("TLabel", background=COLOR_BACKGROUND, font=('Inter', 9), foreground=COLOR_TEXT_DARK)
        style.configure("Header.TLabel", font=('Inter', 18, 'bold'), foreground=COLOR_HEADER_BG, background=COLOR_BACKGROUND)
        style.configure("SubHeader.TLabel", font=('Inter', 12, 'bold'), foreground=COLOR_TEXT_DARK, background=COLOR_BACKGROUND)
        style.configure("SectionHeader.TLabel", font=('Inter', 11, 'bold'), foreground=COLOR_TEXT_DARK, background=COLOR_BACKGROUND)
        style.configure("Info.TLabel", font=('Inter', 11, 'bold'), foreground=COLOR_SUCCESS, background=COLOR_BACKGROUND)
        style.configure("Warning.TLabel", font=('Inter', 11, 'bold'), foreground=COLOR_DANGER, background=COLOR_BACKGROUND)
        style.configure("SmallInfo.TLabel", font=('Inter', 8), foreground=COLOR_TEXT_DARK, background=COLOR_BACKGROUND)

        # Button styles
        style.configure("TButton", font=('Inter', 10, 'bold'), padding=8,
                        background=COLOR_PRIMARY, foreground=COLOR_TEXT_LIGHT,
                        borderwidth=0, relief="flat", focusthickness=3, focuscolor=COLOR_ACCENT)
        style.map("TButton",
                  background=[('active', COLOR_ACCENT), ('pressed', COLOR_ACCENT)],
                  foreground=[('active', COLOR_TEXT_LIGHT), ('pressed', COLOR_TEXT_LIGHT)])
        style.configure("Danger.TButton", font=('Inter', 10, 'bold'), padding=8,
                        background=COLOR_DANGER, foreground=COLOR_TEXT_LIGHT,
                        borderwidth=0, relief="flat", focusthickness=3, focuscolor=COLOR_ACCENT)
        style.map("Danger.TButton",
                  background=[('active', '#c0392b'), ('pressed', '#c0392b')],
                  foreground=[('active', COLOR_TEXT_LIGHT), ('pressed', COLOR_TEXT_LIGHT)])

        # Entry and Combobox styles
        style.configure("TEntry", font=('Inter', 10), padding=5, fieldbackground=COLOR_TEXT_LIGHT,
                        foreground=COLOR_TEXT_DARK, borderwidth=1, relief="solid")
        style.configure("TCombobox", font=('Inter', 10), padding=5, fieldbackground=COLOR_TEXT_LIGHT,
                        foreground=COLOR_TEXT_DARK, borderwidth=1, relief="solid")
        style.map('TCombobox', fieldbackground=[('readonly', COLOR_TEXT_LIGHT)],
                  selectbackground=[('readonly', COLOR_TEXT_LIGHT)],
                  selectforeground=[('readonly', COLOR_TEXT_DARK)])

        # Treeview styles
        style.configure("Treeview.Heading", font=('Inter', 10, 'bold'), background=COLOR_LIGHT_GREY, foreground=COLOR_TEXT_DARK,
                        relief="raised", padding=[5,5,5,5])
        style.configure("Treeview", background=COLOR_TEXT_LIGHT, fieldbackground=COLOR_TEXT_LIGHT,
                        foreground=COLOR_TEXT_DARK, font=('Inter', 9), rowheight=28, borderwidth=1,
                        relief="solid")
        style.map('Treeview', background=[('selected', '#a8d8ff')])

        # Scrollbar styles for Treeview, making them match the theme
        style.configure("Vertical.TScrollbar", background=COLOR_LIGHT_GREY, troughcolor=COLOR_BACKGROUND,
                        bordercolor=COLOR_LIGHT_GREY, arrowcolor=COLOR_TEXT_DARK)
        style.map("Vertical.TScrollbar",
                  background=[('active', COLOR_ACCENT)])

        # Checkbutton style
        style.configure("TCheckbutton", background=COLOR_BACKGROUND, font=('Inter', 9),
                        foreground=COLOR_TEXT_DARK)
