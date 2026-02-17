/**
 * MekanAI Settings - CRUD Management
 */

// ══════════════════════════════════════════
// TABLE CONFIGURATIONS
// ══════════════════════════════════════════

const TABLE_CONFIG = {
    styles: {
        label: 'Stiller',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'category', label: 'Kategori' },
            { key: 'subcategory', label: 'Alt Kategori' },
            { key: 'sort_order', label: 'Sıra' },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'category', label: 'Kategori', type: 'text' },
            { key: 'subcategory', label: 'Alt Kategori', type: 'text' },
            { key: 'prompt_snippet', label: 'Prompt Snippet', type: 'textarea' },
            { key: 'negative_snippet', label: 'Negatif Snippet', type: 'textarea' },
            { key: 'thumbnail', label: 'Thumbnail', type: 'text' },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    scenes: {
        label: 'Sahneler',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'category', label: 'Kategori' },
            { key: 'subcategory', label: 'Alt Kategori' },
            { key: 'sort_order', label: 'Sıra' },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'category', label: 'Kategori', type: 'text' },
            { key: 'subcategory', label: 'Alt Kategori', type: 'text' },
            { key: 'prompt_snippet', label: 'Prompt Snippet', type: 'textarea' },
            { key: 'negative_snippet', label: 'Negatif Snippet', type: 'textarea' },
            { key: 'thumbnail', label: 'Thumbnail', type: 'text' },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    perspectives: {
        label: 'Perspektifler',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'sort_order', label: 'Sıra' },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'prompt_snippet', label: 'Prompt Snippet', type: 'textarea' },
            { key: 'negative_snippet', label: 'Negatif Snippet', type: 'textarea' },
            { key: 'thumbnail', label: 'Thumbnail', type: 'text' },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    lightings: {
        label: 'Işıklandırma',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'sort_order', label: 'Sıra' },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'prompt_snippet', label: 'Prompt Snippet', type: 'textarea' },
            { key: 'negative_snippet', label: 'Negatif Snippet', type: 'textarea' },
            { key: 'thumbnail', label: 'Thumbnail', type: 'text' },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    ratios: {
        label: 'Oranlar',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'width', label: 'Genişlik' },
            { key: 'height', label: 'Yükseklik' },
            { key: 'sort_order', label: 'Sıra' },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'width', label: 'Genişlik', type: 'number', required: true },
            { key: 'height', label: 'Yükseklik', type: 'number', required: true },
            { key: 'icon', label: 'İkon', type: 'text' },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    ai_providers: {
        label: 'AI Providerlar',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'key', label: 'Key' },
            { key: 'type', label: 'Tip' },
            { key: 'enabled', label: 'Aktif', render: v => `<span class="toggle-badge ${v ? 'on' : 'off'}">${v ? 'Evet' : 'Hayır'}</span>` },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'key', label: 'Key', type: 'text', required: true },
            { key: 'type', label: 'Tip', type: 'select', options: ['local', 'cloud'] },
            { key: 'base_url', label: 'API URL', type: 'text' },
            { key: 'api_key', label: 'API Key', type: 'text' },
            { key: 'description', label: 'Açıklama', type: 'textarea' },
            { key: 'icon', label: 'İkon', type: 'text' },
            { key: 'enabled', label: 'Aktif', type: 'toggle', default: true },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    ai_models: {
        label: 'AI Modeller',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'provider', label: 'Provider', render: v => v ? v.name : '-' },
            { key: 'type', label: 'Tip' },
            { key: 'enabled', label: 'Aktif', render: v => `<span class="toggle-badge ${v ? 'on' : 'off'}">${v ? 'Evet' : 'Hayır'}</span>` },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'key', label: 'Key', type: 'text', required: true },
            { key: 'provider_id', label: 'Provider', type: 'select', source: 'ai_providers' },
            { key: 'type', label: 'Tip', type: 'select', options: ['checkpoint', 'controlnet', 'adapter', 'upscaler', 'cloud_api'] },
            { key: 'api_model_id', label: 'API Model ID', type: 'text' },
            { key: 'description', label: 'Açıklama', type: 'textarea' },
            { key: 'default_steps', label: 'Steps', type: 'number' },
            { key: 'default_cfg_scale', label: 'CFG Scale', type: 'number' },
            { key: 'default_sampler', label: 'Sampler', type: 'text' },
            { key: 'max_resolution', label: 'Max Resolution', type: 'number' },
            { key: 'module', label: 'CN Module', type: 'text' },
            { key: 'default_weight', label: 'CN Weight', type: 'number' },
            { key: 'scale_factor', label: 'Scale Factor', type: 'number' },
            { key: 'icon', label: 'İkon', type: 'text' },
            { key: 'enabled', label: 'Aktif', type: 'toggle', default: true },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
    modes: {
        label: 'Modlar',
        columns: [
            { key: 'id', label: 'ID', class: 'col-id' },
            { key: 'name', label: 'Ad' },
            { key: 'key', label: 'Key' },
            { key: 'controlnet_module', label: 'CN Module' },
            { key: 'controlnet_weight', label: 'Weight' },
            { key: 'denoising_strength', label: 'Denoise' },
            { key: 'sort_order', label: 'Sıra' },
        ],
        fields: [
            { key: 'name', label: 'Ad', type: 'text', required: true },
            { key: 'key', label: 'Key', type: 'text', required: true },
            { key: 'description', label: 'Açıklama', type: 'textarea' },
            { key: 'icon', label: 'İkon', type: 'text' },
            { key: 'controlnet_module', label: 'ControlNet Module', type: 'text' },
            { key: 'controlnet_weight', label: 'ControlNet Weight', type: 'number' },
            { key: 'denoising_strength', label: 'Denoising Strength', type: 'number' },
            { key: 'sort_order', label: 'Sıra', type: 'number', default: 0 },
        ]
    },
};

// ══════════════════════════════════════════
// STATE
// ══════════════════════════════════════════

let currentTable = null;
let currentData = [];
let editingId = null;
let selectCache = {};  // cache for dropdown sources

// ══════════════════════════════════════════
// INIT
// ══════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Tab clicks
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Form buttons
    document.getElementById('btnAdd').addEventListener('click', () => openForm());
    document.getElementById('btnFormClose').addEventListener('click', closeForm);
    document.getElementById('btnFormCancel').addEventListener('click', closeForm);
    document.getElementById('btnFormSave').addEventListener('click', saveForm);

    // Load general tab data
    loadGeneralStats();
    checkSdStatus();
});

// ══════════════════════════════════════════
// TAB SWITCHING
// ══════════════════════════════════════════

function switchTab(tabName) {
    // Update active tab
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.settings-tab[data-tab="${tabName}"]`).classList.add('active');

    if (tabName === 'general') {
        document.getElementById('panel-general').classList.add('active');
        document.getElementById('panel-table').classList.remove('active');
    } else {
        document.getElementById('panel-general').classList.remove('active');
        document.getElementById('panel-table').classList.add('active');
        loadTable(tabName);
    }
}

// ══════════════════════════════════════════
// TABLE RENDERING
// ══════════════════════════════════════════

async function loadTable(tableName) {
    currentTable = tableName;
    const config = TABLE_CONFIG[tableName];
    if (!config) return;

    document.getElementById('tableTitle').textContent = config.label;

    try {
        const res = await fetch(`/api/settings/${tableName}`);
        const json = await res.json();
        currentData = json.items || [];
        renderTable(config, currentData);
    } catch (err) {
        console.error('Table load error:', err);
    }
}

function renderTable(config, data) {
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');
    const empty = document.getElementById('tableEmpty');

    // Header
    thead.innerHTML = config.columns.map(col =>
        `<th class="${col.class || ''}">${col.label}</th>`
    ).join('') + '<th class="col-actions"></th>';

    // Body
    if (data.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    tbody.innerHTML = data.map(row => {
        const cells = config.columns.map(col => {
            const val = row[col.key];
            const display = col.render ? col.render(val) : (val ?? '-');
            return `<td class="${col.class || ''}">${display}</td>`;
        }).join('');

        return `<tr data-id="${row.id}">
            ${cells}
            <td class="col-actions">
                <div class="row-actions">
                    <button onclick="openForm(${row.id})" title="Düzenle"><i class="fas fa-pen"></i></button>
                    <button class="btn-delete" onclick="deleteItem(${row.id})" title="Sil"><i class="fas fa-trash"></i></button>
                </div>
            </td>
        </tr>`;
    }).join('');
}

// ══════════════════════════════════════════
// FORM (CREATE / EDIT)
// ══════════════════════════════════════════

async function openForm(id = null) {
    const config = TABLE_CONFIG[currentTable];
    if (!config) return;

    editingId = id;
    const record = id ? currentData.find(r => r.id === id) : null;

    document.getElementById('formTitle').textContent = record ? `Düzenle: ${record.name || '#' + record.id}` : 'Yeni Kayıt';

    // Build form fields
    const body = document.getElementById('formBody');
    body.innerHTML = '';

    for (const field of config.fields) {
        const div = document.createElement('div');
        div.className = 'form-field';

        const val = record ? (record[field.key] ?? '') : (field.default ?? '');

        if (field.type === 'textarea') {
            div.innerHTML = `
                <label>${field.label}</label>
                <textarea name="${field.key}" ${field.required ? 'required' : ''}>${val}</textarea>
            `;
        } else if (field.type === 'select' && field.options) {
            const opts = field.options.map(o =>
                `<option value="${o}" ${val === o ? 'selected' : ''}>${o}</option>`
            ).join('');
            div.innerHTML = `
                <label>${field.label}</label>
                <select name="${field.key}">${opts}</select>
            `;
        } else if (field.type === 'select' && field.source) {
            // Dynamic select from another table
            const options = await loadSelectOptions(field.source);
            const opts = options.map(o =>
                `<option value="${o.id}" ${val == o.id ? 'selected' : ''}>${o.name}</option>`
            ).join('');
            div.innerHTML = `
                <label>${field.label}</label>
                <select name="${field.key}">
                    <option value="">-- Seç --</option>
                    ${opts}
                </select>
            `;
        } else if (field.type === 'toggle') {
            div.innerHTML = `
                <label>${field.label}</label>
                <label class="toggle-switch">
                    <input type="checkbox" name="${field.key}" ${val ? 'checked' : ''}>
                    <span>${val ? 'Aktif' : 'Pasif'}</span>
                </label>
            `;
            // Update label on change
            setTimeout(() => {
                const cb = div.querySelector('input[type="checkbox"]');
                if (cb) cb.addEventListener('change', () => {
                    cb.nextElementSibling.textContent = cb.checked ? 'Aktif' : 'Pasif';
                });
            }, 0);
        } else {
            div.innerHTML = `
                <label>${field.label}</label>
                <input type="${field.type === 'number' ? 'number' : 'text'}" name="${field.key}" value="${val}" ${field.required ? 'required' : ''} ${field.type === 'number' ? 'step="any"' : ''}>
            `;
        }

        body.appendChild(div);
    }

    document.getElementById('formOverlay').style.display = 'flex';
}

async function loadSelectOptions(source) {
    if (selectCache[source]) return selectCache[source];
    try {
        const res = await fetch(`/api/settings/${source}`);
        const json = await res.json();
        selectCache[source] = json.items || [];
        return selectCache[source];
    } catch {
        return [];
    }
}

function closeForm() {
    document.getElementById('formOverlay').style.display = 'none';
    editingId = null;
}

async function saveForm() {
    const config = TABLE_CONFIG[currentTable];
    if (!config) return;

    const data = {};
    for (const field of config.fields) {
        const el = document.querySelector(`#formBody [name="${field.key}"]`);
        if (!el) continue;

        if (field.type === 'toggle') {
            data[field.key] = el.checked;
        } else if (field.type === 'number') {
            const v = el.value.trim();
            data[field.key] = v === '' ? null : parseFloat(v);
        } else if (field.type === 'select' && field.source) {
            const v = el.value;
            data[field.key] = v === '' ? null : parseInt(v);
        } else {
            data[field.key] = el.value.trim();
        }
    }

    try {
        const url = editingId
            ? `/api/settings/${currentTable}/${editingId}`
            : `/api/settings/${currentTable}`;
        const method = editingId ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();

        if (json.status === 'success') {
            closeForm();
            selectCache = {};  // clear cache
            loadTable(currentTable);
        } else {
            alert('Hata: ' + (json.message || 'Bilinmeyen hata'));
        }
    } catch (err) {
        alert('Hata: ' + err.message);
    }
}

// ══════════════════════════════════════════
// DELETE
// ══════════════════════════════════════════

async function deleteItem(id) {
    if (!confirm('Bu kaydı silmek istediğinize emin misiniz?')) return;

    try {
        const res = await fetch(`/api/settings/${currentTable}/${id}`, { method: 'DELETE' });
        const json = await res.json();

        if (json.status === 'success') {
            selectCache = {};
            loadTable(currentTable);
        } else {
            alert('Hata: ' + (json.message || 'Silinemedi'));
        }
    } catch (err) {
        alert('Hata: ' + err.message);
    }
}

// ══════════════════════════════════════════
// GENERAL TAB
// ══════════════════════════════════════════

async function loadGeneralStats() {
    const tables = ['styles', 'scenes', 'perspectives', 'lightings', 'ratios', 'ai_providers', 'ai_models', 'modes'];
    const ids = ['countStyles', 'countScenes', 'countPerspectives', 'countLightings', 'countRatios', 'countProviders', 'countModels', 'countModes'];

    for (let i = 0; i < tables.length; i++) {
        try {
            const res = await fetch(`/api/settings/${tables[i]}`);
            const json = await res.json();
            document.getElementById(ids[i]).textContent = json.count ?? '-';
        } catch {
            document.getElementById(ids[i]).textContent = 'Hata';
        }
    }
}

async function checkSdStatus() {
    const badge = document.getElementById('sdStatus');
    const models = document.getElementById('sdModels');
    try {
        const res = await fetch('/api/sd-status');
        const json = await res.json();
        if (json.connected) {
            badge.textContent = 'Bağlı';
            badge.className = 'status-badge online';
            const modelList = json.models || [];
            models.textContent = modelList.length > 0 ? modelList.join(', ') : 'Model bulunamadı';
        } else {
            badge.textContent = 'Bağlantı yok';
            badge.className = 'status-badge offline';
        }
    } catch {
        badge.textContent = 'Hata';
        badge.className = 'status-badge offline';
    }
}
