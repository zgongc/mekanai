"""
api/sd_generator.py
MekanAI - SD WebUI Image Generation Service

Connects to Stable Diffusion WebUI Forge API on local network.
Supports txt2img with ControlNet (depth_midas) for interior/exterior redesign.

Workflow:
    1. User uploads a room photo (source image)
    2. ControlNet extracts depth map via depth_midas
    3. SD generates new image guided by depth + prompt

Usage:
    from api.sd_generator import AIGenerator

    gen = AIGenerator()
    # Without source image (pure txt2img)
    result = gen.generate(prompt="modern living room")
    # With source image (ControlNet depth)
    result = gen.generate(prompt="modern living room", source_image_path="path/to/room.jpg")
"""

import requests
import base64
import time
import json
from pathlib import Path
import models.ai_provider as provider_model


class AIGenerator:
    """Stable Diffusion WebUI Forge API client with ControlNet support"""

    def __init__(self):
        self.timeout = 180  # ControlNet + generation can take time

    def _get_base_url(self):
        """Get SD WebUI base URL from ai_providers table (local provider)"""
        provider = provider_model.get_by_key('local')
        if provider and provider.get('base_url'):
            return provider['base_url'].rstrip('/')
        raise ConnectionError("SD WebUI yapılandırılmamış. Settings > Providers'dan URL ayarlayın.")

    def _encode_image(self, image_path):
        """Read image file and return base64 string"""
        path = Path(image_path)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _request(self, endpoint, payload):
        """Send request to SD WebUI and handle response"""
        url = self._get_base_url()
        try:
            start = time.time()
            r = requests.post(
                f"{url}{endpoint}",
                json=payload,
                timeout=self.timeout
            )
            r.raise_for_status()
            elapsed = round(time.time() - start, 1)

            data = r.json()
            if not data.get('images'):
                return {"error": "Görsel oluşturulamadı - boş yanıt"}

            # Parse info for actual seed
            actual_seed = -1
            info_str = data.get('info', '')
            if info_str:
                try:
                    info = json.loads(info_str) if isinstance(info_str, str) else info_str
                    actual_seed = info.get('seed', -1)
                except (json.JSONDecodeError, TypeError):
                    pass

            return {
                "image_base64": data['images'][0],
                "seed": actual_seed,
                "elapsed": elapsed,
            }

        except requests.exceptions.ConnectionError:
            return {"error": f"SD WebUI bağlantı hatası: {url}"}
        except requests.exceptions.Timeout:
            return {"error": "Zaman aşımı - görsel oluşturma çok uzun sürdü"}
        except requests.exceptions.HTTPError as e:
            msg = str(e)
            try:
                body = e.response.json()
                detail = body.get('detail', '') or body.get('error', '')
                if detail:
                    msg = str(detail)
            except Exception:
                # JSON parse failed, try raw text
                try:
                    text = e.response.text[:500]
                    if text:
                        msg = text
                except Exception:
                    pass
            return {"error": f"SD WebUI hatası: {msg}"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    # ── Main Generation Method ───────────────────────

    def generate(self, prompt, negative_prompt="", width=768, height=512,
                 steps=30, cfg_scale=7.0, seed=-1, sampler="DPM++ SDE",
                 scheduler="Karras", source_image_path=None,
                 controlnet_module="depth_midas", controlnet_model="control_sd15_depth",
                 controlnet_weight=1.0, denoising_strength=0.75):
        """
        Generate image - with or without ControlNet source image.

        If source_image_path is provided:
            Uses txt2img + ControlNet (depth_midas) to redesign the room
        If no source image:
            Uses plain txt2img

        Args:
            prompt: Text description of desired output
            source_image_path: Path to source room photo (optional)
            controlnet_module: ControlNet preprocessor (default: depth_midas)
            controlnet_model: ControlNet model name (default: control_sd15_depth)

        Returns:
            dict with 'image_base64', 'seed', 'elapsed' on success
            dict with 'error' on failure
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "low quality, blurry, distorted, deformed, watermark, text",
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "sampler_name": sampler,
            "scheduler": scheduler,
            "batch_size": 1,
            "n_iter": 1,
        }

        # ControlNet with source image
        if source_image_path:
            img_b64 = self._encode_image(source_image_path)
            if not img_b64:
                return {"error": f"Kaynak görsel bulunamadı: {source_image_path}"}

            # Find matching ControlNet model for current SD architecture
            cn_model = self._find_controlnet_model(controlnet_model, controlnet_module)

            payload["alwayson_scripts"] = {
                "controlnet": {
                    "args": [
                        {
                            "enabled": True,
                            "module": controlnet_module,
                            "model": cn_model,
                            "weight": controlnet_weight,
                            "image": img_b64,
                            "resize_mode": 1,  # Crop and Resize
                            "processor_res": 512,
                            "threshold_a": 0.5,
                            "threshold_b": 0.5,
                            "guidance_start": 0.0,
                            "guidance_end": 1.0,
                            "pixel_perfect": False,
                            "control_mode": 0,  # Balanced
                        }
                    ]
                }
            }

        return self._request("/sdapi/v1/txt2img", payload)

    # ── ControlNet Helpers ───────────────────────────

    def _is_sdxl_loaded(self):
        """Check if currently loaded SD model is SDXL based"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/sdapi/v1/options", timeout=10)
            r.raise_for_status()
            model_name = r.json().get('sd_model_checkpoint', '').lower()
            return any(tag in model_name for tag in ['xl', 'sdxl', 'pony', 'juggernaut_xl'])
        except Exception:
            return False

    def _find_controlnet_model(self, model_name, controlnet_module="depth"):
        """
        Find matching ControlNet model from server.
        Auto-detects SD 1.5 vs SDXL and picks the right variant.
        """
        models = self.get_controlnet_models()
        if not models:
            return model_name

        is_xl = self._is_sdxl_loaded()

        # Extract the task type from module name (depth, canny, lineart, seg)
        task = controlnet_module.split('_')[0] if controlnet_module else 'depth'

        # Try to find a matching model for the right architecture
        best = None
        for m in models:
            ml = m.lower()
            if task not in ml:
                continue
            model_is_xl = any(tag in ml for tag in ['xl', 'sdxl', 'union'])
            if is_xl == model_is_xl:
                best = m
                break

        if best:
            return best

        # Fallback: any model matching the task
        for m in models:
            if task in m.lower():
                return m

        # Last resort: return as-is
        return model_name

    def get_controlnet_models(self):
        """Get available ControlNet models from server"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/controlnet/model_list", timeout=10)
            r.raise_for_status()
            return r.json().get('model_list', [])
        except Exception:
            return []

    def get_controlnet_modules(self):
        """Get available ControlNet preprocessor modules"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/controlnet/module_list", timeout=10)
            r.raise_for_status()
            return r.json().get('module_list', [])
        except Exception:
            return []

    # ── Model Switching ─────────────────────────────

    def set_model(self, model_key):
        """Switch active SD model by matching model_key to available checkpoints"""
        models = self.get_models()
        if not models:
            return False

        # Find matching model (partial match on key)
        match = None
        key_lower = model_key.lower().replace('_', '').replace('-', '')
        for title in models:
            title_lower = title.lower().replace('_', '').replace('-', '')
            if key_lower in title_lower:
                match = title
                break

        if not match:
            return False

        try:
            url = self._get_base_url()
            r = requests.post(f"{url}/sdapi/v1/options",
                              json={"sd_model_checkpoint": match}, timeout=60)
            r.raise_for_status()
            return True
        except Exception:
            return False

    # ── Status & Info ────────────────────────────────

    def check_connection(self):
        """Check if SD WebUI is reachable"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/sdapi/v1/options", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_models(self):
        """Get available SD models"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/sdapi/v1/sd-models", timeout=10)
            r.raise_for_status()
            return [m['title'] for m in r.json()]
        except Exception:
            return []

    def get_samplers(self):
        """Get available samplers"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/sdapi/v1/samplers", timeout=10)
            r.raise_for_status()
            return [s['name'] for s in r.json()]
        except Exception:
            return []

    # ── Upscale / Enhance ─────────────────────────────

    def get_upscalers(self):
        """Get available upscaler models from SD WebUI"""
        try:
            url = self._get_base_url()
            r = requests.get(f"{url}/sdapi/v1/upscalers", timeout=10)
            r.raise_for_status()
            return [u['name'] for u in r.json() if u['name'] != 'None']
        except Exception:
            return []

    def upscale(self, image_base64, upscaler_1="R-ESRGAN 4x+",
                upscaling_resize=2, upscaler_2="", upscaler_2_visibility=0.0):
        """
        Upscale image via SD WebUI extras API.

        Args:
            image_base64: Source image as base64 string
            upscaler_1: Primary upscaler model name
            upscaling_resize: Scale factor (1-8)
            upscaler_2: Optional second upscaler for blending
            upscaler_2_visibility: Blend ratio for second upscaler (0-1)

        Returns:
            dict with 'image_base64', 'elapsed' on success
            dict with 'error' on failure
        """
        url = self._get_base_url()
        payload = {
            "image": image_base64,
            "resize_mode": 0,  # 0 = Scale by factor
            "upscaling_resize": upscaling_resize,
            "upscaler_1": upscaler_1,
            "upscaler_2": upscaler_2 or "None",
            "extras_upscaler_2_visibility": upscaler_2_visibility,
        }

        try:
            start = time.time()
            r = requests.post(
                f"{url}/sdapi/v1/extra-single-image",
                json=payload,
                timeout=self.timeout
            )
            r.raise_for_status()
            elapsed = round(time.time() - start, 1)

            data = r.json()
            image = data.get('image')
            if not image:
                return {"error": "Upscale sonucu boş döndü"}

            return {
                "image_base64": image,
                "elapsed": elapsed,
            }

        except requests.exceptions.ConnectionError:
            return {"error": f"SD WebUI bağlantı hatası: {url}"}
        except requests.exceptions.Timeout:
            return {"error": "Zaman aşımı - upscale işlemi çok uzun sürdü"}
        except requests.exceptions.HTTPError as e:
            msg = str(e)
            try:
                body = e.response.json()
                detail = body.get('detail', '') or body.get('error', '')
                if detail:
                    msg = str(detail)
            except Exception:
                try:
                    text = e.response.text[:500]
                    if text:
                        msg = text
                except Exception:
                    pass
            return {"error": f"SD WebUI hatası: {msg}"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    def save_image(self, image_base64, save_path):
        """Save base64 image to disk"""
        img_data = base64.b64decode(image_base64)
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(img_data)
        return path
