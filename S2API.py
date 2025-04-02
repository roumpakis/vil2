import requests
from io import BytesIO
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from datetime import timedelta
from PIL import Image
import matplotlib.pyplot as plt

class S2API:
    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url

    def get_image(self, bbox, date_from, date_to, cloud_cover, save_as_tiff=False, width=512, height=512):
        img_array , tiff_data= self.get_all_bands( bbox, date_from, date_to, cloud_cover, False, width, height)
        return img_array, tiff_data
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B02", "B03", "B04"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """
        request_payload = self.create_request_payload("sentinel-2-l1c", bbox, date_from, date_to, cloud_cover, evalscript, width, height)
        return self._download_image(request_payload, save_as_tiff)

    def create_request_payload(self, satellite_type, bbox, date_from, date_to, cloud_cover, evalscript, width, height):
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
                            "maxCloudCoverage": cloud_cover
                        }
                    }
                ],
            },
            "output": {"width": width, "height": height},
            "evalscript": evalscript,
        }

    def _download_image(self, request_payload, save_as_tiff):
        headers = {"Accept": "image/tiff", "Authorization": f"Bearer {self.token}"}

        try:
            print("Downloading Sentinel-2 image...")
            response = requests.post(self.base_url, json=request_payload, headers=headers, stream=True)
            response.raise_for_status()

            # Store the image in memory
            tiff_data = BytesIO()
            for chunk in response.iter_content(chunk_size=1024):
                tiff_data.write(chunk)

            tiff_data.seek(0)  # Reset the pointer to the beginning

            # If the user wants to save it as a file
            if save_as_tiff:
                with open("sentinel2.tiff", "wb") as file:
                    file.write(tiff_data.read())
                print(f"Sentinel-2 image saved as sentinel2.tiff")

            return tiff_data  # Return the TIFF image in memory

        except requests.exceptions.RequestException as e:
            print(f"Error downloading Sentinel-2 image: {e}")
            return None

    def get_image_quick(self, bbox, date_from, date_to, cloud_cover, save_as_tiff=False, width=512, height=512):
        """ Λήψη εικόνας Sentinel-2 και μετατροπή της σε NumPy array """
        tiff_data = self.get_image(bbox, date_from, date_to, cloud_cover, save_as_tiff, width, height)

        if tiff_data is None:
            print("⚠ No image data received.")
            return None

        # Διαβάζουμε το TIFF με rasterio
        with MemoryFile(tiff_data) as memfile:
            with memfile.open() as dataset:
                img_array = dataset.read([1, 2, 3])  # Read RGB bands
                img_array = np.moveaxis(img_array, 0, -1)  # Rearrange dimensions to (H, W, C)

        return img_array  # Return NumPy array
    

    
    def get_all_bands(self, bbox, date_from, date_to, cloud_cover, save_as_tiff=False, width=512, height=512):
        # Το evalscript για όλες τις μπάντες του Sentinel-2
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"], 
                     output: { bands: 12, sampleType: "FLOAT32" } };
        }
        function evaluatePixel(sample) {
            return [sample.B01, sample.B02, sample.B03, sample.B04, sample.B05, sample.B06, sample.B07, sample.B08, sample.B8A, sample.B09, sample.B11, sample.B12];
        }
        """

        # Δημιουργία του request payload
        request_payload = {
            "input": {
                "bounds": {
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                    "bbox": bbox,
                },
                "data": [
                    {
                        "type": "sentinel-2-l1c",
                        "dataFilter": {
                            "timeRange": {"from": date_from, "to": date_to},
                            "maxCloudCoverage": cloud_cover
                        }
                    }
                ],
            },
            "output": {"width": width, "height": height},
            "evalscript": evalscript,
        }

        # Header με το token
        headers = {"Accept": "image/tiff", "Authorization": f"Bearer {self.token}"}

        try:
            # Αποστολή του αιτήματος για λήψη της εικόνας
            print("Downloading Sentinel-2 image...")
            response = requests.post(self.base_url, json=request_payload, headers=headers, stream=True)
            response.raise_for_status()

            # Αποθήκευση της εικόνας σε μνήμη
            tiff_data = BytesIO()
            for chunk in response.iter_content(chunk_size=1024):
                tiff_data.write(chunk)

            tiff_data.seek(0)  # Επαναφορά του δείκτη στην αρχή

            # Αν θέλουμε να αποθηκεύσουμε την εικόνα ως TIFF
            if save_as_tiff:
                with open("sentinel2_all_bands.tiff", "wb") as file:
                    file.write(tiff_data.read())
                print(f"Sentinel-2 all bands image saved as sentinel2_all_bands.tiff")

            # Διαβάζουμε το TIFF με το rasterio
            with MemoryFile(tiff_data) as memfile:
                with memfile.open() as dataset:
                    # Διαβάζουμε όλες τις μπάντες
                    img_array = dataset.read([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])  # Όλες οι 12 μπάντες
                    img_array = np.moveaxis(img_array, 0, -1)  # Επαναταξινόμηση των διαστάσεων σε (H, W, C)

            # Εμφάνιση των μπαντών σε ένα πλοτ
            fig, axes = plt.subplots(3, 4, figsize=(15, 10))  # Δημιουργία 3x4 πλοτ
            axes = axes.flatten()

            for i in range(12):
                axes[i].imshow(img_array[:, :, i], cmap='gray')
                axes[i].set_title(f"Band {i + 1}")
                axes[i].axis('off')

            plt.tight_layout()
            plt.show()

            return img_array,tiff_data  # Επιστροφή του NumPy array με όλες τις μπάντες

        except requests.exceptions.RequestException as e:
            print(f"Error downloading Sentinel-2 image: {e}")
            return None
        
