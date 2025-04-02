from CRMAPI import CRMAPI
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.geometry import Polygon, LineString, Point, mapping
from sentinelhub import SHConfig, BBox, DataCollection, SentinelHubRequest, MimeType
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import os, io, tarfile, json, requests
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import datetime as dt, timedelta
from shutil import move
import numpy as np
import datetime
import shapely.wkt
import os
import matplotlib.pyplot as plt
import numpy as np
import shutil
from datetime import date
from datetime import datetime
import folium 
import pytz
import numpy as np
import os
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from sentinelhub import Geometry, CRS, DataCollection, MimeType, SentinelHubRequest
from PIL import Image
import datetime
import pytz
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    DownloadRequest,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    bbox_to_dimensions,
)

#Initialize CRMAPI
rm = CRMAPI()

current_directory=os.getcwd()

client_id='sh-f7cc8302-169d-4001-8f42-0073e0e134f7'
client_secret='2QEneiG3a60JwXSLTZFyHxBYf48nmKF2'
    
config = SHConfig()
config.sh_client_id=client_id
config.sh_client_secret=client_secret

today=datetime.datetime.now(datetime.timezone.utc)

class SentinelAPI():
    #Default Constructor
    def __init__(self):
        self.config = config
        
    def get_images_for_past_3_months(self, res, event_id, sentinel_num):
        """
            Retrieves and saves Sentinel-2 satellite images for the three months leading up to a specified event date.
            ----------
            Parameters:
            1) event_details: Dictionary containing details about the event, including the event time and geographical extent.
            2) event_id : A unique identifier for the event, used to organize the saved images.
            ----------
            Returns:
            ->directory
            1) images_directory: The directory path where the Sentinel-2 images are saved.
        """
        all_sentinel2 = []
        event_date_str = res['eventTime']
        event_date = dt.fromisoformat(event_date_str)

        #Calculate the date three months before the event date
        three_months_before = event_date - relativedelta(months=3)

        #Initialize variables for looping
        current_date = event_date
        counter = 1

        #Directory for saving images
        current_directory = os.getcwd()
        images_directory = os.path.join(current_directory, event_id, "Sentinel_Images_Before")
        if not os.path.exists(images_directory):
            os.makedirs(images_directory)

        #Iterate backwards in weekly intervals
        while current_date > three_months_before:
            #Define the interval as one week before the current date
            interval_end = current_date
            interval_start = interval_end - timedelta(weeks=1)

            #Format interval dates as strings
            interval_start_str = interval_start.strftime('%Y-%m-%d')
            interval_end_str = interval_end.strftime('%Y-%m-%d')

            #Fetch the sentinel data for the given interval
            time_interval = [interval_start_str, interval_end_str]
            polygon_str = res['extent']

            #Create Shapely geometry from the WKT string
            shapely_geometry = shapely.wkt.loads(polygon_str)

            #Convert Shapely geometry to Sentinel Hub Geometry, assuming the CRS is WGS84 (EPSG:4326)
            geometry = Geometry(shapely_geometry, CRS.WGS84)
            if sentinel_num ==1:
                data = self.get_sentinel1_data(geometry, self.config, time_interval, "BeforeEventSentinel1", event_id)
            elif sentinel_num==2:
                data = self.get_sentinel2_data(geometry, self.config, time_interval, "BeforeEventSentinel2", event_id)
            else:
                data = self.get_sentinel3_data(geometry, self.config, time_interval, "BeforeEventSentinel3", event_id)
            #Convert data to an image and save it
            im = Image.fromarray(data)
            image_filename = 's'+str(sentinel_num)+"_"+interval_start_str+"_"+ interval_end_str+".tif"
            im.save(os.path.join(images_directory, image_filename))

            #Move to the previous week
            counter += 1
            current_date -= timedelta(weeks=1)
            all_sentinel2.append(data)

        
        return images_directory

    def get_image_after_event(self, res, event_id, sentinel_num):
        """
            Downloads a Sentinel-2 image for the date two days after the event and stores it with the prefix 'AfterEvent'.
            ----------
            Parameters:
            1) res: Dictionary containing details about the event, including the event time and geographical extent.
            2) event_id: A unique identifier for the event, used to organize the saved images.
            3) sentinel_num: The sentinel satellite number (1, 2, or 3).
            ----------
            Returns:
            -> directory
            1) images_directory: The directory path where the Sentinel-2 image is saved.
        """
        event_date_str = res['eventTime']
        event_date = dt.fromisoformat(event_date_str)

        # Calculate the date two days after the event date
        two_days_after = event_date + timedelta(days=5)

        # Format the date as a string
        two_days_after_str = two_days_after.strftime('%Y-%m-%d')

        # Directory for saving images
        current_directory = os.getcwd()
        images_directory = os.path.join(current_directory, event_id, "Sentinel_Images_After")
        if not os.path.exists(images_directory):
            os.makedirs(images_directory)

        # Fetch the sentinel data for the date two days after the event
        time_interval = [two_days_after_str, two_days_after_str]
        polygon_str = res['extent']

        # Create Shapely geometry from the WKT string
        shapely_geometry = shapely.wkt.loads(polygon_str)

        # Convert Shapely geometry to Sentinel Hub Geometry, assuming the CRS is WGS84 (EPSG:4326)
        geometry = Geometry(shapely_geometry, CRS.WGS84)

        if sentinel_num == 1:
            data = self.get_sentinel1_data(geometry, self.config, time_interval, "AfterEventSentinel1", event_id)
        elif sentinel_num == 2:
            data = self.get_sentinel2_data(geometry, self.config, time_interval, "AfterEventSentinel2", event_id)
        else:
            data = self.get_sentinel3_data(geometry, self.config, time_interval, "AfterEventSentinel3", event_id)

        # Convert data to an image and save it
        im = Image.fromarray(data)
        image_filename = 's' + str(sentinel_num) + "_AfterEvent_" + two_days_after_str + ".tif"
        im.save(os.path.join(images_directory, image_filename))

        return images_directory

    def get_sentinel1_data(self, geometry, config, time_interval, filename, event_id):
        """
        Retrieves Sentinel-1 satellite data for a specified time interval and geometry, 
        saves the data as a TIFF image, and returns the data.
        ----------
        Parameters:
        1) geometry: The geographical area of interest.
        2) config: Configuration settings for the Sentinel Hub request.
        3) time_interval (tuple): The start and end dates for data retrieval.
        4) filename: The name of the file to save the data.
        5) event_id: Identifier for the event, used to organize the saved data.
        ----------
        Returns:
        -> array
        1) data: The retrieved Sentinel-1 satellite data.
        """
        # Define the target directory for saving images
        target_directory = os.path.join(os.getcwd(), event_id, "Sentinel_Images")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        request = SentinelHubRequest(
            data_folder=target_directory,
            evalscript="""
            //VERSION=3

            function setup() {
                return {
                    input: ["VV"],
                    output: { bands: 1 }
                };
            }

            function evaluatePixel(sample) {
                return [sample.VV];
            }
            """,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL1,
                    time_interval=time_interval,
                ),
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.TIFF),
            ],
            geometry=geometry,
            size=(2048, 2048),
            config=config
        )
        
        # Save the data
       # request.save_data()
        
        # Get the saved data
        data = request.get_data()[0]
        
        # Define the filename for the saved TIFF file
        tiff_file_path = os.path.join(target_directory, filename + ".tif")
        
        # Save the data directly as TIFF file
        with open(tiff_file_path, 'wb') as f:
            f.write(data)
        
        # Optional: Check and clean up if the data array is all zeros
        if np.sum(data) == 0:
            if os.path.exists(tiff_file_path):
                os.remove(tiff_file_path)
        
        return data
    
    def get_sentinel2_data(self, geometry, config, time_interval, filename, event_id):
        """
        Retrieves Sentinel-2 satellite data for a specified time interval and geometry, 
        saves the data as a TIFF image, and returns the data.
        ----------
        Parameters:
        1) geometry: The geographical area of interest.
        2) config: Configuration settings for the Sentinel Hub request.
        3) time_interval (tuple): The start and end dates for data retrieval.
        4) filename: The name of the file to save the data.
        5) event_id: Identifier for the event, used to organize the saved data.
        ----------
        Returns:
        -> array
        1) data: The retrieved Sentinel-2 satellite data.
        """
        # Define the target directory for saving images
        target_directory = os.path.join(os.getcwd(), event_id, "Sentinel_Images")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        request = SentinelHubRequest(
            data_folder=target_directory,
            evalscript="""
            //VERSION=3
            
            let minVal = 0.0;
            let maxVal = 0.4;
            
            let viz = new HighlightCompressVisualizer(minVal, maxVal);
            
            function evaluatePixel(samples) {
                let val = [samples.B04, samples.B03, samples.B02];
                val = viz.processList(val);
                val.push(samples.dataMask);
                return val;
            }
            
            function setup() {
                return {
                    input: [{
                        bands: [
                            "B02",
                            "B03",
                            "B04",
                            "dataMask"
                        ]
                    }],
                    output: {
                        bands: 4
                    }
                }
            }
            """,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,   
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                    time_interval=time_interval,
                ),
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.TIFF),
            ],
            geometry=geometry,
            size=(2048, 2048),
            config=config
        )
        
        # Save the data
        #request.save_data()
        
        # Get the saved data
        data = request.get_data()[0]
        
        # Define the filename for the saved TIFF file
        tiff_file_path = os.path.join(target_directory, filename + ".tif")
        
        # Save the data directly as TIFF file
        with open(tiff_file_path, 'wb') as f:
            f.write(data)
        
        # Optional: Check and clean up if the data array is all zeros
        if np.sum(data) == 0:
            if os.path.exists(tiff_file_path):
                os.remove(tiff_file_path)
        
        return data

    def get_sentinel3_data(self, geometry, config, time_interval, filename, event_id):
        """
        Retrieves Sentinel-3 satellite data for a specified time interval and geometry, 
        saves the data as a TIFF image, and returns the data.
        ----------
        Parameters:
        1) geometry: The geographical area of interest.
        2) config: Configuration settings for the Sentinel Hub request.
        3) time_interval: The start and end dates for data retrieval.
        4) filename: The name of the file to save the data.
        5) event_id: Identifier for the event, used to organize the saved data.
        ----------
        Returns:
        -> array
        1) data: The retrieved Sentinel-3 satellite data.
        """
        # Define the target directory for saving images
        target_directory = os.path.join(os.getcwd(), event_id, "Sentinel_Images")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["S1", "S2", "S3", "S5", "S6"],
                output: {
                    bands: 3,
                    sampleType: "AUTO",
                },
            }
        }

        function evaluatePixel(sample) {
            // NDVI calculation
            var ndvi = (sample.S3 - sample.S2) / (sample.S3 + sample.S2);
            
            // Enhanced vegetation index
            var evi = 2.5 * ((sample.S3 - sample.S2) / (sample.S3 + 6 * sample.S2 - 7.5 * sample.S1 + 1));
            
            // Short-wave infrared combination
            var swir = (sample.S5 + sample.S6) / 2;
            
            return [2.5 * swir, 2.5 * evi, 2.5 * sample.S1];
        }
        """

        request = SentinelHubRequest(
            data_folder=target_directory,
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL3_SLSTR,
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                    time_interval=time_interval,
                ),
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.TIFF),
            ],
            geometry=geometry,
            size=(2048, 2048),
            config=config
        )
        
        # Save the data
        #request.save_data()
        
        # Get the saved data
        data = request.get_data()[0]
        
        # Define the filename for the saved TIFF file
        tiff_file_path = os.path.join(target_directory, filename + ".tif")
        
        # Save the data directly as TIFF file
        with open(tiff_file_path, 'wb') as f:
            f.write(data)
        
        # Optional: Check and clean up if the data array is all zeros
        if np.sum(data) == 0:
            if os.path.exists(tiff_file_path):
                os.remove(tiff_file_path)
        
        return data

    def get_sentinel_map(self, event_details, event_id, sentinel_version):
        """
        Generates a map overlay using Sentinel satellite data for a specific event 
        and version, and returns the map and event details.
        ----------
        Parameters:
        1) event_details: Main dictionary of the event
        2) event_id: Identifier for the event.
        3) sentinel_version: Version of Sentinel data to retrieve (1, 2, or 3).
        ----------
        Returns:
        ->folium map
        1) m: A Folium map object with the Sentinel data overlay.
        ->dictionary
        2) res: The event details used for creating the map.
        """
        res = event_details['results'][0]

        # Parse event date
        event_date_str = event_details['results'][0]['eventTime']
        event_date = dt.fromisoformat(event_date_str)

        date_before_start = event_date - timedelta(days=7)
        date_before_end = event_date - timedelta(days=1)

        # Initialize the map variable
        m = None

        # Determine the number of AOIs
        size = len(res['aois'])

        # Choose the appropriate Sentinel data function based on the version
        if sentinel_version == 1:
            get_sentinel_data = self.get_sentinel1_data
        elif sentinel_version == 2:
            get_sentinel_data = self.get_sentinel2_data
        elif sentinel_version == 3:
            get_sentinel_data = self.get_sentinel3_data
        else:
            raise ValueError("Invalid Sentinel version. Choose 1, 2, or 3.")

        if size == 1:
            # Get the area of interest (AOI) from the event details
            polygon_str = res['extent']

            # Create Shapely geometry from the WKT string
            shapely_geometry = shapely.wkt.loads(polygon_str)

            # Convert Shapely geometry to Sentinel Hub Geometry, assuming the CRS is WGS84 (EPSG:4326)
            geometry = Geometry(shapely_geometry, CRS.WGS84)

            # Get Sentinel data
            data = get_sentinel_data(geometry, self.config, (date_before_start, date_before_end), f'Sentinel{sentinel_version}', event_id)

            # Create a Folium map centered on the geometry
            map_center = [geometry.geometry.centroid.y, geometry.geometry.centroid.x]
            m = folium.Map(location=map_center, zoom_start=12)

            # Define the bounding box for the geometry
            bbox = geometry.bbox
            bounds = [[bbox.min_y, bbox.min_x], [bbox.max_y, bbox.max_x]]

            # Overlay the Sentinel data image on the Folium map
            image_overlay = folium.raster_layers.ImageOverlay(
                name=f"Sentinel-{sentinel_version} Image",
                control=False,
                image=data,
                bounds=bounds,
                opacity=1
            )
            image_overlay.add_to(m)

        else:
            map_center = [0, 0]
            m = folium.Map(location=map_center, zoom_start=12)

            for j in range(size):
                event_id = os.path.join(res['code'], f'AOI{j+1}')
                files_path = os.path.join(event_id)
                extent_path = os.path.join(event_id, f'AOI{j+1}_Extent.json')

                # Read and load the extent data
                with open(extent_path, 'r') as extent_file:
                    data = json.load(extent_file)

                for polygon_data in data:
                    # Ensure that we are dealing with a dictionary with the key "Coordinates"
                    if "Coordinates" not in polygon_data:
                        continue

                    extent_coordinates = polygon_data['Coordinates']

                    extent_coordinates = [(coord[1], coord[0]) for coord in extent_coordinates]

                    # Create Shapely Polygon using the coordinates
                    polygon = Polygon(extent_coordinates)
                    if not polygon.is_valid:
                        continue

                    minx, miny, maxx, maxy = polygon.bounds
                    shape_res = rm.determine_resolution((minx, miny, maxx, maxy))
                    shape = (shape_res, shape_res)
                    transform = from_bounds(minx, miny, maxx, maxy, shape[1], shape[0])

                    # Convert Shapely geometry to Sentinel Hub Geometry, assuming the CRS is WGS84 (EPSG:4326)
                    geometry = Geometry(polygon, CRS.WGS84)

                    # Fetch Sentinel data
                    sentinel_data = get_sentinel_data(geometry, self.config, (date_before_start, date_before_end), "aname", event_id)

                    # Define the bounding box for the geometry
                    bounds = [[miny, minx], [maxy, maxx]]

                    # Overlay the Sentinel data image on the Folium map
                    image_overlay = folium.raster_layers.ImageOverlay(
                        name=f"Sentinel-{sentinel_version} Image AOI {j+1}",
                        image=sentinel_data,
                        bounds=bounds,
                        control=False,
                        opacity=1
                    )
                    image_overlay.add_to(m)

        return m, res, sentinel_data

    def get_sentinel1_map(self,event_details,event_id):
        """
            Generates and saves a Sentinel-1 map overlay for a specific event.
            ----------
            Parameters:
            1) event_details: Main dictionary of the event
            2) event_id: Identifier for the event.
        """
        map_s1,res_s1 = self.get_sentinel_map(event_details,event_id, 1)
        rm.add_layers(res_s1,'Sentinel1.html',map_s1)
        
    def get_sentinel2_map(self,event_details,event_id):
        """
            Generates and saves a Sentinel-2 map overlay for a specific event.
            ----------
            Parameters:
            1) event_details: Main dictionary of the event
            2) event_id: Identifier for the event.
        """
        map_s2, res_s2 = self.get_sentinel_map(event_details,event_id, 2)
        rm.add_layers(res_s2,'Sentinel2.html',map_s2)
        
    def get_sentinel3_map(self,event_details,event_id):
        """
            Generates and saves a Sentinel-3 map overlay for a specific event.
            ----------
            Parameters:
            1) event_details: Main dictionary of the event
            2) event_id: Identifier for the event.
        """
        map_s3, res_s3 = self.get_sentinel_map(event_details,event_id, 3)
        rm.add_layers(res_s3,'Sentinel3.html',map_s3)