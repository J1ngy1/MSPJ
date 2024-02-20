#!/bin/bash

# Start CouchDB in the background
echo "Starting CouchDB..."
docker-entrypoint.sh couchdb &

# Wait for CouchDB to be up
echo "Waiting for CouchDB to start..."
while ! curl -s http://localhost:5984/ > /dev/null; do
  sleep 1
done
echo "CouchDB started."

# Now run your data.sh script
echo "Running data.sh script..."
./data.sh

# Keep the container running after the script finishes
wait
