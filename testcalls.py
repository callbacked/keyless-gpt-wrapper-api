import requests

# EXAMPLE CURL SCRIPTS
# [STREAMING]
# -----------------------
# curl -X POST "http://localhost:1337/v1/chat/completions" \
#      -H "Content-Type: application/json" \
#      -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}' \
#      -H "Accept: text/event-stream"

# [NON STREAMING]
#-----------------------
# curl -X POST "http://localhost:1337/v1/chat/completions/non-streaming" \
#      -H "Content-Type: application/json" \
#      -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Tell me a joke"}]}'

# [GET MODELS]
#-----------------------
# curl -X GET "http://localhost:1337/v1/models"


# api server
base_url = "http://localhost:1337/v1" # i used 1337

# get response of list of models
response = requests.get(f"{base_url}/models")
print("GET /v1/models")
print("Status Code:", response.status_code)
print("Response:", response.json())

# Test /v1/chat/completions (non-streaming, so message is sent all at once and not chunks)
data = {
    "model": "gpt-4o-mini", # or claude-3-haiku
    "messages": [
        {"role": "user", "content": "Tell me a joke"}
    ]
}
response = requests.post(f"{base_url}/chat/completions/non-streaming", json=data)
print("\nPOST /v1/chat/completions/non-streaming")
print("Status Code:", response.status_code)
print("Response:", response.json())

# Test /v1/chat/completions (streaming, so message is sent in chunks)
response = requests.post(f"{base_url}/chat/completions", json=data, stream=True)
print("\nPOST /v1/chat/completions")
print("Status Code:", response.status_code)
print("Response:")
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
