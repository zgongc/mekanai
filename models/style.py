"""
MekanAI - Style Model & CRUD
"""
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class Style(Base):
    """Visual style definitions for image generation"""
    __tablename__ = "styles"

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
    return [r.to_dict() for r in db_session.query(Style).order_by(Style.sort_order).all()]

def get_by_category(category):
    return [r.to_dict() for r in
            db_session.query(Style).filter(Style.category == category)
            .order_by(Style.sort_order).all()]

def get_by_id(style_id):
    row = db_session.query(Style).get(style_id)
    return row.to_dict() if row else None

def create(**kwargs):
    obj = Style(**kwargs)
    db_session.add(obj)
    db_session.commit()
    return obj.to_dict()

def update(style_id, **kwargs):
    obj = db_session.query(Style).get(style_id)
    if not obj:
        return None
    for k, v in kwargs.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db_session.commit()
    return obj.to_dict()

def delete(style_id):
    obj = db_session.query(Style).get(style_id)
    if not obj:
        return False
    db_session.delete(obj)
    db_session.commit()
    return True


# ============================================
# SEED
# ============================================
def seed_from_json():
    """Load styles from data/styles_seed.json if table is empty"""
    if db_session.query(Style).count() > 0:
        return
    json_path = Path('data/seed/styles_seed.json')
    if not json_path.exists():
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get('styles', []):
        db_session.add(Style(
            name=item['name'],
            category=item['category'],
            subcategory=item.get('subcategory'),
            prompt_snippet=item.get('prompt_snippet', ''),
            negative_snippet=item.get('negative_snippet', ''),
            thumbnail=item.get('thumbnail', ''),
            sort_order=item.get('sort_order', 0),
        ))
    db_session.commit()
    print(f"[+] Seeded {db_session.query(Style).count()} styles")
