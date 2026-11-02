#!/bin/sh
# Bring up the K1 Max LiDAR under Simple AF. Started in the background by
# k1max-boot.sh; safe to run again.
#
# The stock udev hook (laser_status.sh) switches the LiDAR off right after it
# enumerates unless /tmp/load_done exists, which the Creality stack would
# create. Then lidar-direct.py, the open driver, serves /tmp/ai_server_uds for
# lidar.py. Creality's cx_ai_middleware (same JSON API) is retired since
# 2026-11-01: never started here, stopped if something did; it still ships on
# the printer for a manual last resort (custom/LIDAR-NOTES.md).
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
C=$(dirname "$(readlink -f "$0")")
killall cx_ai_middleware > /dev/null 2>&1 && sleep 1
# module stream mode (variables.cfg lidar_stream_mode, LIDAR_STREAM_MODE):
# 1 = ~10.7 instead of ~5 frames/s
MODE=$(sed -n 's/^lidar_stream_mode *= *\([01]\) *$/\1/p' \
    /usr/data/printer_data/config/variables.cfg 2> /dev/null)
pgrep -f lidar-direct.py > /dev/null ||
    setsid python3 -B $C/lidar-direct.py --stream-mode ${MODE:-0} \
        --camera-port 8081 < /dev/null > /dev/null 2>&1 &
# forward the driver's socket to the helper computer that runs lidar_service.py
# (helper/): only that address may connect
LIDAR_HELPER=10.0.1.34
if ! ps | grep -v grep | grep -q lidar-bridge.py; then
    setsid python3 $C/lidar-bridge.py 7130 $LIDAR_HELPER < /dev/null > /dev/null 2>&1 &
fi
echo "lidar-start: up, driver direct" | tee /tmp/lidar-start.log
