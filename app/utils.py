import requests
import time
import base64
from datetime import datetime, UTC, timedelta
from jwt import encode
from .config import token_key, cerebras_api_key, phosus_api_key, phosus_key_id
from cerebras.cloud.sdk import Cerebras
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = '/tmp/uploads'

_cached_token = None
_token_expiry = None

def get_phosus_token():
    """Generate JWT token for Phosus API with caching"""
    global _cached_token, _token_expiry
    
    current_time = datetime.now(UTC)
    
    if _cached_token and _token_expiry and _token_expiry > current_time + timedelta(minutes=5):
        return _cached_token
    
    expiry_time = current_time + timedelta(days=1)
    payload = {
        'account_key_id': phosus_key_id,
        'exp': expiry_time,
        'iat': current_time
    }
    
    _cached_token = encode(payload, key=phosus_api_key, algorithm='HS256')
    _token_expiry = expiry_time
    return _cached_token

def call_phosus_api(image_path):
    """Get caption from Phosus API"""
    try:
        jwt_token = get_phosus_token()
        headers = {"authorizationToken": jwt_token}
        
        with open(image_path, "rb") as f:
            base64_img_str = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {"image_b64": base64_img_str}
        
        print("Calling Phosus API...")
        response = requests.post(
            "https://api.phosus.com/icaption/v1",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["prediction"], None
            
        try:
            error_data = response.json()
            if error_data.get("error", {}).get("msg") == "Insufficient Credit":
                print("Phosus API Credit Exhausted")
                return "An interesting image", "API credit limit reached. Please try again later."
        except:
            pass
            
        return "An interesting image", f"Error: Status {response.status_code}"
        
    except Exception as e:
        print(f"Phosus API Error: {str(e)}")
        return "An interesting image", str(e)

def check_huggingface_status(timeout=10):
    """Check if Phosus API is operational"""
    try:
        jwt_token = get_phosus_token()
        headers = {"authorizationToken": jwt_token}
        
        # Simple test request to Phosus API
        response = requests.get(
            "https://api.phosus.com/status",  # Assuming there's a status endpoint
            headers=headers,
            timeout=timeout
        )
        return response.status_code == 200
    except Exception:
        return False

def process_image(file):
    """Process the uploaded image: save it and return its path."""
    if file.filename == '':
        raise ValueError('No selected file')

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path, filename

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
                "content": (
                    f"You are a creative caption generator. {get_emotion_prompt(emotion)} "
                    "Format each caption on a new line starting with a number and a period. "
                    "Keep responses clean and concise without additional formatting or quotes."
                )
            },
            {
                "role": "user",
                "content": f"Based on this image description: '{base_caption}', generate 5 unique captions."
            }
        ]
        
        stream = client.chat.completions.create(
            messages=messages,
            model="llama3.1-8b",
            stream=True,
            max_completion_tokens=1024,
            temperature=0.8
        )

        full_response = ""
        for chunk in stream:
            full_response += (chunk.choices[0].delta.content or "")
        
        # Clean up the response
        captions = []
        for line in full_response.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 6)):
                caption = line[line.find('.')+1:].strip()
                caption = caption.strip('"').strip("'")  # Remove quotes if present
                captions.append(caption)
        
        return captions[:5], None
        
    except Exception as e:
        error_message = f"Creative caption generation failed: {str(e)}"
        return [], error_message