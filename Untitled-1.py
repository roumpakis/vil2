def get_overlay(event_id):
    try:
        event_details = rm.get_event_details(event_id)
        if event_details is None:
            return jsonify({'before_image': None, 'after_image': None, 'popup': None, 'bounds': None, 'reportLink': None})

        polygon_str = event_details['results'][0]['extent']
        shapely_geometry = shapely.wkt.loads(polygon_str)
        geometry = Geometry(shapely_geometry, CRS.WGS84)
        bounds = shapely_geometry.bounds

        event_time = event_details['results'][0]['eventTime']
        event_date = dt.strptime(event_time, '%Y-%m-%dT%H:%M:%S')

        # Define time intervals for before and after images
        date_before_start = event_date - timedelta(days=20)
        date_before_end = event_date - timedelta(days=1)
        time_interval_before = (date_before_start, date_before_end)

        time_interval_after = (event_date, event_date + timedelta(days=8))

        # Fetch data from Sentinel API
        data_before = sapi.get_sentinel_data(geometry, sapi.config, time_interval_before, "before_image")
        data_after = sapi.get_sentinel_data(geometry, sapi.config, time_interval_after, "after_image")

        if data_before.size > 0 and data_after.size > 0:
            image_before = np.array(data_before)
            image_after = np.array(data_after)

            image_pil_before = Image.fromarray(image_before)
            image_pil_after = Image.fromarray(image_after)

            image_filename_before = f"{event_id}_before.png"
            image_filename_after = f"{event_id}_after.png"

            image_path_before = os.path.join('static', 'overlays', image_filename_before)
            image_path_after = os.path.join('static', 'overlays', image_filename_after)

            image_pil_before.save(image_path_before, format="PNG")
            image_pil_after.save(image_path_after, format="PNG")

            report_link = event_details['results'][0].get('reportLink', '')