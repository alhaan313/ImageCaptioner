import requests
import time
from .config import token_key, cerebras_api_key
import os
from werkzeug.utils import secure_filename
from cerebras.cloud.sdk import Cerebras

UPLOAD_FOLDER = '/tmp/uploads'

# Updated list of currently active models
BLIP_MODELS = [
    'Salesforce/blip-image-captioning-large',
    'Salesforce/blip2-flan-t5-xl',
    'moondream/moondream-v1.5'
]

_last_successful_model = None

def process_image(file):
    """Process the uploaded image: save it and return its path."""
    if file.filename == '':
        raise ValueError('No selected file')

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path, filename

def check_huggingface_status(timeout=10):
    """Check if HuggingFace Inference API is operational"""
    try:
        # Try a small test request to a reliable model
        response = requests.get(
            "https://api-inference.huggingface.co/status", 
            headers={'Authorization': f'Bearer {token_key}'},
            timeout=timeout
        )
        return response.status_code == 200
    except Exception:
        return False

def call_blip_api(image_path, max_retries=2, retry_delay=2):
    """Send image to BLIP inference api with retries and wait for model loading"""
    if not check_huggingface_status():
        return "Unable to process image at this time", "HuggingFace Inference API is currently unavailable. Please try again later."
    
    global _last_successful_model
    
    if _last_successful_model:
        models_to_try = [_last_successful_model] + [m for m in BLIP_MODELS if m != _last_successful_model]
    else:
        models_to_try = BLIP_MODELS

    last_error = None
    for model in models_to_try:
        for attempt in range(max_retries):
            try:
                print(f"Trying BLIP model: {model} (attempt {attempt + 1})")
                api_url = f'https://api-inference.huggingface.co/models/{model}'
                headers = {
                    'Authorization': f'Bearer {token_key}',
                    'Content-Type': 'application/json'
                }
                
                # Convert image to base64
                import base64
                with open(image_path, "rb") as f:
                    image_bytes = base64.b64encode(f.read()).decode('utf-8')
                
                # Send as JSON with base64 encoded image
                payload = {
                    "inputs": f"data:image/jpeg;base64,{image_bytes}"
                }
                
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                print(f"Response from {model}: Status {response.status_code}")
                print(f"Response content: {response.text[:200]}")  # Print first 200 chars of response
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        _last_successful_model = model
                        return data[0], None  # Some models return direct string
                    elif isinstance(data, dict):
                        result = data.get("generated_text", data.get("caption", str(data)))
                        _last_successful_model = model
                        return result, None
                
                if response.status_code != 404:
                    time.sleep(retry_delay)
                    continue
                
                last_error = f"Status {response.status_code} from {model}"
                break
                
            except Exception as e:
                print(f"Error with {model}: {str(e)}")
                last_error = str(e)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
    
    print(f"All BLIP models failed. Last error: {last_error}")
    return "An interesting image", f"Image processing service temporarily unavailable. Last error: {last_error}"

def get_emotion_prompt(emotion):
    prompts = {
        'happy': "Generate an upbeat and cheerful caption that emphasizes joy and positivity",
        'sad': "Create a thoughtful, melancholic caption that captures emotional depth",
        'thoughtful': "Write a philosophical and contemplative caption that provokes deep thinking",
        'geeky': "Generate a technically-oriented caption with subtle tech/geek culture references",
        'romantic': "Create a romantic and poetic caption that emphasizes beauty and emotion",
        'funny': "Write a humorous and witty caption that makes people smile"
    }
    return prompts.get(emotion, "Generate a creative caption")

def generate_cerebras_captions(image_path, emotion, base_caption):
    """Generate multiple captions using Cerebras API"""
    try:
        client = Cerebras(api_key=cerebras_api_key)
        
        messages = [
            {
                "role": "system",
                "content": f"You are a creative caption generator. {get_emotion_prompt(emotion)}"
            },
            {
                "role": "user",
                "content": f"Based on this image description: '{base_caption}', generate 5 unique and creative captions, numbered 1-5."
            }
        ]
        
        stream = client.chat.completions.create(
            messages=messages,
            model="llama3.1-8b",
            stream=True,
            max_completion_tokens=1024,
            temperature=0.7,
            top_p=1
        )

        # Collect the response
        full_response = ""
        for chunk in stream:
            full_response += (chunk.choices[0].delta.content or "")
        
        captions = [cap.strip() for cap in full_response.split("\n") 
                    if cap.strip() and any(cap.startswith(str(i)) for i in range(1,6))]
        
        return captions[:5], None
        
    except Exception as e:
        error_message = "Our AI enhancement service is temporarily unavailable. We've provided a base caption for your image."
        return [], error_message