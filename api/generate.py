"""
MekanAI Image Generation API
SD WebUI Forge + ControlNet + Cloud API (Gemini/Stability/OpenAI) integration
"""
from flask import request, jsonify, current_app
from api.sd_generator import AIGenerator
from api.gemini_generator import GeminiGenerator
from api.stability_generator import StabilityGenerator
from api.openai_generator import OpenAIGenerator
from api.grok_generator import GrokGenerator
from api.comfyui_generator import ComfyUIGenerator
import models.image as image_model
import models.project as project_model
import models.ai_model as ai_model_model
import models.ai_provider as provider_model
import models.style as style_model
import models.perspective as perspective_model
import models.lighting as lighting_model
import time


def register_routes(bp):
    """Register image generation API routes"""

    generator = AIGenerator()

    @bp.route('/generate-image', methods=['POST'])
    def generate_image():
        """
        Generate image via SD WebUI.
        If source image exists → ControlNet depth_midas + txt2img
        If no source image → plain txt2img
        """
        try:
            return _do_generate()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'status': 'error', 'message': f'Sunucu hatası: {str(e)}'}), 500

    def _do_generate():
        data = request.json
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({'status': 'error', 'message': 'Prompt gerekli'}), 400

        negative_prompt = data.get('negative_prompt', '')
        model = data.get('model', '')
        sampler = data.get('sampler', 'DPM++ 2M Karras')
        width = data.get('width', 768)
        height = data.get('height', 512)
        steps = data.get('steps', 30)
        cfg_scale = data.get('cfg_scale', 7.0)
        seed = data.get('seed', -1)
        style_id = data.get('style_id')
        perspective_id = data.get('perspective_id')
        lighting_id = data.get('lighting_id')
        project_id = data.get('project_id')
        source_image_id = data.get('source_image_id')
        controlnet_module = data.get('controlnet_module', 'depth_midas')
        controlnet_weight = data.get('controlnet_weight', 1.0)

        # Merge style snippets into prompt
        style_name = None
        if style_id:
            style = style_model.get_by_id(style_id)
            if style:
                style_name = style['name']
                if style.get('prompt_snippet'):
                    prompt = f"{prompt}, {style['prompt_snippet']}"
                if style.get('negative_snippet'):
                    negative_prompt = f"{negative_prompt}, {style['negative_snippet']}" if negative_prompt else style['negative_snippet']

        # Merge perspective snippets into prompt
        if perspective_id:
            perspective = perspective_model.get_by_id(perspective_id)
            if perspective:
                if perspective.get('prompt_snippet'):
                    prompt = f"{prompt}, {perspective['prompt_snippet']}"
                if perspective.get('negative_snippet'):
                    negative_prompt = f"{negative_prompt}, {perspective['negative_snippet']}" if negative_prompt else perspective['negative_snippet']

        # Merge lighting snippets into prompt
        if lighting_id:
            lighting = lighting_model.get_by_id(lighting_id)
            if lighting:
                if lighting.get('prompt_snippet'):
                    prompt = f"{prompt}, {lighting['prompt_snippet']}"
                if lighting.get('negative_snippet'):
                    negative_prompt = f"{negative_prompt}, {lighting['negative_snippet']}" if negative_prompt else lighting['negative_snippet']

        source_path = None

        # Detect provider: explicit provider_key > model-based detection
        model_info = ai_model_model.get_by_key(model) if model else None
        provider_key = data.get('provider_key') or None
        if not provider_key and model_info and model_info.get('provider'):
            provider_key = model_info['provider'].get('key')

        # ── ComfyUI (local, workflow-based) ──
        if provider_key == 'comfyui':
            comfyui_gen = ComfyUIGenerator()
            checkpoint_hint = model_info.get('api_model_id', model) if model_info else model

            # Source image for img2img / ControlNet
            source_path = None
            source_image_base64 = data.get('source_image_base64')
            if source_image_base64:
                import tempfile, base64
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp.write(base64.b64decode(source_image_base64))
                tmp.close()
                source_path = tmp.name
            elif source_image_id:
                source = image_model.get_by_id(source_image_id)
                if source:
                    folder = project_model.get_project_path(source['project_id'])
                    if folder:
                        src = folder / source['filename']
                        if src.exists():
                            source_path = str(src)

            # Parse sampler and scheduler
            sampler_name = sampler
            scheduler = "Automatic"
            for sched in ["Karras", "Exponential", "SGM Uniform"]:
                if sampler.endswith(sched):
                    sampler_name = sampler[:-len(sched)].strip()
                    scheduler = sched
                    break

            # ControlNet mode: when controlnet_module is specified and source image exists
            if controlnet_module and source_path:
                result = comfyui_gen.generate_controlnet(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg_scale=cfg_scale,
                    seed=seed,
                    sampler=sampler_name,
                    scheduler=scheduler,
                    model=checkpoint_hint,
                    source_image_path=source_path,
                    controlnet_module=controlnet_module,
                    controlnet_weight=controlnet_weight,
                )
            else:
                # Standard img2img or txt2img
                denoising_strength = data.get('denoising_strength', 0.75)
                result = comfyui_gen.generate(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg_scale=cfg_scale,
                    seed=seed,
                    sampler=sampler_name,
                    scheduler=scheduler,
                    model=checkpoint_hint,
                    source_image_path=source_path,
                    denoising_strength=denoising_strength,
                )

        # ── Cloud API ──
        elif provider_key and provider_key not in ('local', 'comfyui') and model_info.get('api_model_id'):
            provider = provider_model.get_by_key(provider_key)
            if not provider or not provider.get('api_key'):
                return jsonify({'status': 'error', 'message': f'{provider_key} API key ayarlanmamış. Settings > Providers\'dan ekleyin.'}), 400

            api_key = provider['api_key']
            base_url = provider.get('base_url')
            api_model_id = model_info['api_model_id']

            # Get source image for cloud img2img (floorplan, sketch)
            cloud_source_b64 = data.get('source_image_base64')
            if not cloud_source_b64 and source_image_id:
                source = image_model.get_by_id(source_image_id)
                if source:
                    folder = project_model.get_project_path(source['project_id'])
                    if folder:
                        src = folder / source['filename']
                        if src.exists():
                            import base64 as b64mod
                            cloud_source_b64 = b64mod.b64encode(src.read_bytes()).decode('utf-8')

            if provider_key == 'stability':
                cloud_gen = StabilityGenerator(
                    api_key=api_key,
                    base_url=base_url or 'https://api.stability.ai/v2beta'
                )
                result = cloud_gen.generate(
                    prompt=prompt,
                    model_id=api_model_id,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    seed=seed,
                    source_image_base64=cloud_source_b64,
                )
            elif provider_key == 'openai':
                cloud_gen = OpenAIGenerator(
                    api_key=api_key,
                    base_url=base_url or 'https://api.openai.com/v1'
                )
                result = cloud_gen.generate(
                    prompt=prompt,
                    model_id=api_model_id,
                    width=width,
                    height=height,
                )
            elif provider_key == 'grok':
                cloud_gen = GrokGenerator(
                    api_key=api_key,
                    base_url=base_url or 'https://api.x.ai/v1'
                )
                result = cloud_gen.generate(
                    prompt=prompt,
                    model_id=api_model_id,
                    width=width,
                    height=height,
                )
            else:
                # Gemini / Imagen (default cloud)
                cloud_gen = GeminiGenerator(
                    api_key=api_key,
                    base_url=base_url or 'https://generativelanguage.googleapis.com/v1beta'
                )
                result = cloud_gen.generate(
                    prompt=prompt,
                    model_id=api_model_id,
                    width=width,
                    height=height,
                )

        # ── Local SD WebUI ──
        else:
            # Switch SD WebUI model if specified
            if model:
                generator.set_model(model)

            # Find source image for ControlNet
            source_path = None
            source_image_base64 = data.get('source_image_base64')
            if source_image_base64:
                import tempfile, base64
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp.write(base64.b64decode(source_image_base64))
                tmp.close()
                source_path = tmp.name
            elif source_image_id:
                source = image_model.get_by_id(source_image_id)
                if source:
                    folder = project_model.get_project_path(source['project_id'])
                    if folder:
                        src = folder / source['filename']
                        if src.exists():
                            source_path = str(src)

            # Parse sampler name and scheduler
            sampler_name = sampler
            scheduler = "Automatic"
            for sched in ["Karras", "Exponential", "SGM Uniform"]:
                if sampler.endswith(sched):
                    sampler_name = sampler[:-len(sched)].strip()
                    scheduler = sched
                    break

            result = generator.generate(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                seed=seed,
                sampler=sampler_name,
                scheduler=scheduler,
                source_image_path=source_path,
                controlnet_module=controlnet_module,
                controlnet_weight=controlnet_weight,
            )

        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 500

        # Save to project if project_id provided
        saved_image = None
        if project_id:
            folder = project_model.get_project_path(project_id)
            if folder:
                filename = f"gen_{int(time.time())}.png"
                save_path = folder / filename
                generator.save_image(result['image_base64'], save_path)

                settings = {
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'model': model,
                    'sampler': sampler,
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'cfg_scale': cfg_scale,
                    'seed': result.get('seed', seed),
                    'style_id': style_id,
                    'style_name': style_name,
                    'perspective_id': perspective_id,
                    'lighting_id': lighting_id,
                    'source': 'controlnet_depth' if source_path else 'txt2img',
                    'source_image_id': source_image_id,
                }
                saved_image = image_model.create(
                    project_id=project_id,
                    filename=filename,
                    settings=settings,
                    parent_id=source_image_id,
                )

        return jsonify({
            'status': 'success',
            'image_base64': result['image_base64'],
            'seed': result.get('seed'),
            'elapsed': result.get('elapsed'),
            'saved_image': saved_image,
        })

    @bp.route('/sd-status', methods=['GET'])
    def sd_status():
        """Check SD WebUI connection + available models"""
        connected = generator.check_connection()
        data = {'status': 'success', 'connected': connected}
        if connected:
            data['models'] = generator.get_models()
            data['controlnet_models'] = generator.get_controlnet_models()
        return jsonify(data)

    @bp.route('/sketch-to-image', methods=['POST'])
    def sketch_to_image():
        """Convert sketch to rendered image via ControlNet"""
        # TODO: ControlNet scribble/lineart integration
        return jsonify({
            'status': 'success',
            'message': 'Sketch-to-image will be implemented'
        })

    @bp.route('/projects', methods=['GET'])
    def list_projects():
        """List all projects for the save-to-project modal"""
        projects = project_model.get_all()
        return jsonify({'status': 'success', 'projects': projects})

    @bp.route('/save-to-project', methods=['POST'])
    def save_to_project():
        """Save a base64 image to an existing project"""
        data = request.json
        project_id = data.get('project_id')
        image_base64 = data.get('image_base64')
        settings = data.get('settings', {})

        if not project_id or not image_base64:
            return jsonify({'status': 'error', 'message': 'project_id ve image_base64 gerekli'}), 400

        folder = project_model.get_project_path(project_id)
        if not folder:
            return jsonify({'status': 'error', 'message': 'Proje bulunamadı'}), 404

        filename = f"gen_{int(time.time())}.png"
        save_path = folder / filename
        generator.save_image(image_base64, save_path)

        saved_image = image_model.create(
            project_id=project_id,
            filename=filename,
            settings=settings,
        )

        return jsonify({'status': 'success', 'image': saved_image})

    @bp.route('/upscalers', methods=['GET'])
    def list_upscalers():
        """Get available upscaler models from SD WebUI"""
        upscalers = generator.get_upscalers()
        return jsonify({'status': 'success', 'upscalers': upscalers})

    @bp.route('/upscale', methods=['POST'])
    def upscale_image():
        """Upscale an image via SD WebUI or Cloud API"""
        data = request.json
        image_base64 = data.get('image_base64')
        if not image_base64:
            return jsonify({'status': 'error', 'message': 'image_base64 gerekli'}), 400

        provider_key = data.get('provider_key', 'local')
        model_key = data.get('model_key', '')

        # ── Cloud: Stability AI ──
        if provider_key == 'stability':
            provider = provider_model.get_by_key('stability')
            if not provider or not provider.get('api_key'):
                return jsonify({'status': 'error', 'message': 'Stability AI API key ayarlanmamış.'}), 400

            cloud_gen = StabilityGenerator(
                api_key=provider['api_key'],
                base_url=provider.get('base_url') or 'https://api.stability.ai/v2beta'
            )

            model_info = ai_model_model.get_by_key(model_key) if model_key else None
            api_model_id = model_info['api_model_id'] if model_info else 'conservative-upscale'

            if api_model_id == 'conservative-upscale':
                result = cloud_gen.upscale(
                    image_base64=image_base64,
                    prompt=data.get('prompt', ''),
                    creativity=data.get('creativity', 0.35),
                )
            else:
                # Structure control (img2img enhance)
                result = cloud_gen._generate_structure(
                    prompt=data.get('prompt', 'high quality, detailed, enhanced'),
                    source_image_base64=image_base64,
                )

        # ── ComfyUI ──
        elif provider_key == 'comfyui':
            comfyui_gen = ComfyUIGenerator()
            upscale_model = data.get('upscaler_1', '')
            scale = data.get('upscaling_resize', 2)
            result = comfyui_gen.upscale(
                image_base64=image_base64,
                upscale_model=upscale_model,
                scale=scale,
            )

        # ── Local: SD WebUI ──
        else:
            upscaler_1 = data.get('upscaler_1', 'R-ESRGAN 4x+')
            upscaling_resize = data.get('upscaling_resize', 2)
            upscaler_2 = data.get('upscaler_2', '')
            upscaler_2_visibility = data.get('upscaler_2_visibility', 0.0)

            result = generator.upscale(
                image_base64=image_base64,
                upscaler_1=upscaler_1,
                upscaling_resize=upscaling_resize,
                upscaler_2=upscaler_2,
                upscaler_2_visibility=upscaler_2_visibility,
            )

        if 'error' in result:
            return jsonify({'status': 'error', 'message': result['error']}), 500

        return jsonify({
            'status': 'success',
            'image_base64': result['image_base64'],
            'elapsed': result.get('elapsed'),
        })

    @bp.route('/comfyui-upscalers', methods=['GET'])
    def comfyui_upscalers():
        """Get available upscale models from ComfyUI"""
        comfyui_gen = ComfyUIGenerator()
        models = comfyui_gen.get_upscale_models()
        return jsonify({'status': 'success', 'upscalers': models})

    @bp.route('/comfyui-status', methods=['GET'])
    def comfyui_status():
        """Check ComfyUI connection + available checkpoints"""
        comfyui_gen = ComfyUIGenerator()
        connected = comfyui_gen.check_connection()
        data = {'status': 'success', 'connected': connected}
        if connected:
            data['checkpoints'] = comfyui_gen.get_checkpoints()
        return jsonify(data)

    @bp.route('/comfyui-checkpoints', methods=['GET'])
    def comfyui_checkpoints():
        """Get available ComfyUI checkpoint models"""
        comfyui_gen = ComfyUIGenerator()
        checkpoints = comfyui_gen.get_checkpoints()
        return jsonify({'status': 'success', 'checkpoints': checkpoints})

    @bp.route('/comfyui-controlnet-options', methods=['GET'])
    def comfyui_controlnet_options():
        """Get available ControlNet preprocessors filtered by checkpoint compatibility"""
        checkpoint = request.args.get('checkpoint', '')
        comfyui_gen = ComfyUIGenerator()
        options = comfyui_gen.get_available_controlnet_options(checkpoint=checkpoint)
        return jsonify({'status': 'success', 'options': options})

    @bp.route('/status', methods=['GET'])
    def api_status():
        """Check API and service status"""
        config = current_app.config.get('APP_CONFIG')
        return jsonify({
            'app': 'running',
            'version': config.get('system.version') if config else '1.0.0'
        })
