#!/bin/bash
echo "Launching P1 Router Config Editor..."

if [ -f dist/P1RouterConfigEditor ]; then
    ./dist/P1RouterConfigEditor
else
    if [ -d venv ]; then
        source venv/bin/activate
        python config_editor_launcher.py
        deactivate
    else
        python3 config_editor_launcher.py
    fi
fi
