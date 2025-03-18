#!/bin/bash

# installing dep
sudo apt update
sudo apt install pip

# creating venv
python3 -m venv venvlang
sudo chmod +x venvlang/bin/activate

source venvlang/bin/activate

# Create necessary directories
mkdir -p data
mkdir -p chroma_db

# Install required packages
pip install -r requirements.txt

#sudo apt install nginx -y

#sudo systemctl start nginx
#sudo systemctl status nginx

#sudo bash ./setup_nginx.sh
sudo ufw allow 'Nginx Full'


# Run the Flask application with Gunicorn for production deployment
# 4 worker processes, binding to port 8080
gunicorn -w 4 -b 0.0.0.0:8080 main:app &
