#!/bin/bash

# Start all the other dockers
docker load -i ./controller/envoy_controller_20240114.tar
docker compose up >& ./docker-compose.log


