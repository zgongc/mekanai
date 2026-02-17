"""
MekanAI - Project Model & CRUD
"""
import re
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy import Column, Integer, String, Text, DateTime
from config import config
from .base import Base, db_session

# ============================================
# MODEL
# ============================================
class Project(Base):
    """User design projects"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    folder_name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'folder_name': self.folder_name,
            'description': self.description or '',
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None,
        }


# ============================================
# CRUD
# ============================================
def get_all():
    """Get all projects ordered by latest update"""
    rows = db_session.query(Project).order_by(Project.updated_at.desc()).all()
    return [r.to_dict() for r in rows]


def get_by_id(project_id):
    row = db_session.query(Project).get(project_id)
    return row.to_dict() if row else None


def create(name, description=''):
    folder_name = _generate_folder_name(name)
    projects_path = _get_projects_path()
    folder_path = projects_path / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)

    try:
        project = Project(name=name, folder_name=folder_name, description=description)
        db_session.add(project)
        db_session.commit()
        return project.to_dict()
    except Exception as e:
        db_session.rollback()
        if folder_path.exists() and not any(folder_path.iterdir()):
            folder_path.rmdir()
        raise e


def update(project_id, name=None, description=None):
    project = db_session.query(Project).get(project_id)
    if not project:
        return None
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    project.updated_at = datetime.utcnow()
    try:
        db_session.commit()
        return project.to_dict()
    except Exception:
        db_session.rollback()
        raise


def delete(project_id, delete_files=True):
    from .image import delete_by_project
    delete_by_project(project_id)

    project = db_session.query(Project).get(project_id)
    if not project:
        return False

    if delete_files:
        folder = get_project_path(project_id)
        if folder and folder.exists():
            shutil.rmtree(folder)

    db_session.delete(project)
    db_session.commit()
    return True


# ============================================
# FILESYSTEM
# ============================================
def get_project_path(project_id):
    project = db_session.query(Project).get(project_id)
    if not project:
        return None
    return _get_projects_path() / project.folder_name


def get_project_images(project_id):
    folder = get_project_path(project_id)
    if not folder or not folder.exists():
        return []
    exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
    return [
        {'filename': f.name, 'size': f.stat().st_size}
        for f in sorted(folder.iterdir()) if f.suffix.lower() in exts
    ]


# ============================================
# HELPERS
# ============================================
def _get_projects_path():
    p = Path(config.get('paths.projects', 'data/projects'))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _generate_folder_name(name):
    tr_map = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosuCGIOSU')
    folder = name.translate(tr_map).lower().strip()
    folder = re.sub(r'[^a-z0-9\s-]', '', folder)
    folder = re.sub(r'[\s]+', '_', folder)
    folder = re.sub(r'_+', '_', folder).strip('_')
    if not folder:
        folder = 'proje'
    base = folder
    counter = 1
    projects_path = _get_projects_path()
    while (projects_path / folder).exists():
        folder = f"{base}_{counter}"
        counter += 1
    return folder
