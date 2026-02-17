#!/bin/bash
echo "========================================"
echo "   MekanAI - Kurulum"
echo "========================================"
echo

# Python kontrolü
echo "[1/3] Python kontrolü yapılıyor..."
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
echo "[2/3] Virtual Environment kontrolü..."
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
echo "[3/3] Paketler yükleniyor..."
pip install -r requirements.txt --quiet
echo "Temel paketler yüklendi"
echo

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
