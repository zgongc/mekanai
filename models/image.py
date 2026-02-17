"""
MekanAI - Image Model & CRUD
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class Image(Base):
    """Image metadata - stores generation settings as JSON"""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(Integer, ForeignKey('images.id', ondelete='SET NULL'), nullable=True, index=True)
    filename = Column(String(300), nullable=False)
    settings = Column(Text, default='{}')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referential relationship: parent ← children
    children = relationship('Image', backref=backref('parent', remote_side=[id]),
                            cascade='all', passive_deletes=True)

    def to_dict(self):
        settings = self.settings or '{}'
        if isinstance(settings, str):
            try:
                settings = json.loads(settings)
            except (json.JSONDecodeError, TypeError):
                settings = {}
        return {
            'id': self.id,
            'project_id': self.project_id,
            'parent_id': self.parent_id,
            'filename': self.filename,
            'settings': settings,
            'child_count': len(self.children) if self.children else 0,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None,
        }


# ============================================
# CRUD
# ============================================
def get_by_project(project_id):
    rows = db_session.query(Image).filter(Image.project_id == project_id)\
        .order_by(Image.created_at.desc()).all()
    return [r.to_dict() for r in rows]


def get_root_by_project(project_id):
    """Get only root images (uploaded, no parent) for a project"""
    rows = db_session.query(Image).filter(
        Image.project_id == project_id,
        Image.parent_id.is_(None)
    ).order_by(Image.created_at.desc()).all()
    return [r.to_dict() for r in rows]


def get_children(image_id):
    """Get child images (derivatives) of a given image"""
    rows = db_session.query(Image).filter(Image.parent_id == image_id)\
        .order_by(Image.created_at.desc()).all()
    return [r.to_dict() for r in rows]


def get_by_id(image_id):
    row = db_session.query(Image).get(image_id)
    return row.to_dict() if row else None


def count_by_project(project_id):
    return db_session.query(Image).filter(Image.project_id == project_id).count()


def get_latest_by_project(project_id):
    """Get the most recent image for a project (for thumbnail)"""
    row = db_session.query(Image).filter(Image.project_id == project_id)\
        .order_by(Image.created_at.desc()).first()
    return row.to_dict() if row else None


def create(project_id, filename, settings=None, parent_id=None):
    settings_json = json.dumps(settings or {}, ensure_ascii=False)
    image = Image(project_id=project_id, filename=filename, settings=settings_json, parent_id=parent_id)
    db_session.add(image)
    db_session.commit()
    return image.to_dict()


def update_settings(image_id, settings):
    image = db_session.query(Image).get(image_id)
    if not image:
        return None
    image.settings = json.dumps(settings, ensure_ascii=False)
    image.updated_at = datetime.utcnow()
    db_session.commit()
    return image.to_dict()


def delete(image_id):
    image = db_session.query(Image).get(image_id)
    if not image:
        return False
    _delete_file(image.project_id, image.filename)
    db_session.delete(image)
    db_session.commit()
    return True


def delete_multiple(image_ids):
    deleted = []
    for image_id in image_ids:
        if delete(image_id):
            deleted.append(image_id)
    return deleted


def delete_by_project(project_id):
    db_session.query(Image).filter(Image.project_id == project_id).delete()
    db_session.commit()
    return True


# ============================================
# FILESYSTEM
# ============================================
def _delete_file(project_id, filename):
    from .project import get_project_path
    folder = get_project_path(project_id)
    if folder:
        file_path = folder / filename
        if file_path.exists():
            file_path.unlink()
