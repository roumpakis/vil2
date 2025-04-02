import numpy as np
import cv2
from PIL import Image
from flask import Flask, request, jsonify
import base64
import io

app = Flask(__name__)

def load_image_from_base64(image_base64):
    try:
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        return np.array(image)
    except Exception as e:
        raise Exception(f"Error loading image: {e}")

def create_change_mask(before_image, after_image, threshold=30):
    gray_before = cv2.cvtColor(before_image, cv2.COLOR_RGB2GRAY)
    gray_after = cv2.cvtColor(after_image, cv2.COLOR_RGB2GRAY)
    
    diff = cv2.absdiff(gray_before, gray_after)
    
    _, change_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    
    change_mask_rgb = np.zeros((change_mask.shape[0], change_mask.shape[1], 3), dtype=np.uint8)
    change_mask_rgb[change_mask == 255] = [255, 0, 0]
    
    return change_mask_rgb, diff

@app.route('/detect_change', methods=['POST'])
def detect_change():
    try:
        data = request.json
        before_image_base64 = data.get('before_image')
        after_image_base64 = data.get('after_image')

        before_image = load_image_from_base64(before_image_base64)
        after_image = load_image_from_base64(after_image_base64)

        change_mask, diff_image = create_change_mask(before_image, after_image)
        
        # Convert to base64 to send the result
        mask_image_pil = Image.fromarray(change_mask)
        diff_image_pil = Image.fromarray(diff_image)

        mask_image_bytes = io.BytesIO()
        diff_image_bytes = io.BytesIO()

        mask_image_pil.save(mask_image_bytes, format='PNG')
        diff_image_pil.save(diff_image_bytes, format='PNG')

        return jsonify({
            'change_mask': base64.b64encode(mask_image_bytes.getvalue()).decode('utf-8'),
            'diff_image': base64.b64encode(diff_image_bytes.getvalue()).decode('utf-8')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5012, host='0.0.0.0')
