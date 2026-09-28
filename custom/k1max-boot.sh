#!/bin/sh
# Recreate the K1 Max customisations that live outside printer_data.
# Runs at boot from /etc/init.d/S54k1max (before Klipper) and after updates.
#   k1max-boot.sh         links + cron
#   k1max-boot.sh links   links only
C=/usr/data/pellcorp-overrides/custom

# Kalico loads mesh_edge_extend from klippy/plugins; a Kalico reinstall
# deletes the link, and Klipper will not start without it
if [ -d /usr/data/klipper/klippy/plugins ]; then
    ln -sf $C/mesh_edge_extend.py /usr/data/klipper/klippy/plugins/mesh_edge_extend.py
fi

# the boot script itself, in case the root filesystem was reset
if [ ! -f /etc/init.d/S54k1max ] || ! cmp -s $C/S54k1max /etc/init.d/S54k1max; then
    cp $C/S54k1max /etc/init.d/S54k1max && chmod 755 /etc/init.d/S54k1max
fi

[ "$1" = "links" ] && exit 0

# nightly update check
mkdir -p /etc/crontabs
cp $C/crontab /etc/crontabs/root
pidof crond > /dev/null || crond -c /etc/crontabs
exit 0
