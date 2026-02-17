@echo off
echo ========================================
echo    MekanAI - Setup
echo ========================================
echo.

:: Check Python
echo [1/4] Checking Python...
py -c "" >tmp_stdout.txt 2>tmp_stderr.txt
if %ERRORLEVEL% == 0 goto :python_found

echo [!] Python not found!
echo.

:: Try winget auto-install
echo [1.1] Checking winget for auto-install...
WHERE winget >nul 2>&1
if %ERRORLEVEL% == 0 goto :install_with_winget

echo [!] Winget not found
goto :manual_python_install

:install_with_winget
echo [OK] Winget found
echo.
echo [*] Installing Python 3.12 automatically...
echo     (This may take a few minutes)
echo.

winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
if %ERRORLEVEL% == 0 goto :python_installed_success

echo.
echo [!] Winget installation failed.
goto :manual_python_install

:python_installed_success
echo.
echo [OK] Python installed successfully!
echo.
echo [!] IMPORTANT: To apply changes:
echo     1. Close this window
echo     2. Open a new command prompt
echo     3. Run setup.bat again
echo.
pause
exit /b 0

:manual_python_install
echo.
echo ========================================
echo    Manual Python Installation Required
echo ========================================
echo.
echo OPTION 1 - Winget (Recommended):
echo     winget install -e --id Python.Python.3.12
echo.
echo OPTION 2 - Manual:
echo     1. https://www.python.org/downloads/
echo     2. Check "Add Python to PATH" during install
echo.
pause
exit /b 1

:python_found
py --version
echo [OK] Python installed
echo.

:: Virtual Environment
echo [2/4] Checking Virtual Environment...
if exist "venv\" goto :venv_exists

echo [*] Creating virtual environment...
py -m venv venv
if %ERRORLEVEL% == 0 goto :venv_created

echo [!] ERROR: Could not create virtual environment!
pause
exit /b 1

:venv_created
echo [OK] Virtual environment created
goto :activate_venv

:venv_exists
echo [OK] Virtual environment exists

:activate_venv
echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% == 0 goto :venv_activated

echo [!] ERROR: Could not activate virtual environment!
pause
exit /b 1

:venv_activated
echo [OK] Virtual environment active
echo.

:: Pip upgrade
python -m pip install --upgrade pip --quiet
echo [OK] pip updated
echo.

:: Install packages
echo [4/4] Installing packages...
pip install -r requirements.txt --quiet
echo [OK] Packages installed
echo.

:: GPU packages (optional)
echo ========================================
echo    GPU / Local SD WebUI Support
echo ========================================
echo.
echo Install PyTorch + CUDA?
echo (Only needed if you have an NVIDIA GPU and will use local SD WebUI)
echo.
echo    [1] Yes - Install PyTorch with CUDA 12.1 (recommended, ~3GB)
echo    [2] No  - I will only use Cloud APIs
echo.
set /p gpu_choice="Your choice (1/2): "

if "%gpu_choice%"=="1" goto :install_gpu
echo [*] GPU packages skipped.
echo     You can install later:
echo     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
echo     pip install -r requirements-gpu.txt
goto :finish_setup

:install_gpu
echo.
echo [*] Installing PyTorch CUDA... (This may take a few minutes)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --quiet
echo [*] Installing other GPU packages...
pip install -r requirements-gpu.txt --quiet
echo [OK] GPU packages installed

:finish_setup
echo.
echo ========================================
echo    [OK] SETUP COMPLETE!
echo ========================================
echo.
echo To start the application:
echo     start.bat
echo.
echo Or manually:
echo     venv\Scripts\activate
echo     python app.py
echo.
pause

:: Cleanup
del tmp_stdout.txt 2>nul
del tmp_stderr.txt 2>nul
