# CLAUDE.md - MekanAI Project

## Proje
İç mimarlar için AI görsel üretim platformu.
Flask + SD WebUI Forge + ComfyUI + ControlNet + Cloud APIs. PromeAI benzeri UI hedefleniyor.

## Yapı
```
app.py              → Flask factory (create_app pattern)
views/              → Sayfa route'ları (blueprint)
api/                → REST endpoints + AI generator'lar (*_generator.py)
models/             → SQLAlchemy ORM modelleri + CRUD (her tablo kendi dosyasında)
templates/          → Jinja2 HTML
static/css/         → style.css (temel) + sayfa bazlı CSS dosyaları
static/js/          → JavaScript dosyaları
configs/            → config.yaml, .env
data/db/            → SQLite DB
data/seed/          → Seed JSON dosyaları
data/projects/      → Proje dosyaları
```

## Veritabanı Kuralları

### SQLAlchemy ORM kullan (raw SQL değil)
- Her tablo kendi dosyasında: `models/scene.py`, `models/style.py` vs.
- Model tanımı + CRUD işlemleri **aynı dosyada** olsun
- Her alan açıkça tanımlanmalı (type, nullable, index, default, docstring)
- İlişkiler `relationship()` ile belirtilmeli

### Model dosya şablonu:
```python
# models/scene.py
"""
MekanAI - Scene Model & CRUD
"""
from .base import Base, db_session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

# ============================================
# MODEL
# ============================================
class Scene(Base):
    """AI sahne tanımları"""
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), index=True)
    prompt_snippet = Column(Text)
    negative_snippet = Column(Text)
    thumbnail = Column(String(200))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================
# CRUD
# ============================================
def get_all(): ...
def get_by_category(category): ...
def get_by_id(scene_id): ...
def create(**kwargs): ...
def update(scene_id, **kwargs): ...
def delete(scene_id): ...

# ============================================
# SEED
# ============================================
def seed_from_json():
    """data/seed/scenes_seed.json dosyasından başlangıç verileri yükle"""
    ...
```

### Tablolar & Seed Verileri:

| Tablo | Dosya | Seed JSON | Kayıt |
|-------|-------|-----------|-------|
| `projects` | `models/project.py` | - | - |
| `images` | `models/image.py` | - | FK → projects |
| `ai_providers` | `models/ai_provider.py` | `data/seed/providers_seed.json` | 6 (local, comfyui, openai, stability, gemini, grok) |
| `ai_models` | `models/ai_model.py` | `data/seed/models_seed.json` | 15+ (FK → ai_providers) |
| `styles` | `models/style.py` | `data/seed/styles_seed.json` | 25 (category/subcategory) |
| `scenes` | `models/scene.py` | `data/seed/scenes_seed.json` | 28 (category/subcategory) |
| `perspectives` | `models/perspective.py` | `data/seed/perspectives_seed.json` | 21 |
| `lightings` | `models/lighting.py` | `data/seed/lightings_seed.json` | 24 |
| `ratios` | `models/ratio.py` | `data/seed/ratios_seed.json` | 13 preset + manuel input |
| `modes` | `models/mode.py` | `data/seed/modes_seed.json` | 8 (ControlNet ayarları) |

### İlişkiler:
```
AIProvider (1) ──── (*) AIModel     → provider_id FK + relationship
Project    (1) ──── (*) Image       → project_id FK + ON DELETE CASCADE
```

### Prompt Birleştirme Mantığı:
```
final_prompt = user_prompt + style.prompt_snippet + scene.prompt_snippet + perspective.prompt_snippet + lighting.prompt_snippet
final_negative = user_negative + style.negative_snippet + scene.negative_snippet + perspective.negative_snippet + lighting.negative_snippet
```

### Mode → ControlNet Ayarları:
Mode tablosu ControlNet modülü, weight ve denoising_strength değerlerini belirler.
Detail (en sadık) → Concept → Free (tam yaratıcı) skalasında çalışır.

## CSS Kuralları
- **style.css** → Temel tanımlamalar (reset, layout, renkler, tipografi, ortak bileşenler)
- **canvas.css** → Canvas sayfasına özel stiller
- **projects.css** → Projects sayfasına özel stiller
- Her yeni sayfa için ayrı CSS dosyası oluştur
- style.css'i şişirme!

## Kod Kuralları
- Türkçe UI, İngilizce kod
- Flask blueprint yapısı koru
- Config: configs/config.yaml üzerinden
- DB: SQLite + SQLAlchemy ORM
- SD WebUI API: localhost:7860 veya 192.168.1.195:7860
- Yeni sayfa → views/ altına blueprint
- Yeni API → api/ altına register_routes pattern
- Yeni tablo → models/ altına model + CRUD

## UI Referansı (PromeAI)
PromeAI (promeai.pro/blender) benzeri sol panel yapısı:
- Prompt + Reference Image
- Model seçimi (dropdown, provider bazlı gruplama)
- Style (thumbnail grid popup, üst kategori tab + alt kategori chip/tag)
- Scene (thumbnail grid popup, üst kategori tab + ara seviye tag + alt seviye tag, çoklu seçim)
- Perspective (thumbnail grid popup)
- Mode (ikon kartları, başlık + açıklama paragrafı, seçili=mavi border)
- Advanced toggle: Negative Prompt, Artistry slider, Ratio popup, Lighting popup
- Generate butonu

## SD WebUI Endpoints
- txt2img: POST /sdapi/v1/txt2img
- img2img: POST /sdapi/v1/img2img
- ControlNet: alwayson_scripts içinde
- depth_midas: Sketch → Render pipeline

## ComfyUI Endpoints
- Queue prompt: POST /prompt (workflow JSON)
- History: GET /history/{prompt_id}
- Download: GET /view?filename=...&type=output
- Upload: POST /upload/image
- Info: GET /object_info/{NodeClass}
- Status: GET /system_stats

## Aktif Görevler
- [x] SQLAlchemy ORM'e geçiş (raw SQL → ORM)
- [x] Seed JSON'lardan tabloları oluştur ve verileri yükle
- [x] ai_providers tablosu + ai_models relationship
- [x] Canvas sayfası (txt2img)
- [x] Sketch sayfası (ControlNet + source image)
- [x] SD WebUI Forge API bağlantısı (ai_generator.py)
- [ ] Settings sayfası: tablo yönetimi (CRUD UI)
- [ ] PromeAI tarzı thumbnail grid popup UI (style/scene/perspective/lighting)
- [ ] Mode seçim kartları UI
- [ ] Ratio popup (preset butonlar + manuel input)
- [ ] Prompt birleştirme mantığı (seçimler → final prompt)
- [ ] Floorplan sayfası
- [ ] Image Enhancer / Upscaler
- [ ] Node-based canvas (LiteGraph.js - gelecek)
