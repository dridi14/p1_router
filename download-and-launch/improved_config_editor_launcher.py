#!/usr/bin/env python3

"""
Launcher for the Improved P1 Router Config Editor
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

def launch_improved_editor():
    """Launch the improved configuration editor"""
    # First ensure we have a config file in the right place
    if not ensure_config_exists():
        print("ERROR: Could not create or find config.json")
        return False
    
    try:
        # Try to run the improved editor directly
        print("Launching Improved P1 Router Config Editor...")
        
        # Run the improved editor script
        import improved_config_editor
        app = improved_config_editor.ImprovedConfigEditor()
        app.mainloop()
        
    except ImportError as e:
        print(f"Import error: {e}")
        # If direct import fails, try running as subprocess
        print("Launching as subprocess...")
        try:
            subprocess.run([sys.executable, "improved_config_editor.py"])
        except Exception as e:
            print(f"Error launching Improved Config Editor: {e}")
            return False
            
    return True

if __name__ == "__main__":
    launch_improved_editor() 