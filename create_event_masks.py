import os
import re
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import numpy as np
import rasterio
from generate_raster_mask import generate_raster_mask

def create_event_masks(base_path, event_id):
    """
    Processes and visualizes event images based on extracted directory.
    Automatically determines the image dimensions from a Sentinel-2 TIFF file.

    Parameters:
    - base_path (str): The base directory where data is stored.
    - event_id (int): The event ID for processing.

    Returns:
    - None
    """

    # Define main directory and extracted directory paths
    main_dir = os.path.join(base_path, f"EMSR{event_id}_results")
    extracted_dir = os.path.join(base_path, f"EMSR{event_id}_extracted")

    # Ensure results directory exists
    os.makedirs(main_dir, exist_ok=True)

    # Find a Sentinel-2 .tiff image and determine its dimensions
    def get_image_dimensions(directory):
        for file in os.listdir(directory):
            if file.lower().endswith(".tiff") and "sentinel2" in file.lower():
                tiff_path = os.path.join(directory, file)
                with rasterio.open(tiff_path) as dataset:
                    print('height: ', dataset.height, ' width: ', dataset.width)
                    return dataset.height, dataset.width
        return 256, 256  # Default if no suitable image is found

    # Get dimensions from Sentinel-2 image or default to 256x256
    height, width = get_image_dimensions(main_dir)
    print(f"Using image dimensions: {height}x{width}")

    # Function to extract both folder_version and file_version
    def get_existing_combinations(extracted_dir):
        existing_combinations = []
        pattern = re.compile(r"EMSR(\d+)_AOI(\d+)_([A-Z]+)_(\w+)_v(\d+)")

        for root, dirs, _ in os.walk(extracted_dir):
            for dir_name in dirs:
                match = pattern.match(dir_name)
                if match:
                    aoi_number = match.group(2)
                    kind = match.group(3)
                    product_type = match.group(4)
                    folder_version = match.group(5)

                    # Find the shapefiles inside the folder to determine file_version
                    shapefile_pattern = re.compile(
                        fr"EMSR{event_id}_AOI{aoi_number}_{kind}_{product_type}_.*_v(\d+)\.shp"
                    )
                    file_version = None

                    folder_path = os.path.join(root, dir_name)
                    for file in os.listdir(folder_path):
                        shapefile_match = shapefile_pattern.match(file)
                        if shapefile_match:
                            file_version = shapefile_match.group(1)
                            break  # Take the first one found

                    if file_version is None:
                        print(f"Warning: No shapefile found for {dir_name}. Skipping.")
                        continue

                    combination = [aoi_number, kind, product_type, folder_version, file_version]
                    if combination not in existing_combinations:
                        existing_combinations.append(combination)

        return existing_combinations

    # Get all available data combinations
    all_data = get_existing_combinations(extracted_dir)
    print(f"Total data combinations found: {len(all_data)}")

    # Determine grid layout for subplots
    num_plots = len(all_data)
    cols = 2  # Adjust this number to control the number of columns
    rows = (num_plots // cols) + (1 if num_plots % cols != 0 else 0)

    # Create a figure with subplots
    fig, axes = plt.subplots(rows, cols, figsize=(15, 15))
    axes = axes.flatten()  # Flatten for easy iteration

    for idx, data in enumerate(all_data):
        title = f"AOI: {data[0]}, Kind: {data[1]}, Product type: {data[2]}, Folder Version: {data[3]}, File Version: {data[4]}"
        filename = f"{data[0]}_{data[1]}_{data[2]}_{data[3]}_{data[4]}.png"
        print(f"Processing: {title}")

        # Extract metadata
        aoi_number, kind, product_type, folder_version, file_version = data

        # Generate raster mask with correct versions
        mask = generate_raster_mask(event_id, folder_version, kind, aoi_number, height, width, base_path, product_type, file_version)

        if mask is None:
            print(f"Skipping {filename}: Mask generation failed.")
            continue

        # Convert to uint8 if necessary
        if mask.dtype != np.uint8:
            mask = mask.astype(np.uint8)

        # Save the mask image
        png_path = os.path.join(main_dir, filename)
        imageio.imwrite(png_path, mask)
        print(f"Saved: {png_path}")

        # Plot the mask
        axes[idx].imshow(mask, cmap='gray')
        axes[idx].set_title(title)
        axes[idx].axis('off')

    # Hide unused subplots
    for j in range(num_plots, len(axes)):
        axes[j].axis('off')

    # Adjust layout and display
    #plt.tight_layout()
    #plt.show()
    return

    # Example usage
#base_path = "D:\\GitHub\\okok"
#event_id = 736
#create_event_masks(base_path, event_id)


