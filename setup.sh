#!/bin/bash
echo "========================================"
echo "   MekanAI - Kurulum"
echo "========================================"
echo

# Python kontrolü
echo "[1/4] Python kontrolü yapılıyor..."
if ! command -v python3 &>/dev/null; then
    echo "Python3 bulunamadı!"
    echo
    echo "Kurulum:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    echo
    exit 1
fi
python3 --version
echo "Python yüklü"
echo

# Virtual Environment
echo "[2/4] Virtual Environment kontrolü..."
if [ -d "venv" ]; then
    echo "Virtual environment mevcut"
else
    echo "Virtual environment oluşturuluyor..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "HATA: Virtual environment oluşturulamadı!"
        echo "python3-venv paketini kurun: sudo apt install python3-venv"
        exit 1
    fi
    echo "Virtual environment oluşturuldu"
fi
echo

# Activate
echo "[3/4] Virtual environment aktive ediliyor..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "HATA: Virtual environment aktive edilemedi!"
    exit 1
fi
echo "Virtual environment aktif"
echo

# Pip güncelleme
python -m pip install --upgrade pip --quiet
echo "pip güncellendi"
echo

# Temel paketler
echo "[4/4] Temel paketler yükleniyor..."
pip install -r requirements.txt --quiet
echo "Temel paketler yüklendi"
echo

# GPU paketleri (opsiyonel)
echo "========================================"
echo "   GPU / Lokal SD WebUI Desteği"
echo "========================================"
echo
echo "PyTorch + CUDA yüklemek ister misiniz?"
echo "(Sadece NVIDIA ekran kartı ve lokal SD WebUI kullanacaksanız gerekli)"
echo
echo "  [1] Evet - CUDA 12.1 ile PyTorch yükle (~3GB)"
echo "  [2] Hayır - Sadece Cloud API kullanacağım"
echo
read -p "Seçiminiz (1/2): " gpu_choice

if [ "$gpu_choice" = "1" ]; then
    echo
    echo "PyTorch CUDA yükleniyor... (Birkaç dakika sürebilir)"
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --quiet
    echo "Diğer GPU paketleri yükleniyor..."
    pip install -r requirements-gpu.txt --quiet
    echo "GPU paketleri yüklendi"
else
    echo "GPU paketleri atlandı."
    echo "  İstediğiniz zaman yükleyebilirsiniz:"
    echo "  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121"
    echo "  pip install -r requirements-gpu.txt"
fi

echo
echo "========================================"
echo "   KURULUM TAMAMLANDI!"
echo "========================================"
echo
echo "Uygulamayı başlatmak için:"
echo "  ./start.sh"
echo
echo "Veya manuel olarak:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo
