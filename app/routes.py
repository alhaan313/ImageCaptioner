from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash, send_from_directory
import requests
import os
from werkzeug.utils import secure_filename
from .utils import call_blip_api, process_image, generate_cerebras_captions

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
        tone = request.form.get('tone', 'professional')
        file_path, filename = process_image(file)
        
        print(f"Processing image: {filename}")
        
        # Get base caption from BLIP
        base_caption, error = call_blip_api(file_path)
        print(f"Base caption: {base_caption}")
        print(f"BLIP error: {error}")
        
        # Always proceed with Cerebras, using whatever caption we got
        captions, cerebras_error = generate_cerebras_captions(file_path, tone, base_caption)
        
        image_url = url_for('main.uploaded_file', filename=filename)

        # Don't redirect on error, just show the results with whatever we got
        return render_template('result.html', 
                             base_caption=base_caption or "Image processing incomplete",
                             captions=captions,
                             error_message=error or cerebras_error,
                             image_url=image_url,
                             tone=tone)
    
    except Exception as e:
        print(f"Critical Error in generate_caption: {str(e)}")
        flash("Unable to process image. Please try again.", 'error')
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


@main.route('/api/status')
def api_status():
    from .utils import check_huggingface_status
    return jsonify({'operational': check_huggingface_status()})