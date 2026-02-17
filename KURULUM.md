# MekanAI - Kurulum Rehberi (Windows)

## Gereksinimler

- Windows 10/11
- Python 3.10 veya uzeri ([Indir](https://www.python.org/downloads/))
- SD WebUI Forge (Lokal AI icin - opsiyonel)

## Hizli Baslangic

### 1. Kurulum (Ilk Defa)

Proje klasorunde calistirin:
```
setup.bat
```

**Setup.bat ne yapar?**
- Python yuklu mu kontrol eder
- Virtual environment olusturur
- Flask ve gerekli paketleri yukler

### 2. Uygulamayi Baslat

```
start.bat
```

Tarayicida acilir: `http://localhost:5000`

Ag uzerinden erisim: `http://<IP_ADRESINIZ>:5000`

## Manuel Kurulum (Alternatif)

```bash
# 1. Virtual environment olustur
python -m venv venv

# 2. Aktive et
venv\Scripts\activate

# 3. Paketleri yukle
pip install -r requirements.txt

# 4. GPU paketleri (opsiyonel - sadece NVIDIA GPU + lokal SD WebUI için)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements-gpu.txt

# 5. Calistir
python app.py
```

---

## Cloud API Entegrasyonu

MekanAI, birden fazla AI saglayicisini destekler. API key'leri **Settings > Providers** sayfasindan eklenir.

### Stability AI (Onerilen)

Desteklenen ozellikler: Text-to-Image, Structure Control (Floorplan img2img)

| Bilgi | Deger |
|-------|-------|
| Kayit | [https://platform.stability.ai](https://platform.stability.ai) |
| API Key | Platform > API Keys > Create API Key |
| Fiyat | ~$0.03/gorsel (Stable Image Core) |
| Modeller | Stable Image Core, SD3.5, Stable Image Ultra |

**Kurulum:**
1. [platform.stability.ai](https://platform.stability.ai) adresinden hesap olusturun
2. Dashboard > API Keys > **Create API Key**
3. MekanAI > Settings > Providers > **Stability AI** > API Key alanina yapisirin
4. Canvas veya Floorplan'da Provider olarak **Stability AI** secin

### Google Gemini

Desteklenen ozellikler: Text-to-Image (Gemini Flash Image, Imagen 4)

| Bilgi | Deger |
|-------|-------|
| API Key | [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Fiyat | ~$0.04/gorsel (Gemini Flash Image) |
| Onemli | Billing (faturalandirma) aktif olmali |
| Modeller | Gemini 2.5 Flash Image, Imagen 4 Fast |

**Kurulum:**
1. [aistudio.google.com/apikey](https://aistudio.google.com/apikey) adresinden API key olusturun
2. AI Studio > Settings > Billing > **Pay-as-you-go** planini aktif edin
3. MekanAI > Settings > Providers > **Google Gemini** > API Key alanina yapisirin

> **Not:** gemini.google.com aboneligi (Antigravity/Gemini Pro) API erisimi saglamaz.
> API icin ayri olarak Google Cloud billing gereklidir.

### OpenAI (DALL-E 3)

Desteklenen ozellikler: Text-to-Image

| Bilgi | Deger |
|-------|-------|
| Kayit | [https://platform.openai.com](https://platform.openai.com) |
| API Key | Platform > API Keys > Create new secret key |
| Fiyat | $0.04/gorsel (1024x1024), $0.08/gorsel (1792x1024) |
| Modeller | DALL-E 3 |

**Kurulum:**
1. [platform.openai.com](https://platform.openai.com) adresinden hesap olusturun
2. Settings > Billing > kredi/odeme yontemi ekleyin
3. API Keys > **Create new secret key**
4. MekanAI > Settings > Providers > **OpenAI** > API Key alanina yapisirin

### xAI Grok

| Bilgi | Deger |
|-------|-------|
| Kayit | [https://console.x.ai](https://console.x.ai) |
| API Key | Console > API Keys |

> Grok gorsel uretim entegrasyonu henuz aktif degil.

---

## Lokal AI: SD WebUI Forge

Lokal GPU ile gorsel uretim icin SD WebUI Forge kullanilir.

### Gereksinimler
- NVIDIA GPU (RTX 3060+ onerilen, 8GB+ VRAM)
- CUDA destekli suruculer

### Kurulum

```bash
# 1. SD WebUI Forge'u klonla
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git

# 2. Baslat (ilk kurulum otomatik yapilir)
cd stable-diffusion-webui-forge
webui.bat --api --listen
```

### API Modunda Baslatma

SD WebUI Forge'u API modunda baslatmak icin `webui-user.bat` dosyasini duzenleyin:
```bat
set COMMANDLINE_ARGS=--api --listen
```

Varsayilan adres: `http://localhost:7860`

### MekanAI'ya Baglama

1. SD WebUI Forge'un calistigini dogrulayin: `http://<FORGE_IP>:7860`
2. MekanAI > Settings > Providers > **SD WebUI Forge** > Base URL'i girin
   - Ayni bilgisayar: `http://localhost:7860`
   - Ag uzerinden: `http://192.168.1.XXX:7860`

### Checkpoint Modelleri

Modelleri SD WebUI Forge'un `models/Stable-diffusion/` klasorune koyun:
- Mimari: Architecture Exterior, DvArch, Architecture RealMix
- Genel: RealVisXL, SDXL Base, FLUX.1 Schnell
- Hizli: SDXL Turbo, SatPony Lightning

---

## Sorun Giderme

### "Python bulunamadi" hatasi
- Python'u [buradan](https://www.python.org/downloads/) indirin
- Kurulumda **"Add Python to PATH"** secenegini isaretleyin

### Port 5000 kullanimda
`configs/config.yaml` dosyasinda portu degistirin:
```yaml
server:
  port: 8080
```

### SD WebUI Forge baglanti hatasi
- Forge'un `--api --listen` parametreleriyle calistigini dogrulayin
- Firewall ayarlarinizi kontrol edin (port 7860)
- Settings > Providers'dan Base URL'in dogru oldugunu kontrol edin

### Cloud API hatalari

| Hata | Cozum |
|------|-------|
| "API key ayarlanmamis" | Settings > Providers'dan key ekleyin |
| "Billing hard limit reached" | Provider platformundan kredi/limit ekleyin |
| "Quota exceeded" | Billing/faturalandirma aktif edin |
| "Unauthorized" | API key'in dogru oldugunu kontrol edin |

---

## Ozellikler

- Text-to-Image (Canvas) - Prompt'tan gorsel uretim
- Sketch-to-Image (Sketch) - Cizimden render
- Floorplan Render - Kat planindan 3D gorunum
- Image Enhance - Gorsel iyilestirme ve upscale
- Coklu Provider - Local + Stability AI + Gemini + OpenAI
- Stil/Perspektif/Aydinlatma - Prompt snippet'leri ile zenginlestirme
- Proje Yonetimi - Gorselleri projelerde organize etme
- Dark/Light Mode

---

## Yapilandirma Dosyalari

| Dosya | Aciklama |
|-------|----------|
| `configs/config.yaml` | Sunucu, veritabani, yol ayarlari |
| `data/db/mekanai.db` | SQLite veritabani |
| `data/seed/*.json` | Baslangic verileri (stiller, modeller vs.) |
