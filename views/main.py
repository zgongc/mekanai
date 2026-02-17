"""
MekanAI Main Views
Page routes: home, canvas, floorplan, settings
"""
from flask import render_template, request
import models.image as image_model
import models.project as project_model
import models.ai_provider as provider_model
import models.ai_model as ai_model_model
import models.style as style_model
import models.perspective as perspective_model
import models.ratio as ratio_model
import models.lighting as lighting_model


def register_routes(bp):
    """Register main page routes"""

    @bp.route('/')
    def home():
        return render_template('home.html', active_page='home')

    @bp.route('/canvas')
    def canvas():
        providers = provider_model.get_enabled()
        models = ai_model_model.get_generatable()
        styles = style_model.get_all()
        perspectives = perspective_model.get_all()
        ratios = ratio_model.get_all()
        lightings = lighting_model.get_all()
        return render_template('canvas.html', active_page='canvas',
                               providers=providers, ai_models=models, styles=styles,
                               perspectives=perspectives, ratios=ratios, lightings=lightings)

    @bp.route('/sketch')
    def sketch():
        image = None
        project = None
        image_id = request.args.get('image', type=int)
        if image_id:
            image = image_model.get_by_id(image_id)
            if image:
                project = project_model.get_by_id(image['project_id'])
        providers = provider_model.get_enabled()
        models = ai_model_model.get_generatable()
        styles = style_model.get_all()
        perspectives = perspective_model.get_all()
        ratios = ratio_model.get_all()
        lightings = lighting_model.get_all()
        return render_template('sketch.html', active_page='sketch',
                               image=image, project=project,
                               providers=providers, ai_models=models, styles=styles,
                               perspectives=perspectives, ratios=ratios, lightings=lightings)

    @bp.route('/enhance')
    def enhance():
        image = None
        project = None
        image_id = request.args.get('image', type=int)
        if image_id:
            image = image_model.get_by_id(image_id)
            if image:
                project = project_model.get_by_id(image['project_id'])

        providers = provider_model.get_enabled()
        upscale_models = ai_model_model.get_upscale_capable()
        # Only show providers that have upscale models or are local (dynamic SD WebUI upscalers)
        upscale_provider_ids = {m['provider_id'] for m in upscale_models}
        enhance_providers = [p for p in providers if p['id'] in upscale_provider_ids or p['key'] in ('local', 'comfyui')]
        return render_template('enhance.html', active_page='enhance',
                               image=image, project=project,
                               providers=enhance_providers, upscale_models=upscale_models)

    @bp.route('/floorplan')
    def floorplan():
        image = None
        project = None
        image_id = request.args.get('image', type=int)
        if image_id:
            image = image_model.get_by_id(image_id)
            if image:
                project = project_model.get_by_id(image['project_id'])
        providers = provider_model.get_enabled()
        models = ai_model_model.get_generatable()
        return render_template('floorplan.html', active_page='floorplan',
                               image=image, project=project,
                               providers=providers, ai_models=models)

    @bp.route('/help')
    def help_page():
        return render_template('help.html', active_page='help')

    @bp.route('/settings')
    def settings():
        return render_template('settings/index.html', active_page='settings')
