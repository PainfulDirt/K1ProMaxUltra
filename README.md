# K1ProMaxUltra

A Creality **K1 Max** tuned for accurate first layers on a **glass bed**. It runs [Pellcorp's Simple AF](https://github.com/pellcorp/creality) firmware with [Kalico](https://github.com/pellcorp/kalico) and uses two sensors together:

- a **Microprobe V2** for homing and the bed mesh,
- the **stock bed load cells** for nozzle-touch Z.

The repo is the printer's live **Pellcorp config overrides** folder. Pellcorp updates install normally and then re-apply everything here, so the printer stays current and keeps its tuning.

## What's different from a stock Simple AF install

| Problem | What this does |
|---|---|
| The mesh seemed to be ignored on the glass bed | **Adaptive Glass Soak**: when the bed reaches 80 °C, the middle of the glass is 0.16 mm low. It then rises 0.25 mm over ~6.5 minutes, and the edges keep moving for 10+ minutes after that, so a mesh taken right away doesn't match the bed by the first layer. Every 40 s, START_PRINT probes the Z-home spot plus the corners of the print's own footprint (from the object outlines, like the adaptive mesh) until none of them moves. A small print in the middle watches 2 spots; a full-bed print watches 5. |
| Z homing cold, meshing hot | **Hot Z re-home** after the soak, then a mesh with `zero_reference_position` at the Z-home spot. |
| First-layer height depends on the probe offset | **True Zero Touch**: first a **Nozzle Deep Clean** on the rear edge of the bed ([custom/nozzle_wipe.py](custom/nozzle_wipe.py): Creality's `NOZZLE_CLEAR` from the K1 source plus extras, no wipe pads needed). A random start along the strip so old residue isn't picked up again; both ends of the wipe touched with the load cells (mesh off) so it presses 0.15 mm into the real surface; ooze anchored on the PEI while heating to the filament's print temperature; hot drag down into the PEI and scrub passes on fresh lines; a 1 mm retract; cooled to 160 °C pressed into the PEI with the fan so the residue sets on the bed; a slow 5 mm rising peel; a fast flick that snaps off hanging strings. A bad tap (Kalico's tap quality) cleans again on its own, and a touch that still reads early gets one more clean and touch before falling back to the Microprobe. Then it taps the bed at the mesh zero point with the load cells, and that contact becomes Z=0. The Microprobe checks the result, and if the touch reads early (dirty nozzle) it falls back to Microprobe Z instead of trusting it. |
| Where the Microprobe can reach | The Microprobe sits **20.3 mm behind the nozzle, in line on X** (moved 2026-10-06; it used to be 33 mm to the left). The mesh covers the full width, X 5–295 × Y 20–295. Only the front ~20 mm can't be probed, and Klipper holds the front row flat there. |
| The probe behind the nozzle hits the Z rod housings at the back | **Keep-out zones** ([custom/keep_out.py](custom/keep_out.py)): measured by stepping the toolhead back until ~3 mm were left. Blocked for the nozzle: back-left corner X 0–19 beyond Y 292, middle X 130–170 beyond Y 293, back-right X 266–286 beyond Y 302 and X 286+ beyond Y 287. Klipper checks every move: travel moves that would cross a zone are routed in front of it, anything else is refused before it moves. The Orca printers have the same zones (the corners are cut out of the bed shape, the middle is the excluded area), so nothing gets sliced there. The end-of-print park is at Y 270, and the Nozzle Deep Clean strip is at the back-left (X 40–100), where the probe clears the frame. |
| The stock LiDAR is dead under Simple AF (Creality's hotplug script switches it off) | **LiDAR** ([custom/lidar.py](custom/lidar.py), [custom/lidar-start.sh](custom/lidar-start.sh)): at boot the LiDAR is kept powered and the open driver is started ([custom/lidar-direct.py](custom/lidar-direct.py) + [custom/lidar_serial.py](custom/lidar_serial.py), reverse-engineered serial protocol in [custom/LIDAR-NOTES.md](custom/LIDAR-NOTES.md)). It replaced Creality's closed `cx_ai_middleware` (same socket API), which is retired since 2026-11-01: it still ships on the printer but is never started (`LIDAR_DRIVER` restarts the open driver). The plugin moves the toolhead and collects height profiles, about 1500 points across a 29 mm laser line, repeatable to 1–2 µm. Because the plate's texture doesn't move, a bare-plate scan is subtracted from every measurement. **LiDAR PA calibration** (`LIDAR_PA_CALIBRATION`) prints a test as a real print, measures it, and sets the pressure advance it finds. Everything is reduced while scanning (580 bins per profile, plain Python a row at a time), because the K1 has ~200 MB of RAM and a heavy job stalls Klipper. |
| The K1 has ~200 MB of RAM and a slow CPU | **LiDAR work on a helper computer** ([helper/](helper/)): with `service:` in `[lidar]`, a Raspberry Pi (here a Pi 4B, 1 GB) runs `lidar_service.py`. It fetches the point clouds, reduces them, stores the raw captures and runs the analysis. The K1 only moves the toolhead and forwards bytes (`custom/lidar-bridge.py`, over Wi-Fi). Without `service:` everything runs on the printer as before. Klipper itself stays on the K1: a test of the direct Ethernet cable between the two showed link drops and a hung K1 Ethernet port, which would stop a print if the MCUs talked over it. |
| ABS/ASA warping in a cold chamber | **Chamber Heat Soak**: the ABS/ASA Orca profiles pass `CHAMBER_TEMP=45`. With the bed at temperature and the chamber fan held off, START_PRINT waits until the chamber air reaches that. It gives up after 30 minutes so a cold room never blocks a print. PLA/PETG pass 0 and skip it. |
| Printing with filament that was unloaded | **Filament check**: the K1 filament sensor sits before the extruder, so it still reports filament after `UNLOAD_FILAMENT`. `LOAD_FILAMENT`/`UNLOAD_FILAMENT` remember the state, and START_PRINT refuses to start (before heating or homing) until the filament is loaded again. |
| Homing and mesh probes triggering at different heights | The Z homing speed now matches the probe speed. At 1 mm/s vs 5 mm/s they triggered 0.03 mm apart. |
| X-rail wobble | **Axis twist compensation**, measured with nozzle touch against the Microprobe at 7 spots. No paper test. With the Microprobe 20 mm behind the nozzle the twist is ~0.2 mm across X (2026-10-29). `AXIS_TWIST_TOUCH_CALIBRATE` repeats it inside Klipper (forced every 300 h). Drift between its passes (bed or hotend still settling) is fitted out, and a rejected run is retried before the next print. |
| Hotend temperature dips when the fan changes speed | **MPC** (Kalico) instead of PID: 0.5 °C overshoot, ±1.5 °C on a 0→100% fan step. |
| The glass changes how the bed heats | Bed PID retuned at 80 °C with the glass on. The input shaper was re-run too (X 3hump_ei 77.6 Hz, Y ei 52 Hz). |
| Calibrations go stale | **Forced calibration intervals**: print hours are counted, and when a calibration is due it runs automatically before the next print. Input shaper + belt data every 200 h, axis twist (load-cell method, [custom/twist_touch.py](custom/twist_touch.py)) every 300 h, hotend MPC + bed PID every 500 h. Results are used right away where Klipper allows it, and saved (SAVE_CONFIG) automatically ~5 minutes after the print ends. |
| Updates | A **nightly check** writes `UPDATES.md` to the config folder, and there are one-click update macros. See below. |

## Layout

```
tuning.cfg               all the printer-side changes above (included from printer.cfg)
printer.cfg, *.cfg       Pellcorp overrides: only the lines that differ from Pellcorp's files
printer.cfg.save_config  SAVE_CONFIG block: probe offset, input shaper, PID/MPC, meshes
custom/
  twist_touch.py         Kalico plugin: AXIS_TWIST_TOUCH_CALIBRATE (load-cell twist calibration)
  keep_out.py            Kalico plugin: keep-out zones (moves around / refuses moves into them)
  lidar.py               Kalico plugin: LiDAR scans and LiDAR PA calibration
  lidar-start.sh         keeps the LiDAR powered and starts Creality's driver (from k1max-boot.sh)
  lidar-bridge.py        forwards the LiDAR driver to the helper computer
helper/
  lidar_service.py       the LiDAR captures and analysis, on a Raspberry Pi or any Linux box
  k1-lidar.service       systemd unit (set the printer address in it)
  install.sh             installs both on the helper: sh helper/install.sh
  k1max-boot.sh          recreates the plugin link and starts cron (runs at boot via S54k1max)
  check-updates.sh       nightly: Pellcorp/Kalico update check -> UPDATES.md
  update.sh              saves overrides (+ git push), updates, re-links, checks Klipper
orcaslicer/              OrcaSlicer 2.4 profiles for this printer (5 nozzles, 59 processes: Balanced everywhere, Precision (10 mm3/s quality cap) and Fast where they make a difference, plus Speed Benchy profiles (0.4: 12:28, 0.8: 9:14, 1.0: 8:45), 12 filaments)
```

## Switches and buttons

**Switches** are in Fluidd's *Outputs* panel. They decide what START_PRINT does and are remembered across restarts (`variables.cfg`).

| Switch | Default | Off means |
|---|---|---|
| `Adaptive_Glass_Soak` | on | no waiting for the glass to settle before the mesh |
| `Nozzle_Deep_Clean` | on | True Zero Touch happens without cleaning the nozzle first |
| `True_Zero_Touch` | on | no load-cell touch: Z comes from the Microprobe (`z_offset` 0.831, measured with the load cells at bed ~70C, nozzle 150C) |
| `Chamber_Heat_Soak` | on | ABS/ASA prints start without waiting for the chamber to warm up |
| `Forced_Calibration` | on | due calibrations are not run before prints |
| `First_Layer_Check` | off | on: the LiDAR scans the bare plate under the objects before the purge and the first layer when layer 2 starts, and reports the real first-layer thickness (~3 min for a 100 mm part) |
| `First_Layer_Learn` | off | on: the Z offset learned per filament from those checks is applied after the nozzle touch |
| `LiDAR_Mesh` | off (on here since 2026-11-01) | on: START_PRINT meshes with the LiDAR instead of the Microprobe, ~12 min faster, same first layer (see *LiDAR bed mesh*); the Microprobe takes over when the LiDAR can't |
| `LiDAR_Camera` | off | on: the LiDAR's IR camera is a second webcam in Fluidd (see *LiDAR status, camera and stream mode*); off hides it and keeps the fill light off |

Pellcorp's older **Bed_Warp_Stabilisation** (a fixed timer after the bed reaches temperature) is retired: Adaptive Glass Soak replaces it. `k1max-boot.sh` renames it to `_Bed_Warp_Stabilisation`, which hides it in Fluidd, and keeps it off. It does this at every boot and after every update, because Pellcorp updates restore it.

### LiDAR bed mesh

`LIDAR_MESH LEVEL=1-5` (`ADAPTIVE=1` for the printed objects only) meshes with the LiDAR, with its own correction tables (`LIDAR_MESH_CALIBRATION`: X-beam twist and the error along Y). Measured 2026-11-01 on a cold plate (rms differences, raw / with a plane removed):

| Level | | Points | Time (full bed) | vs level 4 | vs level 5 |
|---|---|---|---|---|---|
| 1 | quick, moving 150 mm/s | 7×7 | 22 s | 13 / 13 µm | |
| 2 | fast, moving 120 mm/s | 12×12 | 40 s | 13 / 13 µm | 34 / 19 µm |
| 3 | normal, moving 60 mm/s | 20×20 | 1.8 min | 12 / 12 µm | 35 / 19 µm |
| 4 | fine, 10 strips with the whole laser line | 30×30 | 4.9 min | | 32 / 14 µm |
| 5 | level 4 + 5×5 nozzle touches (load cells), fitted to them | 30×30 | 13.5 min | | |
| Microprobe | 10×11 (Klipper's mesh, axis twist compensation) | | ~13 min | | 16 / 16 µm |

**Along Y the LiDAR reads a slope the nozzle doesn't**: +22 ± 4 µm per 100 mm (~57 µm front to back), measured by `LIDAR_MESH_CALIBRATION` with nozzle touches and LiDAR readings on the same spots, in alternating passes so the printer's drift cancels. Only the slope is kept: each spot's texture scatters ±13-20 µm between the nozzle's touch and the laser's view, more than the effect itself between neighbouring spots. Comparing meshes taken one after the other can't measure it: in the first hour after switching on, the printer itself moved by up to ~35 µm/100 mm between two meshes 20 minutes apart (2026-11-01). 

**Tested with prints (2026-11-01):** 9 pads of 30×30 mm across the bed (X/Y 60, 150, 240), PLA, the first layer of each measured by `First_Layer_Check`, same file and settings, only the mesh changed:

| Mesh | Mesh time | Pads, rms around their mean | X tilt | Y tilt |
|---|---|---|---|---|
| LiDAR level 3, X twist table from 10-29 | 80 s | 21.7 µm | -3.5 | -0.9 µm/100 mm |
| Microprobe, twist table from 10-29 | ~13 min | 14.7 µm | -5.2 | +0.2 |
| LiDAR level 3, both tables measured that day | 80 s | **16.8 µm** | -3.3 | -3.5 |
| Microprobe, twist table measured that day | ~13 min | 17.7 µm | -10.6 | +0.4 |

With fresh tables (`AXIS_TWIST_TOUCH_CALIBRATE` for both X tables, `LIDAR_MESH_CALIBRATION` for the Y line) the LiDAR mesh is as good as the Microprobe's and a print starts ~12 minutes sooner, so it is the mesh this printer uses now. The old X table showed up as ~18 µm between the middle and the sides: rerun the calibrations after changes to the plate, the gantry or the LiDAR. All four prints had the middle column ~30 µm thinner, with either mesh: not the mesh (still open).

With the `LiDAR_Mesh` switch on, START_PRINT runs `LIDAR_BED_MESH LEVEL=<print_level> ADAPTIVE=1 FALLBACK=1` (`variable_print_level` in `LIDAR_MESH`, default 3). The switch is off in a fresh install: run `LIDAR_MESH_CALIBRATION` first. The area always includes the zero reference spot: the LiDAR has no absolute height, so the mesh is made 0 where Z is homed and touched. When the LiDAR can't do it (objects beyond what it sees, X 5–269 × Y 5–265; the service down; a failed scan) the Microprobe meshes instead and the print goes on. `MESH_COMPARE A= B=` compares two profiles, `MESH_BENCHMARK_RUN` all methods on a hot plate.

### LiDAR vs Microprobe

Everything measured on this printer (glass bed + textured PEI, cold plate unless noted), 2026-10-29 to 2026-11-01.

**Speed and reach**

| | LiDAR | Microprobe |
|---|---|---|
| Full-bed mesh | 22 s (7×7) · 40 s (12×12) · 1.8 min (20×20) · 4.9 min (30×30) | ~7 min (9×9) · ~13 min (12×12) |
| Mesh in START_PRINT (9 pads over X/Y 45-255) | 80 s (level 3, 17×17) | ~13 min |
| Whole test print, start to end | 28 min | 40 min |
| Area it can mesh | X 5-269 × Y 5-265 (to X 283 with levels 4-5) | X 5-295 × Y 20-295 |
| Blind spot | the right ~30 mm and the back ~35 mm (the laser looks 36 mm left of and 21 mm in front of the nozzle) | the front ~20 mm (it sits 20.3 mm behind the nozzle) |
| How it measures | looks down, no contact, a 29 mm wide line, ~1500 points per frame | touches each point with a pin, 3 samples |

**Accuracy**

| | LiDAR | Microprobe |
|---|---|---|
| **Against 36 nozzle touches** (`MESH_BENCHMARK`, bed 70 °C, grid tables) | **18.3-18.5 µm rms** (levels 1-3: 21 s, 35 s, 95 s) | **18.9 µm rms** (764 s) |
| Same mesh twice (level 3, 9 min apart) | 9.8 µm rms; level 2 twice: 8.3 µm | not measured |
| LiDAR mesh vs Microprobe mesh (one after the other) | 16-18 µm rms apart | (the same comparison) |
| X-beam twist it sees (the toolhead tips along X) | +0.06 to -0.10 mm across X (in front of the nozzle) | +0.14 to -0.13 mm across X (behind it: opposite sign) |
| Error along Y, against the nozzle | a curve rising ~50 µm front to back on a 70 °C bed (grid), +22 µm/100 mm on a cold one: taken off by its Y table; the same at 60, 70 and 100 °C within 10-14 µm | none seen (prints flat in Y) |
| Absolute height | no: relative, made 0 where the nozzle touches (True Zero) | yes, relative to the Z home |
| Calibration it needs | position (`LIDAR_OFFSET_CALIBRATION`), X twist + Y line (`LIDAR_MESH_CALIBRATION`, ~16 min) | Z offset, X twist (`AXIS_TWIST_TOUCH_CALIBRATE`) |
| Odd results seen | none since the skew fix (2026-11-01); needs the helper computer running (else the probe meshes) | one early trigger in a twist run ("triggered prior to movement", 2026-11-01) |

**First layer, printed** (9 pads 30×30 mm at X/Y 60, 150, 240, PLA, bed 70 °C, thickness by `First_Layer_Check`, sliced 0.200 mm):

| | LiDAR (fresh tables) | Microprobe (fresh table) |
|---|---|---|
| Pads, back row (X 60 / 150 / 240) | 204 / 185 / 199 µm | 222 / 191 / 208 µm |
| Pads, middle row | 196 / 161 / 179 µm | 214 / 168 / 180 µm |
| Pads, front row | 212 / 179 / 216 µm | 219 / 190 / 210 µm |
| Spread, rms around the mean | **16.8 µm** | 17.7 µm |
| Tilt X / Y | -3.3 / -3.5 µm/100 mm | -10.6 / +0.4 µm/100 mm |
| With the twist tables from 3 days earlier | 21.7 µm (an 18 µm X shape) | 14.7 µm |

The mean thickness of a print (192 vs 200 µm here) follows the True Zero touch, not the mesh. The thin middle column (X 150) that showed up with both was the first-layer check itself: the plate's change between its two scans is bowl-shaped and was taken off as a plane. Re-analysed with the curved surface (2026-11-02), the LiDAR-mesh pads spread **6.1 µm rms** (median 0.204 mm for 0.200).

**Buttons** are in Fluidd's *Macros* panel and on the screen. They always run, whatever the switches say.

| Button | Does |
|---|---|
| `ADAPTIVE_GLASS_SOAK` | heats the bed (`BED_TEMP=`, default the current target or 70 °C) and waits until the glass stops moving |
| `NOZZLE_DEEP_CLEAN` | the nozzle clean on its own |
| `TRUE_ZERO_TOUCH` | Nozzle Deep Clean, then set Z=0 by touching the bed with the nozzle |
| `CHAMBER_HEAT_SOAK` | heats the bed (`BED_TEMP=`, default 100 °C) until the chamber air reaches `TEMP=` (default 45 °C) |
| `CALIBRATION_STATUS` | print hours counted and when each forced calibration is due |
| `CALIBRATE_NEXT_PRINT` | `WHAT=shaper\|twist\|heaters\|all`: marks a calibration as due, so it runs before the next print |
| `BACKUP_TO_GITHUB` | saves the config overrides and pushes them here |
| `PRINTER_CHECK_UPDATES`, `PRINTER_UPDATE_PELLCORP`, `PRINTER_UPDATE_KALICO` | see *Updates* |
| `LIDAR_PA_FLOW_CALIBRATION` (also `LIDAR_PA_CALIBRATION`, `LIDAR_FLOW_CALIBRATION`) | `EXTRUDER_TEMP=`, `BED_TEMP=` (default 210/60), `FILAMENT_NAME=` (default: the last printed filament), `X=`/`Y=` (default 100/35; keep X−14…X+24, Y−2…Y+187 clear): one print measured by the LiDAR's **camera**. Inside START_PRINT, before the purge, the Pi picks the exposure for the plate, takes a plate photo and scans 4 bare strips. Then 9 PA lines (PA 0.00–0.08) and 4 groups of 90/100/110 % flow lines are printed, and after a cool-down the camera photographs them (line width to a few µm). PA comes from how the lines bulge after slowing down and thin after speeding up, and is applied and saved (`lidar_pa`). Flow comes from the width of the flow lines × the gap (bare strips vs the mesh) and is saved per filament (`lidar_flow`, applied as M221 at print start). On 2026-11-08 the camera's flow was ~4 % too low (the user's eye preferred 104 % over the measured 108.6 %), so the flow result isn't trusted yet; PA is. Needs the Pi service; the report is `pf-<job>.html` on the Pi. |
| `LIDAR_MESH_CALIBRATION` | calibrates the LiDAR for bed meshes against nozzle touches (load cells): the X-beam twist along Y145 and the error along Y (straight line, from lines at X100 and X200) (~16 min, nozzle at 150 °C, one wipe; keep Y145 and X100/X200 clear). Rerun after changing the plate, the LiDAR mount or the gantry. Best on a bed heated like for a print: the bed heater is off only during each touch. `GRID=7,5` measures a whole grid instead (~25 min): at every point the nozzle taps until 3 readings agree, then the LiDAR looks at the same spot; the difference splits into an X curve and a Y curve over the whole bed (saved) and what is left after both (reported, with suspect points). Method after [Axis Twist Mesh](https://github.com/sterling5241/axis-mesh). Every run is kept with its bed temperature, and every LiDAR mesh uses the weighted mean of all runs on a hot bed (45 °C and up) or on a cold one: grids at 60, 70 and 100 °C agreed within the scatter between runs (10-14 µm), so more runs give better tables. `BED_TEMPS=60,70,100` heats, soaks and calibrates at each of them; `RESET=1` forgets the earlier runs (after changing the plate, the LiDAR mount or the gantry). `LIDAR_TWIST_CALIBRATION AXIS=X\|Y` does one line. |
| `LIDAR_OFFSET_CALIBRATION`, `CREALITY_PA_TEST` | `EXTRUDER_TEMP=`, `BED_TEMP=` (default 250/70): print a 1-layer cross (arms ±7 mm) and find where the LiDAR looks, from camera photos (cross + laser line in the same picture) checked against a LiDAR scan (saved only when both agree within 0.15 mm); or Creality's PA pattern read by eye |

### LiDAR status, camera and stream mode

- `LIDAR_STATUS` shows the module's firmware, serial number and temperature (and, with module firmware 1.0.16 or later, its own timing per frame). `SELFTEST=1` runs the module's laser and fill-light brightness test; `AMBIENT=1` counts the points it finds with the laser off, i.e. room light read as a line (several hundred per frame in a bright room: where the laser is weak, on dark filament, such points can replace real ones).
- Meshes and LiDAR calibrations log the module temperature before and after (console line `LiDAR module 46.0 -> 47.0 C`) and append one line per run to `lidar_runs.jsonl` next to `klippy.log`, for relating the warm-up drift to temperature (the module doesn't compensate for it).
- **Camera.** `lidar-direct.py` serves the LiDAR's IR camera on port 8081 (`http://<printer>:8081/` shows it, `/snapshot` is one JPEG): a ~3 cm wide close-up next to the nozzle, sharp at first-layer height. Only while the `LiDAR_Camera` switch is on, and only when the LiDAR hasn't measured for 10 s (otherwise the last picture comes back); the fill light stays on while somebody watches and is off for every LiDAR measurement. About one picture per second on the stock module firmware (800×300). To see it in Fluidd once: *Settings → Cameras → Add*, service *Adaptive MJPEG-Streamer*, stream and snapshot URL `http://<printer>:8081/snapshot`, name `LiDAR`; the switch then shows and hides that camera.
- **Exposure follows the plate.** A dark or glossy sheet returns much less light: on black smooth PEI the module found only −10…+9 mm of the 29 mm laser line at its default exposure (1000), at 4000 all of it. Every LiDAR job (scan, mesh, first-layer check, calibration) now has the Pi pick the lowest exposure that sees the whole line (1000/2000/4000/8000), once per print or command. The measured height doesn't change with exposure (within 2 µm on bare plate).
- **Thin translucent lines.** The LiDAR reads thin white lines too low (the laser light spreads inside the plastic; a 0.2 mm line read 0.11–0.19 mm), and a single white layer on black PEI reads ~0.035 mm thin. The camera measures line widths instead (PA/flow calibration, offset cross).
- `LIDAR_STREAM_MODE MODE=1` lets the module capture continuously (10.7 instead of 5 frames/s). It isn't the default: dwell scans only got ~15 % faster (moves dominate) and meshes were ~12 µm rms noisier. Each mode keeps its own `LIDAR_TIMING`.
- The driver refuses the commands that would change the module for good: Creality's sticker calibration, factory restore, firmware update, baud rate and watchdog settings (written to the module's flash), and the deliberate hang.

## Updates

- **Every night at 4:00**, the printer checks Pellcorp and Kalico for new commits. Nothing is installed automatically. The result goes to `UPDATES.md`, visible in Fluidd under Configuration, and a message appears when the printer is idle. It also says when a Kalico update includes new MCU firmware (which needs a power cycle).
- **`PRINTER_UPDATE_PELLCORP`** / **`PRINTER_UPDATE_KALICO`**: these refuse to run while printing. Otherwise they save the overrides (committing and pushing them here), update, restore the plugin link, and report whether Klipper came back `ready`. The log is `logs/k1max_update.log`.
- **`PRINTER_CHECK_UPDATES`** runs the check on demand.

## Backups to this repo (from the printer itself)

`/usr/data/pellcorp-overrides` on the printer is a git checkout of this repo. Pellcorp's `CONFIG_OVERRIDES` (also run by the update macros) commits and pushes whenever something changed, so this repo always matches the printer.

The printer pushes with its own **deploy key**, which works for this repo only. K1 firmware ships an old dropbear (2019.78), which has two quirks:

- RSA keys sign with SHA-1, which GitHub rejects for git operations (though `ssh -T` still says hello). Use an **ECDSA** key: `dropbearkey -t ecdsa -s 256 -f /usr/data/.ssh/k1max_github_ecdsa`, then add the public part (`dropbearkey -y -f ...`) under *Settings → Deploy keys* with write access.
- git assumes OpenSSH options that dropbear doesn't understand, so set:
  ```
  git config core.sshCommand "dbclient -i /usr/data/.ssh/k1max_github_ecdsa -y"
  git config ssh.variant simple
  ```

## What you need

- **Simple AF** (Pellcorp) from September 2026 or later, installed with the Microprobe option. This build's `S13mcu_update` can also flash the bed MCU.
- **Kalico instead of Klipper**, on Pellcorp's `aug2026` branch, which has the multi-chip `hx711s` load-cell driver and `register_as_probe: False`:
  ```
  cd /usr/data/pellcorp && sh ./installer.sh --klipper-repo kalico aug2026
  ```
  Then **switch the printer off and on**. That flashes the main, nozzle and bed MCUs (bed firmware `bed0_121` or newer has the HX711 support). Check `/usr/data/mcu.versions` afterwards.
- A **Microprobe V2**. The stock load cells stay in place; they're only used for the nozzle touch.

## Using this on your own K1 / K1 Max

This is one specific printer, so read `tuning.cfg` before copying anything. The values **tied to this hardware** are:

- `[probe]` / Microprobe: `x_offset 0`, `y_offset 20.3`, `z_offset` (SAVE_CONFIG, measure it with the load cells: nozzle contact vs Microprobe at the same spot), `zero_reference_position` (the probe position while homing Z: nozzle 153,153 → 153,173.3), and `mesh_min`/`mesh_max` (the probe's reach)
- `[load_cell_probe]`: the load-cell settings. The leveling board needs Pellcorp's Kalico **bed MCU firmware with HX711 support** (bed0_121 or newer). The pins are the stock K1 ones. `reference_tare_counts` must be measured on your printer (read `force_g` with the bed empty). `counts_per_gram` is Pellcorp's K1 value.
- `[axis_twist_compensation]` values (SAVE_CONFIG block), Adaptive Glass Soak thresholds (`_GLASS_SOAK`), the Nozzle Deep Clean strip location (`[nozzle_wipe]`, X 40–100 at Y 297.4–298.6), and the `[keep_out]` zones (measure your own: they depend on the probe mount)

Rough steps on a Simple AF printer that has Kalico and the load-cell bed firmware:

1. Copy `custom/` to `/usr/data/pellcorp-overrides/custom/` and run `custom/k1max-boot.sh`. This has to come **first**: `tuning.cfg` has `[twist_touch]`, `[keep_out]` and `[lidar]` sections, and Klipper won't start until the plugins are linked in.
2. Copy `tuning.cfg` to `printer_data/config/` and add `[include tuning.cfg]` to `printer.cfg`, after the probe includes.
3. Change the hardware-specific values above, restart, then run `CONFIG_OVERRIDES` so updates keep your changes.

## Roadmap

**LiDAR** (done: LiDAR PA calibration, LiDAR offset self-check, first-layer thickness check, LiDAR bed mesh levels 1-5 used by START_PRINT, combined probe + LiDAR twist calibration, XY skew, open driver with the middleware retired)
- **True first-layer thickness: done (2026-10-29).** `First_Layer_Check`: bare plate before, first layer after, the difference is the real thickness (test print 0.194 mm for 0.200). Since 2026-11-01 a short prime line in front of the objects refills the nozzle after the pause for the scan, so layer 2 starts clean (`PRIME=3` mm). Since 2026-11-02 the plate's own change between the two scans may be curved: the bare plate between and around the objects showed a bowl of 40-60 µm (middle lower) on the 9-pad test prints, which made the middle look 25-38 µm too thin. With bare plate inside the objects' area (gaps between parts or islands) a quadratic surface comes off instead of a plane; the pads then spread 6-8 µm rms instead of 16-23, and the Microprobe (pad minus plate) agrees. Left: store the PLA line ramp per filament for parts under 40 mm.
- **First-layer diagnosis: LiDAR + camera.** The first-layer check's thickness can't tell a nozzle that is too high from too much plastic: on a 6-pad test (2026-11-02) Z +0.05 mm read 0.225 mm and flow 115 % read 0.231 mm. The LiDAR's camera tells them apart: with the nozzle too high the lines stay round and bare PEI sparkles between them (1.55 % of the picture vs 0.38 % for flow 115 % and 0.37 % for the reference). Next: repeat the test, then let First_Layer_Learn change the Z offset only when the photo shows gaps, and report flow otherwise.
- **Flow / extrusion multiplier: camera width works relatively, not yet absolutely (2026-11-08).** Inside a group of lines at the same nozzle height the camera width follows the flow (+36…54 µm per +10 %), but the absolute flow came out ~4 % low against a printed A/B check (pads at 100/104/108.6 %: 104 % looked best). Next idea: find the flow where a short single-layer band is flattest (camera: gloss, no ridges, no gaps), independent of the gap and the edge definition. The 5-layer pad test (below) can't work: thickness is pinned by the nozzle under ~100 %. Earlier plan: measure single-line cross-sections (height × width) against what was commanded, per filament. The PA test already measures these areas. Better (planned 2026-11-02): count volume. Bare-plate scan, print a solid pad of ~1 mm (5 layers) from self-generated G-code (so the commanded E is known exactly), scan again; the height difference summed over the pad is the printed volume, and printed / commanded volume is the real flow ratio. It doesn't depend on the nozzle height (too high leaves gaps, too low pushes ridges, the volume stays the same), and on 1 mm the scan's ~5 µm leftover error is ~0.5 %. Two or three pads at different flows (0.95 / 1.00 / 1.05) show that it follows. Check the LiDAR's height scale first (scans at known Z steps: a 2 % scale error is a 2 % flow error), measure inside the pad (the steep edges can hide from the LiDAR's camera) and after a fixed cool-down (shrink). The LiDAR camera's pictures (IR capture works since 2026-11-02) can cross-check gaps and line width.
- **Bed mesh: done (2026-10-29, in START_PRINT 2026-11-01).** LiDAR mesh levels 1-5 agree with the Microprobe to 17 µm rms once both have their own twist table; the `LiDAR_Mesh` switch makes START_PRINT use it, with the Microprobe as fallback. Y correction (2026-11-01): `LIDAR_MESH_CALIBRATION` measures the LiDAR's slope along Y against the nozzle (+22 ± 4 µm/100 mm) besides the X twist. Printed A/B the same day: with fresh tables the LiDAR mesh matched the Microprobe (16.8 vs 17.7 µm rms over 9 pads) and is START_PRINT's mesh now. Left: `MESH_BENCHMARK_RUN` on a hot, settled plate to see whether level 2 is enough, and why the middle of the bed prints ~30 µm thin with either mesh.
- **Strings and blobs before a print.** A quick scan of the print area after the purge; warn or stop if something is lying where the part goes.
- **Axis twist: done (2026-10-29).** The probe (behind the nozzle) and the LiDAR (in front) see the X-beam twist with opposite signs; nozzle touches calibrate both tables in one run (`LIDAR_TWIST_CALIBRATION`).
- **Faster scanning, part 2.** Done so far (2026-10-07): with the helper service, scans plan their rows just ahead of the toolhead and take one frame per row standing still ("dwell" mode), 0.38 s per row instead of 1.3 s, equally repeatable (15.5 vs 14.5 µm between passes). Measured limits: the LiDAR delivers ~4.3 frames/s, and a frame is ~0.19 s old when it arrives. Scanning while moving was tried and dropped: textured PEI changes by ~76 µm between rows only 0.1 mm apart, so frames have to be taken at exactly the same Y in both scans. Locking the pauses to the LiDAR's frame rhythm: done (2026-10-12, below). Left: using every point's own Y and full X resolution on the helper.
- **Open LiDAR driver: done (2026-10-12).** `lidar-direct.py` drives the LiDAR without Creality's closed `cx_ai_middleware` (same results, ~15 % more frames/s, 5 % CPU). Dwell scans are locked to the LiDAR's frames (`LIDAR_TIMING` measures them): one row per frame, a 51-row scan in 12-14 s instead of 20-21 s. The middleware is retired since 2026-11-01 (never started; still on the printer as a manual last resort). Left to try: 2.5 Mbaud on the serial link, possible only without the middleware.
- **LiDAR reports on the helper computer.** The Pi already runs the LiDAR service, keeps the raw scans and writes a height map per fine mesh (`/var/lib/k1-lidar/heightmap-*.json`): add pages to view them and their history.
- **Klipper on the helper computer.** Only if the direct cable proves stable in a long soak test (another cable; the K1's Ethernet hung after link drops on 2026-10-07): bridge the three MCU UARTs to the Pi.

**More calibrations** (ideas; pressure advance and input shaper/belts are already handled). Uses the accelerometer, the LiDAR or the load cell, so none of them needs a ruler or the eye.
- **VFA speed sweep (accelerometer, no print).** VFA (vertical fine artifacts, the fine regular ripples on walls) mostly comes from the stepper motors: the ripple period is the distance of a motor's electrical cycle (0.8 mm on a 20T GT2 pulley with 200-step motors), so it shows up at the speeds where `speed / period` hits a belt or frame resonance. Move at constant speed from 20 to 300 mm/s in small steps along X, Y and both diagonals, record vibration, and list the speeds with a peak. Result: speeds to avoid (or a wall speed picked between peaks) and a quick before/after number for every change below.
- **VFA stepper settings, A/B with the same sweep.** Compare `interpolate` on/off, microsteps (16 vs 32 vs 64), StealthChop vs SpreadCycle and run current. Pick the quietest, keep the result in `variables.cfg`.
- **VFA seen by the LiDAR.** The LiDAR looks down, so a vertical wall is invisible to it. A shallow slope (~20°) turns the ripple into a height wave on top. Print one, scan it, take the spectrum along the slope: shows the real period and amplitude, and whether it is the motors (fixed period) or the extruder (period follows the extruded length).
- **Extruder ripple check.** The same scan separates the extruder gear (one ripple per gear turn of extruded filament) from the motors. If it is the extruder, that is a `rotation_distance`/gear problem and not a speed one.
- **Max volumetric flow.** Print a line with rising speed and scan its cross-section: the speed where the area stops following the commanded flow is the real limit per filament and temperature. The slicer value comes from this.
- **Skew / squareness: done (2026-10-30).** `SKEW_SCAN` (a printed square, scanned twice, turned a quarter turn in between) and `SKEW_CALIBRATE`: -0.20° (-0.35 mm per 100 mm), saved as skew profile `lidar` and loaded at boot. Left: the shrink factor per filament (printed size vs commanded).
- **Retraction.** Print two posts, scan the gap for strings, and step distance and speed to the lowest value that stays clean. Shares the "strings and blobs" scan above.
- **Ringing tower measured, not looked at.** Accelerometer on the toolhead during real corners at set acceleration and square corner velocity, to choose acceleration per axis from numbers.
- **Sensorless homing threshold.** The stall threshold (`SGTHRS`) auto-tuned by homing at several speeds and temperatures, picking the middle of the range that works.
- **Load cell `counts_per_gram`.** Weigh a known mass (a 100-500 g calibration weight) once; today the grams are approximate (see Known limitations).
- **Z lead screw error.** Step Z in small increments over the LiDAR's working range and compare the measured plate distance with the commanded move; a repeating error is the cause of Z banding. Only covers the first few mm, so a period seen there is a hint, not proof.

**Fun with the LiDAR camera** (IR capture works since 2026-11-02: JPEG 800×600 or 1600×1200, or a raw 1600×600 frame, 1-4 s each, ~3 cm wide, sharp at scan height)
- **Microscope mosaic.** Pictures in a grid over a print, stitched on the Pi into one ~20 µm/pixel image of the whole first layer.
- **Photo draped on the height scan.** The mosaic over the LiDAR height map of the same area, as a 3D view in the browser.
- **Snapshot in Fluidd: done (2026-11-02).** The camera is a second webcam in Fluidd, switched with `LiDAR_Camera` (see *LiDAR status, camera and stream mode*).
- **XY from the plate texture.** Pictures of the PEI before and after a move, matched against each other: the real travel to a few µm (skew, step length) without printing.

**Other**
- **Silicone wipe pads** (K2 Plus) for the Nozzle Deep Clean.

## Known limitations

- The nozzle wipe can still leave a thin string hanging off the side of the nozzle. It doesn't affect the touch (the Microprobe check shows a clean contact), and the purge line picks it up. A silicone brush at the back edge would be the proper fix.
- The LiDAR position is measured by `LIDAR_OFFSET_CALIBRATION` (a printed cross, scanned at Z3 and Z5; saved in `variables.cfg`, overrides `[lidar]`). Rerun it after changing the plate or the LiDAR mount. Lines along X read up to ~0.3 mm off in Y (see LIDAR-NOTES), lines along Y are exact in X.
- `counts_per_gram` was not weighed on this printer, so load-cell forces in grams are approximate. The touch height doesn't depend on it.

## OrcaSlicer profiles

`orcaslicer/`: import `K1Max-Tuned-OrcaSlicer-profiles.zip` with *File → Import → Import Configs*, then set your printer's address in the printer profile (Connection). See [orcaslicer/README.md](orcaslicer/README.md) for what's inside and why. They match the printer side: the start G-code is just `START_PRINT` (with the filament's chamber temperature: 45 °C for ABS/ASA), layer progress is reported, object labels are on (for the adaptive mesh), jerk is 0 so the corner velocity the input shaper was tuned for is kept, and arc fitting is off.

## Credits

- [Pellcorp / Simple AF](https://github.com/pellcorp/creality), [Kalico](https://github.com/KalicoCrew/kalico), and Pellcorp's [load-cell work](https://github.com/pellcorp/creality/issues/1500) built on OpenCentauri's hx711s driver
- The LiDAR grid calibration (`LIDAR_GRID_CALIBRATE`) follows [Axis Twist Mesh](https://github.com/sterling5241/axis-mesh) by sterling5241: its agreeing-taps method and its analysis (X curve, Y curve, interaction, suspect points, edge checks), used with the author's permission
- `twist_touch.py`, `keep_out.py` and `lidar.py` are GPLv3, like Klipper and Kalico

Use at your own risk. This drives a hot nozzle into the bed on purpose.
