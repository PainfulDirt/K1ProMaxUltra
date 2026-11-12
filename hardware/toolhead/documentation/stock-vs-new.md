# Stock vs new toolhead

Side by side: the stock K1 Max front cover with its duct and 4020, against the new build (frame +
cover in ASA, S7 duct in PC, the same stock 4020; everything else stock and in place).

**There are no measured performance numbers for the new toolhead yet.** Nothing has been printed or
fitted. The "Measured after fitting" column is empty on purpose. The only MEASURED values on this
page are the user's existing calibrations of the stock toolhead.

Tags, per value:
- **MEASURED**: measured on this printer (today: the stock calibrations in `printer.cfg.save_config`
  and `variables.cfg`).
- **SIMULATED**: OpenFOAM, `cfd-report.md` (absolute values ±20–30 %; rankings robust; ties inside
  ±3 % on means, ±5 % on the weakest sector).
- **ESTIMATED**: hand calculation or arithmetic on estimated inputs.
- **DESIGN**: a property of the CAD or the design decision, true by construction.

CFD values are given at both 4020 bounds, **lower / upper** (191 / 390 Pa shut-off). The stock
4020's real curve is unknown (test V1); the lower bound is the more plausible one
(`cfd-report.md` §10).

## 1. Part cooling (S7 vs the stock duct, same 4020)

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Fan flow Q [L/s] | 0.804 / 1.199 | 0.801 / 1.211 | SIMULATED | — (V1, V2) | `cfd-report.md` §10 |
| Layer annulus speed, r 1–6 mm, Z +0.3 [m/s] | 1.83 / 3.47 | **8.84 / 13.34** (×4.8 / ×3.8) | SIMULATED | — (V3) | §10 |
| Weakest of 8 sectors [m/s] | 0.35 / 0.68 | **6.28 / 9.16** (×18 / ×13) | SIMULATED | — (V3) | §10 |
| Symmetry min/mean | 0.19 / 0.20 | 0.71 / 0.69 | SIMULATED | — (V3: pass ≥ 0.5) | §10 |
| Part top r ≤ 5, near-wall U0.3 [m/s] | 1.38 / 2.74 | **7.81 / 12.28** (×5.7 / ×4.5) | SIMULATED | — | §10 |
| Part side faces, top 3 mm, U0.3 [m/s] | 0.62 / 1.04 | 2.63 / 4.07 | SIMULATED | — | §10 |
| Part top r ≤ 5, h (thermal proxy) [W/m²K] | 42 / 54 | **147 / 216** (×3.5 / ×4.0) | SIMULATED (proxy, comparative) | — (V5, V6) | §11 |
| Heat removed from the part, top + sides [W] | 10.2 / 14.8 | 20.3 / 26.7 (×2.0 / ×1.8) | SIMULATED (proxy) | — | §11 |
| Weak side faces (h, −X left / +Y rear) [W/m²K] | 44 / 17 (lower); 72 / 31 (upper) | 37 / 48 (lower); 66 / 70 (upper) | SIMULATED (proxy) | — (V5 per direction) | §11 |
| Outlets | slots around the sock at Z ≈ 7–10, above the sock bottom | 5 wedge ports (6 × 3 mm, 25° floor, 45° ceiling, 12° yaw) just outside a 3 mm sock clearance, lips at Z 2.44 | DESIGN | — | §6.1, §12.3 |
| Part fans | 1 × stock 4020 | the same 1 × stock 4020 | DESIGN | — | DD-01 |

## 2. Nozzle and heater

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Nozzle cone near-wall U0.3 [m/s] | 0.95 / 1.90 | 7.17 / 10.98 | SIMULATED | — | `cfd-report.md` §10 |
| Nozzle convective loss at 100 % fan [W] | 1.16 / 1.65 | 4.38 / 5.57 | SIMULATED (proxy) | — | §11 |
| Sock convective loss at 100 % fan [W] (sock surface assumed 150 °C) | 6.8 / 9.5 | 9.8 / 12.3 | SIMULATED (proxy) + ESTIMATED sock temperature | — | §11 |
| **Extra heater demand at 100 % fan** | — | **+6.2 / +6.8 W** (about 10 % of the 60 W heater); about 2–3 W at 40–60 % fan | SIMULATED (proxy; energy balance closes only to 47–56 % on S7, indicative) | — (V4) | §11 |
| MPC `fan_ambient_transfer` at 100 % [W/K] | **0.1166** | ≈ 0.14–0.15 | stock MEASURED; new ESTIMATED (my arithmetic, `calibration.md` E) | — (V4, `calibration.md` E) | `printer.cfg.save_config`; `calibration.md` |
| MPC `ambient_transfer` (fan 0) [W/K] | 0.0800 | expected about the same | stock MEASURED; new ESTIMATED | — | `printer.cfg.save_config` |
| Hotend, heater, sock | stock 2023 ceramic, 60 W | unchanged | DESIGN | — | DD-01 |

## 3. LiDAR

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Laser-line region air speed, mean / max (fan 100 %, upper 4020 bound, nozzle 3 mm above a bare bed) [m/s] | 0.18 / 0.41 | 0.87 / 1.50 | SIMULATED | — (V7) | `cfd-report.md` §13.1 |
| Window region air speed, mean / max (same case) [m/s] | 0.087 / 0.18 | 0.17 / 0.25 (moving downward, away from the module) | SIMULATED | — (V7) | §13.1 |
| Air speed at 0 % fan | 0 (no part-fan flow) | 0 (no part-fan flow) | DESIGN (not simulated: the model has no other air source) | — | §13.1 |
| Optical effect of the air | — | ≈ 0.3 µm spot shift for a 20 K gradient, below the 1–2 µm repeatability | ESTIMATED | — | DD-02 |
| Module, bracket, pose | as fitted | unchanged; no new part enters the LiDAR boxes or the sheet (tightest: cover 0.50 mm to the ESTIMATED body box) | DESIGN (boxes ESTIMATED, M6) | — (`calibration.md` G) | DD-02, validation report |
| LiDAR offsets X / Y | **−36.013 / −21.336** | unchanged (no recalibration) | stock MEASURED; new DESIGN | — (`calibration.md` G dry run) | `variables.cfg` |
| LiDAR twist range | **0.181 mm** | expected ≈ same (re-run with the twist calibration) | stock MEASURED | — (`calibration.md` H) | `variables.cfg` |

## 4. Mass and dynamics

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| Cover + duct (without fan) | 23.8 g (K1, community measured) … 32.5 g (K1 / K1 Max reports) | frame 5.84 + cover 6.42 + duct 9.24 = 21.5 g at 100 % infill | stock: community values (not this printer); new: ESTIMATED (CAD volume × typical density) | — (M12) | research/02 C1; validation report |
| Stock duct part alone | 3.2 g (Henlor model, PC density) | duct body 9.24 g PC (8.2 g if it were ASA) | ESTIMATED | — | `cfd-report.md` §12.3 |
| Probe adapter | 785004: 10.6–10.9 g (PLA/PETG) | probe mount 11.45 g PA-CF (**not released**; 785004 stays until M8) | ESTIMATED | — | validation report |
| Screws and inserts (new build) | stock PCB screws 3.9 g (removed) | 13.73 g (3 × M3×30, 2 × M3×24, 4 × M3×6, 6 M3 + 2 M2.5 inserts, probe screws) | ESTIMATED | — | validation report |
| 4020 blower | 22–31 g (retailer range; 24 g used in CAD) | the same fan | ESTIMATED | — (M7/M12) | research/02 C9 |
| **Moving-mass change** | 0 | **−0.6 … +8.4 g** (with the probe mount; about 0.6–0.9 g less while the 785004 stays) | ESTIMATED | — (kitchen scale, M12/M13) | validation report |
| X moving mass | about 450 g (400–500) | +the change above | ESTIMATED | — (M13 mass test) | design-decisions, Phase 1 finding 5 |
| **X input shaper** | **77.6 Hz** (3hump_ei) | **76.9 … 77.7 Hz** | stock MEASURED; new ESTIMATED | — (`calibration.md` H, pass ≥ 76.0) | `printer.cfg.save_config`; validation report |
| **Y input shaper** | **52.0 Hz** (ei) | **51.8 … 52.0 Hz** | stock MEASURED; new ESTIMATED | — (`calibration.md` H) | same |
| Frame modes (new part) | — | rocking 1168–4440 Hz; fan plate 1416 Hz with the 4th pad, 147 Hz without | ESTIMATED | — (shaper graph) | validation report |
| Duct mode (new part) | — | **unknown**: not estimated (two tabs + socket, 45 mm lever) | — | — (shaper graph, rattle check) | `cfd-report.md` §16 |

## 5. Envelope

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| **Front extent** (Y) | −55.0 (stock cover) | **−58.2** (cover; 3.2 mm further forward; the 4020 alone −56.5) | DESIGN; stock DERIVED (Henlor) | — (`calibration.md` D; M9) | validation report WARN |
| Right extent, inside the XY-joint band (Z 44.3…91.8) | carriage +24.2; stock cover +24.0 | cover +24.0, frame +20.0 (hard limit 24.2) | DESIGN | — (`calibration.md` D) | validation report |
| **Right extent**, all Z | +25.2 (cover screw heads at Z ≈ 35) | **+31.0** (duct body, only below Z 23, outside the joint band) | DESIGN; stock DERIVED | — (`calibration.md` D) | validation report; research/02 T1 |
| Left extent | −25.2 (carriage / cover screw heads) | −24.0 (cover) for the new parts; the LiDAR module sets the real left side, unchanged | DESIGN | — | validation report |
| Rear extent | 785004 rear 29.1 | probe mount 29.10 (when released); duct body 27.5 | DESIGN | — | validation report |
| **Lowest point above the nozzle tip** | stock duct +7.1; cover lip +6.4 | duct lips **+2.44** (limit 2.0, `DUCT_MIN_Z`) | DESIGN; stock DERIVED | — (`assembly.md` step 6) | research/02 C4, C6; validation report |
| Closest printed part to the sock | stock duct hugs the sock (ignores the 3 mm rule) | duct 3.35 mm (limit 3.0, `HOT_ZONE_CLEARANCE`) | DESIGN | — (`assembly.md` step 6) | `cfd-report.md` §6.1; validation report |

## 6. Sensors, electrical, service, materials

| Quantity | Stock | New | Tag | Measured after fitting | Source |
|---|---|---|---|---|---|
| MicroProbe offset | **x 0, y +20.3** | unchanged | stock MEASURED/config; new DESIGN | — | `tuning.cfg` `[probe]` |
| Probe `z_offset` | **0.831** | expected within ±0.05 with the 785004 kept | stock MEASURED; new ESTIMATED tolerance | — (`calibration.md` F) | `printer.cfg.save_config` |
| Probe twist range | **0.267 mm** | expected ≈ same | stock MEASURED | — (`calibration.md` H) | `printer.cfg.save_config` |
| Part-fan electrics | PB8 PWM, PB6 enable, PB3 tach (unused), 0.3 A | **unchanged**; no add-on, no config change | DESIGN | — | `electrical.md` §1 |
| Front cover removal | 2 × M3×4 at the sides; community reports the LiDAR has to be unplugged at every nozzle change | 2 × M3×6 on top; slides off forward without unplugging the LiDAR, probe or fan and without removing the duct | stock: community report; new: DESIGN | — (`assembly.md` step 7) | research/02 C5, §5; `cad/README.md` |
| Fan swap | 3 × M3×18 into the cover | duct off, then 2 × M3×24 into frame inserts | DESIGN | — | research/02 C7; BOM |
| Nozzle change | stock procedure | duct off first (2 × M3×6, drop it down); whether a wrench fits with the duct on is not known | DESIGN / INFERRED | — | `maintenance.md` §1 |
| Threads in printed parts | — | brass heat-set inserts for every screw the new parts take | DESIGN | — | `cad/README.md` |
| Materials | stock cover and duct material not documented in the sources | frame and cover ASA; duct PC (or PA-CF); probe mount PA-CF; no PLA/PETG anywhere | DESIGN | — | DD-07 |
| Release state | in service | coupon PRINT FIRST; frame, cover, duct FIT-CHECK FIRST; probe mount NOT RELEASED | DESIGN | — | validation report |

## 7. What is still unknown

| Unknown | Effect | How it gets answered |
|---|---|---|
| The stock 4020's real P–Q curve | absolute airflow and cooling of both stock and new (the bounds span about ±20 % about the midpoint); the Same Sky upgrade decision | V1 (M16) |
| Any measured cooling performance | whether the simulated ×3.5–×4.8 gains show up in prints, and in which directions | V2, V3, V5, V6 |
| The real heater penalty | heater reserve at full fan | V4 (`calibration.md` E) |
| LiDAR window soiling, scan behaviour with the fan on | DD-02's assumption | V7 |
| Lip warping near the heater | the PC choice and the 3 mm clearance | V8 |
| Real masses | shaper prediction | M12, M13, `calibration.md` H |
| Fit of the printed parts | release of the frame, cover and duct | coupon, then `assembly.md` checks |
| Interfaces still ESTIMATED or MISSING | LiDAR boxes (M6), 4020 holes and outlet (M7), probe anchor (M8), travel clearance (M9), PCB pads (M10), hotend version (M1), sock surface temperature | `missing-information.md` |
| Cover vs the fan screw heads | the cover may need a CAD change | `assembly.md` step 7 |
| Duct cantilever stiffness | a possible new shaper peak or flutter | `calibration.md` H; `assembly.md` step 6 |
