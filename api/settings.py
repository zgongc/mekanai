"""
MekanAI Settings API
Generic CRUD endpoints for all reference tables
"""
from flask import request, jsonify
import models.style as style_model
import models.scene as scene_model
import models.perspective as perspective_model
import models.lighting as lighting_model
import models.ratio as ratio_model
import models.ai_provider as ai_provider_model
import models.ai_model as ai_model_model
import models.mode as mode_model


TABLE_MAP = {
    'styles': style_model,
    'scenes': scene_model,
    'perspectives': perspective_model,
    'lightings': lighting_model,
    'ratios': ratio_model,
    'ai_providers': ai_provider_model,
    'ai_models': ai_model_model,
    'modes': mode_model,
}


def register_routes(bp):
    """Register settings CRUD API routes"""

    @bp.route('/settings/<table_name>', methods=['GET'])
    def settings_list(table_name):
        """List all records for a table"""
        model = TABLE_MAP.get(table_name)
        if not model:
            return jsonify({'status': 'error', 'message': f'Bilinmeyen tablo: {table_name}'}), 404
        try:
            items = model.get_all()
            return jsonify({'status': 'success', 'items': items, 'count': len(items)})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/settings/<table_name>', methods=['POST'])
    def settings_create(table_name):
        """Create a new record"""
        model = TABLE_MAP.get(table_name)
        if not model:
            return jsonify({'status': 'error', 'message': f'Bilinmeyen tablo: {table_name}'}), 404
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'Veri gerekli'}), 400
        try:
            item = model.create(**data)
            return jsonify({'status': 'success', 'item': item}), 201
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/settings/<table_name>/<int:item_id>', methods=['GET'])
    def settings_get(table_name, item_id):
        """Get a single record"""
        model = TABLE_MAP.get(table_name)
        if not model:
            return jsonify({'status': 'error', 'message': f'Bilinmeyen tablo: {table_name}'}), 404
        try:
            item = model.get_by_id(item_id)
            if not item:
                return jsonify({'status': 'error', 'message': 'Kayıt bulunamadı'}), 404
            return jsonify({'status': 'success', 'item': item})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/settings/<table_name>/<int:item_id>', methods=['PUT'])
    def settings_update(table_name, item_id):
        """Update a record"""
        model = TABLE_MAP.get(table_name)
        if not model:
            return jsonify({'status': 'error', 'message': f'Bilinmeyen tablo: {table_name}'}), 404
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'Veri gerekli'}), 400
        try:
            item = model.update(item_id, **data)
            if not item:
                return jsonify({'status': 'error', 'message': 'Kayıt bulunamadı'}), 404
            return jsonify({'status': 'success', 'item': item})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/settings/<table_name>/<int:item_id>', methods=['DELETE'])
    def settings_delete(table_name, item_id):
        """Delete a record"""
        model = TABLE_MAP.get(table_name)
        if not model:
            return jsonify({'status': 'error', 'message': f'Bilinmeyen tablo: {table_name}'}), 404
        try:
            result = model.delete(item_id)
            if not result:
                return jsonify({'status': 'error', 'message': 'Kayıt bulunamadı'}), 404
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
