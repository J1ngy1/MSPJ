#!/bin/bash

# Start all the other dockers
docker load -i ./controller/envoy_controller_20241018.tar
docker compose up --build


