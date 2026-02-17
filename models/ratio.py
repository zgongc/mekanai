"""
MekanAI - Ratio Model & CRUD
"""
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .base import Base, db_session

# Manual input configuration (loaded from seed JSON)
ALLOW_MANUAL = True
MANUAL_MIN = 256
MANUAL_MAX = 2048
MANUAL_STEP = 64

# ============================================
# MODEL
# ============================================
class Ratio(Base):
    """Aspect ratio presets"""
    __tablename__ = "ratios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'icon': self.icon or '',
            'sort_order': self.sort_order,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    return [r.to_dict() for r in db_session.query(Ratio).order_by(Ratio.sort_order).all()]

def get_by_id(rid):
    row = db_session.query(Ratio).get(rid)
    return row.to_dict() if row else None

def get_manual_config():
    return {
        'allow_manual': ALLOW_MANUAL,
        'min': MANUAL_MIN,
        'max': MANUAL_MAX,
        'step': MANUAL_STEP,
    }

def create(**kwargs):
    obj = Ratio(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(rid, **kwargs):
    obj = db_session.query(Ratio).get(rid)
    if not obj:
        return None
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(rid):
    obj = db_session.query(Ratio).get(rid)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    global ALLOW_MANUAL, MANUAL_MIN, MANUAL_MAX, MANUAL_STEP

    if db_session.query(Ratio).count() > 0:
        return
    json_path = Path('data/seed/ratios_seed.json')
    if not json_path.exists():
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ALLOW_MANUAL = data.get('allow_manual', True)
    MANUAL_MIN = data.get('manual_min', 256)
    MANUAL_MAX = data.get('manual_max', 2048)
    MANUAL_STEP = data.get('manual_step', 64)

    for item in data.get('ratios', []):
        db_session.add(Ratio(
            name=item['name'],
            width=item['width'],
            height=item['height'],
            icon=item.get('icon', ''),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(Ratio).count()} ratios")
