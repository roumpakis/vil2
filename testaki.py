import numpy as np
import cv2
from PIL import Image

def load_image(image_path):
    """Load an image from a file path."""
    try:
        image = Image.open(image_path).convert("RGB")
        return np.array(image)
    except Exception as e:
        print(f"Error loading image: {e}")
        raise

def save_image(image_array, output_path):
    """Save a numpy array as an image file."""
    try:
        Image.fromarray(image_array.astype(np.uint8)).save(output_path)
        print(f"Image saved to {output_path}")
    except Exception as e:
        print(f"Error saving image: {e}")
        raise

def create_change_mask(before_image, after_image, threshold=30):
    """Create a color change mask and difference image between two images."""
    # Convert images to grayscale
    gray_before = cv2.cvtColor(before_image, cv2.COLOR_RGB2GRAY)
    gray_after = cv2.cvtColor(after_image, cv2.COLOR_RGB2GRAY)
    
    # Compute absolute difference
    diff = cv2.absdiff(gray_before, gray_after)
    
    # Threshold the difference image to get a binary mask
    _, change_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    
    # Map binary mask to RGB colors (Red for changes)
    change_mask_rgb = np.zeros((change_mask.shape[0], change_mask.shape[1], 3), dtype=np.uint8)
    change_mask_rgb[change_mask == 255] = [255, 0, 0]  # Red color for changes
    
    return change_mask_rgb, diff

def main(before_image_path, after_image_path, output_mask_path, output_diff_path):
    """Main function to process images and create a color change mask and difference image."""
    # Load images
    before_image = load_image(before_image_path)
    after_image = load_image(after_image_path)
    
    # Debug: Check if images are loaded properly
    print(f"Before image shape: {before_image.shape}")
    print(f"After image shape: {after_image.shape}")
    
    # Create the change mask and difference image
    change_mask, diff_image = create_change_mask(before_image, after_image)
    
    # Save the change mask and difference image
    save_image(change_mask, output_mask_path)
    save_image(diff_image, output_diff_path)

if __name__ == '__main__':
    # Example usage
    before_image_path = r'D:\app\breles-full-complet\breles\classapp\static\overlays\EMSR746_before.png'  # Path to the before image
    after_image_path = r'D:\app\breles-full-complet\breles\classapp\static\overlays\EMSR746_after.png'   # Path to the after image
    output_mask_path = r'D:\app\breles-full-complet\breles\classapp\changes\EMSR746_change_mask.png'    # Path to save the change mask
    output_diff_path = r'D:\app\breles-full-complet\breles\classapp\changes\EMSR746_diff_image.png'      # Path to save the difference image
    
    main(before_image_path, after_image_path, output_mask_path, output_diff_path)
