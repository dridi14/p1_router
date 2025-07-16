#!/usr/bin/env python3

"""
Build script for the P1 Router Config Editor executable.
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def check_virtual_env():
    """Check if running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def prepare_config():
    """Make sure config file is in the right location"""
    print("Preparing configuration file...")
    # Ensure ./config directory exists
    if not os.path.exists("config"):
        os.makedirs("config", exist_ok=True)
    
    # Copy config from p1_router/config if it exists
    source_config = os.path.join("p1_router", "config", "config.json")
    target_config = os.path.join("config", "config.json")
    
    if os.path.exists(source_config) and not os.path.exists(target_config):
        shutil.copy(source_config, target_config)
        print(f"Copied config from {source_config} to {target_config}")
    
    # If no config exists, create a minimal one
    if not os.path.exists(target_config):
        print("Creating default config.json")
        minimal_config = """[
  {
    "from": 100,
    "to": 269,
    "ip": "192.168.1.45",
    "universe": 0
  }
]"""
        with open(target_config, "w") as f:
            f.write(minimal_config)
    
    print("Configuration ready")
    return os.path.exists(target_config)

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    
    # Minimum requirements for the config editor
    requirements = ["pyinstaller"]
    
    if not check_virtual_env():
        print("Warning: Not running in a virtual environment!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborting. Please run this script from a virtual environment.")
            sys.exit(1)
    
    # Install base requirements from the project
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "p1_router/requirements.txt"])
    except:
        print("Warning: Could not install from requirements.txt, installing minimal dependencies...")
    
    # Install PyInstaller for packaging
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + requirements)
    print("All dependencies installed successfully.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building Config Editor executable with PyInstaller...")
    
    # Create PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=P1RouterConfigEditor",
        "--onefile",
        "--windowed",
        "--add-data=config/config.json;config/",  # Add the config in the correct location
        "--add-data=p1_router/config/config.json;p1_router/config/",  # Also include original for backup
        "config_editor_launcher.py"
    ]
    
    # Execute PyInstaller
    subprocess.check_call(pyinstaller_cmd)
    print("Config Editor executable build complete.")

def create_shortcut():
    """Create shortcut for easy access"""
    print("Creating shortcut...")
    
    with open("Launch_Config_Editor.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Launching P1 Router Config Editor...\n\n")
        f.write("IF EXIST dist\\P1RouterConfigEditor.exe (\n")
        f.write("    start dist\\P1RouterConfigEditor.exe\n")
        f.write(") ELSE (\n")
        f.write("    IF EXIST venv\\Scripts\\activate.bat (\n")
        f.write("        call venv\\Scripts\\activate.bat\n")
        f.write("        python config_editor_launcher.py\n")
        f.write("        call deactivate\n")
        f.write("    ) ELSE (\n")
        f.write("        python config_editor_launcher.py\n")
        f.write("    )\n")
        f.write(")\n")
    
    # For Linux/macOS users
    with open("launch_config_editor.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo \"Launching P1 Router Config Editor...\"\n\n")
        f.write("if [ -f dist/P1RouterConfigEditor ]; then\n")
        f.write("    ./dist/P1RouterConfigEditor\n")
        f.write("else\n")
        f.write("    if [ -d venv ]; then\n")
        f.write("        source venv/bin/activate\n")
        f.write("        python config_editor_launcher.py\n")
        f.write("        deactivate\n")
        f.write("    else\n")
        f.write("        python3 config_editor_launcher.py\n")
        f.write("    fi\n")
        f.write("fi\n")
    
    # Make shell script executable on Unix-like systems
    try:
        os.chmod("launch_config_editor.sh", 0o755)
    except:
        pass
        
    print("Shortcuts created.")

def clean_build_files():
    """Clean up temporary build files"""
    print("Cleaning up build files...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("P1RouterConfigEditor.spec"):
        os.remove("P1RouterConfigEditor.spec")
    print("Cleanup complete.")

def main():
    """Main build process"""
    print("=== P1 Router Config Editor - Executable Builder ===")
    
    try:
        # Check virtual environment
        if check_virtual_env():
            print(f"Using virtual environment: {sys.prefix}")
        else:
            print("Warning: Not running in a virtual environment")
        
        # Prepare config file in the correct location
        if not prepare_config():
            print("ERROR: Could not prepare config file")
            return 1
        
        # Install dependencies
        install_requirements()
        
        # Build the executable
        build_executable()
        
        # Create shortcuts
        create_shortcut()
        
        # Clean up temporary files
        clean_build_files()
        
        print("\nBuild successful! Config Editor executable is located in the 'dist' folder.")
        print("You can run the application using:")
        print("  - Windows: Launch_Config_Editor.bat or dist\\P1RouterConfigEditor.exe")
        print("  - Linux/macOS: ./launch_config_editor.sh")
        
    except Exception as e:
        print(f"Error during build process: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 