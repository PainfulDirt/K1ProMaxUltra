#!/bin/sh
# Install the k1-lidar service on a helper computer (Debian / DietPi /
# Raspberry Pi OS). Run from a checkout of this repo:  sh helper/install.sh
# Edit the printer address in k1-lidar.service first if it isn't 10.0.1.129.
set -e
R=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p /opt/k1-lidar /var/lib/k1-lidar
cp "$R/custom/lidar.py" "$R/helper/lidar_service.py" /opt/k1-lidar/
cp "$R/helper/k1-lidar.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now k1-lidar
systemctl --no-pager status k1-lidar | head -5
