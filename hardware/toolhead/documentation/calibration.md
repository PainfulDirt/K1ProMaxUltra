# Post-install calibration

The calibration procedure after fitting the new cooling module (frame, stock 4020, S7 duct) and
cover on **this** K1 Max, and later the probe mount. It uses the printer's own macros
(`tuning.cfg`, `custom/*.py`, the repo `README.md`). **No sensor moves** (DD-02, DD-03), so there is
no sensor recalibration in this procedure, only checks. What does change is the nozzle's airflow
(MPC), the moving mass (input shaper, twist) and the front envelope (clearances).

No printer config file in the repo is changed by this project. Every `SAVE_CONFIG` below writes
the printer's own calibration results, as the printer's macros already do.

Baselines are the values in the repo today (MEASURED on this printer by the user's existing
calibrations):

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
| Probe x/y offset | no | probe position kept (DD-03); the new probe mount, when released, copies 785004's anchor-to-probe relation | no re-measure. The z_offset check below would reveal a shift |
| Probe `z_offset` | maybe a little | same probe pose, but a different thermal environment (new duct airflow), and a new mount once one is fitted | **yes**, load-cell method (step F) |
| `zero_reference_position`, `mesh_min/max`, `screws_tilt_adjust` | no | follow from the probe offset | no |
| LiDAR pose, offsets, `custom/lidar.py` reach values | **no** | module and bracket untouched (DD-02) | **check only** (step G): no `LIDAR_OFFSET_CALIBRATION` is run to change anything, because the cover swap happens right next to the bracket |
| Axis twist (probe and LiDAR) | probably small | pitch behaviour depends on toolhead mass and CG; the mass change is **−0.7 … +8.3 g** (validation report) | **yes** (step H) |
| Keep-out zones | no, if nothing reaches behind Y +29.1 | new parts end at Y −22.3 (frame), duct body at Y +27.5; the probe mount rear is 29.10 vs 29.1 for 785004 (validation report) | **verify** (step D), and re-measure if a rear part changed |
| Front/side clearance | **yes** | new cover front **−58.2** vs stock −55.0 (validation WARN, M9); duct body reaches X +31.0 below Z 23 (outside the XY-joint band) | **yes** (step D) |
| Input shaper | small | predicted X **76.9 … 77.7 Hz**, Y **51.8 … 52.0 Hz** (validation report, ESTIMATED at an X moving mass of 450 g) | **yes** (step H). Also watch for a frame mode near 150 Hz (validation WARN: 147 Hz without the 4th pad) and any duct flutter |
| MPC fan model | **yes** | `fan_ambient_transfer` is duct-specific (DD-05, research/03 §3); CFD expects the fan's extra nozzle + sock loss to rise by +6.2 … +6.8 W at 100 % (`cfd-report.md` §11) | **required** (step E) |
| Bed PID | no | bed unchanged | runs anyway with `WHAT=heaters` |
| PA | barely | hotend and extruder unchanged | spot-check (step J) |
| ADXL `axes_map` | no | PCB orientation unchanged | no |
| Fan config | no | stock 4020 on the stock channel, Pellcorp's `[fan]` unchanged (`electrical.md` §1) | function test (step C) |
| Orca bed shape, nozzle-wipe strip, park positions | no | they follow the keep-outs | no |

## 2. Order of operations

| Step | What | Printer hot? | Approx. time |
|---|---|---|---|
| A | Baseline capture (before disassembly) | yes | 20 min |
| B | Install (`assembly.md`), cold checks | no | — |
| C | Fan function test (no config change) | no | 10 min |
| D | Clearances and keep-outs (rear jog **mandatory**), motors on, slow | no | 30 min |
| E | **MPC re-calibration** (+ fan-step test, heater reserve, max-flow headroom) | yes | 25–35 min |
| F | Probe z_offset via the load cells | yes | 15 min |
| G | LiDAR checks (no recalibration) | yes (optional dry-run cross) | 10 min |
| H | Twist (probe + LiDAR) and input shaper, via `CALIBRATE_NEXT_PRINT` and one sacrificial print | yes | 30 min |
| I | LiDAR offsets and twist, **only** if step G found the bracket disturbed | yes | 15 min |
| J | PA spot-check (`LIDAR_PA_CALIBRATION`) | yes | 15 min |
| K | First-layer checks | yes | one print |
| L | Slicer fan percentages: re-tune (your decision) | yes | several coupons |
| M | Save and back up | — | — |

Why this order:
- MPC goes first among the hot steps: the nozzle wipe cools its blob at `M106 S255`
  (`custom/nozzle_wipe.py`), and every later touch and print uses the part fan.
- z_offset comes before any print, because True Zero Touch falls back to Microprobe Z when the
  touch differs from the probe by more than −0.03 / +0.15 mm (`_LOAD_CELL_TOUCH_Z`).
- The LiDAR offsets are checked before the LiDAR twist, because the twist uses them.

### A. Baseline capture (stock cover still fitted)

1. `BACKUP_TO_GITHUB` and note the commit hash. This is the rollback reference (§5).
2. `CALIBRATION_STATUS`: note the print hours and when each calibration is due.
3. `LIDAR_OFFSET_CALIBRATION APPLY=0`: note the reported X/Y offsets and arm lengths. This gives
   the run-to-run noise of the check on the untouched printer. Nothing is saved.
4. Optional, closes M13: `SHAPER_CALIBRATE` with and without a ~50 g mass taped to the toolhead.
   Keep the CSVs.
5. Optional, for V4 (`validation.md`): note `fan_ambient_transfer` from `printer.cfg.save_config`
   (0.1166 today). It is the stock reference for the heater-penalty test.
6. Weigh the stock cover + 4020 on a kitchen scale (M12). Also measure the 4020 (M7): outlet
   opening and screw-hole through-length, before the fan goes onto the frame (`assembly.md` step 2).

### B. Install, then check cold (motors off)

Follow `assembly.md`. Its checks after each step are part of this calibration:
- PCB screws replaced in sequence, snug only; frame bosses flat on the PCB.
- Duct-to-sock gap ≥ 3 mm all round (`HOT_ZONE_CLEARANCE`; CAD 3.35 mm).
- Duct lowest point ≥ 2.0 mm above the nozzle tip (`DUCT_MIN_Z`; CAD 2.44 mm). A 2 mm drill shank
  under the duct while the tip sits on a flat block.
- `PROBE_DOWN`, `QUERY_PROBE`, `PROBE_UP`: the pin deploys and retracts freely, and its lead is not
  pulled by the new tie points.
- Nothing touches the LiDAR module, its bracket or its windows. The cover's left wall must clear the
  module (CAD: 0.50 mm to the ESTIMATED `LIDAR_RESERVED_BODY` box, M6). Look along the laser sheet:
  no part, cable or tie may hang below the module.
- Cables: nothing rubs the X rods or belts.

### C. Fan function test (no config change)

The baseline uses Pellcorp's `[fan]` unchanged (`electrical.md` §1). Nothing to include.
1. `M106 S26`, `S77`, `S128`, `S255`, then `M107`: the fan starts every time, and the speed rises
   monotonically by ear. Feel the air at the ports at S255 (cold printer).
2. If you chose to include `part_fan_stock4020.cfg` with the tach for commissioning (a config change,
   `electrical.md` §5): read the rpm in Fluidd. It should be within ±15 % of the datasheet speed at
   S255 (ESTIMATED tolerance; datasheet ±10 %). Note it as the install value for `maintenance.md` §3.
3. Heat the nozzle to above 40 °C: the 3010 hotend fan starts (unchanged channel; its tach reads in
   Fluidd). Its intake now draws through the frame window (693 mm² open, validation report).
4. Only if the fan stalls at low duty: tune `off_below` and `kick_start_time` (`electrical.md` §3)
   **now**, before MPC.

### D. Clearances and keep-outs (motors on, speed F600, a finger on the e-stop / power switch)

1. `G28`, then lift Z to 50 (`G0 Z50 F600`).
2. **Front:** `G0 X150 Y0`, then step to Y −2 in 0.5 mm steps. The gap from the cover front (−58.2,
   3.2 mm further forward than the stock −55.0) to the door and frame must be ≥ 2 mm (ESTIMATED). If
   it is not, stop: the Y minimum would have to change (Pellcorp base config). Report it, because it
   is the M9 open point.
3. **Left / right:** at Y 150, step to X −2 and X 306.5 at Z 50 and at Z 5. Gap from the cover,
   duct and fan to the XY joints ≥ 1 mm (ESTIMATED). Inside the joint band (Z 44.3…91.8 above the tip)
   the cover is ±24.0 against `RIGHT_LIMIT_X` 24.2; the duct body reaches X +31.0 only below Z 23,
   outside the band (validation report).
4. **Rear keep-outs: mandatory for this build** (review R-01). Today's zones were measured with the
   MicroProbe body and the 785004 adapter as the rearmost parts. The new duct is a different shape
   behind and beside the probe, so the zones are not known to clear it. Jog with the duct fitted, at
   **Z 5 and again at Z 0.5**, in 0.5 mm steps. At each point check the gap between the rearmost
   toolhead part (probe, adapter, duct, frame) and the Z-rod housing.

| Point or sweep (nozzle X, Y) | Zone it guards |
|---|---|
| 150, 292 | zone1 (middle housing) |
| sweep X 105 → 130 at the largest allowed Y, beside zone1 | middle housing, reached by anything right of the probe |
| −2, 291 | zone2 (left corner) |
| 286, 301 | zone3 (right housing) |
| sweep X 266 → 306.5 along the zone3/zone4 borders | right housing and corner |
| 306.5, 286 | zone4 (right corner) |

   Accept a gap of 2–4 mm (ESTIMATED). If it is less than 2 mm anywhere, stop. Re-measure that zone the
   way the `tuning.cfg` comment describes, then update `[keep_out]` plus the Orca bed shapes
   (`orcaslicer/make_profiles.py`). That is a printer-config change, so it is your decision; keep the
   old values for rollback. If the gap is more than 5 mm, leave the zones alone (conservative).

### E. MPC re-calibration (required after fitting, and after any fan or duct change)

1. With the printer cold and the chamber at room temperature:
   `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7`, then `SAVE_CONFIG`
   (DD-05, `cfd-report.md` §12.2).
   - Alternative: `CALIBRATE_NEXT_PRINT WHAT=heaters`. It runs MPC + bed PID (~25 min) at the next
     START_PRINT and saves 5 min after the print ends. Use this only if you can wait until after
     step H, since the nozzle wipe and every touch run on the old fan model until then.
2. Fan-step test: `M109 S250`, wait 2 min, then `M106 S255`, then after 2 min `M107`. Watch the
   extruder graph.
3. Heater reserve: at the hottest nozzle temperature you print with the fan at 100 %, the extruder
   power in Fluidd must settle clearly below 100 %. The new duct takes several more watts from the
   60 W heater at full fan (below).

What to expect. The stock fan's share of the block's heat loss is 0.1166 − 0.0800 = 0.0366 W/K at
100 %, about +8 W at ΔT ≈ 225 K (research/03 §3). The CFD thermal proxy adds +6.2 W (lower 4020
bound) to +6.8 W (upper) of nozzle + sock loss at 100 % fan over the stock duct
(`cfd-report.md` §11, which says to expect the fan term to roughly double). On the same 225 K that
puts `fan_ambient_transfer` at 100 % near **0.14–0.15 W/K** (ESTIMATED, my arithmetic). Treat it as
indicative only: the proxy ran with 45 °C air and an assumed 150 °C sock surface, and its energy balance does not close: on S7 the heat leaving through the open boundaries exceeds the wall input by 47–56 % (STOCK 2–3 %), so the error differs per case (review R-08).

| Quantity | Pass | Basis |
|---|---|---|
| block_heat_capacity | 16.36 ± 10 % | hotend unchanged (ESTIMATED tolerance) |
| sensor_responsiveness | 0.0917 ± 15 % | ESTIMATED |
| ambient_transfer (fan 0) | 0.0800 ± 10 % | ESTIMATED; the new cover changes natural convection a little |
| fan_ambient_transfer at 100 % | **record it** (this is test V4 in `validation.md`). Expected **above** 0.1166, roughly 0.14–0.15. **≤ 0.1166**: less air reaches the nozzle than CFD predicts; check the duct is seated on the fan outlet and no port is blocked. **> ~0.18** (about twice the predicted increase, ESTIMATED limit): a jet is hitting the block or the duct is mis-seated; check the duct pose and the 3 mm sock gap | CFD proxy (indicative); ESTIMATED limits |
| Fan-step deviation | ≤ ±1.5 °C, overshoot ≤ 0.5 °C | README baseline |
| Heater power at the hottest print temperature, fan 100 % | settles clearly below 100 % | `cfd-report.md` §15 V4 ("plan for the heater's reserve") |

4. **Heater headroom at maximum flow** (review R-18). Static power (step 3) is not the worst case.
   Extrude a purge at the highest volumetric flow you print, at the hottest temperature, with the fan
   at 100 %. For the Orca "Speed Benchy" profile that is 32 mm³/s at 255 °C: about 100 mm of filament
   at 13.3 mm/s, in the air over the purge area or the wipe strip. Record the heater duty and the
   temperature droop.
   - The review estimates about 79 % duty with the new duct against 69 % stock (REVIEWER-ESTIMATE).
   - Pass: duty ≤ 90 % and droop ≤ 3 °C.
   - If it fails, lower the profile's maximum flow or its fan percentage at that flow.

   Also check flow consistency at fan 0 % and 100 %, because the cooler tip changes melt temperature
   (step J's PA test is one way to do it).

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
| Change vs 0.831, probe mount unchanged (785004) | ≤ 0.05 | ESTIMATED (thermal environment only) |
| Change vs 0.831, new probe mount | ≤ 0.5 | research/01 §B.4 (mount-face tolerance) |
| Change > 1.0 | **stop**: outside DD-03's envelope; the probe mount is wrong | DD-03 |

### G. LiDAR checks (no sensor moved: no recalibration)

The module, its bracket and its pose are untouched (DD-02). **Do not run
`LIDAR_OFFSET_CALIBRATION` to apply anything, and never run Creality's sticker calibration with the
glass plate fitted** (DD-02). The checks below only read.

1. **Visual, cold:** the bracket screws were not loosened; the windows are clean; no part, cable or
   tie hangs into the laser sheet or the camera view under the module (`LIDAR_RESERVED_OPTICAL`:
   CAD clearances frame 2.50, cover 2.06, duct 2.22 mm, all ESTIMATED boxes, M6).
2. **`LIDAR_STATUS`**: the module answers as before.
3. **Optional dry run** (read-only, prints a small cross): clear the plate around X 135–165,
   Y 133–167 and run `LIDAR_OFFSET_CALIBRATION APPLY=0`. It scans the cross at Z3 and Z5 and reports
   without saving.

| Result vs `variables.cfg` | Meaning | Action |
|---|---|---|
| \|ΔX\| ≤ 0.10, \|ΔY\| ≤ 0.30, per-Z slopes within ±0.02 (X) / ±0.05 (Y), arms 20.1–20.3 mm (LIDAR-NOTES). The ΔX and slope limits are ESTIMATED | unchanged. The Y limit is wider because lines along X read up to ~0.3 mm off in Y (README, LIDAR-NOTES) | **nothing to apply** (expected result) |
| Outside that, but < 5 mm | the bracket was disturbed during the cover swap | re-seat or check the bracket screws (2.0 mm hex) first and repeat the dry run. Only if it still disagrees: step I |
| "more than 5mm from the current one, not applied" | the macro refuses any change > 5 mm in X or Y (`custom/lidar.py`). The module has moved or rotated | **stop**. Do not delete the saved offsets to force it. Restore the module pose (DD-02) |
| "implausible change with height" | per-Z slopes are outside the macro's limits (\|kx\| > 1, \|ky\| > 3) | check that nothing has entered the laser sheet (step G.1), then repeat |

Compare ΔX/ΔY against the step A dry run. A difference smaller than the A-vs-baseline noise is
not a change.

### H. Twist and input shaper (one sacrificial print)

1. Make sure the `Forced_Calibration` switch is on.
2. Run `CALIBRATE_NEXT_PRINT WHAT=twist` and `CALIBRATE_NEXT_PRINT WHAT=shaper`.
   (`WHAT=heaters` too, if step E was skipped.)
3. Print something small (e.g. a 20 mm cube) with `First_Layer_Check` on.
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
| Shaper X | ≥ **76.0 Hz** (architecture target, DD comparison table); expected **76.9 … 77.7** | validation report (ESTIMATED) |
| Shaper Y | 51–53 Hz; expected **51.8 … 52.0** | validation report; ±1 Hz ESTIMATED repeatability |
| Projected max accel X | ≥ ~4300 mm/s² (baseline 4408) | research/01 §D |
| X response graph | no new peak at 100–200 Hz. A peak near 150 Hz is the frame's fan-plate mode without the 4th pad (validation WARN 147 Hz). Another new peak may be the duct: it hangs on two tabs and the fan socket, and its own mode is not estimated (`validation.md`) | validation report; `cfd-report.md` §16 |
| Belt graph | both belt curves still overlap as before | — |

If X is below 76 Hz, check for loose fan, duct or cover screws (a rattle shows as a broad peak).
Then run the M13 mass test and report it.

### I. LiDAR offsets and twist (only if step G found the bracket disturbed and re-seating did not fix it)

This is the exception, not part of the normal procedure. `LIDAR_OFFSET_CALIBRATION` (APPLY=1), then
`LIDAR_TWIST_CALIBRATION` (homed, clear plate along Y 145). Same pass criteria as the LiDAR rows in
step H. Report it: DD-02 assumes the pose does not change.

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

A single-layer print runs its after-scan from `_SAF_END_PRINT_START`, possibly with the part fan
still running (§6). If the report's gates fail only on such prints, note it for test V7.

### L. Slicer fan percentages (your decision; review R-12)

At the same fan percentage the layer now gets several times the stock airflow: ×3.8–4.8 in layer
speed in CFD, not measured. Today's Orca percentages were tuned for the stock duct, so ABS/ASA may
lose layer bonding and warp or crack more. PETG bridging and layer adhesion change too. Those
symptoms would come from the percentages, not from the duct.

1. Starting point (REVIEWER-ESTIMATE, a starting point only): ABS/ASA and PETG fan maxima at about
   1/3–1/2 of today's values (ABS/ASA 0–30 % → about 0–12 %; PETG 30–80 % → about 15–35 %). PLA can
   stay at 100 %.
2. Tune with a layer-adhesion coupon (snap test of a thin wall), a warp coupon (a long thin bar,
   measuring the corner lift) and the V5 overhang/bridge print, in that filament.
3. Record the result in the filament profiles (`orcaslicer/make_profiles.py`). This is a slicer
   profile change: keep the old values for rollback.
4. Do the same for the overhang/bridge fan values (M18).

### M. Save and back up

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
`CALIBRATE_NEXT_PRINT WHAT=heaters`, then one print. **After a fan model change** (e.g. the
conditional Same Sky upgrade): C → E → H(shaper). **After a duct change or re-print:** B (duct
clearances) → E → H(shaper) → K.

## 4. Summary of acceptance numbers

| Step | Number | Baseline | Pass |
|---|---|---|---|
| B | duct to sock / duct lowest point above the tip | — (CAD 3.35 / 2.44) | ≥ 3.0 / ≥ 2.0 mm |
| E | fan_ambient_transfer @100 % | 0.1166 | record; expected ≈ 0.14–0.15; ≤ 0.1166 or > ~0.18 means investigate |
| E | fan-step deviation | ±1.5 °C | ≤ ±1.5 °C |
| F | True Zero Touch d | — | ≤ ±0.010 after the update |
| F | z_offset | 0.831 | ±0.05 (same mount), ±0.5 (new mount) |
| G | LiDAR ΔX / ΔY (dry run, nothing applied) | −36.013 / −21.336 | ≤ 0.10 / ≤ 0.30, otherwise re-seat; > 5 = stop |
| H | probe twist range | 0.267 | ±0.03; pass spread ≤ 0.04 |
| H | LiDAR twist range | 0.181 | ±0.03; pass spread ≤ 0.04 |
| H | shaper X / Y | 77.6 / 52.0 Hz | X ≥ 76.0 (expected 76.9–77.7), Y 51–53 |
| J | PA | 0.046 PETG / 0.04 ASA | ±0.01 |
| K | first-layer median error | — | ±0.02 mm |

## 5. Rollback to the stock cover

1. **Config:** nothing to undo for the baseline (no config was changed). If you included a
   `part_fan.cfg` snippet, delete the `[include part_fan.cfg]` line (and the file), then
   `FIRMWARE_RESTART`.
2. **Hardware**, printer off and cold: `assembly.md` §3 (cover, duct, fan, frame off; stock PCB
   screws, 4020 into the stock cover, stock cover on).
3. **Calibration:** either
   - (preferred) `CALIBRATE_NEXT_PRINT WHAT=all` plus steps F, G and K, judged against the §4
     baselines; or
   - restore the SAVE_CONFIG values (`[probe] z_offset`, `[extruder]` MPC, `[input_shaper]`,
     `[axis_twist_compensation]`) and `variables.cfg` (`lidar_*`) from the commit noted in step A.
     That is valid only if nothing else changed in between.

   MPC must be re-run or restored either way: the stock duct has its own `fan_ambient_transfer`.
4. `BACKUP_TO_GITHUB`.

## 6. Proposed, not applied: part fan off during LiDAR scans

DD-02 proposes running every LiDAR scan with the part fan off. With S7 the air speed along the bed
under the laser line rises to 0.87 m/s mean (1.50 max) against 0.18 m/s for STOCK at 100 % fan
(`cfd-report.md` §13.1, upper 4020 bound). Air movement is not expected to bend the beam (DD-02),
but the wall jet can move loose dust or strings across the scan line while the fan runs, and the
0 % fan case was not simulated. Whether it affects readings at all is open (test V7).

Where the repo's macros scan, and the fan state there:

| Scan | Called from | Part fan at that moment |
|---|---|---|
| Bare-plate scan before the purge: `FIRST_LAYER_SCAN PHASE=before`, or `LIDAR_SCAN NAME=pa_base` for the PA test | `_SAF_START_PRINT_AFTER_BED_MESH` → `_LIDAR_PRINT_SCAN` (`tuning.cfg`) | normally off: the nozzle wipe that runs just before ends with `M106 S0` (`custom/nozzle_wipe.py`). Not enforced by `_LIDAR_PRINT_SCAN` itself |
| First-layer scan at the layer-2 change: `FIRST_LAYER_SCAN PHASE=after` | `_FIRST_LAYER_AFTER` (`tuning.cfg`), from the slicer's layer-change G-code | **may be on**: the slicer may already have switched the fan on for layer 2 (DD-02) |
| First-layer scan of a one-layer print: `FIRST_LAYER_SCAN PHASE=after FINAL=1` | `_SAF_END_PRINT_START` (`tuning.cfg`) | **may be on**: whatever the print left |
| PA test scan (`LIDAR_PA_CALIBRATE`) and offset cross (`LIDAR_OFFSET_CALIBRATE`) | `custom/lidar.py` | off: both print with the fan on (`M106 S{FAN}` / `M106 S128`), cool the nozzle at `M106 S255`, then send `M106 S0` before the scan |

The change, if the user wants it (a printer-config edit to `tuning.cfg`, **not applied by this
project**, not tested):

```
[gcode_macro _FIRST_LAYER_AFTER]
gcode:
    {% if printer.lidar.first_layer_armed %}
      {% set fan = printer.fan.speed %}
      M106 S0
      FIRST_LAYER_SCAN PHASE=after
      M106 S{(fan * 255)|round|int}
    {% endif %}
```

and an `M106 S0` before `FIRST_LAYER_SCAN PHASE=after FINAL=1` in `_SAF_END_PRINT_START`. Open
points before adopting it:
- whether the slicer's own fan command for layer 2 comes before or after the layer-change G-code
  (if after, the restore line is redundant but harmless);
- the 4020 needs some time to spin down; the scan may start before the air has stopped;
- the pause with the fan off changes the first layer's cooling history for that print.

Test V7 (`validation.md`) is the evidence for or against it.
