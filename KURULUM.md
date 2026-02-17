# MekanAI - Kurulum Rehberi

## 1. Kurulum (İlk Defa)

### Windows

1. Bu sayfadaki yeşil **`<> Code`** butonuna tıklayın
2. Açılan menüden **Download ZIP** seçin
3. İndirilen ZIP dosyasına sağ tıklayın → **Tümü Çıkart** (Extract All) seçin
4. Çıkan `mekanai-main` klasörünün içine girin
5. **`setup.bat`** dosyasını bulun ve çift tıklayın
6. Siyah bir komut penceresi açılacak — kurulum otomatik başlar

**Setup ne yapar?**
- Python yüklü mü kontrol eder (yoksa otomatik yükler)
- Proje için izole bir Python ortamı (venv) oluşturur
- Flask, Pillow, SQLAlchemy gibi gerekli kütüphaneleri yükler
- Size GPU/CUDA kurulumu isteyip istemediğinizi sorar (lokal AI için gerekli)

> Kurulum tamamlanınca "SETUP COMPLETE!" yazısını göreceksiniz.
> Bir tuşa basıp pencereyi kapatabilirsiniz.

### Linux / Mac

Terminal açın ve sırasıyla çalıştırın:

```bash
git clone https://github.com/zgongc/mekanai.git
cd mekanai
chmod +x setup.sh start.sh
./setup.sh
```

---

## 2. Başlatma (Her Seferinde)

### Windows

`mekanai` klasöründeki **`start.bat`** dosyasına çift tıklayın.

Siyah pencere açılacak ve tarayıcınız otomatik olarak **http://localhost:5000** adresini açacak.

> Tarayıcı açılmazsa, adres çubuğuna `http://localhost:5000` yazın.
> Siyah pencereyi kapatmayın — uygulama o pencerede çalışıyor.
> Durdurmak için siyah pencerede **CTRL+C** tuşlayına basın.

### Linux / Mac

```bash
./start.sh
```

### Ağ Üzerinden Erişim

Başka bir bilgisayardan erişmek için, MekanAI'nin çalıştığı bilgisayarın IP adresiyle:

```
http://192.168.1.XXX:5000
```

---

## 3. AI Sunucu Bağlantısı

MekanAI tek başına görsel üretmez — bir AI motoruna bağlanır. İki yol var:

### Yol A: Lokal GPU ile Ücretsiz Üretim (Önerilen)

Bilgisayarınızda NVIDIA GPU varsa (RTX 3060+ önerilen):

**SD WebUI Forge kurulumu:**
1. https://github.com/lllyasviel/stable-diffusion-webui-forge adresinden indirin
2. `webui.bat --listen --api` ile başlatın (ilk açılışta otomatik kurulum yapar)
3. MekanAI > Ayarlar > Providers > **SD WebUI Forge** > Base URL: `http://localhost:7860`
4. Enable edin — artık Canvas, Sketch, Floorplan, Enhance kullanabilirsiniz

**ComfyUI kurulumu (alternatif):**
1. https://github.com/comfyanonymous/ComfyUI adresinden indirin
2. `python main.py --listen 0.0.0.0` ile başlatın
3. MekanAI > Ayarlar > Providers > **ComfyUI** > Base URL: `http://localhost:8188`

> Lokal AI ile sınırsız görsel üretebilirsiniz — ek maliyet yoktur.

### Yol B: Cloud API (GPU Gerektirmez)

GPU'nuz yoksa veya hızlı sonuç istiyorsanız Cloud API kullanabilirsiniz:

1. MekanAI'yi başlatın → sol menüden **Ayarlar** sayfasına gidin
2. **Providers** sekmesinden istediğiniz servisi seçin
3. API anahtarını yapıştırın ve **Enable** edin

| Servis | API Key Nereden Alınır | Ücret |
|--------|----------------------|-------|
| Google Gemini | https://aistudio.google.com/apikey | Ücretsiz tier mevcut |
| xAI Grok | https://console.x.ai | Kayıtta $25 ücretsiz kredi |
| Stability AI | https://platform.stability.ai | Kredi bazlı (~$0.03/görsel) |
| OpenAI DALL-E | https://platform.openai.com | ~$0.04/görsel |

> Detaylı API key alma adımları için: MekanAI içinden **Yardım** sayfasına bakın.

---

## 4. Sorun Giderme

**setup.bat çift tıklayınca hiçbir şey olmuyor:**
- Dosyaya sağ tıklayın → **Yönetici olarak çalıştır** (Run as Administrator)
- Antivirüs/Windows Defender engelliyorsa geçici olarak kapatın

**"Python not found" hatası:**
- https://www.python.org/downloads/ adresinden Python 3.12 indirin
- Kurulumda **"Add Python to PATH"** kutucuğunu mutlaka işaretleyin
- Bilgisayarı yeniden başlatın, sonra setup.bat'i tekrar çalıştırın

**Sayfa açılmıyor (localhost:5000):**
- start.bat'in hala çalıştığından emin olun (siyah pencere açık olmalı)
- Farklı tarayıcı deneyin (Edge önerilen)
- Firewall 5000 portunu engelliyor olabilir

**SD WebUI / ComfyUI bağlantı hatası:**
- AI sunucusunun çalıştığından emin olun
- SD WebUI'yi `--listen --api` parametreleriyle başlatın
- ComfyUI'yi `--listen 0.0.0.0` ile başlatın
- Ayarlar'dan base URL'i kontrol edin

**Chrome'da tercihler kaydedilmiyor:**
- Adres çubuğundaki kilit/bilgi ikonuna tıklayın → Site ayarları → Çerezlere izin verin
- Veya `chrome://settings/cookies` adresinden genel ayarları kontrol edin
