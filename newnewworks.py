import os
import re
import time
import json
import time
import shutil
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


# === 1. DOWNLOAD ZIP FILE ===
def download_file(url, save_path):
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
def extract_zip(zip_path, extract_to):
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
def find_json_files(base_dir):
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
def create_maps_by_aoi(json_files_by_aoi, all_images_bounds, s2_image, output_dir="maps"):
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






# Extract bbox from the extent
#polygon = extent

def convert_tiff_for_folium(tiff_bytes):
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

def sentinel2_tiff_to_numpy(tiff_bytes, bands=[4]):  # Default: Red band (B4)
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


def format_date(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # Σωστή μορφή με 'Z' στο τέλος

# Convert BytesIO PNG to NumPy array

def tiff_to_numpy(tiff_bytes):
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


def check_bands_in_tiff(tiff_bytes):
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



# If available bands include 4, 3, 2, proceed with extraction.



# Function to save image as PNG
def save_as_png(image_path, output_path):
    with rasterio.open(image_path) as src:
        image = src.read(1)  # Read first band
        plt.imshow(image, cmap="gray")
        plt.axis("off")
        plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close()




# Initialize CRMAPI
rm = CRMAPI()
# Get event details
#start, end = rm.get_range()
id_num = 733
event_id = f'EMSR{id_num}'
details = rm.get_event_details(event_id)
if details is None:
    print('details none broo!')
# === MAIN EXECUTION ===
DOWNLOAD_URL = f'https://rapidmapping.emergency.copernicus.eu/backend/{event_id}/{event_id}_products.zip'
ZIP_FILE_PATH = f"./{event_id}_products.zip"
EXTRACTED_DIR = f"./{event_id}_extracted"
res = details['results'][0]
code = res['code']
extent = res['extent']
aois = res['aois']
countries = res['countries']
event_time = res['eventTime']
activation_time = res['activationTime']
centroid = res['centroid']
product_path = res['productsPath']
reason = res['reason']
category = res['category']
code = res['code']
name = res['name']
sub_category = res['subCategory']

# === MAIN EXECUTION ===
DOWNLOAD_URL = f'https://rapidmapping.emergency.copernicus.eu/backend/{event_id}/{event_id}_products.zip'
ZIP_FILE_PATH = f"./{event_id}_products.zip"
EXTRACTED_DIR = f"./{event_id}_extracted"

if not os.path.exists(ZIP_FILE_PATH):
    download_file(DOWNLOAD_URL, ZIP_FILE_PATH)
else:
    print(f"📂 File already exists: {ZIP_FILE_PATH}")

if not os.path.exists(EXTRACTED_DIR):
    extract_zip(ZIP_FILE_PATH, EXTRACTED_DIR)
    os.remove(ZIP_FILE_PATH)
else:
    print(f"📂 Already extracted: {EXTRACTED_DIR}")

# Find all JSON files organized by AOI
#===============================================================
json_files_by_aoi = find_json_files(EXTRACTED_DIR)

# Create main directory
main_dir = f"{event_id}_results"
os.makedirs(main_dir, exist_ok=True)

# Create subfolders for each AOI
#for aoi in json_files_by_aoi.keys():
#    os.makedirs(os.path.join(main_dir, aoi), exist_ok=True)


event_dt = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S')
# Υπολογισμός ημερομηνιών
before_end = event_dt - timedelta(days=1)
before_start = before_end - timedelta(days=20)
after_start = event_dt
after_end = after_start + timedelta(days=5)

# Αποθήκευση στο σωστό format (0 στην ώρα)
before_start = format_date(before_start.replace(hour=0, minute=0, second=0))
before_end = format_date(before_end.replace(hour=0, minute=0, second=0))
after_start = format_date(after_start.replace(hour=0, minute=0, second=0))
after_end = format_date(after_end.replace(hour=0, minute=0, second=0))

# Εκτύπωση αποτελεσμάτων
print("before_start:", before_start)
print("before_end:", before_end)
print("after_start:", after_start)
print("after_end:", after_end)

cloud_cover = 20  # Max allowed cloud cover in %
#width = 256
#height = 256
CLIENT_ID = "sh-f7cc8302-169d-4001-8f42-0073e0e134f7"
CLIENT_SECRET = "2QEneiG3a60JwXSLTZFyHxBYf48nmKF2"
CLIENT_ID = "sh-f7cc8302-169d-4001-8f42-0073e0e134f7"
CLIENT_SECRET = "2QEneiG3a60JwXSLTZFyHxBYf48nmKF2"

BASE_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
# Create an instance of the manager class
sentinel_manager = SentinelAPIManager(CLIENT_ID, CLIENT_SECRET, BASE_URL)

# Download Sentinel-2 image


i = 0
all_aois_images = []
all_aois_bounds = []
# Save images inside respective AOI folders
a_dir = None
for aoi in json_files_by_aoi.keys():
    aoi_dir = os.path.join(main_dir, aoi)
    polygon = aois[i]['extent']
    coordinates = re.findall(r"([-+]?[0-9]*\.?[0-9]+)\s([-+]?[0-9]*\.?[0-9]+)", polygon)
    
    coords = [(float(lon), float(lat)) for lon, lat in coordinates]
    lons, lats = zip(*coords)
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    bbox = [min_lon, min_lat, max_lon, max_lat]
    bbox_new= BBox(bbox, crs=CRS('4326'))
    resolution = 10  # meters
    bbox_size = bbox_to_dimensions(bbox_new, resolution=resolution)  # Shape: (width, height)
    print(bbox_size)
    print(bbox_size)
    print(type(bbox_size))
    if bbox_size[0] > 1800 or bbox_size[1] > 1800:
        print(f"🚫 Skipping {aoi}: Bounding box too large for Sentinel API!"
              f" (Width: {bbox_size[0]}, Height: {bbox_size[1]})")
        continue

    print(f"{aoi}: BBox for Sentinel API: {bbox}")
    print(aoi_dir)
    
    s1_tiff_before,s2_tiff_before,s3_tiff_before \
        = sentinel_manager.download_all_images(bbox, before_start, before_end, cloud_cover, save_as_tiff=False, width=bbox_size[0], height=bbox_size[1])
    with open(aoi_dir+"before_sentinel2.tiff", "wb") as file:
        file.write(s2_tiff_before.read())
        print(f"Before Sentinel-2 image saved as sentinel2.tiff")
    with open(aoi_dir+"before_sentinel1.tiff", "wb") as file:
        file.write(s1_tiff_before.read())
        print(f"Before Sentinel-1 image saved as sentinel1.tiff")

    time.sleep(10)
    s1_tiff,s2_tiff,s3_tiff \
        = sentinel_manager.download_all_images(bbox, after_start, after_end, cloud_cover, save_as_tiff=False, width=bbox_size[0], height=bbox_size[1])
    with open(aoi_dir+"sentinel2.tiff", "wb") as file:
        file.write(s2_tiff.read())
        print(f"Sentinel-2 image saved as sentinel2.tiff")
    with open(aoi_dir+"sentinel1.tiff", "wb") as file:
        file.write(s1_tiff.read())
        print(f"Sentinel-1 image saved as sentinel1.tiff")
    time.sleep(10)
    # Check the bands in your TIFF
    band_count, available_bands = check_bands_in_tiff(s2_tiff)
    bands=[1,2,3]
    #   bands=[1]
    s2_rgb, s2_bounds = sentinel2_tiff_to_numpy(s2_tiff, bands)  # B4 (Red), B3 (Green), B2 (Blue)
    if len(bands) == 3:
    # Reshape for plotting (C x H x W → H x W x C)
        s2_rgb = np.moveaxis(s2_rgb, 0, -1)  
    all_aois_images.append(s2_rgb)
    all_aois_bounds.append(s2_bounds)
    # Plot RGB Image
    #plt.imshow(s2_rgb)
    #plt.axis("off")
    #plt.show()

    a_dir =  f"{event_id}_results"
    create_monit_gif(main_dir)
    
    i+=1
if a_dir is not None:
    # Create maps using Sentinel-2 overlay
    output_maps_dir = f"{event_id}_maps"
    os.makedirs(output_maps_dir, exist_ok=True)
    #main_dir = f"EMSR{event_id}_results"
    create_maps_by_aoi(json_files_by_aoi, all_aois_bounds, all_aois_images, output_dir=output_maps_dir)
    print(f"All files saved successfully in {main_dir} and {output_maps_dir}!")


    # Ορισμός του base_path ως την τρέχουσα διαδρομή
    base_path = os.getcwd()
    print(base_path)
    create_event_masks(base_path, event_id=id_num)
    # Example usage




# Διαγραφή του φακέλου _extracted στο τέλος του script
if os.path.exists(EXTRACTED_DIR):
    print(f"🗑️ Deleting extracted folder: {EXTRACTED_DIR}")
    shutil.rmtree(EXTRACTED_DIR)
    print("✅ Extraction folder deleted.")
else:
    print("⚠️ Extracted folder not found, skipping deletion.")

print(f"All files saved successfully in {main_dir}!")