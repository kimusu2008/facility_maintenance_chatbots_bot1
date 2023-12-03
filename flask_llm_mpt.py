from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Databricks endpoint details
API_BASE = "https://adb-3849325689522069.9.azuredatabricks.net"
ENDPOINT = "serving-endpoints/mpt7b/invocations"
API_KEY = "dapid5958d21d09377a327be2de83d1a9eb5-2"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

@app.route('/openai/deployments/mpt7b/chat/completions', methods=['POST'])
def custom_predict():
    try:
        # Preprocess the incoming request data
        input_data = preprocess(request.get_json())

        # Prepare data for Databricks endpoint
        data = {"dataframe_split": {"data": [input_data]}}

        # Call Databricks endpoint
        response = requests.post(f"{API_BASE}/{ENDPOINT}", json=data, headers=HEADERS)
        response.raise_for_status()

        # Postprocess response
        result = postprocess(response.json())

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def preprocess(data):
    """
    Format input data to match Databricks endpoint input format.
    """
    # Extract message content from request
    messages = data.get("messages", [])
    if not messages or "content" not in messages[0]:
        raise ValueError("Invalid input format. 'messages' must contain 'content'.")

    #user_message = messages[0]["content"]
    user_message = ' '.join([item['content'] for item in data['messages']])

    # Format data to match Databricks endpoint input format
    preprocessed_data = f"Question: {user_message} Answer: "
    #preprocessed_data = f"{user_message}"

    # systemsg = messages[0]["content"]
    # question = messages[1]["content"]
    #preprocessed_data = f"{systemsg} Your Question is: {question}"

    return preprocessed_data


import time

def postprocess(databricks_response):
    """
    Format Databricks response to match OpenAI API response format.
    """
    # Dummy values API details
    unique_id = f"chatcmpl-{int(time.time())}"
    prompt_tokens = 12
    completion_tokens = 113
    total_tokens = 125

    # Extracting response from Databricks' API
    predictions = databricks_response.get('predictions', [])
    databricks_content = predictions[0] if predictions else "No response"

    # Format response to match OpenAI API response format
    response = {
        "id": unique_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "mpt7b",  # Update as per the actual model used
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": databricks_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    }
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234)
