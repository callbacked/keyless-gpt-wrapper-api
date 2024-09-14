from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from duckduckgo_search import DDGS
from fastapi.responses import JSONResponse, StreamingResponse
import logging
import uuid
import time
import json

app = FastAPI()

logging.basicConfig(level=logging.INFO)

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

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict

@app.get("/v1/models")
async def list_models():
    models = [
        ModelInfo(id="gpt-4o-mini"),
        ModelInfo(id="claude-3-haiku") # since its already available, why not?
    ]
    return {"data": models, "object": "list"}

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    query = request.messages[-1].content
    # logging.info(f"Received query: {query}") # UNCOMMENT THIS IF YOU WANT TO SEE REQUESTS SENT

    async def generate():
        try:
            results = DDGS().chat(query, model=request.model)
            #logging.info(f"Result: {results}") # UNCOMMENT THIS IF YOU WANT TO SEE RESPONSES GIVEN
            response = {
                "id": f"chatcmpl-{str(uuid.uuid4())[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": results
                        },
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(response)}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"Exception occurred: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/v1/chat/completions/non-streaming")
async def chat_completion_non_streaming(request: ChatCompletionRequest):
    query = request.messages[-1].content
    logging.info(f"Received query: {query}")
    try:
        results = DDGS().chat(query, model=request.model)
        logging.info(f"Results from DDGS: {results}")
        response = {
            "id": f"chatcmpl-{str(uuid.uuid4())[:8]}",
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
        logging.info(f"Sending response: {response}")
        return JSONResponse(content=response, media_type="application/json")
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1337)