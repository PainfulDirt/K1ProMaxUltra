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
| Model | steady incompressible RANS, k-ω SST, `simpleFoam` SIMPLEC, Spalding wall functions; laminar as a bracketing check | `cfd-report.md` §2, §17.5, research/04 |
| Fan | `fanPressure` P–Q inlet at the fan outlet face. Stock 4020 at two bounds: lower (proxy-scaled, 191 Pa shut-off) and upper (ESTIMATED, 390 Pa). Same Sky and Delta from digitized datasheet curves (first round) | `cfd-report.md` §2, §14.3 |
| Environment | nozzle, sock, heat-break neck, heatsink, a 20 mm printed-part proxy with its top 0.2 mm under the tip, bed; air box X ±70, Y −80…55, Z bed…45 with open faces. No carriage, PCB, 3010 flow, cover or motion in the new-design cases. Review-round variants: a 120 × 120 mm plate, and the MicroProbe body + 785004 as a wall | `cfd-report.md` §3, §17.5 |
| Mesh | L2 production level (base cell 2.54 mm, duct walls level 3, nozzle level 4), about 0.90 M cells for S8; L3 check 1.64 M (S8) and 1.97 M (STOCK) | `cfd-report.md` §2, §17.5 |
| Averaging | every field metric is a mean over iterations 300 → stop; one S8 run continued to 1500 iterations and averaged over 750–1500 | `cfd-report.md` §2, §17.5 |
| Cases | first round: 20 flow cases, the L1/L3 check of S7, a domain check, 2 LiDAR-environment cases (§13.4). Review round (§17): S8a, S8b and four manufacturing/clearance variants; the final S8 at both fan bounds, laminar, L3, plate, probe body, skewed inlet and long average; STOCK repeated in the same round (L2, L3, laminar, plate, probe body); the S8 LiDAR case; closed-balance thermal runs of S8 and STOCK | `cfd-report.md` §13, §17 |
| Thermal proxy | passive scalar on the frozen iteration-averaged flux; part 200 °C, nozzle 250 °C, sock surface 150 °C (ESTIMATED), air 45 °C; h per wall face. Quoted only when the enthalpy balance closes to ≤ 5 % | `cfd-report.md` §17.7 |

### 1.2 Results the design rests on

S8 duct with one stock 4020, against the STOCK duct at the same fan curve, STOCK run again in the
same round with the same settings (`cfd-report.md` §17.5–§17.7, §13.1). The spread in brackets is
over the robustness checks of §17.5.

| Metric | STOCK, lower / upper 4020 bound | S8, lower / upper | Ratio (lower bound; spread) |
|---|---|---|---|
| Layer annulus speed, Z +0.3 [m/s] | 2.12 / 3.47 | 9.38 / 14.49 | ×4.4 (×4.3–5.3); ×4.2 at the upper bound |
| Weakest of 8 sectors [m/s] (min/mean) | 0.36 (0.17) / 0.68 (0.20) | 5.51 (0.59) / 8.65 (0.60) | ×15 (×12–30): "an order of magnitude", the least repeatable metric |
| Part top r ≤ 5, near-wall U0.3 [m/s] | 1.68 / 2.74 | 7.53 / 12.04 | ×4.5 (×4.5–5.8) |
| Side faces −X / +X / −Y / +Y, near-wall U0.3 [m/s] | 0.78 / 0.29 / 1.43 / 0.10 (lower) | 4.49 / 3.35 / 2.93 / 0.45 (lower) | ×5.8 / ×12 / ×2.0 / ×4.4; every face above STOCK in every variant (−Y ×2.0–2.5 the smallest) |
| Part top r ≤ 5, h (thermal proxy) [W/m²K] | 40 (lower) | 134 (lower) | ×3.3 |
| Heat removed from the part, top + sides [W] | 10.4 (lower) | 20.9 (lower) | ×2.0 |
| Nozzle cone near-wall U0.3 [m/s] | 1.00 / 1.90 | 7.25 / 10.83 | ×7.2 |
| Extra nozzle + sock loss at 100 % fan [W] | — | about +7.6 (lower; nozzle +3.1, sock +4.5) | about 13 % of the 60 W heater |
| LiDAR laser-line region, mean / max [m/s] (upper bound, nozzle 3 mm above a bare bed) | 0.18 / 0.41 | 0.041 / 0.13 | less air than STOCK |
| LiDAR window region, mean / max [m/s] (same case) | 0.087 / 0.18 | 0.17 / 0.34 | — |

The S8 min/mean, cone and port values come from `simulations/cfd/results/summary.csv`. The thermal
proxy was run at the lower bound only in the review round.

Fan alternatives (first round, on S7, lower-bound 4020 as the reference, `cfd-report.md` §10):
Same Sky +13 % layer speed, Delta +10 % typical / −10 % minimum-spec, two 4020s (D2) −5 % layer
speed and −44 % weakest sector. These are what DD-01 decided the fan on. The Same Sky is not
buildable in this architecture (§17.8). The S7 numbers of the first round (×4.8, ×14–18, ×3.5 h,
+6.2 W) are superseded.

### 1.3 Evidence that the numbers are numerically sound

| Check | Result | Source |
|---|---|---|
| Pipeline validation case (slot duct + nozzle), mesh L1 → L2 → L3 | area- and flux-averaged metrics within ±1.5 % (GCI-type bound); wall shear not mesh-converged; single-point probes ±20–30 %. This is numerical verification, not an experimental validation (review R-28) | research/04 §8 |
| Fan boundary condition | the `fanPressure` inlet sits on the fan curve to 1e-7; operating point agrees with an independent system-curve intersection to 0.5 % | research/04 §8 |
| S8 mesh, L2 (0.90 M) vs L3 (1.64 M) | S8 annulus −10 %, weakest sector −21 %, part top −3 %; STOCK −8 %, 0 %, −7 %. The S8/STOCK ratios move by −3 % (annulus), −20 % (weakest sector), +4 % (part top): the means are converged within the scatter band, the weakest sector is not | `cfd-report.md` §17.5 |
| Turbulence model (laminar vs k-ω SST) | S8 +4 %, STOCK −13 % on the annulus; the ratios grow; the ranking does not change | §17.5 |
| Part size (120 mm plate) and probe body as a wall | ratios ×5.0 and ×4.7 on the annulus; STOCK's rear sector halves with the probe body | §17.5 |
| Skewed fan outlet (65 % of the flow through one half) | annulus +1.6 %, weakest sector +3 %, part top +8 % | §17.5 |
| Averaging window (750–1500 instead of 300–750) | S8 means move ≤ 3.4 % | §17.5 |
| Run-to-run scatter | the same STOCK geometry re-meshed and re-run: +16 % on the annulus. Small geometry changes cannot be resolved below about ±8–10 % on the means, ±20–30 % on the weakest sector and a factor of about 2 on single faces | §17.2, §17.3 |
| S7 mesh, L1 / L2 / L3 (first round, record) | means converged; weakest sector −21.5 % L2 → L3 | §13.2 |
| Domain size (S7 in an enlarged box) | near-nozzle metrics −1 … +6 % | §13.3 |
| Convergence | first round: 9 cases met the watchdog (fan Q and p within 0.4 % over 100 iterations), the rest reached the 750-iteration cap; mass imbalance ≤ 0.2 % in every case (§13.4). Review round: the STOCK repeat met the watchdog, the S8 runs reached the cap (`summary.csv` `converged`); the long-average run shows the S8 means are converged in the averaging window (§17.5) | §13.4, §17.5 |
| Thermal proxy, global | enthalpy balance closes to −0.03 % (S8) and −0.5 % (STOCK). The S7-era proxy did not close (+47 … +56 %); its values are withdrawn (review R-08) | §17.7 |
| Fan inlet area, STOCK 198.8 vs S8 221 mm² | STOCK's flow is low by ≤ 0.5 %, inside the scatter; not equalized | §17.9 (R-28) |

### 1.4 Limits of the simulation

From `cfd-report.md` §14 and §17:
1. RANS at Re ≈ 10³: rankings are robust; absolute velocities carry ±20–30 %.
2. Weakly unsteady flow, pseudo-time averaged; not a time-accurate mean. Single runs scatter (§1.3).
3. The stock 4020 has no published curve. Its two bounds change the layer speed by +51 % from the
   lower to the upper bound (about ±20 % about the midpoint). The fan choice holds at both bounds; the
   absolute cooling does not.
4. Geometry: no cover, carriage, PCB or 3010 flow in the new-design cases; the stock duct is a
   reverse-engineered thin shell; many interfaces are ESTIMATED. The CFD inlet assumes a sealed
   socket: the assembly seal is part of the design (`cfd-report.md` §17.9).
5. The part proxy is a static 20 mm cube: no motion, no fresh strand, no overhangs or bridges.
6. The thermal proxy ranks convective heat transfer at fixed wall temperatures (no conduction,
   radiation or buoyancy). It is not a print model and not the true MPC heater penalty. The sock
   share scales with the ESTIMATED 150 °C sock surface (M20).
7. Wall shear is used only comparatively.
8. The 0 % fan case for the LiDAR was not run (no air source in the model). The LiDAR model has no
   module body and no buoyancy, so it says nothing about fume transport (review R-21).

Airflow is not cooling, and neither model predicts print quality. §4 decides.

## 2. Geometric / CAD checks

### 2.1 What `validate.py` checks

Current result (`cad/exports/validation_report.md`, with the Henlor stock solids present and the
real S8 duct from `duct_interface.json` v4-final): **0 FAIL, 7 WARN**.
`validate.py --cooling ducts` gives the same (`validation_report_ducts.md`).

| Check group | What it tests | Current result |
|---|---|---|
| Solids | each printed part is one valid, watertight solid; volume and mass | PASS ×5 (frame 6.64 g, cover 6.34 g, probe mount 11.45 g, coupon 2.99 g, duct 9.39 g at the PC placeholder density) |
| Minimum wall (1500 sampled rays) | share of the surface under 0.8 mm (limit 0.5 %) and the thin rays' geometry | PASS ×4; **WARN** duct (below) |
| Bed contact (review R-05) | flat down-facing area of each part in its own print frame (WARN < 100 mm², FAIL at 0) | frame 492, cover 1583, probe mount 345, coupon 848, duct 1378 mm²: PASS |
| Interference | all 27 solids pairwise; only listed contacts allowed (cover on the frame shelf, duct tabs on the lugs, frame pads on the PCB within 0.1 mm model tolerance, fan standoffs, probe mount on the carriage tabs) | PASS, no unintended overlaps |
| Fan socket (review R-02) | duct vs the 4020 modelled as a solid (body + ESTIMATED outlet nozzle + bores): ≤ 0.5 mm³ inside, only in the socket band | 0.000 mm³, min gap 0.25 mm: PASS |
| Hot zone | distance from each part to the sock/heater ≥ 3.0 (`HOT_ZONE_CLEARANCE`) | duct 4.54, probe mount 5.10, frame 13.74, cover 23.26 mm: PASS |
| `DUCT_MIN_Z` | lowest point of each part ≥ 2.0 above the tip | duct 3.00, frame 4.75, cover 24.00, probe mount 25.95: PASS. The stowed probe pin (Z 1.45) is exempt: stock part, today's state |
| S8 design targets | sock clearance ≥ 4.5 and lowest point ≥ 3.0, checked as their own targets (`interfaces.py` keeps 3.0 / 2.0) | 4.543 mm, Z 3.00: PASS |
| Rear footprint (review R-01) | behind Y +10 and below Z 30, every part (duct and fan included) inside the MicroProbe body + 785004 XY footprint the keep-out zones were measured with | duct max Y 9.80, frame −22.30, fan −36.50; probe mount inside the footprint: PASS |
| LiDAR | each part vs `LIDAR_RESERVED_OPTICAL`, `LIDAR_RESERVED_BODY` and the laser sheet | no intrusion; tightest: cover to the body box 0.50 mm, duct to the optical box 1.41, cover to the optical box 2.06, frame 2.50: PASS |
| Duct air path | frame, cover and probe mount stay out of the S8 internal air volume | gaps 1.20 / 2.00 / 13.78 mm: PASS |
| Cover clearances | cover to duct and frame below the shelf ≥ 0.3 | 0.55 / 0.30 mm: PASS |
| Fan intake | Ø30 aperture over the Ø28 inlet disc | 100 % open (616 of 616 mm²): PASS |
| Frame mount points | the frame provides the 2 fan screws, T_left, T_right and T_3: open Ø4.0 insert hole, solid Ø8.5 boss, solid mating face at Y −36.5, screw along +Y | PASS ×5 |
| Insert bosses (review R-20) | plastic around a Ø5.0 knurl ≥ 1.6 mm, blind holes with a 0.8 mm floor | 1.80 mm on every boss; the upper-left fan boss 1.35 mm on 18 % of its ring (INFO, local trim): PASS |
| PCB component zone | only the boss pads inside the zone | PASS (599.6 mm³, all pads) |
| 3010 intake | open area through the frame ≥ 625 mm² | 693 mm²: PASS |
| XY-joint band | X ≤ 24.2 inside Z 44.3…91.8 | PASS for all parts and the fan (the duct is not in the band) |
| PCB screws | last 3 mm of each M3×30 vs the stock carriage and heatsink solids; driver access through the frame | PASS ×3 / PASS ×3 (the fan comes off first) |
| Screw heads, shanks and tips (review R-02, R-03, R-15) | every added screw: ISO 7380 head (Ø5.7 × 1.65, on a washer for the duct tabs) vs all solids; Ø3.0 shank clear; tip ≥ 2.5 mm in the insert and ≥ 0.5 mm short of the hole floor | heads and shanks PASS (fan heads 0.50 mm to the cover); tips PASS for duct tabs ×3 and cover ×2; **WARN** fan screws ×2 (below) |
| Driver access | a straight Ø6.3 × 25 mm driver path (fallback Ø3.0 hex key) against the parts fitted at that screw's step (frame → fan → duct → cover); service access with everything fitted as INFO | PASS at every step. Service: the PCB screws need the fan and cover off; T_right needs a 2.0 mm hex key with the cover on (driver blocked) |
| Frame modes | hand estimates, want > 2 × 77.6 Hz | 4436 / 1259 Hz rocking, 1416 Hz fan plate with the 4th pad: PASS; **WARN** without the 4th pad |
| Duct pitch mode (review R-22) | hand estimate on the three tabs, want > 2 × 77.6 Hz | 1530 … 2742 Hz: PASS (rigid duct; E = 2200 MPa placeholder for the resin) |
| Tolerance stack-up (review R-16) | ±0.2 mm per joint and per print | duct position worst case 0.62 / RSS 0.35 mm against margins of 1.54 (hot zone) and 1.0 (`DUCT_MIN_Z`); fan head vs cover hole worst case 0.8 / RSS 0.4 mm against 0.5 radial (INFO) |
| Release status | per part: unconfirmed dependencies | frame 13 of 49, cover 4 of 19, duct 14 of 26, coupon 5 of 18, probe mount 12 of 39 |

### 2.2 The 7 WARN and why they are accepted (`cad/README.md`)

| WARN | Value | Why it is accepted |
|---|---|---|
| Duct minimum wall | 0.13 % of rays under 0.8 mm | 0 rays between parallel faces; the 2 thin rays sit on acute convex edges (wedge 57–65°) at the port-root junctions. Not a thin wall; the limit is 0.5 %. The socket-notch slivers of the first S8 export are gone (`cfd-report.md` §17.4) |
| Fan screw tips ×2 | M3×24 ends 0.20 mm from the insert-hole floor (rule ≥ 0.5) | with the ESTIMATED 20 mm through-length the safe length is 22.5…23.7 mm, and no standard ISO 7380 length fits. M7 (through-length and hole type) decides the length (review R-03) |
| Fan hole vs outlet | 154 mm³ of the lower Ø3.4 fan bore lies inside the modelled outlet column | a real blower cannot have both: the hole positions (DERIVED from a generic fan) or the outlet (ESTIMATED) are wrong. M7 resolves it (review R-02) |
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
| Duct bending and the resin's modulus | the pitch-mode estimate (1530…2742 Hz) treats the duct as rigid and uses E = 2200 MPa (PC) as a placeholder. Any HT resin above about 23 MPa passes the > 155 Hz rule (`cfd-report.md` §17.4), so stiffness is not the risk; brittleness is | shaper graph (`calibration.md` H), tap test (`assembly.md` step 6), the 10-hour audit (`maintenance.md` §5) |
| Resin print quality | cure, flushing, support marks, warping: not modelled | delivery inspection (`assembly.md` step 3.4) |
| Socket leakage | the CFD inlet is sealed; the 0.25 mm slots leak about 11 % unsealed (hand estimate) | assembly seal, V2 |
| Stock geometry | the stock solids are Henlor's reverse-engineered **K1**, not a K1 Max; carriage, LiDAR module and cover fixing are partly MISSING (M2, M6) | coupon, M#, fit-checks |
| Travel limits | only the modelled limits (`RIGHT_LIMIT_X`, soft `FRONT_LIMIT_Y`, the rear footprint) | `calibration.md` D, with the rear jog D.4 mandatory |
| Printability | overhangs and walls are checked geometrically; no part has been printed | §4 |

## 3. Estimated (hand calculations and arithmetic)

| Quantity | Value | Basis | Source |
|---|---|---|---|
| Moving mass vs stock | **+3.1 … +12.0 g** | printed parts at 100 % infill (densities ESTIMATED; the duct at the PC placeholder) + 16.5 g of screws, inserts, washers and brass sleeves (masses ESTIMATED) − stock cover + duct 23.8–32.5 g (community values) − 785004 10.6–10.9 g − stock PCB screws 3.9 g. Assumes the new probe mount replaces the 785004; while the 785004 stays, about 0.6–0.9 g less | validation report |
| X shaper | **76.6 … 77.3 Hz** (77.6 today) | 77.6 Hz scaled by √(m / (m + Δm)) at an ESTIMATED X moving mass of 450 g (400 g: 76.5…77.3; 500 g: 76.7…77.4) | validation report |
| Y shaper | **51.6 … 51.9 Hz** (52.0 today) | same at 820–960 g | validation report |
| Frame modes | rocking 4436 Hz (preloaded) / 1259 Hz (stack in compression only); fan plate 1416 Hz with the 4th pad, 147 Hz without | beam and joint hand estimates; the clamp stack is brass sleeve + PCB + 3010 corner pillar (the 3010 is the soft link) | `structure/stiffness.py`, validation report |
| Duct pitch mode | **1530 … 2742 Hz** on three tabs | rigid duct, lever 46.3 mm, J 4782 g·mm²; E = 2200 MPa placeholder | validation report; `cfd-report.md` §17.4 |
| Probe mount | sub-µm deflection, first modes 2445 Hz (Y) / 6046 Hz (X); thermal Z drift 10.8 µm per 10 K (PA-CF) against 18.9 µm for a PLA/PETG 785004 | hand estimates | validation report |
| Nozzle heat-loss penalty | about **+7.6 W** at 100 % fan (nozzle +3.1, sock +4.5), lower 4020 bound, about 13 % of the 60 W heater; roughly 3–5 W at 30–60 % fan | thermal proxy (SIMULATED, energy balance closed) with an ESTIMATED 150 °C sock surface | `cfd-report.md` §17.7 |
| MPC `fan_ambient_transfer` at 100 % after fitting | ≈ 0.15 W/K (0.1166 today) | arithmetic: today's fan term 0.0366 W/K ≈ 8.2 W at ΔT ≈ 225 K (research/03 §3) + 7.6 W ≈ 15.8 W → 0.070 W/K, + 0.0800 | `calibration.md` E |
| Socket leakage without a seal | about 0.09 L/s (11 % of the fan flow), duct flow −2–3 %; at 0.5 mm clearance about −15 % | laminar slot flow, hand calculation | `cfd-report.md` §17.9 |
| Duct position tolerance | worst case 0.62 mm, RSS 0.35 mm | ±0.2 mm per joint and per print | validation report |
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
| 4020 outlet, holes, hole type, through-length | measured; F6 length chosen and `validate.py` re-run; the hole-vs-outlet contradiction resolved; socket slides over the outlet | M7 |
| Brass sleeves | cut to 11.10 mm, flush with the pad face, held between head and PCB after tightening | BT4M size (ESTIMATED until bought) |
| Frame pads on the PCB | 0.05 feeler does not pass; nothing touches the plate; 4th pad gap ≤ 0.3 mm | M10 |
| Fan screws | they clamp the fan on the standoffs before the tip reaches the blind-hole floor | M7 |
| Resin duct on delivery | tabs without cracks, all 4 ports open (3.0 mm shank), base flat with every lip on the surface, socket intact | the service's print (DD-07a) |
| Duct to sock | ≥ 3.0 mm all round (CAD 4.54) | `HOT_ZONE_CLEARANCE` |
| Duct lowest point | ≥ 2.0 mm above the tip all round (CAD 3.0) | `DUCT_MIN_Z` |
| Duct tabs | all three seated, washers under the heads, no crack after tightening | DD-07a |
| Socket seal | no flow out of the joint at 100 % fan (tissue or smoke) | `cfd-report.md` §17.9, V2 |
| Duct vs probe and LiDAR | visible gaps; nothing in the laser sheet | M8, M6 |
| Duct tap test | no rattle | duct pitch estimate (rigid duct) |
| Cover over the fan screw heads | seats flat, front wall not bulged | modelled: heads sit in Ø6.7 cover holes, 0.50 mm clear (PASS); positions follow the ESTIMATED 4020 holes (M7) |
| Cover vs LiDAR module | visible gap | M6 (CAD 0.50 mm) |
| Cover removal | slides off without unplugging anything or removing the duct | design intent |
| Travel limits | front gap ≥ 2 mm at Y −2; side gaps ≥ 1 mm at X −2 / 306.5; rear keep-out jog with the duct fitted, 2–4 mm (ESTIMATED limits) | M9 (`calibration.md` D, D.4 mandatory) |

### 4.3 Validation tests V1–V8

From `cfd-report.md` §15. None has been run. CFD values are S8 at the lower 4020 bound unless noted.

**Per-face criterion** (DD-01, `cfd-report.md` §17.6), used by V3 and V5: each of the four faces
(−X LiDAR side, +X, −Y front, +Y probe side) must do **at least as well as STOCK** at the same
settings, and a face counts as worse only if it is below **0.8 × STOCK in two independent runs or
prints**, because single results per face scatter by about a factor of 2. That needs the same
measurement or print made with the stock duct first: do it before the stock cover comes off
(`calibration.md` step A), or after a rollback.

| # | Test | Equipment | What it validates | Pass / use |
|---|---|---|---|---|
| V1 | **Stock 4020 P–Q**: outlet capped (shut-off pressure), then free-air flow (bag-fill timing or a vane anemometer in a known-area tube); on the optional spare 4020 | ±1–2 kPa differential manometer, bag/stopwatch | which 4020 bound applies (191 vs 390 Pa) | replaces the bounds; re-run S8 and STOCK with the measured curve |
| V2 | **Socket seal, then port exit velocities**: first the fan-socket joint with its seal fitted (tissue or smoke at the joint at 100 % fan: no leak); then a hot-wire or vane anemometer 1 mm in front of each of the 4 outlets, 100 % fan, the HT-resin duct | hot-wire probe (Ø ≤ 3 mm) or a 16 mm vane | the seal (`cfd-report.md` §17.9); flow split (CFD 22 / 33 / 17 / 28 % at 240° / 275° / 315° / 355°) and jet speed (CFD flux-mean 12.3 m/s) | no leak at the joint; ports within ±20 % of CFD → the model is trusted for ranking |
| V3 | **Layer-plane survey**: probe at Z +0.3…1 mm under the nozzle (heater off, glass bed), 8 directions at r 3 and 6 mm; then the near-wall speed at the top 3 mm of each side face of a 20 mm block standing under the nozzle (its top one layer under the tip), with the stock duct and with S8 | as V2, on a 3-axis jog using the printer | the annulus metric and its symmetry (CFD min/mean 0.59); the per-face gain (CFD −X ×5.8, +X ×12, −Y ×2.0, +Y ×4.4) | min/mean ≥ 0.5 confirms the ring layout; **every face passes the per-face criterion above** |
| V4 | **Heater-power penalty**: `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7` with STOCK (today's 0.1166 W/K at 100 %), then with S8 (`calibration.md` E), at 260 °C | printer only | real nozzle cooling (CFD cone near-wall 7.25 vs 1.00 m/s STOCK; +7.6 W heater demand at 100 % fan) | `fan_ambient_transfer` at 100 % against 0.1166 W/K (expected ≈ 0.15); heater keeps a reserve at the hottest print temperature with the fan at 100 % |
| V5 | **Overhang / bridge prints** in 4 orientations (0°, 90°, 180°, 270° relative to the toolhead), so that each test face points at −X, +X, −Y and +Y in turn: overhang steps 30–70°, bridges 10–40 mm, a deliberately curling ABS overhang (review R-06; check the lips and base afterwards). PLA at 100 % fan (a test print on the bed, not a toolhead part) and ABS at 30–40 %. Run with the K1 Max auxiliary side fan on and off (review R-10). The same prints with the stock duct are the reference | printer | real cooling **per face** (review R-11); the weakest face in CFD is +Y (probe side) in absolute terms, the smallest gain −Y (front) | overhang angle reached and droop per face; **every face passes the per-face criterion above**; no lip or base damage from the curl print |
| V6 | **Bridge sag measured with the LiDAR**: scan the bridge print's underside profile with the `LIDAR_...` macros | the printer's LiDAR | sag (mm) per orientation and fan speed, STOCK vs S8 | sag ratio S8/STOCK; an improvement is expected from the layer-speed ratio |
| V7 | **LiDAR window contamination**: 2 h ABS print at 100 % fan, inspect and wipe the windows, compare scan noise before and after | printer | DD-02: fumes onto the windows (CFD window region 0.17 m/s mean, 0.34 max, upper bound; the model has no plume and no module body) | no visible deposit, scan repeatability unchanged. Also the evidence for or against the proposed fan-off rule for scans (`calibration.md` §6) |
| V8 | **Thermal soak, quantitative** (review R-07): the HT-resin duct; thin thermocouples on the sock bottom (M20), on the manifold's inner face (7.8 mm from the sock) and on the port top lip closest to the sock (4.54 mm); nozzle at 300 °C, chamber 45 °C, fan 0 %, ≥ 4 h; measure the base and lip height with a feeler gauge or calipers before and after | 2–3 thin K-type thermocouples + reader, calipers | DD-07 / DD-07a: the resin's HDT margin, sock clearance | hottest duct point ≥ 15 K below the resin's HDT: **238 °C class at 0.45 MPa after the full thermal post-cure, from the TDS of the exact material the service used** (so ≤ about 223 °C for a 238 °C resin); lip and base height change < 0.1 mm; no visible distortion, crack or discolouration |

V5's PLA is a test-print material on the bed, not a toolhead part: no PLA or PETG goes near the
hotend (DD-07).

### 4.4 Calibration acceptance

`calibration.md` §4 lists the numbers the printer's own calibrations must meet after fitting
(MPC, z_offset, LiDAR check, twist, shaper, PA, first layer). They are measurements on the printer
and will be the first MEASURED data for the new toolhead.
