# custom/

Things that live outside `printer_data` and are recreated by `k1max-boot.sh`
(run at every boot from `/etc/init.d/S54k1max`, before Klipper starts, and
after every update):

| File | What it does |
|---|---|
| `twist_touch.py` | Kalico plugin providing `AXIS_TWIST_TOUCH_CALIBRATE` (axis twist with the load cells); linked into `klipper/klippy/plugins/` |
| `keep_out.py` | Kalico plugin for `[keep_out]`: keeps the toolhead out of zones where the probe hits the frame (travel goes around, anything else is refused); linked into `klipper/klippy/plugins/` |
| `lidar.py` | Kalico plugin for `[lidar]`: LiDAR scans, meshes and calibrations through the driver's socket `/tmp/ai_server_uds` (`lidar-direct.py`); linked into `klipper/klippy/plugins/` |
| `lidar-start.sh` | keeps the LiDAR powered (stock `laser_status.sh` switches it off without `/tmp/load_done`), starts the open driver `lidar-direct.py` and `lidar-bridge.py` if they aren't running; `lidar-start.sh restart` stops both first (the `LIDAR_DRIVER` macro); run in the background by `k1max-boot.sh`. Creality's `cx_ai_middleware` is retired (never started; manual fallback in `LIDAR-NOTES.md`) |
| `lidar-direct.py` | the open LiDAR driver (replaces `cx_ai_middleware`, same JSON API on `/tmp/ai_server_uds`); frame stream for dwell scans, re-init after module/USB loss (restoring laser, stream, level, exposure, gain), IR camera on HTTP port 8081; log `/tmp/lidar-direct.log` |
| `lidar_serial.py` | the module's serial protocol (frames, authentication, init, commands); refuses the unsafe commands (flash writes, IR type 0, watchdog) |
| `lidar-bridge.py` | forwards the driver's socket over TCP (port 7130, only from the helper's address) for `helper/lidar_service.py`; started by `lidar-start.sh` |
| `LIDAR-NOTES.md` | what's known about the LiDAR: hardware, the socket API (middleware and open driver), the serial frame format, Creality's calibrations, and what not to run |
| `k1max-boot.sh` | recreates the plugin links and `/etc/init.d/S54k1max`, retires Pellcorp's Bed_Warp_Stabilisation, merges the crontab line into root's crontab (other entries kept), starts `crond` |
| `S54k1max` | the init script itself (copied to `/etc/init.d/`) |
| `crontab` | runs `check-updates.sh` every night at 4:00 |
| `check-updates.sh` | checks Pellcorp and Kalico for new commits and writes `UPDATES.md` to the config folder (installs nothing) |
| `update.sh` | backs up overrides (and pushes to GitHub), updates Pellcorp or Kalico, re-links, checks Klipper is `ready`; used by the `PRINTER_UPDATE_*` macros |
