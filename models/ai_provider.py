"""
MekanAI - AI Provider Model & CRUD
API key önceliği: DB > .env
"""
import os
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base, db_session

# Provider key → env var mapping
ENV_KEY_MAP = {
    'openai': 'OPENAI_API_KEY',
    'stability': 'STABILITY_API_KEY',
    'gemini': 'GEMINI_API_KEY',
    'grok': 'GROK_API_KEY',
}

# ============================================
# MODEL
# ============================================
class AIProvider(Base):
    """AI service provider definitions (local SD WebUI, cloud APIs)"""
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    key = Column(String(50), nullable=False, unique=True, index=True)   # local, openai, stability, gemini, grok
    type = Column(String(20), nullable=False)                           # local | cloud
    base_url = Column(String(500))                                      # API endpoint (nullable)
    api_key = Column(String(500))                                        # API key (cloud providers)
    description = Column(Text)
    icon = Column(String(50))
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    models = relationship('AIModel', back_populates='provider')

    def to_dict(self):
        # DB öncelikli, yoksa .env'den oku
        api_key = self.api_key or ''
        if not api_key:
            env_var = ENV_KEY_MAP.get(self.key)
            if env_var:
                api_key = os.environ.get(env_var, '')
        return {
            'id': self.id,
            'name': self.name,
            'key': self.key,
            'type': self.type,
            'base_url': self.base_url or '',
            'api_key': api_key,
            'description': self.description or '',
            'icon': self.icon or '',
            'enabled': self.enabled,
            'sort_order': self.sort_order,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    return [r.to_dict() for r in db_session.query(AIProvider).order_by(AIProvider.sort_order).all()]

def get_by_id(pid):
    row = db_session.query(AIProvider).get(pid)
    return row.to_dict() if row else None

def get_by_key(key):
    row = db_session.query(AIProvider).filter(AIProvider.key == key).first()
    return row.to_dict() if row else None

def get_enabled():
    return [r.to_dict() for r in
            db_session.query(AIProvider).filter(AIProvider.enabled == True)
            .order_by(AIProvider.sort_order).all()]

def create(**kwargs):
    obj = AIProvider(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(pid, **kwargs):
    obj = db_session.query(AIProvider).get(pid)
    if not obj:
        return None
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(pid):
    obj = db_session.query(AIProvider).get(pid)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    if db_session.query(AIProvider).count() > 0:
        return
    json_path = Path('data/seed/providers_seed.json')
    if not json_path.exists():
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get('providers', []):
        db_session.add(AIProvider(
            name=item['name'],
            key=item['key'],
            type=item.get('type', 'local'),
            base_url=item.get('base_url'),
            api_key=item.get('api_key', ''),
            description=item.get('description', ''),
            icon=item.get('icon', ''),
            enabled=item.get('enabled', True),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(AIProvider).count()} ai_providers")
