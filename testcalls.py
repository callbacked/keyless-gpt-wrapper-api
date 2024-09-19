import requests
import json

# This tests functionality for:

# 1. Listing models
# 2. Chat completion
# 3. Chat completion non-streaming
# 4. Getting a conversation ID and ending the conversation by deleting it


base_url = "http://localhost:1337/v1" 
conversation_id = None

def test_list_models():
    response = requests.get(f"{base_url}/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    print("List Models:", data)

def test_chat_completion():
    global conversation_id
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
    response = requests.post(f"{base_url}/chat/completions", data=json.dumps(payload), headers=headers, stream=True)
    assert response.status_code == 200
    print("Chat Completion:")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            print(decoded_line)
            if "id" in decoded_line:
                conversation_id = json.loads(decoded_line.split("data: ")[1])["id"]
    print("Conversation ID captured:", conversation_id)

def test_end_conversation(conversation_id):
    response = requests.delete(f"{base_url}/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    print("End Conversation:", data)

if __name__ == "__main__":
    test_list_models()
    test_chat_completion()
    if conversation_id:
        test_end_conversation(conversation_id)
    else:
        print("No valid conversation ID found to end the conversation.")