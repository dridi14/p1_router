#!/usr/bin/env python3

"""
Animation Tool Launcher
This script launches the Animation Tool for the P1 Router project.
It can be called from the main application or run directly.
"""

import os
import sys
import tkinter as tk

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main window class
from ui.main_window import MainWindow


def main():
    """Launch the animation tool"""
    print("Launching P1 Router Animation Tool...")
    
    # Create the root window
    root = tk.Tk()
    
    try:
        # Create and start the application
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print(f"Error launching animation tool: {e}")
        traceback.print_exc()
        
        # Show error in a message box if the window system is ready
        if 'root' in locals() and root.winfo_exists():
            from tkinter import messagebox
            messagebox.showerror("Error", f"An error occurred launching the animation tool:\n\n{e}")
        
        # Exit with error code
        sys.exit(1)


if __name__ == "__main__":
    main() 