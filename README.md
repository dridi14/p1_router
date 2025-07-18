# P1 Router Application

## Overview
P1 Router is a lighting control application that serves as a bridge between eHuB messages (from Unity or similar systems) and physical lighting controllers using ArtNet protocol. It provides efficient routing, mapping, and monitoring capabilities for lighting installations of any scale.

## Features
- eHuB Protocol listener and parser
- Entity-to-Controller mapping
- Efficient ArtNet routing
- DMX output monitoring
- Configuration management
- Network load control
- Patching system
- Testing interfaces with image and video support

## Installation

### Option 1: Automatic Installation with Virtual Environment (Recommended)
1. Run the appropriate installer script for your platform:
   - **Windows**: Run `auto_install.bat`
   - **Linux/macOS**: Run `./auto_install.sh` (make executable first with `chmod +x auto_install.sh`)

   The script will:
   - Check for Python installation
   - Create a virtual environment
   - Install all required dependencies
   - Build the executable
   - Create launcher scripts

2. After installation, run the application using:
   - **Windows**: `Launch_P1_Router.bat`
   - **Linux/macOS**: `./run_p1_router.sh`

### Option 2: Manual Installation with Virtual Environment
1. Create a virtual environment:
   ```
   # Windows
   python -m pip install virtualenv
   python -m virtualenv venv
   venv\Scripts\activate
   
   # Linux/macOS
   python3 -m pip install virtualenv
   python3 -m virtualenv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r p1_router/requirements.txt
   pip install pillow opencv-python
   ```

3. Run the launcher:
   ```
   python launcher.py
   ```

4. Optionally, build the executable:
   ```
   pip install pyinstaller
   python build_exe.py
   ```

### Option 3: Direct Installation (Not Recommended)
If you prefer not to use a virtual environment (not recommended due to potential conflicts):
1. Install dependencies:
   ```
   pip install -r p1_router/requirements.txt
   pip install pillow opencv-python
   ```

2. Run the launcher:
   ```
   python launcher.py
   ```

## Usage

The P1 Router Control Panel provides the following functionality:

### Main Router
- Start/Stop the main routing engine that listens for eHuB messages and sends ArtNet commands

### eHuB Listener
- Start/Stop the basic eHuB listener to capture and save messages

### Testing Interfaces
- Basic Tester: Launch a graphical interface for testing entity mapping and colors
- Advanced Tester: Launch an enhanced interface with video playback support

### Controls
- Start All: Start both the router and listener
- Stop All: Stop all running components
- Exit: Clean up and exit the application

## Configuration

The system is configured through `p1_router/config/config.json` which maps entity IDs to controllers, universes, and channels.

Example configuration format:
```json
[
  {
    "from": 100,
    "to": 269,
    "ip": "192.168.1.45",
    "universe": 0
  }
]
```

## Development

To set up the development environment:

1. Create and activate a virtual environment:
   ```
   # Windows
   python -m virtualenv venv
   venv\Scripts\activate
   
   # Linux/macOS
   python3 -m virtualenv venv
   source venv/bin/activate
   ```

2. Install the package in development mode:
   ```
   pip install -e .
   ```

3. Run tests:
   ```
   python -m p1_router.tester
   ```

## Requirements
- Python 3.6+
- Pillow
- OpenCV (for video playback)
- NumPy

## License
Proprietary - All rights reserved. 