# s1_api.py
import requests
from io import BytesIO

class S1API:
    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url

    def get_image(self, bbox, date_from, date_to, save_as_tiff=False, width=512, height=512):
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["VV"], output: { bands: 1, sampleType: SampleType.FLOAT32 } };
        }
        function evaluatePixel(samples) {
            return [samples.VV];
        }
        """
        request_payload = self.create_request_payload("sentinel-1-grd", bbox, date_from, date_to, evalscript, width, height)
        return self._download_image(request_payload, save_as_tiff)

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

    def _download_image(self, request_payload, save_as_tiff):
        headers = {"Accept": "image/tiff", "Authorization": f"Bearer {self.token}"}
        
        try:
            print("Downloading Sentinel-1 image...")
            response = requests.post(self.base_url, json=request_payload, headers=headers, stream=True)
            response.raise_for_status()

            # Store the image in memory
            tiff_data = BytesIO()
            for chunk in response.iter_content(chunk_size=1024):
                tiff_data.write(chunk)

            tiff_data.seek(0)  # Reset the pointer to the beginning

            # If the user wants to save it as a file
            if save_as_tiff:
                with open("sentinel1.tiff", "wb") as file:
                    file.write(tiff_data.read())
                print(f"Sentinel-1 image saved as sentinel1.tiff")
            
            return tiff_data  # Return the TIFF image in memory

        except requests.exceptions.RequestException as e:
            print(f"Error downloading Sentinel-1 image: {e}")
            return None
