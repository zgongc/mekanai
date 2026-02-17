"""
MekanAI - Perspective Model & CRUD
"""
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class Perspective(Base):
    """Camera angle and perspective definitions"""
    __tablename__ = "perspectives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    prompt_snippet = Column(Text)
    negative_snippet = Column(Text)
    thumbnail = Column(String(200))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'prompt_snippet': self.prompt_snippet or '',
            'negative_snippet': self.negative_snippet or '',
            'thumbnail': self.thumbnail or '',
            'sort_order': self.sort_order,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    return [r.to_dict() for r in db_session.query(Perspective).order_by(Perspective.sort_order).all()]

def get_by_id(pid):
    row = db_session.query(Perspective).get(pid)
    return row.to_dict() if row else None

def create(**kwargs):
    obj = Perspective(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(pid, **kwargs):
    obj = db_session.query(Perspective).get(pid)
    if not obj:
        return None
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(pid):
    obj = db_session.query(Perspective).get(pid)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    if db_session.query(Perspective).count() > 0:
        return
    json_path = Path('data/seed/perspectives_seed.json')
    if not json_path.exists():
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('perspectives', data) if isinstance(data, dict) else data
    for item in items:
        db_session.add(Perspective(
            name=item['name'],
            prompt_snippet=item.get('prompt_snippet', ''),
            negative_snippet=item.get('negative_snippet', ''),
            thumbnail=item.get('thumbnail', ''),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(Perspective).count()} perspectives")
