import rasterio
import numpy as np
import cv2
import os
import matplotlib.pyplot as plt

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

# --- Μετατροπή ---
tiff_path = r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\static\all_data\EMSR795_results\AOI02_sentinel1.tiff"
png_path = r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\static\all_data\EMSR795_results\AOI02_sentinel1.png"

convert_sentinel1_tiff_to_png(tiff_path, png_path)

# --- Προβολή εικόνας ---
image = cv2.imread(png_path, cv2.IMREAD_GRAYSCALE)
plt.figure(figsize=(6, 6))
plt.imshow(image, cmap="gray")
plt.axis("off")
plt.title("Sentinel-1 VV (Enhanced PNG)")
plt.show()

