import os
import re
import time
import json
import time
import shutil
import numpy as np
import cv2
import os
from PIL import Image
import io
import os
import zipfile
import requests
import io
from create_monit_gif import create_monit_gif
#from generate_raster_mask import generate_raster_mask
from shapely.geometry import box, mapping
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from rasterio.io import MemoryFile
from rasterio.warp import reproject, Resampling
from PIL import Image
import folium
from folium import GeoJson, GeoJsonPopup, GeoJsonTooltip, LayerControl
from datetime import datetime, timedelta
from SentinelAPIManager import SentinelAPIManager
from CRMAPI import CRMAPI
from create_event_masks import create_event_masks
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    DownloadRequest,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    bbox_to_dimensions,
)

import os
import shutil

class Utils:  
    def __init__(self):
        print("Utils class initialized.")

    def setup_all_data_folder(self,base_path):
        """ Δημιουργεί φάκελο all_data και μετακινεί τα αρχεία _maps και _results εκεί. """
        all_data_path = os.path.join(base_path, "static","all_data")
        os.makedirs(all_data_path, exist_ok=True)


        for filename in os.listdir(base_path):
            if "_maps" in filename or "_results" in filename:
                src_path = os.path.join(base_path, filename)
                dst_path = os.path.join(all_data_path, filename)

                # Έλεγχος αν ο προορισμός ήδη υπάρχει
                if not os.path.exists(dst_path):
                    shutil.move(src_path, dst_path)
                    print(f"Moved: {filename}")
                else:
                    print(f"Skipping (exists): {filename}")
            print(f"Όλα τα σχετικά αρχεία μεταφέρθηκαν στο: {all_data_path}")

    def find_unique_emsr(self,all_data_path):
        """ Επιστρέφει μια λίστα με μοναδικά EMSR IDs από τα αρχεία στον φάκελο all_data. """
        unique_emsr = set()
        
        for filename in os.listdir(all_data_path):
            parts = filename.split("_")
            for part in parts:
                if part.startswith("EMSR") and part[4:].isdigit():  # Π.χ. EMSR123
                    unique_emsr.add(part)

        return sorted(unique_emsr)
    # === 1. DOWNLOAD ZIP FILE ===
    def download_file(self,url, save_path):
        print(f"Starting download from {url}...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Download completed: {save_path}")
        else:
            print(f"❌ Download failed! HTTP {response.status_code}")
            exit(1)

    # === 2. UNZIP FILES (INCLUDING NESTED ZIPS) ===
    def extract_zip(self,zip_path, extract_to):
        print(f"📂 Extracting: {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        for root, _, files in os.walk(extract_to):
            for file in files:
                if file.endswith(".zip"):
                    zip_file_path = os.path.join(root, file)
                    zip_extract_path = os.path.splitext(zip_file_path)[0]
                    with zipfile.ZipFile(zip_file_path, 'r') as nested_zip:
                        nested_zip.extractall(zip_extract_path)
                    os.remove(zip_file_path)
        
        print(f"✅ Extraction completed: {extract_to}")

    # === 3. FIND ALL JSON FILES ORGANIZED BY AOI (EXCLUDING IMAGE FOOTPRINTS) ===
    def find_json_files(self,base_dir):
        json_files_by_aoi = {}
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".json") and "imageFootprint" not in file:
                    file_path = os.path.join(root, file)
                    
                    # Load JSON and check for image footprints in metadata
                    with open(file_path, 'r', encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if not isinstance(data, dict) or "features" not in data:
                        continue
                    
                    # Skip JSONs that contain 'footprint' or 'scene_id' in properties
                    contains_footprint = any(
                        "footprint" in feature.get("properties", {}).keys() or
                        "scene_id" in feature.get("properties", {}).keys()
                        for feature in data["features"]
                    )
                    if contains_footprint:
                        print(f"🚫 Skipping footprint JSON: {file}")
                        continue
                    
                    # Extract AOI name from file name
                    aoi = next((part for part in file.split("_") if part.startswith("AOI")), "Unknown_AOI")
                    
                    if aoi not in json_files_by_aoi:
                        json_files_by_aoi[aoi] = []
                    
                    json_files_by_aoi[aoi].append(file_path)
        
        return json_files_by_aoi
    # === 4. CREATE MAPS FOR EACH AOI ===
    def create_maps_by_aoi(self,json_files_by_aoi, all_images_bounds, s2_image, output_dir="maps"):
        os.makedirs(output_dir, exist_ok=True)
        aoi_num = 0
        for aoi, json_files in json_files_by_aoi.items():
            m = folium.Map(location=[0, 0], zoom_start=13)
            first_valid_coord = None
            
            # Add GeoJSON features to the map
            for json_file in json_files:
                with open(json_file, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                
                if not isinstance(data, dict) or "features" not in data or not isinstance(data["features"], list):
                    print(f"❌ Skipping {json_file}: Invalid JSON structure!")
                    continue
                
                features = data["features"]
                if not features:
                    print(f"❌ Skipping {json_file}: Empty 'features' list!")
                    continue
                
                if not first_valid_coord:
                    for feature in features:
                        geometry = feature.get("geometry", {})
                        if geometry.get("type") == "Polygon" and "coordinates" in geometry:
                            coords = geometry["coordinates"]
                            if isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list) and len(coords[0]) > 0:
                                first_valid_coord = coords[0][0]
                                break
                
                geojson_layer = GeoJson(
                    {"type": "FeatureCollection", "features": features},
                    name=os.path.basename(json_file),
                    popup=GeoJsonPopup(
                        fields=list(features[0]["properties"].keys()),
                        aliases=[key.replace("_", " ").title() for key in features[0]["properties"].keys()],
                        localize=True
                    ),
                    tooltip=GeoJsonTooltip(
                        fields=list(features[0]["properties"].keys())[:2],
                        aliases=["Field 1", "Field 2"],
                        sticky=True
                    )
                )
                geojson_layer.add_to(m)
            
            # Set the map's location and zoom based on the first valid coordinate
            if first_valid_coord:
                m.location = [first_valid_coord[1], first_valid_coord[0]]
                m.zoom_start = 10
            
            # Add the Sentinel-2 image as overlay
            bbox = all_images_bounds[aoi_num]
            folium.raster_layers.ImageOverlay(
                image=s2_image[aoi_num],
                bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
                name="Sentinel-2 Image",
                opacity=1,
            ).add_to(m)
            
            # Add Layer Control
            LayerControl().add_to(m)
            
            # Add JavaScript for "Select All" / "Unselect All" buttons
            select_all_js = """
            <script>
            function toggleLayers(selectAll) {
                var checkboxes = document.querySelectorAll('input[type=checkbox]');
                for (var i = 0; i < checkboxes.length; i++) {
                    if (checkboxes[i].parentElement.textContent.trim() !== "Base Layer") {
                        checkboxes[i].checked = selectAll;
                        checkboxes[i].dispatchEvent(new Event('click'));
                    }
                }
            }
            </script>
            <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; background: white; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.3);">
                <button onclick="toggleLayers(true)">Select All</button>
                <button onclick="toggleLayers(false)">Unselect All</button>
            </div>
            """

            # Save the map as an HTML file
            output_file = os.path.join(output_dir, f"{aoi}_map.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(m.get_root().render().replace("</body>", select_all_js + "</body>"))
            
            print(f"✅ Map saved as '{output_file}'")
            
            aoi_num += 1


    def convert_tiff_for_folium(self,tiff_bytes):
        """Convert a TIFF (BytesIO) to PNG (BytesIO) and extract bounds for Folium."""
        
        # Ensure BytesIO starts at the beginning
        tiff_bytes.seek(0)
        
        # Open TIFF using rasterio MemoryFile
        with MemoryFile(tiff_bytes) as memfile:
            with memfile.open(driver="GTiff") as dataset:  # ✅ Explicit driver
                print("Opened TIFF successfully!")
                
                # Read the first band
                image_array = dataset.read(1).astype(np.float32)

                # Normalize image to 0-255
                image_array = 255 * (image_array - np.min(image_array)) / (np.max(image_array) - np.min(image_array))
                image_array = image_array.astype(np.uint8)

                # Convert to PNG
                img = Image.fromarray(image_array)
                png_bytes = io.BytesIO()
                img.save(png_bytes, format="PNG")
                png_bytes.seek(0)

                # Get bounding box (for positioning in Folium)
                bounds = dataset.bounds
                print(f"Bounds: {bounds}")

                return png_bytes, bounds

    def sentinel2_tiff_to_numpy(self,tiff_bytes, bands=[4]):  # Default: Red band (B4)
        """Convert Sentinel-2 TIFF (BytesIO) to a NumPy array."""
        
        tiff_bytes.seek(0)  # Ensure BytesIO is at the start
        
        with MemoryFile(tiff_bytes) as memfile:
            with memfile.open(driver="GTiff") as dataset:
                print("Opened Sentinel-2 TIFF successfully!")

                # Read selected bands
                img_array = dataset.read(bands)  # Read bands (1-based index)

                # Get the bounding box (for folium)
                bounds = dataset.bounds

                return img_array, bounds


    def format_date(self,dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # Σωστή μορφή με 'Z' στο τέλος

    # Convert BytesIO PNG to NumPy array

    def tiff_to_numpy(self,tiff_bytes):
        """Convert a TIFF (BytesIO) file to a NumPy array."""
        
        tiff_bytes.seek(0)  # Ensure BytesIO is at the beginning
        
        with MemoryFile(tiff_bytes) as memfile:
            with memfile.open(driver="GTiff") as dataset:
                print("Opened TIFF successfully!")
                
                # Read the first band (grayscale) as a NumPy array
                img_array = dataset.read(1)  # Read first band (1-based index)
                
                # Get the bounding box for georeferencing
                bounds = dataset.bounds

                return img_array, bounds


    def check_bands_in_tiff(self,tiff_bytes):
        """Check how many bands are available in the TIFF file."""
        tiff_bytes.seek(0)  # Reset to the start of the BytesIO stream
        
        with rasterio.open(tiff_bytes) as dataset:
            # Get the number of bands
            band_count = dataset.count
            print(f"Number of bands in the TIFF: {band_count}")
            
            # List all band numbers
            bands = [i for i in range(1, band_count + 1)]
            print(f"Available bands: {bands}")
            
        return band_count, bands

    
    # Function to save image as PNG
    def save_as_png(self,image_path, output_path):
        with rasterio.open(image_path) as src:
            image = src.read(1)  # Read first band
            plt.imshow(image, cmap="gray")
            plt.axis("off")
            plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
            plt.close()
    # ✅ Το Cesium Ion Access Token σου
    CESIUM_ION_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJjZmQ5ZThlMi05OTZjLTQyNzUtOWE4OS0zMDljMzY3YWMyNjQiLCJpZCI6MjMyNzg2LCJpYXQiOjE3MjI4NzYyNTF9._EaN2cJDoDrXjzQn1G5qUaWtYR--Y-YUM92-H6mYnkQ"

# ✅ Το Cesium Ion Access Token σου
    CESIUM_ION_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJjZmQ5ZThlMi05OTZjLTQyNzUtOWE4OS0zMDljMzY3YWMyNjQiLCJpZCI6MjMyNzg2LCJpYXQiOjE3MjI4NzYyNTF9._EaN2cJDoDrXjzQn1G5qUaWtYR--Y-YUM92-H6mYnkQ"

    def create_3d_maps_by_aoi(self,json_files_by_aoi, all_images_bounds, s2_image, cesium_token, output_dir="maps"):
        os.makedirs(output_dir, exist_ok=True)
        aoi_num = 0
        
        for aoi, json_files in json_files_by_aoi.items():
            # Set up Cesium HTML structure
            html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Cesium 3D Map</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.94.0/Cesium.js"></script>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.94.0/Cesium.css">
            </head>
            <body>
                <div id="cesiumContainer" style="width: 100%; height: 100vh;"></div>
                <script>
                // CesiumJS setup
                const viewer = new Cesium.Viewer('cesiumContainer', {
                    imageryProviderViewModel: Cesium.createOpenStreetMapImageryProviderViewModel(),
                    shouldAnimate: true
                });
                viewer.scene.globe.enableLighting = true;
                """
            
            first_valid_coord = None
            
            # Add GeoJSON features to the map
            geojson_layers = []
            for json_file in json_files:
                with open(json_file, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                
                if not isinstance(data, dict) or "features" not in data or not isinstance(data["features"], list):
                    print(f"❌ Skipping {json_file}: Invalid JSON structure!")
                    continue
                
                features = data["features"]
                if not features:
                    print(f"❌ Skipping {json_file}: Empty 'features' list!")
                    continue
                
                if not first_valid_coord:
                    for feature in features:
                        geometry = feature.get("geometry", {})
                        if geometry.get("type") == "Polygon" and "coordinates" in geometry:
                            coords = geometry["coordinates"]
                            if isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list) and len(coords[0]) > 0:
                                first_valid_coord = coords[0][0]
                                break
                
                geojson_layers.append(features)
            
            # Add the Sentinel-2 image as a 3D overlay
            bbox = all_images_bounds[aoi_num]
            s2_image_data = s2_image[aoi_num]
            
            html_content += f"""
            // Add Sentinel-2 image overlay
            const boundingBox = [
                Cesium.Cartographic.fromDegrees({bbox[0]}, {bbox[1]}), 
                Cesium.Cartographic.fromDegrees({bbox[2]}, {bbox[3]})
            ];
            const imageUrl = '{s2_image_data}';
            const imageryLayer = viewer.scene.imageryLayers.addImageryProvider(
                new Cesium.UrlTemplateImageryProvider({{
                    url : imageUrl
                }})
            );
            """
            
            # Add GeoJSON features as 3D polygons
            for layer in geojson_layers:
                html_content += """
                const geoJsonDataSource = Cesium.GeoJsonDataSource.load({json_data});
                geoJsonDataSource.then(function(dataSource) {{
                    viewer.dataSources.add(dataSource);
                    viewer.zoomTo(dataSource);
                }});
                """.format(json_data=layer)
            
            # Set the camera to a specific starting position (Fixed location: Thessaloniki, Greece)
            html_content += """
            viewer.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(23.7275, 37.9838, 1000),  // Fixed position near Thessaloniki, Greece
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-20),
                    roll: 0
                }
            });
            """
            
            # End HTML content
            html_content += """
                </script>
            </body>
            </html>
            """
            
            # Save the Cesium map as an HTML file
            output_file = os.path.join(output_dir, f"{aoi}_cesium_map.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"✅ Map saved as '{output_file}'")
            
            aoi_num += 1