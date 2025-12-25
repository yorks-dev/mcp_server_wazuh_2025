FROM nginx:alpine

# Install openssl for self-signed certificates
RUN apk add --no-cache openssl

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy frontend files
COPY index.html /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Generate self-signed certificate (for development)
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx-selfsigned.key \
    -out /etc/nginx/ssl/nginx-selfsigned.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=localhost"

# Create dhparam for better security
RUN openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
