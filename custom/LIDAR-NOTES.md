# K1 Max LiDAR: reverse-engineering notes

What's known about Creality's K1 Max "AI LiDAR" and its software, from the
binaries on the printer (`/usr/bin/cx_ai_middleware`, `master-server`,
`lidarCalib`, `laser_ota_util`, `cx_ai_crypto`) and from testing on a K1 Max
running Simple AF. `lidar.py` and `lidar-start.sh` are built on this.

## Hardware

- USB serial device, CH343 (`1a86:55d3`), `/dev/ttyACM0`, udev symlink
  `/dev/serial/by-id/creality-laser`. Not a camera (no UVC).
- Power: GPIO **PA14** (`laser_power.sh on|off|restart`). The pin comes from
  the USB port it sits on (`laser_status.sh`).
- The stock udev hook `laser_status.sh` runs on plug-in: it checks the
  firmware (`laser_ota_util`) and **switches the LiDAR off unless
  `/tmp/load_done` exists** (the Creality stack creates it). That's why it
  looks dead under Simple AF.
- udev also runs `cx_ai_crypto` on the port (sends an "encryption key",
  SHA256).
- Firmware: `/usr/share/laser/fw/3D-CONTOUR-WQ-V1013-O.bin`, reports version
  1.0.13 and a serial number.

## Measurements

- One capture: a line profile of ~1500 points `[x, y, z]` in µm, ~29 mm wide
  (x -14.4..+14.8 mm), z = distance (~25.5 mm with the nozzle 3 mm above the
  surface).
- Working range is narrow: full coverage with the nozzle 3-5 mm above the
  surface (distance ~25-28 mm), partial at 8 mm, nothing at 10+.
- Repeatability 1-2 µm between captures; distance follows Z 1:1.
- Position on a K1 Max with glass + PEI: line centre at nozzle **X -36,
  Y -21.2**, profile x runs towards printer -X. The stock config says
  `laser_y_offset: -23.2`: the laser hits at an angle, so the spot moves in Y
  with the surface height.
- The ~200 MB of RAM on the K1 can't take big analyses next to Klipper
  (a numpy run on ~50 MB of scans stalled it: MCU "Rescheduled timer in the
  past"). Reduce data while scanning.

## cx_ai_middleware socket API

Unix socket `/tmp/ai_server_uds`. Request = JSON + `0x03` (ETX), reply the
same. Use **one persistent connection**: the middleware leaks a descriptor
per connection and stops accepting after a few thousand.

```
{"control": "set_laser_open"}                  -> {"result": {"code": 0}}
{"control": "open_flow"}                       start streaming
{"control": "set_point_cloud_level", "level": 0}   0 = all points, 1/2 = 1/2, 1/4
{"control": "get_point_cloud"}                 -> {"result": {"code": 0, "point_cloud": [[x,y,z], ...]}}
{"control": "close_flow"}, {"control": "set_laser_close"}
{"control": "get_laser_exposure"} / "set_laser_exposure" {"exposure": n}   default 1000
{"control": "get_laser_gain"} / "set_laser_gain" {"gain": n}               default 1000
```

Without `open_flow`, `get_point_cloud` returns code 4 and no points.

All commands (dispatch table in `.rodata`): `open_flow close_flow
get_point_cloud get_level_value set_point_cloud_level get_point_cloud_level
module_restart set_laser_open set_laser_close set_fill_light_open
set_fill_light_close create_ir_image get_an_ir_image get_flow_detection
get_select_line set_laser_cali_step set_laser_coor get_laser_coor
get_first_floor_detect get_laser_exposure set_laser_exposure get_laser_gain
set_laser_gain set_laser_point_cloud_mode set_laser_roi_area
set_take_over_model get_laser_offset get_laser_offset_0.2mm
get_flow_detection_new get_first_floor_detect_new`

Result codes seen: 0 ok, 4 no data, 101 LiDAR not ready, 102 the module
refused, 103 missing/invalid parameters.

**Don't use `create_ir_image`** (`type` + `resolution`, both ints): this
module refuses it (102) and then stops answering until power-cycled
(`laser_power.sh off`, `on`, restart `cx_ai_middleware`).

## Serial protocol (middleware <-> LiDAR, from LaserDrive.c)

```
AF FF | len (u16 LE, = 2 + payload) | src | cmd | payload | checksum (u16 LE)
checksum = -(sum of all bytes before it) & 0xffff
```

Replies come from src 2. Command numbers and the point-cloud payload layout
aren't documented yet (next step: strace the middleware).

## Creality's calibrations (master-server)

Two different things:

1. **Sticker calibration = the LiDAR's internal calibration** (`set_laser_cali_step`,
   passed straight to the module, which stores the result itself).
   `device_structure_config.json` → `laser_offset`:
   `cali_x_offset 7, cali_y_offset 168, cali_z_offset 1`. Sequence: G28,
   nozzle X10 Y10 Z0.2, close the stream, LiDAR light on, nozzle to
   **X7 Y168 Z1** (LiDAR over X-29 Y145, the sticker in the middle of the left
   edge) → `step 1`, nozzle to **Z1+2 = Z3** → `step 2`. It needs the sticker
   at the stock distances. **With a raised plate (glass mod) don't run it**:
   the sticker is 4-5 mm further away and the module would store wrong
   geometry.
2. **Nozzle-to-laser offset** (`get_laser_offset`): compares scan points with
   the G-code positions of printed lines (`scan_point` vs `gcode_point`).
   Same idea as `lidar.py`'s printed cross: print something known, scan it.

Other routines in master-server use the same building blocks: PA ("flow_pa"),
flow ("flow_em", PLA only), first-layer check ("scan table", then "scan
first floor"), all scan-before / scan-after.
