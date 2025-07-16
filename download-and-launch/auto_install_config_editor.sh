#!/bin/bash

echo "==================================================="
echo "P1 Router Config Editor - Automatic Installer"
echo "==================================================="
echo

echo "Checking for Python installation..."
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed."
    echo "Please install Python 3.6+ and try again."
    echo "You can download Python from https://www.python.org/downloads/"
    exit 1
fi

echo "Python found. Checking version..."
python3 --version

echo
echo "Creating virtual environment for Config Editor..."
python3 -m pip install --upgrade pip
python3 -m pip install virtualenv
python3 -m virtualenv venv_config

echo
echo "Activating virtual environment..."
source venv_config/bin/activate

echo
echo "Installing required packages for Config Editor..."
pip install -r p1_router/requirements.txt
pip install pyinstaller

echo
echo "Building Config Editor executable..."
python build_config_editor_exe.py

echo
echo "Deactivating virtual environment..."
deactivate

echo
echo "Installation completed!"
echo "You can now run the Config Editor using:"
echo "  1. ./launch_config_editor.sh"
echo "  2. Or directly with dist/P1RouterConfigEditor"
echo

# Make the launch script executable
chmod +x launch_config_editor.sh

echo "Launch script has been made executable." 