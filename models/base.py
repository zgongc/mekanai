"""
MekanAI - Database Base
SQLAlchemy engine, session, and Base configuration
"""
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from config import config

Base = declarative_base()

# ── Engine & Session (module-level) ──────────────
_db_path = config.get('database.path', 'data/db/mekanai.db')
engine = create_engine(f"sqlite:///{_db_path}", echo=False, pool_pre_ping=True)


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode and foreign keys for SQLite"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


event.listen(engine, "connect", _set_sqlite_pragma)

session_factory = sessionmaker(bind=engine)
db_session = scoped_session(session_factory)


# ── Init & Seed ──────────────────────────────────

def init_db():
    """Create tables and seed data."""
    # Import all models so Base.metadata knows about them
    from . import project, image, style, scene, perspective, lighting, ratio, ai_provider, ai_model, mode

    Base.metadata.create_all(bind=engine)

    _run_migrations()
    _seed_all()
    print("[+] DB initialized (SQLAlchemy ORM)")


def _run_migrations():
    """Run schema migrations for existing databases"""
    insp = inspect(engine)
    # Migration: add parent_id to images table
    if 'images' in insp.get_table_names():
        columns = [c['name'] for c in insp.get_columns('images')]
        if 'parent_id' not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE images ADD COLUMN parent_id INTEGER REFERENCES images(id) ON DELETE SET NULL"))
            print("[+] Migration: images.parent_id added")

    # Migration: ai_providers - set local base_url + rename api_key_field → api_key
    if 'ai_providers' in insp.get_table_names():
        columns = [c['name'] for c in insp.get_columns('ai_providers')]
        with engine.begin() as conn:
            result = conn.execute(text("SELECT base_url FROM ai_providers WHERE key='local'")).fetchone()
            if result and not result[0]:
                conn.execute(text("UPDATE ai_providers SET base_url='http://192.168.1.195:7860' WHERE key='local'"))
                print("[+] Migration: local provider base_url set")
            if 'api_key_field' in columns and 'api_key' not in columns:
                conn.execute(text("ALTER TABLE ai_providers RENAME COLUMN api_key_field TO api_key"))
                print("[+] Migration: ai_providers.api_key_field → api_key")
            # Set cloud provider base_urls if empty
            for pkey, purl in [
                ('gemini', 'https://generativelanguage.googleapis.com/v1beta'),
                ('openai', 'https://api.openai.com/v1'),
                ('stability', 'https://api.stability.ai/v2beta'),
                ('grok', 'https://api.x.ai/v1'),
            ]:
                r = conn.execute(text("SELECT base_url FROM ai_providers WHERE key=:k"), {"k": pkey}).fetchone()
                if r and not r[0]:
                    conn.execute(text("UPDATE ai_providers SET base_url=:u WHERE key=:k"), {"u": purl, "k": pkey})
                    print(f"[+] Migration: {pkey} provider base_url set")

    # Migration: add api_model_id to ai_models + insert Gemini models
    if 'ai_models' in insp.get_table_names():
        columns = [c['name'] for c in insp.get_columns('ai_models')]
        with engine.begin() as conn:
            if 'api_model_id' not in columns:
                conn.execute(text("ALTER TABLE ai_models ADD COLUMN api_model_id VARCHAR(100)"))
                print("[+] Migration: ai_models.api_model_id added")
            # Insert Gemini models if not present
            exists = conn.execute(text("SELECT id FROM ai_models WHERE key='gemini_flash_image'")).fetchone()
            if not exists:
                gemini_pid = conn.execute(text("SELECT id FROM ai_providers WHERE key='gemini'")).fetchone()
                if gemini_pid:
                    pid = gemini_pid[0]
                    conn.execute(text(
                        "INSERT INTO ai_models (name,key,provider_id,type,api_model_id,description,capabilities,max_resolution,icon,enabled,sort_order) "
                        "VALUES ('Gemini 2.5 Flash Image','gemini_flash_image',:pid,'cloud_api','gemini-2.5-flash-image',"
                        "'Nano Banana — hızlı, ucuz, metin+görsel mixed üretim (~$0.04/görsel)','[\"txt2img\"]',2048,'gemini',1,52)"
                    ), {"pid": pid})
                    conn.execute(text(
                        "INSERT INTO ai_models (name,key,provider_id,type,api_model_id,description,capabilities,max_resolution,icon,enabled,sort_order) "
                        "VALUES ('Imagen 4 Fast','imagen4_fast',:pid,'cloud_api','imagen-4.0-fast-generate-001',"
                        "'Google Imagen 4 Fast — en ucuz, hızlı text-to-image ($0.02/görsel)','[\"txt2img\"]',2048,'gemini',1,53)"
                    ), {"pid": pid})
                    print("[+] Migration: Gemini models inserted")

            # Set api_model_id for existing cloud models (DALL-E 3, Stability)
            for mkey, mid in [
                ('dalle3', 'dall-e-3'),
                ('stability_sdxl', 'stable-image-core'),
            ]:
                r = conn.execute(text("SELECT api_model_id FROM ai_models WHERE key=:k"), {"k": mkey}).fetchone()
                if r and not r[0]:
                    conn.execute(text("UPDATE ai_models SET api_model_id=:m WHERE key=:k"), {"m": mid, "k": mkey})
                    print(f"[+] Migration: {mkey} api_model_id set to {mid}")

    # Migration: Insert ComfyUI provider + models
    if 'ai_providers' in insp.get_table_names():
        with engine.begin() as conn:
            comfyui_exists = conn.execute(text("SELECT id FROM ai_providers WHERE key='comfyui'")).fetchone()
            if not comfyui_exists:
                conn.execute(text(
                    "INSERT INTO ai_providers (name,key,type,base_url,description,icon,enabled,sort_order) "
                    "VALUES ('ComfyUI','comfyui','local','http://localhost:8188',"
                    "'ComfyUI — Node tabanlı, gelişmiş workflow desteği','comfyui',0,2)"
                ))
                print("[+] Migration: ComfyUI provider inserted")

                # Insert ComfyUI models
                comfyui_pid = conn.execute(text("SELECT id FROM ai_providers WHERE key='comfyui'")).fetchone()
                if comfyui_pid:
                    pid = comfyui_pid[0]
                    conn.execute(text(
                        "INSERT INTO ai_models (name,key,provider_id,type,api_model_id,description,capabilities,"
                        "default_steps,default_cfg_scale,default_sampler,max_resolution,icon,enabled,sort_order) "
                        "VALUES ('FLUX.1 Dev','flux_dev',:pid,'checkpoint','flux1-dev',"
                        "'FLUX.1 Dev — yüksek kalite, detaylı, yaratıcı çıktı (ComfyUI)',"
                        "'[\"txt2img\",\"img2img\"]',20,1.0,'Euler',2048,'flux',1,13)"
                    ), {"pid": pid})
                    conn.execute(text(
                        "INSERT INTO ai_models (name,key,provider_id,type,api_model_id,description,capabilities,"
                        "default_steps,default_cfg_scale,default_sampler,max_resolution,icon,enabled,sort_order) "
                        "VALUES ('SD3.5 Large Turbo','sd35_large_turbo',:pid,'checkpoint','sd3.5_large_turbo',"
                        "'SD 3.5 Large Turbo — hızlı, yüksek kalite (4-8 step, ComfyUI)',"
                        "'[\"txt2img\",\"img2img\"]',4,1.0,'Euler',1536,'sd35',1,14)"
                    ), {"pid": pid})
                    print("[+] Migration: ComfyUI models inserted")


def _seed_all():
    """Seed all reference tables if they are empty"""
    from .style import seed_from_json as seed_styles
    from .scene import seed_from_json as seed_scenes
    from .perspective import seed_from_json as seed_perspectives
    from .lighting import seed_from_json as seed_lightings
    from .ratio import seed_from_json as seed_ratios
    from .ai_provider import seed_from_json as seed_ai_providers
    from .ai_model import seed_from_json as seed_ai_models
    from .mode import seed_from_json as seed_modes

    seed_styles()
    seed_scenes()
    seed_perspectives()
    seed_lightings()
    seed_ratios()
    seed_ai_providers()
    seed_ai_models()
    seed_modes()


def shutdown_session(exception=None):
    """Remove scoped session at end of request."""
    db_session.remove()
