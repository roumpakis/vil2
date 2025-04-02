import os
import re
import time
import json
import time
import shutil
import numpy as np
import numpy as np
import rasterio
from io import BytesIO
from rasterio.enums import Resampling
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
from Utils import Utils
utils = Utils()
import numpy as np
import rasterio
from rasterio.enums import Resampling

import rasterio
import numpy as np


#def store_img_png(tiff_img, selected_bands, image_path):
#        # Οι μπάντες που θέλουμε να κρατήσουμε (π.χ., RGB = [4, 3, 2])
#    # Convert to NumPy array
#    s2_all_before_array =   select_bands_and_return_array(tiff_img, selected_bands)
##    # Convert to 8-bit if necessary
#   if s2_all_before_array.dtype != np.uint8:
#        s2_all_before_array = (s2_all_before_array / np.max(s2_all_before_array) * 255).astype(np.uint8)
#    # Ensure directory exists
#    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    # Save image
#    cv2.imwrite(image_path, cv2.cvtColor(s2_all_before_array, cv2.COLOR_RGB2BGR))
#    print(f"Saved image at {image_path}")
#    return s2_all_before_array

import os
import numpy as np
import cv2

def convert_sentinel1_tiff_to_png(tiff_path, png_path):
    """
    Διαβάζει μια εικόνα TIFF (Sentinel-1 VV), τη μετατρέπει σε PNG και την αποθηκεύει.

    Παράμετροι:
    - tiff_path (str): Το path του αρχείου TIFF.
    - png_path (str): Το path όπου θα αποθηκευτεί το PNG.
    """

    # Άνοιγμα του TIFF αρχείου
    with rasterio.open(tiff_path) as dataset:
        image_array = dataset.read(1)  # Sentinel-1 έχει μόνο μία μπάντα (VV)

        # **Log μετασχηματισμός** για να αναδείξουμε λεπτομέρειες (αντί για απλή κανονικοποίηση)
        image_array = np.log1p(image_array - np.min(image_array))  # log(1 + x) για αποφυγή αρνητικών τιμών
        image_array = (image_array / image_array.max()) * 255  # Κανονικοποίηση σε 0-255

        # Μετατροπή σε uint8
        image_array = image_array.astype(np.uint8)

        # Διασφαλίζουμε ότι ο φάκελος υπάρχει
        os.makedirs(os.path.dirname(png_path), exist_ok=True)

        # Αποθήκευση ως PNG με OpenCV
        cv2.imwrite(png_path, image_array)
        print(f"Saved PNG image at {png_path}")
        return image_array
        
def store_img_png(tiff_img, selected_bands, image_path):
    """
    Επιλέγει μπάντες από την εικόνα TIFF, τις κανονικοποιεί και τις αποθηκεύει ως PNG.
    
    Παράμετροι:
    tiff_img (numpy.ndarray): Η εικόνα TIFF σε μορφή NumPy array.
    selected_bands (list): Η λίστα με τα indices των μπαντών που θέλουμε να κρατήσουμε (π.χ., [3, 8, 11]).
    image_path (str): Το path για την αποθήκευση της εικόνας PNG.
    
    Επιστρέφει:
    numpy.ndarray: Η κανονικοποιημένη εικόνα.
    """
    
    # Επιλέγουμε τις μπάντες από την εικόνα
    s2_all_before_array = select_bands_and_return_array(tiff_img, selected_bands)
    
    # Αν μόνο μία μπάντα υπάρχει, προσθέτουμε τη διάσταση των καναλιών
    if s2_all_before_array.shape[0] == 3:
        s2_all_before_array = s2_all_before_array[0, :, :][:, :, np.newaxis]  # Για 1 μπάντα προσθήκη της διάστασης (H, W, 1)
    
    # Αν η εικόνα είναι τύπου int16, τότε κάνουμε κανονικοποίηση για να την μετατρέψουμε σε uint8
    if s2_all_before_array.dtype == np.int16:
        # Κανονικοποιούμε σε 0-255 για να το αποθηκεύσουμε ως uint8
        s2_all_before_array = (s2_all_before_array - np.min(s2_all_before_array)) / (np.max(s2_all_before_array) - np.min(s2_all_before_array)) * 255
        s2_all_before_array = s2_all_before_array.astype(np.uint8)
    
    # Αν η εικόνα έχει πολλές μπάντες (π.χ., RGB), τη μετατρέπουμε σε BGR για να την αποθηκεύσουμε με OpenCV
    if s2_all_before_array.shape[2] == 3:
        s2_all_before_array = cv2.cvtColor(s2_all_before_array, cv2.COLOR_RGB2BGR)
    
    # Διασφαλίζουμε ότι ο φάκελος υπάρχει
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    # Αποθήκευση της εικόνας ως PNG
    cv2.imwrite(image_path, s2_all_before_array)
    print(f"Saved image at {image_path}")
    
    return s2_all_before_array



def save_normalized_image_as_png(s2_tiff, selected_bands, png_path):
    """
    Επιλέγει μπάντες από την εικόνα, κανονικοποιεί τις τιμές και αποθηκεύει την εικόνα ως PNG.
    
    Παράμετροι:
    s2_tiff (BytesIO): Το TIFF αρχείο σε μορφή BytesIO.
    selected_bands (list): Η λίστα με τα indices των μπαντών που θέλουμε να κρατήσουμε (π.χ., [3, 8, 11]).
    png_path (str): Το path όπου θα αποθηκευτεί η εικόνα PNG.
    
    Επιστρέφει:
    numpy.ndarray: Η κανονικοποιημένη εικόνα.
    """
    
    # Φόρτωση της εικόνας TIFF από το BytesIO αντικείμενο με το σωστό driver
    with rasterio.open(BytesIO(s2_tiff.read()), driver='GTiff') as dataset:
        # Διαβάζουμε τις μπάντες που επιλέξαμε
        image_data = np.array([dataset.read(band) for band in selected_bands])

    # Αν χρειάζεται, μετατρέπουμε σε RGB (3 μπάντες) ή διαφορετικά χρώματα
    if image_data.shape[3] == 1:
        image_data = image_data[0, :, :][:, :, np.newaxis]  # Για περιπτώσεις με 1 band
    
    # Κλιμάκωση σε 8-bit αν δεν είναι ήδη (0-255)
    if image_data.dtype != np.uint8:
        image_data = (image_data / np.max(image_data) * 255).astype(np.uint8)
    
    # Διασφαλίζουμε ότι ο φάκελος υπάρχει
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    
    # Δημιουργία της εικόνας από το numpy array
    image = Image.fromarray(np.transpose(image_data, (1, 2, 0)))  # Μετατροπή σε (ύψος, πλάτος, μπάνες)
    
    # Αποθήκευση της εικόνας ως PNG
    image.save(png_path, format='PNG')
    
    # Επιστροφή της κανονικοποιημένης εικόνας
    return image_data



def save_tiff_as_png(tiff_file, png_path):
    with rasterio.open(tiff_file) as src:
        # Διαβάζουμε όλες τις μπάντες της εικόνας
        bands = src.read()

        # Αν το TIFF έχει μόνο 1 μπάντα (ασπρόμαυρη εικόνα), αποθηκεύουμε την πρώτη μπάντα
        if bands.shape[0] == 1:
            # Δημιουργούμε μία ασπρόμαυρη εικόνα από την πρώτη μπάντα
            gray_image = bands[0, :, :]
            cv2.imwrite(png_path, gray_image)
        else:
            # Εάν υπάρχουν 3 μπάντες, δημιουργούμε έγχρωμη εικόνα RGB
            if bands.shape[0] == 3:
                rgb_image = np.moveaxis(bands, 0, -1)  # Μετακινούμε τις διαστάσεις για να είναι (height, width, bands)
                rgb_image = rgb_image.astype(np.float32)
                rgb_image = (rgb_image - rgb_image.min()) / (rgb_image.max() - rgb_image.min()) * 255
                rgb_image = rgb_image.astype(np.uint8)
                cv2.imwrite(png_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
            else:
                # Αν έχει περισσότερες από 3 μπάντες, αποθηκεύουμε μόνο τις πρώτες 3 ή όλες τις μπάντες, ανάλογα με την περίπτωση
                bands_to_save = bands[:3, :, :]  # Εδώ χρησιμοποιούμε μόνο τις πρώτες 3 μπάντες
                rgb_image = np.moveaxis(bands_to_save, 0, -1)
                rgb_image = rgb_image.astype(np.float32)
                rgb_image = (rgb_image - rgb_image.min()) / (rgb_image.max() - rgb_image.min()) * 255
                rgb_image = rgb_image.astype(np.uint8)
                cv2.imwrite(png_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
            
    print(f"PNG image saved at: {png_path}")
    
def save_selected_bands_as_tiff(s2_image_bytes, selected_bands_indices, output_path):
    """
    Επιλέγει τις μπάντες από το TIFF αρχείο και αποθηκεύει το νέο TIFF με τις επιλεγμένες μπάντες.
    """
    # Επαναφορά δείκτη για το BytesIO
    s2_image_bytes.seek(0)


    # Άνοιγμα του TIFF με rasterio
    with rasterio.open(s2_image_bytes) as src:
        # Διαβάζουμε τις μπάντες που ζητήθηκαν από τη λίστα των selected_bands_indices
        print(f"Διαστάσεις: {src.width} x {src.height}")
        print(f"Αριθμός μπαντών: {src.count}")
        print(f"Γενικά metadata: {src.meta}")
        selected_bands = src.read(selected_bands_indices)  # (len(selected_bands_indices), height, width)
        
        # Αντιγραφή των μεταδεδομένων από το πρωτότυπο TIFF
        meta = src.meta.copy()

        # Αλλαγή του αριθμού των μπαντών και τύπου δεδομένων στο metadata
        meta.update(count=len(selected_bands_indices), dtype=selected_bands.dtype)

        # Αν χρειάζεται να διασφαλίσουμε ότι είναι RGB, ορίζουμε το color_space σωστά
        # Αποθήκευση του νέου TIFF με τις επιλεγμένες μπάντες
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(selected_bands)  # Γράφουμε τις επιλεγμένες μπάντες στο νέο TIFF

    print(f"Το νέο TIFF αρχείο αποθηκεύθηκε ως: {output_path}")


def select_bands_and_return_array(s2_image_bytes, selected_bands_indices):
    """
    Επιλέγει τις μπάντες που θέλεις από το TIFF αρχείο και επιστρέφει το NumPy array της εικόνας.

    Parameters:
    - s2_image_bytes: BytesIO αντικείμενο που περιέχει το TIFF αρχείο.
    - selected_bands_indices: Λίστα με τις μπάντες που θέλεις να κρατήσεις (π.χ. [4, 3, 2] για RGB).
    
    Returns:
    - NumPy array της επιλεγμένης εικόνας.
    """
    # Επαναφορά δείκτη για το BytesIO
    s2_image_bytes.seek(0)

    # Άνοιγμα του TIFF με rasterio
    with rasterio.open(s2_image_bytes) as src:
        # Διαβάζουμε τις μπάντες που ζητήθηκαν από τη λίστα των selected_bands_indices
        selected_bands = src.read(selected_bands_indices)  # (len(selected_bands_indices), height, width)
        
        # Κανονικοποίηση των τιμών για να είναι μεταξύ 0 και 255
        selected_bands = selected_bands.astype(np.float32)
        selected_bands = (selected_bands - selected_bands.min()) / (selected_bands.max() - selected_bands.min()) * 255
        selected_bands = selected_bands.astype(np.uint8)  # Μετατροπή σε 8-bit εικόνα
        
        # Μετατροπή σε RGB (αν η επιλεγμένη μορφή είναι RGB)
        rgb_image = np.moveaxis(selected_bands, 0, -1)  # Rearrange axes to (height, width, bands)
        
        return rgb_image
    

def do_all(event_id):
    id_num = event_id
    # Initialize CRMAPI
    rm = CRMAPI()
    event_id = f"EMSR{event_id}"
    details = rm.get_event_details(event_id)
    json_file_path = os.path.join(os.getcwd(), "JSONS", f"{event_id}.json")
    if details and details['results']:
        event_result = details['results'][0]
        # Extract the required details including the reason
        event_info = {
            'id': event_id,
            'code': event_result['code'],
            'eventTime': event_result['eventTime'],
            'continent': event_result['continent'],
            'country': event_result['countries'][0]['name'],
            'extent': event_result['extent'],
            'reportLink': event_result.get('reportLink', ''),  # Add reportLink here
            'reason': event_result.get('reason', '')  # Add reason here
        }
        # Δημιουργία του φακέλου αν δεν υπάρχει
        folder_path = os.path.dirname(json_file_path)  # Παίρνουμε τον φάκελο από το path
        if not os.path.exists(folder_path):  # Αν ο φάκελος δεν υπάρχει
            os.makedirs(folder_path)  # Δημιουργούμε τον φάκελο και τους υποφακέλους αν χρειάζεται
        # Save the event details to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(event_info, json_file)
       
    if details is None:
        print('details none broo!')
    # === MAIN EXECUTION ===
    #DOWNLOAD_URL = f'https://rapidmapping.emergency.copernicus.eu/backend/{event_id}/{event_id}_products.zip'
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
        utils.download_file(DOWNLOAD_URL, ZIP_FILE_PATH)
    else:
        print(f"📂 File already exists: {ZIP_FILE_PATH}")

    if not os.path.exists(EXTRACTED_DIR):
        utils.extract_zip(ZIP_FILE_PATH, EXTRACTED_DIR)
        os.remove(ZIP_FILE_PATH)
    else:
        print(f"📂 Already extracted: {EXTRACTED_DIR}")

    # Find all JSON files organized by AOI
    #===============================================================
    json_files_by_aoi = utils.find_json_files(EXTRACTED_DIR)

    # Create main directory
    main_dir = f"{event_id}_results"
    os.makedirs(main_dir, exist_ok=True)

    # Create subfolders for each AOI
    #for aoi in json_files_by_aoi.keys():
    #    os.makedirs(os.path.join(main_dir, aoi), exist_ok=True)


    event_dt = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S')
    # Υπολογισμός ημερομηνιών
    before_end = event_dt - timedelta(days=2)
    before_start = before_end - timedelta(days=40)
    after_start = event_dt
    after_end = after_start + timedelta(days=15)

    # Αποθήκευση στο σωστό format (0 στην ώρα)
    before_start = utils.format_date(before_start.replace(hour=0, minute=0, second=0))
    before_end = utils.format_date(before_end.replace(hour=0, minute=0, second=0))
    after_start = utils.format_date(after_start.replace(hour=0, minute=0, second=0))
    after_end = utils.format_date(after_end.replace(hour=0, minute=0, second=0))

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
    
    coordinates = re.findall(r"([-+]?[0-9]*\.?[0-9]+)\s([-+]?[0-9]*\.?[0-9]+)", extent)
        
    coords = [(float(lon), float(lat)) for lon, lat in coordinates]
    lons, lats = zip(*coords)
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    bbox = [min_lon, min_lat, max_lon, max_lat]
    bbox_new= BBox(bbox, crs=CRS('4326'))
    # Download Sentinel-2 image
    image_filename_before = f"{event_id}_before.png"
    image_filename_after = f"{event_id}_after.png"
    image_path_before = os.path.join('static', 'overlays', image_filename_before)
    image_path_after = os.path.join('static', 'overlays', image_filename_after)
    #==========================================================================================#########################################
    #_,s2_all_before,_ = sentinel_manager.download_all_images(bbox, before_start, before_end, cloud_cover, save_as_tiff=False, width=1024, height=1024)
    #_,s2_all_after,_ = sentinel_manager.download_all_images(bbox, after_start, after_end, cloud_cover, save_as_tiff=False, width=1024, height=1024)

        # Οι μπάντες που θέλουμε να κρατήσουμε (π.χ., RGB = [4, 3, 2])
    selected_bands = [3, 8, 11]  
    #s2_all_before_array = store_img_png(s2_all_before, selected_bands, image_path_before) #
    
    
    # Convert to NumPy array
    #s2_all_after_array =  store_img_png(s2_all_after, selected_bands, image_path_after) 


#_________________________________________________________________________________########################################
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
        if False:
        #if bbox_size[0] > 2500 or bbox_size[1] > 2500:
            print(f"🚫 Skipping {aoi}: Bounding box too large for Sentinel API!"
                f" (Width: {bbox_size[0]}, Height: {bbox_size[1]})")
            continue

        print(f"{aoi}: BBox for Sentinel API: {bbox}")
        print(aoi_dir)
        
        s2_before_path = aoi_dir+"_before_sentinel2.tiff"
        s1_before_path = aoi_dir+"_before_sentinel1.tiff"
        s2_after_path = aoi_dir+"_sentinel2.tiff"
        s1_after_path = aoi_dir+"_sentinel1.tiff"
                #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BEFORE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



        if not os.path.exists(s2_before_path or s1_before_path ):
            s1_tiff_before,s2_tiff_before,s3_tiff_before = sentinel_manager.download_all_images(bbox, before_start, before_end, cloud_cover, save_as_tiff=False, width=bbox_size[0], height=bbox_size[1])
           # s2_tiff_before =   select_bands_and_return_array(s2_tiff_before, selected_bands)
            save_selected_bands_as_tiff(s2_tiff_before, selected_bands, s2_before_path)
            png_path = s2_before_path.replace(".tiff", ".png")
            s2_tiff_before.seek(0)  # Reset the pointer to the beginning of the BytesIO object
            s2_before_png = store_img_png(s2_tiff_before, selected_bands, png_path)
            
            with open(s1_before_path, "wb") as file:
                file.write(s1_tiff_before.read())
                print(f"Before Sentinel-1 image saved as sentinel1_before.tiff")
                print(s1_before_path)
                png_path = s1_before_path.replace(".tiff", ".png")
                s1_tiff_before.seek(0)  # Reset the pointer to the beginning of the BytesIO object
                s1_before_png = convert_sentinel1_tiff_to_png(s1_before_path, png_path)
                        


            time.sleep(5)                
        else:
            print(f"📂 File already exists: {s1_before_path}")

        #if not os.path.exists(s2_after_path or s1_after_path ):
        if True:
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ AFTER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            s1_tiff,s2_tiff,s3_tiff = sentinel_manager.download_all_images(bbox, after_start, after_end, cloud_cover, save_as_tiff=False, width=bbox_size[0], height=bbox_size[1])
                    # Οι μπάντες που θέλουμε να κρατήσουμε (π.χ., RGB = [4, 3, 2])
            selected_bands = [3, 8, 11]

            # Convert to NumPy array
            save_selected_bands_as_tiff(s2_tiff, selected_bands, s2_before_path)
            with open(s2_after_path, "wb") as file:
                file.write(s2_tiff.read())
                print(f"Sentinel-2 image saved as sentinel2.tiff")
                png_path = s2_after_path.replace(".tiff", ".png")
                s2_after_png =   store_img_png(s2_tiff, selected_bands, png_path)
        
            with open(s1_after_path, "wb") as file:
                file.write(s1_tiff.read())
                print(f"Sentinel-1 image saved as sentinel1.tiff")
                png_path = s1_after_path.replace(".tiff", ".png")
                s1_after_png = convert_sentinel1_tiff_to_png(s1_after_path, png_path)


            time.sleep(1)
        else:
            # Αν οι εικόνες υπάρχουν ήδη, τις φορτώνουμε από το path
            print(f"📂 File already exists: {s2_after_path} and {s1_after_path}")
            continue



        


        # Check the bands in your TIFF
        band_count, available_bands = utils.check_bands_in_tiff(s2_tiff)
        bands=[3,8,11]
        #   bands=[1]
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',bands)
        s2_rgb, s2_bounds = utils.sentinel2_tiff_to_numpy(s2_tiff, bands)  # B4 (Red), B3 (Green), B2 (Blue)
        if len(bands) == 3:
        # Reshape for plotting (C x H x W → H x W x C)
            s2_rgb = np.moveaxis(s2_rgb, 0, -1)  
        all_aois_images.append(s2_rgb)
        all_aois_bounds.append(s2_bounds)
        # Plot RGB Image
        plt.imshow(s2_rgb)
        plt.axis("off")
        plt.show()

        a_dir =  f"{event_id}_results"
        create_monit_gif(main_dir)
        
        i+=1
    if a_dir is not None:
        # Create maps using Sentinel-2 overlay
        output_maps_dir = f"{event_id}_maps"
        os.makedirs(output_maps_dir, exist_ok=True)
        #main_dir = f"EMSR{event_id}_results"
        utils.create_maps_by_aoi(json_files_by_aoi, all_aois_bounds, all_aois_images, output_dir=output_maps_dir)
        #create_3d_maps_by_aoi(json_files_by_aoi, all_aois_bounds, all_aois_images, CESIUM_ION_ACCESS_TOKEN, output_dir="maps")
        print(f"All files saved successfully in {main_dir} and {output_maps_dir}!")


        # Ορισμός του base_path ως την τρέχουσα διαδρομή
        base_path = os.getcwd()
        print(base_path)
        create_event_masks(base_path, event_id=id_num)
        # Example usage


    create_monit_gif(main_dir)

    # Διαγραφή του φακέλου _extracted στο τέλος του script
    if os.path.exists(EXTRACTED_DIR):
        print(f"🗑️ Deleting extracted folder: {EXTRACTED_DIR}")
        shutil.rmtree(EXTRACTED_DIR)
        print("✅ Extraction folder deleted.")
    else:
        print("⚠️ Extracted folder not found, skipping deletion.")

    print(f"All files saved successfully in {main_dir}!")
