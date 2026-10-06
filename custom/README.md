# custom/

Things that live outside `printer_data` and are recreated by `k1max-boot.sh`
(run at every boot from `/etc/init.d/S54k1max`, before Klipper starts, and
after every update):

| File | What it does |
|---|---|
| `twist_touch.py` | Kalico plugin providing `AXIS_TWIST_TOUCH_CALIBRATE` (axis twist with the load cells); linked into `klipper/klippy/plugins/` |
| `keep_out.py` | Kalico plugin for `[keep_out]`: keeps the toolhead out of zones where the probe hits the frame (travel goes around, anything else is refused); linked into `klipper/klippy/plugins/` |
| `lidar.py` | Kalico plugin for `[lidar]`: LiDAR scans through Creality's `cx_ai_middleware` and the LiDAR PA calibration; linked into `klipper/klippy/plugins/` |
| `lidar-start.sh` | keeps the LiDAR powered (stock `laser_status.sh` switches it off without `/tmp/load_done`) and starts `cx_ai_middleware`; run in the background by `k1max-boot.sh` |
| `LIDAR-NOTES.md` | what's known about the LiDAR: hardware, the middleware socket API, the serial frame format, Creality's calibrations, and what not to run |
| `k1max-boot.sh` | recreates the plugin links and `/etc/init.d/S54k1max`, retires Pellcorp's Bed_Warp_Stabilisation, installs the crontab, starts `crond` |
| `S54k1max` | the init script itself (copied to `/etc/init.d/`) |
| `crontab` | runs `check-updates.sh` every night at 4:00 |
| `check-updates.sh` | checks Pellcorp and Kalico for new commits and writes `UPDATES.md` to the config folder (installs nothing) |
| `update.sh` | backs up overrides (and pushes to GitHub), updates Pellcorp or Kalico, re-links, checks Klipper is `ready`; used by the `PRINTER_UPDATE_*` macros |
