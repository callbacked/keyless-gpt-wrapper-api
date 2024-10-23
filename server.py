from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from fastapi.responses import StreamingResponse
import logging
import uuid
import time
import json
import asyncio
import random
import httpx
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
MODEL_MAPPING = {
    "keyless-gpt-4o-mini": "gpt-4o-mini",
    "keyless-claude-3-haiku": "claude-3-haiku-20240307",
    "keyless-mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "keyless-meta-Llama-3.1-70B-Instruct-Turbo": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
}

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = int(time.time())
    owned_by: str = "custom"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: ChatCompletionResponseUsage

class DeltaMessage(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChatCompletionStreamResponseChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[str] = None

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamResponseChoice]

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
            elif response.status_code == 429:
                logging.warning("Rate limit exceeded. Changing User-Agent and retrying.")
                for attempt in range(5):  # Try up to 5 times
                    user_agent = get_next_user_agent()
                    vqd_token = await update_vqd_token(user_agent)
                    headers["User-Agent"] = user_agent
                    headers["x-vqd-4"] = vqd_token
                    logging.info(f"Retrying with new User-Agent: {user_agent}")
                    response = await client.post("https://duckduckgo.com/duckchat/v1/chat", json=payload, headers=headers)
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

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    conversation_id = str(uuid.uuid4())

    logging.info(f"Received chat completion request for conversation {conversation_id}")
    logging.info(f"Request: {request.model_dump()}")

    conversation_history = conversations.get(conversation_id, [])
    conversation_history.extend(request.messages)

    async def generate():
        try:
            full_response = ""
            async for chunk in chat_with_duckduckgo(" ".join([msg.content for msg in request.messages]), request.model, conversation_history):
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
                await asyncio.sleep(random.uniform(0.05, 0.1))

            final_response = ChatCompletionStreamResponse(
                id=conversation_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionStreamResponseChoice(
                        index=0,
                        delta=DeltaMessage(),
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
        async for chunk in chat_with_duckduckgo(" ".join([msg.content for msg in request.messages]), request.model, conversation_history):
            full_response += chunk

        response = ChatCompletionResponse(
            id=conversation_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=full_response),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionResponseUsage(
                prompt_tokens=sum(len(msg.content.split()) for msg in conversation_history),
                completion_tokens=len(full_response.split()),
                total_tokens=sum(len(msg.content.split()) for msg in conversation_history) + len(full_response.split())
            )
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1337)
