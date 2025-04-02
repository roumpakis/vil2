from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL.ExifTags import TAGS

def get_image_info(image_path):
    try:
        with Image.open(image_path) as img:
            # Βασικές πληροφορίες
            print(f"Μορφή: {img.format}")
            print(f"Μέγεθος: {img.size} pixels")
            print(f"Λειτουργία Χρώματος: {img.mode}")
            
            # Μέγεθος αρχείου σε bytes
            file_size = os.path.getsize(image_path)
            print(f"Μέγεθος αρχείου: {file_size / 1024:.2f} KB")
            
            # EXIF δεδομένα (αν υπάρχουν)
            exif_data = img._getexif()
            if exif_data:
                print("--- EXIF Δεδομένα ---")
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    print(f"{tag}: {value}")
            else:
                print("Δεν βρέθηκαν EXIF δεδομένα.")
            
            # Μετατροπή της εικόνας σε numpy array για στατιστικές πληροφορίες
            img_array = np.array(img)
            plt.imshow(img_array)
            if len(img_array.shape) == 3:  # Έγχρωμη εικόνα
                min_val = img_array.min(axis=(0, 1))
                max_val = img_array.max(axis=(0, 1))
                mean_val = img_array.mean(axis=(0, 1))
                std_val = img_array.std(axis=(0, 1))
                print(f"Ελάχιστες τιμές καναλιών: {min_val}")
                print(f"Μέγιστες τιμές καναλιών: {max_val}")
                print(f"Μέσες τιμές καναλιών: {mean_val}")
                print(f"Τυπική απόκλιση καναλιών: {std_val}")
                
                # Ιστόγραμμα για κάθε κανάλι χρώματος
                colors = ['Red', 'Green', 'Blue']
                plt.figure(figsize=(10, 5))
                for i, color in enumerate(colors):
                    plt.hist(img_array[:, :, i].ravel(), bins=256, color=color.lower(), alpha=0.6, label=color)
                plt.xlabel("Τιμές φωτεινότητας")
                plt.ylabel("Συχνότητα")
                plt.title("Ιστόγραμμα RGB Καναλιών")
                plt.legend()
                plt.show()
            else:  # Ασπρόμαυρη εικόνα
                print(f"Ελάχιστη τιμή: {img_array.min()}")
                print(f"Μέγιστη τιμή: {img_array.max()}")
                print(f"Μέση τιμή: {img_array.mean()}")
                print(f"Τυπική απόκλιση: {img_array.std()}")
                
                # Ιστόγραμμα για ασπρόμαυρη εικόνα
                plt.figure(figsize=(10, 5))
                plt.hist(img_array.ravel(), bins=256, color='black', alpha=0.6)
                plt.xlabel("Τιμές φωτεινότητας")
                plt.ylabel("Συχνότητα")
                plt.title("Ιστόγραμμα Ασπρόμαυρης Εικόνας")
                plt.show()
    except Exception as e:
        print(f"Σφάλμα: {e}")

# Δώσε τη διαδρομή της εικόνας σου
image_path = r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\static\all_data\EMSR795_results\AOI02_sentinel1.png"  # Αντικατέστησε με την πραγματική διαδρομή
get_image_info(image_path)