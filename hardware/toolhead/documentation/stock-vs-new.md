# Stock vs new toolhead

Side by side: the stock K1 Max front cover with its duct and 4020, against the new build (frame +
cover in ASA, the S8 duct in HT resin from a print service (DD-07a), the same stock 4020; everything
else stock and in place).

**There are no measured performance numbers for the new toolhead yet.** Nothing has been printed or
fitted. The "Measured after fitting" column is empty on purpose. The only MEASURED values on this
page are the user's existing calibrations of the stock toolhead.

Tags, per value:
- **MEASURED**: measured on this printer (today: the stock calibrations in `printer.cfg.save_config`
  and `variables.cfg`).
- **SIMULATED**: OpenFOAM, `cfd-report.md` (absolute values ±20–30 %; rankings robust). Single runs
  scatter: about ±8–10 % on the means, ±20–30 % on the weakest sector and a factor of about 2 on a
  single side face (`cfd-report.md` §17.3, §17.5).
- **ESTIMATED**: hand calculation or arithmetic on estimated inputs.
- **DESIGN**: a property of the CAD or the design decision, true by construction.

CFD values are given at both 4020 bounds, **lower / upper** (191 / 390 Pa shut-off). The stock
4020's real curve is unknown (test V1); decisions are made at the lower bound. STOCK at the lower
bound is the review-round repeat, run in the same round and with the same settings as S8
(`STOCK_part_proxy_r8`); at the upper bound it is the first-round STOCK run. Ratios in brackets after
a value are the spread over the robustness checks of `cfd-report.md` §17.5 (laminar, L3 mesh, 120 mm
plate, probe body as a wall, skewed fan outlet, long averaging window). Values marked "summary" are
from `simulations/cfd/results/summary.csv`, the table of every run (`cfd-report.md` §1).

## 1. Part cooling (S8 vs the stock duct, same 4020)

All on the 20 mm part proxy, steady RANS k-ω SST, L2 mesh.

| Quantity | Stock | New (S8) | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Fan flow Q [L/s] | 0.805 / 1.199 | 0.809 / 1.211 | SIMULATED | — (V1, V2) | summary |
| Layer annulus speed, r 1–6 mm, Z +0.3 [m/s] | 2.12 / 3.47 | **9.38 / 14.49** (×4.4 / ×4.2; spread ×4.3–5.3) | SIMULATED | — (V3) | `cfd-report.md` §17.5 |
| Weakest of 8 sectors [m/s] | 0.36 / 0.68 | **5.51 / 8.65** (×15 / ×13; spread ×12–30, the least repeatable metric; L3 4.36, ×12) | SIMULATED | — (V3) | §17.5 |
| Symmetry min/mean | 0.17 / 0.20 | 0.59 / 0.60 | SIMULATED | — (V3: pass ≥ 0.5) | summary |
| Part top r ≤ 5, near-wall U0.3 [m/s] | 1.68 / 2.74 | **7.53 / 12.04** (×4.5 / ×4.4; spread ×4.5–5.8) | SIMULATED | — | §17.5 |
| Part side faces, top 3 mm, U0.3, −X / +X / −Y / +Y [m/s], lower bound | 0.78 / 0.29 / 1.43 / 0.10 | 4.49 / 3.35 / 2.93 / 0.45 (×5.8 / ×12 / ×2.0 / ×4.4); every face above stock in every variant, −Y ×2.0–2.5 the smallest | SIMULATED (per-face values known to about a factor of 2) | — (V3, V5 per face) | §17.6 |
| The same, upper bound | 1.40 / 0.54 / 1.96 / 0.25 | 8.41 / 5.15 / 4.67 / 0.92 (×6.0 / ×9.5 / ×2.4 / ×3.6) | SIMULATED | — | §17.6 |
| Part top r ≤ 5, h (thermal proxy) [W/m²K], lower bound | 40 | **134** (×3.3) | SIMULATED (proxy, energy balance closed: −0.5 % STOCK, −0.03 % S8) | — (V5, V6) | §17.7 |
| Heat removed from the part, top + sides [W], lower bound | 10.4 | 20.9 (×2.0) | SIMULATED (proxy) | — | §17.7 |
| Side-face h, −X / +X / −Y / +Y [W/m²K], lower bound | 39 / 31 / 82 / 19 | 102 / 101 / 92 / 41 (every face above stock; −Y only ×1.1, inside the scatter) | SIMULATED (proxy) | — (V5 per face) | §17.7 |
| Thermal proxy at the upper bound | not run in the review round | not run in the review round | — | — | §17.7 |
| Outlets | slots around the sock at Z ≈ 7–10, above the sock bottom | 4 wedge ports, 7.5 × 3 mm (90 mm² total), at 240°, 275°, 315°, 355°; 25° floor, 45° ceiling, 12° yaw; outlet bottom Z 4.32; closest material 4.54 mm from the sock | DESIGN | — | §6.1, §17.4 |
| Port flow split, 240° / 275° / 315° / 355° | — | 22 / 33 / 17 / 28 %; jet flux-mean 12.3 m/s (lower bound) | SIMULATED | — (V2) | summary |
| Part fans | 1 × stock 4020 | the same 1 × stock 4020 | DESIGN | — | DD-01 |

## 2. Nozzle and heater

| Quantity | Stock | New (S8) | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Nozzle cone near-wall U0.3 [m/s] | 1.00 / 1.90 | 7.25 / 10.83 | SIMULATED | — | summary |
| Nozzle convective loss at 100 % fan [W], lower bound | 1.11 | 4.19 (+3.1) | SIMULATED (proxy, balance closed) | — | `cfd-report.md` §17.7 |
| Sock convective loss at 100 % fan [W], lower bound (sock surface assumed 150 °C) | 6.54 | 11.06 (+4.5) | SIMULATED (proxy) + ESTIMATED sock temperature | — | §17.7 |
| **Extra heater demand at 100 % fan** | — | **about +7.6 W** (about 13 % of the 60 W heater); roughly Q^0.8 of it, 3–5 W, at 30–60 % fan | SIMULATED (proxy) + ESTIMATED sock temperature (MISSING `SOCK_SURFACE_T`, M20) | — (V4) | §17.7 |
| The same at the upper bound | — | not run in the review round | — | — | §17.7 |
| MPC `fan_ambient_transfer` at 100 % [W/K] | **0.1166** | ≈ 0.15 | stock MEASURED; new ESTIMATED (arithmetic, `calibration.md` E) | — (V4, `calibration.md` E) | `printer.cfg.save_config`; `calibration.md` |
| MPC `ambient_transfer` (fan 0) [W/K] | 0.0800 | expected about the same | stock MEASURED; new ESTIMATED | — | `printer.cfg.save_config` |
| Hotend, heater, sock | stock 2023 ceramic, 60 W | unchanged | DESIGN | — | DD-01 |

The S7-era heater figures (+6.2 / +6.8 W) came from a thermal proxy whose energy balance did not close
and are withdrawn (`cfd-report.md` §17.7, review R-08).

## 3. LiDAR

| Quantity | Stock | New (S8) | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Laser-line region air speed, mean / max (fan 100 %, upper 4020 bound, nozzle 3 mm above a bare bed) [m/s] | 0.18 / 0.41 | **0.041 / 0.13** (less than stock: no port on the left, and the swirl turns the front-left jet back toward the part) | SIMULATED | — (V7) | `cfd-report.md` §13.1 |
| Window region air speed, mean / max (same case) [m/s] | 0.087 / 0.18 | 0.17 / 0.34 | SIMULATED (isothermal, no module body: says nothing about fume transport, review R-21) | — (V7) | §13.1 |
| Air speed at 0 % fan | 0 (no part-fan flow) | 0 (no part-fan flow) | DESIGN (not simulated: the model has no other air source) | — | §13.1 |
| Optical effect of the air | — | ≈ 0.3 µm spot shift for a 20 K gradient, below the 1–2 µm repeatability | ESTIMATED | — | DD-02 |
| Module, bracket, pose | as fitted | unchanged; no new part enters the LiDAR boxes or the sheet (tightest: cover 0.50 mm to the ESTIMATED body box; duct 1.41 mm to the optical box) | DESIGN (boxes ESTIMATED, M6) | — (`calibration.md` G) | DD-02, validation report |
| LiDAR offsets X / Y | **−36.013 / −21.336** | unchanged (no recalibration) | stock MEASURED; new DESIGN | — (`calibration.md` G dry run) | `variables.cfg` |
| LiDAR twist range | **0.181 mm** | expected ≈ same (re-run with the twist calibration) | stock MEASURED | — (`calibration.md` H) | `variables.cfg` |

## 4. Mass and dynamics

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Cover + duct (without fan) | 23.8 g (K1, community measured) … 32.5 g (K1 / K1 Max reports) | frame 6.64 + cover 6.34 + duct 9.4 = 22.4 g at 100 % infill | stock: community values (not this printer); new: ESTIMATED (CAD volume × typical density) | — (M12) | research/02 C1; validation report |
| Stock duct part alone | 3.2 g (Henlor model, PC density) | duct body 7.82 cm³: 9.4 g at the PC density 1.20 used as a placeholder for the HT resin; about 9.4–10.2 g at the 1.2–1.3 g/cm³ typical of HT resins | ESTIMATED (resin TDS density unknown) | — (weigh on delivery) | validation report; `cfd-report.md` §17.4 |
| Probe adapter | 785004: 10.6–10.9 g (PLA/PETG, ESTIMATED) | reprint of the same 785004 in ASA, PC or PA-CF (R-27; mass changes with the material, not weighed); later the probe mount 11.45 g PA-CF (**not released**; the 785004 stays until M8) | ESTIMATED | — | validation report |
| Screws, inserts, washers, sleeves (new build) | stock PCB screws 3.9 g (removed) | 16.5 g (screws, inserts, the 3 tab washers and the 3 brass sleeves) | ESTIMATED | — | validation report |
| 4020 blower | 22–31 g (retailer range; 24 g used in CAD) | the same fan | ESTIMATED | — (M7/M12) | research/02 C9 |
| **Moving-mass change** | 0 | **+3.1 … +12.0 g** (with the probe mount; about 0.6–0.9 g less while the 785004 stays) | ESTIMATED | — (kitchen scale, M12/M13) | validation report |
| X moving mass | about 450 g (400–500) | +the change above | ESTIMATED | — (M13 mass test) | design-decisions, Phase 1 finding 5 |
| **X input shaper** | **77.6 Hz** (3hump_ei) | **76.6 … 77.3 Hz** | stock MEASURED; new ESTIMATED | — (`calibration.md` H, pass ≥ 76.0) | `printer.cfg.save_config`; validation report |
| **Y input shaper** | **52.0 Hz** (ei) | **51.6 … 51.9 Hz** | stock MEASURED; new ESTIMATED | — (`calibration.md` H) | same |
| Frame modes (new part) | — | rocking 1259–4436 Hz; fan plate 1416 Hz with the 4th pad, 147 Hz without | ESTIMATED | — (shaper graph) | validation report |
| Duct pitch mode (new part) | — | **1530 … 2742 Hz** on three tabs (rigid duct; E = 2200 MPa placeholder for the resin; the duct's own bending is not included) | ESTIMATED | — (shaper graph, tap test) | validation report; `cfd-report.md` §17.4 |

## 5. Envelope

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| **Front extent** (Y) | −55.0 (stock cover) | **−58.2** (cover; 3.2 mm further forward; the 4020 alone −56.5) | DESIGN; stock DERIVED (Henlor) | — (`calibration.md` D; M9) | validation report WARN |
| Right extent, inside the XY-joint band (Z 44.3…91.8) | carriage +24.2; stock cover +24.0 | cover +24.0, frame +20.0 (hard limit 24.2) | DESIGN | — (`calibration.md` D) | validation report |
| **Right extent**, all Z | +25.2 (cover screw heads at Z ≈ 35) | **+31.0** (duct body, Z 3.0…27.2, below the XY-joint band) | DESIGN; stock DERIVED | — (`calibration.md` D) | validation report; research/02 T1 |
| Left extent | −25.2 (carriage / cover screw heads) | −24.0 (cover) for the new parts; the LiDAR module sets the real left side, unchanged | DESIGN | — | validation report |
| Rear extent | 785004 rear 29.1 | probe mount 29.10 (when released); duct body **+9.8** (nothing of the duct behind Y +10, review R-01) | DESIGN | — (`calibration.md` D.4, mandatory) | validation report |
| **Lowest point above the nozzle tip** | stock duct +7.1; cover lip +6.4 | duct flat base **+3.0** (limit 2.0, `DUCT_MIN_Z`; S8 design target 3.0) | DESIGN; stock DERIVED | — (`assembly.md` step 6) | research/02 C4, C6; validation report |
| Closest printed part to the sock | stock duct hugs the sock (ignores the 3 mm rule) | duct **4.54 mm** (the ports' top-lip chamfers; the manifold's inner wall 7.8 mm); limit 3.0 (`HOT_ZONE_CLEARANCE`), S8 design target 4.5 | DESIGN | — (`assembly.md` step 6) | `cfd-report.md` §17.4; validation report |

## 6. Sensors, electrical, service, materials

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| MicroProbe offset | **x 0, y +20.3** | unchanged | stock MEASURED/config; new DESIGN | — | `tuning.cfg` `[probe]` |
| Probe `z_offset` | **0.831** | expected within ±0.05 with the 785004 kept | stock MEASURED; new ESTIMATED tolerance | — (`calibration.md` F) | `printer.cfg.save_config` |
| Probe twist range | **0.267 mm** | expected ≈ same | stock MEASURED | — (`calibration.md` H) | `printer.cfg.save_config` |
| Part-fan electrics | PB8 PWM, PB6 enable, PB3 tach (unused), 0.3 A | **unchanged**; no add-on, no config change | DESIGN | — | `electrical.md` §1 |
| Front cover removal | 2 × M3×4 at the sides; community reports the LiDAR has to be unplugged at every nozzle change | 2 × M3×6 on top; slides off forward without unplugging the LiDAR, probe or fan and without removing the duct | stock: community report; new: DESIGN | — (`assembly.md` step 7) | research/02 C5, §5; `cad/README.md` |
| Fan swap | 3 × M3×18 into the cover | duct off, then 2 × M3 ISO 7380 into frame inserts (M3×24 in CAD; the final length waits for M7) | DESIGN | — | research/02 C7; BOM F6 |
| Nozzle change | stock procedure | duct off first (3 × M3×6 with washers, drop it down); whether a wrench fits with the duct on is not known | DESIGN / INFERRED | — | `maintenance.md` §1 |
| Threads and clamping in printed parts | — | brass heat-set inserts for every screw the frame and cover take (blind holes with a 0.8 mm floor); brass compression sleeves (BT4M) in the three PCB bosses; M3 washers under the resin duct's tab screws | DESIGN | — | `cad/README.md` |
| Materials | stock cover and duct material not documented in the sources | frame and cover ASA; duct HT resin, 238 °C class after the full thermal post-cure, from a print service (fallbacks PC, MJF PA12); probe mount PA-CF; the 785004 reprinted in ASA, PC or PA-CF; no PLA or PETG on the toolhead | DESIGN | — | DD-07, DD-07a |
| Release state | in service | coupon PRINT FIRST; frame, cover, duct FIT-CHECK FIRST; probe mount NOT RELEASED | DESIGN | — | validation report |

## 7. What is still unknown

| Unknown | Effect | How it gets answered |
|---|---|---|
| The stock 4020's real P–Q curve | absolute airflow and cooling of both stock and new (the bounds span about ±20 % about the midpoint) | V1 (M16) |
| Any measured cooling performance | whether the simulated gains (layer speed ×4.4, ×4.3–5.3; part-top h ×3.3) show up in prints, and on which faces | V2, V3, V5, V6 |
| The real heater penalty | heater reserve at full fan | V4 (`calibration.md` E) |
| LiDAR window soiling, scan behaviour with the fan on | DD-02's assumption | V7 |
| The resin's heat margin near the sock | the HT-resin choice (HDT 238 °C class per the TDS) at 4.54 mm from a sock of unknown temperature | M20, V8 |
| Socket seal | unsealed, the 0.25 mm socket slots leak about 11 % of the fan flow (ESTIMATED) | `assembly.md` step 6, V2 |
| Real masses | shaper prediction | M12, M13, `calibration.md` H |
| Fit of the printed parts | release of the frame, cover and duct | coupon, then `assembly.md` checks |
| Interfaces still ESTIMATED or MISSING | LiDAR boxes (M6), 4020 holes, hole type and outlet (M7; the modelled lower hole lies in the modelled outlet), probe anchor (M8), travel clearance (M9), PCB pads (M10), snag clearance (M11), hotend version (M1), sock surface temperature (M20) | `missing-information.md` |
| Cover vs the fan screw heads | the cover may need a CAD change | `assembly.md` step 7 |
| Duct stiffness beyond the rigid-duct estimate, resin modulus | a possible new shaper peak or flutter | `calibration.md` H; `assembly.md` step 6 tap test |
