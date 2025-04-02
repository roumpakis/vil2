<<<<<<< HEAD
import os
import json

def create_3d_map_by_aoi(json_files_by_aoi, all_images_bounds, s2_image, cesium_token, output_dir="maps"):
    os.makedirs(output_dir, exist_ok=True)
    aoi_num = 0

    for aoi, json_files in json_files_by_aoi.items():
        cesium_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cesium 3D Map - {aoi}</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.106/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.106/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        #cesiumContainer {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <script>
        Cesium.Ion.defaultAccessToken = '{cesium_token}';
        
        const viewer = new Cesium.Viewer('cesiumContainer', {{
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false
        }});

        viewer.scene.globe.enableLighting = true;

        // Load GeoJSON Layers
        {geojson_layers}

        // Add Sentinel-2 Image Overlay
        viewer.entities.add({{
            name: "Sentinel-2 Image",
            rectangle: {{
                coordinates: Cesium.Rectangle.fromDegrees({bounds}),
                material: new Cesium.ImageMaterialProperty({{
                    image: "{s2_image}"
                }})
            }}
        }});

        viewer.flyTo(viewer.entities);
    </script>
</body>
</html>"""

        geojson_layers = ""

        # Add GeoJSON layers to the map
        for json_file in json_files:
            with open(json_file, 'r', encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "features" not in data or not isinstance(data["features"], list):
                print(f"❌ Skipping {json_file}: Invalid JSON structure!")
                continue
            
            features = data["features"]
            if not features:
                print(f"❌ Skipping {json_file}: Empty 'features' list!")
                continue

            geojson_layers += f"""
                Cesium.GeoJsonDataSource.load({json.dumps(data)}).then(function(dataSource) {{
                    viewer.dataSources.add(dataSource);
                }});
            """

        # Get bounding box for AOI
        if aoi_num >= len(all_images_bounds):
            print(f"⚠️ Skipping AOI {aoi}: Missing bounds!")
            continue

        bounds = all_images_bounds[aoi_num]
        bounds_str = f"{bounds[0]}, {bounds[1]}, {bounds[2]}, {bounds[3]}"

        # Create HTML for the 3D map
        html_content = cesium_template.format(
            aoi=aoi,
            geojson_layers=geojson_layers,
            bounds=bounds_str,
            s2_image=s2_image[aoi_num],
            cesium_token=cesium_token
        )

        # Save the map as HTML
        output_file = os.path.join(output_dir, f"{aoi}_3d_map.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ 3D Map saved as '{output_file}'")

        aoi_num += 1

# Example Usage
json_files_by_aoi = {
    "AOI1": ["path_to_aoi1_geojson_1.json", "path_to_aoi1_geojson_2.json"],
    "AOI2": ["path_to_aoi2_geojson_1.json"]
}
all_images_bounds = [
    [-10, 35, 5, 45],  # Bounding box for AOI1
    [0, 30, 10, 40]    # Bounding box for AOI2
]
s2_image = [
    "path_to_aoi1_sentinel2_image.png",  # Sentinel-2 image for AOI1
    "path_to_aoi2_sentinel2_image.png"   # Sentinel-2 image for AOI2
]
cesium_token = "your-cesium-ion-token-here"  # Make sure to insert your token here

create_3d_map_by_aoi(json_files_by_aoi, all_images_bounds, s2_image, cesium_token)

# Example usage
bounds = [-10, 35, 5, 45]  # Example bounding box in [west, south, east, north] format
=======
import os
import json

def create_3d_map_by_aoi(json_files_by_aoi, all_images_bounds, s2_image, cesium_token, output_dir="maps"):
    os.makedirs(output_dir, exist_ok=True)
    aoi_num = 0

    for aoi, json_files in json_files_by_aoi.items():
        cesium_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cesium 3D Map - {aoi}</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.106/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.106/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        #cesiumContainer {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <script>
        Cesium.Ion.defaultAccessToken = '{cesium_token}';
        
        const viewer = new Cesium.Viewer('cesiumContainer', {{
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false
        }});

        viewer.scene.globe.enableLighting = true;

        // Load GeoJSON Layers
        {geojson_layers}

        // Add Sentinel-2 Image Overlay
        viewer.entities.add({{
            name: "Sentinel-2 Image",
            rectangle: {{
                coordinates: Cesium.Rectangle.fromDegrees({bounds}),
                material: new Cesium.ImageMaterialProperty({{
                    image: "{s2_image}"
                }})
            }}
        }});

        viewer.flyTo(viewer.entities);
    </script>
</body>
</html>"""

        geojson_layers = ""

        # Add GeoJSON layers to the map
        for json_file in json_files:
            with open(json_file, 'r', encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "features" not in data or not isinstance(data["features"], list):
                print(f"❌ Skipping {json_file}: Invalid JSON structure!")
                continue
            
            features = data["features"]
            if not features:
                print(f"❌ Skipping {json_file}: Empty 'features' list!")
                continue

            geojson_layers += f"""
                Cesium.GeoJsonDataSource.load({json.dumps(data)}).then(function(dataSource) {{
                    viewer.dataSources.add(dataSource);
                }});
            """

        # Get bounding box for AOI
        if aoi_num >= len(all_images_bounds):
            print(f"⚠️ Skipping AOI {aoi}: Missing bounds!")
            continue

        bounds = all_images_bounds[aoi_num]
        bounds_str = f"{bounds[0]}, {bounds[1]}, {bounds[2]}, {bounds[3]}"

        # Create HTML for the 3D map
        html_content = cesium_template.format(
            aoi=aoi,
            geojson_layers=geojson_layers,
            bounds=bounds_str,
            s2_image=s2_image[aoi_num],
            cesium_token=cesium_token
        )

        # Save the map as HTML
        output_file = os.path.join(output_dir, f"{aoi}_3d_map.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ 3D Map saved as '{output_file}'")

        aoi_num += 1

# Example Usage
json_files_by_aoi = {
    "AOI1": ["path_to_aoi1_geojson_1.json", "path_to_aoi1_geojson_2.json"],
    "AOI2": ["path_to_aoi2_geojson_1.json"]
}
all_images_bounds = [
    [-10, 35, 5, 45],  # Bounding box for AOI1
    [0, 30, 10, 40]    # Bounding box for AOI2
]
s2_image = [
    "path_to_aoi1_sentinel2_image.png",  # Sentinel-2 image for AOI1
    "path_to_aoi2_sentinel2_image.png"   # Sentinel-2 image for AOI2
]
cesium_token = "your-cesium-ion-token-here"  # Make sure to insert your token here

create_3d_map_by_aoi(json_files_by_aoi, all_images_bounds, s2_image, cesium_token)

# Example usage
bounds = [-10, 35, 5, 45]  # Example bounding box in [west, south, east, north] format
>>>>>>> ae00c6b6489c43778d4b099d33fc6fc3ce22fb20
