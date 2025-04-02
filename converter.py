import os
import rasterio
import numpy as np
from PIL import Image

def convert_tiff_to_png(root_folder):
    for foldername, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith(".tiff"):
                tiff_path = os.path.join(foldername, filename)
                png_path = os.path.join(foldername, filename.rsplit(".", 1)[0] + ".png")
                
                try:
                    with rasterio.open(tiff_path) as dataset:
                        # Read bands 3 (Green), 8 (NIR), 11 (SWIR)
                        band_data = np.stack([dataset.read(i) for i in [3, 8, 11]], axis=-1).astype(np.float32)
                        
                        # Replace NoData values with 0
                        band_data[band_data == dataset.nodata] = 0
                        
                        # Normalize each band independently
                        for i in range(3):
                            min_val, max_val = np.percentile(band_data[:, :, i], (2, 98))  # Stretch contrast
                            if max_val - min_val > 0:
                                band_data[:, :, i] = np.clip((band_data[:, :, i] - min_val) / (max_val - min_val) * 255, 0, 255)
                            else:
                                band_data[:, :, i] = 0  # Avoid divide by zero
                        
                        band_data = band_data.astype(np.uint8)
                        img = Image.fromarray(band_data, mode="RGB")
                        img.save(png_path, "PNG")
                    print(f"Converted: {tiff_path} -> {png_path}")
                except Exception as e:
                    print(f"Error converting {tiff_path}: {e}")

if __name__ == "__main__":
    root_directory = r"C:\\Users\\csdro\\Downloads\\app_12_2\\autoeinai\\to_new\\EMSR795_results"
    convert_tiff_to_png(root_directory)
