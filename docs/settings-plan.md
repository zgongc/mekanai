# Settings Sayfası - Tablo Yönetimi Planı

## Amaç
`/settings` sayfasında tüm referans tablolarını (styles, scenes, perspectives, lightings, ratios, ai_providers, ai_models, modes) görüntüleme, ekleme, düzenleme ve silme (CRUD) işlemleri yapılabilecek bir admin paneli.

## UI Tasarımı

### Layout
```
┌─────────────────────────────────────────────────────┐
│  Settings                                           │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│  Genel   │  [Tablo içeriği / form]                  │
│  ──────  │                                          │
│  Styles  │  ┌─ Styles ──────────────────────────┐   │
│  Scenes  │  │ + Yeni Ekle          🔍 Ara...    │   │
│  Perspct │  ├───────────────────────────────────┤   │
│  Light.  │  │ ID │ Ad    │ Kategori │ İşlem     │   │
│  Ratios  │  │  1 │ Real. │ photo    │ ✏️ 🗑️     │   │
│  Provid. │  │  2 │ Cine. │ photo    │ ✏️ 🗑️     │   │
│  Models  │  │  3 │ Anime │ anime    │ ✏️ 🗑️     │   │
│  Modes   │  │ ...│       │          │           │   │
│          │  └───────────────────────────────────┘   │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

- **Sol:** Dikey tab menü (her tablo bir sekme)
- **Sağ:** Seçilen tablonun kayıtları (sortable tablo + CRUD butonları)
- **Genel** sekmesi: Tema, SD WebUI bağlantı durumu, config bilgileri

### Tablo Bazlı Özellikler

| Tablo | Listeleme Kolonları | Form Alanları | Özel |
|-------|-------------------|---------------|------|
| **Styles** | id, thumbnail, name, category, subcategory, sort_order | name, category, subcategory, prompt_snippet, negative_snippet, thumbnail (upload), sort_order | Kategori filtre |
| **Scenes** | id, thumbnail, name, category, subcategory, sort_order | name, category, subcategory, prompt_snippet, negative_snippet, thumbnail (upload), sort_order | Kategori filtre |
| **Perspectives** | id, thumbnail, name, sort_order | name, prompt_snippet, negative_snippet, thumbnail (upload), sort_order | - |
| **Lightings** | id, thumbnail, name, sort_order | name, prompt_snippet, negative_snippet, thumbnail (upload), sort_order | - |
| **Ratios** | id, name, width, height, icon, sort_order | name, width, height, icon, sort_order | width/height sayısal input |
| **AI Providers** | id, icon, name, key, type, enabled | name, key, type, base_url, api_key_field, description, icon, enabled | enabled toggle |
| **AI Models** | id, icon, name, provider, type, enabled | name, key, provider_id (dropdown), type, description, capabilities, default_steps, default_cfg_scale, default_sampler, max_resolution, module, default_weight, scale_factor, icon, enabled, sort_order | Provider dropdown, capabilities JSON editor |
| **Modes** | id, icon, name, key, controlnet_module, sort_order | name, key, description, icon, controlnet_module, controlnet_weight, denoising_strength, sort_order | Weight/denoising slider |

### CRUD Akışı

**Listeleme:**
- Sayfa yüklendiğinde sol menüden seçili tablonun tüm kayıtları çekilir
- GET `/api/settings/<tablo_adı>` → JSON array

**Ekleme:**
- "+ Yeni Ekle" butonuna tıkla → sağ tarafta boş form açılır (veya modal)
- Formu doldur → POST `/api/settings/<tablo_adı>` → Yeni kayıt oluştur

**Düzenleme:**
- Satırdaki ✏️ butonuna tıkla → form mevcut verilerle dolu açılır
- Kaydet → PUT `/api/settings/<tablo_adı>/<id>` → Güncelle

**Silme:**
- Satırdaki 🗑️ butonuna tıkla → Onay dialogu → DELETE `/api/settings/<tablo_adı>/<id>`

### Sıralama (Drag & Drop - opsiyonel)
- `sort_order` alanı olan tablolarda satırları sürükle-bırak ile sıralama
- PUT `/api/settings/<tablo_adı>/reorder` → `{ ids: [3, 1, 2, ...] }`

## Dosya Yapısı

### Yeni Oluşturulacak
| Dosya | Açıklama |
|-------|----------|
| `templates/settings/index.html` | Ana layout (sol tab menü + sağ content area) |
| `templates/settings/general.html` | Genel ayarlar partial (tema, SD WebUI durumu) |
| `templates/settings/table.html` | Generic tablo listeleme + form partial |
| `api/settings.py` | Settings REST API (generic CRUD for all tables) |
| `static/css/settings.css` | Settings sayfası stilleri |
| `static/js/settings.js` | Settings CRUD JS (tab switch, form, table render) |

### Güncellenecek
| Dosya | Açıklama |
|-------|----------|
| `templates/settings.html` | Sil (templates/settings/index.html'e taşındı) |
| `views/main.py` | settings route → `templates/settings/index.html` render |
| `api/__init__.py` | settings route import |

## API Tasarımı

### Generic Settings API (`api/settings.py`)

```
GET    /api/settings/styles              → Tüm stiller
POST   /api/settings/styles              → Yeni stil oluştur
PUT    /api/settings/styles/<id>         → Stil güncelle
DELETE /api/settings/styles/<id>         → Stil sil

GET    /api/settings/scenes              → Tüm sahneler
POST   /api/settings/scenes              → ...
PUT    /api/settings/scenes/<id>         → ...
DELETE /api/settings/scenes/<id>         → ...

... (aynı pattern tüm tablolar için)
```

### Generic Yaklaşım
Her tablo için ayrı endpoint yazmak yerine, tablo adını URL'den alıp ilgili model modülüne yönlendiren bir mapper:

```python
TABLE_MAP = {
    'styles': style_model,
    'scenes': scene_model,
    'perspectives': perspective_model,
    'lightings': lighting_model,
    'ratios': ratio_model,
    'ai_providers': ai_provider_model,
    'ai_models': ai_model_model,
    'modes': mode_model,
}

@bp.route('/<table_name>', methods=['GET'])
def list_items(table_name):
    model = TABLE_MAP.get(table_name)
    return jsonify(model.get_all())
```

## Frontend Akışı (settings.js)

```
1. Sayfa yükle → Sol menüde ilk sekme (Genel) aktif
2. Sekmeye tıkla → fetchTable(tableName)
3. fetchTable():
   - GET /api/settings/{tableName}
   - renderTable(data, columns) → HTML tablo oluştur
   - "+ Yeni Ekle" butonu bind
4. Edit butonu → openForm(tableName, record)
   - Form alanlarını tablo tipine göre oluştur (TABLE_CONFIG)
   - Mevcut verileri form'a doldur
5. Kaydet → POST veya PUT
6. Sil → confirm() → DELETE
7. Tablo yeniden render
```

### Frontend Tablo Config
```javascript
const TABLE_CONFIG = {
    styles: {
        label: 'Stiller',
        columns: ['id', 'thumbnail', 'name', 'category', 'subcategory', 'sort_order'],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'category', label: 'Kategori', type: 'text' },
            { key: 'subcategory', label: 'Alt Kategori', type: 'text' },
            { key: 'prompt_snippet', label: 'Prompt', type: 'textarea' },
            { key: 'negative_snippet', label: 'Negatif Prompt', type: 'textarea' },
            { key: 'thumbnail', label: 'Thumbnail', type: 'text' },
            { key: 'sort_order', label: 'Sıra', type: 'number' },
        ]
    },
    scenes: { ... },
    ai_models: {
        label: 'AI Modeller',
        columns: ['id', 'name', 'provider', 'type', 'enabled'],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'key', label: 'Key', type: 'text', required: true },
            { key: 'provider_id', label: 'Provider', type: 'select', source: 'ai_providers' },
            { key: 'type', label: 'Tip', type: 'select', options: ['checkpoint','controlnet','adapter','upscaler','cloud_api'] },
            { key: 'enabled', label: 'Aktif', type: 'toggle' },
            ...
        ]
    },
    ...
};
```

## Template Yapısı
```
templates/settings/
├── index.html          → Ana sayfa layout (extends base.html)
├── general.html        → Genel ayarlar partial (tema, bağlantı durumu)
└── table.html          → Generic tablo partial (list + form)
```

`index.html` Jinja2 ile tab menüsünü ve content area'yı render eder.
JS ile tab değişiminde API'den veri çekilir ve sağ panele inject edilir.

## Uygulama Sırası
1. `api/settings.py` - Generic CRUD API
2. `templates/settings/index.html` - Ana layout
3. `static/css/settings.css` - Stiller
4. `static/js/settings.js` - CRUD JS mantığı
5. `views/main.py` - settings route güncelle
6. `api/__init__.py` - Route kayıt
7. Test: tüm tablolarda list/create/update/delete
