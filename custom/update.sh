#!/bin/sh
# Update Pellcorp or Kalico, keeping this printer's customisations:
#   1. refuse while printing
#   2. CONFIG_OVERRIDES: save your changes (and push them to GitHub)
#   3. update
#   4. restore the Kalico plugin link, check Klipper comes back
# Usage: update.sh [--bg] pellcorp|kalico
LOG=/usr/data/printer_data/logs/k1max_update.log
C=/usr/data/pellcorp-overrides/custom

if [ "$1" = "--bg" ]; then
    # detach, Klipper restarts during the update
    shift
    setsid nohup "$0" "$@" > /dev/null 2>&1 &
    echo "Update of $1 started, log: logs/k1max_update.log"
    exit 0
fi
what=${1:-pellcorp}
exec >> $LOG 2>&1
echo
echo "=== $(date '+%Y-%m-%d %H:%M:%S') update $what"

state() {
    python3 -c 'import json,urllib.request
try:
    r=json.load(urllib.request.urlopen("http://127.0.0.1:7125/printer/objects/query?print_stats=state",timeout=10))
    print(r["result"]["status"]["print_stats"]["state"])
except Exception:
    print("unknown")'
}
say() {
    python3 - "$1" <<'PY'
import json, sys, urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:7125/printer/gcode/script",
        data=json.dumps({"script": "RESPOND TYPE=command MSG='%s'" % sys.argv[1].replace("'", "")}).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)
except Exception:
    pass
PY
}

case "$(state)" in
    printing|paused) echo "printer is busy, not updating"; say "Update refused: printer is printing"; exit 1 ;;
esac

echo "--- saving overrides"
/usr/data/pellcorp/tools/config-overrides.sh || { echo "config overrides failed, not updating"; say "Update aborted: saving your changes failed, see k1max_update.log"; exit 1; }

case "$what" in
    pellcorp)
        cd /usr/data/pellcorp && git pull --ff-only || { say "Update aborted: git pull failed"; exit 1; }
        sh ./installer.sh --update
        ;;
    kalico)
        branch=$(git -C /usr/data/klipper rev-parse --abbrev-ref HEAD)
        sh /usr/data/pellcorp/installer.sh --klipper-repo kalico "$branch"
        ;;
    *) echo "unknown target $what"; exit 1 ;;
esac

$C/k1max-boot.sh links
echo "--- restarting Klipper"
/etc/init.d/S55klipper_service restart

ok=no
for i in $(seq 1 40); do
    sleep 3
    s=$(python3 -c 'import json,urllib.request
try:
    r=json.load(urllib.request.urlopen("http://127.0.0.1:7125/printer/info",timeout=5))["result"]
    print(r["state"], "|", r["state_message"].replace("\n"," ")[:300])
except Exception:
    print("down")')
    case "$s" in
        ready*) ok=yes; break ;;
        error*|shutdown*) break ;;
    esac
done
echo "klipper: $s"
$C/check-updates.sh
if [ "$ok" = "yes" ]; then
    msg="Update of $what finished, Klipper is ready"
    grep -q "power cycle" $LOG && tail -40 $LOG | grep -q "power cycle" && msg="$msg - MCU firmware pending: switch the printer off and on"
else
    msg="Update of $what finished but Klipper is NOT ready: $s - see k1max_update.log"
fi
echo "$msg"
say "$msg"
