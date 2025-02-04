from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash, send_from_directory
import requests
import os
from werkzeug.utils import secure_filename
from .utils import call_blip_api, process_image

main = Blueprint('main', __name__)

UPLOAD_FOLDER = '/tmp/uploads'

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# Serve uploaded files
@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('/tmp/uploads', filename)


# Web Output Endpoint
@main.route('/generate-caption', methods=['POST'])
def generate_caption():
    try:
        if 'image' not in request.files:
            flash('No image file found', 'error')
            return redirect(url_for('main.index'))

        file = request.files['image']
        file_path, filename = process_image(file)
        caption = call_blip_api(file_path)
        image_url = url_for('main.uploaded_file', filename=filename)

        return render_template('result.html', caption=caption, image_url=image_url)
    
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        flash(f"Error: {e}", 'error')
        return redirect(url_for('main.index'))

# api-endpoint
@main.route('/generate-caption-api', methods=['POST'])
def generate_caption_api():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file found'}), 400

        file = request.files['image']
        file_path = process_image(file)
        caption = call_blip_api(file_path)

        return jsonify({'caption': caption})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f"Error: {e}"}), 500