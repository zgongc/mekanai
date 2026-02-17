@echo off
chcp 65001 >NUL
echo ========================================
echo    MekanAI - Kurulum
echo ========================================
echo.

:: Python kontrolü
echo [1/4] Python kontrolü yapılıyor...
py -c "" >tmp_stdout.txt 2>tmp_stderr.txt
if %ERRORLEVEL% == 0 goto :python_found

echo ⚠️  Python bulunamadı!
echo.

:: Python yoksa winget kontrolü
echo [1.1] Otomatik kurulum için winget kontrol ediliyor...
WHERE winget >nul 2>&1
if %ERRORLEVEL% == 0 goto :install_with_winget

:: Winget de yoksa manuel kurulum
echo ⚠️  Winget bulunamadı
goto :manual_python_install

:install_with_winget
echo ✅ Winget bulundu
echo.
echo 🔽 Python 3.12 otomatik yükleniyor...
echo    (Bu işlem birkaç dakika sürebilir)
echo.

winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
if %ERRORLEVEL% == 0 goto :python_installed_success

echo.
echo ❌ Winget ile yükleme başarısız oldu.
goto :manual_python_install

:python_installed_success
echo.
echo ✅ Python başarıyla yüklendi!
echo.
echo ⚠️  ÖNEMLI: Değişikliklerin geçerli olması için:
echo    1. Bu pencereyi kapatın
echo    2. Yeni bir komut istemi açın
echo    3. setup.bat'ı tekrar çalıştırın
echo.
pause
exit /b 0

:manual_python_install
echo.
echo ========================================
echo    Manuel Python Kurulumu Gerekli
echo ========================================
echo.
echo YÖNTEM 1 - Winget (Önerilen):
echo    winget install -e --id Python.Python.3.12
echo.
echo YÖNTEM 2 - Manuel:
echo    1. https://www.python.org/downloads/
echo    2. "Add Python to PATH" seçeneğini işaretleyin
echo.
pause
exit /b 1

:python_found
py --version
echo ✅ Python yüklü
echo.

:: Virtual Environment
echo [2/4] Virtual Environment kontrolü...
if exist "venv\" goto :venv_exists

echo ⚙️  Virtual environment oluşturuluyor...
py -m venv venv
if %ERRORLEVEL% == 0 goto :venv_created

echo ❌ HATA: Virtual environment oluşturulamadı!
pause
exit /b 1

:venv_created
echo ✅ Virtual environment oluşturuldu
goto :activate_venv

:venv_exists
echo ✅ Virtual environment mevcut

:activate_venv
echo.
echo [3/4] Virtual environment aktive ediliyor...
call venv\Scripts\activate.bat
if %ERRORLEVEL% == 0 goto :venv_activated

echo ❌ HATA: Virtual environment aktive edilemedi!
pause
exit /b 1

:venv_activated
echo ✅ Virtual environment aktif
echo.

:: Pip güncellemesi
python -m pip install --upgrade pip --quiet
echo ✅ pip güncellendi
echo.

:: Temel paketler
echo [4/4] Temel paketler yükleniyor...
pip install -r requirements.txt --quiet
echo ✅ Temel paketler yüklendi
echo.

:: GPU paketleri (opsiyonel)
echo ========================================
echo    GPU / Lokal SD WebUI Desteği
echo ========================================
echo.
echo PyTorch + CUDA yüklemek ister misiniz?
echo (Sadece NVIDIA ekran kartı ve lokal SD WebUI kullanacaksanız gerekli)
echo.
echo    [1] Evet - CUDA 12.1 ile PyTorch yükle (önerilen, ~3GB)
echo    [2] Hayır - Sadece Cloud API kullanacağım
echo.
set /p gpu_choice="Seçiminiz (1/2): "

if "%gpu_choice%"=="1" goto :install_gpu
echo ⏭️  GPU paketleri atlandı.
echo    İstediğiniz zaman yükleyebilirsiniz:
echo    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
echo    pip install -r requirements-gpu.txt
goto :finish_setup

:install_gpu
echo.
echo ⚙️  PyTorch CUDA yükleniyor... (Birkaç dakika sürebilir)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --quiet
echo ⚙️  Diğer GPU paketleri yükleniyor...
pip install -r requirements-gpu.txt --quiet
echo ✅ GPU paketleri yüklendi

:finish_setup
echo.
echo ========================================
echo    ✅ KURULUM TAMAMLANDI!
echo ========================================
echo.
echo Uygulamayı başlatmak için:
echo    start.bat
echo.
echo Veya manuel olarak:
echo    venv\Scripts\activate
echo    python app.py
echo.
pause

:: Temizlik
del tmp_stdout.txt 2>nul
del tmp_stderr.txt 2>nul
