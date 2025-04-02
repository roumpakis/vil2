from datetime import timedelta, datetime
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from SentinelAPIManager import SentinelAPIManager

# Διαπιστευτήρια API
CLIENT_ID = "sh-f7cc8302-169d-4001-8f42-0073e0e134f7"
CLIENT_SECRET = "2QEneiG3a60JwXSLTZFyHxBYf48nmKF2"
BASE_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Δημιουργία αντικειμένου API Manager
sentinel_manager = SentinelAPIManager(CLIENT_ID, CLIENT_SECRET, BASE_URL)

# Ορισμός των παραμέτρων
bbox = [16.0, 48.0, 16.5, 48.5]  # Παράδειγμα BBOX
date_before_start = "2024-02-01"
date_before_end = "2024-02-10"
event_date = "2024-02-15"  # Είναι string και χρειάζεται μετατροπή σε datetime

# ✅ Διορθώνουμε τη μετατροπή των ημερομηνιών
event_date_dt = datetime.strptime(event_date, "%Y-%m-%d")  # Μετατροπή σε datetime
event_date_end = event_date_dt + timedelta(days=12)  # Προσθήκη 12 ημερών
event_date_end_str = event_date_end.strftime("%Y-%m-%d")  # Επιστροφή σε string

# Λήψη εικόνων πριν και μετά
data_before = sentinel_manager.s2_api.get_image_quick(
    bbox, date_before_start, date_before_end, 10, save_as_tiff=False, width=512, height=512
)
data_after = sentinel_manager.s2_api.get_image_quick(
    bbox, event_date, event_date_end_str, 10, save_as_tiff=False, width=512, height=512
)

# Έλεγχος αν οι εικόνες είναι έγκυρες
if data_before is not None and data_after is not None:
    # Προβολή εικόνων
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(data_before)
    plt.title("Before Event")

    plt.subplot(1, 2, 2)
    plt.imshow(data_after)
    plt.title("After Event")

    plt.show()

    # Μετατροπή των δεδομένων σε εικόνες PIL
    image_pil_before = Image.fromarray((data_before * 255).astype(np.uint8))
    image_pil_after = Image.fromarray((data_after * 255).astype(np.uint8))

    # Αποθήκευση των εικόνων
    image_pil_before.save("before_event.png", format="PNG")
    image_pil_after.save("after_event.png", format="PNG")
    print("✅ Images saved successfully!")
else:
    print("⚠ Could not retrieve Sentinel-2 images.")
