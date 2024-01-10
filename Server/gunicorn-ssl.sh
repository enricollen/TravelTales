#!bin/sh
$CERT_PATH="../Tests/SSL/"
gunicorn -w 4 -b 0.0.0.0:5000 --certfile=${CERT_PATH}cert.pem --keyfile=${CERT_PATH}key.pem server:app  # Replace 'cert.pem' and 'key.pem' with your SSL certificate and key
