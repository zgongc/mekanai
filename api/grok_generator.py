"""
api/grok_generator.py
MekanAI - xAI Grok Image Generation

Endpoint: POST https://api.x.ai/v1/images/generations
Models: grok-imagine-image-pro, grok-imagine-image, grok-2-image-1212

Usage:
    from api.grok_generator import GrokGenerator
    gen = GrokGenerator(api_key="...", base_url="https://api.x.ai/v1")
    result = gen.generate(prompt="modern living room", model_id="grok-imagine-image")
"""

import requests
import time


class GrokGenerator:
    """xAI Grok Image Generation API client"""

    def __init__(self, api_key, base_url="https://api.x.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = 120

    def generate(self, prompt, model_id="grok-imagine-image",
                 aspect_ratio="1:1", width=None, height=None):
        """
        Generate image via xAI Grok API.

        Args:
            prompt: Text description
            model_id: API model identifier
            aspect_ratio: "1:1", "3:4", "4:3", "9:16", "16:9"
            width/height: Used to auto-detect aspect ratio if provided

        Returns:
            dict with 'image_base64', 'elapsed' on success
            dict with 'error' on failure
        """
        if width and height:
            aspect_ratio = self._detect_aspect_ratio(width, height)

        url = f"{self.base_url}/images/generations"

        payload = {
            "model": model_id,
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json",
            "aspect_ratio": aspect_ratio,
        }

        try:
            start = time.time()
            r = requests.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            elapsed = round(time.time() - start, 1)

            data = r.json()
            images = data.get('data', [])
            if not images:
                return {"error": "Grok boş yanıt döndü"}

            image_b64 = images[0].get('b64_json')
            if not image_b64:
                return {"error": "Grok yanıtında görsel bulunamadı"}

            return {
                "image_base64": image_b64,
                "elapsed": elapsed,
            }

        except requests.exceptions.HTTPError as e:
            return {"error": self._parse_error(e)}
        except requests.exceptions.ConnectionError:
            return {"error": "Grok API bağlantı hatası"}
        except requests.exceptions.Timeout:
            return {"error": "Grok API zaman aşımı"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    def _parse_error(self, http_error):
        """Extract error message from HTTP error response"""
        try:
            body = http_error.response.json()
            err = body.get('error', {})
            msg = err.get('message', '') if isinstance(err, dict) else str(err)
            if msg:
                return f"Grok API: {msg}"
        except Exception:
            pass
        try:
            text = http_error.response.text[:500]
            if text:
                return f"Grok API: {text}"
        except Exception:
            pass
        return f"Grok API hatası: {str(http_error)}"

    def _detect_aspect_ratio(self, width, height):
        """Map width/height to closest supported aspect ratio"""
        ratio = width / height
        ratios = {
            "1:1": 1.0,
            "4:3": 4/3,
            "3:4": 3/4,
            "16:9": 16/9,
            "9:16": 9/16,
        }
        closest = min(ratios.items(), key=lambda x: abs(x[1] - ratio))
        return closest[0]
