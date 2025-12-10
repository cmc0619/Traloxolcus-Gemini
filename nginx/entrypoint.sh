#!/bin/sh

# Ensure SSL directory exists
mkdir -p /etc/nginx/ssl/live

# Generate Self-Signed Cert if missing
if [ ! -f /etc/nginx/ssl/live/selfsigned.crt ]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/live/selfsigned.key \
        -out /etc/nginx/ssl/live/selfsigned.crt \
        -subj "/CN=localhost"
fi

# Execute CMD (nginx)
exec "$@"
