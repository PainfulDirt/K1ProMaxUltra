# Post-install calibration

The calibration procedure after fitting the new cooling module, cover and (later) the probe
mount on **this** K1 Max. It uses the printer's own macros (`tuning.cfg`, `custom/*.py`, the repo
`README.md`). Baselines are the values in the repo today:

| Baseline | Value | Source |
|---|---|---|
| Probe offset | x 0, y +20.3 | `tuning.cfg` `[probe]` |
| Probe `z_offset` | **0.831** | `printer.cfg.save_config` |
| Load-cell `z_offset` | −0.02 | `tuning.cfg` `[load_cell_probe]` |
| Input shaper | X **3hump_ei 77.6 Hz**, Y **ei 52.0 Hz** | `printer.cfg.save_config` |
| Projected max accel | X ≈ 4408, Y ≈ 5036 mm/s² | research/01 §D (ESTIMATED reimplementation) |
| MPC | block_heat_capacity 16.36 J/K; sensor_responsiveness 0.0917; ambient_transfer 0.0800 W/K; fan_ambient_transfer 0.0800 → **0.1166** (0 → 100 %) | `printer.cfg.save_config` |
| MPC control | 0.5 °C overshoot, ±1.5 °C on a 0 → 100 % fan step | README |
| Probe twist | z_compensations **+0.1327 … −0.1339** (range **0.267 mm**), X 10–290 | `printer.cfg.save_config` |
| LiDAR offsets | X **−36.013**, Y **−21.336**, x_per_z 0.0354, y_per_z −0.986 | `variables.cfg` |
| LiDAR twist | comp **+0.0805 … −0.1007** (range **0.181 mm**), pass spread **0.0118** | `variables.cfg` `lidar_twist` |
| LiDAR distance at touch | 22.599 mm (bed 69.8 °C, nozzle 150 °C) | `variables.cfg` `lidar_zero_log` |
| PA (0.4 nozzle) | PLA/ASA/ABS 0.04, PETG 0.046 | `orcaslicer/README.md` |
| Keep-out zones | zone1 X130–170 > Y293; zone2 X−10–19 > Y292; zone3 X266–286 > Y302; zone4 X286+ > Y287 | `tuning.cfg` `[keep_out]` |

Tolerances marked ESTIMATED are my engineering judgement, not measured repeatability. Tighten
them once the first post-install runs are logged.

## 1. What changes and what does not

| Item | Changes? | Why | Still check? |
|---|---|---|---|
| Probe x/y offset | no | probe position kept (DD-03); a new probe mount copies 785004's anchor-to-probe relation | no re-measure. The z_offset check below would reveal a shift |
| Probe `z_offset` | maybe a little | same probe pose, but a different thermal environment (new duct airflow), and a new mount if one is fitted | **yes**, load-cell method (step F) |
| `zero_reference_position`, `mesh_min/max`, `screws_tilt_adjust` | no | follow from the probe offset | no |
| LiDAR pose, offsets, `custom/lidar.py` reach values | no | module and bracket untouched (DD-02) | **yes**, a quick dry-run check (step G), because the cover swap happens right next to the bracket |
| Axis twist (probe and LiDAR) | probably small | pitch behaviour depends on toolhead mass and CG; the mass delta is −7.3 … +1.6 g (validation report) | **yes** (step H) |
| Keep-out zones | no, if nothing reaches behind Y +29.1 | new parts end at Y −22.3 (frame); the probe mount rear is 29.10 vs 29.1 for 785004 (validation report) | **verify** (step D), and re-measure if a rear part changed |
| Front/side clearance | **yes** | new cover front −58.7 vs stock −55.0 (validation WARN; −58.2 with the duct v1) | **yes** (step D) |
| Input shaper | small | predicted X 77.5–78.2 Hz, Y 51.95–52.23 Hz (validation report) | **yes** (step H). Also watch for a frame mode near 150 Hz (validation WARN: 147 Hz without the 4th pad) |
| MPC fan model | **yes** | `fan_ambient_transfer` is duct-specific (DD-05, research/03 §3) | **required** (step E) |
| Bed PID | no | bed unchanged | runs anyway with `WHAT=heaters` |
| PA | barely | hotend and extruder unchanged | spot-check (step J) |
| ADXL `axes_map` | no | PCB orientation unchanged | no |
| Orca bed shape, nozzle-wipe strip, park positions | no | they follow the keep-outs | no |

## 2. Order of operations

| Step | What | Printer hot? | Approx. time |
|---|---|---|---|
| A | Baseline capture (before disassembly) | yes | 20 min |
| B | Install, cold checks | no | — |
| C | Fan config and fan function test | no | 10 min |
| D | Clearances and keep-outs, motors on, slow | no | 15 min |
| E | MPC re-calibration (+ fan-step test) | yes | 15–25 min |
| F | Probe z_offset via the load cells | yes | 15 min |
| G | LiDAR offset check (`LIDAR_OFFSET_CALIBRATION APPLY=0`) | yes (prints a cross) | 10 min |
| H | Twist (probe + LiDAR) and input shaper, via `CALIBRATE_NEXT_PRINT` and one sacrificial print | yes | 30 min |
| I | Apply LiDAR offsets only if step G says so, then repeat the LiDAR twist | yes | 15 min |
| J | PA spot-check (`LIDAR_PA_CALIBRATION`) | yes | 15 min |
| K | First-layer checks | yes | one print |
| L | Save and back up | — | — |

Why this order:
- MPC goes first among the hot steps, because the nozzle wipe and every later step use the part
  fan.
- z_offset comes before any print, because True Zero Touch falls back to Microprobe Z when the
  touch differs from the probe by more than −0.03 / +0.15 mm (`_LOAD_CELL_TOUCH_Z`).
- The LiDAR offsets are checked before the LiDAR twist, because the twist uses them.

### A. Baseline capture (stock cover still fitted)

1. `BACKUP_TO_GITHUB` and note the commit hash. This is the rollback reference (§5).
2. `CALIBRATION_STATUS`: note the print hours and when each calibration is due.
3. `LIDAR_OFFSET_CALIBRATION APPLY=0`: note the reported X/Y offsets and arm lengths. This gives
   the run-to-run noise of the check on the untouched printer.
4. Optional, closes M13: `SHAPER_CALIBRATE` with and without a ~50 g mass taped to the toolhead.
   Keep the CSVs.
5. Optional: `MEASURE_AXES_NOISE` (ADXL baseline for the buck EMI check, `electrical.md` §3.4).
6. Weigh the stock cover + 4020 on a kitchen scale (M12).

### B. Install, then check cold (motors off)

- PCB screws: replace the stock screws **one at a time** with the 3 × M3×30 (`bill-of-materials.md`),
  so the PCB and 3010 stay located. Tighten snug only.
- Nothing touches the LiDAR module, its bracket or its windows. The left cover wall must clear the
  module by ≥ 0.5 mm (validation: cover vs `LIDAR_RESERVED_BODY` 0.50 mm). Look along the laser
  sheet: no part, cable or tie may hang below the module.
- `PROBE_DOWN`, `QUERY_PROBE`, `PROBE_UP`: the pin deploys and retracts freely, and its lead is not
  pulled by the new tie points.
- Duct lowest point ≥ 2.0 mm above the nozzle tip (`DUCT_MIN_Z`). Check with a 2 mm drill shank
  under the duct while the tip sits on a flat block.
- Cables: the probe lead goes to the TOUCH port from the left; the fan lead is tied at the frame's
  right top corner. Nothing may rub the X rods or belts.

### C. Fan config and function test

1. Include the variant snippet (`electrical.md` §7), then `FIRMWARE_RESTART`.
2. `M106 S26`, `S77`, `S128`, `S255`, then `M107`: the fan starts every time, and speed rises
   monotonically. If a tach is wired, read the rpm in Fluidd: it should be within ±15 % of the
   datasheet speed at S255 (ESTIMATED tolerance; datasheet ±10 %).
3. Heat the nozzle to above 40 °C: the 3010 hotend fan starts (unchanged channel; its tach reads in
   Fluidd).
4. Tune `off_below` and `kick_start_time` (`electrical.md` §5.5) **now**, before MPC.

### D. Clearances and keep-outs (motors on, speed F600, a finger on the e-stop / power switch)

1. `G28`, then lift Z to 50 (`G0 Z50 F600`).
2. **Front:** `G0 X150 Y0`, then step to Y −2 in 0.5 mm steps. The gap from the cover/duct front to
   the door and frame must be ≥ 2 mm (ESTIMATED). If it is not, stop: the Y minimum must change
   (Pellcorp base config). Report it, because it is the M9 open point.
3. **Left / right:** at Y 150, step to X −2 and X 306.5 at Z 50 and at Z 5. Gap from the cover,
   duct and fan to the XY joints ≥ 1 mm (ESTIMATED). The cover is ±24.0 against `RIGHT_LIMIT_X`
   24.2 in the joint band, and the duct v1 reaches X +31 below that band.
4. **Rear keep-outs, only if a part behind the nozzle changed** (new probe mount, or anything past
   Y +29.1): move the nozzle to each point below in 0.5 mm steps and check the gap between the
   rearmost toolhead part and the Z-rod housing. Today's zones were measured with ~3 mm left.

| Point (nozzle X, Y) | Zone it guards |
|---|---|
| 150, 292 | zone1 (middle housing) |
| −2, 291 | zone2 (left corner) |
| 286, 301 | zone3 (right housing) |
| 306.5, 286 | zone4 (right corner) |

   Accept a gap of 2–4 mm (ESTIMATED). If it is less than 2 mm, re-measure that zone the way the
   `tuning.cfg` comment describes, and update `[keep_out]` plus the Orca bed shapes
   (`orcaslicer/make_profiles.py`). If it is more than 5 mm, leave the zones alone (conservative).

### E. MPC re-calibration (required after any fan or duct change)

1. With the printer cold and the chamber at room temperature:
   `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7`, then `SAVE_CONFIG`.
   - Alternative: `CALIBRATE_NEXT_PRINT WHAT=heaters`. It runs MPC + bed PID (~25 min) at the next
     START_PRINT and saves 5 min after the print ends. Use this only if you can wait until after
     step H, since the nozzle wipe and every touch run on the old fan model until then.
2. Fan-step test: `M109 S250`, wait 2 min, then `M106 S255`, then after 2 min `M107`. Watch the
   extruder graph.

| Quantity | Pass | Basis |
|---|---|---|
| block_heat_capacity | 16.36 ± 10 % | hotend unchanged (ESTIMATED tolerance) |
| sensor_responsiveness | 0.0917 ± 15 % | ESTIMATED |
| ambient_transfer (fan 0) | 0.0800 ± 10 % | ESTIMATED; the new cover changes natural convection a little |
| fan_ambient_transfer at 100 % | record it. **≤ 0.1166 expected** if the duct aims below the block as designed. **> 0.14** (fan adds > 75 % heat loss) means air is hitting the block: check the sock and the duct aim | ESTIMATED |
| Fan-step deviation | ≤ ±1.5 °C, overshoot ≤ 0.5 °C | README baseline |

### F. Probe z_offset via the load cells

True Zero Touch reports `Z=0 set by the nozzle (±d mm vs Microprobe)`, where
d = probe reading − `[probe] z_offset` − load-cell `z_offset` (`_LOAD_CELL_TOUCH_CHECK`). The true
probe offset is therefore **0.831 + d**. The macro does the touch under the conditions the offset
was measured in: bed ~70 °C with the heater off, nozzle 150 °C, after the wipe.

1. Heat the bed to 70 °C and run `ADAPTIVE_GLASS_SOAK BED_TEMP=70`.
2. Run `TRUE_ZERO_TOUCH` **5 times** and note each d. If a run says "dirty nozzle", it does not
   count.
3. Median of d = d̃. If |d̃| > 0.010:
   `SET_GCODE_OFFSET Z={-d̃}`, then `Z_OFFSET_APPLY_PROBE`, then `SET_GCODE_OFFSET Z=0`, then
   `SAVE_CONFIG`. `Z_OFFSET_APPLY_PROBE` subtracts the G-code offset from the probe z_offset, so
   the new value is 0.831 + d̃.
4. Run `TRUE_ZERO_TOUCH` 3 more times.

| Check | Pass | Basis |
|---|---|---|
| \|d\| after the update | ≤ 0.010 | `_LOAD_CELL_TOUCH_Z` comment: "a clean touch reads within ~0.01 of zero" |
| Spread of the 3 values | ≤ 0.010 | probe spread 0.005 typical (`tuning.cfg`); touch noise ~3 µm |
| Change vs 0.831, probe mount unchanged | ≤ 0.05 | ESTIMATED (thermal environment only) |
| Change vs 0.831, new probe mount | ≤ 0.5 | research/01 §B.4 (mount-face tolerance) |
| Change > 1.0 | **stop**: outside DD-03's envelope; the probe mount is wrong | DD-03 |

### G. LiDAR offset check (dry run)

1. Clear the plate around X 135–165, Y 133–167.
2. Run `LIDAR_OFFSET_CALIBRATION APPLY=0`. It prints a cross, scans it at Z3 and Z5, and reports
   without saving.

| Result vs `variables.cfg` | Meaning | Action |
|---|---|---|
| \|ΔX\| ≤ 0.10, \|ΔY\| ≤ 0.30, per-Z slopes within ±0.02 (X) / ±0.05 (Y), arms 20.1–20.3 mm (LIDAR-NOTES). The ΔX and slope limits are ESTIMATED | unchanged. The Y limit is wider because lines along X read up to ~0.3 mm off in Y (README, LIDAR-NOTES) | **nothing to apply** |
| Outside that, but < 5 mm | the bracket was disturbed during the cover swap | re-seat or check the bracket screws (2.0 mm hex), then `LIDAR_OFFSET_CALIBRATION` (APPLY=1), then the LiDAR twist (step I) |
| "more than 5mm from the current one, not applied" | the macro refuses any change > 5 mm in X or Y (`custom/lidar.py`). The module has moved or rotated | **stop**. Do not delete the saved offsets to force it. Restore the module pose (DD-02). Never run Creality's sticker calibration with the glass plate fitted |
| "implausible change with height" | per-Z slopes are outside the macro's limits (\|kx\| > 1, \|ky\| > 3) | check that nothing has entered the laser sheet (step B), then repeat |

Compare ΔX/ΔY against the step A dry run. A difference smaller than the A-vs-baseline noise is
not a change.

### H. Twist and input shaper (one sacrificial print)

1. Make sure the `Forced_Calibration` switch is on.
2. Run `CALIBRATE_NEXT_PRINT WHAT=twist` and `CALIBRATE_NEXT_PRINT WHAT=shaper`.
   (`WHAT=heaters` too, if step E was skipped.)
3. Print something small in PETG or PLA (e.g. a 20 mm cube) with `First_Layer_Check` on.
4. During START_PRINT:
   - the shaper + belt data run after G28 (~6 min);
   - `AXIS_TWIST_TOUCH_CALIBRATE` runs after the glass soak and hot Z re-home (~15 min). It also
     measures the LiDAR twist, because `[lidar] service:` is set (`custom/twist_touch.py`).
5. The results are saved by `SAVE_CONFIG` ~5 min after the print ends (`_CALIB_SAVE`; Klipper
   restarts). The belt graph goes to `config/images/belts_calibration.png`.

| Check | Pass | Basis |
|---|---|---|
| Probe twist applied | "Axis twist: … pass spread ≤ 0.040" (`max_pass_diff`); otherwise it is not applied and retries | `tuning.cfg` `[twist_touch]` |
| Probe twist range | 0.267 ± 0.03 mm, same sign pattern (+ at X10, − at X290) | baseline; ESTIMATED tolerance |
| Probe-nozzle offset printed by the twist run | within ±0.01 of the new z_offset | cross-check of step F |
| LiDAR twist saved | pass spread ≤ 0.040 (not saved otherwise); expect ≈ 0.012 like the baseline | `twist_touch.py`; baseline |
| LiDAR twist range | 0.181 ± 0.03 mm | baseline; ESTIMATED tolerance |
| Shaper X | ≥ **76.0 Hz** (DD architecture target), expected 77.5–78.2 | DD comparison table; validation report |
| Shaper Y | 51–53 Hz, expected 51.95–52.23 | validation report; ±1 Hz ESTIMATED repeatability |
| Projected max accel X | ≥ ~4300 mm/s² (baseline 4408) | research/01 §D |
| X response graph | no new peak at 100–200 Hz. A peak near 150 Hz is the frame's fan-plate mode without the 4th pad (validation WARN 147 Hz) | validation report |
| Belt graph | both belt curves still overlap as before | — |

If X is below 76 Hz, check for loose fan, duct or cover screws (a rattle shows as a broad peak).
Then run the M13 mass test and report it.

### I. LiDAR twist re-run (only if step G applied new offsets)

`LIDAR_TWIST_CALIBRATION` (homed, clear plate along Y 145). Same pass criteria as the LiDAR rows in
step H.

### J. Pressure advance spot-check

`LIDAR_PA_CALIBRATION` (default 250 / 70, PETG; keep X 130–154, Y 100–220 clear). For ASA:
`LIDAR_PA_CALIBRATION EXTRUDER_TEMP=260 BED_TEMP=100`.
Pass: within ±0.01 of the profile value (0.046 PETG; 0.04 ASA/PLA). The extruder and hotend are
unchanged, so a bigger shift means something else changed. If it holds, put the new value in the
Orca filament profile.

### K. First-layer checks

1. With `First_Layer_Check` on and `First_Layer_Learn` **off** (so the raw error is visible), print
   a large single-layer test, the same kind that set the load-cell `z_offset −0.02`.
2. Read the Pi report (`/var/lib/k1-lidar/firstlayer/fl-<id>.html`).

| Quantity | Pass | Basis |
|---|---|---|
| Median thickness − sliced height | within ±0.02 mm | ESTIMATED |
| Clean-measurement gates | ≥ 100 cells, p95−p05 ≤ 0.15, bare rms ≤ 0.03 | LIDAR-NOTES (learning gates) |
| Thickness tilt (mesh error) | ≤ 20 µm / 100 mm | ESTIMATED |
| Visual | even squish over the whole bed, no ridges at the front (the probe cannot reach the front ~20 mm) | README |

### L. Save and back up

`SAVE_CONFIG` if anything is still pending, then `CONFIG_OVERRIDES` / `BACKUP_TO_GITHUB`. Record
the new values in a commit message. Run `CALIBRATION_STATUS`: the H steps reset their counters.

## 3. `CALIBRATE_NEXT_PRINT` shortcuts

| Command | Runs at the next START_PRINT | Time | Saved |
|---|---|---|---|
| `CALIBRATE_NEXT_PRINT WHAT=heaters` | `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7` + bed `PID_CALIBRATE` (at the print's bed temp, else 80) | ~25 min | SAVE_CONFIG ~5 min after the print |
| `CALIBRATE_NEXT_PRINT WHAT=shaper` | `SHAPER_CALIBRATE` + belt resonance data (graph made after the print) | ~6 min | same |
| `CALIBRATE_NEXT_PRINT WHAT=twist` | `AXIS_TWIST_TOUCH_CALIBRATE` (probe + LiDAR), after the glass soak and hot re-home | ~15 min | same; a rejected run retries next print |
| `CALIBRATE_NEXT_PRINT WHAT=all` | all three | ~45 min | same |

They need the `Forced_Calibration` switch on (`_SAF_START_PRINT_AFTER_G28`). The macro marks the
item as due by back-dating its counter (`tuning.cfg`). The intervals stay 200 h (shaper),
300 h (twist) and 500 h (heaters).

**Fast path after a fan-only swap** (same duct, same fan model): step C, then
`CALIBRATE_NEXT_PRINT WHAT=heaters`, then one print. **After a fan model change:** C → E → H(shaper).
**After a duct change:** B (duct clearance) → E → H(shaper) → K.

## 4. Summary of acceptance numbers

| Step | Number | Baseline | Pass |
|---|---|---|---|
| E | fan_ambient_transfer @100 % | 0.1166 | record; > 0.14 means investigate |
| E | fan-step deviation | ±1.5 °C | ≤ ±1.5 °C |
| F | True Zero Touch d | — | ≤ ±0.010 after the update |
| F | z_offset | 0.831 | ±0.05 (same mount), ±0.5 (new mount) |
| G | LiDAR ΔX / ΔY | −36.013 / −21.336 | ≤ 0.10 / ≤ 0.30, otherwise re-seat and apply; > 5 = stop |
| H | probe twist range | 0.267 | ±0.03; pass spread ≤ 0.04 |
| H | LiDAR twist range | 0.181 | ±0.03; pass spread ≤ 0.04 |
| H | shaper X / Y | 77.6 / 52.0 Hz | X ≥ 76.0, Y 51–53 |
| J | PA | 0.046 PETG / 0.04 ASA | ±0.01 |
| K | first-layer median error | — | ±0.02 mm |

## 5. Rollback to the stock cover

1. **Config:** delete the `[include part_fan.cfg]` line (and the file), then `FIRMWARE_RESTART`.
   Pellcorp's stock `[fan]` is active again.
2. **Hardware**, printer off and cold:
   1. Remove the 2 × M3×6 cover screws and slide the cover forward.
   2. Unplug the fan(s) and add-on, and remove the duct (2 × M3×6) and the fan(s).
   3. Remove the 3 × M3×30 **one at a time**, refitting the stock screw each time: 2 × M3×18 BHCS
      upper (into the carriage inserts) and 1 × M3×20 BHCS lower-left (into the heatsink)
      (research/02 N6/N7).
   4. Mount the stock 4020 in the stock cover (3 × M3×18 BHCS, research/02 C7) and plug it in.
   5. Slide the stock cover on, then fit the 2 × M3×4 ultra-low SHCS at the sides into the carriage
      inserts (research/02 C5).
   6. If the new probe mount was fitted, refit 785004 on the same two anchor screws.
3. **Calibration:** either
   - (preferred) `CALIBRATE_NEXT_PRINT WHAT=all` plus steps F, G and K, judged against the §4
     baselines; or
   - restore the SAVE_CONFIG values (`[probe] z_offset`, `[extruder]` MPC, `[input_shaper]`,
     `[axis_twist_compensation]`) and `variables.cfg` (`lidar_*`) from the commit noted in step A.
     That is valid only if nothing else changed in between.

   MPC must be re-run or restored either way: the stock duct has its own `fan_ambient_transfer`.
4. `BACKUP_TO_GITHUB`.
