#!/usr/bin/env python3

"""
Animation Tool Launcher
A launcher script for the P1 Router Animation Tool
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox


def main():
    """Launch the Animation Tool"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level if in download-and-launch
    
    # Try different path configurations to handle various install scenarios
    animation_tool_paths = [
        os.path.join(project_root, "animation-tool"),
        os.path.join(project_root, "p1_router", "animation-tool"),
        os.path.join(project_root, "p1_router")
    ]
    
    # Add all potential paths to sys.path
    for path in animation_tool_paths:
        if os.path.exists(path):
            print(f"Adding path: {path}")
            sys.path.insert(0, path)
    
    # Also add project root
    sys.path.insert(0, project_root)
    
    print(f"Python path: {sys.path}")
    
    # Try to import the animation tool main window
    try:
        # Try various import paths
        try:
            print("Attempting to import from ui.main_window...")
            from ui.main_window import MainWindow
            print("Import successful!")
        except ImportError as e1:
            print(f"First import attempt failed: {e1}")
            try:
                print("Attempting to import from p1_router.animation-tool.ui.main_window...")
                from p1_router.animation_tool.ui.main_window import MainWindow
                print("Import successful!")
            except ImportError as e2:
                print(f"Second import attempt failed: {e2}")
                
                # One last attempt - check for animation-tool with underscores
                animation_tool_alt_paths = [
                    os.path.join(project_root, "animation_tool"),
                    os.path.join(project_root, "p1_router", "animation_tool"),
                ]
                
                for path in animation_tool_alt_paths:
                    if os.path.exists(path):
                        print(f"Adding alternate path: {path}")
                        sys.path.insert(0, path)
                
                try:
                    print("Final attempt to import...")
                    from ui.main_window import MainWindow
                    print("Import successful!")
                except ImportError as e3:
                    # Create a more detailed error message
                    error_msg = f"All import attempts failed:\n{e1}\n{e2}\n{e3}"
                    print(error_msg)
                    raise ImportError(error_msg)
        
        # Create the root window
        root = tk.Tk()
        root.title("P1 Router Animation Tool")
        
        # Create the application
        print("Creating application...")
        app = MainWindow(root)
        
        # Start the application
        print("Starting application...")
        root.mainloop()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        # Display error message
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        messagebox.showerror(
            "Animation Tool Error",
            f"Could not import animation tool modules.\n\n"
            f"Please make sure the animation tool is correctly installed.\n\n"
            f"Error details: {str(e)}\n\n"
            f"Paths checked: {animation_tool_paths}"
        )
        root.destroy()
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        # Display error message
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        messagebox.showerror(
            "Animation Tool Error",
            f"An error occurred while launching the animation tool:\n\n{str(e)}"
        )
        root.destroy()
        sys.exit(1)

if __name__ == "__main__":
    main() 