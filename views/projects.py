"""
MekanAI Projects Views
Page rendering and API endpoints for project management
"""
from flask import render_template, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import models.project as project_model
import models.image as image_model

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}


def register_routes(bp):
    """Register project page and API routes"""

    # ── Page Routes ─────────────────────────────────────

    @bp.route('/projects')
    def projects():
        """Projects listing page"""
        project_list = project_model.get_all()
        for p in project_list:
            p['image_count'] = image_model.count_by_project(p['id'])
            latest = image_model.get_latest_by_project(p['id'])
            p['latest_image'] = latest['filename'] if latest else None
        return render_template('projects.html', active_page='projects', projects=project_list)

    @bp.route('/projects/<int:project_id>')
    def project_detail(project_id):
        """Single project detail page - shows project images"""
        project = project_model.get_by_id(project_id)
        if not project:
            abort(404)
        images = image_model.get_root_by_project(project_id)
        return render_template('project_detail.html', active_page='projects', project=project, images=images)

    @bp.route('/projects/<int:project_id>/images/<path:filename>')
    def project_image(project_id, filename):
        """Serve project image files"""
        folder = project_model.get_project_path(project_id)
        if not folder or not folder.exists():
            abort(404)
        return send_from_directory(str(folder), filename)

    # ── Project API ─────────────────────────────────────

    @bp.route('/api/projects', methods=['GET'])
    def api_list_projects():
        """Get all projects (JSON)"""
        try:
            projects = project_model.get_all()
            return jsonify({'status': 'success', 'projects': projects})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/api/projects', methods=['POST'])
    def api_create_project():
        """Create a new project"""
        data = request.json
        if not data or not data.get('name'):
            return jsonify({'status': 'error', 'message': 'Proje adı gerekli'}), 400

        name = data['name'].strip()
        description = data.get('description', '').strip()

        try:
            project = project_model.create(name, description)
            return jsonify({'status': 'success', 'project': project}), 201
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/api/projects/<int:project_id>', methods=['PUT'])
    def api_update_project(project_id):
        """Update project name and/or description"""
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'Veri gerekli'}), 400
        try:
            project = project_model.update(
                project_id,
                name=data.get('name'),
                description=data.get('description')
            )
            if not project:
                return jsonify({'status': 'error', 'message': 'Proje bulunamadı'}), 404
            return jsonify({'status': 'success', 'project': project})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
    def api_delete_project(project_id):
        """Delete project + all images + folder"""
        try:
            project_model.delete(project_id)
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # ── Image Upload API ────────────────────────────────

    @bp.route('/api/projects/<int:project_id>/upload', methods=['POST'])
    def api_upload_images(project_id):
        """Upload multiple images to a project + create DB records"""
        folder = project_model.get_project_path(project_id)
        if not folder:
            return jsonify({'status': 'error', 'message': 'Proje bulunamadı'}), 404

        files = request.files.getlist('images')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'status': 'error', 'message': 'Dosya seçilmedi'}), 400

        saved = []
        skipped = []
        for f in files:
            if not f.filename:
                continue
            ext = '.' + f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
            if ext not in ALLOWED_EXTENSIONS:
                skipped.append(f.filename)
                continue

            filename = secure_filename(f.filename)
            dest = folder / filename
            # Aynı isim varsa numaralandır
            counter = 1
            stem = dest.stem
            while dest.exists():
                dest = folder / f"{stem}_{counter}{dest.suffix}"
                counter += 1

            f.save(str(dest))

            # DB kaydı oluştur
            image_model.create(
                project_id=project_id,
                filename=dest.name,
                settings={'source': 'upload'}
            )
            saved.append(dest.name)

        return jsonify({
            'status': 'success',
            'saved': saved,
            'skipped': skipped,
            'count': len(saved)
        })

    # ── Image Delete API ────────────────────────────────

    @bp.route('/api/images/<int:image_id>', methods=['DELETE'])
    def api_delete_image(image_id):
        """Delete single image"""
        try:
            result = image_model.delete(image_id)
            if not result:
                return jsonify({'status': 'error', 'message': 'Görsel bulunamadı'}), 404
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/api/images/<int:image_id>/children', methods=['GET'])
    def api_image_children(image_id):
        """Get child (derivative) images of a given image"""
        try:
            children = image_model.get_children(image_id)
            return jsonify({'status': 'success', 'items': children, 'count': len(children)})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/api/images/delete-multiple', methods=['POST'])
    def api_delete_images():
        """Delete multiple images by ID list"""
        data = request.json
        if not data or not data.get('ids'):
            return jsonify({'status': 'error', 'message': 'Görsel ID listesi gerekli'}), 400

        try:
            deleted = image_model.delete_multiple(data['ids'])
            return jsonify({'status': 'success', 'deleted': deleted, 'count': len(deleted)})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
