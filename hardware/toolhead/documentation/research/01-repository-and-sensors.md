# 01 · Repository & sensor research (Agent 1)

Date: 2026-10-30. Scope: the facts a custom K1 Max toolhead needs from the printer repo, FreeTheBeam, Pellcorp Simple AF, and the BIQU MicroProbe V2 docs.

**Conventions.** Origin is the nozzle tip. +X is printer right, +Y is toward the printer rear (the Microprobe at +20.3 sits behind the nozzle), +Z is up. Units are mm.

**Labels.**
- **VERIFIED**: comes from a source given as file:line or URL.
- **MEASURED-BY-USER**: a value the user measured on this printer, as recorded in the repo.
- **ESTIMATED**: derived, inferred, or taken from a web search summary whose primary page could not be fetched. The reasoning is given each time.

Short source names used below:
- `R:` is `/home/user/K1ProMaxUltra`.
- `FTB:` is `/home/user/painfuldirt/freethebeam`.
- `PC:` is a clone of github.com/pellcorp/creality (main @465ee76, 2026-10-28).
- `PCW:` is a clone of github.com/pellcorp/creality-wiki.
- `BTT:` is a clone of github.com/bigtreetech/MicroProbe (@5937988, 2024-03-30).
- `KAL:` is a sparse clone of github.com/KalicoCrew/kalico.
- `CRA:` is a clone of github.com/CrealityOfficial/K1_Series_Annex.

Reference files I downloaded are in `/tmp/claude-0/-home-user-K1ProMaxUltra/1fc00b30-b973-54a8-8106-390cde6c1256/scratchpad/ref/sensors/` (see §G).

---

## 0. Decision-relevant headlines

1. **Moving the LiDAR or probe is mostly a software re-calibration, but several mount-dependent numbers are hard-coded.**
   - The LiDAR offset, its per-Z slopes, the twist table and the probe offset are all re-measurable with existing macros.
   - Hard-coded in `custom/lidar.py`: the mesh reach `MESH_X=(5,270)`, `MESH_Y=(5,265)` and fine-mesh X 4–284 (R:custom/lidar.py:2309-2312, 2405); strip width 28 and spacing 26 (lines 906, 1134); the twist `Y=145` default.
   - Also mount-dependent: the keep-out zones, the nozzle-wipe strip, the screws-tilt points and the Orca bed shapes. All of these must be changed by hand.
   - `LIDAR_OFFSET_CALIBRATE` **refuses any result more than 5 mm from the current offset** (R:custom/lidar.py:3879-3881). Before a LiDAR move, seed the new approximate offsets first.
2. **The LiDAR line must stay parallel to printer X.** The software models only:
   - a sign flip (`x_dir: ±1`),
   - a linear XY drift with Z (`x_per_z`, `y_per_z`),
   - a constant profile tilt (measured from the data itself).

   There is no yaw or 90° rotation support. All scan planning assumes strips along Y and a profile across X.
3. **The working distance is fixed by mount height.**
   - The module reads about 22.60 mm with the nozzle on the bed (R:variables.cfg:13) and about 25.5 mm at nozzle Z3 (R:custom/LIDAR-NOTES.md:27-28).
   - Full coverage is at about 25–28 mm (nozzle Z 3–5), partial at nozzle Z8, nothing at Z ≥ 10.
   - A new mount must hold the module's distance origin at about 22.6 mm above the nozzle tip, or `scan_z`/`offset_z` must change.
4. **The toolhead pitches (nose up/down, about the X axis) as it travels along X.** The data comes from the axis-twist tables:
   - Probe 20.3 mm behind the nozzle: probe − nozzle varies 0.267 mm across X (R:printer.cfg.save_config:54).
   - LiDAR 21.3 mm in front: −0.181 mm (R:variables.cfg:8).
   - Old probe mount (33 mm left, Y 0): only 0.070 mm (git c74fe8b).
   - **Every mm of Y offset of a sensor from the nozzle adds roughly 9–13 µm of X-dependent error.** This is ESTIMATED, see §B.6. It is compensated, but only along X at one calibration Y.
5. **Mass budget.** The current shapers give Klipper-projected max accel of **X 4408 mm/s² (3hump_ei 77.6 Hz)** and **Y 5036 (ei 52 Hz)**. These come from my reimplementation of the Kalico formula; the X value matches the README's "~4400". A single-mode estimate: +20 % moving mass on X gives about 70.8 Hz and about 3670 mm/s² (§D).
6. **The MicroProbe V2 is a 2× Ø2.7 mm (M2.5) hole pair, 17 mm apart**, on a 21.93 × 15.60 mm flange.
   - The drawing gives the heights: flange top to extended tip is 28.10 mm.
   - The repo's z_offset of 0.831 puts the mount flange top about 26.8 mm above the nozzle tip (ESTIMATED, §B.4).
7. **Fans are pinned on the nozzle MCU.**
   - Part fan: `!nozzle_mcu:PB8` (PWM, 10 ms), enable PB6, tach PB3 (commented out).
   - Heatbreak fan: `nozzle_mcu:PB5`, on/off above 40 °C, tach PB4.
   - The aux (side) and chamber fans are on the main MCU, not the toolhead.
   - MPC data says the part fan at 100 % raises hotend heat loss by **46 %**, and the effect saturates above about 66 % fan (§C.3).

---

## A. LiDAR (Creality K1 Max "AI LiDAR")

### A.1 Hardware and interface

| Item | Value | Label / source |
|---|---|---|
| Interface | USB CDC serial, CH343 bridge `1a86:55d3`, `/dev/ttyACM0` → `/dev/serial/by-id/creality-laser`, 1 500 000 baud 8N1 | VERIFIED R:custom/LIDAR-NOTES.md:10-12, 89; FTB:docs/pinout.md |
| Not a camera device | no UVC; all data is over serial | VERIFIED FTB:docs/pinout.md |
| Power switching | main-board GPIO **PA14** via `laser_power.sh` | VERIFIED R:custom/LIDAR-NOTES.md:13 |
| Cable on K1 Max | a separate USB cable from the main board to the toolhead. It plugs into the "AI LiDAR extension line port" on the nozzle MCU board (K1-NOZZLE-M_V12) as a pass-through. Port pins: GND, D+, D−, GND, 5V | VERIFIED PCW:docs/beacon_wiring.md:7; image `nozzle_lidar_usb_port_wiring.png`; CRA:"pin out/Nozzle-board-A-en.JPEG" |
| Side of the toolhead | LiDAR is on the **left** side of the printhead ("left (LIDAR) side") | VERIFIED PCW:docs/microprobe_wiring.md:18 |
| Firmware | `3D-CONTOUR-WQ-V1013-O.bin`, v1.0.13, RISC-V FreeRTOS | VERIFIED R:custom/LIDAR-NOTES.md:19-20, 87 |
| Mechanical fixing | 2 screws, removed with a **2.0 mm hex key**; alignment posts on top of the module go into holes in the bracket | ESTIMATED: web search summary of Micro Swiss FlowTech K1 instructions and the DREMC hotend-replacement guide. Primary PDF blocked (cdn.shopify.com not allowed). A 2.0 mm key suggests M2.5 socket-head screws (ESTIMATED). |
| Kit mass | Creality "LiDAR Sensor Kit" 71 g, including cable and mounting accessories | ESTIMATED: search summary of the galaxus.ch/digitec.ch listing. The module's own mass is not known. |
| **Module outline, hole pattern, window positions** | **Not found** in the repo, FreeTheBeam, Pellcorp, Creality GitHub or the web | Must come from the user (§F) |

### A.2 Measured optical geometry (nozzle frame)

| Quantity | Value | Label / source |
|---|---|---|
| Line centre at nozzle Z = 3 (current) | X **−36.013**, Y **−21.336** | MEASURED-BY-USER R:variables.cfg:9,11 (`LIDAR_OFFSET_CALIBRATE`, 2026-10-07, glass+PEI) |
| Line drift with nozzle height | dX/dZ **+0.0354**, dY/dZ **−0.986** per mm | MEASURED-BY-USER R:variables.cfg:10,12 |
| `[lidar]` config fallback | x_offset −36, y_offset −21.2, x_dir −1 | VERIFIED R:tuning.cfg:927-930 |
| Creality stock value | `laser_y_offset −23.2`; sticker routine assumes LiDAR = nozzle + (−36, −23) | VERIFIED R:custom/LIDAR-NOTES.md:48-49, 316-319 |
| Stock −23.2 vs measured | equals the measured line at nozzle Z ≈ 4.9 mm. Either Creality specified a different working height, or the glass raised the plate | ESTIMATED: (−23.2 + 21.336)/(−0.986) + 3 |
| Laser sheet incidence | **≈44.6° from vertical in the Y–Z plane**. The sheet slopes toward −Y (front) going down, so the emitter is behind (+Y of) the line, nearer the nozzle | ESTIMATED: atan(0.986). The repo states "~45° in Y" (R:custom/LIDAR-NOTES.md:35) |
| Sheet tilt in X | ≈2.0° (0.035 mm/mm) | ESTIMATED: atan(0.0354) |
| Line length and orientation | ~29 mm, profile x −14.4…+14.8 mm, ~1500 points, line along printer X. Profile +x points to printer −X (`x_dir −1`) | VERIFIED R:custom/LIDAR-NOTES.md:25-26, 46-47; R:tuning.cfg:930 |
| Printer-X span of the line at Z3 | X ≈ −21.6 … −50.8 (nozzle frame) | ESTIMATED: −36 ∓ 14.4/14.8 with x_dir −1 |
| Sheet thickness in Y | non-zero. A 0.6 mm line along X reads as an empty row, then a ~0.7 mm jump ramping over ~1.8 mm of Y. Y bias up to ~0.3 mm | VERIFIED R:custom/LIDAR-NOTES.md:37-43 |
| Shadowing | lines along Y show a bump plus a few empty bins (shadow); lines along X are shadowed in Y (see above). Use widths and areas, not peaks | VERIFIED R:custom/LIDAR-NOTES.md:37-43 |
| Profile tilt (flat plate) | ~0.031 mm/mm (early note); **−0.041 mm/mm ±10 µm** across strips (2026-10-29). About 1.2 mm over the line. The repo attributes it to the mounting | MEASURED-BY-USER R:custom/LIDAR-NOTES.md:44-45, 187-189; R:custom/lidar.py:1255-1258 |
| Implied mount roll about Y | ≈2.3° | ESTIMATED: atan(0.041), assuming tilt = roll |
| Working distance | full coverage at nozzle Z 3–5 (distance ~25–28 mm), partial at Z8, nothing at Z ≥ 10 | VERIFIED R:custom/LIDAR-NOTES.md:29-30 |
| Distance with nozzle on the bed | **22.599 mm** (bed 69.8 °C, nozzle 150 °C) | MEASURED-BY-USER R:variables.cfg:13. Meaning from R:custom/twist_touch.py:209-210 |
| Distance at nozzle Z3 | ~25.5 mm; distance follows Z 1:1 | VERIFIED R:custom/LIDAR-NOTES.md:27-28, 31 |
| Module distance origin | ≈ 22.6 mm above the nozzle-tip plane. This is the module's internal z = 0, not necessarily its window | ESTIMATED from the two rows above |
| Lower working limit | untested below about 22.6 mm (it still reads at nozzle Z0) | ESTIMATED |
| Repeatability | 1–2 µm between captures; dwell vs stop scans 18–31 µm p05–p95 (texture) | VERIFIED R:custom/LIDAR-NOTES.md:31, 157-160 |
| Frame rate and latency | ≤ 4.98 frames/s (direct driver); frame data is ~163–197 ms old on arrival | VERIFIED R:custom/LIDAR-NOTES.md:126-139 |
| Twist seen by the LiDAR | `lidar_twist.comp` +0.0805 → −0.1007 mm over laser X 10–270 at Y 153, Z 3 | MEASURED-BY-USER R:variables.cfg:8 |

### A.3 What controls each characteristic

| Characteristic | Fixed by mount geometry | Handled in software (where) | In module firmware |
|---|---|---|---|
| XY position of the line relative to the nozzle | yes | `[lidar] x_offset/y_offset` (R:tuning.cfg:928-929), overridden by `lidar_x_offset`/`lidar_y_offset` in variables.cfg when all four vars exist (R:custom/lidar.py:1680-1692) | no |
| Drift of the line with Z (incidence angle) | yes (sheet angle) | `x_per_z`, `y_per_z`, `offset_z` (default 3) (R:custom/lidar.py:1609-1611, 1695-1699) | no |
| Working distance / standoff | **yes** (mount height) | `scan_z` (default 3) and `offset_z`; every scan is at Z = scan_z (+ layer height) | intrinsic range fixed in the module |
| Line orientation (along X, direction) | **yes** | only the sign `x_dir`. **Yaw and 90° are not modelled** | no |
| Profile tilt (roll) | yes | measured from each scan: `profile_tilt()` / `MODE=fine` tilt table (R:custom/lidar.py:775-789, 1255); centre-only use ±3 mm ignores it (R:custom/lidar.py:445-450) | no |
| Shadowing and sheet thickness | yes (optics) | bare-plate subtraction; measure areas, not peaks | no |
| X-beam twist seen by the LiDAR | lever arm = mount Y offset | `lidar_twist` from `LIDAR_TWIST_CALIBRATION` / `AXIS_TWIST_TOUCH_CALIBRATE` (R:custom/twist_touch.py:128-147) | no |
| Pixel → metric (µm) conversion | n/a | n/a | **yes**: the module outputs calibrated x, y, z in µm. Command 0x1E returns 100 bytes of "calibration parameters". Command 0x05 (sticker calibration) **stores geometry in the module** (R:custom/LIDAR-NOTES.md:96, 115; FTB:docs/protocol.md:9-12) |
| Exposure / gain | n/a | socket `set_laser_exposure/gain` (default 1000) | yes |

**Does moving it require Creality's sticker calibration? No.** Running it is actively harmful with a glass or raised plate: "the module would store wrong geometry", with no known recovery (R:custom/LIDAR-NOTES.md:316-321; FTB:README.md "Warnings"). The open driver refuses 0x05 (FTB:driver/lidar_serial.py:50-54).

The −0.041 mm/mm tilt the module reports today shows that its internal calibration does not level its output to the bed. Mount effects are therefore handled in software, and a rigid move should not invalidate the module's intrinsic calibration (ESTIMATED).

Suggested safeguard: read 0x1E (a read-only getter) before and after the move and compare. This is not implemented in the driver.

### A.4 What to re-run or change if the LiDAR moves or rotates

1. **Before** powering up on the new mount:
   - Set `[lidar] x_offset`/`y_offset` (R:tuning.cfg:928-929) to the new CAD value.
   - **Also overwrite or delete** `lidar_x_offset`, `lidar_y_offset`, `lidar_x_per_z`, `lidar_y_per_z` in variables.cfg (R:variables.cfg:9-12). Saved values win over the config, and calibration refuses a change of more than 5 mm (R:custom/lidar.py:3879-3881).
   - Set `x_dir` if the module is turned 180°.
   - Set `scan_z`/`offset_z` if the distance origin is no longer about 22.6 mm above the tip.
2. `LIDAR_OFFSET_CALIBRATION` (prints a cross; the plate around X135–165 Y133–167 must be clear) (R:tuning.cfg:969-977). Check that the arms read 20.1–20.3 mm (scale check).
3. `LIDAR_TWIST_CALIBRATION`, or `AXIS_TWIST_TOUCH_CALIBRATE`, which does the LiDAR too when `service:` is set. This rewrites `lidar_twist` (R:tuning.cfg:979-993; R:custom/twist_touch.py:128-147).
4. Edit the hard-coded reach in `custom/lidar.py`: `MESH_X`, `MESH_Y` (2311-2312), fine X 4–284 (2405), `strip_x0` 18 (2551). Re-check the macro test areas (PA test X130–154 Y100–220, Creality PA test X170–204 Y60–199) for reach and keep-out. Line width and spacing (28/26) only change if the line length changes.
5. `LIDAR_TIMING` is only needed if the driver changes, not the geometry (R:custom/lidar.py:35-40).
6. Throw away stored mount-specific data on the Pi (`/var/lib/k1-lidar`): bare-plate references, height maps, `firstlayer/corrmap.json`. Re-validate `fl_zoffset` if First_Layer_Learn is used.
7. Re-run `LIDAR_BED_MESH`/`MESH_BENCHMARK` comparisons if they are used for acceptance.
8. Never run the sticker calibration, `create_ir_image`/0x56, 0x1B or OTA (FTB:docs/protocol.md:7-20).

### A.5 Thermal and airflow sensitivity

- **Nothing is documented** in the repo or FreeTheBeam about thermal drift of the LiDAR.
- An IR sensor temperature getter exists (0x1C, R:custom/lidar_serial.py:40, 277) but is unused.
- Scans run with the nozzle at ≤150 °C (R:tuning.cfg:255, 258). The first-layer check drops the nozzle 30 °C and retracts (R:custom/LIDAR-NOTES.md:228-232).
- Air and fan effects on the reading have not been studied (ESTIMATED risk). Recommend logging 0x1C during long scans after any redesign that moves hot air past the module.

---

## B. BIQU MicroProbe V2

### B.1 Current configuration

| Item | Value | Label / source |
|---|---|---|
| Offsets | x_offset **0**, y_offset **+20.3** | MEASURED-BY-USER R:tuning.cfg:12-14 |
| z_offset | **0.831** (load cells: nozzle contact vs probe at the same spot, bed ~70 °C, nozzle 150 °C) | MEASURED-BY-USER R:printer.cfg.save_config:6; R:README.md:60 |
| z_offset history | 1.210 (old mount) → 0.876 (2026-10-06 move) → 0.831 | VERIFIED git c74fe8b |
| Sampling | samples 3, median, tolerance 0.04, retries 3; probe retracts between samples (Pellcorp default `deactivate_on_each_sample: true`) | VERIFIED R:tuning.cfg:15-22; PC:config/microprobe.cfg |
| Typical spread | 0.005 mm, single outliers up to ~0.04 mm | MEASURED-BY-USER R:tuning.cfg:19-20 |
| Speeds | Pellcorp: speed 5, lift_speed 20. Z homing second speed set to 5 so homing and probing match (0.03 mm difference at 1 vs 5 mm/s) | VERIFIED PC:config/microprobe.cfg; R:printer.cfg:3-4; R:README.md "Homing and mesh probes" |
| Pins | deploy `[output_pin probe_enable] nozzle_mcu:PA8`; signal `^!nozzle_mcu:PA9` (V2, active low) | VERIFIED PC:config/microprobe.cfg |
| Connector | nozzle MCU board **TOUCH** port: 5-pin Molex PicoBlade, pinout GND / 5V / PA8 / GND / PA9. Reachable from the left (LiDAR) side; only the outer cover has to come off | VERIFIED PCW:docs/microprobe_wiring.md:7-18; image `nozzle_rear.png` (board K1-NOZZLE-C_V14) |
| Deploy macros | `PROBE_DOWN`/`PROBE_UP` = `SET_PIN probe_enable 1/0`, G4 P500 after deploy | VERIFIED R:tuning.cfg:23-35 |
| Mount in use | **likely** Printables 785004 "BIQU Microprobe for Creality K1/MAX/C" (its listing shows y_offset 20.3 and `PROBE_DOWN`, matching git c74fe8b) | ESTIMATED: search snippet only. Printables (www and API) blocked. **User to confirm** |
| Previous mount | Pellcorp "Default" k1m = Printables 867527 remix, x −33, y 0 | VERIFIED PC:mounts/microprobe/Default-k1m.overrides; git c74fe8b |

### B.2 Physical data (V2)

All rows: VERIFIED from `BTT:MicroProbe V2 User Manual_20240330.pdf`, p. 4–5.

| Item | Value |
|---|---|
| Envelope | 21.9 × 15.6 × 28.1 mm (extended) |
| Flange | width 21.93; depth 15.60; thickness 2.10 |
| Mounting holes | **2 × Ø2.7**, **17.00 apart**, 2.50 from the flange side edges, **6.80 from the back face** |
| Heights below flange top | body bottom 23.98; then 25.30, 27.58, 28.10 (= body bottom + 1.32, 3.60, 4.12) |
| Bracket rule | probe bottom ~1–2 mm below the nozzle at full extension |
| Mass, electrical | 6 g; 5 V; 19 mA standby, 350 mA operating; 5-pin 1.25 mm; signal is open drain and needs a strong pull-up |
| Environment and accuracy | ≤60 °C ambient; σ 0.001 mm (24 °C ambient, 60 °C bed), σ 0.003 mm (60 °C ambient, 100 °C bed); 10 M cycles |
| Screws in BIQU kits | M2.5×5 |

**My reading of the side view (ESTIMATED):** the stowed pin protrudes 1.32 mm below the body; the trigger point is at 3.60; full extension is 4.12. That gives a deploy stroke of about 2.80 mm and about 0.52 mm of travel to trigger.

**BTT STEP files.** The repo has no V2 mockup. `BIQU microprobe mockup.STEP` is dated 2022-10-18, so it is V1.
- Its holes are Ø2.7 at 16.93 mm spacing (matches V2).
- Its pin is Ø1.6, centred between the holes along the hole line and 2.75 mm off that line.
- Its total height (~21.7 mm) does **not** match V2 (28.1).
- Use it only for the hole pattern; use the V2 drawing for heights (ESTIMATED).

### B.3 Keep-out zones and how they come from the probe

Zones are in nozzle coordinates. They were measured 2026-10-06 by stepping the toolhead back until about 3 mm of gap was left between the **probe** and the Z-rod housings (R:tuning.cfg:886-902).

| Zone | X | Y beyond | Measurement note | Label |
|---|---|---|---|---|
| zone1, middle housing | 130–170 | 293 | blocked at Y293 at X150; X105 and X195 clear to the end of travel; housing 30 mm + 10 mm each side | MEASURED-BY-USER R:tuning.cfg:890, 896 |
| zone2, left corner | −10–19 | 292 | Y292 at X−2; X20 clear | MEASURED-BY-USER R:tuning.cfg:891, 898 |
| zone3, right housing | 266–286 | 302 | Y302 at X286, Y305 at X266 | MEASURED-BY-USER R:tuning.cfg:892, 900 |
| zone4, right corner | 286–330 | 287 | Y287 at X306.5 | MEASURED-BY-USER R:tuning.cfg:892, 902 |

- Y travel max is 306 (PC:mounts/microprobe/Default-k1m.overrides; PC:rpi/printers/creality-k1m-2024.cfg:89).
- **Derivation (ESTIMATED):** zone y_min ≈ housing front Y − (rearmost toolhead point relative to the nozzle) − 3 mm.
- With the old side mount (Y 0) there were no keep-outs, so the stock toolhead's rearmost point clears the housings over the full travel. Its Y value is not in the repo.
- Any part of a new toolhead that reaches further back than today's probe (pin +20.3 plus the body behind it, ≈ +28 if the pin is mid-body) reduces Y reach at these X ranges.
- The zones are also in Orca: `printable_area` corners cut out, `bed_exclude_area` 130–170 × 293–300 (R:orcaslicer/machine/*.json; R:orcaslicer/README.md "Bed keep-out zones").
- `[skew_correction]` must stay after `[keep_out]` (R:tuning.cfg:904-911).

### B.4 Probe height relative to the nozzle (ESTIMATED)

These values combine the V2 drawing with the measured z_offset 0.831, assuming the trigger point is at body bottom − 3.60:

| Feature | Z |
|---|---|
| Trigger plane | −0.83 |
| Extended tip | −1.35 |
| Stowed tip | +1.45 |
| Body bottom | +2.77 |
| **Flange top (mount face)** | **+26.75** |

This fits BIQU's 1–2 mm rule. The mount face Z tolerance is about ±0.5 mm before z_offset leaves BIQU's recommended window. The z_offset itself is re-measured anyway.

### B.5 What changes if the probe moves

| Item | Where | Rule today | Label |
|---|---|---|---|
| `x_offset`/`y_offset` | R:tuning.cfg:13-14 | measured | MEASURED-BY-USER |
| `z_offset` | SAVE_CONFIG (R:printer.cfg.save_config:6) | re-measure with load cells (`_LOAD_CELL_TOUCH_CHECK` logic, R:tuning.cfg:326-351) | MEASURED-BY-USER |
| `zero_reference_position` | R:tuning.cfg:40 = (153, 173.3) | = Z-home nozzle position (home_x, home_y) + probe offset. home_x/y = int(position_max/2) = 153/153 (PC:k1/installer.sh:973-977) | VERIFIED |
| `mesh_min`/`mesh_max` | R:tuning.cfg:43-44 = (5,20)/(295,295) | probe reach: travel −2…306.5 (X), −2…306 (Y) plus offset, inside the bed and keep-outs. Y min 20 ≈ −2 + 20.3 | VERIFIED |
| Overridden values | R:microprobe.cfg:2-3, 12-14 | `mesh_min 5,5 / mesh_max 262,295` and `calibrate_end_x 273` are **stale for the old mount** but are overridden later by tuning.cfg. Clean these up in the redesign | VERIFIED |
| Stale saved mesh | R:printer.cfg.save_config:48-51 | `bed_mesh default` has X 5–261.96, Y 5–295 (old reach) | VERIFIED |
| `screws_tilt_adjust` | R:microprobe.cfg:6-9 (changed 2026-10-09, git feac58f) | nozzle = screw − probe offset | MEASURED-BY-USER |
| `[axis_twist_compensation]` | R:tuning.cfg:395-397 (end_x 290); microprobe.cfg start_x 10, y 153; SAVE_CONFIG z_compensations, start 10, end 290 | **re-run `AXIS_TWIST_TOUCH_CALIBRATE`** (7 points, 2 passes) | VERIFIED |
| Glass-soak spots | `_GLASS_SOAK` reads probe offsets and mesh limits at runtime (R:tuning.cfg:79-111) | automatic | VERIFIED |
| True Zero touch | touches at zero_ref, checks the probe at zero_ref − offset (R:tuning.cfg:297-314) | automatic | VERIFIED |
| `[keep_out]` zones | R:tuning.cfg:894-902 | **re-measure** | MEASURED-BY-USER |
| Orca bed shape | R:orcaslicer/make_profiles.py → machine JSONs | regenerate | VERIFIED |
| `[nozzle_wipe]` strip | X 40–100, Y 297.4–298.6 (R:tuning.cfg:378-386); chosen where the probe clears the frame (R:README.md:18) | re-place | MEASURED-BY-USER |
| Park positions | cancel 296/270, custom 296/8 (R:start_end.cfg); end-of-print park Y 270 (R:README.md:18) | check against keep-outs | VERIFIED |
| LiDAR reach comment | R:custom/lidar.py:2309-2312 | MESH_Y top (265) comes from where the nozzle meets the keep-outs (287 − 21.3) | VERIFIED |

### B.6 Twist and lever arm: why sensor placement matters (ESTIMATED analysis of MEASURED data)

All twist values are "sensor − nozzle at the same bed spot", so bed shape cancels.

| Setup | Lever | Range across X | Implied angle variation |
|---|---|---|---|
| Probe now | Y +20.3 | +0.133 → −0.134 = **0.267 mm** over X 10–290 | ≈ 13 mrad pitch about X |
| LiDAR now | Y −21.3 (also X −36) | **−0.181 mm** (opposite sign, as expected) | ≈ 8.5 mrad |
| Probe, old mount | X −33, Y 0 | +0.039 → −0.032 = **0.070 mm** over nozzle X 43–306 | ≈ 2 mrad roll |

Sources: probe now R:printer.cfg.save_config:54-56; LiDAR R:variables.cfg:8; old mount git c74fe8b.

- The probe and LiDAR angles disagree, so the motion is not a pure rigid pitch. The remaining 0.018 mm/100 mm Y slope between LiDAR and probe is unexplained (R:custom/LIDAR-NOTES.md:181-186).
- Conclusion: the carriage pitch varies about 5× more than its roll along X. **Sensors offset in Y pick up far more X-dependent error than sensors offset in X.**
- Twist compensation removes this only along X, at calibrate_y 153 (LiDAR at Y 145/153).
- A redesign that changes the toolhead's pitch stiffness, or its mass and CG relative to the X carriage, changes these tables.

---

## C. Fans and thermal as configured

### C.1 Fans (Pellcorp K1/K1 Max patch: PC:k1/patches/fan_control.cfg; same in PC:rpi/printers/creality-k1m-2024.cfg:214-235)

| Fan | Section | Pin | PWM settings | Notes |
|---|---|---|---|---|
| Part cooling ("model fan", 4-pin GND/PWM/FG/FAN+ on K1-NOZZLE-M_V12) | `[fan]` | `!nozzle_mcu:PB8`, `enable_pin nozzle_mcu:PB6` | cycle_time 0.010, hardware_pwm false. kick_start_time, off_below and max_power are **not set**, so Klipper defaults apply (0.1 s / 0 / 1.0, ESTIMATED from Klipper defaults) | tach `^nozzle_mcu:PB3` commented out. `p_selector_map: chamber, auxiliary, chamber` (M106 P1/P2/P3). `[extruder] cooling_fan: fan` feeds MPC (R:tuning.cfg:414) |
| Hotend / heatbreak | `[heater_fan hotend]` | `nozzle_mcu:PB5`, tach `^nozzle_mcu:PB4` | on above heater_temp 40 °C (full speed by default) | connector on K1-NOZZLE-C_V14 (PCW image `nozzle_rear.png`) |
| Auxiliary (side, chassis) | `[fan_generic auxiliary]` | main MCU `PB1` | cycle_time **0.002** ("fixes throttling below 80 %") | not on the toolhead; Orca `auxiliary_fan: 1` |
| Chamber (exhaust) | `[fan_generic chamber]` + `[temperature_fan chamber_fan]` | main `PC0` (duplicate_pin_override PC0, PC5) | 0.010; watermark control, target 35 °C default, max_temp 70 | M141 sets the threshold per filament |
| Main-board MCU fan | `[static_digital_output]` | `PB2` | always on | — |

Other nozzle MCU pins:
- Heater `PB7`, thermistor `PA0` (EPCOS 100K).
- Extruder `PB1/PB0/PB2`, rotation_distance 6.9, 16 µsteps.
- ADXL345 `PA4–PA7`, `axes_map: x,-z,y`.
- Filament sensor 2 `PA10`.

Source: PC:rpi/printers/creality-k1m-2024.cfg:131-198; CRA images.

### C.2 Orca filament fan settings (R:orcaslicer/filament/*.json, R:orcaslicer/make_profiles.py:195-232)

| Filament | Part fan min–max % | Aux fan % | Chamber fan threshold (M141) | Max flow mm³/s | Nozzle °C |
|---|---|---|---|---|---|
| PLA / Matte / Silk / + / Rapid | 100–100 | 70 | 35 | 20 / 18 / 8 / 18 / 23 | 220–225 |
| PLA Speed Benchy | 100–100 | 100 | 35 | 32 | 255 |
| PETG (all) | 30–80 (Silk 60, Matte 70) | 0 | 40 | 8–14 | 245–250 |
| ABS / ASA | 0–30 | 0 | 60 (soak to 45 °C) | 16 | 260 |

- Machine settings: `fan_kickstart 0`, `fan_speedup_time 0`, `fan_speedup_overhangs 1`, `auxiliary_fan 1`.
- Overhang and bridge fan speeds are **inherited from Creality Generic presets** and are not in the repo.
- PLA is limited by the fan's maximum (already 100 %). This is the case where a stronger part-cooling design helps directly (ESTIMATED).

### C.3 MPC model and what it says about the fan (R:printer.cfg.save_config:20-25; breakpoint spacing KAL:docs/MPC.md:185-188)

| Quantity | Value | Label |
|---|---|---|
| heater_power | 60 W ("K1 series 60 W ceramic heater") | VERIFIED R:tuning.cfg:412-413 |
| block_heat_capacity | 16.36 J/K | MEASURED-BY-USER |
| sensor_responsiveness | 0.0917 K/s/K | MEASURED-BY-USER |
| ambient_transfer (fan off) | 0.0800 W/K | MEASURED-BY-USER |
| fan_ambient_transfer at 0/16.7/33/50/66.7/83/100 % | 0.0800, 0.0892, 0.0995, 0.1062, 0.1148, 0.1149, 0.1166 W/K | MEASURED-BY-USER (`MPC_CALIBRATE FAN_BREAKPOINTS=7`, R:tuning.cfg:765) |
| Fan effect | +46 % heat loss at 100 %; about linear to 66 %, then **flat** (0.1148 → 0.1166) | ESTIMATED from the table |
| Extra heat loss at 250 °C (ΔT ≈ 225 K) | ≈ 18 W (fan off) → 26 W (fan 100 %), +8 W | ESTIMATED |
| Heater headroom | 60 W vs 26 W loss, before filament. Melt power at 23 mm³/s PLA ≈ 23 × 1.25 g/cm³ × 1.8 J/gK × 200 K ≈ 10 W | ESTIMATED |
| Control result | 0.5 °C overshoot, ±1.5 °C on a 0→100 % fan step | VERIFIED R:README.md:25 |
| Hotend flow | stock hotend melts ~23 mm³/s fast PLA in practice; 32 mm³/s "rated max" at 255 °C; PETG at 18 mm³/s under-extruded on layer 2 | VERIFIED R:orcaslicer/README.md:64, 77, 99 |

**Implication.** The current duct blows a lot of air on the heater block. A redesign that shields the block (sock, duct aimed below the nozzle) changes `fan_ambient_transfer`; re-run `MPC_CALIBRATE`. The flat top end suggests the fan or duct saturates above about 66 %, which could also be a fan-curve effect (ESTIMATED).

---

## D. Toolhead hardware facts in the repo, and input-shaper mass sensitivity

| Item | Value | Label / source |
|---|---|---|
| Printer | K1 Max, CoreXY, Simple AF + Kalico (aug2026 branch), glass bed + textured PEI | VERIFIED R:README.md:1-3, 100-106 |
| Hotend / heater | stock K1-series hotend, 60 W ceramic heater, EPCOS 100K thermistor | VERIFIED R:tuning.cfg:412-413; PC:rpi/printers/creality-k1m-2024.cfg:141-143 |
| Nozzles | 0.2/0.4/0.6/0.8/1.0, `nozzle_type: brass` in Orca | VERIFIED R:orcaslicer/README.md:21-27; machine JSON |
| Hotend mods | **none recorded** in the repo; README mentions a possible high-flow hotend only as a future option | VERIFIED R:orcaslicer/README.md:64 |
| Extruder | stock, rotation_distance 6.9, 16 µsteps (Pellcorp definition; user's base printer.cfg not in repo) | VERIFIED PC:rpi/printers/creality-k1m-2024.cfg:134-138 |
| Accelerometer | ADXL345 on the nozzle MCU board, software SPI PA4–PA7, `axes_map: x,-z,y` (chip is mounted vertically) | VERIFIED PC:rpi/printers/creality-k1m-2024.cfg:192-198 |
| Shaper test point | `resonance_tester` probe_points 150,150,10; accel_per_hz 75 | VERIFIED same file:200-204 |
| Load cells | 4× HX711 under the bed (leveling MCU); not on the toolhead | VERIFIED R:tuning.cfg:197-234 |
| Kinematics limits | max_velocity 800, max_accel 20000, SCV 5; X −2…306.5, Y −2…306; XY 32 µsteps, rotation_distance 40 (20T GT2) | VERIFIED PC:rpi/printers/creality-k1m-2024.cfg:53-90, 206-212; R:README.md:138 ("20T GT2") |
| Input shaper | X **3hump_ei 77.6 Hz**, Y **ei 52.0 Hz** (re-run with glass) | MEASURED-BY-USER R:printer.cfg.save_config:8-12 |
| Projected max accel at TARGET_SMOOTHING 0.12, SCV 5, ζ 0.1 | **X 4408**, **Y 5036** mm/s² | ESTIMATED: my reimplementation of KAL:klippy/extras/shaper_defs.py and shaper_calibrate.py:240-371. The X value matches R:orcaslicer/README.md:86 ("~4400–5800") |
| Slicer accelerations | walls 4000–5000, top 2500–3000, infill 8000–10000, travel 12000; Speed Benchy 20000 | VERIFIED R:orcaslicer/README.md:86, 75 |

**Mass sensitivity.** Single-mode model: f ∝ 1/√m_eff, then Klipper's max_accel formula (ESTIMATED).

| Effective moving mass | X freq / max accel (3hump_ei) | Y freq / max accel (ei) |
|---|---|---|
| ×0.9 | 81.8 Hz / 4898 | 54.8 Hz / 5595 |
| ×1.0 (today) | 77.6 / 4408 | 52.0 / 5036 |
| ×1.1 | 74.0 / 4007 | 49.6 / 4578 |
| ×1.2 | 70.8 / 3673 | 47.5 / 4196 |
| ×1.3 | 68.1 / 3391 | 45.6 / 3873 |
| ×1.5 | 63.4 / 2938 | 42.5 / 3357 |

**How to read the table:**
- On CoreXY, X moves only the toolhead (plus belts), so X is the most sensitive to toolhead mass.
- Y moves the whole X gantry, so a toolhead mass change is a smaller fraction of m_eff on Y.
- The 3hump_ei choice on X suggests a multi-peak or less clean X response. The single-mode model is a rough guide.
- A stiffer toolhead and carriage connection can raise the frequency even when mass goes up.
- **The toolhead's real mass is not recorded anywhere** (§F).

---

## E. What a toolhead redesign breaks or must re-calibrate (checklist)

**Wiring and electronics**
- [ ] Nozzle MCU boards (K1-NOZZLE-M_V12 + K1-NOZZLE-C_V14):
  - Keep the pins: heater PB7, thermistor PA0, extruder PB0–2, part fan PB8/PB6 (+PB3 tach), heatbreak fan PB5/PB4, probe PA8/PA9 on TOUCH, filament sensor PA10, ADXL PA4–7.
  - Keep the LiDAR pass-through port. The LiDAR USB arrives on a separate cable.
- [ ] ADXL `axes_map` if the board orientation changes; re-run SHAPER_CALIBRATE + belt test (forced every 200 h; `CALIBRATE_NEXT_PRINT WHAT=shaper`).
- [ ] Part-fan PWM (`cycle_time`, kick-start) if the fan model changes. Heatbreak fan tach is expected on PB4.

**Thermal**
- [ ] `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7` (changed duct, sock or heater block). Update `heater_power` if the heater changes.
- [ ] Orca max volumetric speeds (`vol` in make_profiles.py) if the hotend changes; regenerate profiles.
- [ ] PA per nozzle (`LIDAR_PA_CALIBRATION`).

**Probe (if it moves)**
- [ ] `[probe] x_offset/y_offset`, then `z_offset` via load-cell comparison.
- [ ] `zero_reference_position`, `mesh_min/mesh_max`. Clean up the stale values in microprobe.cfg (mesh 262/295, calibrate_end_x 273) and the stale saved `bed_mesh default`.
- [ ] `[axis_twist_compensation]` (calibrate_start/end_x, y) → `AXIS_TWIST_TOUCH_CALIBRATE`.
- [ ] `screws_tilt_adjust` points.
- [ ] Glass-soak thresholds only if probe noise changes (`_GLASS_SOAK` threshold 0.012).

**Envelope**
- [ ] Re-measure `[keep_out]` zones with the new rearmost and outermost points. Mind the left/right/front collision points too; today only rear zones exist.
- [ ] Orca `printable_area`/`bed_exclude_area` (5 machine JSONs via make_profiles.py).
- [ ] `[nozzle_wipe]` strip location; park positions; check `position_min/max` and homing still reach the endstops (sensorless). home_x/home_y come from position_max.

**LiDAR (if it moves)**
- [ ] §A.4 steps 1–7.

**Load-cell touch**
- [ ] The nozzle must still be the lowest point. Check that the probe's stowed tip (≈ +1.45) and the LiDAR window clear the bed at touch and wipe (wipe presses 0.15 into the PEI, the peel rises 5 mm).
- [ ] Re-check `_LOAD_CELL_TOUCH_Z` min/max difference limits (−0.03/+0.15) after z_offset changes.
- [ ] Toolhead mass does not affect the load-cell touch (the bed is weighed), but extra wiring drag could.

**Validation**
- [ ] First-layer test (load_cell `z_offset −0.02` came from a full-bed first-layer test, R:tuning.cfg:214-216).
- [ ] Mesh vs LiDAR benchmark (`MESH_BENCHMARK_RUN`).
- [ ] `CONFIG_OVERRIDES` so updates keep the changes.

---

## F. Information only the user can provide

1. **The LiDAR module itself:**
   - outline (L × W × H);
   - mounting-hole positions and thread, and the screw length;
   - alignment-post diameters and positions;
   - **emitter and camera window positions and sizes** relative to the mounting face;
   - connector position and cable exit;
   - mass.

   Ideally: photos from 6 sides with calipers, or a scan. Also measure the stock bracket's position relative to the nozzle (X, Y, Z of the mounting face).
2. **The current Microprobe mount:**
   - confirm it is Printables 785004 and send the STL or STEP (the Printables API and site are blocked here);
   - photo plus the measured pin position (should be 0/+20.3);
   - which screws and holes on the K1 toolhead it uses.
3. **Toolhead mass** (stock, with probe and LiDAR), and the X-carriage mass if separable. This is needed for the shaper and mass budget.
4. **Stock toolhead geometry:**
   - nozzle tip to carriage mounting points, nozzle MCU board location and orientation, fan and duct sizes and positions;
   - outer envelope (front, left, right extremes), so new collisions can be checked.

   Also confirm the part-fan type (blower size) and the heatbreak-fan size.
5. **Base printer.cfg as installed** (not in the repo: the K1 Max 2023 vs 2024 variant, rotation_distance 72 vs 40, position_max, the exact fan, ADXL and extruder sections). The README's "20T GT2" suggests the 2024 variant (40).
6. **Z-rod housing positions** (or photos) and the frame clearance at the back and sides, to predict keep-outs before printing.
7. **Optional on-printer reads:**
   - LiDAR 0x1E calibration bytes and 0x1C temperature (read-only), as a baseline before moving the module;
   - a `LIDAR_TWIST_CALIBRATION` run plus `AXIS_TWIST_TOUCH_CALIBRATE` at a second Y, to tell pitch from bed effects.
8. **Overhang and bridge fan values** from the Creality Generic presets in the user's Orca install (inherited, not in the repo).
9. **Network access** (this session): `www.printables.com`, `api.printables.com`, `pellcorp.github.io` and `cdn.shopify.com` were blocked. Allow them, or have the user provide the 785004 files.

---

## G. Reference files obtained (untrusted downloads, nothing executed)

Folder: `/tmp/claude-0/-home-user-K1ProMaxUltra/1fc00b30-b973-54a8-8106-390cde6c1256/scratchpad/ref/sensors/`

| File | What it is | Source |
|---|---|---|
| `MicroProbe V2 User Manual_20240330.pdf` | V2 manual | BTT |
| `microprobe_v2_dimensions_page5.png` | dimension drawing, p. 5 | rendered from the manual |
| `biqu_microprobe_mockup_2022_V1.STEP` | V1 mockup (2022); hole pattern only | BTT |
| `microprobe_V2_bracket_stealthburner.STEP` | V2 bracket example | BTT |
| `nozzle_rear.png` | nozzle board K1-NOZZLE-C_V14 pinout, including TOUCH | PCW |
| `touch_port.png`, `bltouch_wiring.png` | TOUCH port and probe wiring | PCW |
| `nozzle_lidar_usb_port_wiring.png` | LiDAR port pinout | PCW |
| `Nozzle-board-A-en.JPEG`, `Nozzle-board-B-en.JPEG` | Creality nozzle board ports: LiDAR extension, power, model fan, heatbreak fan, TOUCH | CRA |

Scripts (my own): `…/scratchpad/scripts/shaper_mass.py`, `stepbb.py`, `stepcirc.py`.

---

## H. Network-restored findings (2026-10-30, second pass)

**Access this pass:**
- Worked: the Printables GraphQL API and `files.printables.com`/`media.printables.com` (via curl), `cdn.shopify.com` (curl), github.com.
- Still failing in WebFetch: `pellcorp.github.io`. I used the wiki's git source instead (`PCW` @ecd1770, 2026-10-29), which has the same content. `curl https://pellcorp.github.io/creality-wiki/microprobe/` returned 200 and matches it.
- `store.dremc.com.au` is still blocked.

All downloads are in `/tmp/claude-0/-home-user-K1ProMaxUltra/1fc00b30-b973-54a8-8106-390cde6c1256/scratchpad/ref/sensors/{p785004,p773067,p1476318,web}/`. They were treated as data; no downloaded code was run. The geometry was measured with my own scripts in `…/scratchpad/scripts/` (`stl_holes*.py`, `stl_slices.py`, `stl_render.py`).

**New label used here:**
- **DERIVED** = measured from community CAD (same meaning as `interfaces.py`).

### H.1 Printables 785004: the current probe adapter (closes part of M8)

**Model data** (VERIFIED, Printables GraphQL `print(id:785004)`):
- "Biqu MicroProbe for Creality K1 / MAX / C", user "aadfg dsadg".
- Licence: **Creative Commons Public Domain**.
- One file: `Biqu_microprobe_K1.STL` (206 284 B). The STL header names it `K1_Bl_Touch_Adapter001`.
- The description is a Klipper block: `probe_enable nozzle_mcu:PA8`, `pin ^!nozzle_mcu:PA9`, `x_offset 0`, `y_offset 20.3`, `samples 2`, `deactivate_on_each_sample False`, `PROBE_DOWN/UP`.
- It links github.com/Veisen/K1_microprobe. That repo's HOW-TO also lists a commented alternative "zadni offset" (Czech, "rear offset") `y_offset 25.25`, and `mesh_min 5,25.3`.
- **This matches the repo's 2026-10-06 config exactly (git c74fe8b), so the probe mount is 785004 with high confidence.** It is still not confirmed by the user.
- Photos (3) show the adapter hanging vertically behind the hotend, under the rear of the extruder motor, with the probe pointing down.

**Files saved:** `p785004/biqu_microprobe_k1_785004.stl`, `img_3324/3325/3379.jpeg`, plus my renders and slices (`render_785004.png`, `slicesZ/X/Y.png`).

**Measured geometry.** STL frame: Z up (the probe flange is at the bottom face), +Y_stl toward the printer rear (the chamfered cable side faces the camera in the rear-view photo). All rows DERIVED from the STL.

| Feature | STL frame | Value |
|---|---|---|
| Envelope | X 1.57–35.67, Y 2.57–18.29, Z 368.95–401.45 | **34.10 × 15.72 × 32.50**; watertight; 8.55 cm³ |
| Bottom face = probe flange seat | Z 368.95, flat | footprint Y 2.57–18.29 (15.7, about the probe's 15.60 depth) |
| Probe screw bores | (10.07, 10.49) and (27.00, 10.49) | **Ø3.90, 8 mm deep** (Z 369–377), Ø4.4 entry chamfer; **spacing 16.93** (BIQU: 17); centre X 18.535. Likely M2.5 heat-set inserts or a self-tap pilot (ESTIMATED) |
| Top screw holes (toolhead side) | (6.57, 9.25) and (30.67, 9.25) | **Ø2.40** through Z 395.5–398.5, then a **Ø4.20 counterbore 2.95 deep** from the top face; **spacing 24.10**; centre X 18.62 (same as the probe centre within 0.09) |
| Side windows (pockets) | open on the Y_min face (Y 6.05); X ≈ 4–9 and 28–33; Z ≈ 386.7–396; depth to Y ≈ 11 | ≈ 5 W × 7–9 H × 5 D. Each top hole ends inside one window, so they act as nut or screw-head pockets, or clearance for a toolhead tab (purpose ESTIMATED) |
| Cable channel | through-slot X 13–24 × Y 14–18, full height | for the probe lead (rear side) |
| Body shape | Z ≥ 384: block Y 6.05–18.29, chamfered rear; Z 369–383: skirt tapering to the probe | — |

**How it attaches to the toolhead (ESTIMATED, user to confirm with one photo).**
- The flat Y_min face (Y_stl 6.05) faces the toolhead.
- Two vertical screws, 24.10 mm apart and about M2 (Ø2.4 clearance, Ø4.2 head counterbore), plus the two side windows, engage two features on the underside or rear of the K1 toolhead about 27–33 mm above the probe flange.
- The adapter carries no other fasteners. No source names the K1 screws it reuses.

**Placement in the nozzle frame (ESTIMATED).**

Assumptions:
1. X: adapter and probe centre at nozzle X 0. This matches `x_offset 0`.
2. Z: adapter bottom = probe flange top = **+26.75** (§B.4).
3. Y: the probe pin (Y +20.3) is at the middle of the body's 15.60 depth. The connector (the 6.80 side) faces +Y, toward the cable slot. That puts the pin 1.0 mm in front of the hole line. **V2 does not publish its pin position relative to the holes.** The 2022 V1 mockup has it 2.75 off the hole line, so the result carries about ±2 mm uncertainty.

Mapping: X_p = X_stl − 18.58; Y_p = Y_stl + 10.81; Z_p = Z_stl − 342.20.

| Item | Nozzle frame (X, Y, Z) |
|---|---|
| Probe pin | 0, **+20.3**, tip extended −1.35 / trigger −0.83 / stowed +1.45 (§B.4) |
| Probe body (V2) | Y **+12.5 … +28.1**, X ±10.97, Z +2.77 … +26.75 (body), flange +24.65 … +26.75 |
| Adapter envelope | X −17.0 … +17.1, Y **+13.4 … +29.1** (block above Z +41.8: +16.9 … +29.1), Z **+26.75 … +59.25** |
| Adapter → toolhead screws | X ±12.05, Y +20.1, heads at the top face Z +59.25 (counterbore down to +56.3) |
| Side windows | X ≈ −14.6…−9.6 and +9.4…+14.4; Y +16.9…+21.8; Z ≈ +44.5…+53.8 |
| **Rearmost point of the probe assembly** | **Y ≈ +29.1** (adapter). Range +25.4…+30.9 over the pin-position uncertainty |

The derived toolhead mating face (Y ≈ +16.9 at Z > +42) and screw height (≈ +56…+59) are a constraint for the new rear structure, but only once the user confirms them. The keep-out data then implies the middle Z-rod housing front is at about Y 293 + 3 + 29.1 ≈ **325** in printer coordinates (ESTIMATED).

### H.2 LiDAR module physical data (M6)

**Sources found:**

| Source | What it gives | Label |
|---|---|---|
| **Micro Swiss FlowTech K1/K1 Max install PDF** (cdn.shopify.com, 2 pages) | "Remove the two screws holding the LiDAR sensor (**2.0 mm Allen wrench**)"; "Reattach the LiDAR sensor **to the mounting bracket** using two screws". The step-1 photo shows the module on the **left side** of the toolhead with both screws on top, driven from above | VERIFIED: `web/flowtech.pdf` p. 1, steps 1 and 11 |
| **Printables 773067** "Creality K1 Max AI LiDAR Mounting Plate" (Icezaza, **CC BY-NC-SA**; author notes "Haven't tested it") | community replica of the stock sheet-metal bracket, STEP + STL | DERIVED (untested replica) |
| **Printables 1476318** "Lidar Cover \| K1 Max" (Hysaru, **CC BY-SA**) | replacement top cover (`AiLidarBody.stl` + `.f3d`); photos of the module with the stock bracket fitted | DERIVED |
| Creality "LiDAR Sensor Kit" listing | 71 g including cable and mounting accessories | ESTIMATED (search snippet; store.dremc.com.au still blocked) |

**Stock bracket** (from the 773067 STEP; the frame is a flat sheet-metal L). DERIVED:
- 1.5 mm sheet with an L-bend.
- **Main leg 35.0 × ~21** (STL 35 × 22.5 including the bend).
  - It screws to the module's back face with **2 × Ø2.53 holes, countersunk to Ø4.0**, at a diagonal offset **17.0 in length × 15.0 in height**.
  - It has **2 × Ø1.9 locating holes**, 17.5 apart, on the mid-line.
  - It has a 5 × 3.5 relief slot next to the bend.
- **Toolhead flange 13.5 × 13.5**, on top of one end of the module (photo 1476318 #2). It carries a **4-hole diamond**:
  - 2 × Ø2.53 countersunk to Ø3.76, **8.0 apart**;
  - 2 × Ø2.0, **8.5 apart**, on the perpendicular axis;
  - same centre for both pairs.
  - These are the "two screws above the LiDAR" (2.0 mm key) plus two locating features. Whether the Ø2.0 pair takes posts or screws is ESTIMATED.

**Module body.**
- **Footprint about 46.6 (X, along the laser line) × 19.4 (Y)**, from the replacement top cover's outer outline. DERIVED; outline 46.56 × 19.40. It has 2 internal locating pegs Ø2.4, 22.5 apart, and Ø2.0 holes at a diagonal 20 × 14.5.
- **Height about 25–28 mm.** ESTIMATED from the photo proportions (front face aspect ≈ 0.6 × 46.6) and from the bracket's 21–22.5 mm back leg.
- Photo 1476318 #1 shows a dark window strip along the **lower front edge** with two round optical elements on one half, plus a hinged black flap. **The exact window positions and sizes on the underside are still MISSING.**
- **The module's own mass is still MISSING.** The 71 g kit figure is an upper bound for module + cable + bracket (ESTIMATED).

**Combined with the optics data** (§A.2, all ESTIMATED):
- The module's internal distance origin is about 22.6 mm above the nozzle tip.
- The laser sheet comes from +Y at about 45°.
- The line is centred at nozzle X −36.
- So a module 46.6 long centred on the line would span about X −59.3 … −12.7. The current `LIDAR_RESERVED` X range (−62 … −18) may be **too short by about 5 mm on the +X (nozzle) side** if the body is centred on the line. Which way the optics are offset inside the body is unknown, so confirm with a photo or measurement.

### H.3 Pellcorp docs: anything that changes §B and §C

- **No change to the probe findings.**
  - The rendered wiki matches the git source: TOUCH port, 5-pin PicoBlade, GND/5V/PA8/GND/PA9, reachable from the left (LiDAR) side; "All mount options assume a V2 microprobe" (PCW:docs/microprobe.md:60).
  - Pellcorp has no official mount for the rear in-line position (the Default k1m mount is 867527 at x −33).
- **One addition to the fan findings:**
  - The part fan is deliberately `[fan]`, not `[fan_generic part]`, to avoid "move queue overflow" crashes. `M106 P0` is not supported for it; P1/P2/P3 address chamber/auxiliary/chamber (PCW:docs/nozzle_wipe.md:115-116; docs/rpi_faq.md:7-15).
  - `M141` sets the chamber fan's turn-on temperature (PCW:docs/chamber_temp.md:41-55).
  - Nothing new on fan PWM or tach. The part-fan tach (PB3) stays commented out in Pellcorp.
- **New hotend fact:** the K1 filament path from the extruder gears is pipe 23.6 → heatbreak 10.5 → pipe 3 → nozzle 28.3, **65.4 mm total** for the stock ("Unicorn") nozzle; 65.5 mm for a CHCB-OTC. VERIFIED PCW:docs/m600_support.md:46-62 (a user-contributed macro comment).
- The nozzle MCU is `/dev/ttyS7` on K1 (PCW:docs/firmware.md:65). The second board photo (CRA, K1-NOZZLE-M_V12) labels the part-fan connector "Model Fan" with pins GND/PWM/FG/FAN+.

### H.4 Proposed value changes for `cad/source/interfaces.py` (not edited)

| Name | Current | Proposed | Status | Source |
|---|---|---|---|---|
| `REAR_LIMIT_Y` | 30.0 ESTIMATED | **31.0** (adapter rear ≈ 29.1, range 25.4–30.9; rounded up) | ESTIMATED | H.1 (785004 STL + V2 drawing) |
| `PROBE_RETRACTED_MIN_Z` | 2.0 ESTIMATED | add the current-state value **1.45** (stowed tip today) and keep 2.0 only as a design target; flag that the current mount does not meet 2.0 | ESTIMATED | §B.4 |
| `PROBE_MOUNT_FACE_Z` | 26.75 ESTIMATED | unchanged (785004 bottom face = flange seat, so the adapter adds no correction) | ESTIMATED | §B.4, H.1 |
| new `PROBE_ADAPTER_785004` | — | Box X −17.0…+17.1, Y +13.4…+29.1, Z +26.75…+59.25 | ESTIMATED (DERIVED shape, ESTIMATED placement) | H.1 |
| new `PROBE_ADAPTER_SCREWS` | — | 2 × Ø2.4 (≈M2) at X ±12.05, Y +20.1; Ø4.2 counterbore at Z +59.25 | DERIVED / ESTIMATED placement | H.1 |
| new `PROBE_BODY_Y` | — | +12.5 … +28.1 | ESTIMATED | H.1 assumption 3 |
| `PROBE_HOLE_SPACING` | 17.0 VERIFIED | unchanged (785004 measures 16.93) | VERIFIED | BIQU; H.1 |
| `PROBE_SCREW_BORE` (new) | — | Ø3.9 × 8 deep (insert/pilot) if 785004 is reused | DERIVED | H.1 |
| new `LIDAR_BODY_FOOTPRINT` | — | **46.6 (X) × 19.4 (Y)**; height 25–28 | DERIVED (footprint) / ESTIMATED (height) | H.2 (1476318) |
| new `LIDAR_BRACKET_FLANGE` | — | 13.5 × 13.5 × 1.5 sheet; 4-hole diamond: 2 × Ø2.53 csk 8.0 apart + 2 × Ø2.0 8.5 apart; screws driven from above with a **2.0 mm hex key** | DERIVED (holes) / VERIFIED (2 screws, 2.0 mm key) | H.2 (773067; FlowTech PDF) |
| new `LIDAR_BRACKET_PLATE` | — | 35 × ~21 × 1.5; 2 × Ø2.53 csk (Δ 17.0 × 15.0), 2 × Ø1.9 locating (Δ 17.5) | DERIVED (untested replica) | H.2 (773067) |
| `LIDAR_RESERVED` | X −62…−18 | **X −62…−12** until the window and body position are measured (a centred 46.6 body reaches −12.7) | ESTIMATED | H.2 |
| `LIDAR_MASS` (new) | — | MISSING; ≤ 71 g kit upper bound | ESTIMATED | H.2 |
| `FILAMENT_PATH_GEAR_TO_TIP` (new) | — | 65.4 (stock) / 65.5 (CHCB-OTC) | VERIFIED (community) | H.3 |

### H.5 Still open after this pass

- **M8 (probe):** one photo of the adapter on the toolhead (which K1 screws or tabs the two vertical M2 screws and windows use), and the probe pin position relative to its holes (calipers).
- **M6 (LiDAR):**
  - window and emitter positions on the module underside;
  - true body height and its position relative to the line centre;
  - module mass (scale);
  - bracket flange position on the toolhead (X, Y, Z of the 4-hole centre relative to the nozzle).
- **Network:** `store.dremc.com.au` and WebFetch to `pellcorp.github.io` are still blocked. The latter is not needed now (git source plus curl).
