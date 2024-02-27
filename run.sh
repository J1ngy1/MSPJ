#!/bin/bash

# Start all the other dockers
docker load -i ./controller/envoy_controller_20240221.tar
docker compose up --build


