"""
MekanAI - Mode Model & CRUD
"""
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class Mode(Base):
    """ControlNet mode presets (Detail → Free scale)"""
    __tablename__ = "modes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    key = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text)
    icon = Column(String(100))
    controlnet_module = Column(String(50), nullable=True)    # null for 'free' mode
    controlnet_weight = Column(Float, default=0.0)
    denoising_strength = Column(Float, default=1.0)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'key': self.key,
            'description': self.description or '',
            'icon': self.icon or '',
            'controlnet_module': self.controlnet_module,
            'controlnet_weight': self.controlnet_weight,
            'denoising_strength': self.denoising_strength,
            'sort_order': self.sort_order,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    return [r.to_dict() for r in db_session.query(Mode).order_by(Mode.sort_order).all()]

def get_by_id(mid):
    row = db_session.query(Mode).get(mid)
    return row.to_dict() if row else None

def get_by_key(key):
    row = db_session.query(Mode).filter(Mode.key == key).first()
    return row.to_dict() if row else None

def create(**kwargs):
    obj = Mode(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(mid, **kwargs):
    obj = db_session.query(Mode).get(mid)
    if not obj:
        return None
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(mid):
    obj = db_session.query(Mode).get(mid)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    if db_session.query(Mode).count() > 0:
        return
    json_path = Path('data/seed/modes_seed.json')
    if not json_path.exists():
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get('modes', []):
        db_session.add(Mode(
            name=item['name'],
            key=item['key'],
            description=item.get('description', ''),
            icon=item.get('icon', ''),
            controlnet_module=item.get('controlnet_module'),
            controlnet_weight=item.get('controlnet_weight', 0.0),
            denoising_strength=item.get('denoising_strength', 1.0),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(Mode).count()} modes")
