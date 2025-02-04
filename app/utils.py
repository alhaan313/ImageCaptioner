import requests
from .config import token_key
import os
from werkzeug.utils import secure_filename

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