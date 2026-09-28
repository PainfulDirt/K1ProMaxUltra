#!/bin/sh
# Check Pellcorp (Simple AF) and Kalico for updates. Nothing is installed:
# the result goes to UPDATES.md in the Fluidd config folder, and a message
# is shown on the printer when it is idle. Update with K1_UPDATE_PELLCORP /
# K1_UPDATE_KALICO.
OUT=/usr/data/printer_data/config/UPDATES.md
TMP=$OUT.tmp

cd /usr/data/pellcorp || exit 1
git fetch -q origin 2> /dev/null
pc_installed=$(grep installed_sha /usr/data/pellcorp.done | cut -d= -f2)
[ -n "$pc_installed" ] || pc_installed=$(git rev-parse HEAD)
pc_up=$(git rev-parse @{upstream})
pc_count=$(git rev-list --count $pc_installed..$pc_up 2> /dev/null || echo "?")
pc_log=$(git --no-pager log --no-color --date=short --format="- %ad %s" $pc_installed..$pc_up 2> /dev/null | head -40)

cd /usr/data/klipper || exit 1
kl_branch=$(git rev-parse --abbrev-ref HEAD)
git fetch -q origin 2> /dev/null
kl_up=$(git rev-parse @{upstream})
kl_count=$(git rev-list --count HEAD..$kl_up 2> /dev/null || echo "?")
kl_log=$(git --no-pager log --no-color --date=short --format="- %ad %s" HEAD..$kl_up 2> /dev/null | head -40)
kl_fw=no
git diff --name-only HEAD $kl_up -- fw/K1 2> /dev/null | grep -q . && kl_fw=yes

{
    echo "# Printer updates"
    echo
    echo "Checked $(date '+%Y-%m-%d %H:%M'). Nothing has been installed."
    echo
    echo "## Pellcorp Simple AF: $pc_count new commit(s)"
    echo
    if [ "$pc_count" != "0" ]; then
        echo "Install with the **K1_UPDATE_PELLCORP** macro (backs up your changes first)."
        echo
        echo "$pc_log"
    else
        echo "Up to date."
    fi
    echo
    echo "## Kalico ($kl_branch): $kl_count new commit(s)"
    echo
    if [ "$kl_count" != "0" ]; then
        echo "Install with the **K1_UPDATE_KALICO** macro."
        if [ "$kl_fw" = "yes" ]; then
            echo
            echo "**Includes new MCU firmware**: after the update the printer must be"
            echo "switched off and on so the boards get flashed."
        fi
        echo
        echo "$kl_log"
    else
        echo "Up to date."
    fi
} > $TMP && mv $TMP $OUT

if [ "$pc_count" != "0" ] || [ "$kl_count" != "0" ]; then
    python3 - "$pc_count" "$kl_count" <<'PY'
import json, sys, urllib.request
B = "http://127.0.0.1:7125"
try:
    st = json.load(urllib.request.urlopen(B + "/printer/objects/query?print_stats=state", timeout=10))
    if st["result"]["status"]["print_stats"]["state"] in ("printing", "paused"):
        sys.exit(0)
    msg = "Updates: Pellcorp %s, Kalico %s - see UPDATES.md" % (sys.argv[1], sys.argv[2])
    req = urllib.request.Request(B + "/printer/gcode/script",
        data=json.dumps({"script": "M117 " + msg + "\nRESPOND TYPE=command MSG='" + msg + "'"}).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)
except Exception:
    pass
PY
fi
exit 0
