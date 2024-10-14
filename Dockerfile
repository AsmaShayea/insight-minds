# Use the official Python 3.12 image as a base
FROM python:3.12-alpine

# Set a working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code into the container
COPY ./app ./app

# Copy the start script into the container
COPY ./start.sh ./  # Ensure it copies to the working directory

# Make the start script executable
RUN chmod +x start.sh  # Adjust if necessary to ensure executable

# Set the command to run the start script
CMD ["sh", "start.sh"]  # Use `sh` to execute the script
