# Keyless GPT Wrapper API

I wanted to use GPT-4o-mini like I would normally do on the website (for free), but just doing it through API calls. 

This is done by using the DuckDuckGo Python library, and using its [chat() function](https://pypi.org/project/duckduckgo-search). From there I made an OpenAI Compatible API to make sure I can use it in other services. More notably in those VSCode coding extensions.

**Note:** I know it works with the Continue.dev VSCode extension, have not tested it on anything else, so YMMV

Do not expect frequent updates, I'll be using this until it breaks pretty much.


# Setting up
1 . ``pip install -r requirements.txt``
2. ``python server.py``  **(should now be running on localhost:1337)**
3. Perform a test call by running ``python testcalls.py`` **in a separate terminal**

(docker pending)
## Sending requests
#### Calling upon available models
``curl -X GET http://127.0.0.1:1337/v1/models
``

#### Receiving streamed message (message sent in chunks)

Where ``"content":`` is where you put your message

    curl -X POST "http://localhost:1337/v1/chat/completions"  \
    
    -H "Content-Type: application/json"  \
    
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'  \
    
    -H "Accept: text/event-stream"

#### Receiving non-streamed messaged (message sent at once)

    curl -X POST "http://localhost:1337/v1/chat/completions/non-streaming"  \
    
    -H "Content-Type: application/json"  \
    
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'

*Honestly haven't noticed much of a difference between the two, I just wanted to ensure it followed the same standards as the OpenAI Compatible API.*

## Retaining conversation context
In cases where you want to continue having a conversion you can keep note of the conversation_id generated, for instance:

You send your initial message (using curl as an example):

    curl -X POST "http://localhost:1337/v1/chat/completions"  \
    
    -H "Content-Type: application/json"  \
    
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'  \
    
    -H "Accept: text/event-stream"


You receive:

```{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "user",
      "content": "Tell me a joke"
    }
  ],
  "data": {
    "id": "ca218944-3bc0-41c6-8b9e-37ad52407bb9", <========== TAKE NOTE OF THIS
    "object": "chat.completion.chunk",
    "created": 1726380683,
    "model": "gpt-4o-mini",
    "choices": [
      {
        "index": 0,
        "delta": {
          "role": "assistant",
          "content": "Why did the scarecrow win an award? \n\nBecause he was outstanding in his field!"
        },
        "finish_reason": null
      }
    ]
  },
  "data_status": "[DONE]"
}
```

With the response received,  you can send a follow-up question with the conversation_id appended at the end:

```
curl -X POST http://127.0.0.1:1337/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me another"}], "conversation_id": "ca218944-3bc0-41c6-8b9e-37ad52407bb9"}'
```
#### Deleting a conversation
``curl -X DELETE http://127.0.0.1:1337/v1/conversations/ca218944-3bc0-41c6-8b9e-37ad52407bb9
``
