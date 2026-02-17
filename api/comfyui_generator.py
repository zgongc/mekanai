"""
api/comfyui_generator.py
MekanAI - ComfyUI Image Generation Service

Connects to ComfyUI API for image generation.
Queue-based architecture: POST /prompt → poll /history → GET /view

Supports:
    - txt2img: Text-to-image generation
    - img2img: Image-to-image with source (denoise-based)
    - controlnet: ControlNet-guided generation (depth, canny, lineart, etc.)
    - upscale: Image upscaling with ESRGAN models

Usage:
    from api.comfyui_generator import ComfyUIGenerator

    gen = ComfyUIGenerator()
    result = gen.generate(prompt="modern living room")
    result = gen.generate(prompt="modern living room", source_image_path="room.jpg")
    result = gen.generate_controlnet(prompt="...", source_image_path="plan.png", controlnet_module="depth_midas")
"""

import requests
import base64
import time
import random
from uuid import uuid4
from pathlib import Path
import models.ai_provider as provider_model


class ComfyUIGenerator:
    """ComfyUI API client with workflow-based generation"""

    # SD WebUI sampler name → ComfyUI sampler name
    SAMPLER_MAP = {
        'Euler': 'euler',
        'Euler a': 'euler_ancestral',
        'Heun': 'heun',
        'DPM2': 'dpm_2',
        'DPM2 a': 'dpm_2_ancestral',
        'LMS': 'lms',
        'DPM++ 2M': 'dpmpp_2m',
        'DPM++ SDE': 'dpmpp_sde',
        'DPM++ 2S a': 'dpmpp_2s_ancestral',
        'DPM++ 3M SDE': 'dpmpp_3m_sde',
        'DDIM': 'ddim',
        'UniPC': 'uni_pc',
        'LCM': 'lcm',
    }

    # SD WebUI scheduler → ComfyUI scheduler
    SCHEDULER_MAP = {
        'Karras': 'karras',
        'Exponential': 'exponential',
        'SGM Uniform': 'sgm_uniform',
        'Automatic': 'normal',
    }

    # SD WebUI ControlNet preprocessor → ComfyUI preprocessor node + ControlNet model pattern
    CONTROLNET_MAP = {
        'depth_midas': {
            'preprocessor': 'MiDaS-DepthMapPreprocessor',
            'model_pattern': 'depth',
        },
        'depth_zoe': {
            'preprocessor': 'Zoe-DepthMapPreprocessor',
            'model_pattern': 'depth',
        },
        'canny': {
            'preprocessor': 'CannyEdgePreprocessor',
            'model_pattern': 'canny',
        },
        'lineart': {
            'preprocessor': 'LineArtPreprocessor',
            'model_pattern': 'lineart',
        },
        'seg_ofade20k': {
            'preprocessor': 'OneFormer-ADE20K-SemSegPreprocessor',
            'model_pattern': 'seg',
        },
    }

    def __init__(self):
        self.timeout = 300  # Generation can take time
        self.client_id = str(uuid4())

    def _get_base_url(self):
        """Get ComfyUI base URL from ai_providers table"""
        provider = provider_model.get_by_key('comfyui')
        if provider and provider.get('base_url'):
            return provider['base_url'].rstrip('/')
        raise ConnectionError("ComfyUI yapılandırılmamış. Settings > Providers'dan URL ayarlayın.")

    # ── Main Generation Method ───────────────────────

    def generate(self, prompt, negative_prompt="", width=512, height=512,
                 steps=20, cfg_scale=7.0, seed=-1, sampler="euler",
                 scheduler="normal", model="", source_image_path=None,
                 denoising_strength=0.75):
        """
        Generate image via ComfyUI workflow.

        If source_image_path provided → img2img (VAEEncode + denoise)
        Otherwise → txt2img (EmptyLatentImage)

        Args:
            prompt: Text description
            model: Checkpoint name or search pattern
            source_image_path: Path to source image for img2img
            denoising_strength: Denoise level for img2img (0-1)

        Returns:
            dict with 'image_base64', 'seed', 'elapsed' on success
            dict with 'error' on failure
        """
        # Map sampler/scheduler from SD WebUI format
        comfy_sampler = self._map_sampler(sampler)
        comfy_scheduler = self._map_scheduler(scheduler)

        if seed == -1:
            seed = random.randint(0, 2**63 - 1)

        # Find checkpoint name on server
        checkpoint = self._resolve_checkpoint(model)
        if not checkpoint:
            return {"error": f"ComfyUI'de checkpoint bulunamadı: {model}"}

        try:
            if source_image_path:
                # Upload source image to ComfyUI
                uploaded = self._upload_image(source_image_path)
                if not uploaded:
                    return {"error": "Kaynak görsel ComfyUI'ye yüklenemedi"}

                workflow = self._build_img2img_workflow(
                    prompt=prompt, negative_prompt=negative_prompt,
                    checkpoint=checkpoint, width=width, height=height,
                    steps=steps, cfg_scale=cfg_scale, seed=seed,
                    sampler=comfy_sampler, scheduler=comfy_scheduler,
                    image_name=uploaded, denoise=denoising_strength,
                )
            else:
                workflow = self._build_txt2img_workflow(
                    prompt=prompt, negative_prompt=negative_prompt,
                    checkpoint=checkpoint, width=width, height=height,
                    steps=steps, cfg_scale=cfg_scale, seed=seed,
                    sampler=comfy_sampler, scheduler=comfy_scheduler,
                )

            # Queue workflow
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                return {"error": "ComfyUI'ye workflow gönderilemedi"}

            # Wait for result
            return self._wait_for_result(prompt_id, seed)

        except ConnectionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"ComfyUI hatası: {str(e)}"}

    # ── Workflow Builders ────────────────────────────

    def _build_txt2img_workflow(self, prompt, negative_prompt, checkpoint,
                                 width, height, steps, cfg_scale, seed,
                                 sampler, scheduler):
        """Build standard txt2img workflow (CheckpointLoader → KSampler → VAEDecode → Save)"""
        return {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt or "", "clip": ["4", 1]}
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "MekanAI", "images": ["8", 0]}
            }
        }

    def _build_img2img_workflow(self, prompt, negative_prompt, checkpoint,
                                 width, height, steps, cfg_scale, seed,
                                 sampler, scheduler, image_name, denoise):
        """Build img2img workflow (LoadImage → VAEEncode → KSampler with denoise)"""
        return {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint}
            },
            "10": {
                "class_type": "LoadImage",
                "inputs": {"image": image_name}
            },
            "11": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["10", 0], "vae": ["4", 2]}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt or "", "clip": ["4", 1]}
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": denoise,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["11", 0]
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "MekanAI", "images": ["8", 0]}
            }
        }

    # ── ControlNet Generation ────────────────────────

    def generate_controlnet(self, prompt, negative_prompt="", width=512, height=512,
                            steps=20, cfg_scale=7.0, seed=-1, sampler="euler",
                            scheduler="normal", model="", source_image_path=None,
                            controlnet_module="depth_midas", controlnet_weight=1.0):
        """
        Generate image with ControlNet guidance via ComfyUI.

        Workflow: LoadImage → Preprocessor → ControlNetApply → KSampler → VAEDecode → Save

        Args:
            source_image_path: Path to source image (e.g., floor plan)
            controlnet_module: SD WebUI-style preprocessor name (depth_midas, canny, etc.)
            controlnet_weight: ControlNet strength (0-2)
        """
        comfy_sampler = self._map_sampler(sampler)
        comfy_scheduler = self._map_scheduler(scheduler)

        if seed == -1:
            seed = random.randint(0, 2**63 - 1)

        checkpoint = self._resolve_checkpoint(model)
        if not checkpoint:
            return {"error": f"ComfyUI'de checkpoint bulunamadı: {model}"}

        # Find matching ControlNet model (arch-aware)
        cn_info = self.CONTROLNET_MAP.get(controlnet_module, self.CONTROLNET_MAP['depth_midas'])
        cn_model = self._resolve_controlnet_model(cn_info['model_pattern'], checkpoint=checkpoint)
        if not cn_model:
            available = self.get_controlnet_models()
            avail_str = ', '.join(available[:5]) if available else 'hiç yok'
            return {"error": f"Checkpoint ({checkpoint}) ile uyumlu ControlNet modeli bulunamadı "
                    f"(aranan: {cn_info['model_pattern']}). "
                    f"Mevcut CN modelleri: {avail_str}. "
                    "Checkpoint tipine uygun ControlNet modeli ekleyin."}

        # Check if preprocessor node is available
        preprocessor = cn_info['preprocessor']
        has_preprocessor = self._check_node_exists(preprocessor)

        try:
            # Upload source image
            if not source_image_path:
                return {"error": "ControlNet için kaynak görsel gerekli"}

            uploaded = self._upload_image(source_image_path)
            if not uploaded:
                return {"error": "Kaynak görsel ComfyUI'ye yüklenemedi"}

            workflow = self._build_controlnet_workflow(
                prompt=prompt, negative_prompt=negative_prompt,
                checkpoint=checkpoint, width=width, height=height,
                steps=steps, cfg_scale=cfg_scale, seed=seed,
                sampler=comfy_sampler, scheduler=comfy_scheduler,
                image_name=uploaded, cn_model=cn_model,
                preprocessor=preprocessor if has_preprocessor else None,
                cn_weight=controlnet_weight,
            )

            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                return {"error": "ComfyUI'ye ControlNet workflow gönderilemedi"}

            return self._wait_for_result(prompt_id, seed)

        except ConnectionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"ComfyUI ControlNet hatası: {str(e)}"}

    def _build_controlnet_workflow(self, prompt, negative_prompt, checkpoint,
                                    width, height, steps, cfg_scale, seed,
                                    sampler, scheduler, image_name, cn_model,
                                    preprocessor, cn_weight):
        """Build ControlNet workflow.

        If preprocessor is available:
            LoadImage → Preprocessor → ControlNetApply → KSampler
        If no preprocessor (raw image used directly):
            LoadImage → ControlNetApply → KSampler
        """
        workflow = {
            # Checkpoint
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": checkpoint}
            },
            # Source image
            "10": {
                "class_type": "LoadImage",
                "inputs": {"image": image_name}
            },
            # ControlNet model
            "12": {
                "class_type": "ControlNetLoader",
                "inputs": {"control_net_name": cn_model}
            },
            # Positive prompt
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            # Negative prompt
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt or "", "clip": ["4", 1]}
            },
            # Empty latent (txt2img with CN guidance)
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1}
            },
            # KSampler
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["13", 0],  # ControlNet-applied positive
                    "negative": ["14", 1],  # ControlNet-applied negative
                    "latent_image": ["5", 0]
                }
            },
            # VAEDecode + Save
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "MekanAI_cn", "images": ["8", 0]}
            }
        }

        # Determine which image feeds into ControlNet (preprocessed or raw)
        if preprocessor:
            workflow["11"] = {
                "class_type": preprocessor,
                "inputs": {"image": ["10", 0]}
            }
            cn_image_ref = ["11", 0]
        else:
            cn_image_ref = ["10", 0]

        # ControlNetApplyAdvanced → applies CN to both positive and negative conditioning
        workflow["13"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "control_net": ["12", 0],
                "image": cn_image_ref,
                "strength": cn_weight,
                "start_percent": 0.0,
                "end_percent": 1.0,
            }
        }
        # Alias node 14 → output of 13 (negative is output index 1)
        workflow["14"] = workflow["13"]  # same node, negative output referenced via index

        # Actually, ControlNetApplyAdvanced outputs [positive, negative]
        # KSampler positive = ["13", 0], negative = ["13", 1]
        workflow["3"]["inputs"]["positive"] = ["13", 0]
        workflow["3"]["inputs"]["negative"] = ["13", 1]

        # Remove the dummy node 14
        if "14" in workflow and workflow["14"] is workflow["13"]:
            del workflow["14"]

        return workflow

    def _resolve_controlnet_model(self, pattern, checkpoint=""):
        """Find matching ControlNet model on ComfyUI by pattern + checkpoint arch.

        Detects base model architecture from checkpoint name (flux, sdxl, sd15)
        and prioritizes ControlNet models that match both the pattern AND the arch.
        Falls back to pattern-only match if no arch-specific match found.
        """
        models = self.get_controlnet_models()
        if not models:
            return None

        # Detect base model architecture from checkpoint name
        cp_lower = checkpoint.lower() if checkpoint else ""
        if "flux" in cp_lower:
            arch = "flux"
        elif any(x in cp_lower for x in ("sdxl", "xl_", "_xl")):
            arch = "sdxl"
        else:
            arch = "sd15"

        pattern_lower = pattern.lower()

        # First pass: match pattern + architecture
        for m in models:
            m_lower = m.lower()
            if pattern_lower in m_lower:
                if arch == "flux" and "flux" in m_lower:
                    return m
                elif arch == "sdxl" and ("sdxl" in m_lower or "xl" in m_lower):
                    return m
                elif arch == "sd15" and "flux" not in m_lower and "sdxl" not in m_lower and "xl" not in m_lower:
                    return m

        # Second pass: pattern only (any arch)
        for m in models:
            if pattern_lower in m.lower():
                return m

        # No match found
        return None

    def get_available_controlnet_options(self, checkpoint=""):
        """Return which CONTROLNET_MAP preprocessors have a matching CN model for the given checkpoint.

        Returns list of dicts: [{"value": "depth_midas", "label": "Depth (Midas)", "cn_model": "..."}]
        """
        LABELS = {
            'depth_midas': 'Depth (Midas)',
            'depth_zoe': 'Depth (Zoe)',
            'canny': 'Canny Edge',
            'lineart': 'Lineart',
            'seg_ofade20k': 'Segmentation',
        }

        result = []
        for key, info in self.CONTROLNET_MAP.items():
            cn_model = self._resolve_controlnet_model(info['model_pattern'], checkpoint=checkpoint)
            if cn_model:
                result.append({
                    'value': key,
                    'label': LABELS.get(key, key),
                    'cn_model': cn_model,
                })
        return result

    def _check_node_exists(self, node_class):
        """Check if a ComfyUI node class is available"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/object_info/{node_class}", timeout=5)
            return r.status_code == 200 and node_class in r.json()
        except Exception:
            return False

    def get_controlnet_models(self):
        """Get available ControlNet models from ComfyUI"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/object_info/ControlNetLoader", timeout=10)
            r.raise_for_status()
            data = r.json()
            inputs = data.get('ControlNetLoader', {}).get('input', {})
            required = inputs.get('required', {})
            return self._parse_combo_field(required.get('control_net_name', []))
        except Exception:
            return []

    # ── Upscale / Enhance ─────────────────────────────

    def upscale(self, image_base64, upscale_model="", scale=2):
        """
        Upscale image via ComfyUI UpscaleModelLoader + ImageUpscaleWithModel.

        Args:
            image_base64: Base64-encoded source image
            upscale_model: Upscale model name (e.g. RealESRGAN_x4plus.pth)
            scale: Target scale factor (1-8). After model upscale, image is
                   resized to original_size * scale.

        Returns:
            dict with 'image_base64', 'elapsed' on success
            dict with 'error' on failure
        """
        # Resolve upscale model
        if not upscale_model:
            models = self.get_upscale_models()
            if not models:
                return {"error": "ComfyUI'de upscale modeli bulunamadı"}
            upscale_model = models[0]

        # Get original image dimensions for scale calculation
        from io import BytesIO
        from PIL import Image
        img_bytes = base64.b64decode(image_base64)
        img = Image.open(BytesIO(img_bytes))
        orig_w, orig_h = img.size
        target_w = orig_w * scale
        target_h = orig_h * scale

        # Upload source image
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(img_bytes)
        tmp.close()

        uploaded = self._upload_image(tmp.name)
        if not uploaded:
            return {"error": "Kaynak görsel ComfyUI'ye yüklenemedi"}

        try:
            workflow = self._build_upscale_workflow(uploaded, upscale_model, target_w, target_h)

            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                return {"error": "ComfyUI'ye upscale workflow gönderilemedi"}

            return self._wait_for_result(prompt_id, seed=0)

        except ConnectionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"ComfyUI upscale hatası: {str(e)}"}

    def _build_upscale_workflow(self, image_name, upscale_model, target_w, target_h):
        """Build upscale workflow (LoadImage → UpscaleModel → ImageScale → Save)"""
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": image_name}
            },
            "2": {
                "class_type": "UpscaleModelLoader",
                "inputs": {"model_name": upscale_model}
            },
            "3": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["2", 0],
                    "image": ["1", 0]
                }
            },
            "5": {
                "class_type": "ImageScale",
                "inputs": {
                    "image": ["3", 0],
                    "upscale_method": "lanczos",
                    "width": target_w,
                    "height": target_h,
                    "crop": "disabled"
                }
            },
            "4": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "MekanAI_upscale", "images": ["5", 0]}
            }
        }

    def get_upscale_models(self):
        """Get available upscale models from ComfyUI"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/object_info/UpscaleModelLoader", timeout=10)
            r.raise_for_status()
            data = r.json()
            inputs = data.get('UpscaleModelLoader', {}).get('input', {})
            required = inputs.get('required', {})
            return self._parse_combo_field(required.get('model_name', []))
        except Exception:
            return []

    # ── ComfyUI API ──────────────────────────────────

    def _queue_prompt(self, workflow):
        """Queue a workflow on ComfyUI, returns prompt_id"""
        try:
            url = self._get_base_url()
            payload = {"prompt": workflow, "client_id": self.client_id}
            r = requests.post(f"{url}/prompt", json=payload, timeout=30)

            if r.status_code != 200:
                try:
                    err = r.json()
                    error_msg = err.get('error', {}).get('message', '')
                    node_errors = err.get('node_errors', {})
                    if node_errors:
                        for nid, nerr in node_errors.items():
                            msgs = nerr.get('errors', [])
                            if msgs:
                                error_msg = msgs[0].get('message', error_msg)
                                break
                    print(f"[!] ComfyUI queue error: {error_msg}")
                except Exception:
                    print(f"[!] ComfyUI queue error: HTTP {r.status_code}")
                return None

            return r.json().get('prompt_id')

        except requests.exceptions.ConnectionError:
            raise ConnectionError("ComfyUI bağlantı hatası — sunucu çalışıyor mu?")
        except Exception as e:
            print(f"[!] ComfyUI queue error: {e}")
            return None

    def _wait_for_result(self, prompt_id, seed):
        """Poll ComfyUI history until generation completes"""
        url = self._get_base_url()
        start = time.time()

        while time.time() - start < self.timeout:
            try:
                r = requests.get(f"{url}/history/{prompt_id}", timeout=10)
                if r.status_code != 200:
                    time.sleep(1)
                    continue

                data = r.json()
                if prompt_id not in data:
                    time.sleep(1)
                    continue

                history = data[prompt_id]
                status = history.get('status', {})

                # Check for errors
                if status.get('status_str') == 'error':
                    err_msg = "ComfyUI işlem hatası"
                    messages = status.get('messages', [])
                    for msg in messages:
                        if isinstance(msg, list) and len(msg) > 1:
                            if isinstance(msg[1], dict) and msg[1].get('exception_message'):
                                err_msg = msg[1]['exception_message']
                                break
                    return {"error": err_msg}

                # Still processing
                if not status.get('completed'):
                    time.sleep(1)
                    continue

                # Get output images from SaveImage node
                outputs = history.get('outputs', {})
                for node_id, output in outputs.items():
                    images = output.get('images', [])
                    if images:
                        img_info = images[0]
                        img_data = self._download_image(
                            img_info['filename'],
                            img_info.get('subfolder', ''),
                            img_info.get('type', 'output')
                        )
                        if img_data:
                            elapsed = round(time.time() - start, 1)
                            return {
                                "image_base64": base64.b64encode(img_data).decode('utf-8'),
                                "seed": seed,
                                "elapsed": elapsed,
                            }

                return {"error": "ComfyUI çıktı görseli bulunamadı"}

            except requests.exceptions.RequestException:
                time.sleep(2)

        return {"error": "ComfyUI zaman aşımı — üretim çok uzun sürdü"}

    def _download_image(self, filename, subfolder, type_):
        """Download generated image from ComfyUI output"""
        try:
            url = self._get_base_url()
            params = {"filename": filename, "subfolder": subfolder, "type": type_}
            r = requests.get(f"{url}/view", params=params, timeout=30)
            if r.status_code == 200:
                return r.content
        except Exception:
            pass
        return None

    def _upload_image(self, image_path):
        """Upload source image to ComfyUI input folder"""
        try:
            url = self._get_base_url()
            path = Path(image_path)
            if not path.exists():
                return None
            with open(path, 'rb') as f:
                files = {"image": (path.name, f, "image/png")}
                data = {"overwrite": "true"}
                r = requests.post(f"{url}/upload/image", files=files, data=data, timeout=30)
            if r.status_code == 200:
                return r.json().get('name')
        except Exception:
            pass
        return None

    # ── Model Resolution ─────────────────────────────

    def _resolve_checkpoint(self, model_key):
        """Find matching checkpoint on ComfyUI server by fuzzy matching"""
        checkpoints = self.get_checkpoints()

        if not model_key:
            return checkpoints[0] if checkpoints else None

        if not checkpoints:
            return model_key  # Return as-is, let ComfyUI report error

        # Exact match
        for cp in checkpoints:
            if cp == model_key:
                return cp

        # Fuzzy match (strip separators and compare)
        key_lower = model_key.lower().replace('_', '').replace('-', '').replace(' ', '')
        for cp in checkpoints:
            cp_lower = cp.lower().replace('_', '').replace('-', '').replace(' ', '')
            if key_lower in cp_lower:
                return cp

        # No match — return first available
        return checkpoints[0] if checkpoints else model_key

    # ── Sampler Mapping ──────────────────────────────

    def _map_sampler(self, sampler_name):
        """Map SD WebUI sampler name to ComfyUI format"""
        # Strip scheduler suffix first
        clean = sampler_name
        for sched in ['Karras', 'Exponential', 'SGM Uniform']:
            if clean.endswith(sched):
                clean = clean[:-len(sched)].strip()
                break

        mapped = self.SAMPLER_MAP.get(clean)
        if mapped:
            return mapped

        # Fallback: lowercase and normalize
        return clean.lower().replace(' ', '_').replace('++', 'pp').replace('+', 'p')

    def _map_scheduler(self, scheduler):
        """Map SD WebUI scheduler name to ComfyUI format"""
        return self.SCHEDULER_MAP.get(scheduler, scheduler.lower())

    # ── Status & Info ────────────────────────────────

    def check_connection(self):
        """Check if ComfyUI is reachable"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/system_stats", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_checkpoints(self):
        """Get available checkpoint models from ComfyUI"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/object_info/CheckpointLoaderSimple", timeout=10)
            r.raise_for_status()
            data = r.json()
            inputs = data.get('CheckpointLoaderSimple', {}).get('input', {})
            required = inputs.get('required', {})
            return self._parse_combo_field(required.get('ckpt_name', []))
        except Exception:
            return []

    def get_samplers(self):
        """Get available samplers from ComfyUI"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/object_info/KSampler", timeout=10)
            r.raise_for_status()
            data = r.json()
            inputs = data.get('KSampler', {}).get('input', {}).get('required', {})
            return self._parse_combo_field(inputs.get('sampler_name', []))
        except Exception:
            return []

    def get_schedulers(self):
        """Get available schedulers from ComfyUI"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/object_info/KSampler", timeout=10)
            r.raise_for_status()
            data = r.json()
            inputs = data.get('KSampler', {}).get('input', {}).get('required', {})
            return self._parse_combo_field(inputs.get('scheduler', []))
        except Exception:
            return []

    @staticmethod
    def _parse_combo_field(field):
        """Parse ComfyUI object_info combo field (handles both old and new format).

        Old format: [["option1", "option2"]]
        New format: ["COMBO", {"options": ["option1", "option2"]}]
        """
        if not field:
            return []
        # New format: first element is type string like "COMBO"
        if len(field) >= 2 and isinstance(field[0], str) and isinstance(field[1], dict):
            return field[1].get('options', [])
        # Old format: first element is the list of options
        if isinstance(field[0], list):
            return field[0]
        return []
