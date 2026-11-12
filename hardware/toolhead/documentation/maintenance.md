# Maintenance

For the A+ toolhead: new cooling-module frame, cover and S7 duct, with the stock 4020, hotend,
carriage, PCB, 3010, LiDAR and MicroProbe. Step references (B, C, E, F, G, H, J, K) point to
`calibration.md` §2. Intervals marked ESTIMATED are starting values. Tie them to the printer's
forced-calibration hours (`CALIBRATION_STATUS`: shaper 200 h, twist 300 h, heaters 500 h).
Screws and inserts: `bill-of-materials.md` §2. Full assembly and rollback: `assembly.md`.

## 0. Opening the toolhead and taking the duct off

**Cover** (no unplugging needed):
1. Remove the 2 × M3×6 ISO 7380 screws on the cover top (2.0 mm hex).
2. Slide the cover forward. The LiDAR, probe and fan leads stay plugged; the cover is open at the
   rear and bottom and comes off without removing the duct (`cad/README.md`, `cover.py`).
3. Never loosen the LiDAR bracket screws (2.0 mm hex) for routine work.

**Duct** (S7: it hangs on two tabs, T_left and T_right, with one M3 along +Y each into a frame lug
insert, plus its fan socket, which slides 4 mm over the 4020's outlet; `cad/README.md`,
`duct_interface.json`):
1. Printer cold (nozzle below 50 °C). Before switching off, give the toolhead at least 50 mm of
   free space under the nozzle (`G0 Z50`): the duct comes off downward.
2. Cover off (above). Keep the probe stowed.
3. Hold the duct and remove the two tab screws (M3×6 ISO 7380) from the front:
   - T_left at X −7.5, Z 19.5 (below the left half of the fan);
   - T_right at X +24.0, Z 22.5 (right of the fan).
4. Lower the duct straight down. After about 4 mm the socket is free of the fan outlet. Keep it
   level and lower it further, until the manifold (roof apex at Z 16.5) is below the sock bottom
   (Z 4.9), about 12 mm more. Then draw it forward and out.
5. Refit in the reverse order: socket up over the fan outlet, tabs flat on the lug faces, screws
   snug (plastic boss, do not over-tighten), then the checks in `assembly.md` step 6 (≥ 3 mm to the
   sock, lowest point ≥ 2.0 mm above the tip).

Steps 4–5 are **INFERRED from the CAD** (the manifold is a horseshoe around the sock with no part
above or below the sock footprint, `cfd-report.md` §5.1 and §12.3), not tried on the printer.
Confirm them at the first fit (`assembly.md` step 6) and correct this page if the real part needs
another path.

**Fan:** the duct comes off first, because its socket wraps the fan outlet. Then the 2 fan screws
(M3×24, 2.5 mm hex for ISO 4762) at the diagonal corners (X −18.65, Z 60.3) and (X +16.05, Z 25.6).

## 1. Nozzle change

**Can the nozzle wrench reach with the duct fitted? Not determinable from the sources.** The CAD
models the nozzle only as Ø6.9 × 23.3 mm (`interfaces.py` `NOZZLE_MAX_D`, `NOZZLE_LENGTH`), with no
wrench flats, and the repo has no nozzle procedure for the fitted hotend (M1: 2023 ceramic or
"Unicorn"). What the S7 geometry does show:
- below the sock (Z 0 … 4.9 above the tip) the 5 ports sit at r 14.0–20.4 mm around the nozzle, and
  the lips come down to Z 2.44 (`cfd-report.md` §12.3);
- the horseshoe manifold runs from azimuth 231.5° (front-left) through the front and the right side
  to 52° (rear-right), with its inner face just outside the 3 mm clearance around the sock (CAD
  minimum 3.35 mm, validation report);
- the only open side is the rear and the left (52° → 231.5° through 90° and 180°). The MicroProbe
  sits at the rear (body X ±11, Y 12.5…28.1) and the LiDAR on the left (optical keep-out from
  X −18).

**Safe procedure: take the duct off for every nozzle change.**
1. Duct off (§0). The fan and the frame stay.
2. Follow the hotend's own procedure (2023 ceramic or "Unicorn", M1), hot or cold per Creality's
   instructions for the fitted hotend. With the duct off, the PC duct is not exposed to the hot
   nozzle or the wrench.
3. Duct back on (§0 step 5).
4. Check that the duct's lowest point is ≥ 2.0 mm above the new tip (`DUCT_MIN_Z`; 2 mm drill shank
   with the tip on a flat block) and that the duct clears the sock by ≥ 3 mm. A Unicorn tip sits
   0.5 mm lower than the ceramic one (`interfaces.py` `UNICORN_TIP_DZ`), and a Unicorn hotend
   changes the stack by 1.6 mm (M1): the S7 ports are placed for the 2023 hotend
   (`DUCT_HOTEND_VERSION`).

Re-calibrate:

| Change | Re-run | Why |
|---|---|---|
| Any nozzle swap | F (z_offset via `TRUE_ZERO_TOUCH`) | nozzle length tolerance changes the probe-to-tip offset |
| Different nozzle type or length (brass ↔ hardened, other brand) | F + **G** (LiDAR check) | the LiDAR line moves −0.986 mm in Y per mm of tip height (`lidar_y_per_z`), so a 0.5 mm longer tip shifts its Y by ~0.5 mm. If G is out of tolerance, the nozzle change (not the bracket) is the cause, and step I applies |
| Different nozzle mass/material | E (MPC, `WHAT=heaters`) | block heat capacity changes |
| Different diameter | J (PA) + select the Orca printer for that nozzle | — |

## 2. Cleaning the duct

Every 50 print hours (ESTIMATED), after any blob or failed print, and when cooling looks worse:
1. Cold printer, cover off.
2. Remove strings and blobs from the 5 outlets with tweezers. Do not pry the PC / PA-CF lips.
3. For a thorough clean, take the duct off (§0) and blow air **from the fan socket toward the
   outlets**.
4. Check each outlet against its as-printed photo, or with calipers against the CAD 6 × 3 mm.

| What was done | Re-calibrate |
|---|---|
| Duct cleaned in place | nothing |
| Duct removed and refitted | B duct clearances (≥ 3 mm to the sock, ≥ 2.0 mm above the tip); E only if the duct pose could have changed (loose tabs) |
| Duct replaced (re-print) | B + **E** (MPC: `fan_ambient_transfer` is duct-specific) + K |

## 3. Fan replacement

The baseline fan is the stock Creality 4020 (4004110132).
1. Cover off, duct off (§0). Unplug the fan at the board (back-probe nothing).
2. Remove the 2 fan screws. They go into inserts: turn them out gently.
3. Fit the new fan with the same screw length. A longer screw bottoms out in the 5.0 mm insert hole
   (`bill-of-materials.md` F6).
4. Tighten snug only (plastic boss, do not over-tighten). Duct back on (§0 step 5).

| Replacement | Re-calibrate |
|---|---|
| Same model (stock 4020) | C (function test; tach rpm at S255 within ±15 % of the install value if a tach is wired); E recommended (each unit's curve differs; the 4020's is not even known, `validation.md` V1) |
| Same Sky upgrade (conditional, `electrical.md` §2) | needs its own duct variant, a regenerated frame and the buck: follow `electrical.md` §2 + C + **E** + H (shaper: mass change; ≈ 1 % X frequency per 9 g) |
| Stock cover back (rollback) | `assembly.md` §3 and `calibration.md` §5 |

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
| Bracket or module touched or moved | G (`LIDAR_OFFSET_CALIBRATION APPLY=0`, read-only). If the change is out of tolerance: re-seat; only then step I (apply, then the LiDAR twist). **Never** Creality's sticker calibration with the glass plate fitted (DD-02) |

CFD says the S7 duct does not blow onto the windows: at the window region the air is slow
(0.17 m/s against 0.087 for STOCK at 100 % fan) and moves downward, away from the module
(`cfd-report.md` §13.1). That is simulated, not measured. If the windows soil faster than before
the retrofit, record it (test V7, `validation.md`).

## 5. Inspection intervals

| Item | Interval | Check | Limit / action |
|---|---|---|---|
| **Duct lips near the heater** (PC / PA-CF) | after the first 10 h of ABS/ASA at 260 °C, then every 100 h, and after any print with the fan off at ≥ 250 °C (DD-07: community covers warped at the outlets in exactly that case) | lowest duct point above the tip (drill-shank gauge); gap to the sock; outlet shape vs install photo; discolouration or gloss change | ≥ 2.0 mm (`DUCT_MIN_Z`) and ≥ 3 mm to the sock; sag > 0.3 mm or a visibly changed outlet → re-print (PA-CF if it was PC), then E. ESTIMATED limit |
| **Duct tabs and sag** | at every cover removal | cracks at T_left / T_right; the manifold's rear-right end (about 45 mm from the tabs) still level; no rattle when the toolhead is tapped | a crack or sag → re-print. Persistent sag or flutter is the case `cfd-report.md` §16 names for a third tab (CAD change) |
| **Insert pull-out**: cover (2), fan (2), duct (2) | at every cover removal, and every 200 h with the shaper calibration | screws snug; inserts flush, not spinning, not lifted; no cracks around the bosses | a spinning or lifted insert → replace the part (do not glue it); a loose fan screw shows as a new broad peak in the shaper graph |
| **Probe-mount inserts** (M2.5; only once the probe mount is released and fitted) | every 300 h with the twist calibration | flange seated in the pocket, screws snug | True Zero Touch "vs Microprobe" drifting by > 0.02 between prints → inspect first, then F |
| **PCB screws** (3 × M3×30) | every 200 h | snug (the frame rocks on these, `stiffness.py`) | re-snug one at a time (fan and duct off for driver access); never over-torque into the carriage inserts |
| Fan | every 200 h | tach rpm at S255 (if wired); noise; dust on the Ø30 intake | see §3 |
| Cable ties, strain relief | every 200 h | probe lead, fan lead (frame top-corner tie slots) not rubbing rods or belts | — |
| LiDAR windows | see §4 | | |
| Cover, frame (ASA) | every 500 h | warping near the plenum, cracks at the screw bosses | re-print |
| Buck (only with the Same Sky upgrade) | every 200 h | heat-shrink intact, leads strain-relieved, no discolouration | — |

## 6. What to re-calibrate after each action (summary)

| Action | C fans | E MPC | F z_offset | G LiDAR check | H twist/shaper | J PA | K first layer |
|---|---|---|---|---|---|---|---|
| Nozzle swap, same type | | | ✓ | | | | ✓ |
| Nozzle, different type/length | | ✓ | ✓ | ✓ | | ✓ | ✓ |
| Duct cleaned in place | | | | | | | |
| Duct refitted or replaced | | ✓ | | | | | ✓ |
| Fan, same model | ✓ | (✓) | | | | | |
| Fan, different model (Same Sky upgrade) | ✓ | ✓ | | | ✓ shaper | | ✓ |
| `part_fan.cfg` value changed (`off_below`, `max_power`, `cycle_time`) | ✓ | ✓ | | | | | |
| LiDAR windows cleaned | | | | | | | |
| LiDAR bracket touched | | | | ✓ (+ step I only if out of tolerance) | | | |
| Probe or probe mount removed/refitted | | | ✓ | | ✓ twist | | ✓ |
| Rear part changed (anything past Y +29.1) | | | | | | | + keep-out check (D) |
