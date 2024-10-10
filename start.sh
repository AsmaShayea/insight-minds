#!/bin/sh

# Set default PORT if not provided
PORT=${PORT:-8000}

# Run the Uvicorn server
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
