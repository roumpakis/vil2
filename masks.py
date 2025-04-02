import os
import cv2
import matplotlib.pyplot as plt
import numpy as np

def split_image(image, patch_size=256):
    """
    Διαχωρίζει την εικόνα σε μικρότερα κομμάτια (patches) μεγέθους patch_size x patch_size.
    Αν το τελευταίο κομμάτι είναι μικρότερο, προσθέτει padding.
    Επιστρέφει τα patches μαζί με τις συντεταγμένες τους και τις μάσκες για το padding.
    """
    height, width, _ = image.shape
    patches = []
    valid_area = []  # Θα κρατάμε αν το patch είναι έγκυρο ή όχι
    masks = []  # Μάσκες για τα δεδομένα (μάυρο padding)
    data_masks = []  # Μάσκες για τα padding με 0 για μη έγκυρα, 1 για έγκυρα pixels

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
                # Δημιουργούμε τη μάσκα για το padding
                mask = np.ones((patch_size, patch_size), dtype=np.uint8)  # Μαύρη μάσκα
                mask[patch.shape[0]:, patch.shape[1]:] = 0  # Μη έγκυρα pixels (padding) = 0
                masks.append(mask)
                data_masks.append(np.zeros_like(patch))  # Data mask που θα έχει 0 για τα pixels του padding
            else:
                valid_area.append(1)  # Το patch είναι έγκυρο
                masks.append(np.ones((patch_size, patch_size), dtype=np.uint8))  # Ολόκληρο το patch έγκυρο
                data_masks.append(np.ones_like(patch))  # Data mask με 1 για όλα τα pixels

            patches.append(patch)

    return patches, valid_area, masks, data_masks

def plot_data_masks(data_masks, batch_count):
    """
    Πλοτάρει τα data_masks (μάσκες για τα padding) που δημιουργούμε στο προηγούμενο βήμα.
    Το κάθε data_mask δείχνει ποια pixels είναι padding και ποια είναι έγκυρα.
    """
    for i, data_mask in enumerate(data_masks):
        plt.figure(figsize=(5, 5))
        plt.imshow(data_mask, cmap='gray')
        plt.title(f"Data Mask {batch_count}_{i}")
        plt.colorbar()
        plt.show()


def process_and_plot_data_masks(input_path, output_path):
    """
    Διαβάζει τις εικόνες και τα data_masks, και τα πλοτάρει.
    """
    batch_count = 0

    # Φάκελοι για τα δεδομένα
    s1_after_folder = os.path.join(input_path, "S1", "AFTER")
    s2_after_folder = os.path.join(input_path, "S2", "AFTER")
    s1_mask_folder = os.path.join(input_path, "S1", "MASK")
    s2_mask_folder = os.path.join(input_path, "S2", "MASK")

    # Διαβάζουμε τα δεδομένα από τους φακέλους
    for folder in [s1_after_folder, s2_after_folder, s1_mask_folder, s2_mask_folder]:
        files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])

        for file in files:
            file_path = os.path.join(folder, file)

            # Διαβάζουμε την εικόνα
            image = cv2.imread(file_path)

            # Καλούμε την προηγούμενη συνάρτηση για να πάρουμε τα patches και τις μάσκες
            patches, valid_area, masks, data_masks = split_image(image)

            # Πλοτάρουμε τα data_masks για κάθε εικόνα
            plot_data_masks(data_masks, batch_count)
            print(valid_area)
            batch_count += 1
            print(f"Processed batch {batch_count} from {file}")


def main():
    input_path = r'C:\Users\csdro\OMBRIA-master\EMSR750_results'
    output_path = r'C:\Users\csdro\OMBRIA-master\Processed_data'

    # Καλούμε τη συνάρτηση που διαβάζει και πλοτάρει τα data_masks
    process_and_plot_data_masks(input_path, output_path)

if __name__ == "__main__":
    main()
