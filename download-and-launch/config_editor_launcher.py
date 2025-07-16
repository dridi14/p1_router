#!/usr/bin/env python3

"""
Simple launcher for the P1 Router Config Editor.
This script launches the existing configuration editor interface.
"""

import sys
import os
import subprocess
import shutil
import json

def ensure_config_exists():
    """Make sure config.json exists in the expected location"""
    # Check for config file in expected location
    config_dir = os.path.join(os.getcwd(), "p1_router", "config")
    target_config = os.path.join(config_dir, "config.json")
    
    if not os.path.isdir("config"):
        os.makedirs("config", exist_ok=True)
    
    # If config doesn't exist in ./config/ but exists in p1_router/config/, copy it
    if not os.path.exists("config/config.json") and os.path.exists(target_config):
        print(f"Copying config from {target_config} to ./config/config.json")
        try:
            # Try to copy the full config file (which might be large)
            with open(target_config, 'r') as source:
                config_data = json.load(source)
            
            with open("config/config.json", 'w') as dest:
                json.dump(config_data, dest, indent=2)
            
            print(f"Successfully copied complete config with {len(config_data)} entries")
        except Exception as e:
            print(f"Error copying config: {e}. Will create minimal config instead.")
            shutil.copy(target_config, "config/config.json")
    
    # If still no config, create a minimal one
    if not os.path.exists("config/config.json"):
        print("Creating default config.json file")
        minimal_config = """[
  {
    "from": 100,
    "to": 269,
    "ip": "192.168.1.45",
    "universe": 0
  }
]"""
        with open("config/config.json", "w") as f:
            f.write(minimal_config)
    
    return os.path.exists("config/config.json")

def launch_config_editor():
    """Launch the configuration editor directly"""
    # First ensure we have a config file in the right place
    if not ensure_config_exists():
        print("ERROR: Could not create or find config.json")
        return False
    
    try:
        # Try to import and run the config editor directly
        print("Launching P1 Router Config Editor...")
        
        # Add the p1_router directory to Python path to allow imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "p1_router"))
        
        # Modify the config path in the editor before importing
        # This is a bit of a hack but works for direct imports
        import p1_router.config_editor
        p1_router.config_editor.CONFIG_PATH = "config/config.json"
        
        # Import and run the editor
        from p1_router.config_editor import ConfigEditor
        app = ConfigEditor()
        app.mainloop()
        
    except ImportError as e:
        print(f"Import error: {e}")
        # If direct import fails, try running as subprocess
        print("Launching Config Editor as subprocess...")
        try:
            # Create a small temporary wrapper script to fix the path
            with open("_temp_config_editor.py", "w") as f:
                f.write("""
import os
import sys
import json
import shutil

sys.path.insert(0, ".")  # Add current dir to path

# Ensure config directory and file exist
if not os.path.isdir("config"):
    os.makedirs("config", exist_ok=True)

# Copy config from p1_router if needed
if not os.path.exists("config/config.json"):
    source_config = os.path.join("p1_router", "config", "config.json")
    if os.path.exists(source_config):
        shutil.copy(source_config, "config/config.json")
        print(f"Copied config from {source_config}")

# Override the config path
from p1_router.config_editor import CONFIG_PATH, ConfigEditor
import p1_router.config_editor
p1_router.config_editor.CONFIG_PATH = "config/config.json"

if __name__ == "__main__":
    app = ConfigEditor()
    app.mainloop()
""")
            
            subprocess.run([sys.executable, "_temp_config_editor.py"])
            # Clean up
            if os.path.exists("_temp_config_editor.py"):
                os.unlink("_temp_config_editor.py")
                
        except Exception as e:
            print(f"Error launching Config Editor: {e}")
            return False
            
    return True

if __name__ == "__main__":
    launch_config_editor() 