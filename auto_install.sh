#!/bin/bash

echo "==================================================="
echo "P1 Router - Automatic Installer and Builder"
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
echo "Creating virtual environment..."
python3 -m pip install --upgrade pip
python3 -m pip install virtualenv
python3 -m virtualenv venv

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo
echo "Installing required packages in virtual environment..."
pip install -r p1_router/requirements.txt
pip install pillow opencv-python pyinstaller

echo
echo "Building executable from virtual environment..."
python build_exe.py

echo
echo "Deactivating virtual environment..."
deactivate

echo
echo "Installation completed!"
echo "You can now run the P1 Router application using:"
echo "  1. The executable in the dist directory"
echo "  2. Or by running 'python3 launcher.py'"
echo

# Create a launcher script
cat > run_p1_router.sh << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
if [ -f dist/P1Router ]; then
  ./dist/P1Router
else
  # Try to use the virtual environment if it exists
  if [ -d venv ]; then
    source venv/bin/activate
    python launcher.py
    deactivate
  else
    python3 launcher.py
  fi
fi
EOF

chmod +x run_p1_router.sh

echo "A launcher script 'run_p1_router.sh' has been created."
echo "You can run it with: ./run_p1_router.sh"
echo 