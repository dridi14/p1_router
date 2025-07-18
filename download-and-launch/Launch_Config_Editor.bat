@echo off
echo Launching P1 Router Config Editor...

IF EXIST dist\P1RouterConfigEditor.exe (
    start dist\P1RouterConfigEditor.exe
) ELSE (
    IF EXIST venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
        python config_editor_launcher.py
        call deactivate
    ) ELSE (
        python config_editor_launcher.py
    )
)
