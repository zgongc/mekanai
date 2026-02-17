"""
api/stability_generator.py
MekanAI - Stability AI Image Generation

Supports v2beta API endpoints:
    - Stable Image Ultra: /stable-image/generate/ultra
    - Stable Image Core: /stable-image/generate/core
    - SD3.5: /stable-image/generate/sd3
    - Conservative Upscale: /stable-image/upscale/conservative
    - Structure Control: /stable-image/control/structure

Usage:
    from api.stability_generator import StabilityGenerator
    gen = StabilityGenerator(api_key="...", base_url="https://api.stability.ai/v2beta")
    result = gen.generate(prompt="modern living room", model_id="stable-image-core")
    result = gen.upscale(image_base64="...", prompt="high quality interior")
"""

import requests
import base64
import time


class StabilityGenerator:
    """Stability AI v2beta API client for image generation"""

    # Model ID → endpoint mapping
    ENDPOINTS = {
        'stable-image-ultra': 'stable-image/generate/ultra',
        'stable-image-core': 'stable-image/generate/core',
        'sd3.5-large': 'stable-image/generate/sd3',
        'sd3.5-medium': 'stable-image/generate/sd3',
        'sd3-large': 'stable-image/generate/sd3',
        'sd3-turbo': 'stable-image/generate/sd3',
    }

    def __init__(self, api_key, base_url="https://api.stability.ai/v2beta"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = 120

    def generate(self, prompt, model_id="stable-image-core",
                 negative_prompt="", width=None, height=None,
                 seed=-1, output_format="png", source_image_base64=None):
        """
        Generate image via Stability AI API.
        If source_image_base64 provided → structure control (img2img)
        Otherwise → text-to-image

        Returns:
            dict with 'image_base64', 'seed', 'elapsed' on success
            dict with 'error' on failure
        """
        # If source image provided, use structure control endpoint
        if source_image_base64:
            return self._generate_structure(
                prompt=prompt, source_image_base64=source_image_base64,
                negative_prompt=negative_prompt, seed=seed,
                output_format=output_format,
            )

        aspect_ratio = "1:1"
        if width and height:
            aspect_ratio = self._detect_aspect_ratio(width, height)

        endpoint = self.ENDPOINTS.get(model_id, 'stable-image/generate/core')
        url = f"{self.base_url}/{endpoint}"

        data = {
            "prompt": prompt,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio,
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed and seed > 0:
            data["seed"] = str(seed)

        # SD3 endpoint needs model parameter
        if 'sd3' in endpoint:
            data["model"] = model_id

        return self._post_request(url, data)

    def _generate_structure(self, prompt, source_image_base64,
                            negative_prompt="", seed=-1,
                            output_format="png", control_strength=0.7):
        """Generate via structure control endpoint (ControlNet-like img2img)"""
        url = f"{self.base_url}/stable-image/control/structure"

        image_bytes = base64.b64decode(source_image_base64)

        data = {
            "prompt": prompt,
            "output_format": output_format,
            "control_strength": str(control_strength),
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed and seed > 0:
            data["seed"] = str(seed)

        files = {
            "image": ("source.png", image_bytes, "image/png"),
        }

        return self._post_request(url, data, files=files)

    def upscale(self, image_base64, prompt="", negative_prompt="",
                creativity=0.35, seed=-1, output_format="png"):
        """
        Upscale image via Conservative Upscale endpoint.
        Scales from 64x64 up to 4K resolution (20-40x).

        Args:
            image_base64: Base64-encoded source image
            prompt: Description of desired output
            creativity: Detail generation (0 to 0.35, default 0.35)
        """
        url = f"{self.base_url}/stable-image/upscale/conservative"

        image_bytes = base64.b64decode(image_base64)

        data = {
            "output_format": output_format,
            "creativity": str(creativity),
        }

        if prompt:
            data["prompt"] = prompt
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed and seed > 0:
            data["seed"] = str(seed)

        files = {
            "image": ("source.png", image_bytes, "image/png"),
        }

        return self._post_request(url, data, files=files)

    def _post_request(self, url, data, files=None):
        """Execute API request and return result"""
        if not files:
            files = {"none": ''}

        try:
            start = time.time()
            r = requests.post(
                url,
                headers={
                    "authorization": f"Bearer {self.api_key}",
                    "accept": "image/*",
                },
                files=files,
                data=data,
                timeout=self.timeout,
            )
            elapsed = round(time.time() - start, 1)

            if r.status_code != 200:
                return {"error": self._parse_error(r)}

            # Response is raw image bytes
            image_b64 = base64.b64encode(r.content).decode('utf-8')
            result_seed = r.headers.get('seed')

            return {
                "image_base64": image_b64,
                "seed": int(result_seed) if result_seed else None,
                "elapsed": elapsed,
            }

        except requests.exceptions.ConnectionError:
            return {"error": "Stability AI bağlantı hatası"}
        except requests.exceptions.Timeout:
            return {"error": "Stability AI zaman aşımı"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    def _parse_error(self, response):
        """Extract error message from error response"""
        try:
            body = response.json()
            if isinstance(body, dict):
                msg = body.get('message') or body.get('name') or str(body)
                return f"Stability AI: {msg}"
        except Exception:
            pass
        return f"Stability AI hatası: HTTP {response.status_code}"

    def _detect_aspect_ratio(self, width, height):
        """Map width/height to closest supported aspect ratio"""
        ratio = width / height
        ratios = {
            "1:1": 1.0,
            "3:2": 3/2,
            "2:3": 2/3,
            "4:5": 4/5,
            "5:4": 5/4,
            "16:9": 16/9,
            "9:16": 9/16,
            "21:9": 21/9,
            "9:21": 9/21,
        }
        closest = min(ratios.items(), key=lambda x: abs(x[1] - ratio))
        return closest[0]
