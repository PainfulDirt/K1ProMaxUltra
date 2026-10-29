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

## Bed mesh with the LiDAR (2026-10-29)

Test on a cold, bare plate: 10 strips (laser X 18-270, 28 mm apart, Y 25-265,
1 mm rows) against a 10x11 Microprobe mesh on the same grid and 6 load-cell
nozzle touches at Y145 (data and scripts: `k1-lidar/bedmesh/`).

- Shape: after taking a plane out, LiDAR and probe agree to 17-25 um rms.
- Both carry the **X-beam twist**: the toolhead tips forward/back by an
  amount that changes along X. Probe - nozzle drifts +0.2 mm across X, LiDAR
  - nozzle -0.18 mm (probe 20 mm behind the nozzle, laser 21 mm in front).
  With a twist table from the nozzle touches (`LIDAR_TWIST_CALIBRATE`) the
  LiDAR mesh matches the twist-corrected probe mesh to 23-25 um rms. A
  +0.018 mm/100 mm slope along Y is left between the two (unknown which one;
  the twist table is measured along X only).
- The profile's own tilt is the same in every strip (-0.041 mm/mm, +-10 um
  over 26 mm between strips), so the whole line width can be used with a
  tilt table taken from the scan itself (`MODE=fine`); strips 28 mm apart
  then meet with steps of -37..+24 um (median per seam) and the off-centre
  mesh columns agree with the probe interpolated between its columns to
  20 um rms.
- One frame per grid point is as good as dense rows at the grid points
  (25 vs 23 um rms): `MODE=fast` stands at the grid points only.
- Kalico on the K1: building a ZMesh (bicubic, mesh_pps 2) takes 68 ms for
  12x12, 209 ms for 21x19, 517 ms for 30x30 (LIDAR_BED_MESH's maximum);
  `calc_z` is ~0.12 ms whatever the size. A 12x12 probe mesh takes ~12.7 min
  (5.3 s per point).

## Mesh levels, the ultimate mesh, benchmark (design, 2026-10-29, offline)

Studies: `k1-lidar/bedmesh/study_levels.py` (today's strips), `test_sim.py`
(simulated printer running the real code: motion/trapq, frame stream with
exposure windows, load cells, probe, the Pi service).

| level | how | grid | est. time | vs probe* | vs dense map | sim vs truth** |
|---|---|---|---|---|---|---|
| 1 quick | moving 150 mm/s | 7x7 | ~20 s | 24.9 um | 8.4 um | 15.4 um |
| 2 fast | moving 120 mm/s | 12x12 | ~40 s | 23 um | 7.0 um | 14.6 um |
| 3 normal | moving 60 mm/s | 20x20 | ~1.7 min | 22.9 um | 6.4 um | 13.2 um |
| 4 fine | dwell strips, STEP 2, whole line | 30x30 | ~4.8 min | 22.6 um | 5.8 um | 13.4 um |
| 5 ultimate | 4 + 5x5 nozzle touches | 30x30 | ~13 min | 14.2 um*** | - | 6.3 um |

\* rms against the twist-corrected probe mesh at its 110 points (real data):
mostly a systematic LiDAR-probe difference (a Y slope of 0.018 mm/100 mm,
~17 um after a plane), the same for every level. \** with a planted LiDAR
error (that Y slope + a 12 um bump) the twist table can't see. \*** held-out
probe points after a synthetic touch correction (probe as stand-in truth).

- Moving scans: the old moving scan (`k1-lidar/cmp/move*`, ~1.7 mm/s)
  matches a stop scan at mesh scale to 6-7 um (dwell 5.5, stop-stop 3).
  For a mesh the blur along Y only averages the texture: simulated with
  today's rows, 150 mm/s (5-16 mm blur) is as good as dwell. Frames are
  kept only for full-speed or standing windows (trapq), placed at the
  middle; the column ends stand still for a frame. A wrong exposure timing
  shows as a Y shift between directions (BOTH_WAYS=1 measures it;
  `moving_lag`); at a 1/1000 slope 50 ms at 150 mm/s is ~7 um.
- Touches (load cells): ~11 s per spot with 3 samples, ~3 um noise
  (medians). Bed heater off only around each touch (BED_OFF=1:
  SET_HEATER_TEMPERATURE 0, 0.3 s, touch, back), like the True Zero touch
  but seconds instead of minutes; the PID loses its integral each time,
  so the bed sags ~1-2 C during the touch phase. A reference touch on the
  zero reference spot at the start, every 6 spots and at the end gives a
  linear drift in time that comes off all touches.
- Correction: nozzle - LiDAR at the touches, polynomial order 0-3 by
  leave-one-out (LOO rms = the honest accuracy number reported). The touch
  grid also contains the twist (X dependence at several Y), so level 5
  doesn't need a fresh twist table; levels 1-4 do (AXIS_TWIST_TOUCH_
  CALIBRATE, LiDAR + probe from the same touches).
- Kalico: ZMesh build 68 ms (12x12) .. 517 ms (30x30) on the K1, calc_z
  ~0.12 ms any size; 30x30 is the cap.

**Data on the Pi** (`/var/lib/k1-lidar`): `meshes/mesh-<stamp>.json` (every
mesh: xs, ys, matrix rows = Y, the request incl. level/twist),
`heightmap-<stamp>.json` (levels 4/5: 0.5 mm cells from x0 x scan rows ys,
um; meta: time, extruder/bed temperature, z, step, level, twist, mesh_xs/
mesh_ys, filament, file; level 5: `correction` = order, coef, poly, LOO,
touches with residuals, drift), `benchmarks/bench-<stamp>.{json,html}`.

**Later: first-layer check** (not built). The goal is the first layer, the
mesh is a means: scan the bare print area (adaptive area) before the print
and the first layer after it, wide solid areas only (narrow lines read
badly, see Measurements), difference = thickness map on the same 0.5 mm x
row grid as the height maps. Feed back (a) a per-filament Z offset /
squish value (thickness vs the sliced layer height) and (b) a slowly
learned correction map on top of the mesh (same coordinates as the mesh
JSON). Needs START_PRINT to save the filament type (`filament_type` in
variables.cfg is read already) and the sliced first-layer height.

## First-layer check (2026-10-29, offline-tested)

Switches (Fluidd Outputs, saved in variables.cfg): `First_Layer_Check` (scan
before the print and after layer 1) and `First_Layer_Learn` (apply the
learned Z offset per filament). Both off by default.

- START_PRINT (`_SAF_START_PRINT_AFTER_BED_MESH`): after the True Zero touch,
  `_FIRST_LAYER_OFFSET` sets the learned offset, then `_LIDAR_PRINT_SCAN`
  runs `FIRST_LAYER_SCAN PHASE=before` with the nozzle at 150C: the objects
  of the file (exclude_object polygons) + 8 mm of bare plate, strips 26 mm
  apart (the line is ~28 mm wide), dwell rows 2 mm apart (1 mm when the
  area is small; up to 3 mm so one scan stays under 120 s), Z = scan_z +
  first-layer height, bed mesh off (heights in the toolhead frame).
- Layer 2 (Orca layer-change G-code: `{if layer_num == 1}_FIRST_LAYER_AFTER`):
  retract 1 mm, nozzle target -30C, lift, the same strips and rows, the Pi's
  analysis, then M109 back, over the stop position, RESTORE_GCODE_STATE
  MOVE=1, unretract. A failed scan only loses the check. One-layer prints:
  END_PRINT (`_SAF_END_PRINT_START`) scans with FINAL=1 (no reheat/return).
  Cancel and the next START_PRINT drop a pending check.
- Analysis (`fl_analyze`, on the Pi): thickness = (z_a - d_a) - (z_b - d_b)
  per 0.5 mm x row cell; a plane through the bare cells (> 3 mm outside
  every object) is the plate's drift between the scans and comes off;
  printed cells = inside an object, >= 2 mm from its outline, > 40 % of the
  sliced height, with their 4 neighbours printed too. Report: median,
  p05-p95, per object, tilt of the thickness (mesh error), drift.
- Real noise floor of a before/after pair at the same rows (PA test of
  2026-10-17, bare plate): 14 um rms per cell, p05-p95 -22..+27 um. A first
  layer has thousands of cells, so the median is limited by systematic
  errors, not this. Offline (test_first_layer.py, simulated texture and
  drift): a planted 0.230 mm layer for a 0.200 slice reads 0.2303, a tilt of
  +20 um/100 mm reads +19.3.
- Time: a 100 x 100 mm part = 5 strips x 59 rows, ~85 s per scan: ~1.5 min
  more in START_PRINT and a ~2 min pause at layer 2 (scan + reheating 30C).
- Pi files (/var/lib/k1-lidar/firstlayer/): `fl-<id>.json` (plan, result,
  thickness map in um), `fl-<id>.html`, `history.jsonl` (one line per
  check: file, filament, temps, Z offset, result), `corrmap.json`.
- Learning (a): error e = median - sliced height; with First_Layer_Learn on
  and a clean measurement (>= 100 cells, p95-p05 <= 0.15, |e| <= 0.15, bare
  rms <= 0.03), the filament's offset becomes offset_used - 0.5 e (step at
  most 0.03 mm, total within +-0.15 mm), key = filament preset name with
  spaces as _ (`fl_zoffset` in variables.cfg).
- Correction map (b), data only, not applied yet: per 10 mm cell the
  median of (thickness - print median), folded into `corrmap.json` as a
  running mean (newest 0.3). Thicker = the nozzle was too high there, so the
  mesh value there should go down by that much. To apply: LiDAR meshes in
  `_load_mesh` (matrix minus the interpolated map before set_zero_reference,
  only cells seen in >= 3 prints); probe meshes need a command after
  BED_MESH_CALIBRATE that rebuilds the active mesh the same way.

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
