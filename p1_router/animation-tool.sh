#!/bin/bash
echo "Starting P1 Router Animation Tool..."
python3 download-and-launch/animation_tool_launcher.py
if [ $? -ne 0 ]; then
  echo "Animation Tool failed to start"
  echo "Error code: $?"
  read -p "Press [Enter] to continue..."
fi 