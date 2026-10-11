# K1 Max LiDAR: reverse-engineering notes

What's known about Creality's K1 Max "AI LiDAR" and its software, from the
binaries on the printer (`/usr/bin/cx_ai_middleware`, `master-server`,
`lidarCalib`, `laser_ota_util`, `cx_ai_crypto`), the module's firmware, and
testing on a K1 Max running Simple AF. `lidar.py`, `lidar-start.sh` and the
open driver (`lidar_serial.py`, `lidar-direct.py`) are built on this.

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
- Laser offset self-check (`LIDAR_OFFSET_CALIBRATE`, 2026-10-07, glass +
  PEI, cross at X150 Y150): at nozzle Z3 the line centre is at nozzle
  **X -36.01, Y -21.34**; per mm of nozzle height it moves **Y -0.99**,
  X +0.035 (the laser comes in at ~45° in Y, X doesn't move). The profile
  scale is right: 20 mm arms read 20.1-20.3 mm.
- How printed lines look: a 0.6 mm line along Y (across the profile) shows
  only a small bump (~0.1-0.15 mm) next to a few empty bins (shadow); a line
  along X (crossed row by row) shows an empty row, then a jump to ~0.7 mm
  that ramps down over ~1.8 mm of Y. The laser sheet has a thickness in Y
  and the reading blends line and plate, so heights are only rough and the
  Y centre of a line along X is biased (estimated up to ~0.3 mm). Measure
  widths/areas, not peak heights.
- The profile is tilted: distance changes ~0.031 mm per mm of profile x on a
  flat plate (the LiDAR's mounting, not the bed: same in every scan).
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

## Serial protocol (host <-> LiDAR module)

From the middleware (`LaserDrive.c`, `SerialPort.c`) and the module's own
firmware (RISC-V, FreeRTOS, `3D-CONTOUR-WQ-V1013-O.bin`), checked against
recorded traffic and used by the open driver (`lidar_serial.py`,
`lidar-direct.py`).

Port `/dev/serial/by-id/creality-laser`, **1 500 000 baud**, 8N1, raw.

```
AF FF | len (u16 LE, = 2 + payload) | src | cmd | payload | checksum (u16 LE)
checksum = -(sum of all bytes before it) & 0xffff
src 01 = host, 02 = module (replies echo cmd)
```

Replies: set commands and actions answer `status` (0 = ok); getters 0x03 0x07
0x09 0x0B 0x0D 0x0F 0x16 0x18 0x55 0x59 answer the bare value; the others
answer `status + data`. Simple commands take ~8 ms.

| cmd | name (firmware) | request payload | reply |
|---|---|---|---|
| 0x01 / 0x02 | stream on / off | - | status |
| 0x03 | software version | - | 3 bytes (1.0.13) |
| 0x04 | **point cloud** | - | status + N x (x, y, z) int16 LE, µm (max 1600 points) |
| 0x05 | calibration (sticker) | step | **never** (stores geometry in the module) |
| 0x06 / 0x07 | point cloud mode set / get | mode | status / value |
| 0x08 / 0x09 | point cloud level set / get | 0 all, 1 half, 2 quarter | status / value |
| 0x0A / 0x0B | ROI set / get | x_min u16, x_max u16 (sensor columns 0..1600) | status / 4 bytes |
| 0x0C / 0x0D | stream mode set / get (stream off only) | 0/1 | status / value |
| 0x0E / 0x0F | coordinate mode set / get (init sets 1) | 1 | status / value |
| 0x10, 0x19, 0x1A | OTA firmware update | | **never** |
| 0x11 | reset | - | status |
| 0x12 | restore | - | **never** |
| 0x13 | laser on/off | 1 / 0 | status |
| 0x14 | fill light on/off | 1 / 0 | status |
| 0x15 / 0x16 | exposure set / get | u24 LE (default 1000) | status / 3 bytes |
| 0x17 / 0x18 | gain set / get | u24 LE (default 1000) | status / 3 bytes |
| 0x1B | UART config | baud index (0 1.5M, 1 2M, 2 2.5M), flow control | **saved in the module's flash**: the middleware (fixed 1.5M) can't talk to it afterwards |
| 0x1C | IR sensor temperature | - | status + 4 bytes |
| 0x1D | serial number | - | status + 12 bytes ASCII |
| 0x1E | calibration parameters | - | status + 100 bytes |
| 0x1F, 0x20 | debug print, self test | | |
| 0x21 | point cloud in 2000-byte chunks | | |
| 0x55 | status | - | error bits (0 = ok) |
| 0x56 / 0x57 | IR image capture / download | | 0x56 **never** (hangs the module) |
| 0x58 / 0x59 / 0xAB | watchdog | | |
| 0xA0 / 0xA1 | auth challenge / key | - / 32 bytes | see below |
| 0xAA | set authorised flag | | sets the flag unchecked (debug backdoor) |

Before authentication the module only answers 0x55, 0xA0, 0xA1, 0xAA.
**Authentication** (no secret): 0xA0 answers `status, 8 bytes`; negate each
byte (`-b & 0xff`); bytes 0-3 = int32 LE `value`, 4-7 = 4 alphanumeric chars
`r`; key = `SHA256(str(value) + md5_hex_lowercase(r))`, sent with 0xA1 (reply
status 0 = ok). udev runs `cx_ai_crypto` for this at every enumeration; the
open driver does it itself.

**Init** (middleware order): 0x55 (must be 0), auth, 0x03, 0x1D, 0x0E = 1.
Then laser on (0x13 1), stream on (0x01), point clouds (0x04).

**Timing**: 0x04 waits for the next captured frame: ~140 ms until the reply
starts, ~60 ms for 9 KB at 1.5 Mbaud, so **~5 frames/s is the module's
limit** (direct: 4.98/s; through the middleware ~4.3/s). The module runs on
a 28.4 ms sensor tick: back-to-back frames come every 7 ticks (199 ms) at
level 0, 6 (170 ms) at level 1, 5 (142 ms) at level 2, 4 (114 ms) when the
frame is empty. A request that comes late slips the frame by a whole tick.
ROI and exposure don't change the rate (this module refuses 0x0A, status 1).

**What a frame covers** (LIDAR_TIMING, fast Z ramps over the plate, times
taken by lidar-direct.py when the frame arrives from the module): level 0
~197..163 ms before arrival (median 178, sd 10 ms), level 1 ~163..120 ms.
Measure with fast ramps (5 mm/s): the laser hits at ~45 deg, so a Z move
also slides the line over the plate's texture, which reads as height noise
(at 0.5 mm/s it smeared the result to a ~190 ms wide window). Scans that
stand still only for that measured window still came out blurred: leave
generous still time after it (lidar.py does, up to the next row's deadline).

**Dwell scans locked to the frames** (lidar.py, direct driver): frames are
streamed back-to-back by lidar-direct.py (`prefetch`) and time-stamped in
Klipper's clock; rows are planned so the toolhead stands still for one
frame's window and moves to the next row in between: one frame per row,
0.2 s. 51 rows (Y 20 mm, 0.4 mm steps): 12-14 s, was 20-21 s; 0 rows missed
in 3 runs; matches a stop-mode scan of the same strip within the scan noise
(p05..p95 of the difference 18-31 um, two stop-mode-era scans: 26 um).

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
