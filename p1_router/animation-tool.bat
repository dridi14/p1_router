@echo off
echo Starting P1 Router Animation Tool...
python download-and-launch/animation_tool_launcher.py
if %ERRORLEVEL% neq 0 (
  echo Animation Tool failed to start
  echo Error code: %ERRORLEVEL%
  pause
) 