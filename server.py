from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from fastapi.responses import StreamingResponse
import logging
import uuid
import time
import json
import httpx
from datetime import datetime, timedelta
from models import ChatMessage, ChatCompletionRequest, ChatCompletionResponse, ChatCompletionResponseChoice, ChatCompletionResponseUsage, DeltaMessage, ModelInfo, AudioData, AudioConfig, ChatCompletionStreamResponse, ChatCompletionStreamResponseChoice
from config import MODEL_MAPPING, VOICES
from tts import TTSRequest, TTSEngine
import base64
import os 
import argparse
from fake_useragent import UserAgent

def parse_arguments():
    parser = argparse.ArgumentParser(description='Start the chat API server')
    parser.add_argument('--session-id', 
                       help='TikTok session ID for TTS functionality (overrides TIKTOK_SESSION_ID env variable)',
                       default=None)
    return parser.parse_args()
app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active conversations
conversations: Dict[str, List[ChatMessage]] = {}

ua = UserAgent()

def get_next_user_agent():
    return ua.random

async def update_vqd_token(user_agent):
    async with httpx.AsyncClient() as client:
        try:
            await client.get("https://duckduckgo.com/country.json", headers={"User-Agent": user_agent})
            headers = {"x-vqd-accept": "1", "User-Agent": user_agent}
            response = await client.get("https://duckduckgo.com/duckchat/v1/status", headers=headers)
            if response.status_code == 200:
                vqd_token = response.headers.get("x-vqd-4", "")
                logging.info(f"Fetched new x-vqd-4 token: {vqd_token}")
                return vqd_token
            else:
                logging.warning(f"Failed to fetch x-vqd-4 token. Status code: {response.status_code}")
                return ""
        except Exception as e:
            logging.error(f"Error fetching x-vqd-4 token: {str(e)}")
            return ""

async def chat_with_duckduckgo(query: str, model: str, conversation_history: List[ChatMessage]):
    original_model = MODEL_MAPPING.get(model, model)
    user_agent = get_next_user_agent()
    vqd_token = await update_vqd_token(user_agent)
    if not vqd_token:
        raise HTTPException(status_code=500, detail="Failed to obtain VQD token")

    # If there is a system message, add it before the first user message (DDG AI doesnt let us send system messages, so this is a workaround -- fundamentally, it works the same way when setting a system prompt)
    system_message = next((msg for msg in conversation_history if msg.role == "system"), None)
    
    # turns out i did not add in the partial context fixes from last release
    messages = []
    if system_message:
        messages.append({"role": "user", "content": system_message.content})

    for msg in conversation_history:
        if msg.role in ["user", "assistant"]:
            messages.append({
                "role": "user", 
                "content": msg.content
            })

    payload = {
        "model": original_model,
        "messages": messages
    }

    headers = {
        "x-vqd-4": vqd_token,
        "Content-Type": "application/json",
        "User-Agent": user_agent
    }

    logging.info(f"Sending payload to DuckDuckGo with User-Agent: {user_agent}")
    # swapped to stream using client.stream() - no more artificial streaming
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream('POST', "https://duckduckgo.com/duckchat/v1/chat", json=payload, headers=headers) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:].strip()
                            if data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(data)
                                message = json_data.get("message", "")
                                yield message
                            except json.JSONDecodeError:
                                logging.warning(f"Failed to parse JSON: {data}")
                elif response.status_code == 429:
                    for attempt in range(5): # Try up to 5 times
                        user_agent = get_next_user_agent()
                        vqd_token = await update_vqd_token(user_agent)
                        headers.update({
                            "User-Agent": user_agent,
                            "x-vqd-4": vqd_token
                        })
                        async with client.stream('POST', "https://duckduckgo.com/duckchat/v1/chat", json=payload, headers=headers) as retry_response:
                            if retry_response.status_code == 200:
                                async for line in retry_response.aiter_lines():
                                    if line.startswith("data: "):
                                        data = line[6:].strip()
                                        if data == "[DONE]":
                                            break
                                        try:
                                            json_data = json.loads(data)
                                            message = json_data.get("message", "")
                                            yield message
                                        except json.JSONDecodeError:
                                            logging.warning(f"Failed to parse JSON: {data}")
                                break
                    else:
                        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
                else:
                    logging.error(f"Error response from DuckDuckGo. Status code: {response.status_code}")
                    raise HTTPException(status_code=response.status_code, detail=f"Error communicating with DuckDuckGo: {response.text}")
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {str(e)}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            logging.error(f"Request error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logging.error(f"Unexpected error in chat_with_duckduckgo: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/v1/models")
async def list_models():
    logging.info("Listing available models")
    models = [ModelInfo(id=model_id) for model_id in MODEL_MAPPING.keys()]
    return {"data": models, "object": "list"}

@app.get("/v1/audio/speech/voices")
async def list_voices():
    voices = []
    for voice_id, info in VOICES.items():
        voices.append({
            "voice_id": voice_id,
            "name": info["name"],
            "language": info["language"],
            "category": info["category"]
        })
    return {"voices": voices}

@app.post("/v1/audio/speech")
async def create_speech(request: TTSRequest):
    try:
        tts_engine = TTSEngine.get_instance()
        if not tts_engine:
            raise ValueError("TTS functionality is not available. Check TIKTOK_SESSION_ID configuration.")

        audio_data = await tts_engine.generate_speech(request.input, request.voice)

        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={
                "Content-Type": "audio/mpeg",
                "Content-Length": str(len(audio_data))
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    # Use provided conversation_id, id, or generate new one
    conversation_id = request.conversation_id or str(uuid.uuid4())
    logging.info(f"Received chat completion request for conversation {conversation_id}")
    logging.info(f"Request: {request.model_dump()}")

    # Check if audio generation is requested and available
    tts_engine = TTSEngine.get_instance()
    generate_audio = (
        request.modalities is not None and
        "audio" in request.modalities and
        request.audio is not None and
        tts_engine is not None
    )

    # Get existing conversation history or initialize new one
    conversation_history = conversations.get(conversation_id, [])
    
    # Add new messages to history
    for msg in request.messages:
        # Only add message if it's not already in the history
        if not any(existing.content == msg.content and existing.role == msg.role 
                  for existing in conversation_history):
            conversation_history.append(msg)
    
    conversations[conversation_id] = conversation_history

    async def generate():
        try:
            full_response = ""
            async for chunk in chat_with_duckduckgo(
                " ".join([msg.content for msg in request.messages if msg.content]),
                request.model,
                conversation_history
            ):
                full_response += chunk
                response = ChatCompletionStreamResponse(
                    id=conversation_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionStreamResponseChoice(
                            index=0,
                            delta=DeltaMessage(content=chunk),
                            finish_reason=None
                        )
                    ]
                )
                yield f"data: {response.model_dump_json()}\n\n"

            # Generate audio if requested (for streaming responses)
            audio_data = None
            audio_id = None
            if generate_audio:
                try:
                    tiktok_voice = request.audio.voice if isinstance(request.audio.voice, str) else "en_us_002"
                    audio_bytes = await tts_engine.generate_speech(full_response, tiktok_voice)
                    audio_data = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else ""
                    audio_id = f"audio_{uuid.uuid4().hex[:12]}"
                    logging.info(f"Starting audio generation for voice: {tiktok_voice}")
                    logging.info(f"Text to convert: {full_response}")
                    
                    # Log the TTS engine state
                    logging.info(f"TTS Engine state: {tts_engine is not None}")
                    logging.info(f"Audio bytes received: {len(audio_bytes) if audio_bytes else 'None'}")
                    
                    if audio_bytes:
                        audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                        logging.info(f"Base64 encoded data length: {len(audio_data)}")
                    else:
                        logging.error("No audio bytes received from TTS engine")
                        
                except Exception as e:
                    logging.error(f"Audio generation failed: {str(e)}", exc_info=True)

            final_response = ChatCompletionStreamResponse(
                id=conversation_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionStreamResponseChoice(
                        index=0,
                        delta=DeltaMessage(
                            audio=AudioData(
                                id=audio_id,
                                expires_at=int((datetime.now() + timedelta(hours=1)).timestamp()),
                                data=audio_data,
                                transcript=full_response
                            ) if generate_audio else None
                        ),
                        finish_reason="stop"
                    )
                ]
            )
            yield f"data: {final_response.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    if request.stream:
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        full_response = ""
        async for chunk in chat_with_duckduckgo(
            " ".join([msg.content for msg in request.messages if msg.content]), 
            request.model,
            conversation_history
        ):
            full_response += chunk

        # Generate audio if requested (for non-streaming responses)
        audio_data = None
        audio_id = None
        if generate_audio:
            try:
                tiktok_voice = request.audio.voice if isinstance(request.audio.voice, str) else "en_us_002"
                audio_bytes = await tts_engine.generate_speech(full_response, tiktok_voice)
                audio_data = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else ""
                audio_id = f"audio_{uuid.uuid4().hex[:12]}"
                logging.info(f"Starting audio generation for voice: {tiktok_voice}")
                logging.info(f"Text to convert: {full_response}")
                
                # Log the TTS engine state
                logging.info(f"TTS Engine state: {tts_engine is not None}")
                logging.info(f"Audio bytes received: {len(audio_bytes) if audio_bytes else 'None'}")
            
                if audio_bytes:
                    audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                    logging.info(f"Base64 encoded data length: {len(audio_data)}")
                else:
                    logging.error("No audio bytes received from TTS engine")
            except Exception as e:
                logging.error(f"Audio generation failed: {str(e)}", exc_info=True)

        # Calculate token counts
        prompt_tokens = sum(len(msg.content.split()) if msg.content else 0 for msg in conversation_history)
        completion_tokens = len(full_response.split())
        total_tokens = prompt_tokens + completion_tokens

        # Create and store assistant's response
        assistant_message = ChatMessage(
            role="assistant",
            content=full_response if not generate_audio else None,
            audio=AudioData(
                id=audio_id,
                expires_at=int((datetime.now() + timedelta(hours=1)).timestamp()),
                data=audio_data,
                transcript=full_response
            ) if generate_audio else None
        )
        
        conversation_history.append(assistant_message)
        conversations[conversation_id] = conversation_history

        response = ChatCompletionResponse(
            id=conversation_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=assistant_message,
                    finish_reason="stop"
                )
            ],
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        )
        
        return response

@app.delete("/v1/conversations/{conversation_id}")
async def end_conversation(conversation_id: str):
    if conversation_id in conversations:
        del conversations[conversation_id]
        logging.info(f"Conversation {conversation_id} ended and context cleared")
        return {"message": f"Conversation {conversation_id} ended and context cleared."}
    else:
        logging.warning(f"Attempt to end non-existent conversation {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

if __name__ == "__main__":
    import uvicorn

    # Initialize TTS Engine according to arguments if passed or not
    args = parse_arguments()
    session_id = args.session_id or os.getenv('TIKTOK_SESSION_ID') # local users pass args directly, docker folks use env vars
    tts_engine = TTSEngine.initialize(session_id=session_id)

    if tts_engine:
        logging.info("TikTok TTS functionality enabled")
    else:
        logging.info("TikTok TTS functionality disabled - set TIKTOK_SESSION_ID environment in your docker-compose or docker run command \n or pass --session-id argument to enable if running locally")

    uvicorn.run(app, host="0.0.0.0", port=1337)

