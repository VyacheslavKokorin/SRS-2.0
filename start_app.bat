@echo off
setlocal
pushd %~dp0

set "VENV_DIR=%~dp0.venv"
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [setup] Creating virtual environment...
    py -3 -m venv "%VENV_DIR%" || python -m venv "%VENV_DIR%"
    if exist "%VENV_DIR%\Scripts\python.exe" (
        echo [setup] Upgrading pip...
        "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
        echo [setup] Installing dependencies...
        "%VENV_DIR%\Scripts\pip.exe" install -r "%~dp0requirements.txt"
    ) else (
        echo [error] Python 3 is required but was not found.
        pause
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"
set FLASK_APP=app.py
python app.py

popd
endlocal
