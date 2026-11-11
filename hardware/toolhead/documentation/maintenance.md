# Maintenance

For the A+ toolhead (new frame, cover, duct; stock hotend, carriage, PCB, 3010, LiDAR, MicroProbe).
Step references (C, E, F, G, H, J, K) point to `calibration.md` §2. Intervals marked ESTIMATED are
starting values. Tie them to the printer's forced-calibration hours (`CALIBRATION_STATUS`:
shaper 200 h, twist 300 h, heaters 500 h).

**Opening the toolhead:**
1. Remove the 2 × M3×6 screws on the cover top.
2. Slide the cover forward. The LiDAR, probe and fan leads stay plugged; the cover is open at the
   rear and bottom (`cover.py`).
3. The duct (2 × M3×6 into the frame) and the fan(s) (2 screws each) come off separately.
4. Never loosen the LiDAR bracket screws (2.0 mm hex) for routine work.

## 1. Nozzle change

1. Follow the hotend's own procedure (2023 ceramic or "Unicorn", M1). Hot or cold per Creality's
   instructions for the fitted hotend.
2. Whether the duct must come off for wrench access depends on the final duct (**TBD** once CFD
   decides). With the stub/v1 geometry the nozzle end sits 3 mm in front of the sock (`STUB_DUCT_TIP_Y`
   −12.0 vs sock −8.6), so plan on removing the duct.
3. Afterwards, check the duct lowest point is ≥ 2.0 mm above the new tip (`DUCT_MIN_Z`; 2 mm drill
   shank). A Unicorn tip sits 0.5 mm lower than the ceramic one (`interfaces.py`
   `UNICORN_TIP_DZ`).

Re-calibrate:

| Change | Re-run | Why |
|---|---|---|
| Any nozzle swap | F (z_offset via `TRUE_ZERO_TOUCH`) | nozzle length tolerance changes the probe-to-tip offset |
| Different nozzle type or length (brass ↔ hardened, other brand) | F + **G** (LiDAR offset check) | the LiDAR line moves −0.986 mm in Y per mm of tip height (`lidar_y_per_z`), so a 0.5 mm longer tip shifts its Y by ~0.5 mm |
| Different nozzle mass/material | E (MPC, `WHAT=heaters`) | block heat capacity changes |
| Different diameter | J (PA) + select the Orca printer for that nozzle | — |

## 2. Cleaning the ducts

Every 50 print hours (ESTIMATED), after any blob or failed print, and when cooling looks worse:
1. Cold printer, cover off, fan unplugged.
2. Remove strings and blobs from the outlets with tweezers. Do not pry the PC/PA-CF lips.
3. Blow air **from the fan socket toward the outlets** (fan removed, or its rotor held still).
4. Check each outlet against its as-printed photo, or a pin gauge of the CAD width.

| What was done | Re-calibrate |
|---|---|
| Duct cleaned in place | nothing |
| Duct removed and refitted | B duct clearance (≥ 2.0 mm above the tip); E only if the duct pose could have changed (loose tabs) |
| Duct replaced (re-print) | B + **E** (MPC: `fan_ambient_transfer` is duct-specific) + K |

## 3. Fan replacement

1. Cover off. Unplug the fan at the board (back-probe nothing).
2. Remove the 2 fan screws. They go into inserts: turn them out gently.
3. Fit the new fan with the same screw length. A longer screw bottoms out (`bill-of-materials.md`
   F6).
4. Tighten snug only.

| Replacement | Re-calibrate |
|---|---|
| Same model | C (function test, tach rpm at S255 within ±15 % of the install value); E recommended (a new fan's curve differs by unit, e.g. Delta minimum spec is 71–73 % of typical, research/03 §10.2) |
| Different model | change the `part_fan.cfg` variant (`electrical.md` §7) + current budget (§6) + C + **E** + H (shaper: mass change; ≈ 1 % X frequency per 9 g) |
| Stock 4020 back (rollback) | `calibration.md` §5 |

Bearing-wear signs:
- the tach rpm at S255 is > 10 % below the install value (ESTIMATED);
- new noise at low speed;
- the fan needs a higher `off_below` to start.

## 4. LiDAR window cleaning

When to clean:
- the first-layer check reports bare-plate rms > 0.03 (the LIDAR-NOTES "clean measurement" gate);
- scans show gaps;
- every 100 print hours (ESTIMATED).

How:
1. Printer off, or at least the LiDAR idle. Never look into the windows while it is powered.
2. Lint-free swab with a little isopropyl alcohol. One wipe per window, no pressure.
3. Do not touch the bracket or its screws.
4. The windows are on the module's underside, lower front edge (research/01 §H.2).

| What was done | Re-calibrate |
|---|---|
| Windows cleaned, bracket untouched | nothing |
| Bracket or module touched or moved | G (`LIDAR_OFFSET_CALIBRATION APPLY=0`). If the change is out of tolerance: re-seat, apply, then the LiDAR twist (I). **Never** Creality's sticker calibration with the glass plate fitted (DD-02) |

The new ducts must not blow fumes onto the windows (DD-02). If they soil faster than before the
retrofit, report it to CFD (window-region velocity).

## 5. Inspection intervals

| Item | Interval | Check | Limit / action |
|---|---|---|---|
| **Duct lips near the heater** (PC / PA-CF) | after the first 10 h of ABS/ASA at 260 °C, then every 100 h, and after any print with the fan off at ≥ 250 °C (DD-07: community covers warped at the outlets in exactly that case) | lowest duct point above the tip (drill-shank gauge); outlet shape vs install photo; discolouration or gloss change | ≥ 2.0 mm (`DUCT_MIN_Z`); sag > 0.3 mm or a visibly changed outlet → re-print (PA-CF if it was PC), then E. ESTIMATED limit |
| **Insert pull-out**: cover (2), fan (2 per fan), duct (2) | at every cover removal, and every 200 h with the shaper calibration | screws snug; inserts flush, not spinning, not lifted; no cracks around the bosses | a spinning or lifted insert → replace the part (do not glue it); a loose fan screw shows as a new broad peak in the shaper graph |
| **Probe-mount inserts** (M2.5) | every 300 h with the twist calibration | flange seated in the pocket, screws snug | True Zero Touch "vs Microprobe" drifting by > 0.02 between prints → inspect first, then F |
| **PCB screws** (3 × M3×30) | every 200 h | snug (the frame rocks on these, `stiffness.py`) | re-snug one at a time; never over-torque into the carriage inserts |
| Fan(s) | every 200 h | tach rpm at S255 (if wired); noise; dust on the intake vents | see §3 |
| Buck / MOSFET add-on | every 200 h | heat-shrink intact, leads strain-relieved, no discolouration | — |
| Cable ties, strain relief | every 200 h | probe lead (left), fan lead (right top corner) not rubbing rods or belts | — |
| LiDAR windows | see §4 | | |
| Cover, frame (ASA) | every 500 h | warping near the plenum, cracks at the screw bosses | re-print |

## 6. What to re-calibrate after each action (summary)

| Action | C fans | E MPC | F z_offset | G LiDAR offset | H twist/shaper | J PA | K first layer |
|---|---|---|---|---|---|---|---|
| Nozzle swap, same type | | | ✓ | | | | ✓ |
| Nozzle, different type/length | | ✓ | ✓ | ✓ | | ✓ | ✓ |
| Duct cleaned in place | | | | | | | |
| Duct refitted or replaced | | ✓ | | | | | ✓ |
| Fan, same model | ✓ | (✓) | | | | | |
| Fan, different model or count | ✓ | ✓ | | | ✓ shaper | | ✓ |
| `part_fan.cfg` value changed (`off_below`, `max_power`, `cycle_time`) | ✓ | ✓ | | | | | |
| LiDAR windows cleaned | | | | | | | |
| LiDAR bracket touched | | | | ✓ (+ LiDAR twist if applied) | | | |
| Probe or probe mount removed/refitted | | | ✓ | | ✓ twist | | ✓ |
| Rear part changed (anything past Y +29.1) | | | | | | | + keep-out check (D) |
