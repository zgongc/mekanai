"""
api/gemini_generator.py
MekanAI - Google Gemini & Imagen Image Generation

Supports two APIs:
    1. Gemini Native (Nano Banana) — generateContent endpoint
       Models: gemini-2.5-flash-image
    2. Imagen 4 — predict endpoint
       Models: imagen-4.0-fast-generate-001, imagen-4.0-generate-001

Usage:
    from api.gemini_generator import GeminiGenerator
    gen = GeminiGenerator(api_key="...", base_url="...")
    result = gen.generate(prompt="modern living room", model_id="gemini-2.5-flash-image")
"""

import requests
import base64
import time


class GeminiGenerator:
    """Google Gemini & Imagen API client for image generation"""

    def __init__(self, api_key, base_url="https://generativelanguage.googleapis.com/v1beta"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = 120

    def generate(self, prompt, model_id="gemini-2.5-flash-image",
                 aspect_ratio="1:1", width=None, height=None):
        """
        Generate image via Gemini or Imagen API.

        Args:
            prompt: Text description
            model_id: API model identifier
            aspect_ratio: "1:1", "3:4", "4:3", "9:16", "16:9"
            width/height: Used to auto-detect aspect ratio if provided

        Returns:
            dict with 'image_base64', 'elapsed' on success
            dict with 'error' on failure
        """
        # Auto-detect aspect ratio from width/height
        if width and height:
            aspect_ratio = self._detect_aspect_ratio(width, height)

        if model_id.startswith('imagen'):
            return self._generate_imagen(prompt, model_id, aspect_ratio)
        else:
            return self._generate_gemini(prompt, model_id, aspect_ratio)

    def _generate_gemini(self, prompt, model_id, aspect_ratio):
        """Generate via Gemini Native (Nano Banana) — generateContent endpoint"""
        url = f"{self.base_url}/models/{model_id}:generateContent"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio
                }
            }
        }

        try:
            start = time.time()
            r = requests.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self.api_key},
                timeout=self.timeout
            )
            r.raise_for_status()
            elapsed = round(time.time() - start, 1)

            data = r.json()
            candidates = data.get('candidates', [])
            if not candidates:
                return {"error": "Gemini boş yanıt döndü"}

            # Find image part in response
            parts = candidates[0].get('content', {}).get('parts', [])
            for part in parts:
                inline_data = part.get('inlineData')
                if inline_data and inline_data.get('mimeType', '').startswith('image/'):
                    return {
                        "image_base64": inline_data['data'],
                        "elapsed": elapsed,
                    }

            return {"error": "Gemini yanıtında görsel bulunamadı"}

        except requests.exceptions.HTTPError as e:
            return {"error": self._parse_error(e)}
        except requests.exceptions.ConnectionError:
            return {"error": "Gemini API bağlantı hatası"}
        except requests.exceptions.Timeout:
            return {"error": "Gemini API zaman aşımı"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    def _generate_imagen(self, prompt, model_id, aspect_ratio):
        """Generate via Imagen 4 — predict endpoint"""
        url = f"{self.base_url}/models/{model_id}:predict"

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
            }
        }

        try:
            start = time.time()
            r = requests.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self.api_key},
                timeout=self.timeout
            )
            r.raise_for_status()
            elapsed = round(time.time() - start, 1)

            data = r.json()
            predictions = data.get('predictions', [])
            if not predictions:
                return {"error": "Imagen boş yanıt döndü"}

            image_b64 = predictions[0].get('bytesBase64Encoded')
            if not image_b64:
                return {"error": "Imagen yanıtında görsel bulunamadı"}

            return {
                "image_base64": image_b64,
                "elapsed": elapsed,
            }

        except requests.exceptions.HTTPError as e:
            return {"error": self._parse_error(e)}
        except requests.exceptions.ConnectionError:
            return {"error": "Imagen API bağlantı hatası"}
        except requests.exceptions.Timeout:
            return {"error": "Imagen API zaman aşımı"}
        except Exception as e:
            return {"error": f"Beklenmeyen hata: {str(e)}"}

    def _parse_error(self, http_error):
        """Extract error message from HTTP error response"""
        try:
            body = http_error.response.json()
            err = body.get('error', {})
            msg = err.get('message', '') if isinstance(err, dict) else str(err)
            if msg:
                return f"Gemini API: {msg}"
        except Exception:
            pass
        try:
            text = http_error.response.text[:500]
            if text:
                return f"Gemini API: {text}"
        except Exception:
            pass
        return f"Gemini API hatası: {str(http_error)}"

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
