# Validation status

What has been validated for the new toolhead, how, and what is still open. It is split strictly
by the kind of evidence:

| § | Kind | Meaning here |
|---|---|---|
| 1 | **SIMULATED** | OpenFOAM runs in this project (`cfd-report.md`, results in `simulations/cfd/results/`) |
| 2 | **GEOMETRIC / CAD** | automated checks on the CAD solids (`cad/source/validate.py`, `export.py`) |
| 3 | **ESTIMATED** | hand calculations and arithmetic on estimated inputs |
| 4 | **NOT DONE** | physical tests and prints that still have to happen, with pass criteria |

**No physical test, print or measurement of the new parts has been made.** Every performance
number below is simulated or estimated. The only measured data on this printer are the user's
existing calibrations of the stock toolhead (`calibration.md`, baseline table).

## 1. Simulated (CFD)

### 1.1 What was simulated

| Item | Value | Source |
|---|---|---|
| Model | steady incompressible RANS, k-ω SST, `simpleFoam` SIMPLEC, Spalding wall functions | `cfd-report.md` §2, research/04 |
| Fan | `fanPressure` P–Q inlet at the fan outlet face. Stock 4020 at two bounds: lower (proxy-scaled, 191 Pa shut-off) and upper (ESTIMATED, 390 Pa). Same Sky and Delta from digitized datasheet curves | `cfd-report.md` §2, §14.3 |
| Environment | nozzle, sock, heat-break neck, heatsink, a 20 mm printed-part proxy with its top 0.2 mm under the tip, bed; air box X ±70, Y −80…55, Z bed…45 with open faces. No carriage, PCB, 3010 flow, cover or motion in the new-design cases | `cfd-report.md` §3 |
| Mesh | L2 production level (base cell 2.54 mm, duct walls level 3, nozzle level 4), about 0.96 M cells for S7 | `cfd-report.md` §2, §10 |
| Averaging | every field metric is a mean over iterations 300 → stop | `cfd-report.md` §2, §13.4 |
| Cases | 20 flow cases (L2, 0.82–1.24 M cells), 5 thermal restarts, 2 LiDAR-environment cases, plus mesh and domain checks | `cfd-report.md` §13.4 |
| Thermal proxy | passive scalar on the converged flow; part 200 °C, nozzle 250 °C, sock surface 150 °C (ESTIMATED), air 45 °C; h per wall face | `cfd-report.md` §7, §11 |

### 1.2 Results the design rests on

S7 duct with one stock 4020, against the STOCK duct at the same fan curve
(`cfd-report.md` §10, §11, §13.1).

| Metric | STOCK, lower / upper 4020 bound | S7, lower / upper | Ratio (lower bound) |
|---|---|---|---|
| Layer annulus speed, Z +0.3 [m/s] | 1.83 / 3.47 | 8.84 / 13.34 | ×4.8 |
| Weakest of 8 sectors [m/s] (min/mean) | 0.35 (0.19) / 0.68 (0.20) | 6.28 (0.71) / 9.16 (0.69); L3: 4.93 (0.56) | ×14–18 (not mesh-converged) |
| Part top r ≤ 5, near-wall U0.3 [m/s] | 1.38 / 2.74 | 7.81 / 12.28 | ×5.7 |
| Part top r ≤ 5, h (thermal proxy) [W/m²K] | 42 / 54 | 147 / 216 | ×3.5 |
| Heat removed from the part, top + sides [W] | 10.2 / 14.8 | 20.3 / 26.7 | ×2.0 |
| Nozzle cone near-wall U0.3 [m/s] | 0.95 / 1.90 | 7.17 / 10.98 | ×7.5 |
| Extra nozzle + sock loss at 100 % fan [W] | — | +6.2 / +6.8 | (about 10 % of the 60 W heater) |
| LiDAR laser-line region, mean / max [m/s] (upper bound, nozzle 3 mm above a bare bed) | 0.18 / 0.41 | 0.87 / 1.50 | — |
| LiDAR window region, mean / max [m/s] (same case) | 0.087 / 0.18 | 0.17 / 0.25 | — |

Fan alternatives on S7, lower-bound 4020 as the reference (`cfd-report.md` §10): Same Sky +13 %
layer speed (+21 % part-top h), Delta +10 % typical / −10 % minimum-spec, two 4020s (D2) −5 % layer
speed and −44 % weakest sector. These are what DD-01 decided on.

### 1.3 Evidence that the numbers are numerically sound

| Check | Result | Source |
|---|---|---|
| Pipeline validation case (slot duct + nozzle), mesh L1 → L2 → L3 | area- and flux-averaged metrics within ±1.5 % (GCI-type bound); wall shear not mesh-converged; single-point probes ±20–30 % | research/04 §8 |
| Fan boundary condition | the `fanPressure` inlet sits on the fan curve to 1e-7; operating point agrees with an independent system-curve intersection to 0.5 % | research/04 §8 |
| Early stopping | an L1 run continued to 1500 iterations changed the annulus mean by 1e-4 m/s | research/04 §8 |
| S7 mesh, L1 (0.51 M) vs L2 (0.96 M) | annulus +0.3 %; weakest sector −8 %; part top +5 %; cone wall shear −14 %; fan Q +2 % | `cfd-report.md` §13.2 |
| S7 mesh, L2 (0.96 M) vs L3 (1.70 M) | means converged: annulus −0.7 %, part top −0.3 %, cone −2.8 %, fan Q −0.3 %; side faces −7 %; **weakest sector −21.5 % (6.28 → 4.93; GCI-type ±27 %), not converged** | `cfd-report.md` §13.2 |
| Domain size (S7 in an enlarged box, 1.17 M cells) | near-nozzle metrics −1 … +6 %; LiDAR-region speeds +13 % / +29 % in relative terms but ≤ 0.2 m/s absolute | `cfd-report.md` §13.3 |
| Repeatability for a sub-millimetre geometry change (S4 vs S7) | ±3 % on means, ±5 % on the weakest sector. Smaller differences are ties; for the weakest sector, differences under about 25 % are ties (L3 check) | `cfd-report.md` §9 It.6, §13.4 |
| Convergence | 9 cases met the watchdog (fan Q and p within 0.4 % over 100 iterations), the rest reached the 750-iteration cap with fan Q swinging 0.5–1.4 % (S1 2.5 %); mass imbalance ≤ 0.2 % in every case; checkMesh passes except single skewed faces (≤ 5.3) away from the measurement regions | `cfd-report.md` §13.4 |
| Thermal proxy, local | wall flux matches the near-wall temperature gradient (STOCK part top: h ≈ 40 against 46 W/m²K face mean) | `cfd-report.md` §7 |
| Thermal proxy, global | enthalpy balance closes within 2–3 % for STOCK but not for S7 (+47 … +56 %). S7's h values are more likely under-estimated; the ranking does not depend on it | `cfd-report.md` §7, §11 |

### 1.4 Limits of the simulation

From `cfd-report.md` §14:
1. RANS at Re ≈ 10³: rankings are robust; absolute velocities carry ±20–30 %.
2. Weakly unsteady flow, pseudo-time averaged; not a time-accurate mean.
3. The stock 4020 has no published curve. Its two bounds change the layer speed by about ±50 % between
   them (±20 % about the midpoint). The fan choice holds at both bounds; the absolute cooling does
   not. Uniform outlet profile, no swirl.
4. Geometry: no cover, carriage, PCB or 3010 flow in the new-design cases; the stock duct is a
   reverse-engineered thin shell; many interfaces are ESTIMATED.
5. The part proxy is a static 20 mm cube: no motion, no fresh strand, no overhangs or bridges.
6. The thermal proxy ranks convective heat transfer at fixed wall temperatures. It is not a print
   model and not the true MPC heater penalty.
7. Wall shear is used only comparatively.
8. The 0 % fan case for the LiDAR was not run (no air source in the model).

Airflow is not cooling, and neither model predicts print quality. §4 decides.

## 2. Geometric / CAD checks

### 2.1 What `validate.py` checks

Current result (`cad/exports/validation_report.md`, with the Henlor stock solids present and the
real S7 duct from `duct_interface.json` v3-final): **0 FAIL, 4 WARN**.
`validate.py --cooling ducts` gives the same (`validation_report_ducts.md`).

| Check group | What it tests | Current result |
|---|---|---|
| Solids | each printed part is one valid, watertight solid; volume and mass | PASS ×5 (frame 5.84 g, cover 6.35 g, probe mount 11.45 g, coupon 2.89 g, duct 9.24 g) |
| Minimum wall (1500 sampled rays) | share of the surface under 0.8 mm (limit 0.5 %) and the thin rays' geometry | PASS ×4; **WARN** duct (below) |
| Interference | all 27 solids pairwise; only listed contacts allowed (cover on the frame shelf, duct tabs on the lugs, frame pads on the PCB within 0.1 mm model tolerance, duct socket over the fan outlet, probe mount on the carriage tabs) | PASS, no unintended overlaps |
| Hot zone | distance from each part to the sock/heater ≥ 3.0 (`HOT_ZONE_CLEARANCE`) | duct 3.35, probe mount 5.10, frame 13.74, cover 23.26 mm: PASS |
| `DUCT_MIN_Z` | lowest point of each part ≥ 2.0 above the tip | duct 2.44, frame 15.90, cover 24.00, probe mount 25.95: PASS. The stowed probe pin (Z 1.45) is exempt: stock part, today's state |
| LiDAR | each part vs `LIDAR_RESERVED_OPTICAL`, `LIDAR_RESERVED_BODY` and the laser sheet | no intrusion; tightest: cover to the body box 0.50 mm, cover to the optical box 2.06, duct 2.22, frame 2.50: PASS |
| Duct air path | frame, cover and probe mount stay out of the S7 internal air volume | gaps 1.20 / 2.00 / 9.59 mm: PASS |
| Cover clearances | cover to duct and frame below the shelf ≥ 0.3 | 0.40 / 0.30 mm: PASS |
| Fan intake | Ø30 aperture over the Ø28 inlet disc | 100 % open (616 of 616 mm²): PASS |
| Frame mount points | the frame provides the 2 fan screws, T_left and T_right: open Ø4.0 insert hole, solid Ø7.2 boss, solid mating face at Y −36.5, screw along +Y | PASS ×4 |
| Rear limit | nothing behind Y 31.0 below Z 30; probe mount rear vs today's 785004 | PASS (probe mount 29.10 vs 29.1) |
| PCB component zone | only the boss pads inside the zone | PASS (710.4 mm³, all pads) |
| 3010 intake | open area through the frame ≥ 625 mm² | 693 mm²: PASS |
| XY-joint band | X ≤ 24.2 inside Z 44.3…91.8 | PASS for all parts (the duct is not in the band) |
| PCB screws | last 3 mm of each M3×30 vs the stock carriage and heatsink solids; driver access through the frame | PASS ×3 / PASS ×3 (the fan comes off first) |
| Screw heads | every added screw's ISO 7380 head (Ø5.7 × 1.65) vs all printed and stock solids: overlap = FAIL, gap < 0.3 mm to an unclamped part = WARN | PASS for PCB ×3, fan ×2 (0.300 / 0.299 mm, the lower one to the duct socket), duct tabs ×2, cover ×2 |
| Driver access | a straight Ø6.3 × 25 mm driver path (fallback Ø3.0 hex key) against the parts fitted at that screw's step (frame → fan → duct → cover); service access with everything fitted as INFO | PASS at every step. Service: the PCB screws need the fan and cover off; T_right needs a 2.0 mm hex key with the cover on (driver blocked) |
| Frame modes | hand estimates, want > 2 × 77.6 Hz | 4440 / 1168 Hz rocking, 1416 Hz fan plate with the 4th pad: PASS; **WARN** without the 4th pad |
| Release status | per part: unconfirmed dependencies | frame 8 of 37, cover 4 of 18, duct 12 of 24, coupon 5 of 18, probe mount 12 of 39 |

### 2.2 The 4 WARN and why they are accepted (`cad/README.md`)

| WARN | Value | Why it is accepted |
|---|---|---|
| Duct minimum wall | 0.37 mm on 0.27 % of rays | every thin ray sits on an acute convex edge (wedge 66–85°), none between parallel faces: the ridge where each port floor steps onto the manifold floor, and the port/manifold junctions. Not a thin wall. Inside the air path, so only the duct owner can change it (S6's flush roots did, at a CFD cost of 6–8 %) |
| Front extent | −58.2 (cover) vs `FRONT_LIMIT_Y` −55 | a soft limit, DERIVED from the stock cover; the real travel clearance is unmeasured (M9). The 4020 alone reaches −56.5; the cover adds 0.5 + 1.2. Checked on the printer in `calibration.md` D |
| Probe anchor, `interfaces.py` vs Henlor carriage | shift (0, −2.8, −0.6) mm | M8. The mount copies 785004's anchor-to-probe relation, so the pin lands where it does today; only the placement in the nozzle frame is uncertain |
| Frame fan-plate mode without the 4th pad | 147 Hz (want > 155) | only if the PCB "2nd plate" is not a real part (M10); the coupon checks the pad |

The INFO line on `LIDAR_RESERVED_BODY` overlapping the stock carriage by 1.2 mm in X is expected:
the box's inner face lies where the LiDAR bracket seats (M6).

### 2.3 Export checks (`export.py`)

Every part is exported to STEP, 3MF and STL, re-opened and compared with the CAD solid
(`cad/exports/export_manifest.json`, all `pass`):

| Format | Tolerance |
|---|---|
| STEP round trip | 1 solid, OCC-valid, closed, dV/V < 1e-6, bbox 1e-3 mm |
| 3MF / STL | 1 object, dV/V < 5e-3, bbox 0.05 mm; STL watertight, consistent winding |
| Assembly STEP | same named, coloured leaves and groups, per-leaf dV/V < 1e-6 |

### 2.4 What the CAD checks do not cover

| Gap | Why it matters | Where it gets checked |
|---|---|---|
| Duct cantilever mode | the duct hangs on two tabs and the socket, with a 45 mm lever; no estimate exists (`stiffness.py` covers the frame and probe mount only; it asks for > 150 Hz) | shaper graph (`calibration.md` H), rattle check (`assembly.md` step 6) |
| Stock geometry | the stock solids are Henlor's reverse-engineered **K1**, not a K1 Max; carriage, LiDAR module and cover fixing are partly MISSING (M2, M6) | coupon, M#, fit-checks |
| Travel limits | only the modelled limits (`RIGHT_LIMIT_X`, soft `FRONT_LIMIT_Y`, `REAR_LIMIT_Y`) | `calibration.md` D |
| Printability | overhangs and walls are checked geometrically; no part has been printed | §4 |

## 3. Estimated (hand calculations and arithmetic)

| Quantity | Value | Basis | Source |
|---|---|---|---|
| Moving mass vs stock | **−0.7 … +8.3 g** | printed parts at 100 % infill (densities ESTIMATED) + 13.73 g of screws and inserts (masses ESTIMATED) − stock cover + duct 23.8–32.5 g (community values) − 785004 10.6–10.9 g − stock PCB screws 3.9 g. Assumes the new probe mount replaces the 785004 | validation report |
| X shaper | **76.9 … 77.7 Hz** (77.6 today) | 77.6 Hz scaled by √(m / (m + Δm)) at an ESTIMATED X moving mass of 450 g (400 g: 76.8…77.7; 500 g: 77.0…77.7) | validation report |
| Y shaper | **51.8 … 52.0 Hz** (52.0 today) | same at 820–960 g | validation report |
| Frame modes | rocking 4440 Hz (preloaded) / 1168 Hz (boss in compression only); fan plate 1416 Hz with the 4th pad, 147 Hz without | beam and joint hand estimates; the upper PCB screws' target (carriage inserts) is DERIVED; if it were plastic, the joint could be softer than the pessimistic case | `structure/stiffness.py`, validation report |
| Probe mount | sub-µm deflection, first modes 2445 Hz (Y) / 6046 Hz (X); thermal Z drift 10.8 µm per 10 K (PA-CF) against 18.9 µm for a PLA/PETG 785004 | hand estimates | validation report |
| Nozzle heat-loss penalty | +6.2 W (lower bound) / +6.8 W (upper) at 100 % fan, about 10 % of the 60 W heater; about 2–3 W at 40–60 % fan | thermal proxy (SIMULATED) with an ESTIMATED 150 °C sock surface; energy balance unclosed (outflow exceeds wall input by 47–56 % on S7, 2–3 % on STOCK), so indicative | `cfd-report.md` §11 |
| MPC `fan_ambient_transfer` at 100 % after fitting | ≈ 0.14–0.15 W/K (0.1166 today) | my arithmetic: today's fan term 0.0366 W/K ≈ 8 W at ΔT ≈ 225 K (research/03 §3) + the 6.2–6.8 W above | `calibration.md` E |
| LiDAR beam deflection by air | about 0.3 µm spot shift for a 20 K gradient over 25 mm, below the module's 1–2 µm repeatability | dn/dT ≈ −1e-6 per K | DD-02 |

## 4. Not done: physical tests required

None of these has been done. Order: §4.1 first, then the priority-1 measurements
(`missing-information.md`), then §4.2, then `calibration.md`, then §4.3.

### 4.1 Fit-check coupon (PRINT FIRST)

Procedure: `print-settings.md` §5.

| Check | Pass |
|---|---|
| Overall depth (plate + neck) | 10.8 ± 0.15 mm |
| Ring width | 32.0 ± 0.15 mm (gives the ASA shrink) |
| PCB hole pattern | 24.0 ± 0.10 mm |
| Neck Ø at the PCB end | 5.8 ± 0.10 mm |
| Neck step to the 4th-corner pad face | 6.34 ± 0.15 mm |
| Probe fence | 22.13 × 15.80 mm; the probe drops in without force, play ≤ 0.2 |
| Probe insert spacing | 17.0 ± 0.10 mm |
| Inserts (1 × M3, 2 × M2.5) | flush, square, do not spin at snug; no bulge or split |
| On the printer | every neck flat on bare PCB (0.05 feeler does not pass), no component under a neck or touching the plate, window aligned with the PCB fan cutout, 3010 spins freely, 4th-pad gap recorded (> 0.3 mm or no 2nd plate: report) |
| M2.5×5 probe screws | ≥ 5 turns of engagement, seat flat without bottoming |

### 4.2 CAD fit checks on the printer (FIT-CHECK FIRST parts)

From `assembly.md` §2; each one confirms an ESTIMATED value.

| Check | Pass | Confirms |
|---|---|---|
| 4020 hole through-length and outlet | measured; F6 length chosen by the rule; socket slides over the outlet | M7 |
| Frame pads on the PCB | 0.05 feeler does not pass; nothing touches the plate; 4th pad gap ≤ 0.3 mm | M10 |
| Fan screws | fan seated on the standoffs without the screws bottoming | M7 |
| Duct to sock | ≥ 3.0 mm all round | `HOT_ZONE_CLEARANCE` |
| Duct lowest point | ≥ 2.0 mm above the tip all round | `DUCT_MIN_Z` |
| Duct vs probe and LiDAR | visible gaps; nothing in the laser sheet | M8, M6 |
| Duct rattle | none when tapped | duct cantilever (no estimate) |
| Cover over the fan screw heads | seats flat, front wall not bulged | modelled: heads sit in Ø6.3 cover holes, 0.30 mm clear (PASS); positions follow the ESTIMATED 4020 holes (M7) |
| Cover vs LiDAR module | visible gap | M6 (CAD 0.50 mm) |
| Cover removal | slides off without unplugging anything or removing the duct | design intent |
| Travel limits | front gap ≥ 2 mm at Y −2; side gaps ≥ 1 mm at X −2 / 306.5 (ESTIMATED limits) | M9 (`calibration.md` D) |

### 4.3 Validation tests V1–V8

From `cfd-report.md` §15. None has been run.

| # | Test | Equipment | What it validates | Pass / use |
|---|---|---|---|---|
| V1 | **Stock 4020 P–Q**: outlet capped (shut-off pressure), then free-air flow (bag-fill timing or a vane anemometer in a known-area tube); on the optional spare 4020 | ±1–2 kPa differential manometer, bag/stopwatch | which 4020 bound applies (191 vs 390 Pa) | replaces the bounds; re-run S7 with the measured curve (1 run). Also one of the two conditions for the Same Sky upgrade |
| V2 | **Port exit velocities**: hot-wire or vane anemometer 1 mm in front of each of the 5 outlets, 100 % fan, PC duct | hot-wire probe (Ø ≤ 3 mm) or a 16 mm vane | flow split (CFD 16–25 % per port) and jet speed (CFD flux-mean 11.8 m/s at the lower bound) | within ±20 % of CFD → the model is trusted for ranking |
| V3 | **Layer-plane survey**: probe at Z +0.3…1 mm under the nozzle (heater off, glass bed), 8 directions at r 3 and 6 mm | as V2, on a 3-axis jog using the printer | the annulus metric and its symmetry (CFD min/mean 0.71) | min/mean ≥ 0.5 confirms the ring layout |
| V4 | **Heater-power penalty**: `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7` with STOCK (today's 0.1166 W/K at 100 %), then with S7 (`calibration.md` E), at 260 °C | printer only | real nozzle cooling (CFD cone near-wall 7.2 vs 1.0 m/s STOCK, lower bound) | `fan_ambient_transfer` at 100 % against 0.1166 W/K; heater keeps a reserve at the hottest print temperature with the fan at 100 % |
| V5 | **Overhang / bridge prints** in 4 orientations (0°, 90°, 180°, 270° relative to the toolhead): overhang steps 30–70°, bridges 10–40 mm. The CFD plan uses PLA at 100 % fan (a test print on the bed, not a toolhead part) and ABS at 30–40 % | printer | real cooling and its direction dependence (left/rear are the weakest sectors in CFD) | overhang angle reached and droop per direction. With V1, the second condition for the Same Sky upgrade |
| V6 | **Bridge sag measured with the LiDAR**: scan the bridge print's underside profile with the `LIDAR_...` macros | the printer's LiDAR | sag (mm) per orientation and fan speed, STOCK vs S7 | sag ratio S7/STOCK; ≥ 30 % improvement expected from the layer-speed ratio |
| V7 | **LiDAR window contamination**: 2 h ABS print at 100 % fan, inspect and wipe the windows, compare scan noise before and after | printer | DD-02: fumes onto the windows (CFD window region 0.17 m/s mean, moving downward) | no visible deposit, scan repeatability unchanged. Also the evidence for or against the proposed fan-off rule for scans (`calibration.md` §6) |
| V8 | **Thermal soak, quantitative** (revised after review R-07): duct in the chosen filament; thermocouples on the sock bottom (M20) and on the manifold's inner face; nozzle at 300 °C, chamber 45 °C, fan 0 %, ≥ 4 h; measure lip Z with a feeler gauge or calipers before and after | 2 thin K-type thermocouples + reader, calipers | DD-07: HDT margin, sock clearance | inner face ≥ 15 K below the filament's HDT (TDS, 0.45 MPa); lip Z change < 0.1 mm; no visible distortion |

V5's PLA is a test-print material on the bed, not a toolhead part: no PLA or PETG goes near the
hotend (DD-07).

### 4.4 Calibration acceptance

`calibration.md` §4 lists the numbers the printer's own calibrations must meet after fitting
(MPC, z_offset, LiDAR check, twist, shaper, PA, first layer). They are measurements on the printer
and will be the first MEASURED data for the new toolhead.
