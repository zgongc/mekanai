"""
api/openai_generator.py
MekanAI - OpenAI DALL-E Image Generation

Supports:
    - DALL-E 3: High quality text-to-image
    - DALL-E 2: Fast text-to-image

Usage:
    from api.openai_generator import OpenAIGenerator
    gen = OpenAIGenerator(api_key="...", base_url="https://api.openai.com/v1")
    result = gen.generate(prompt="modern living room", model_id="dall-e-3")
"""

import requests
import time


class OpenAIGenerator:
    """OpenAI DALL-E API client for image generation"""

    # Supported sizes per model
    SIZES = {
        'dall-e-3': ['1024x1024', '1792x1024', '1024x1792'],
        'dall-e-2': ['256x256', '512x512', '1024x1024'],
    }

    def __init__(self, api_key, base_url="https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = 120

    def generate(self, prompt, model_id="dall-e-3",
                 width=None, height=None, quality="standard"):
        """
        Generate image via OpenAI DALL-E API.

        Returns:
            dict with 'image_base64', 'elapsed' on success
            dict with 'error' on failure
        """
        size = self._detect_size(model_id, width, height)
        url = f"{self.base_url}/images/generations"

        payload = {
            "model": model_id,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }

        if model_id == 'dall-e-3':
            payload["quality"] = quality

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
            elapsed = round(time.time() - start, 1)

            if r.status_code != 200:
                return {"error": self._parse_error(r)}

            data = r.json()
            images = data.get('data', [])
            if not images:
                return {"error": "OpenAI boş yanıt döndü"}

            image_b64 = images[0].get('b64_json')
            if not image_b64:
                return {"error": "OpenAI yanıtında görsel bulunamadı"}

            return {
                "image_base64": image_b64,
                "elapsed": elapsed,
            }

        except requests.exceptions.ConnectionError:
            return {"error": "OpenAI API bağlantı hatası"}
        except requests.exceptions.Timeout:
            return {"error": "OpenAI API zaman aşımı"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    def _parse_error(self, response):
        """Extract error message from error response"""
        try:
            body = response.json()
            err = body.get('error', {})
            msg = err.get('message', '') if isinstance(err, dict) else str(err)
            if msg:
                return f"OpenAI API: {msg}"
        except Exception:
            pass
        return f"OpenAI API hatası: HTTP {response.status_code}"

    def _detect_size(self, model_id, width, height):
        """Map width/height to closest supported DALL-E size"""
        if not width or not height:
            return '1024x1024'

        ratio = width / height
        if model_id == 'dall-e-3':
            if ratio > 1.3:
                return '1792x1024'
            elif ratio < 0.77:
                return '1024x1792'
            else:
                return '1024x1024'
        else:
            # DALL-E 2
            return '1024x1024'
