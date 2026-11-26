@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================================================
echo  Arknights Projekt Red Desktop Pet v4.5 (Debug Console)
echo ====================================================================

set PY_CMD=
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" (
    "%CONDA_PREFIX%\python.exe" -c "import PySide6" 2>nul
    if %errorlevel% equ 0 set PY_CMD="%CONDA_PREFIX%\python.exe"
)
if not defined PY_CMD if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import PySide6" 2>nul
    if %errorlevel% equ 0 set PY_CMD=".venv\Scripts\python.exe"
)
if not defined PY_CMD (
    set PY_CMD=python
)

%PY_CMD% run.py
echo.
echo 桌宠进程已退出。
pause
