#!/bin/sh
# Install the k1-lidar service on a helper computer (Debian / DietPi /
# Raspberry Pi OS). Run from a checkout of this repo:  sh helper/install.sh
# Edit the printer address in k1-lidar.service first if it isn't 10.0.1.28.
# The service runs as root (camera photos and scans in /var/lib/k1-lidar).
set -e
R=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p /opt/k1-lidar /var/lib/k1-lidar
# the service, the camera/PA/flow modules it imports and the shared analysis
cp "$R/custom/lidar.py" "$R"/helper/lidar_*.py /opt/k1-lidar/
for m in lidar.py lidar_service.py lidar_camera.py lidar_pa_flow.py lidar_bands.py; do
    [ -f "/opt/k1-lidar/$m" ] || { echo "missing /opt/k1-lidar/$m"; exit 1; }
done
ls /opt/k1-lidar
# numpy + PIL: the camera calibrations, PA and flow analysis
if ! python3 -c "import numpy, PIL" 2>/dev/null; then
    echo "installing python3-numpy python3-pil"
    if ! { apt-get update && apt-get install -y python3-numpy python3-pil; }; then
        echo "WARNING: could not install numpy/PIL (offline?): LiDAR scans and"
        echo "meshes work, the camera/PA/flow calibrations answer an error until"
        echo "'apt-get install python3-numpy python3-pil' succeeds"
    fi
fi
python3 -c "import numpy, PIL; print('numpy', numpy.__version__, 'PIL', PIL.__version__)" || true
cp "$R/helper/k1-lidar.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable k1-lidar
systemctl restart k1-lidar
systemctl --no-pager status k1-lidar | head -5
