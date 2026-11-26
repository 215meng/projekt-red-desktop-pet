@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYW_CMD=
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\pythonw.exe" (
    "%CONDA_PREFIX%\python.exe" -c "import PySide6" 2>nul
    if %errorlevel% equ 0 set PYW_CMD="%CONDA_PREFIX%\pythonw.exe"
)
if not defined PYW_CMD if exist ".venv\Scripts\pythonw.exe" (
    ".venv\Scripts\python.exe" -c "import PySide6" 2>nul
    if %errorlevel% equ 0 set PYW_CMD=".venv\Scripts\pythonw.exe"
)
if not defined PYW_CMD (
    set PYW_CMD=pythonw
)

start "" %PYW_CMD% run.py
exit
