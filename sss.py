# Given data
data_transferred_gb = 529.12  # in GB
time_minutes = 27*60  # in minutes

# Convert GB to bytes and minutes to seconds
data_transferred_bytes = data_transferred_gb * (1024 ** 3)  # 1 GB = 1024^3 bytes
time_seconds = time_minutes * 60  # 1 minute = 60 seconds

# Calculate download speed in bytes per second
download_speed_bps = data_transferred_bytes / time_seconds

# Convert download speed to megabits per second (Mbps)
download_speed_mbps = (download_speed_bps * 8) / (1024 ** 2)  # 1 byte = 8 bits, 1 MB = 1024^2 bytes

print(download_speed_bps, download_speed_mbps)
