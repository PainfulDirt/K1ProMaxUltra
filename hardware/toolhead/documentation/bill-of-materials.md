# Bill of materials (per toolhead)

The build is decided (DD-01): **one stock Creality 4020 blower (the one already fitted) + the S8
duct + a new cooling-module frame and cover** on the PCB's three-hole pattern. The carriage, hotend,
extruder, nozzle PCB, 3010, LiDAR and MicroProbe positions are stock and unchanged. The electrics are
unchanged too (stock PB8 / PB6 / PB3, `electrical.md` §1). This page is the BOM for that build.
The duct body is HT resin from a print service (DD-07a, the user's decision). Two fans and the Delta
are rejected (DD-01) and are not listed. The Same Sky 5015 is not buildable in this architecture
(§3).

Release status per line (from `cad/exports/validation_report.md`):
- **PRINT FIRST**: the fit-check coupon. It exists to confirm the ESTIMATED values.
- **FIT-CHECK FIRST**: print or order it after the coupon passes and the listed M# are answered,
  then check it on the printer before trusting it (`assembly.md`).
- **NOT RELEASED**: depends on MISSING data. Do not print it for use.
- **RELEASED**: buy or use now.

Screw sizes come from the CAD sources named in each row (`cad/README.md` "BOM"). M# items are in
`missing-information.md`.

## 1. Printed parts

Masses are solid-volume upper bounds (100 % infill) from the validation report, with ESTIMATED
densities ASA 1.07, PC 1.20, PA-CF 1.15 g/cm³ (typical TDS values; use your spool's datasheet). The
duct's HT resin uses the PC density 1.20 as a placeholder until the resin TDS is known; HT resins are
typically 1.2–1.3 g/cm³ (`cfd-report.md` §17.4), so about 9.4–10.2 g.
Files: `cad/exports/3mf/<name>.3mf`, `cad/exports/stl/<name>.stl`, `cad/exports/step/<name>.step`.
Print settings and the service order: `print-settings.md`.

| Part | File name | Material | Mass, g | Qty | Status | Waiting for |
|---|---|---|---|---|---|---|
| Fit-check coupon | `fitcheck_coupon` | ASA (same spool as the frame) | 2.99 | 1 | **PRINT FIRST** | — |
| Cooling-module frame | `cooling_module_frame` | ASA | 6.64 | 1 | **FIT-CHECK FIRST** (13 of 49 dependencies unconfirmed) | coupon result; M10 (PCB pads, component zone, 4th pad); M7 (4020 hole positions, hole type and through-length); M6 (LiDAR boxes); insert hole size; BT4M sleeve size (ESTIMATED until bought) |
| Cover | `cover` | ASA | 6.34 | 1 | **FIT-CHECK FIRST** (4 of 19) | M7 (4020 intake face and inlet Ø28); M6 (LiDAR boxes); M9 (front clearance: front −58.2 vs −55.0) |
| Duct body (S8) | `duct_body` (send the STEP) | **HT resin, 238 °C class** (HDT at 0.45 MPa after the full thermal post-cure, per the TDS), **from a print service** (DD-07a). Fallbacks: PC (FDM, `print-settings.md` §1) or MJF PA12 | 9.4 (PC density placeholder) | **2** (one spare: a resin lip chips rather than bends) | **FIT-CHECK FIRST** (14 of 26) | M7 (4020 outlet 13 × 17, nozzle depth, hole positions, socket fit); M1 (hotend version); M8 (probe keep-out); M10; M6. Order conditions: `print-settings.md` "Duct from a print service" |
| 785004 probe adapter, reprint | the unchanged Printables 785004 STL (research/01 H.1) | **ASA, PC or PA-CF** (review R-27: today's adapter is of unknown material, possibly PLA/PETG, 5.1 mm from the sock) | not weighed (8.55 cm³: about 9.1–10.3 g depending on the material, ESTIMATED) | 1 | reprint before or with this build | — (same geometry, so the probe calibration does not change) |
| MicroProbe mount | `probe_mount` | **PA-CF** (PC acceptable) | 11.45 | 1 | **NOT RELEASED** (12 of 39; `PM_ANCHOR_CONFIRMED_M8` MISSING) | M8 (785004 anchor, photo + calipers). Until then keep the (reprinted) 785004 |

No PLA or PETG for any of these parts (DD-07).

Moving-mass change vs stock: **+3.1 … +12.0 g** (validation report). That is the printed parts at
100 % infill plus 16.5 g of screws, inserts, washers and the 3 brass sleeves (50.3 g added in all),
minus the stock cover + duct (23.8–32.5 g), the 785004 adapter (10.6–10.9 g, PLA/PETG ESTIMATED) and
the stock PCB screws (3.9 g). The range assumes the new probe mount replaces the 785004. While the
785004 stays (probe mount not released), the change is about 0.6–0.9 g lower (11.45 g not added,
10.6–10.9 g not removed); its reprint in ASA/PC/PA-CF changes that by an amount not weighed yet.
Predicted X shaper 76.6 … 77.3 Hz (77.6 Hz today), Y 51.6 … 51.9 Hz (52.0 Hz today), ESTIMATED.

## 2. Fasteners, inserts, sleeves and seal

| # | Item | Exact spec | Qty | Derived from | Status |
|---|---|---|---|---|---|
| F1 | PCB / module screws | **M3×30, ISO 7380 button head**, steel (8.8/10.9 or A2) | 3 | `frame.py` `FRAME_PCB_SCREW_LEN` 30: the frame adds 11.2 mm (9.2 boss + 2.0 plate) to the stock M3×18 / M3×18 / M3×20. The upper tips go 0.8 mm deeper than stock into the carriage inserts; the lower one has 7.3 mm engagement in the heatsink (stock 8.5). Tips checked at Y −3.5 against the Henlor carriage (validation PASS) | FIT-CHECK FIRST |
| F2 | Washer, coupon only | M3, ISO 7089 (3.2 × 7 × 0.5) | 3 | the coupon plate is 1.6 mm against the frame's 2.0 mm; the washer restores the frame's screw depth (`print-settings.md` §5) | RELEASED |
| F3 | M3 heat-set insert, brass, short | for a **Ø4.0** hole, OD ≤ 5.0, length **4.0** (CAD). The fan and duct-tab holes are blind, **4.2 mm deep** with a 0.8 mm floor; the cover holes 6.0 mm deep. A longer insert (the common 5.7 mm type) does **not** fit | frame: **7** (2 fan, 3 duct T_left / T_right / T_3, 2 cover); coupon: 1; spares: 5 | `common.py` `INSERTS["M3"]` (hole 4.0 ESTIMATED); `cad/README.md` BOM | FIT-CHECK FIRST (hole size, confirmed by the coupon) |
| F4 | Cover screws | **M3×6, ISO 7380** | 2 | through the 1.2 mm cover top wall, 4.0 mm in the insert; the tip ends 1.2 mm above the hole floor (safe length 4.5…6.7, validation PASS) | FIT-CHECK FIRST (follows the cover) |
| F5 | Duct-tab screws | **M3×6, ISO 7380** | 3 (T_left, T_right, T_3) | `cooling.py` `DUCT_TAB_SCREW_LEN` 6: washer 0.5 + tab 2.5 + 3.0 in the insert; the tip ends 1.2 mm above the hole floor (safe length 5.5…6.7, validation PASS) | FIT-CHECK FIRST (follows the duct) |
| F5a | Duct-tab washers | **M3, ISO 7089** (3.2 × 7 × 0.5), steel | 3 | DD-07a: the resin tab is brittle; the washer spreads the head load. Tighten only until the tab seats | FIT-CHECK FIRST (follows the duct) |
| F6 | Fan-to-frame screws | **M3, ISO 7380 only** (an ISO 4762 head is 3.0 mm tall and stands 1.3 mm proud of the cover, review R-15). CAD length 24; **the final length is pending M7** | 2 (the 4020's diagonal pair (−18.65, 60.3) and (16.05, 25.6)) | `frame.py` `FRAME_FAN_SCREW_LEN` 24 = through-length 20 (ESTIMATED, M7) + 4. With a 20 mm through-length the safe length is **22.5…23.7 mm**, so M3×24 ends 0.2 mm from the insert-hole floor (validation WARN; no standard ISO 7380 length fits). The insert holes are blind, so an over-long screw stops on the floor instead of entering the PCB zone, but it then cannot clamp the fan. The stock fan is held by M3×18 through the same holes (research/02 C7), which suggests tapping holes, not 20 mm clearance holes. Measure the hole type and through-length (M7), then choose the length; if the holes are tapping holes the joint changes (review R-03) | FIT-CHECK FIRST; **length and joint depend on M7** |
| F7 | M2.5 heat-set insert, brass, short | for a **Ø3.6** hole, length ≤ 4.5 (CAD 4.0) | coupon: 2; probe mount: 2 (later); spares: 4 | `common.py` `INSERTS["M2.5"]` (ESTIMATED) | coupon: RELEASED; probe mount: NOT RELEASED |
| F8 | Probe screws | **M2.5×5** (BIQU kit), through the 2.1 mm flange, then 2.9 mm into the insert | 2 | `probe_mount.py` hardware; BIQU manual | RELEASED (reuse the kit's; also used on the coupon) |
| F9 | Probe-mount anchor screws | **~M2, length unknown**: reuse 785004's. The holes are Ø2.4 clearance with a Ø4.2 × 2.95 counterbore | 2 | `probe_mount.py` `PM_ANCHOR_*` (DERIVED from 785004); size and length **MISSING (M8)** | NOT RELEASED |
| F10 | Cable ties | 2.5 mm wide (slots 1.6 × 3.0 in the frame, 1.6 × 3.2 in the probe mount) | 3 (2 frame top corners, 1 probe-mount roof; the probe-mount one only once that part is released) | `frame.py` `TIE_SLOT`, `probe_mount.py` | RELEASED |
| F11 | Brass compression sleeves | **Albion Alloys BT4M** brass tube, 4.0 OD × 0.45 wall (ID 3.1), sold in 305 mm lengths | 1 length → cut **3 × 11.10 mm** | `cad/README.md` "Brass compression sleeves (R-04)": one per PCB boss, in a Ø4.1 bore, 0.1 mm shorter than the ASA stack so the preload runs metal → PCB → 3010. ESTIMATED until bought; the lower-left bore is a close fit (Ø4.05), ream it to fit | FIT-CHECK FIRST (follows the frame) |
| F12 | Fan-socket seal | Kapton (polyimide) tape, or a 0.5–1 mm thin foam gasket on the socket rim | a short strip | `cfd-report.md` §17.9: the socket has 0.25 mm clearance per side; unsealed, those slots leak about 0.09 L/s, about 11 % of the fan flow (ESTIMATED, hand calculation). The CFD assumes a sealed inlet | RELEASED (consumable) |

**Insert length rule (all M3 and M2.5 inserts):** the CAD inserts are 4.0 mm long. Every M3 insert
hole in the frame is blind with a 0.8 mm floor (review R-03): 4.2 mm deep in the fan standoffs and
duct lugs, 6.0 mm in the cover shelf. Screw lengths (F4, F5, F6) were checked against that floor.
Changing insert length means changing screw lengths and re-running `validate.py`.

**Fan screw heads and the cover:** the F6 heads (ISO 7380, Ø5.7 × 1.65) stand proud of the 4020's
front face. The cover therefore has Ø6.7 through-holes over both, with 0.5 mm radial clearance
(review R-15), and a 2.0 mm hex key reaches the screws through them with the cover on. `validate.py`
models every added screw head and its driver path (PASS). Still check at the cover fit-check
(`assembly.md` step 7): the hole positions follow the ESTIMATED 4020 hole positions (M7).

**Stock parts removed and kept for rollback** (`assembly.md` §3):
- front cover + duct;
- 2 × M3×4 ultra-low SHCS (cover to carriage, research/02 C5);
- 3 × M3×18 BHCS (4020 to the stock cover, C7);
- PCB screws: 2 × M3×18 BHCS + 1 × M3×20 BHCS (N6/N7).

**Stock parts reused unchanged:** carriage, hotend, heatsink, extruder, nozzle PCB, 3010 hotend
fan, **the fitted 4020 blower**, LiDAR + bracket, MicroProbe. The 785004 adapter keeps its geometry
but is reprinted in ASA, PC or PA-CF (§1); keep the old one for rollback.

**Electrical:** nothing to buy. The 4020 stays on the board's "Model Fan" socket. Only if its lead
does not reach after the move (the fan sits 6–7 mm further forward than stock: Y −56.5…−36.5
against the stock −49.4…−30.2, `interfaces.py` `STOCK_4020_POS`; lead length 60 mm, research/02 F3):
one 4-pin extension. The pitch is unconfirmed (1.25 mm vs XH2.54, **MEASURE** first,
`electrical.md` §1.1). Do not cut the stock fan lead.

### Optional

| Item | Qty | Why | Price (snapshot) |
|---|---|---|---|
| Creality K1 / K1 Max 4020 blower, 24 V 0.3 A, 4-pin, **Creality 4004110132** | 1 spare | bench test V1 (P–Q curve, `cfd-report.md` §15 / `validation.md`) and the M7 measurements without taking the fitted fan off; if the holes turn out to be tapping holes, the spare is the one to drill, so the fitted fan stays intact for rollback (review R-03); and a spare | about $10–14 (`cfd-report.md` §12.1, research/03 §11–12 snapshot 2026-11-01; re-check at checkout) |

## 3. Same Sky CBM-5015BF: not buildable in this architecture (record only; do not order)

**The Same Sky does not fit this frame and cover** (review R-13, `cfd-report.md` §17.8, DD-01): in
the XY-joint band it needs 51.6 mm of housing + 1.0 mm stall margin + 2 × 1.7 mm of cover wall and
gap = 56.0 mm, and 55.2 mm is available. It would need an open-sided or asymmetric cover and an
accepted 0 mm stall margin, and the S8 duct has no Same Sky variant (S8SS was not run). The list
below is kept as the record of what the upgrade would have needed. Its original trigger was: bench
test V1 measures the stock 4020 at its lower bound (191 Pa shut-off), **and** the V5/V6 overhang and
bridge prints show insufficient cooling (DD-01 "Would reverse it", `cfd-report.md` §12.1). The
first-round CFD gain on S7 was +13 % layer speed over the 4020's lower bound, at +7.4 g plus a
3–6 g buck, a weaker minimum sector (−11 %) and +13 % nozzle loss (`cfd-report.md` §10); its thermal
figure (+21 % part-top h) came from an unclosed balance and is withdrawn (§17.7).

| Item | Qty | EU source, price (snapshots, SECONDARY; re-check at checkout) |
|---|---|---|
| **Same Sky CBM-5015BF-175-459-22** (12 V, 4-wire PWM + tach) | 1 fitted + 1 spare | radiomag.com.de **€23.18** (1+), 10–14 d (fetched); DigiKey EU (stock 256 in the snapshot) |
| 24→12 V, 1 A buck: **TRACO TSR 1-24120** (preferred) | 1 | DigiKey EU ≈ €5.1–5.2; RS ≈ €5.93 ex VAT; SOS €5.46 ex VAT |
| alt.: RECOM R-78E12-1.0/X9 (15–27 V in: measure the rail first) | (1) | DigiKey EU ≈ €3.43; Bürklin €3.51 |
| alt.: Pololu D24V10F12 (#2834) | (1) | exp-tech.de €7.96 ex VAT; opencircuit €9.00; botland €10.90 |
| 2 × 10 µF ceramic (50 V in, 25 V out), if the buck datasheet asks for them | 2 | any distributor, < €1 (ESTIMATED) |
| 4-pin pigtail for the board's "Model Fan" socket | 1 | pitch 1.25 mm vs XH2.54: **MEASURE** first (`electrical.md` §1.1) |
| 26 AWG silicone wire, heat-shrink | — | — |

Prices: radiomag fetched 2026-11-01 (research/03 §11–12); buck prices from search snapshots
2026-11-11 (`electrical.md` §2.3).

What the upgrade needs besides the parts (`electrical.md` §2):
- **A buck, not a MOSFET.** The Same Sky is a 12 V 4-wire PWM fan. It keeps PB8 (PWM) and PB6
  (supply switch) like the stock fan and must never sit behind a low-side switch (DD-05).
- **The PB6 probe is not needed for current.** One Same Sky draws 0.12 / 0.18 A (typical / max) from
  the 24 V channel through the buck, inside the 0.3 A the channel already carries (`electrical.md`
  §2.6). The probe (`electrical.md` §4, M15) is still recommended: it decides whether the tach may go
  to PB3, shows the rail voltage (needed for the R-78E option, ≤ 27 V), and checks the PWM stage
  polarity and pull-up.
- **Config:** `cycle_time: 0.002` (the fan's PWM minimum is 200 Hz). That is a printer-config change
  (`components/fans/klipper/part_fan_samesky.cfg`, example only), left to the user.
- **CAD:** a different duct variant and cover (not modelled for S8; see above) and a frame
  regenerated from that interface (the Same Sky's holes are Ø4.5, `interfaces.py`). **No buck mount
  is modelled** (`cad/README.md`).
- **Calibration:** MPC, shaper and fan checks again (`calibration.md`).

## 4. Tools

| Tool | Used for |
|---|---|
| Soldering iron with temperature control, M2.5 and M3 heat-set insert tips | inserts (`print-settings.md` §3) |
| Flat cold metal block (≈ 20 × 20 mm) | squaring inserts |
| Hex keys 1.5 / 2.0 / 2.5 mm (ball-end 2.0 helps on ISO 7380 M3) | ISO 7380 M3 (all new M3 screws) = 2.0; M2.5×5 BIQU = 2.0 (DIN 912 M2.5); ~M2 anchors = 1.5 (if SHCS); stock M3×4 ultra-low = 2.0 (ESTIMATED); the stock M3×18 / M3×20 BHCS = 2.0 |
| Calipers ±0.05, feeler gauges 0.05–0.5 | coupon, part checks, hole through-length (M7) |
| Gauges: a 2.0 mm and a 3.0 mm drill shank (or feeler stack) | duct lowest point ≥ 2.0 mm above the tip; ≥ 3 mm duct-to-sock clearance (`assembly.md`); a 3.0 mm shank also checks the port height |
| Kitchen scale ±1 g | masses (M12) |
| Flush cutters, deburring tool, Ø3.4 and Ø4.0 drills (hand clean-up only) | print clean-up; support removal (FDM fallback duct only) |
| Fine razor saw or small tube cutter, deburring tool, Ø4.05 reamer or drill | cutting the 3 BT4M sleeves to 11.10 mm; fitting the lower-left close-fit bore (`cad/README.md`) |
| Filament dryer, dry box | PC / PA-CF (`print-settings.md` §4) |
| Glue stick | PC / PA-CF bed release |
| Hardened 0.4 nozzle | PA-CF (`print-settings.md` §2.2) |
| Multimeter (DC V with 0.1 mV resolution, mA range), alligator leads, 2 back-probe pins | only for the Same Sky option, not buildable as modelled (PB6 probe, buck check, `electrical.md` §4) |
| Fine soldering tip, solder, heat gun, IR thermometer (optional) | only for the Same Sky option (buck wiring and temperature) |
