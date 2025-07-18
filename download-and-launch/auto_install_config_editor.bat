@echo off
echo ===================================================
echo P1 Router Config Editor - Automatic Installer
echo ===================================================
echo.

echo Checking for Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.6+ and try again.
    echo You can download Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found. Checking version...
python --version

echo.
echo Creating virtual environment for Config Editor...
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m virtualenv venv_config

echo.
echo Activating virtual environment...
call venv_config\Scripts\activate.bat

echo.
echo Installing required packages for Config Editor...
python -m pip install -r p1_router/requirements.txt
python -m pip install pyinstaller

echo.
echo Building Config Editor executable...
python build_config_editor_exe.py

echo.
echo Deactivating virtual environment...
call deactivate

echo.
echo Installation completed!
echo You can now run the Config Editor using:
echo   1. Launch_Config_Editor.bat
echo   2. Or directly with dist\P1RouterConfigEditor.exe
echo.

pause 