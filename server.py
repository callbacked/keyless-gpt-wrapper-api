from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from fastapi.responses import JSONResponse, StreamingResponse
import logging
import uuid
import time
import json
import re
import asyncio

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

def compress_text(text):
    original_length = len(text)
    text = re.sub(r'\s+', ' ', text).strip()
    compressed_length = len(text)
    compression_ratio = (original_length - compressed_length) / original_length * 100 if original_length else 0
    logging.info(f"Compressed text from {original_length} to {compressed_length} characters. Compression ratio: {compression_ratio:.2f}%")
    return text

def manage_conversation_context(conversations, conversation_id, new_messages, max_chars=20000): # turns out its 20k!
    current_conversation = conversations.get(conversation_id, [])
    
    initial_char_count = sum(len(m.content) for m in current_conversation)
    initial_message_count = len(current_conversation)
    logging.info(f"Initial state for conversation {conversation_id}: {initial_char_count} characters, {initial_message_count} messages")
    
    for message in new_messages:
        message.content = compress_text(message.content)
    
    current_conversation.extend(new_messages)
    
    total_chars = sum(len(m.content) for m in current_conversation)
    
    removed_messages = 0
    while total_chars > max_chars:
        if current_conversation:
            removed_msg = current_conversation.pop(0)
            removed_messages += 1
            logging.info(f"Removed message: {removed_msg.role} - {removed_msg.content[:50]}...")
        else:
            break  
        total_chars = sum(len(m.content) for m in current_conversation)
    
    final_char_count = total_chars
    final_message_count = len(current_conversation)
    logging.info(f"Final state for conversation {conversation_id}: {final_char_count} characters, {final_message_count} messages")
    logging.info(f"Removed {removed_messages} messages to stay within the limit")
    
    conversations[conversation_id] = current_conversation
    return current_conversation

@app.get("/v1/models")
async def list_models():
    logging.info("Listing available models")
    models = [
        ModelInfo(id="gpt-4o-mini"),
        ModelInfo(id="claude-3-haiku"),
        ModelInfo(id="mixtral-8x7b")
    ]
    return {"data": models, "object": "list"}

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logging.info(f"Received streaming request for conversation {conversation_id}")
    logging.debug(f"Request content: {request.model_dump_json(exclude_unset=True)}")
    
    managed_conversation = manage_conversation_context(conversations, conversation_id, request.messages)
    
    history_json = {
        "conversation_id": conversation_id,
        "messages": [message.model_dump() for message in managed_conversation]
    }
    logging.info(f"Appending conversation history: {json.dumps(history_json)}")
    

    query = " ".join([msg.content for msg in managed_conversation if msg.role != "system"])
    logging.info(f"Generated query for conversation {conversation_id}: {len(query)} characters")
    
    async def generate():
        try:
            logging.info(f"Sending query to DuckDuckGo for conversation {conversation_id}")
            results = DDGS().chat(query, model=request.model)
            logging.info(f"Received response from DuckDuckGo for conversation {conversation_id}: {len(results)} characters")
    
            chunk_size = 10  # 10 chars per sec is a good rate for streaming
            for i in range(0, len(results), chunk_size):
                chunk = results[i:i+chunk_size]
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
                logging.debug(f"Streaming chunk for conversation {conversation_id}: {chunk}")
                yield f"data: {json.dumps(response)}\n\n"
                await asyncio.sleep(0.1)  # simulate streaming

            manage_conversation_context(conversations, conversation_id, [ChatMessage(role="assistant", content=results)])

            yield "data: [DONE]\n\n"
            logging.info(f"Completed streaming response for conversation {conversation_id}")
        except Exception as e:
            logging.error(f"Exception occurred during streaming for conversation {conversation_id}: {str(e)}")
            error_response = {
                "error": {
                    "message": str(e),
                    "type": "internal_error",
                    "code": 500
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/v1/chat/completions/non-streaming")
async def chat_completion_non_streaming(request: ChatCompletionRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logging.info(f"Received non-streaming request for conversation {conversation_id}")
    logging.debug(f"Request content: {request.model_dump_json(exclude_unset=True)}")
    
    managed_conversation = manage_conversation_context(conversations, conversation_id, request.messages)
    
    history_json = {
        "conversation_id": conversation_id,
        "messages": [message.model_dump() for message in managed_conversation]
    }
    logging.info(f"Appending conversation history: {json.dumps(history_json)}")
    
    query = " ".join([msg.content for msg in managed_conversation if msg.role != "system"])
    logging.info(f"Generated query for conversation {conversation_id}: {len(query)} characters")
    
    try:
        logging.info(f"Sending query for conversation {conversation_id}")
        results = DDGS().chat(query, model=request.model)
        logging.info(f"Generated response for conversation {conversation_id}: {len(results)} characters")
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
                        "content": results
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(query),
                "completion_tokens": len(results),
                "total_tokens": len(query) + len(results)
            }
        }

        manage_conversation_context(conversations, conversation_id, [ChatMessage(role="assistant", content=results)])

        logging.info(f"Sending non-streaming response for conversation {conversation_id}")
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
