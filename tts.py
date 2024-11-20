import httpx
import base64
import logging
from typing import Optional, List
from models import BaseModel


class TTSRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "en_us_002"
    response_format: str = "mp3"
    speed: float = 1.0

class TTSEngine:
    _instance: Optional['TTSEngine'] = None
    
    @classmethod
    def initialize(cls, session_id: Optional[str] = None) -> Optional['TTSEngine']:
        if cls._instance is None:
            if not session_id:
                logging.warning("No TikTok session ID provided. TTS functionality will be disabled.")
                return None
            
            try:
                cls._instance = cls(session_id)
                logging.info("TTS Engine initialized successfully")
            except ValueError as e:
                logging.error(f"Failed to initialize TTS Engine: {str(e)}")
                return None
                
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> Optional['TTSEngine']:
        """Get the singleton instance of TTSEngine"""
        return cls._instance

    def __init__(self, session_id: str):
        if not session_id:
            raise ValueError("Session ID is required")
        self.session_id = session_id
        self.headers = {
            'User-Agent': "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
            'Cookie': f'sessionid={session_id}'
        }

    async def generate_speech(self, text: str, voice: str = "en_us_002") -> bytes:
        try:
            # Split text into chunks
            chunks = self._split_text(text)
            logging.info(f"Split text into {len(chunks)} chunks")
            
            all_audio = bytearray()
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    sanitized_text = TextProcessor.sanitize_text(chunk)
                    url = f"https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/?text_speaker={voice}&req_text={sanitized_text}&speaker_map_type=0&aid=1233"
                    
                    logging.info(f"Processing chunk {i}/{len(chunks)} of length {len(chunk)}")
                    logging.info(f"Sanitized text: {sanitized_text[:50]}...")
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, headers=self.headers)
                        #logging.info(f"TikTok API response status for chunk {i}: {response.status_code}")
                        
                        response_data = response.json()
                        #logging.info(f"TikTok API response for chunk {i}: {response_data}")
                        
                        if response_data.get("message") == "Couldn't load speech. Try again.":
                            raise ValueError("Invalid session ID")

                        if response_data.get("status_code") == 2:
                            logging.warning(f"Chunk {i} too long, attempting to split further")
                            # Recursively try with smaller chunks
                            smaller_chunks = self._split_text(chunk, max_size=len(chunk) // 2)
                            for small_chunk in smaller_chunks:
                                small_chunk_audio = await self.generate_speech(small_chunk, voice)
                                all_audio.extend(small_chunk_audio)
                            continue

                        if 'data' not in response_data or 'v_str' not in response_data['data']:
                            error_msg = response_data.get('message', 'Unknown error occurred')
                            raise ValueError(f"TikTok API error: {error_msg}")

                        chunk_audio = base64.b64decode(response_data["data"]["v_str"])
                        logging.info(f"Received audio data for chunk {i}, length: {len(chunk_audio)} bytes")
                        all_audio.extend(chunk_audio)
                        
                except Exception as e:
                    logging.error(f"Error processing chunk {i}: {str(e)}")
                    raise

            logging.info(f"Successfully generated audio for all chunks. Total size: {len(all_audio)} bytes")
            return bytes(all_audio)
                
        except Exception as e:
            logging.error(f"Speech generation failed: {str(e)}", exc_info=True)
            raise

    def _split_text(self, text: str, max_size: int = 200) -> List[str]:
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Split paragraph into sentences
            sentences = [s.strip() + '.' for s in paragraph.split('.') if s.strip()]
            
            for sentence in sentences:
                # If this sentence alone is longer than max_size, split it by commas
                if len(sentence) > max_size:
                    comma_parts = [p.strip() + ',' for p in sentence.split(',') if p.strip()]
                    for part in comma_parts:
                        if len(current_chunk) + len(part) > max_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = part
                        else:
                            current_chunk += " " + part
                else:
                    # If adding this sentence would exceed the limit, start a new chunk
                    if len(current_chunk) + len(sentence) > max_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence
            
            # Add paragraph break if not at the end
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Filter out empty chunks and strip whitespace
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        logging.info(f"Split text into {len(chunks)} chunks: {[len(c) for c in chunks]} chars each")
        return chunks


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
            "\n": " "
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text