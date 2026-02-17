#!/bin/bash
echo "========================================"
echo "   MekanAI - AI Interior Design"
echo "========================================"
echo

# Check installation
if [ ! -d "venv" ]; then
    echo "[!] Virtual environment not found!"
    echo
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo
    exit 1
fi

# Activate Virtual Environment
echo "[*] Starting application..."
source venv/bin/activate

# Check Flask
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo
    echo "[!] ERROR: Flask not installed!"
    echo
    echo "Please run setup:"
    echo "  ./setup.sh"
    echo
    exit 1
fi

# Create .env if not exists
if [ ! -f "configs/.env" ]; then
    echo "[*] Creating configs/.env file..."
    if [ -f "configs/.env.example" ]; then
        cp "configs/.env.example" "configs/.env"
    fi
fi

echo
echo "========================================"
echo "   [*] Server Starting"
echo "========================================"
echo
echo "[*] Address: http://localhost:5000"
echo "[*] Network: http://0.0.0.0:5000"
echo
echo "[i] If browser doesn't open, visit the address above"
echo
echo "[!] To stop: Press CTRL+C"
echo
echo "========================================"
echo

# Open browser after 3 seconds (background)
(sleep 3 && xdg-open http://localhost:5000 2>/dev/null || open http://localhost:5000 2>/dev/null) &

# Start Flask app
python app.py
