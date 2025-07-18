@echo off
echo ===================================================
echo P1 Router - Automatic Installer and Builder
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
echo Creating virtual environment...
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m virtualenv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages in virtual environment...
python -m pip install -r p1_router/requirements.txt
python -m pip install pillow opencv-python pyinstaller

echo.
echo Building executable from virtual environment...
python build_exe.py

echo.
echo Deactivating virtual environment...
call deactivate

echo.
echo Installation completed!
echo You can now run the P1 Router application using:
echo   1. Launch_P1_Router.bat
echo   2. Or directly with dist\P1Router.exe
echo.

pause 