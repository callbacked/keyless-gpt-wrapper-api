
# [Keyless GPT Wrapper API](https://callbacked.github.io/keyless-gpt-wrapper-api/)

I wanted to use GPT-4o-mini like I would normally do on the website (for free), but just doing it through API calls.

  
This is done by interacting with DuckDuckGo's AI chat functionality. Previously, this was achieved using the DuckDuckGo Python library (using the [chat() function](https://pypi.org/project/duckduckgo-search)), but the dependency has been removed due to its limitations. Now, the chat interactions are handled directly through HTTP requests instead.
  
**Note:** I know it works with the Continue.dev VSCode extension, Ollama Open Web UI and Aider, have not tested it on anything else, so YMMV

In my time making this API I found a limitation from interacting with DuckDuckGo's AI chat:

1. Cannot send images (Havent figured this one out yet, probably never will)

*Do not expect frequent updates, I'll be using this until it breaks pretty much.*

*[DuckDuckGo AI Terms of Service](https://duckduckgo.com/aichat/privacy-terms)*


# Example Demo Usage



https://github.com/user-attachments/assets/e4032e31-d12e-4f66-9d27-8932a146811e



https://github.com/user-attachments/assets/1d5ece0e-201e-4079-915c-f5c3351654fa



https://github.com/user-attachments/assets/02dc5970-1b2b-4ce8-8aab-e3b589c276e8



# Setting Up Locally


1.  ``pip install -r requirements.txt``


2.  ``python server.py``  **(should now be running on localhost:1337)**


3. Perform a test call by running ``python testcalls.py``  **in a separate terminal**

# Setting Up Via Docker
This uses the latest image version in the Docker Hub repository

1.  ``docker run -d --name keyless -p 1337:1337 callbacked/keyless:latest``

# Setting Up Via Docker (Building your image locally)

If you don't want to use the Docker Hub image and want to do it yourself, you can do it one of two ways, its up to personal preference:


#### Doing it with docker run:



1.  ``git clone https://github.com/callbacked/keyless-gpt-wrapper-api && cd keyless-gpt-wrapper-api ``



2.  ``docker build -t keyless-gpt-wrapper-api:latest .``



3.  ``docker run --name keyless -d -p 1337:1337 keyless-gpt-wrapper-api:latest``



#### Doing it with docker-compose:


1.  ``git clone https://github.com/callbacked/keyless-gpt-wrapper-api && cd keyless-gpt-wrapper-api ``

  
4.  ``docker-compose up -d``

## Sending requests


#### Calling upon available models
``curl -X GET http://127.0.0.1:1337/v1/models``

So far you can use:
- GPT4o Mini
- Claude 3 Haiku
- Mixtral 8x7b
- Llama 70b Instruct Turbo 

#### Sending a message

Where ``"content":`` is where you put your message, 
```
curl -X POST "http://localhost:1337/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{
  "model": "keyless-gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Tell me a joke"}
  ],
  "stream": false
}'
```
**``stream: true`` if you want your response to be streamed in or ``stream: false`` if you want the response to be given to you all at once, though ``stream:false`` is highly recommended for readibility**

## Retaining conversation context


In cases where you want to continue having a conversion you can keep note of the conversation_id generated, for instance:

  
You send your initial message (using curl as an example): **use ``stream:false`` for readibility**

 ```
curl -X POST "http://localhost:1337/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{
  "model": "keyless-gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Tell me a joke"}
  ],
  "stream": false
}'
```
You receive:
```
{
  "id": "58a22f8d-64b8-45c1-97c4-030d11e6d1b9", <======== TAKE NOTE OF THIS
  "object": "chat.completion",
  "created": 1726798732,
  "model": "keyless-gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Why did the scarecrow win an award? \n\nBecause he was outstanding in his field!"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 4,
    "completion_tokens": 14,
    "total_tokens": 18
  }
}

```

With the response received, you can send a follow-up question with the conversation_id appended at the end:

```
curl -X POST "http://localhost:1337/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{
  "model": "keyless-gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Tell me a joke"}
  ],
  "conversation_id": "58a22f8d-64b8-45c1-97c4-030d11e6d1b9",
  "stream": false
}'
```

#### Deleting a conversation

``curl -X DELETE http://127.0.0.1:1337/v1/conversations/1cecdf45-df73-431b-884b-6d233b5511c7``




