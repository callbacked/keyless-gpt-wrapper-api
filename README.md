
# Keyless GPT Wrapper API

I wanted to use GPT-4o-mini like I would normally do on the website (for free), but just doing it through API calls.

  
This is done by interacting with DuckDuckGo's AI chat functionality. Previously, this was achieved using the DuckDuckGo Python library (using the [chat() function](https://pypi.org/project/duckduckgo-search)), but the dependency has been removed due to its limitations. Now, the chat interactions are handled directly through HTTP requests instead.
  
**Note:** I know it works with the Continue.dev VSCode extension and Ollama Open Web UI, have not tested it on anything else, so YMMV

In my time making this API I found some limitations from using the DuckDuckGo Python Library:


1. Cannot send images

    1a. Havent figured this one out yet

3. Context length for a given conversation session is up to 20k characters, this is because your conversation history is appended in each message you send. DuckDuckGo Chat's frontend does something similar but without sacrificing on character length (don't know how), because each message is treated as a new chat session for what I assume is for privacy reasons.

    2a. As a way to work within the bounds of this, the messages are compressed by removing whitespace in order to retain more characters. Giving it a "lengthier" context. Once you approach the context limit, old messages start getting pruned from its context.

*Do not expect frequent updates, I'll be using this until it breaks pretty much.*

*[DuckDuckGo AI Terms of Service](https://duckduckgo.com/aichat/privacy-terms)*


# Example Demo Usage



https://github.com/user-attachments/assets/1d5ece0e-201e-4079-915c-f5c3351654fa



https://github.com/user-attachments/assets/02dc5970-1b2b-4ce8-8aab-e3b589c276e8



# Setting Up Locally


1.  ``pip install -r requirements.txt``


2.  ``python server.py``  **(should now be running on localhost:1337)**


3. Perform a test call by running ``python testcalls.py``  **in a separate terminal**


# Setting Up Via Docker


You can set up with Docker through one of two ways, its up to personal preference:

  

  

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
#### Receiving streamed message (message sent in chunks)

Where ``"content":`` is where you put your message
```
curl -X POST "http://localhost:1337/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}' \
-H "Accept: text/event-stream"
```
  

#### Receiving non-streamed messaged (message sent at once)

```
curl -X POST "http://localhost:1337/v1/chat/completions/non-streaming" \
-H "Content-Type: application/json" \
-d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'
```

## Retaining conversation context

  

  

In cases where you want to continue having a conversion you can keep note of the conversation_id generated, for instance:

  
You send your initial message (using curl as an example): **use non-streaming always**

 ```
 curl -X POST "http://localhost:1337/v1/chat/completions/non-streaming" \
-H "Content-Type: application/json" \
-d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}' \
-H "Accept: text/event-stream"
```
You receive:
```
{
  "id": "1cecdf45-df73-431b-884b-6d233b5511c7", <========= TAKE NOTE OF THIS
  "object": "chat.completion",
  "created": 1726725779,
  "model": "gpt-4o-mini",
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
    "prompt_tokens": 14,
    "completion_tokens": 78,
    "total_tokens": 92
  }
}
```

With the response received, you can send a follow-up question with the conversation_id appended at the end:

```
curl -X POST http://127.0.0.1:1337/v1/chat/completions/non-streaming \
-H "Content-Type: application/json" \
-d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me another"}], "conversation_id": "1cecdf45-df73-431b-884b-6d233b5511c7"}'
```

#### Deleting a conversation

``curl -X DELETE http://127.0.0.1:1337/v1/conversations/1cecdf45-df73-431b-884b-6d233b5511c7``




