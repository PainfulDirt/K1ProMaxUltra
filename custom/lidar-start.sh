#!/bin/sh
# Bring up the K1 Max LiDAR under Simple AF. Started in the background by
# k1max-boot.sh; safe to run again (starts what isn't running).
#   lidar-start.sh           start the driver and the bridge if not running
#   lidar-start.sh restart   stop both first (LIDAR_DRIVER), then start them
# With `service: 127.0.0.1:<port>` (or localhost) in tuning.cfg's [lidar]
# section, lidar_service.py (helper/, the Pi's analysis service) also runs
# here, niced, talking to the driver's socket directly (no Pi needed);
# restart stops it too (and starts it again only in that mode).
#
# The stock udev hook (laser_status.sh) switches the LiDAR off right after it
# enumerates unless /tmp/load_done exists, which the Creality stack would
# create. Then lidar-direct.py, the open driver, serves /tmp/ai_server_uds for
# lidar.py. Creality's cx_ai_middleware (same JSON API) is retired since
# 2026-11-01: never started here, stopped if something did; it still ships on
# the printer for a manual last resort (custom/LIDAR-NOTES.md).

# PIDs of the python processes running script $1. pgrep -f also matches a
# shell whose command line merely contains the name (an SSH command, this
# script's caller): only python processes count, never this shell or its
# parent.
pids_of() {
    for p in $(pgrep -f "$1"); do
        [ "$p" = "$$" ] || [ "$p" = "$PPID" ] && continue
        tr '\000' ' ' < /proc/$p/cmdline 2> /dev/null | grep -q "python[^ ]* .*$1" &&
            echo $p
    done
}
# stop: SIGTERM, wait up to 5 s, then SIGKILL
stop() {
    P=$(pids_of "$1")
    [ -n "$P" ] || return 0
    kill $P 2> /dev/null
    n=0
    while [ -n "$(pids_of "$1")" ] && [ $n -lt 5 ]; do
        sleep 1; n=$((n + 1))
    done
    P=$(pids_of "$1")
    [ -n "$P" ] && kill -9 $P 2> /dev/null
    echo "lidar-start: stopped $1"
}
if [ "$1" = "restart" ]; then
    stop lidar-direct.py
    stop lidar-bridge.py
    stop lidar_service.py
fi
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
if [ -z "$(pids_of lidar-direct.py)" ]; then
    setsid python3 -B $C/lidar-direct.py --stream-mode ${MODE:-0} \
        --camera-port 8081 < /dev/null > /dev/null 2>&1 &
fi
# forward the driver's socket to the helper computer that runs lidar_service.py
# (helper/): only that address may connect
LIDAR_HELPER=10.0.1.34
if [ -z "$(pids_of lidar-bridge.py)" ]; then
    setsid python3 $C/lidar-bridge.py 7130 $LIDAR_HELPER < /dev/null > /dev/null 2>&1 &
fi
# the analysis service on this printer: [lidar] service: 127.0.0.1:<port>
SVC=$(awk '/^\[lidar\]/ { s = 1; next } /^\[/ { s = 0 }
    s && /^service[ \t]*[:=]/ { sub(/^service[ \t]*[:=][ \t]*/, "");
        sub(/[ \t#;].*/, ""); print; exit }' \
    /usr/data/printer_data/config/tuning.cfg 2> /dev/null)
case $SVC in
    127.0.0.1:*|localhost:*)
        H=$(readlink -f "$C/../helper")
        if [ -z "$(pids_of lidar_service.py)" ]; then
            PYTHONPATH=$C setsid nice -n 19 python3 -B $H/lidar_service.py \
                --printer unix:/tmp/ai_server_uds --listen 127.0.0.1:${SVC##*:} \
                --allow 127.0.0.1 --data /usr/data/printer_data/lidar \
                --profile k1 < /dev/null \
                > /usr/data/printer_data/logs/lidar-service.log 2>&1 &
        fi
        echo "lidar-start: up, driver direct, service local" |
            tee /tmp/lidar-start.log ;;
    *)
        echo "lidar-start: up, driver direct" | tee /tmp/lidar-start.log ;;
esac
