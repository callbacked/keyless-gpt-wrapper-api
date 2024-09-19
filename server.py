from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi.responses import JSONResponse, StreamingResponse
import logging
import uuid
import time
import json
import asyncio
import httpx

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 1677610602
    owned_by: str = "custom"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    conversation_id: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict

# Store active conversations
conversations: Dict[str, List[ChatMessage]] = {}
current_vqd_token = ""

async def update_vqd_token():
    global current_vqd_token
    async with httpx.AsyncClient() as client:
        try:
            await client.get("https://duckduckgo.com/country.json")
            headers = {"x-vqd-accept": "1"}
            response = await client.get("https://duckduckgo.com/duckchat/v1/status", headers=headers)
            if response.status_code == 200:
                current_vqd_token = response.headers.get("x-vqd-4", current_vqd_token)
                logging.info(f"Updated x-vqd-4 token: {current_vqd_token}")
            else:
                logging.warning(f"Failed to update x-vqd-4 token. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error updating x-vqd-4 token: {str(e)}")

async def chat_with_duckduckgo(query: str, model: str, conversation_history: List[ChatMessage]):
    global current_vqd_token

    await update_vqd_token()

    user_messages = [{"role": msg.role, "content": msg.content} for msg in conversation_history if msg.role == "user"]
    payload = {
        "messages": user_messages,
        "model": model
    }

    headers = {
        "x-vqd-4": current_vqd_token,
        "Content-Type": "application/json"
    }

    logging.info(f"Sending payload to DuckDuckGo: {json.dumps(payload)}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://duckduckgo.com/duckchat/v1/chat", json=payload, headers=headers)
            if response.status_code == 200:
                full_response = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            json_data = json.loads(data)
                            message = json_data.get("message", "")
                            full_response += message
                            yield message
                        except json.JSONDecodeError:
                            logging.warning(f"Failed to parse JSON: {data}")
                logging.info(f"Full response from DuckDuckGo: {full_response}")
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
    models = [
        ModelInfo(id="gpt-4o-mini"),
        ModelInfo(id="claude-3-haiku"),
        ModelInfo(id="mixtral-8x7b"),
        ModelInfo(id="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")
    ]
    return {"data": models, "object": "list"}

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    logging.info(f"Received streaming request for conversation {conversation_id}")
    logging.info(f"Request: {request.model_dump()}")

    conversation_history = conversations.get(conversation_id, [])
    conversation_history.extend(request.messages)

    async def generate():
        try:
            async for chunk in chat_with_duckduckgo(" ".join([msg.content for msg in request.messages]), request.model, conversation_history):
                response = {
                    "id": conversation_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": chunk
                            },
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(response)}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/v1/chat/completions/non-streaming")
async def chat_completion_non_streaming(request: ChatCompletionRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    logging.info(f"Received non-streaming request for conversation {conversation_id}")
    logging.info(f"Request: {request.model_dump()}")

    conversation_history = conversations.get(conversation_id, [])
    conversation_history.extend(request.messages)

    try:
        full_response = ""
        async for chunk in chat_with_duckduckgo(" ".join([msg.content for msg in request.messages]), request.model, conversation_history):
            full_response += chunk
        
        response = {
            "id": conversation_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_response
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg.content) for msg in conversation_history),
                "completion_tokens": len(full_response),
                "total_tokens": sum(len(msg.content) for msg in conversation_history) + len(full_response)
            }
        }

        conversation_history.append(ChatMessage(role="assistant", content=full_response))
        conversations[conversation_id] = conversation_history
        
        return JSONResponse(content=response, media_type="application/json")
    except Exception as e:
        logging.error(f"Exception occurred during non-streaming response for conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    uvicorn.run(app, host="0.0.0.0", port=1337)
