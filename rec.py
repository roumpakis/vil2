import os
import numpy as np
import cv2
from tqdm import tqdm

def split_image(image, patch_size=256):
    """
    Διαχωρίζει την εικόνα σε μικρότερα κομμάτια (patches) μεγέθους patch_size x patch_size.
    Αν το τελευταίο κομμάτι είναι μικρότερο, προσθέτει padding.
    Επιστρέφει τα patches μαζί με τις συντεταγμένες τους.
    """
    height, width, _ = image.shape
    patches = []
    valid_area = []  # Θα κρατάμε αν το patch είναι έγκυρο ή όχι

    for y in range(0, height, patch_size):
        for x in range(0, width, patch_size):
            patch = image[y:y+patch_size, x:x+patch_size]
            
            # Έλεγχος αν το patch χρειάζεται padding
            pad_y = patch_size - patch.shape[0] if patch.shape[0] < patch_size else 0
            pad_x = patch_size - patch.shape[1] if patch.shape[1] < patch_size else 0
            
            # Αν χρειάζεται padding, προσθέτουμε μαύρο padding
            if pad_y > 0 or pad_x > 0:
                patch = np.pad(patch, ((0, pad_y), (0, pad_x), (0, 0)), mode='constant', constant_values=0)
                valid_area.append(0)  # Το patch είναι μη έγκυρο
            else:
                valid_area.append(1)  # Το patch είναι έγκυρο

            patches.append(patch)

    return patches, valid_area


def process_images(input_path, output_path):
    """
    Επεξεργάζεται τις εικόνες στους φακέλους S1 και S2.
    Χωρίζει τις εικόνες σε 256x256 patches και τις αποθηκεύει στα αντίστοιχα output directories.
    """
    # Δημιουργία φακέλων εξόδου
    os.makedirs(os.path.join(output_path, "S1_test"), exist_ok=True)
    os.makedirs(os.path.join(output_path, "S2_test"), exist_ok=True)
    os.makedirs(os.path.join(output_path, "Mask_test"), exist_ok=True)
    os.makedirs(os.path.join(output_path, "data_test"), exist_ok=True)

    batch_count = 0

    # Λίστες για τα υποφακέλους AFTER, BEFORE, MASK
    s1_after_folder = os.path.join(input_path, "S1", "AFTER")
    s1_before_folder = os.path.join(input_path, "S1", "BEFORE")
    s1_mask_folder = os.path.join(input_path, "S1", "MASK")
    
    s2_after_folder = os.path.join(input_path, "S2", "AFTER")
    s2_before_folder = os.path.join(input_path, "S2", "BEFORE")
    s2_mask_folder = os.path.join(input_path, "S2", "MASK")
    
    # Ελέγχουμε αν οι φάκελοι υπάρχουν
    if not os.path.exists(s1_after_folder) or not os.path.exists(s1_before_folder) or not os.path.exists(s1_mask_folder):
        print(f"Οι φάκελοι του S1 δεν βρέθηκαν: {input_path}")
        return
    if not os.path.exists(s2_after_folder) or not os.path.exists(s2_before_folder) or not os.path.exists(s2_mask_folder):
        print(f"Οι φάκελοι του S2 δεν βρέθηκαν: {input_path}")
        return

    # Διαβάζουμε και επεξεργαζόμαστε τις εικόνες σε κάθε φάκελο
    for folder in [s1_after_folder, s1_before_folder, s1_mask_folder, s2_after_folder, s2_before_folder, s2_mask_folder]:
        files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])

        for file in files:
            file_path = os.path.join(folder, file)

            # Διαβάζουμε την εικόνα
            image = cv2.imread(file_path)
            
            # Διαχωρίζουμε την εικόνα σε patches και παίρνουμε την έγκυρη περιοχή
            patches, valid_area = split_image(image)
            
            # Δημιουργούμε το batch και αποθηκεύουμε τα δεδομένα
            for i, patch in enumerate(patches):
                # Παράγουμε τον αριθμό batch για τα S1, S2, Mask, και Data
                patch_filename = f"{batch_count}_{i}.png"
                s1_filename = f"s1_batch_{batch_count}_{i}.png"
                s2_filename = f"s2_batch_{batch_count}_{i}.png"
                mask_filename = f"mask_batch_{batch_count}_{i}.png"
                data_filename = f"data_batch_{batch_count}_{i}.png"

                # Αποθήκευση S1, S2 και MASK
                if folder == s1_after_folder:
                    cv2.imwrite(os.path.join(output_path, "S1_test", s1_filename), patch)
                elif folder == s2_after_folder:
                    cv2.imwrite(os.path.join(output_path, "S2_test", s2_filename), patch)
                elif folder == s1_mask_folder:
                    cv2.imwrite(os.path.join(output_path, "Mask_test", mask_filename), patch)
                elif folder == s2_mask_folder:
                    cv2.imwrite(os.path.join(output_path, "Mask_test", mask_filename), patch)

                # Δημιουργούμε το data_test για την έγκυρη περιοχή
                # Το data_test θα έχει 1 για έγκυρο, 0 για μη έγκυρο
                if valid_area[i] == 0:
                    # Αν το patch δεν είναι έγκυρο (είχε padding), βάζουμε 0 για τα μη έγκυρα pixels
                    data_patch = np.zeros_like(patch)
                else:
                    # Αν είναι έγκυρο, κρατάμε την εικόνα ως έχει
                    data_patch = patch

                cv2.imwrite(os.path.join(output_path, "data_test", data_filename), data_patch)

            batch_count += 1
            print(f"Processed batch {batch_count} from {file}")

def main():
    input_path = r'C:\Users\csdro\OMBRIA-master\EMSR750_results'
    output_path = r'C:\Users\csdro\OMBRIA-master\Processed_data'
    
    process_images(input_path, output_path)

if __name__ == "__main__":
    main()
