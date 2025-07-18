# P1 Router Config Editor

## Overview
This is a standalone launcher for the P1 Router Config Editor. It allows you to edit the configuration file for the P1 Router application without starting the entire application.

## Features
- Edit entity mapping (Universe, IP, ID ranges)
- Import/export configurations from CSV
- Validate configuration
- Launch the main router or tester directly from the editor

## Installation

### Option 1: Automatic Installation (Recommended)
1. Run the appropriate installer script for your platform:
   - **Windows**: Run `auto_install_config_editor.bat`
   - **Linux/macOS**: Run `./auto_install_config_editor.sh` (make it executable first with `chmod +x auto_install_config_editor.sh`)

   The script will:
   - Check for Python installation
   - Create a virtual environment
   - Install required dependencies
   - Build the executable
   - Create launcher scripts

2. After installation, run the Config Editor using:
   - **Windows**: `Launch_Config_Editor.bat` or `dist\P1RouterConfigEditor.exe`
   - **Linux/macOS**: `./launch_config_editor.sh`

### Option 2: Manual Installation
1. Make sure Python 3.6+ is installed
2. Install the requirements:
   ```
   pip install -r p1_router/requirements.txt
   ```
3. Run the Config Editor directly:
   ```
   python config_editor_launcher.py
   ```

## Usage

The Config Editor provides the following functionality:

- **View/Edit Configuration**: Double-click on fields to edit values
- **Add Line**: Add a new mapping entry
- **Delete Selected**: Remove the selected mapping entry
- **Import/Export CSV**: Import or export the configuration as CSV
- **Save Config**: Save changes to the config.json file
- **Run Main**: Launch the main router with the current configuration
- **Run Tester**: Launch the tester with the current configuration

## Configuration Format

The configuration defines how entity IDs map to universes and IP addresses:

```json
[
  {
    "from": 100,
    "to": 269,
    "ip": "192.168.1.45",
    "universe": 0
  },
  {
    "from": 270,
    "to": 358,
    "ip": "192.168.1.45",
    "universe": 1
  }
]
```

Each entry maps a range of entity IDs (`from`-`to`) to a specific ArtNet universe at a target IP address. 