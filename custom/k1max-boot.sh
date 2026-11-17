#!/bin/sh
# Recreate the K1 Max customisations that live outside printer_data.
# Runs at boot from /etc/init.d/S54k1max (before Klipper) and after updates.
#   k1max-boot.sh         links + cron
#   k1max-boot.sh links   links only
C=/usr/data/pellcorp-overrides/custom

# Kalico loads the plugins (twist_touch, keep_out, lidar) from klippy/plugins;
# a Kalico reinstall deletes the links, and Klipper will not start without them
if [ -d /usr/data/klipper/klippy/plugins ]; then
    for f in $C/*.py; do
        ln -sf $f /usr/data/klipper/klippy/plugins/$(basename $f)
    done
fi

# retire Pellcorp's time-based Bed_Warp_Stabilisation (Adaptive Glass Soak
# measures instead): rename it so Fluidd hides it, and keep it off. Pellcorp
# updates restore start_end.cfg, so this runs at every boot and after updates
SE=/usr/data/printer_data/config/start_end.cfg
if grep -q "output_pin Bed_Warp_Stabilisation" $SE 2> /dev/null; then
    sed -i 's/output_pin Bed_Warp_Stabilisation/output_pin _Bed_Warp_Stabilisation/g' $SE
fi
sed -i '/^\[output_pin _Bed_Warp_Stabilisation\]/,/^\[/ s/^value: .*/value: 0/' $SE 2> /dev/null

# the boot script itself, in case the root filesystem was reset
if [ ! -f /etc/init.d/S54k1max ] || ! cmp -s $C/S54k1max /etc/init.d/S54k1max; then
    cp $C/S54k1max /etc/init.d/S54k1max && chmod 755 /etc/init.d/S54k1max
fi

[ "$1" = "links" ] && exit 0

# nightly update check: merge our job into root's crontab (other entries are
# kept; an older version of our line is replaced); idempotent
mkdir -p /etc/crontabs
CT=/etc/crontabs/root
touch $CT
{ grep -v 'pellcorp-overrides/custom/check-updates.sh' $CT
  grep -v '^#' $C/crontab | grep .; } > $CT.new
if cmp -s $CT.new $CT; then
    rm -f $CT.new
else
    mv $CT.new $CT
    echo root >> /etc/crontabs/cron.update   # busybox crond: reload root's table
fi
pidof crond > /dev/null || crond -c /etc/crontabs

# LiDAR: keep it powered and start the open driver (lidar-direct.py) for lidar.py
$C/lidar-start.sh > /dev/null 2>&1 &
exit 0
