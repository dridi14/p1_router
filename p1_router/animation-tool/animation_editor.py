#!/usr/bin/env python3

"""
Animation Editor for P1 Router
Main entry point for the LED wall animation tool
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from .core.canvas import AnimationCanvas
from .ui.main_window import MainWindow


def main():
    """Main entry point for the animation tool"""
    root = tk.Tk()
    root.title("P1 Router Animation Tool")
    
    try:
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main() 