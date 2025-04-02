# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 10:19:53 2024

@author: roub
"""

from sentinelhub import SHConfig, BBox, DataCollection, SentinelHubRequest, MimeType
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
# from copernicusNotify import copernicusNotify as CN
import os, io, tarfile, json, requests
from datetime import datetime, timedelta
from datetime import datetime as dt, timedelta
from shutil import move
import numpy as np
import datetime
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
current_directory = os.getcwd()
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
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
import numpy as np
import matplotlib.pyplot as plt
from sentinelhub import Geometry, CRS, DataCollection, MimeType, SentinelHubRequest
from PIL import Image
# from EMSAPIs import EMSAPIs 
#37e4eab1-dc34-4753-94cf-c02e92a4a595
client_id='37e4eab1-dc34-4753-94cf-c02e92a4a595'
client_secret='bOad2DGRO6ElIRPTfONSLjbVr5mBWrvX'
    
        # Configure your API credentials and instance ID
config = SHConfig()
config.sh_client_id = client_id
config.sh_client_secret = client_secret
import datetime
import pytz

# Replace this line
# today = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

# With this line
today = datetime.datetime.now(datetime.timezone.utc)
print(today)

# today = datetime.utcnow().replace(tzinfo=pytz.utc)

# cn = CN()
# events,feed = cn.get_all_notifications()
# e = events[0]

class sentinelAPI():
    
    def __init__(self):
        self.config = config
        
    def get_event_map(self,e):
        r""" get_event_map
            
                Function that creates a folium map with a specific rectangle area around a copernicusl event location.
            
                Parameters
                ----------
                e : dictionary
                    The Copernicus event object
                    Dictionary of must contain the following keys:
            
                    * ``title``: The copernicous event tile.
                    * ``link``: Link to event website.
                    * ``published``: The date of event publication.
                    * ``coords``: The longitude and latitude coordinates.
                    * ``details``: The details of risk assessment .
                    * ``id``: The ID of copernicus event EMSRxxx           
                Returns
                -------
                folium map
                    The folium map with event location and a rectangle AOI.

            
            
                """
    
        long = e['coords'][1]
        lat =  e['coords'][0]
        event_date = dt.strptime(e['published'], '%a, %d %b %Y %H:%M:%S %z')

        square_size = 0.1/4

        # Define a GeoJSON geometry
        long_lat = {
            "type": "Polygon",
            "coordinates": [
                [
          [long - square_size / 2, lat + square_size / 2] ,  # Top-left
            [long + square_size / 2, lat + square_size / 2, ],  # Top-right
            [ long + square_size / 2,lat - square_size / 2],  # Bottom-right
            [long - square_size / 2, lat - square_size / 2 ],  # Bottom-left
        
                ]
            ]
        }
        lat_long= {
            "type": "Polygon",
            "coordinates": [
                [
          [lat + square_size / 2, long - square_size / 2 ] ,  # Top-left
            [lat + square_size / 2 , long + square_size / 2  ],  # Top-right
            [ lat - square_size / 2, long + square_size / 2],  # Bottom-right
            [lat - square_size / 2 , long - square_size / 2  ],  # Bottom-left
        
                ]
            ]
        }
        # Extract longitudes and latitudes
        longitudes = [round(coord[0],6) for coord in long_lat["coordinates"][0]]
        latitudes = [round(coord[1],6) for coord in long_lat["coordinates"][0]]

        # Find minimum and maximum values
        min_longitude = min(longitudes)
        max_longitude = max(longitudes)
        min_latitude = min(latitudes)
        max_latitude = max(latitudes)
        polygon_coordinates = long_lat["coordinates"][0]
        map_center = [long,lat]
        mymap = folium.Map(location=map_center, zoom_start=12)
        folium.Polygon(locations=polygon_coordinates, color='blue', fill=True, fill_color='blue').add_to(mymap)
        
        # Add a pin marker at the specified latitude and longitude
        folium.Marker(location=[long, lat], popup=e['title']).add_to(mymap)
        mask_img =current_directory+ '\\mapicons\\f\\response.jpg'
        # Save the map as an HTML file or display it in the Jupyter Notebook
        folium.raster_layers.ImageOverlay(
             image=mask_img,
             bounds=[(min_longitude,min_latitude),
                     (max_longitude,max_latitude)],
             # bounds=[(27.0,-18.0),
             #         (72.0,42.0)],    
             opacity=1,
             interactive=True,
             cross_origin=False,
             # colormap=lambda x: (0, 0, 0, 0),  # Make the image fully opaque
         ).add_to(mymap)
        return mymap

    def get_event_images_before(self,e):
        r""" get_event_images_before
            
                Function that retrives images before the event. The time interval is 20 days before.
            
                Parameters
                ----------
                e : dictionary
                    The Copernicus event object
                    Dictionary of must contain the following keys:
            
                    * ``title``: The copernicous event tile.
                    * ``link``: Link to event website.
                    * ``published``: The date of event publication.
                    * ``coords``: The longitude and latitude coordinates.
                    * ``details``: The details of risk assessment .
                    * ``id``: The ID of copernicus event EMSRxxx           
                Returns
                -------
                data : np.array
                    The image before the event occurance.

            
            
                """
        long = e['coords'][1]
        lat =  e['coords'][0]
        event_date = dt.strptime(e['published'], '%a, %d %b %Y %H:%M:%S %z')

        date_before_start = event_date- timedelta(days=20)
        date_before_end = event_date - timedelta(days=1)
        time_interval_before = (date_before_start,date_before_end)

        square_size = 0.1/4

        # Define a GeoJSON geometry
        long_lat = {
            "type": "Polygon",
            "coordinates": [
                [
          [long - square_size / 2, lat + square_size / 2] ,  # Top-left
            [long + square_size / 2, lat + square_size / 2, ],  # Top-right
            [ long + square_size / 2,lat - square_size / 2],  # Bottom-right
            [long - square_size / 2, lat - square_size / 2 ],  # Bottom-left
        
                ]
            ]
        }
        lat_long= {
            "type": "Polygon",
            "coordinates": [
                [
          [lat + square_size / 2, long - square_size / 2 ] ,  # Top-left
            [lat + square_size / 2 , long + square_size / 2  ],  # Top-right
            [ lat - square_size / 2, long + square_size / 2],  # Bottom-right
            [lat - square_size / 2 , long - square_size / 2  ],  # Bottom-left
        
                ]
            ]
        }
        bbox_values = [long - square_size / 2, lat - square_size / 2, long + square_size / 2, lat + square_size / 2]
        bbox_str = "&BBOX=" + ",".join(map(str, bbox_values))
        bbox = "&BBOX=" + ",".join(map(str, bbox_values))
        
        
        
        # Convert the GeoJSON to a geometry object
        self.geometry = Geometry(lat_long, CRS('EPSG:4326'))
        
        data = self.get_sentinel_data(self,self.geometry,config,time_interval_before,"1212")
        im = Image.fromarray(data)
        im.save(os.path.join(current_directory, "images\\before.jpeg"))
        return data
    
    def get_event_images_after(self,e):
        long = e['coords'][1]
        lat =  e['coords'][0]
        event_date = dt.strptime(e['published'], '%a, %d %b %Y %H:%M:%S %z')

        date_before_start = event_date- timedelta(days=20)
        date_before_end = event_date - timedelta(days=1)
        time_interval_before = (date_before_start,date_before_end)

        square_size = 0.1/4

        # Define a GeoJSON geometry
        long_lat = {
            "type": "Polygon",
            "coordinates": [
                [
          [long - square_size / 2, lat + square_size / 2] ,  # Top-left
            [long + square_size / 2, lat + square_size / 2, ],  # Top-right
            [ long + square_size / 2,lat - square_size / 2],  # Bottom-right
            [long - square_size / 2, lat - square_size / 2 ],  # Bottom-left
        
                ]
            ]
        }
        lat_long= {
            "type": "Polygon",
            "coordinates": [
                [
          [lat + square_size / 2, long - square_size / 2 ] ,  # Top-left
            [lat + square_size / 2 , long + square_size / 2  ],  # Top-right
            [ lat - square_size / 2, long + square_size / 2],  # Bottom-right
            [lat - square_size / 2 , long - square_size / 2  ],  # Bottom-left
        
                ]
            ]
        }
        

        # Convert the GeoJSON to a geometry object
        self.geometry = Geometry(lat_long, CRS('EPSG:4326'))
        
        data = self.get_data_after(self,e,self.geometry,config)
        print(" days after ", np.sum(data))  
        im = Image.fromarray(data)
        
        im.save(os.path.join(current_directory, "images\\after.jpeg"))
        return data
    
    

    def get_data_after(self,e,geometry,config):
        i=1
        event_date = dt.strptime(e['published'], '%a, %d %b %Y %H:%M:%S %z')
        date_after_end =  event_date+ timedelta(days=1)
        time_interval_after = (event_date,date_after_end)
        data = self.get_sentinel_data(self,self.geometry,config,time_interval_after,str(i))
        filename = "after"+str(i)
        while np.sum(data) == 0 and date_after_end <= today :
            date_after_end =  date_after_end+ timedelta(days=1)
            time_interval_after = (event_date,date_after_end)
            
            data = self.get_sentinel_data(self,self.geometry,config,time_interval_after,filename)
            i=i+1
            filename = "after"+str(i)
        print(str(i)+" days after ", np.sum(data)) 
        # Calculate the mean of the entire image
        current_directory = os.getcwd()
        print(current_directory)
        mask_img =current_directory+ '\\mapicons\\f\\response.jpg'
        
        # Apply the masks to get the corresponding parts of the image
        mask = data.copy()
        
        # Set a threshold value
        threshold = np.mean(data)
        
        # Create a mask based on the threshold
        mask = data >= threshold
        
        # Convert the boolean mask to a numeric array (0 and 1)
        numeric_mask = mask.astype(float)
        
        # Create a custom colormap with different colors for True (above threshold) and False (below threshold)
        colors = ['black', 'white']
        cmap = ListedColormap(colors)
        
        # Save the numeric mask as a PNG image
        plt.imsave(mask_img, numeric_mask, cmap=cmap, vmin=0, vmax=1)
        


        return data
        
        
    def get_sentinel_data(self,geometry,config,time_interval,filename):     
        print(filename)
               ############################## AFTER 
        request = SentinelHubRequest(
            data_folder=os.path.join(current_directory, "sentinel_images\\"),
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
            #change L1C to L2A
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                                 mosaicking_order=MosaickingOrder.LEAST_CC,
                    time_interval=time_interval,
        
                ),
            ],
 responses=[
        SentinelHubRequest.output_response("default", MimeType.JPG),
    ],
            geometry=geometry,
            size=(512, 512),
            config=config
        )
        
        filename=os.path.join(current_directory, "sentinel_images\\"+filename)
        # Define the file path and name for saving the data
        # file_path = "C:\\Users\\roub\\Desktop\\folder_sentinel\\folder"+e['id']+date_before.strftime('%Y-%m-%d')+".jpg"
        request.save_data()

        data = request.get_data()[0]
        # slice_data=data[:,:,0]
        # plt.imshow(slice_data, cmap='viridis')  # You can choose a different colormap
        # plt.colorbar()  # Add a colorbar to the plot
        # plt.title('Slice of ndarray as Image')
        # plt.show()
        # print((request.data_folder))
        # for folder, _, filenames in os.walk(request.data_folder):
        #         for fname in filenames:
        #             print(os.path.join(folder, fname))
        # Assuming the data_folder contains only folders
        all_folders = [folder for folder in os.listdir(request.data_folder) if os.path.isdir(os.path.join(request.data_folder, folder))]
        if np.sum(data) ==0:
            # Find the most recent folder based on creation time
            most_recent_folder = max(all_folders, key=lambda folder: os.path.getctime(os.path.join(request.data_folder, folder)))
        
            # Construct the full path of the most recent folder
            full_path_most_recent_folder = os.path.join(request.data_folder, most_recent_folder)
        
            # Delete the most recent folder
            shutil.rmtree(full_path_most_recent_folder)
        return data
    
