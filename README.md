# Keyless GPT Wrapper API

I wanted to use GPT-4o-mini like I would normally do on the website (for free), but just doing it through API calls. 

This is done by using the DuckDuckGo Python library, and using its [chat() function](https://pypi.org/project/duckduckgo-search). From there I made an OpenAI Compatible API to make sure I can use it in other services. More notably in those VSCode coding extensions.

**Note:** I know it works with the Continue.dev VSCode extension, have not tested it on anything else, so YMMV

Do not expect frequent updates, I'll be using this until it breaks pretty much.


# Setting up
1. ``pip install -r requirements.txt``
2. ``python server.py``  **(should now be running on localhost:1337)**
3. Perform a test call by running ``python testcalls.py`` **in a separate terminal**

(docker pending)
## Example Calls Via curl
Calling upon available models

Receiving streamed message (message sent in chunks)

**Where ``"content":`` is where you put your message**

    curl -X POST "http://localhost:1337/v1/chat/completions"  \
    
    -H "Content-Type: application/json"  \
    
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'  \
    
    -H "Accept: text/event-stream"

Receiving non-streamed messaged (message sent at once)

    curl -X POST "http://localhost:1337/v1/chat/completions/non-streaming"  \
    
    -H "Content-Type: application/json"  \
    
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'

__Honestly haven't noticed much of a difference between the two, I just wanted to ensure it followed the same standards as the OpenAI Compatible API.__



