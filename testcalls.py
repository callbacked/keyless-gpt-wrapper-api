import requests
import json

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
        "model": "keyless-gpt-4o-mini",  
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": True  
    }
    
    response = requests.post(
        f"{base_url}/chat/completions", 
        json=payload,  
        headers=headers, 
        stream=True
    )
    
    assert response.status_code == 200
    print("Chat Completion:")
    
    try:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    data = decoded_line[6:]  
                    if data != "[DONE]":
                        try:
                            response_data = json.loads(data)
                            print(f"Received chunk: {response_data}")
                            if "id" in response_data and not conversation_id:
                                conversation_id = response_data["id"]
                                print(f"Conversation ID captured: {conversation_id}")
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON: {data}")
                            continue
    except Exception as e:
        print(f"Error during streaming: {str(e)}")

def test_non_streaming_chat_completion():
    global conversation_id
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "keyless-gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False
    }
    
    response = requests.post(
        f"{base_url}/chat/completions", 
        json=payload,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    print("Non-streaming Chat Completion:", data)
    if "id" in data:
        conversation_id = data["id"]
        print(f"Conversation ID captured: {conversation_id}")

def test_end_conversation(conversation_id):
    response = requests.delete(f"{base_url}/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    print("End Conversation:", data)

if __name__ == "__main__":
    test_list_models()
    print("\nTesting streaming completion:")
    test_chat_completion()
    print("\nTesting non-streaming completion:")
    test_non_streaming_chat_completion()
    
    if conversation_id:
        print("\nTesting conversation deletion:")
        test_end_conversation(conversation_id)
    else:
        print("No valid conversation ID found to end the conversation.")