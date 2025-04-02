import requests
import json

# Ορισμός του CLIENT_ID και CLIENT_SECRET
CLIENT_ID = "sh-f7cc8302-169d-4001-8f42-0073e0e134f7"
CLIENT_SECRET = "2QEneiG3a60JwXSLTZFyHxBYf48nmKF2"

# Ορισμός του token URL
token_url = "https://sh.dataspace.copernicus.eu/oauth/token"

# Ορισμός των δεδομένων για το αίτημα (grant_type = client_credentials)
data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

# Στέλνουμε το αίτημα για να πάρουμε το token
response = requests.post(token_url, data=data)

if response.status_code == 200:
    access_token = response.json().get("access_token")
    print("Access Token:", access_token)

    # Δεδομένα για το αίτημα εικόνας (BBox και ημερομηνίες)
    bbox = [10.590758, 43.667884, 11.936196, 44.301472]
    date_start = '2025-03-14T00:00:00Z'
    date_end = '2025-03-29T00:00:00Z'
    width = 1024
    height = 1024

    # URL για το API request για λήψη των εικόνων
    download_url = "https://sh.dataspace.copernicus.eu/api/v1/process"

    # Headers που περιέχουν το token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Στοιχεία του request για λήψη εικόνας (με τις επιθυμητές μπάντες)
    evalscript = """
    //VERSION=3
    function setup() {
        return { input: ["B03", "B08", "B11"], output: { bands: 3, sampleType: "FLOAT32" } };
    }
    function evaluatePixel(sample) {
        return [sample.B03, sample.B08, sample.B11];
    }
    """
    
    payload = {
        "input": {
            "bounds": {
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                "bbox": bbox,
            },
            "data": [
                {
                    "type": "sentinel-2-l1c",
                    "dataFilter": {
                        "timeRange": {"from": date_start, "to": date_end},
                        "maxCloudCoverage": 30  # Αν θέλεις να περιορίσεις την κάλυψη σύννεφων
                    }
                }
            ],
        },
        "output": {"width": width, "height": height},
        "evalscript": evalscript,
    }

    # Στέλνουμε το αίτημα για να κατεβάσουμε τα δεδομένα
    download_response = requests.post(download_url, headers=headers, data=json.dumps(payload))

    if download_response.status_code == 200:
        print("Εικόνες κατέβηκαν επιτυχώς.")
        # Αποθήκευση των δεδομένων (ή άλλες ενέργειες)
        with open("sentinel_data.zip", "wb") as f:
            f.write(download_response.content)
        print("Τα δεδομένα αποθηκεύτηκαν στο sentinel_data.zip.")
    else:
        print(f"Αποτυχία στο αίτημα για λήψη εικόνας. Κωδικός Σφάλματος: {download_response.status_code}")
        print(download_response.text)

else:
    print(f"Αποτυχία στην απόκτηση του token. Κωδικός Σφάλματος: {response.status_code}")
    print(response.text)
