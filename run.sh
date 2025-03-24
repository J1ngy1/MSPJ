#!/bin/bash

# Start all the other dockers
docker load -i ./controller/envoy_controller_20241018.tar
docker compose up --build


# CONTAINER_NAME="imo-sidecar-networking-1-ubuntu-curl-1"
# APP_DIR_IN_CONTAINER="/root/hey-visualizer"


# if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
#     docker start $CONTAINER_NAME
# fi


# docker cp ./visualizer "$CONTAINER_NAME:$APP_DIR_IN_CONTAINER"

# docker exec -it $CONTAINER_NAME bash -c "
#     apt update &&
#     apt install -y python3 python3-pip curl git &&
#     pip3 install flask &&
#     if ! command -v hey >/dev/null; then
#         curl -LO https://github.com/rakyll/hey/releases/download/v0.1.4/hey_linux_amd64 &&
#         mv hey_linux_amd64 /usr/local/bin/hey &&
#         chmod +x /usr/local/bin/hey
#     fi
# "

# docker exec -d $CONTAINER_NAME bash -c "
#     cd $APP_DIR_IN_CONTAINER &&
#     nohup python3 app.py --host=0.0.0.0 --port=5055 > flask.log 2>&1 &
# "

# echo "http://localhost:5055"