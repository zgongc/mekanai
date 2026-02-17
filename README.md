# MekanAI - AI Interior Design Platform

İç mimarlar için AI destekli görsel tasarım platformu.
Lokal SD WebUI Forge + Cloud API (Gemini, Stability AI, OpenAI, Grok) hybrid çözüm.

## Özellikler

- **Canvas** — Text-to-image, prompt'tan iç mekan görselleri
- **Sketch** — ControlNet ile el çizimlerini render'a dönüştürme
- **Enhance** — Upscale / enhancement (lokal + cloud)
- **Floorplan** — Kat planından görsel üretimi
- **Projects** — Proje yönetimi ve görsel organizasyonu
- **Hybrid AI** — Lokal (SD WebUI Forge) + Cloud API desteği
- **Multi-Provider** — Gemini, Stability AI, OpenAI DALL-E, xAI Grok
- **Dark/Light Mode**

## Sistem Gereksinimleri

### Minimum (Cloud API):
- Python 3.10+
- 4GB RAM
- İnternet bağlantısı

### Önerilen (Lokal AI):
- Python 3.10+
- NVIDIA GPU (RTX 3090 24GB VRAM önerilen)
- 32GB RAM
- SD WebUI Forge kurulu ve çalışır durumda

## Hızlı Kurulum

### Windows

1. Sayfanın üst kısmındaki yeşil **`<> Code`** butonuna tıklayın → **Download ZIP** seçin
2. ZIP dosyasını indirin ve bir klasöre çıkartın
3. **`setup.bat`** dosyasına çift tıklayın — Python, sanal ortam ve tüm paketler otomatik kurulur
4. Kurulum bitince **`start.bat`** dosyasına çift tıklayın
5. Tarayıcınız otomatik açılacak: **http://localhost:5000**

> Python yüklü değilse setup.bat sizin için otomatik indirip kurar.

### Linux / Mac

```bash
git clone https://github.com/zgongc/mekanai.git
cd mekanai
chmod +x setup.sh start.sh
./setup.sh      # kurulum (bir kez)
./start.sh      # başlat
```

### Manuel Kurulum

Yukarıdaki yöntemler çalışmazsa adım adım:

```bash
# 1. Virtual environment oluştur
python3 -m venv venv

# 2. Aktive et
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Paketleri yükle
pip install -r requirements.txt

# 4. GPU paketleri (opsiyonel - sadece NVIDIA GPU + lokal SD WebUI için)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements-gpu.txt

# 5. Çalıştır
python app.py
```

Tarayıcıda: **http://localhost:5000**

## Proje Yapısı

```
app.py                → Flask factory (create_app)
views/                → Sayfa route'ları (blueprint)
api/                  → REST endpoints + AI generator'lar
models/               → SQLAlchemy ORM + CRUD
templates/            → Jinja2 HTML
static/css/           → CSS dosyaları
static/js/            → JavaScript dosyaları
configs/              → config.yaml
data/db/              → SQLite veritabanı
data/seed/            → Seed JSON dosyaları
data/projects/        → Proje dosyaları
```

## AI Providers

| Provider | Tür | Özellikler |
|----------|-----|-----------|
| SD WebUI Forge | Lokal | txt2img, img2img, ControlNet, upscale |
| Google Gemini | Cloud | txt2img (Imagen) |
| Stability AI | Cloud | txt2img, structure control, upscale |
| OpenAI | Cloud | txt2img (DALL-E 3) |
| xAI Grok | Cloud | txt2img (Aurora) |

### Cloud API Ayarları
Settings sayfasından provider'ları etkinleştirin ve API key'leri girin:
- **Stability AI**: https://platform.stability.ai
- **OpenAI**: https://platform.openai.com
- **Google Gemini**: https://aistudio.google.com
- **xAI Grok**: https://console.x.ai

### Lokal SD WebUI Forge
```bash
# Forge kurulumu
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git
cd stable-diffusion-webui-forge
webui.bat --api --listen
```
Settings > Providers'dan SD WebUI URL'ini ayarlayın (varsayılan: `http://localhost:7860`).

## Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `requirements.txt` | Temel paketler (Flask, SQLAlchemy, Pillow...) |
| `requirements-gpu.txt` | GPU paketleri (torch, diffusers, transformers) |
| `setup.bat` / `setup.sh` | Otomatik kurulum (Windows / Linux) |
| `start.bat` / `start.sh` | Uygulamayı başlatma (Windows / Linux) |
| `configs/config.yaml` | Uygulama ayarları |
