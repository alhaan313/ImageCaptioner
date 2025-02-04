import unittest
import sys
import os

# Ensure the `app` module is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # Now it should work


class TestImageCaptioning(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_image_upload_and_caption_generation(self):
        with open(r'uploads\29699386d0ad9d42d27d76d2ba584adb.jpg', 'rb') as img:
            response = self.client.post('/generate-caption', 
                data={'image': (img, 'sample.jpg')}, 
                content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('caption', response.json)
            self.assertIsInstance(response.json['caption'], str)

if __name__ == '__main__':
    unittest.main()
