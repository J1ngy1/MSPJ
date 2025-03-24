#!/bin/bash

set -e
set -o pipefail

CONTAINER_NAME="imo-sidecar-networking-1-ubuntu-curl-1"
APP_DIR_IN_CONTAINER="/root/hey-visualizer"
LOCAL_APP_DIR="./visualizer"

echo "🔍 Checking if the container exists..."
if ! docker ps -a --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    echo "❌ $CONTAINER_NAME does not exist!"
    exit 1
fi

echo "✅ Container found: $CONTAINER_NAME"

# Start the container if it's not already running
if ! docker ps --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    echo "⏯ Starting container $CONTAINER_NAME..."
    docker start "$CONTAINER_NAME"
else
    echo "✅ Container is already running."
fi

# Copy the Flask project into the container
echo "📁 Copying Flask project into the container..."
if docker cp "$LOCAL_APP_DIR" "$CONTAINER_NAME:$APP_DIR_IN_CONTAINER"; then
    echo "✅ Copy successful"
else
    echo "❌ Copy failed! Please check if the local path is $LOCAL_APP_DIR"
    exit 1
fi

# Install dependencies + hey + fix permissions
echo "🔧 Installing dependencies inside the container..."
docker exec -it "$CONTAINER_NAME" bash -c "
    set -e
    echo '📦 Updating apt...'
    apt update
    echo '📦 Installing Python, pip, wget, etc...'
    apt install -y python3 python3-pip curl git wget
    echo '🐍 Installing Flask...'
    pip3 install flask

    echo '🔨 Checking if hey is available...'
    if ! command -v hey >/dev/null; then
        echo '⬇️ Downloading hey (Linux executable)...'
        cd /tmp
        wget https://github.com/rakyll/hey/releases/download/v0.1.4/hey_linux_amd64 -O hey
        chmod +x hey
        mv hey /usr/local/bin/hey
    fi

    # Ensure hey is executable
    chmod +x /usr/local/bin/hey

    # Remove potentially conflicting ./hey file in Flask project
    rm -f $APP_DIR_IN_CONTAINER/hey

    echo '✅ hey executable check passed'
"

# Start the Flask app
echo "🚀 Starting Flask app (in container, background)..."
docker exec -d "$CONTAINER_NAME" bash -c "
    cd $APP_DIR_IN_CONTAINER &&
    echo '📂 Entering $APP_DIR_IN_CONTAINER' &&
    nohup python3 app.py --host=0.0.0.0 --port=5055 > flask.log 2>&1 &
"

echo "✅ Flask start command sent (running in background)"
echo "🌐 Please visit: http://localhost:5055 (make sure port 5055 is mapped)"
