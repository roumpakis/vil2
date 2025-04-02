import os
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
def convert_to_png(file_path):
    filename = os.path.basename(file_path)
    png_filename = os.path.splitext(filename)[0] + ".png"
    png_file_path = os.path.join(os.path.dirname(file_path), png_filename)

    if not os.path.exists(png_file_path):
        try:
            # Φόρτωση εικόνας με OpenCV
            
            plt.imshow(img)
            
            plt.savefig(r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\static\all_data\EMSR736_results\test.png")
            

            # Αποθήκευση σε PNG
            cv2.imwrite(png_file_path, img)
            print(f"✔ Αποθηκεύτηκε σωστά: {png_file_path}")

        except Exception as e:
            print(f"❌ Σφάλμα: {e}")
# Παράδειγμα χρήσης
file_path = r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\static\all_data\EMSR736_results\AOI01_before_sentinel1.tiff"
convert_to_png(file_path)
img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
img = img * 400  # Πολλαπλασιασμός για να αυξήσουμε τη φωτεινότητα
img = np.clip(img, 0, 255)  # Κόβουμε τις τιμές έτσι ώστε να παραμείνουν στο εύρος [0, 255]

img = (img - img.min()) / (img.max() - img.min())
img = (img * 255).astype(np.uint8)
#img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#plt.imshow(img)
#plt.show()
cv2.imwrite(r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\static\all_data\EMSR736_results\test.png", img)
# Επισκόπηση εικόνας
