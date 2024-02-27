#!/bin/bash
# Add routing rules
ip route add 10.0.1.0/24 via 10.0.1.1 dev eth1
ip route add 10.0.2.0/24 via 10.0.2.1 dev eth0
