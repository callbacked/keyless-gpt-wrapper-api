import httpx
import base64
import logging
from models import BaseModel


class TTSRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "en_us_002"
    response_format: str = "mp3"
    speed: float = 1.0

class TTSEngine:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.headers = {
            'User-Agent': "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
            'Cookie': f'sessionid={session_id}'
        }

    async def generate_speech(self, text: str, voice: str = "en_us_002") -> bytes:
        try:
            sanitized_text = TextProcessor.sanitize_text(text)
            url = f"https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/?text_speaker={voice}&req_text={sanitized_text}&speaker_map_type=0&aid=1233"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers)
                response_data = response.json()
                
                if response_data.get("message") == "Couldn't load speech. Try again.":
                    raise ValueError("Invalid session ID")

                if 'data' not in response_data or 'v_str' not in response_data['data']:
                    error_msg = response_data.get('message', 'Unknown error occurred')
                    raise ValueError(f"TikTok API error: {error_msg}")

                return base64.b64decode(response_data["data"]["v_str"])
                
        except Exception as e:
            logging.error(f"Speech generation failed: {str(e)}")
            raise

class TextProcessor:
    @staticmethod
    def sanitize_text(text: str) -> str:
        replacements = {
            "+": "plus",
            " ": "+",
            "&": "and",
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
            "\n": ""
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text