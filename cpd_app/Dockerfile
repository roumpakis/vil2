# Base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the required files
COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the service will run on
EXPOSE 5012

# Run the Flask service
CMD ["python", "app.py"]
