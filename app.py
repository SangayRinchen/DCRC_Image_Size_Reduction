from flask import Flask, jsonify
from flasgger import Swagger, swag_from
import os
import logging
from PIL import Image


app = Flask(__name__)
Swagger(app)


# Function to get image data and size
def get_image_data_size(image_path):
    with open(image_path, 'rb') as file:
        image_data = file.read()

    image_size_kb = len(image_data) / 1024

    return image_data, image_size_kb

# Function to get image details
def get_image_details(image_path):
    ndi = os.path.basename(os.path.dirname(image_path))
    image_id = os.path.basename(image_path)[:-len('_frontal.jpg')]
    image_size_kb = int(os.path.getsize(image_path) / 1024)

    return {
        'image_name': os.path.basename(image_path),
        'image_size': image_size_kb,
        'ndi': ndi,
        'image_id': image_id
    }

# Function to compress and save image
def compress_and_save_image(ndi, image_id, compressed_path, target_size_kb=1024):
    try:
        # Construct the path to the original image
        original_path = os.path.join('images', ndi, f'{image_id}_frontal.jpg')
        original_path = os.path.abspath(original_path)

        # Use absolute path for compressed image
        compressed_path = os.path.abspath(compressed_path)

        # Open the original image
        with Image.open(original_path) as img:
            # Start with a high-quality value
            quality = 85
            while True:
                # Compress the image with the current quality parameter
                img.save(compressed_path, quality=quality)

                # Check the size of the compressed image
                compressed_size_kb = os.path.getsize(compressed_path) / 1024

                # If the size is less than the target, break the loop
                if compressed_size_kb < target_size_kb:
                    break

                # Decrease the quality for the next iteration
                quality -= 5

                # Ensure the quality doesn't go below a certain threshold
                if quality < 5:
                    quality = 5
                    break

        return True
    except Exception as e:
        logging.error(f'Error compressing image: {str(e)}')
        return False

# Function to create compressed images
def create_compressed_images(images):
    compressed_images = []

    for image_detail in images:
        ndi = image_detail['ndi']
        image_id = image_detail['image_id']
        original_path = os.path.join('images', ndi, f'{image_id}_frontal.JPG')  # Use uppercase extension

        compressed_folder = os.path.join('compressed_images', ndi)

        # Create the compressed folder if it doesn't exist
        os.makedirs(compressed_folder, exist_ok=True)

        # Compressed image path without the "compressed" prefix
        compressed_path = os.path.join(compressed_folder, f'{image_id}_frontal.jpg')

        # Compress and save the image
        if compress_and_save_image(ndi, image_id, compressed_path):
            compressed_images.append({
                'compressed_image_name': os.path.basename(compressed_path),
                'compressed_image_path': compressed_path,
                'original_image_name': image_detail['image_name']
            })

    return compressed_images

@app.route('/get_images', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'A successful response',
            'schema': {
                'type': 'object',
                'properties':
                  {
                    'image_name': {
                      'type': 'string',
                      'description': 'Image name'
                    },
                    'image_size': {
                      'type': 'integer',
                      'description': 'Image size in KB'
                    },
                    'image_id': {
                      'type': 'string',
                      'description': 'Image ID'
                    }
                  }
              }
        }
    }
})
def get_images():
    images = []

    try:
        images_directory = "images"
        # Iterate over all files in the images directory
        for root, dirs, files in os.walk(images_directory):
            for filename in files:
                if filename.lower().endswith('_frontal.jpg'):
                    # Construct the path to the image
                    image_path = os.path.join(root, filename)

                    # Get image details
                    image_detail = get_image_details(image_path)

                    # Only include images larger than 1 MB
                    if image_detail['image_size'] > 1024:
                        images.append(image_detail)

        return jsonify(images)
    except Exception as e:
        logging.error(f'An error occurred: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

@app.route('/compress_images', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'A successful response',
            'schema': {
                'type': 'object',
                'properties':
                  {
                    'compressed_image_name': {
                      'type': 'string',
                      'description': 'Compressed Image name'
                    },
                    'compressed_image_path': {
                      'type': 'string',
                      'description': 'Compressed Image path'
                    },
                    'original_image_name': {
                      'type': 'string',
                      'description': 'Original Image name'
                    }
                  }
              }
        }
    }
})
def compress_images():
    try:
        # Call the first API to get image details
        response = app.test_client().get('/get_images')
        images = response.json
        print("Retrieved images:", images)

        # Create compressed images
        compressed_images = create_compressed_images(images)
        print("Compressed images:", compressed_images)

        return jsonify(compressed_images)
    except Exception as e:
        logging.error(f'An error occurred: {str(e)}')
        return {'error': 'Internal Server Error'}, 500

if __name__ == '__main__':
    app.run(debug=True)
