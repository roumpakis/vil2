# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Ensure the entrypoint script is executable
RUN chmod +x /app/app.py

# Define environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the ML backend port
EXPOSE 5080

# Run mulclas.py when the container launches
CMD ["python", "app.py"]
