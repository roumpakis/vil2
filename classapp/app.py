import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import base64
import io
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the pre-trained CLIP model and processor
model_name = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(model_name)
model = CLIPModel.from_pretrained(model_name)

# Define possible classes for remote sensing images
prompts = [
    "parking lot", "sea", "river", "lake", "road", "car", "building", "residential area", 
    "commercial area", "industrial area", "forest", "grassland", "cropland", "wetlands", 
    "desert", "mountain", "hill", "valley", "stream", "pond", "dam", "coastline", "beach", 
    "harbor", "airport", "railway track", "bridge", "tunnel", "port", "power plant", 
    "solar farm", "wind farm", "water reservoir", "agricultural field", "greenhouse", 
    "orchard", "vineyard", "timberland", "barren land", "mining site", "quarry", 
    "construction site", "golf course", "park", "playground", "cemetery", "university campus", 
    "hospital", "shopping mall", "office building", "highway", "suburban area", "city center", 
    "historic site", "museum", "theater", "sports stadium", "aquarium", "zoo", "military base", 
    "prison", "hotel", "resort", "campground", "temple", "church", "mosque", "synagogue", 
    "residential block", "office park", "warehouse", "factory", "gas station", "convenience store", 
    "restaurant", "pub", "bank", "library", "post office", "bus station", "train station", 
    "airport runway", "aircraft", "ship", "fishing village", "ferry terminal", "boathouse", 
    "marina", "docks", "farmland", "cattle ranch", "poultry farm", "aquaculture farm", 
    "wildlife sanctuary", "nature reserve", "protected area", "national park", "cultural heritage site", 
    "renewable energy facility"
]

@app.route('/classify_image', methods=['POST'])
def classify_image():
    data = request.get_json()
    if 'image_data' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    
    image_data = data['image_data']
    
    try:
        # Decode Base64 image data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Process the image and prompts
        inputs = processor(images=image, text=prompts, return_tensors="pt", padding=True)

        # Perform classification
        with torch.no_grad():
            outputs = model(**inputs)

        # Compute the similarity scores
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)

        # Find the prompt with the highest probability
        predicted_prompt_idx = torch.argmax(probs, dim=1).item()
        predicted_prompt = prompts[predicted_prompt_idx]

        # Get the corresponding probability for the predicted class
        predicted_probability = probs[0, predicted_prompt_idx].item() * 100
        
        return jsonify({
            'predicted_class': predicted_prompt,
            'probability': f"{predicted_probability:.2f}%"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5080)
