import requests
from .config import token_key, cerebras_api_key
import os
from werkzeug.utils import secure_filename
from cerebras.cloud.sdk import Cerebras

UPLOAD_FOLDER = '/tmp/uploads'

def process_image(file):
    """Process the uploaded image: save it and return its path."""
    if file.filename == '':
        raise ValueError('No selected file')

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path, filename

def call_blip_api(image_path):
    # This function will send the image to the Blip inference api
    api_url = 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base'
    headers = {'Authorization' : f'Bearer {token_key}'}
    with open(image_path, "rb") as f:
        data = f.read()
    response = requests.post(api_url, headers=headers, data=data)

    if response.status_code == 200:
        data = response.json()
        return data[0]["generated_text"]
    else:
        return f"Error: {response.status_code} - {response.text}"

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