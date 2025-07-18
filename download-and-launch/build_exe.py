import os
import subprocess
import sys
import shutil
from pathlib import Path

def check_virtual_env():
    """Check if running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def install_requirements():
    """Install required packages for the application"""
    print("Installing required packages...")
    
    if not check_virtual_env():
        print("Warning: Not running in a virtual environment!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborting. Please run this script from a virtual environment.")
            sys.exit(1)
    
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "p1_router/requirements.txt"])
    # Additional requirements for advanced features
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "opencv-python", "pyinstaller"])
    print("All dependencies installed successfully.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable with PyInstaller...")
    
    # Add data files from current environment
    if check_virtual_env():
        site_packages = os.path.join(sys.prefix, "lib", "site-packages")
        if not os.path.exists(site_packages):  # For Windows
            site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
    
    # Create PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=P1Router",
        "--onefile",
        "--windowed",
        "--add-data=p1_router/config/config.json;p1_router/config/",
        "--add-data=p1_router/ehub_sample.bin;p1_router/",
        "--add-data=p1_router/ehub_sample1.bin;p1_router/",
        "launcher.py"
    ]
    
    # Execute PyInstaller
    subprocess.check_call(pyinstaller_cmd)
    print("Executable build complete.")

def create_shortcuts():
    """Create shortcuts for easy access"""
    print("Creating shortcuts...")
    # This would require platform-specific code
    # For Windows, could use a batch file or PowerShell
    
    with open("Launch_P1_Router.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Launching P1 Router...\n\n")
        f.write("IF EXIST dist\\P1Router.exe (\n")
        f.write("    start dist\\P1Router.exe\n")
        f.write(") ELSE (\n")
        f.write("    IF EXIST venv\\Scripts\\activate.bat (\n")
        f.write("        call venv\\Scripts\\activate.bat\n")
        f.write("        python launcher.py\n")
        f.write("        call deactivate\n")
        f.write("    ) ELSE (\n")
        f.write("        python launcher.py\n")
        f.write("    )\n")
        f.write(")\n")
    
    print("Shortcuts created.")

def clean_build_files():
    """Clean up temporary build files"""
    print("Cleaning up build files...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("P1Router.spec"):
        os.remove("P1Router.spec")
    print("Cleanup complete.")

def main():
    """Main build process"""
    print("=== P1 Router Executable Builder ===")
    
    try:
        # Check if running in virtual environment
        if check_virtual_env():
            print(f"Using virtual environment: {sys.prefix}")
        else:
            print("Warning: Not running in a virtual environment")
        
        # Install dependencies
        install_requirements()
        
        # Build the executable
        build_executable()
        
        # Create shortcuts
        create_shortcuts()
        
        # Clean up temporary files
        clean_build_files()
        
        print("\nBuild successful! Executable is located in the 'dist' folder.")
        print("You can run the application using the Launch_P1_Router.bat file or directly from dist/P1Router.exe")
        
    except Exception as e:
        print(f"Error during build process: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 