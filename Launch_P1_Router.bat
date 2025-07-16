@echo off
echo Launching P1 Router...

IF EXIST dist\P1Router.exe (
    start dist\P1Router.exe
) ELSE (
    IF EXIST venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
        python launcher.py
        call deactivate
    ) ELSE (
        python launcher.py
    )
)
