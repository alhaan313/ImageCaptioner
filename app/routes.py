from flask import Blueprint, render_template, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename
from config import token_key

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/generate-caption', methods=['POST'])
def generate_caption():
    if 'image' not in request.files:
        return jsonify({'error' : 'No image file found'}), 400
    
    file = request.files['image']

    if file.filename == '':
        return jsonify({'error' : 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        caption = call_blip_api(file_path)

        return jsonify({'caption' : caption})

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