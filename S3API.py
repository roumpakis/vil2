import requests
import os
import rasterio
import numpy as np

class S3API:
    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url

    def get_image(self, bbox, date_from, date_to, save_path, width=1024, height=1024):
        # Define the script to fetch specific bands (radiance)
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["Oa08_radiance", "Oa06_radiance", "Oa04_radiance"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
            return [sample.Oa08_radiance, sample.Oa06_radiance, sample.Oa04_radiance];
        }
        """
        # Create request payload
        request_payload = self.create_request_payload("sentinel-3", bbox, date_from, date_to, evalscript, width, height)
        
        # Download image and return as NumPy array
        tiff_path = self._download_image(request_payload, save_path)
        if tiff_path:
            return self.read_image_as_array(tiff_path)
        return None

    def create_request_payload(self, satellite_type, bbox, date_from, date_to, evalscript, width, height):
        return {
            "input": {
                "bounds": {
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                    "bbox": bbox,
                },
                "data": [
                    {
                        "type": satellite_type,
                        "dataFilter": {
                            "timeRange": {"from": date_from, "to": date_to},
                        }
                    }
                ],
            },
            "output": {"width": width, "height": height},
            "evalscript": evalscript,
        }

    def _download_image(self, request_payload, save_path):
        headers = {"Accept": "image/tiff", "Authorization": f"Bearer {self.token}"}

        try:
            print("Downloading Sentinel-3 image...")
            # Send request to download image
            response = requests.post(self.base_url, json=request_payload, headers=headers, stream=True)
            response.raise_for_status()

            # Ensure the directory exists
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path))

            # Save the image in TIFF format
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

            print(f"Sentinel-3 image saved as {save_path}")
            return save_path

        except requests.exceptions.RequestException as e:
            print(f"Error downloading Sentinel-3 image: {e}")
            return None

    def read_image_as_array(self, image_path):
        """Read the downloaded GeoTIFF file and return it as a NumPy array."""
        try:
            with rasterio.open(image_path) as src:
                # Read the image data and return the first band (or all bands if needed)
                return src.read()  # This reads all bands as a 3D NumPy array
        except Exception as e:
            print(f"Error reading image as array: {e}")
            return None
