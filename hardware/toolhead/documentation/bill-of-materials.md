# Bill of materials (per toolhead)

Status per line:
- **RELEASED**: buy or print now.
- **FIT-CHECK FIRST**: the coupon confirms it before the frame is printed.
- **NOT RELEASED**: depends on MISSING, STUB or provisional data.
- **VARIANT**: depends on the CFD fan decision. Tags [V-4020], [V-SS], [V-DELTA] as in
  `electrical.md`; delete the losing rows once CFD decides.

The statuses follow `cad/exports/validation_report.md` (stub cooling) and
`validation_report_ducts.md` (duct interface v1, provisional). Screw sizes come from the CAD
sources named in each row. Where the CAD does not fix a size, it is **TBD** with the reason.

## 1. Printed parts

Masses are solid-volume upper bounds (100 % infill) from the validation reports, with ESTIMATED
densities ASA 1.07, PC 1.20, PA-CF 1.15 g/cm³.

| Part | File (`cad/exports/`) | Material | Mass, g | Qty | Status | Waiting for |
|---|---|---|---|---|---|---|
| Fit-check coupon | `3mf/fitcheck_coupon.3mf` (`stl/`, `step/`) | ASA | 2.89 | 1 | **RELEASED, print first** (validation: "PRINT FIRST") | — |
| Cooling-module frame | `3mf/cooling_module_frame.3mf` | ASA | 5.36 (stub) / 5.49 (duct v1) | 1 | NOT RELEASED (14 of 41 dependencies unconfirmed) | final duct mount points; M10 PCB pads; coupon result |
| Cover | `3mf/cover.3mf` | ASA | 7.0 (stub) / 6.91 (duct v1) | 1 | NOT RELEASED (10 of 21) | fan/duct pose; M9 front clearance (front −58.7 vs −55.0) |
| MicroProbe mount | `3mf/probe_mount.3mf` | PA-CF (PC acceptable) | 11.45 | 1 | NOT RELEASED (11 of 39; `PM_ANCHOR_CONFIRMED_M8` MISSING) | M8 (785004 anchor photo + calipers). Until then keep the 785004 |
| Duct body | not exported (Duct agent: `cad/source/ducts/`, `build_ducts()`) | PC (or PA-CF) | 9.4 (validation_ducts) / 9.29 (`duct_interface.json`) | 1 | NOT RELEASED, VARIANT (min-wall and mount-point FAILs) | CFD decision; final mount points |

Moving-mass change vs stock: −7.3 … +1.6 g with the stub (validation report, includes 9.33 g of
hardware). The fan variant changes it: Delta 28 g, Same Sky 23–31 g, stock 4020 22–31 g each.

## 2. Fasteners and inserts

| # | Item | Exact spec | Qty | Derived from | Status |
|---|---|---|---|---|---|
| F1 | PCB / module screws | **M3×30, ISO 7380 button head**, steel (8.8/10.9 or A2) | 3 | `frame.py` `FRAME_PCB_SCREW_LEN` 30: frame adds 11.2 mm (9.2 boss + 2.0 plate) to the stock M3×18/18/20. Upper tips go 0.8 deeper than stock into the carriage inserts; the lower one has 7.3 mm engagement in the heatsink (stock 8.5). Tips checked at Y −3.5 vs the Henlor carriage (validation PASS) | FIT-CHECK FIRST |
| F2 | Washer, coupon only | M3, ISO 7089 (3.2 × 7 × 0.5) | 3 | coupon plate 1.6 vs frame 2.0: the washer restores the frame's screw depth (`print-settings.md` §5) | RELEASED |
| F3 | M3 heat-set insert, brass, short | for a **Ø4.0** hole, length **≤ 4.5** (CAD 4.0). Hole depth 5.0, so a standard 5.7 mm insert does **not** fit | frame: **6** with 1 fan (2 cover + 2 fan + 2 duct); **8** with 2 fans; coupon: 1; spares: 5 | `common.py` `INSERTS["M3"]` (hole 4.0 ESTIMATED), `frame.py` `n_ins` | FIT-CHECK FIRST (hole size); count VARIANT |
| F4 | Cover screws | **M3×6, ISO 7380** | 2 | `frame.py` hardware list: through the 1.2 mm cover top wall → 4.8 mm into an insert hole 5.0 deep. **Do not use M3×8**: it bottoms out | NOT RELEASED (follows the cover) |
| F5 | Duct-to-frame screws | **M3×6, ISO 7380** | 2 | duct v1 tab 2.5 mm thick (`duct_interface.json` `tab_size_mm`) + 3.5 mm in the insert (the stub tab is 3.0 → 3.0). Max usable length 2.5 + 5.0 = 7.5 | NOT RELEASED (duct interface provisional) |
| F6 | Fan-to-frame screws | **M3 × L, TBD.** Rule: L = (fan hole through-length) + 3.5 … 4.5, and **≤ through-length + 5.0** | 2 per fan (diagonal pair) | `duct_interface.json` gives `through_length` 20.0 for the 4020, ESTIMATED from the frame envelope. The stock 4020 is held by M3×18 through the same holes (research/02 C7), so its real hole length is probably < 20. Delta and Same Sky hole lengths are not in the CAD | VARIANT, TBD: measure the hole through-length of the chosen fan (M7) |
| | [V-4020] if the through-length really is 20.0 | M3×24 (ISO 4762/DIN 912, check availability); M3×25 would bottom out exactly at 5.0 | 2 / 4 | as above | VARIANT, TBD |
| F7 | M2.5 heat-set insert, brass, short | for a **Ø3.6** hole, length ≤ 4.5 (CAD 4.0), hole depth 5.0 | probe mount: 2; coupon: 2; spares: 4 | `common.py` `INSERTS["M2.5"]` (ESTIMATED) | FIT-CHECK FIRST |
| F8 | Probe screws | **M2.5×5** (BIQU kit), through the 2.1 mm flange → 2.9 mm in the insert | 2 | `probe_mount.py` hardware; BIQU manual | RELEASED (reuse the kit's) |
| F9 | Probe-mount anchor screws | **~M2, length TBD**: reuse 785004's. The holes are Ø2.4 clearance with a Ø4.2 × 2.95 counterbore | 2 | `probe_mount.py` `PM_ANCHOR_*` (DERIVED from 785004); the size and length are **MISSING (M8)** | NOT RELEASED |
| F10 | Cable ties | 2.5 mm wide (slots 1.6 × 3.0 frame, 1.6 × 3.2 probe mount) | 3 (2 frame top corners, 1 probe-mount roof) | `frame.py` `TIE_SLOT`, `probe_mount.py` | RELEASED |

**Stock parts removed and kept for rollback** (`calibration.md` §5):
- front cover + duct;
- 2 × M3×4 ultra-low SHCS (cover to carriage, research/02 C5);
- 3 × M3×18 BHCS (4020 to cover, C7);
- PCB screws 2 × M3×18 BHCS + 1 × M3×20 BHCS (N6/N7).

**Stock parts reused unchanged:** carriage, hotend, heatsink, extruder, nozzle PCB, 3010 hotend
fan, LiDAR + bracket, MicroProbe + 785004 (until F9 and the probe mount are released).

## 3. Fans and electrical parts (VARIANT)

Prices are research/03 §11–12 snapshots (2026-11-01) and add-on prices from search snapshots
(2026-11-11). All SECONDARY: re-check at checkout. The quantity in brackets is the dual-fan case.

| Variant | Item | Qty | EU source, price | Status |
|---|---|---|---|---|
| [V-4020] | Creality 4020 blower 24 V 4-pin, 4004110132 (stock fan reused) | 0 (+1) | 3D-printer shops ≈ $10–14 | VARIANT; 2 fans only if `electrical.md` §4.4 passes at 0.6 A |
| [V-4020] | 4-pin Y-splice for 2 fans (one FG) | 0 (1) | make from a spare 4020 lead | VARIANT |
| [V-SS] | **Same Sky CBM-5015BF-175-459-22** (12 V, PWM + tach) | 1 + 1 spare (2 + 1) | radiomag.com.de **€23.18** (1+), 10–14 d (fetched); DigiKey EU (stock 256 in snapshot) | VARIANT |
| [V-SS] | 24→12 V 1 A buck: **TRACO TSR 1-24120** (preferred) | 1 | DigiKey EU ≈ €5.1–5.2; RS ≈ €5.93 ex VAT; SOS €5.46 ex VAT | VARIANT |
| [V-SS] | alt.: RECOM R-78E12-1.0/X9 (15–27 V in) | (1) | DigiKey EU ≈ €3.43; Bürklin €3.51 | VARIANT |
| [V-SS] | alt.: Pololu D24V10F12 (#2834) | (1) | exp-tech.de €7.96 ex VAT; opencircuit €9.00; botland €10.90 | VARIANT |
| [V-SS] | 2 × 10 µF ceramic (50 V in, 25 V out), optional per the buck datasheet | 2 | any distributor, < €1 (ESTIMATED) | VARIANT |
| [V-DELTA] | **Delta BFB0524HH-F00** (24 V, FG) | 1 + 1 spare (2 + 1) | DigiKey EU €13.89–15.30 ex VAT; Mouser EU €12.35 (one snapshot); radiomag €25.10. Order **-F00**: Mouser marks the plain part not shipped to EU consumers | VARIANT |
| [V-DELTA] | MOSFET add-on: IRLML0040 (Q1), SS14 or 1N5819 (D1), BZX84C5V1 (DZ1), 22 kΩ / 100 Ω / 100 kΩ, small perfboard, heat-shrink | 1 set (+1 spare set) | TME / DigiKey / Mouser, ≈ €2 per set (ESTIMATED) | VARIANT, not released until the PB6 probe (`electrical.md` §4) |
| all non-stock | 4-pin pigtail for the board's "Model Fan" socket | 1 | pitch 1.25 mm vs XH2.54: **MEASURE** first (`electrical.md` §1) | VARIANT |
| all | 26 AWG silicone wire, heat-shrink | — | — | RELEASED |

The buck and MOSFET add-on still need mounting points on the frame (CAD open item, STATUS step 3).

## 4. Tools

| Tool | Used for |
|---|---|
| Multimeter (DC V with 0.1 mV resolution, mA range), alligator leads, 2 back-probe pins or sewing needles | PB6 probing (`electrical.md` §4), buck check |
| Soldering iron with temperature control, M2.5 and M3 heat-set insert tips | inserts (`print-settings.md` §3) |
| Flat cold metal block (≈ 20 × 20 mm) | squaring inserts |
| Fine soldering tip, solder, heat gun | add-on wiring |
| Hex keys 1.5 / 2.0 / 2.5 mm (ball-end 2.0 helps on ISO 7380 M3) | ISO 7380 M3 = 2.0; M2.5×5 BIQU = 2.0 (DIN 912 M2.5); ~M2 anchors = 1.5 (if SHCS) |
| Calipers ±0.05, feeler gauges 0.05–0.5, a 2 mm drill shank as a gauge | coupon, duct clearance |
| Kitchen scale ±1 g | masses (M12) |
| Flush cutters, deburring tool, Ø3.4 and Ø4.0 drills (hand clean-up only) | print clean-up |
| Filament dryer, dry box | PC / PA-CF (`print-settings.md` §4) |
| Glue stick | PC / PA-CF bed release |
| Hardened 0.4 nozzle and nozzle wrench | PA-CF; nozzle change (`maintenance.md` §1) |
| IR thermometer (optional) | buck and switch temperature |
