#!/bin/bash

# Create necessary directories
mkdir -p data
mkdir -p chroma_db

# Install required packages
pip install -r requirements.txt

# Run the Flask application with Gunicorn for production deployment
# 4 worker processes, binding to port 5000
gunicorn -w 4 -b 0.0.0.0:80 main:app