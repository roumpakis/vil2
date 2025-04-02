import geopandas as gpd
import matplotlib.pyplot as plt
import os
from geocube.api.core import make_geocube
import rasterio
import numpy as np
import json
from shapely.geometry import box, mapping
import cv2

def generate_raster_mask(event_id, folder_version, Kind, aoi_number, height, width, base_path, product_type, file_version):
    """
    Generate a raster mask from a shapefile and save it as GeoTIFF and PNG.
    
    Parameters:
        event_id (int): Event ID
        version (int): Version of the dataset
        Kind (str): Type of event (e.g., "GRA")
        aoi_number (str): Area of Interest number
        height (int): Height of the output raster
        width (int): Width of the output raster
        base_path (str): Base path to the dataset
        product_type (str): The type of the product (e.g., PRODUCT, MONIT02)
    """
    # Update paths to include the `type` parameter
    obs_path = f"{base_path}\\EMSR{event_id}_extracted\\EMSR{event_id}_AOI{aoi_number}_{Kind}_{product_type}_v{folder_version}\\EMSR{event_id}_AOI{aoi_number}_{Kind}_{product_type}_observedEventA_v{file_version}.shp"
    aoi_path = f"{base_path}\\EMSR{event_id}_extracted\\EMSR{event_id}_AOI{aoi_number}_{Kind}_{product_type}_v{folder_version}\\EMSR{event_id}_AOI{aoi_number}_{Kind}_{product_type}_areaOfInterestA_v{file_version}.shp"
    mask_path = f"{base_path}\\EMSR{event_id}_extracted\\EMSR{event_id}_AOI{aoi_number}_{Kind}_{product_type}_v{folder_version}\\Maps"

    print("Observed Event Path:", obs_path)
    print("Area of Interest Path:", aoi_path)
    print("Mask Path:", mask_path)
    
    # Load the shapefiles using GeoPandas
    shape_file_obs = gpd.read_file(obs_path)
    shape_file_aoi = gpd.read_file(aoi_path)
    
    desired_shape = (height, width)
    column_to_rasterize = "dmg_src_id"  # Column to rasterize from the shapefile
    bounds = list(shape_file_aoi.geometry.to_list()[0].bounds)
    
    # Calculate the resolutions based on the bounds
    x_resolution = (bounds[2] - bounds[0]) / (desired_shape[1] - 1)
    y_resolution = (bounds[3] - bounds[1]) / (desired_shape[0] - 1)
    resolution = (-y_resolution, x_resolution)
    
    # Create the geocube (rasterized shapefile)
    geocube = make_geocube(
        vector_data=shape_file_obs,
        measurements=[column_to_rasterize],
        resolution =resolution,
        geom=json.dumps(mapping(box(bounds[0], bounds[1], bounds[2], bounds[3]))),
        output_crs=shape_file_obs.crs,
        fill=0
    )
    
    # Define the mask file paths for GeoTIFF and PNG
    mask_tif = os.path.join(mask_path, f"mask_raster_{event_id}.tif")
    geocube[column_to_rasterize].rio.to_raster(mask_tif)
    
    # Convert the GeoTIFF to PNG and save
    mask_file = os.path.join(mask_path, f"mask_{event_id}.png")
    with rasterio.open(mask_tif) as src:
        data = src.read(1)
        data[data != 0] = 255  # Set all non-zero values to 255 (for mask visualization)
        cv2.imwrite(mask_file, data)
        # Optionally display the mask with matplotlib (commented out)
        #plt.imshow(data, cmap='gray')
        #plt.axis('off')
        #plt.show()
    
    # Output diagnostic information
    print(data)
    print("Shape:", data.shape)
    print("Min, Max:", data.min(), data.max())
    print("Data Type:", data.dtype)
    print("Top-left pixel value:", data[0, 0])
    
    return data
