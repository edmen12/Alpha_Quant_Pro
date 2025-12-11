
import multiprocessing
import sys
import os
import customtkinter as ctk

# Ensure multiprocessing support for PyInstaller
multiprocessing.freeze_support()

# Import the binary module (terminal_apple.pyd)
try:
    import terminal_apple
except ImportError as e:
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.withdraw()
    from tkinter import messagebox
    messagebox.showerror("Fatal Error", f"Core Binary Missing: {e}")
    sys.exit(1)

if __name__ == "__main__":
    terminal_apple.main()
