  
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



# Setting Up

If you want to use this API WITH speech generation functionality, [follow this setup guide](https://github.com/callbacked/keyless-gpt-wrapper-api/wiki/Setting-Up-(With-TTS-Endpoint))

If you want to use this API as-is WITHOUT speech generation functionality, [follow this setup guide](https://github.com/callbacked/keyless-gpt-wrapper-api/wiki/Setting-Up-(Without-TTS-Endpoint))


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

  
You send your initial message (**use ``stream:false`` for readibility**):

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

## (Optional) Text to Speech Endpoint
Assuming you are using the optional TTS endpoint, which uses TikTok's TTS and requires a session_id during setup, you can use this endpoint in a similar fashion to OpenAI's Speech API. This is useful for cases when you are hosting your own LLM Web UI (like Open Web UI) and want to use TTS to read its messages to you, or you want to develop or prototype an AI assistant.

#### Get list of available voices
``curl -X GET http://127.0.0.1:1337/v1/audio/speech/voices``

#### Sending a message with voice generation 
If you want to interact with an LLM and obtain a response with generated speech you can do the following:

```
curl -X POST "http://localhost:1337/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "keyless-gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Tell me a joke"}
    ],
    "modalities": ["audio"],
    "audio": {
      "voice": "en_us_002"
    },
    "stream": false
  }' | jq -r '.choices[0].message.audio.data' | base64 -d > speech.mp3
```
* **Only can be done with ``stream:false``**
* A complete list of voices can be found here(placeholder)
* ``| jq -r '.choices[0].message.audio.data' | base64 -d > speech.mp3`` (decodes the audio data from the completed response to provide an mp3 file)

#### Using TTS Standalone
It is not required to use an LLM to get TTS, you can also generate speech from your own text input.

```
curl -X POST "http://localhost:1337/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, this is a test message",
    "voice": "en_us_002"
  }' \
  --output speech.mp3
```





