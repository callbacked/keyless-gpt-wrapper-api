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
from fake_useragent import UserAgent

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
    user_messages = [{"role": msg.role, "content": msg.content} for msg in conversation_history if msg.role == "user"]
    
    if system_message and user_messages:
        user_messages[0]["content"] = f"{system_message.content}\n\n{user_messages[0]['content']}"

    payload = {
        "messages": user_messages,
        "model": original_model
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
        if not app.state.session_id:
            raise ValueError("Server not initialized with session ID")
            
        engine = TTSEngine(session_id=app.state.session_id)
        audio_data = await engine.generate_speech(request.input, request.voice)
        
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
    conversation_id = str(uuid.uuid4())
    logging.info(f"Received chat completion request for conversation {conversation_id}")
    logging.info(f"Request: {request.model_dump()}")

    # Check if audio generation is requested
    generate_audio = (
        request.modalities is not None and
        "audio" in request.modalities and
        request.audio is not None
    )

    conversation_history = conversations.get(conversation_id, [])
    conversation_history.extend(request.messages)

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
            if generate_audio and app.state.session_id:
                try:
                    engine = TTSEngine(session_id=app.state.session_id)
                    tiktok_voice = VOICES.get(request.audio.voice, "en_us_002")
                    audio_bytes = await engine.generate_speech(full_response, tiktok_voice)
                    audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                    audio_id = f"audio_{uuid.uuid4().hex[:12]}"
                except Exception as e:
                    logging.error(f"Audio generation failed: {str(e)}")

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
        if generate_audio and app.state.session_id:
            try:
                engine = TTSEngine(session_id=app.state.session_id)
                tiktok_voice = VOICES.get(request.audio.voice, "en_us_002")
                audio_bytes = await engine.generate_speech(full_response, tiktok_voice)
                audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                audio_id = f"audio_{uuid.uuid4().hex[:12]}"
            except Exception as e:
                logging.error(f"Audio generation failed: {str(e)}")

        # Calculate token counts
        prompt_tokens = sum(len(msg.content.split()) if msg.content else 0 for msg in conversation_history)
        completion_tokens = len(full_response.split())
        total_tokens = prompt_tokens + completion_tokens

        response = ChatCompletionResponse(
            id=conversation_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=full_response if not generate_audio else None,
                        audio=AudioData(
                            id=audio_id,
                            expires_at=int((datetime.now() + timedelta(hours=1)).timestamp()),
                            data=audio_data,
                            transcript=full_response
                        ) if generate_audio else None
                    ),
                    finish_reason="stop"
                )
            ],
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        )

        conversation_history.append(ChatMessage(role="assistant", content=full_response))
        conversations[conversation_id] = conversation_history
        
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

def create_app(session_id: Optional[str] = None):
    if session_id:
        app.state.session_id = session_id
    return app

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Combined Chat and TTS API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=1337, help="Port to bind to")
    parser.add_argument("--session-id", required=True, help="TikTok session ID")
    
    args = parser.parse_args()
    
    app = create_app(session_id=args.session_id)
    uvicorn.run(app, host=args.host, port=args.port)
