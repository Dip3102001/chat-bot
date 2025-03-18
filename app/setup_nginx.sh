#!/bin/bash

# Variables
SERVER_NAME="localhost"  # Change this to your domain or server IP
PORT="8080"  # Change this to the port where your app is running
CONFIG_FILE="/etc/nginx/sites-available/$SERVER_NAME"

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root. Use: sudo ./setup_nginx.sh"
   exit 1
fi

echo "🚀 Setting up Nginx reverse proxy for $SERVER_NAME on port $PORT..."

# Create Nginx configuration
cat > $CONFIG_FILE <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site by creating a symlink
ln -s $CONFIG_FILE /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid. Restarting Nginx..."
    systemctl restart nginx
    echo "🎉 Setup complete! Your site is now accessible at http://$SERVER_NAME"
else
    echo "❌ Nginx configuration test failed. Please check manually."
fi

