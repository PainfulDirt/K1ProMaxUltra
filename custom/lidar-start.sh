#!/bin/sh
# Bring up the K1 Max LiDAR under Simple AF. Started in the background by
# k1max-boot.sh.
#
# The stock udev hook (laser_status.sh) switches the LiDAR off right after it
# enumerates unless /tmp/load_done exists, which the Creality stack would
# create. Then Creality's cx_ai_middleware, which still ships on the printer,
# drives it and serves /tmp/ai_server_uds for lidar.py.
touch /tmp/load_done
[ -x /usr/bin/laser_power.sh ] || exit 0
# fails harmlessly before the first enumeration (no laser_info.json yet); the
# LiDAR is powered at boot anyway and load_done now keeps it on
laser_power.sh on > /dev/null 2>&1
i=0
while [ ! -e /dev/serial/by-id/creality-laser ] && [ $i -lt 30 ]; do
    sleep 1; i=$((i + 1))
done
if [ ! -e /dev/serial/by-id/creality-laser ]; then
    echo "lidar-start: no LiDAR found" > /tmp/lidar-start.log
    exit 0
fi
sleep 2
pidof cx_ai_middleware > /dev/null || cx_ai_middleware > /dev/null 2>&1 &
echo "lidar-start: up" > /tmp/lidar-start.log
