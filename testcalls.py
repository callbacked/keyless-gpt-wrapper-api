import requests
import json
import time

base_url = "http://localhost:1337/v1"
conversation_id = None

def test_list_models():
    print("\n=== Testing /v1/models endpoint ===")
    response = requests.get(f"{base_url}/models")
    assert response.status_code == 200
    data = response.json()
    
    # Test OpenAI format compliance
    assert "data" in data
    assert "object" in data
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    
    # Test model info structure
    model = data["data"][0]
    assert "id" in model
    assert "object" in model
    assert "created" in model
    assert "owned_by" in model
    assert "permission" in model
    print("✓ Models endpoint format matches OpenAI spec")
    
    # Test headers
    headers = response.headers
    assert "x-request-id" in headers
    assert "x-ratelimit-limit-requests" in headers
    assert "x-ratelimit-remaining-requests" in headers
    assert "x-ratelimit-reset-requests" in headers
    print("✓ Response includes standard OpenAI headers")
    
    print("Models available:", [model["id"] for model in data["data"]])

def test_error_handling():
    print("\n=== Testing Error Handling ===")
    
    # Test invalid model
    print("Testing invalid model error...")
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": "invalid-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 400 or response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "message" in data["error"]
    assert "type" in data["error"]
    print("✓ Invalid model error handled correctly")
    
    # Test invalid request format
    print("\nTesting invalid request format...")
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": "keyless-gpt-4o-mini",
            "invalid_field": "test"
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 422  # FastAPI validation error
    data = response.json()
    assert "error" in data or "detail" in data
    print("✓ Invalid request format handled correctly")

def test_chat_completion():
    print("\n=== Testing Chat Completion ===")
    global conversation_id
    
    # Test non-streaming request
    print("Testing non-streaming completion...")
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": "keyless-gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say hello"}],
            "stream": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response format
    assert "id" in data
    assert "object" in data
    assert data["object"] == "chat.completion"
    assert "created" in data
    assert "model" in data
    assert "choices" in data
    assert "usage" in data
    assert len(data["choices"]) > 0
    assert "message" in data["choices"][0]
    assert "role" in data["choices"][0]["message"]
    assert "content" in data["choices"][0]["message"]
    print("✓ Non-streaming response format matches OpenAI spec")
    
    # Store conversation ID for future tests
    conversation_id = data["id"]
    
    # Test streaming request
    print("\nTesting streaming completion...")
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": "keyless-gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say hello"}],
            "stream": True
        },
        stream=True
    )
    
    assert response.status_code == 200
    print("Streaming response chunks:")
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                assert "id" in chunk
                assert "object" in chunk
                assert chunk["object"] == "chat.completion.chunk"
                assert "choices" in chunk
                print("✓ Received valid chunk")

def test_conversation_context():
    print("\n=== Testing Conversation Context ===")
    if not conversation_id:
        print("Skipping - no conversation ID from previous test")
        return
        
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": "keyless-gpt-4o-mini",
            "messages": [{"role": "user", "content": "What did I just ask you to do?"}],
            "conversation_id": conversation_id,
            "stream": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    print("✓ Successfully used conversation context")
    print(f"Response: {data['choices'][0]['message']['content'][:100]}...")

def test_end_conversation():
    print("\n=== Testing Conversation Deletion ===")
    if not conversation_id:
        print("Skipping - no conversation ID from previous test")
        return
        
    response = requests.delete(f"{base_url}/conversations/{conversation_id}")
    assert response.status_code == 200
    print("✓ Successfully deleted conversation")

if __name__ == "__main__":
    try:
        print("Starting API compatibility tests...")
        print("Make sure the server is running on http://localhost:1337")
        time.sleep(2)  # Give user time to read the message
        
        test_list_models()
        test_error_handling()
        test_chat_completion()
        test_conversation_context()
        test_end_conversation()
        
        print("\n✅ All tests completed successfully!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server. Make sure it's running on http://localhost:1337")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")