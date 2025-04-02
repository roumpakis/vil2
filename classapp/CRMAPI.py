# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 11:10:35 2023

@author: roub
"""


"""CRMAPI.

This module retrives the Copernicos rapid mapping Events with the AOIs.

"""


import requests
import requests
from bs4 import BeautifulSoup
import folium


from folium.plugins import MarkerCluster, Draw

class CRMAPI():
  # default constructor
    def __init__(self, max_events=10):
        self.events,self.events_ids = self.get_all_EMSR(max_events)
        
    def get_all_EMSR(self, max_events):
        """get_all_EMSR.
                    Retrives Copernicus Rapid Mapping Events with page scrapping.
           Parameters
           ----------

           Returns
           -------
            list,list
               all_events:  List of rapid Mapping events with event details
                    * ``all_events[i][0]``: The copernicous event code EMSRxxx.
                    * ``all_events[i][1]``: Short  description of the event.
                    * ``all_events[i][2]``: The date of event occurance.
                    * ``all_events[i][3]``: The kind of the event.
                    * ``all_events[i][4]``: The location of the event.
                    
               events_ids: List of rapid Mapping events IDs
        """
        # Define the URL of the page to scrape
        # url = "https://poc-d8.lolandese.site/search-activations1"
        #url = "https://rapidmapping.emergency.copernicus.eu/backend/staticlist/"
        url = "https://mapping.emergency.copernicus.eu/activations/"
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page with BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
        
            # Find the tbody element
            tbody = soup.find("table").find("tbody")
            all_events = []
            if tbody:
                # Find all rows (tr) within the tbody
                rows = tbody.find_all("tr")
        
                # Loop through the rows and print their content
                for row in rows:
                    # Find all cells (td) within the row
                    cells = row.find_all("td")
                    per_event = []
                    # Extract and print the text from each cell
                    for cell in cells:
                        # print(cell.get_text(strip=True))
                        per_event.append(cell.get_text(strip=True))
                    all_events.append(per_event)                
            else:
                print("Tbody not found on the page.")
        
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
        events_ids = []
        for e in all_events:
            code = e[1]
            description = e[2]
            date = e[3]
            event = e[4]
            loc = e[5]
            events_ids.append(code)
        
        base = "https://emergency.copernicus.eu/mapping/list-of-components/"
         
        link = base+code
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        return all_events[:max_events],events_ids[:max_events]



    def get_event_details(self,event_id):
        """get_event_details.
                    Retrives the Copernicus Rapid Mapping event details. 
           Parameters
           ----------
            event_id : string
                The id of Copernicus event 'EMSRxxx
           Returns
           -------
                    results : JSON
                        JSON with event details or None 
        """
        
        url = "https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations/"
        params = {
            "code": event_id  # Replace with the actual activation code you want to query
        }
        
        try:
            response = requests.get(url, params=params)
        
            if response.status_code == 200:
                # Print the JSON response
                # print(response.json())
                results = response.json()
                return results
            else:
                print(f"Request failed with status code: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None
        
    def get_events_map(self,map_name):
        """get_events_map.
                    Creates a HTML map for all Copernicus Rapid Mapping Events with their AOIs. 
           Parameters
           ----------
            map_name : string
                The name with wich you can store localy the HTML map.
           Returns
           -------
                    my_map : folium.Map
                        Folium map with Copernicus Rapid Mapping Event AOIs
                        
                    res_codes : list
                        String with event ID - Title per event, EMSRxxx - Event_Title
                        res_dets : list
                            String withdetails per event such as code, name, reason, etc
        """
        
        
        map_center = [0, 0]
        my_map = folium.Map(location=map_center, zoom_start=12)
        res_codes = []
        res_dets = []
        for e_id in self.events_ids:
            details = self.get_event_details(e_id)
            if details is None:
                print('Null details')
                continue
            if details['results'] is None:
                print("EINAI NONE RE !!!")
                continue
            res = details['results'][0]
            centroid = res['centroid'] #event centroid
            extent_coords = res['extent'].split("((")[1].split("))")[0].split(",") # the extended event area
            lat=centroid.split(" ")[1].split("(")[1]
            long = centroid.split(" ")[2].split(")")[0]
            
            
            
            stats_str=""
            extent_polygon = self.extent_coords2polygon(extent_coords)
            if res['stats']  is not None:
                
                stats_str = '<br>'.join(f"<b>{key}:</b> {value}" for key, value in res['stats'].items())
            polyline_text = "<b>"+res['code']+" - "+res['name']+ "</b><br><br>"+res['reason']+"<br><br>"+stats_str
            # polyline_text = f"<b>{res['code']} - {res['name']}</b><br>{res['reason']}<br>{stats_str}"
            poly_popup = folium.Popup(polyline_text , max_width=200)
            polygon = folium.Polygon(locations=extent_polygon, color='red', weight=2,dash_array='5, 5', fill=False,popup=poly_popup )
            # Concatenate the values into a string
            
    
            res_codes.append(res['code']+' - '+res['name'])
            res_dets.append(polyline_text)
            # print(res['code'], polyline_text)
            polygon.add_to(my_map)
            AOIS = res['aois']
            colors = [ 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
            i = 0
            for aoi in AOIS:
               
                 extent_coords = aoi['extent'].split("((")[1].split("))")[0].split(",") # the extended event area
                 aoi_polygon = self.extent_coords2polygon(extent_coords)
                 # print(colors[i])
    
                 polygon = folium.Polygon(locations=aoi_polygon, color=colors[i], fill=True, fill_opacity=0.3).add_to(my_map)
                 tooltip_text = aoi['activationCode'] +"-"+aoi['name']
                 folium.Popup(tooltip_text).add_to(polygon)
                 if i == len(colors)-2:
                     i=0
                 else:
                     i=(i+1) #% len(colors)
        
        my_map.save(map_name +".html")
        return my_map,res_codes,res_dets

    def extent_coords2polygon(self,extent_coords):

        # Coordinates for the polygon
        extent_polygon = []
        for coord in extent_coords:
            # print (coord)
            long = float(coord.strip().split(" ")[0])
            lat = float(coord.strip().split(" ")[1])
            extent_polygon.append((lat,long))
        return    extent_polygon         
        
        
