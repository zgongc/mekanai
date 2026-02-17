@echo off
cls

echo ========================================
echo    MekanAI - AI Interior Design
echo ========================================
echo.

:: Check installation
if not exist "venv\" (
    echo [!] Virtual environment not found!
    echo.
    echo Please run setup first:
    echo    setup.bat
    echo.
    pause
    exit /b 1
)

:: Activate Virtual Environment
echo [*] Starting application...
call venv\Scripts\activate.bat

:: Check Flask
python -c "import flask" 2>nul
if errorlevel 1 (
    echo.
    echo [!] ERROR: Flask not installed!
    echo.
    echo Please run setup:
    echo    setup.bat
    echo.
    pause
    exit /b 1
)

:: Create .env if not exists
if not exist "configs\.env" (
    echo [*] Creating configs\.env file...
    if exist "configs\.env.example" (
        copy "configs\.env.example" "configs\.env" >nul
    )
)

echo.
echo ========================================
echo    [*] Server Starting
echo ========================================
echo.
echo [*] Address: http://localhost:5000
echo [*] Network: http://0.0.0.0:5000
echo.
echo [i] If browser doesn't open, visit the address above
echo.
echo [!] To stop: Press CTRL+C
echo.
echo ========================================
echo.

:: Open browser after 5 seconds
start "" timeout /t 5 /nobreak ^>nul ^& start http://localhost:5000

:: Start Flask app
py app.py

:: Handle errors
if errorlevel 1 (
    echo.
    echo [!] Application terminated with an error!
    echo.
    pause
)
