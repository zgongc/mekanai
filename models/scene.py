"""
MekanAI - Scene Model & CRUD
"""
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class Scene(Base):
    """AI scene definitions (rooms, spaces, elements)"""
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

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'subcategory': self.subcategory,
            'prompt_snippet': self.prompt_snippet or '',
            'negative_snippet': self.negative_snippet or '',
            'thumbnail': self.thumbnail or '',
            'sort_order': self.sort_order,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    return [r.to_dict() for r in db_session.query(Scene).order_by(Scene.sort_order).all()]

def get_by_category(category):
    return [r.to_dict() for r in
            db_session.query(Scene).filter(Scene.category == category)
            .order_by(Scene.sort_order).all()]

def get_by_id(scene_id):
    row = db_session.query(Scene).get(scene_id)
    return row.to_dict() if row else None

def create(**kwargs):
    obj = Scene(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(scene_id, **kwargs):
    obj = db_session.query(Scene).get(scene_id)
    if not obj:
        return None
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(scene_id):
    obj = db_session.query(Scene).get(scene_id)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    if db_session.query(Scene).count() > 0:
        return
    json_path = Path('data/seed/scenes_seed.json')
    if not json_path.exists():
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get('scenes', []):
        db_session.add(Scene(
            name=item['name'],
            category=item['category'],
            subcategory=item.get('subcategory'),
            prompt_snippet=item.get('prompt_snippet', ''),
            negative_snippet=item.get('negative_snippet', ''),
            thumbnail=item.get('thumbnail', ''),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(Scene).count()} scenes")
