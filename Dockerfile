# Use the official Python 3.12 image as a base
FROM python:3.12-alpine

# Set a working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code into the container
COPY ./app ./app

# Copy the start script into the container
COPY ./start.sh ./

# Make the start script executable
RUN chmod +x start.sh

# Set the command to run the start script
CMD ["./start.sh"]
