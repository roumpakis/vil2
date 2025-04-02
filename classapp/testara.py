from flask import Flask
import os
from CRMAPI import CRMAPI
from sentinelAPI import sentinelAPI
from datetime import datetime as dt, timedelta
from sentinelhub import Geometry, CRS
import shapely.wkt
import numpy as np
from PIL import Image

app = Flask(__name__)

# Initialize CRMAPI and SentinelAPI
rm = CRMAPI(15)
events, ids = rm.events, rm.events_ids
sapi = sentinelAPI()

# Ensure the static/overlays directory exists
static_overlays_path = 'D:/app/breles-full-complet/breles/classapp/static/overlays'
os.makedirs(static_overlays_path, exist_ok=True)

# Process images for a subset of events
i = 0
for event_id in ids:
    event_details = rm.get_event_details(event_id)


    if not event_details:
        print(f"No details found for event ID {event_id}")
        continue

    # Extract polygon and event time
    polygon_str = event_details['results'][0]['extent']
    shapely_geometry = shapely.wkt.loads(polygon_str)
    geometry = Geometry(shapely_geometry, CRS.WGS84)
    bounds = shapely_geometry.bounds

    event_time = event_details['results'][0]['eventTime']
    event_date = dt.strptime(event_time, '%Y-%m-%dT%H:%M:%S')

    # Define time intervals for before and after images
    date_before_start = event_date - timedelta(days=20)
    date_before_end = event_date - timedelta(days=1)
    time_interval_before = (date_before_start, date_before_end)

    time_interval_after = (event_date, event_date + timedelta(days=8))

    # Fetch data from Sentinel API
    data_before = sapi.get_sentinel_data(geometry, sapi.config, time_interval_before, "before_image")
    data_after = sapi.get_sentinel_data(geometry, sapi.config, time_interval_after, "after_image")

    if data_before.size > 0 and data_after.size > 0:
        # Convert to PIL images
        image_before = Image.fromarray(np.array(data_before))
        image_after = Image.fromarray(np.array(data_after))

        # Define file paths
        image_filename_before = f"{event_id}_before.png"
        image_filename_after = f"{event_id}_after.png"

        image_path_before = os.path.join(static_overlays_path, image_filename_before)
        image_path_after = os.path.join(static_overlays_path, image_filename_after)

        # Save images
        image_before.save(image_path_before, format="PNG")
        image_after.save(image_path_after, format="PNG")

        print(f"Saved images for event ID {event_id} to {static_overlays_path}")
    else:
        print(f"No valid data found for event ID {event_id}")
