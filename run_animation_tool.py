#!/usr/bin/env python3

"""
Animation Tool Launcher
A simple script to launch the animation tool from the project root
"""

import os
import sys
import importlib.util
import tkinter as tk
from tkinter import messagebox

def main():
    """Launch the animation tool"""
    # Get the absolute path to the animation tool directory
    animation_tool_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "p1_router", 
        "animation-tool"
    )
    
    # Add the animation tool directory to the Python path
    sys.path.append(os.path.dirname(animation_tool_dir))
    
    try:
        # Import the main window module
        spec = importlib.util.spec_from_file_location(
            "main_window", 
            os.path.join(animation_tool_dir, "ui", "main_window.py")
        )
        main_window = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_window)
        
        # Create the root window
        root = tk.Tk()
        root.title("P1 Router Animation Tool")
        
        # Create and start the application
        app = main_window.MainWindow(root)
        root.mainloop()
    except Exception as e:
        # Show error message
        print(f"Error launching animation tool: {e}")
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Animation Tool Error",
                f"An error occurred while launching the animation tool:\n\n{str(e)}"
            )
            root.destroy()
        except:
            pass
        
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 