"""
MekanAI - AI Model & CRUD
"""
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class AIModel(Base):
    """AI model definitions (checkpoint, controlnet, upscaler, cloud)"""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    key = Column(String(50), nullable=False, unique=True, index=True)
    provider_id = Column(Integer, ForeignKey('ai_providers.id'), nullable=True, index=True)
    type = Column(String(50), nullable=False)                        # checkpoint, controlnet, adapter, upscaler, cloud_api
    api_model_id = Column(String(100))                               # cloud API model identifier (e.g. gemini-2.5-flash-image)
    description = Column(Text)
    capabilities = Column(Text)                                      # JSON array: ["txt2img", "img2img"]
    default_steps = Column(Integer)
    default_cfg_scale = Column(Float)
    default_sampler = Column(String(50))
    max_resolution = Column(Integer)
    module = Column(String(50))                                      # controlnet preprocessor module
    default_weight = Column(Float)                                   # controlnet/adapter weight
    scale_factor = Column(Integer)                                   # upscaler scale
    icon = Column(String(50))
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    provider = relationship('AIProvider', back_populates='models')

    def to_dict(self):
        caps = self.capabilities or '[]'
        if isinstance(caps, str):
            try:
                caps = json.loads(caps)
            except (json.JSONDecodeError, TypeError):
                caps = []
        return {
            'id': self.id,
            'name': self.name,
            'key': self.key,
            'provider_id': self.provider_id,
            'provider': self.provider.to_dict() if self.provider else None,
            'type': self.type,
            'api_model_id': self.api_model_id or '',
            'description': self.description or '',
            'capabilities': caps,
            'default_steps': self.default_steps,
            'default_cfg_scale': self.default_cfg_scale,
            'default_sampler': self.default_sampler,
            'max_resolution': self.max_resolution,
            'module': self.module,
            'default_weight': self.default_weight,
            'scale_factor': self.scale_factor,
            'icon': self.icon or '',
            'enabled': self.enabled,
            'sort_order': self.sort_order,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    return [r.to_dict() for r in db_session.query(AIModel).order_by(AIModel.sort_order).all()]

def get_by_id(mid):
    row = db_session.query(AIModel).get(mid)
    return row.to_dict() if row else None

def get_by_key(key):
    row = db_session.query(AIModel).filter(AIModel.key == key).first()
    return row.to_dict() if row else None

def get_by_type(type_name):
    return [r.to_dict() for r in
            db_session.query(AIModel).filter(AIModel.type == type_name)
            .order_by(AIModel.sort_order).all()]

def get_by_types(type_names):
    """Get models matching any of the given types"""
    return [r.to_dict() for r in
            db_session.query(AIModel).filter(AIModel.type.in_(type_names))
            .order_by(AIModel.sort_order).all()]

def get_generatable():
    """Get all models that can generate images (checkpoints + cloud APIs)"""
    return get_by_types(['checkpoint', 'cloud_api'])

def get_upscale_capable():
    """Get cloud/DB models with 'upscale' in capabilities"""
    models = get_all()
    return [m for m in models
            if m.get('type') in ('upscaler', 'cloud_api')
            and 'upscale' in m.get('capabilities', [])]

def get_by_provider(provider_id):
    return [r.to_dict() for r in
            db_session.query(AIModel).filter(AIModel.provider_id == provider_id)
            .order_by(AIModel.sort_order).all()]

def get_enabled():
    return [r.to_dict() for r in
            db_session.query(AIModel).filter(AIModel.enabled == True)
            .order_by(AIModel.sort_order).all()]

def create(**kwargs):
    if 'capabilities' in kwargs and isinstance(kwargs['capabilities'], list):
        kwargs['capabilities'] = json.dumps(kwargs['capabilities'])
    obj = AIModel(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(mid, **kwargs):
    obj = db_session.query(AIModel).get(mid)
    if not obj:
        return None
    if 'capabilities' in kwargs and isinstance(kwargs['capabilities'], list):
        kwargs['capabilities'] = json.dumps(kwargs['capabilities'])
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(mid):
    obj = db_session.query(AIModel).get(mid)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    if db_session.query(AIModel).count() > 0:
        return
    json_path = Path('data/seed/models_seed.json')
    if not json_path.exists():
        return

    # Provider key → id mapping
    from .ai_provider import AIProvider
    provider_map = {p.key: p.id for p in db_session.query(AIProvider).all()}

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get('models', []):
        caps = item.get('capabilities', [])
        provider_key = item.get('provider', 'local')
        db_session.add(AIModel(
            name=item['name'],
            key=item['key'],
            provider_id=provider_map.get(provider_key),
            type=item.get('type', 'checkpoint'),
            api_model_id=item.get('api_model_id'),
            description=item.get('description', ''),
            capabilities=json.dumps(caps) if isinstance(caps, list) else caps,
            default_steps=item.get('default_steps'),
            default_cfg_scale=item.get('default_cfg_scale'),
            default_sampler=item.get('default_sampler'),
            max_resolution=item.get('max_resolution'),
            module=item.get('module'),
            default_weight=item.get('default_weight'),
            scale_factor=item.get('scale_factor'),
            icon=item.get('icon', ''),
            enabled=item.get('enabled', True),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(AIModel).count()} ai_models")
