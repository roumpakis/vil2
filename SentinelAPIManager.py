import numpy as np
import rasterio
import matplotlib.pyplot as plt
import requests
from S1API import S1API
from S2API import S2API
from S3API import S3API

class SentinelAPIManager:
    def __init__(self, client_id, client_secret, base_url):
        self.token = self.get_access_token(client_id, client_secret)
        self.base_url = base_url

        # Initialize the API classes
        self.s1_api = S1API(self.token, self.base_url)
        self.s2_api = S2API(self.token, self.base_url)
        self.s3_api = S3API(self.token, self.base_url)

    def get_access_token(self, client_id, client_secret):
        """Authenticate and return an access token."""
        TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        response = requests.post(TOKEN_URL, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]

    def download_all_images(self, bbox, date_from, date_to, cloud_cover, save_as_tiff=True, width=512, height=512):
        s1_path, s2_path, s3_path = None, None, None

        # Get the image paths from the API methods
        try:
            s1_image_tiff = self.s1_api.get_image(bbox, date_from, date_to, save_as_tiff, width, height)
            _,s2_image_tiff = self.s2_api.get_image(bbox, date_from, date_to, cloud_cover, save_as_tiff, width, height)
            #s3_image = self.s3_api.get_image(bbox, date_from, date_to, save_as_tiff, width, height)
            s3_image = None
        except Exception as e:
            print(f"Error downloading images: {e}")
            return None, None, None

        s3_image_array = None
        return  s1_image_tiff, s2_image_tiff, s3_image

    def read_image_as_array(self, image_path):
        """Read a GeoTIFF file and return it as a numpy array."""
        if not image_path:
            return None

        try:
            with rasterio.open(image_path) as src:
                return src.read(1)  # Read the first band
        except Exception as e:
            print(f"Error reading image {image_path}: {e}")
            return None

    def plot_images(self, images, titles, cmap='gray'):
        """Plot the downloaded images using matplotlib."""
        # Ensure images are valid
        valid_images = [img for img in images if img is not None]
        
        if not valid_images:
            print("No valid images to display.")
            return

        # Create subplots
        fig, axes = plt.subplots(1, len(valid_images), figsize=(15, 5))

        for i, ax in enumerate(axes):
            ax.imshow(valid_images[i], cmap=cmap)
            ax.set_title(titles[i])
            ax.axis('off')

        plt.show()
