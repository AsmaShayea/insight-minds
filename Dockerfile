# Use the official Python 3.12 image as a base
FROM python:3.12-alpine

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn

# Copy the start script into the container
COPY ./start.sh /start.sh

# Make the start script executable
RUN chmod +x /start.sh

# Copy the app code into the container
COPY ./app /app

# Set the command to run the start script
CMD ["./start.sh"]
