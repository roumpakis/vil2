from flask import Flask, render_template, jsonify
import os
import json
import re
from matplotlib import pyplot as plt
from CRMAPI import CRMAPI
#from sentinelAPI import sentinelAPI
from datetime import datetime as dt, timedelta
from sentinelhub import Geometry, CRS
import shapely.wkt
import numpy as np
from PIL import Image
import base64
import requests
#from do_all import find_unique_emsr 
import cv2
from SentinelAPIManager import SentinelAPIManager
CLIENT_ID = "sh-f7cc8302-169d-4001-8f42-0073e0e134f7"
CLIENT_SECRET = "2QEneiG3a60JwXSLTZFyHxBYf48nmKF2"
from Utils import Utils
utils = Utils()

BASE_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
    # Create an instance of the manager class
sentinel_manager = SentinelAPIManager(CLIENT_ID, CLIENT_SECRET, BASE_URL)
app = Flask(__name__)

# Initialize CRMAPI and SentinelAPI
rm = CRMAPI()
#sapi = sentinelAPI()

# Ensure the static/overlays and event_data directories exist
os.makedirs('static/overlays', exist_ok=True)
os.makedirs('static/event_data', exist_ok=True)  # Directory for event data JSON files

def convert_tiff_to_png(tiff_path):
    """Μετατρέπει ένα αρχείο TIFF σε PNG και επιστρέφει το νέο path"""
    if not os.path.exists(tiff_path):
        return None

    # Λήψη του ονόματος του αρχείου χωρίς την επέκταση
    base_name = os.path.splitext(os.path.basename(tiff_path))[0]
    png_path = os.path.join(os.path.dirname(tiff_path), f"{base_name}.png")

    try:
        # Άνοιγμα του TIFF αρχείου και αποθήκευση ως PNG
        with Image.open(tiff_path) as img:
            img.save(png_path, 'PNG')
        return f'/{png_path.replace("static", "")}'  # Επιστρέφουμε το path ως relative URL
    except Exception as e:
        print(f"Error converting {tiff_path} to PNG: {e}")
        return None
    
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_events')
def get_events():
    event_list = []
    import os

    # Specify the path to the folder
    #folder_path = os.path.join('static', 'event_data')
    #print(folder_path)

    # Create a list of filenames without the .json extension
    #filenames = [os.path.splitext(file)[0] for file in os.listdir(folder_path) if file.endswith('.json')]

    # Iterate through filenames and fetch event details
    #for event_event_idsid in filenames:
 
    base_directory = os.getcwd()

    all_data_path = os.path.join(base_directory,"static", "all_data")
    event_ids = utils.find_unique_emsr(all_data_path)
    #for event_id in rm.events_ids:
    for event_id in event_ids:
        event_details = get_event_details_from_file_or_api(event_id)
        if event_details:
            event_info = {
                'id': event_id,
                'code': event_details['code'],
                'eventTime': event_details['eventTime'],
                'continent': event_details['continent'],
                'country': event_details['country'],
                'extent': event_details['extent'],
                'reportLink': event_details['reportLink'],  # Added report link
                'reason': event_details['reason']  # Added reason
            }
            event_list.append(event_info)
    return jsonify({'events': event_list})

def get_event_details_from_file_or_api(event_id):
    """
    Check if the event details are stored in a JSON file.
    If yes, load them. If not, call the API and store the data in a JSON file.
    """
    #json_file_path = os.path.join('static', 'event_data', f"{event_id}.json")
    json_file_path = os.path.join( 'JSONS', f"{event_id}.json")
    # Check if the JSON file already exists
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            print(f"Loading event details for {event_id} from JSON file.")
            return json.load(json_file)
    
    print(f"Fetching event details for {event_id} from API.")
    event_details = rm.get_event_details(event_id)

    if event_details and event_details['results']:
        event_result = event_details['results'][0]
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
        # Save the event details to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(event_info, json_file)
        return event_info

    return None

@app.route('/get_overlay/<event_id>')
def get_overlay(event_id):
    try:
        event_details = get_event_details_from_file_or_api(event_id)

        if event_details is None:
            return jsonify({'before_image': None, 'after_image': None, 'popup': None, 'bounds': None, 'reportLink': None})

        polygon_str = event_details['extent']
        shapely_geometry = shapely.wkt.loads(polygon_str)
        geometry = Geometry(shapely_geometry, CRS.WGS84)
        bounds = shapely_geometry.bounds

        event_time = event_details['eventTime']
        event_date = dt.strptime(event_time, '%Y-%m-%dT%H:%M:%S')


    
        # Define image filenames
        image_filename_before = f"{event_id}_before.png"
        image_filename_after = f"{event_id}_after.png"
        image_path_before = os.path.join('static', 'overlays', image_filename_before)
        image_path_after = os.path.join('static', 'overlays', image_filename_after)

        # Check if the images already exist
        if os.path.exists(image_path_before) and os.path.exists(image_path_after):
            print("Images already exist. Skipping Sentinel API call.")
        else:
            print("Images not found. Fetching data from Sentinel API.")
            # Define time intervals for before and after images
            date_before_start = event_date - timedelta(days=20)
            date_before_end = event_date - timedelta(days=1)
            time_interval_before = (date_before_start, date_before_end)

            time_interval_after = (event_date, event_date + timedelta(days=12))

            # Fetch data from Sentinel API
            #Ορισμός διαδρομής φακέλου
            # data_folder = r"D:\app_12_2\autoeinai\all_data\EMSR733_results"

            # # Ονόματα αρχείων
            # before_filename = "AOI01before_sentinel2.tiff"
            # after_filename = "AOI01sentinel2.tiff"

            # # Διαδρομές αρχείων
            # before_image_path = os.path.join(data_folder, before_filename)
            # after_image_path = os.path.join(data_folder, after_filename)

            # # Φόρτωση των εικόνων
            # if os.path.exists(before_image_path):
            #     print(f"📂 Loading image: {before_image_path}")
            #     data_before = np.array(Image.open(before_image_path))
            # else:
            #     print(f"⚠ Image not found: {before_image_path}")
            #     data_before = None

            # if os.path.exists(after_image_path):
            #     print(f"📂 Loading image: {after_image_path}")
            #     data_after = np.array(Image.open(after_image_path))
            # else:
            #     print(f"⚠ Image not found: {after_image_path}")
            #     data_after = None




            #data_before = sapi.get_sentinel_data(geometry, sapi.config, time_interval_before, "before_image")
            #data_after = sapi.get_sentinel_data(geometry, sapi.config, time_interval_after, "after_image")
            
            #data_before = sapi.get_sentinel_data(geometry, sapi.config, time_interval_before, "before_image")
            #data_after = sapi.get_sentinel_data(geometry, sapi.config, time_interval_after, "after_image")

            # Ensure valid data is returned
            # if data_before.size > 0 and data_after.size > 0:
            #     image_before = np.array(data_before)
            #     image_after = np.array(data_after)

            #     # Convert to PIL images and save them
            #     image_pil_before = Image.fromarray(image_before)
            #     image_pil_after = Image.fromarray(image_after)
            #     image_pil_before.save(image_path_before, format="PNG")
            #     image_pil_after.save(image_path_after, format="PNG")
            print('prepei na ta katebasoume')
            #else:
            #    return jsonify({'before_image': None, 'after_image': None, 'popup': None, 'bounds': None, 'reportLink': None})

        # Perform classification using ML backend service
        #classification_url = 'http://ml-service:80/classify_image'
        classification_url = 'http://127.0.0.1:5080/classify_image'
        payload = {'image_data': base64.b64encode(open(image_path_before, 'rb').read()).decode('utf-8')}
        response = requests.post(classification_url, json=payload)

        # Handle classification response
        classification_result = 'Error in classification'
        if response.status_code == 200:
            classification_result = response.json().get('predicted_class', 'Unknown') + f" ({response.json().get('probability', 'N/A')})"

        # Perform change detection using the change detection backend service
        #change_detection_url = 'http://change-detection-service:80/detect_change'
        change_detection_url = 'http://127.0.0.1:5012/classifdetect_changey_image'

        change_payload = {
            'before_image': base64.b64encode(open(image_path_before, 'rb').read()).decode('utf-8'),
            'after_image': base64.b64encode(open(image_path_after, 'rb').read()).decode('utf-8')
        }
        change_response = requests.post(change_detection_url, json=change_payload)

        change_mask_base64 = None
        diff_image_base64 = None
        
        if change_response.status_code == 200:
            change_mask_base64 = change_response.json().get('change_mask', None)
            diff_image_base64 = change_response.json().get('diff_image', None)
        

        et = 'other'
        if 'fire' in event_details['reason']:
            et = 'fire'
        elif 'flood' in event_details['reason']:
            et = 'flood'


        # Prepare report link and popup text
        report_link = event_details.get('reportLink', '')
        popup_text = (
            f"<b>Code:</b> {event_details['code']}<br>"
            f"<b>Date:</b> {event_details['eventTime']}<br>"
            f"<b>Continent:</b> {event_details['continent']}<br>"
            f"<b>Country:</b> {event_details['country']}<br><br>"
            f"<b>Reason:</b> {event_details['reason']}<br>"  # Added reason
            f"<b>Classification:</b> {classification_result}"
        )
        print('ftasame mexri edw!!!!!!!!!!!!!! : ', et)
        return jsonify({
            'after_image': f"/static/overlays/{image_filename_after}",
            'before_image': f"/static/overlays/{image_filename_before}",
            'popup': popup_text,
            'bounds': [bounds[0], bounds[1], bounds[2], bounds[3]],
            'reportLink': report_link,
            'change_mask': change_mask_base64,  # Base64 encoded change mask
            'diff_image': diff_image_base64,  # Base64 encoded difference image
            'et': et
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'before_image': None, 'after_image': None, 'popup': None, 'bounds': None, 'reportLink': None, 'change_mask': None, 'diff_image': None})




# @app.route('/ai_analysis/<event_id>')
# def ai_analysis(event_id):
#     # Fetch event details to get the reason
#     event_details = get_event_details_from_file_or_api(event_id)
    
#     # Check if event details exist and get the reason
#     if event_details:
#         reason = event_details.get('reason', 'Unknown').lower()  # Convert reason to lowercase for case-insensitive matching
#     else:
#         reason = 'Unknown'

#     # Determine event type based on reason content
#     event_type = 'Unknown'  # Default to unknown

#     if 'fire' in reason:
#         event_type = 'Fire'
#     elif 'flood' in reason:
#         event_type = 'Flood'
#     elif 'earthquake' in reason:
#         event_type = 'Earthquake'
#     elif 'landslide' in reason:
#         event_type = 'Landslide'

#     print(f"Detected event type: {event_type}")

#     # Pass event_id and detected event type to the template
#     return render_template('ai_analysis.html', event_id=event_id, reason=event_type)
@app.route('/get_maps/<event_id>')
def get_maps(event_id):
    """Διαβάζει όλα τα HTML αρχεία των χαρτών και τα επιστρέφει ως JSON."""
    maps_path = f'static/all_data/{event_id}_maps'
    map_htmls = []

    if os.path.exists(maps_path) and os.path.isdir(maps_path):
        html_files = [f for f in os.listdir(maps_path) if f.endswith('.html')]
        for html_file in html_files:
            html_path = os.path.join(maps_path, html_file)
            with open(html_path, 'r', encoding='utf-8') as file:
                map_htmls.append(file.read())

    return jsonify({"map_htmls": map_htmls if map_htmls else ["<p>Map not available</p>"]})


import os
import re


def convert_tiff_to_png_in_folder(folder_path):
    """Μετατρέπει όλες τις εικόνες TIFF σε PNG στο φάκελο και τις αποθηκεύει με το ίδιο όνομα."""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if filename.lower().endswith('.tiff'):
            # Δημιουργούμε το όνομα για την PNG εικόνα
            png_filename = filename.replace('.tiff', '.png')
            png_file_path = os.path.join(folder_path, png_filename)
            
            # Αν η PNG δεν υπάρχει ήδη, την δημιουργούμε
            if not os.path.exists(png_file_path):
                try:
                    with Image.open(file_path) as img:
                        # Αν είναι Sentinel-1, υποχρεωτικά grayscale
                        if "sentinel1" in filename.lower():
                            #print('AAAAAAAAAAAAA ti paizei me ton sentinel1!!!!')
                            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
                            img = img * 500  # Πολλαπλασιασμός για να αυξήσουμε τη φωτεινότητα
                            img = np.clip(img, 0, 255)  # Κόβουμε τις τιμές έτσι ώστε να παραμείνουν στο εύρος [0, 255]
                            img = (img - img.min()) / (img.max() - img.min())
                            img = (img * 255).astype(np.uint8)
                            xx = png_file_path
                            #print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',xx)
                            cv2.imwrite(png_file_path, img)
                            print(f"Μετατροπή: {filename} -> {png_filename} (Sentinel-1, Grayscale)")
                        else:
                            img = img.convert('RGB')  # Μετατροπή σε RGB για τις υπόλοιπες
                            print(f"Μετατροπή: {filename} -> {png_filename} (RGB)")
                            img.save(png_file_path, format="PNG", optimize=True)
                        #img.save(png_file_path, 'PNG')
                        
                except Exception as e:
                    print(f"Σφάλμα κατά τη μετατροπή {filename}: {e}")
            else:
                print(f"Η εικόνα {png_filename} υπάρχει ήδη.")  

def get_overlay_paths(event_id):
    """Επιστρέφει τα paths των εικόνων, ομαδοποιημένα ανά AOI και άλλες μάσκες."""
    overlays_path = 'static/overlays'
    results_path = f'static/all_data/{event_id}_results'

    # Before/After images (PNG)
    before_image = f'/{overlays_path}/{event_id}_before.png' if os.path.exists(f'{overlays_path}/{event_id}_before.png') else None
    after_image = f'/{overlays_path}/{event_id}_after.png' if os.path.exists(f'{overlays_path}/{event_id}_after.png') else None

    # Λεξικό για τα AOI images (PNG)
    aoi_images = {}
    other_images = []

    if os.path.exists(results_path):
        # Πρώτα μετατρέπουμε όλες τις TIFF εικόνες σε PNG
        convert_tiff_to_png_in_folder(results_path)

        for filename in os.listdir(results_path):
            filepath = os.path.join(results_path, filename)
            relative_filepath = f'/static/all_data/{event_id}_results/{filename}'

            # Έλεγχος αν είναι AOI εικόνα
            if 'AOI' in filename and filename.endswith('.png'):
                aoi_id = filename.split('_')[0]
                
                if aoi_id not in aoi_images:
                    aoi_images[aoi_id] = {
                        'before_sentinel1': None,
                        'sentinel1': None,
                        'before_sentinel2': None,
                        'sentinel2': None
                    }
                
                # Κατηγοριοποίηση των PNG εικόνων
                if 'before_sentinel1' in filename:
                    aoi_images[aoi_id]['before_sentinel1'] = relative_filepath
                elif 'sentinel1' in filename:
                    aoi_images[aoi_id]['sentinel1'] = relative_filepath
                elif 'before_sentinel2' in filename:
                    aoi_images[aoi_id]['before_sentinel2'] = relative_filepath
                elif 'sentinel2' in filename:
                    aoi_images[aoi_id]['sentinel2'] = relative_filepath
            else:
                # Αν δεν είναι AOI εικόνα, προσθέτουμε στην κατηγορία των άλλων εικόνων
                if filename.endswith('.png'):
                    other_images.append(relative_filepath)

    return before_image, after_image, aoi_images, other_images




@app.route('/ai_analysis/<event_id>')
def ai_analysis(event_id):
    event_details = get_event_details_from_file_or_api(event_id)  # Assume this function exists
    reason = event_details.get('reason', 'Unknown').lower()
    etime = event_details.get('eventTime', 'Unknown')
    
    # Determine event type
    event_type = 'Unknown'
    if 'fire' in reason:
        event_type = 'Fire'
    elif 'flood' in reason:
        event_type = 'Flood'
    elif 'earthquake' in reason:
        event_type = 'Earthquake'
    elif 'landslide' in reason:
        event_type = 'Landslide'

    reason = event_details.get('reason', 'Unknown')
    
    before_image, after_image, aoi_images, other_images = get_overlay_paths(event_id)

    event_info = f'<b>Event Time:</b> {etime}<br><b>Type:</b> {event_type}<br><b>Reason:</b> {reason}'
    print('other images ', other_images)
    print('aoi images ', aoi_images)

    return render_template(
        'ai_analysis.html',
        event_id=event_id,
        reason=event_info,
        before_image=before_image,
        after_image=after_image,
        aoi_images=aoi_images,
        other_images=other_images
    )

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
