# Bill of materials (per toolhead)

The build is decided (DD-01): **one stock Creality 4020 blower (the one already fitted) + the S7
duct + a new cooling-module frame and cover** on the PCB's three-hole pattern. The carriage, hotend,
extruder, nozzle PCB, 3010, LiDAR and MicroProbe positions are stock and unchanged. The electrics are
unchanged too (stock PB8 / PB6 / PB3, `electrical.md` §1). This page is the BOM for that build.
The Same Sky 5015 option is a conditional upgrade and has its own section (§3). Two fans and the
Delta are rejected (DD-01, `cfd-report.md` §10) and are not listed.

Release status per line (from `cad/exports/validation_report.md`):
- **PRINT FIRST**: the fit-check coupon. It exists to confirm the ESTIMATED values.
- **FIT-CHECK FIRST**: print it after the coupon passes and the listed M# are answered, then check
  it on the printer before trusting it (`assembly.md`).
- **NOT RELEASED**: depends on MISSING data. Do not print it for use.
- **RELEASED**: buy or use now.

Screw sizes come from the CAD sources named in each row (`cad/README.md` "BOM"). M# items are in
`missing-information.md`.

## 1. Printed parts

Masses are solid-volume upper bounds (100 % infill) from the validation report, with ESTIMATED
densities ASA 1.07, PC 1.20, PA-CF 1.15 g/cm³ (typical TDS values; use your spool's datasheet).
Files: `cad/exports/3mf/<name>.3mf`, `cad/exports/stl/<name>.stl`, `cad/exports/step/<name>.step`.
Print settings: `print-settings.md`.

| Part | File name | Material | Mass, g | Qty | Status | Waiting for |
|---|---|---|---|---|---|---|
| Fit-check coupon | `fitcheck_coupon` | ASA (same spool as the frame) | 2.89 | 1 | **PRINT FIRST** | — |
| Cooling-module frame | `cooling_module_frame` | ASA | 5.84 | 1 | **FIT-CHECK FIRST** (8 of 37 dependencies unconfirmed) | coupon result; M10 (PCB pads, component zone, 4th pad); M7 (4020 hole positions and through-length); M6 (LiDAR boxes); insert hole size |
| Cover | `cover` | ASA | 6.42 | 1 | **FIT-CHECK FIRST** (4 of 18) | M7 (4020 intake face and inlet Ø28); M6 (LiDAR boxes); M9 (front clearance: front −58.2 vs −55.0) |
| Duct body (S7) | `duct_body` | **PC** (or PA-CF, 8.9 g) | 9.24 | 1 | **FIT-CHECK FIRST** (12 of 24) | M7 (4020 outlet 17 × 13, hole positions, socket fit); M1 (hotend version); M8 (probe keep-out); M10; M6 |
| MicroProbe mount | `probe_mount` | **PA-CF** (PC acceptable) | 11.45 | 1 | **NOT RELEASED** (12 of 39; `PM_ANCHOR_CONFIRMED_M8` MISSING) | M8 (785004 anchor, photo + calipers). Until then keep the 785004 |

No PLA or PETG for any of these parts (DD-07).

Moving-mass change vs stock: **−0.6 … +8.4 g** (validation report). That is the printed parts at
100 % infill (46.7 g added, including 13.73 g of screws and inserts) minus the stock cover + duct
(23.8–32.5 g), the 785004 adapter (10.6–10.9 g) and the stock PCB screws (3.9 g). The range assumes
the new probe mount replaces the 785004. While the 785004 stays (probe mount not released), the
change is about 0.6–0.9 g lower (11.45 g not added, 10.6–10.9 g not removed). Predicted X shaper
76.9 … 77.7 Hz (77.6 Hz today), Y 51.8 … 52.0 Hz (52.0 Hz today), ESTIMATED.

## 2. Fasteners and inserts

| # | Item | Exact spec | Qty | Derived from | Status |
|---|---|---|---|---|---|
| F1 | PCB / module screws | **M3×30, ISO 7380 button head**, steel (8.8/10.9 or A2) | 3 | `frame.py` `FRAME_PCB_SCREW_LEN` 30: the frame adds 11.2 mm (9.2 boss + 2.0 plate) to the stock M3×18 / M3×18 / M3×20. The upper tips go 0.8 mm deeper than stock into the carriage inserts; the lower one has 7.3 mm engagement in the heatsink (stock 8.5). Tips checked at Y −3.5 against the Henlor carriage (validation PASS) | FIT-CHECK FIRST |
| F2 | Washer, coupon only | M3, ISO 7089 (3.2 × 7 × 0.5) | 3 | the coupon plate is 1.6 mm against the frame's 2.0 mm; the washer restores the frame's screw depth (`print-settings.md` §5) | RELEASED |
| F3 | M3 heat-set insert, brass, short | for a **Ø4.0** hole, length **≤ 4.5** (CAD 4.0). The hole is 5.0 deep (4.0 + 1.0 relief), so a standard 5.7 mm insert does **not** fit | frame: **6** (2 fan, 2 duct T_left / T_right, 2 cover); coupon: 1; spares: 5 | `common.py` `INSERTS["M3"]` (hole 4.0 ESTIMATED); `cad/README.md` BOM | FIT-CHECK FIRST (hole size, confirmed by the coupon) |
| F4 | Cover screws | **M3×6, ISO 7380** | 2 | `frame.py` hardware list: through the 1.2 mm cover top wall, then 4.8 mm into the 5.0 mm insert hole. **Do not use M3×8**: it bottoms out | FIT-CHECK FIRST (follows the cover) |
| F5 | Duct-to-frame screws | **M3×6, ISO 7380** | 2 | `cooling.py` `DUCT_TAB_SCREW_LEN` 6: duct tab 2.5 mm (`duct_interface.json` `tab_size_mm`) + 3.5 mm in the insert. Maximum usable length 2.5 + 5.0 = 7.5 | FIT-CHECK FIRST (follows the duct) |
| F6 | Fan-to-frame screws | **M3×24** (ISO 4762 / DIN 912 or ISO 7380; check availability). Rule: L = fan hole through-length + 3.5 … 4.5, and **≤ through-length + 5.0**. M3×25 would bottom out exactly at 5.0 | 2 (the 4020's diagonal pair (−18.65, 60.3) and (16.05, 25.6)) | `frame.py` `FRAME_FAN_SCREW_LEN` 24 = through-length 20 + 4. **The 20 mm through-length is ESTIMATED (M7).** The stock fan is held by M3×18 through the same holes (research/02 C7), so the real length may be under 20: then M3×24 would bottom out. Measure the hole through-length first and buy L by the rule | FIT-CHECK FIRST; **length depends on M7** |
| F7 | M2.5 heat-set insert, brass, short | for a **Ø3.6** hole, length ≤ 4.5 (CAD 4.0); hole depth 5.0 | coupon: 2; probe mount: 2 (later); spares: 4 | `common.py` `INSERTS["M2.5"]` (ESTIMATED) | coupon: RELEASED; probe mount: NOT RELEASED |
| F8 | Probe screws | **M2.5×5** (BIQU kit), through the 2.1 mm flange, then 2.9 mm into the insert | 2 | `probe_mount.py` hardware; BIQU manual | RELEASED (reuse the kit's; also used on the coupon) |
| F9 | Probe-mount anchor screws | **~M2, length unknown**: reuse 785004's. The holes are Ø2.4 clearance with a Ø4.2 × 2.95 counterbore | 2 | `probe_mount.py` `PM_ANCHOR_*` (DERIVED from 785004); size and length **MISSING (M8)** | NOT RELEASED |
| F10 | Cable ties | 2.5 mm wide (slots 1.6 × 3.0 in the frame, 1.6 × 3.2 in the probe mount) | 3 (2 frame top corners, 1 probe-mount roof; the probe-mount one only once that part is released) | `frame.py` `TIE_SLOT`, `probe_mount.py` | RELEASED |

**Insert length rule (all M3 and M2.5 inserts):** the CAD holes are 5.0 mm deep, sized for a 4.0 mm
insert plus 1.0 mm of melt and screw-tip relief. Any insert up to 4.5 mm long fits. A longer one
(the common 5.7 mm M3 type) leaves no relief, and the screws above (F4, F5, F6) were sized for
**≤ 5.0 mm** of thread below the mating face. Changing insert length means changing screw lengths.

**Known fit issue to check (fan screw heads vs. cover):** the cover's front wall sits 0.5 mm in front
of the 4020's front face (`COVER_GAP`), and the F6 screw heads sit on that face. An ISO 7380 M3 head
is 1.65 mm tall (`common.py` `BUTTON_HEAD`), so the heads occupy the cover wall unless the 4020's holes
are recessed (M7). `validate.py` does not model screw heads, so this is not in its report. Check it at
the cover fit-check (`assembly.md` step 7).

**Stock parts removed and kept for rollback** (`assembly.md` §3):
- front cover + duct;
- 2 × M3×4 ultra-low SHCS (cover to carriage, research/02 C5);
- 3 × M3×18 BHCS (4020 to the stock cover, C7);
- PCB screws: 2 × M3×18 BHCS + 1 × M3×20 BHCS (N6/N7).

**Stock parts reused unchanged:** carriage, hotend, heatsink, extruder, nozzle PCB, 3010 hotend
fan, **the fitted 4020 blower**, LiDAR + bracket, MicroProbe + 785004 (until F9 and the probe mount
are released).

**Electrical:** nothing to buy. The 4020 stays on the board's "Model Fan" socket. Only if its lead
does not reach after the move (the fan sits 6–7 mm further forward than stock: Y −56.5…−36.5
against the stock −49.4…−30.2, `interfaces.py` `STOCK_4020_POS`; lead length 60 mm, research/02 F3):
one 4-pin extension. The pitch is unconfirmed (1.25 mm vs XH2.54, **MEASURE** first,
`electrical.md` §1.1). Do not cut the stock fan lead.

### Optional

| Item | Qty | Why | Price (snapshot) |
|---|---|---|---|
| Creality K1 / K1 Max 4020 blower, 24 V 0.3 A, 4-pin, **Creality 4004110132** | 1 spare | bench test V1 (P–Q curve, `cfd-report.md` §15 / `validation.md`) without taking the fitted fan off, and a spare | about $10–14 (`cfd-report.md` §12.1, research/03 §11–12 snapshot 2026-11-01; re-check at checkout) |

## 3. Conditional upgrade: Same Sky CBM-5015BF (not part of the baseline; do not order now)

Order this only if **both**: bench test V1 measures the stock 4020 at its lower bound (191 Pa
shut-off), **and** the V5/V6 overhang and bridge prints show insufficient cooling (DD-01 "Would
reverse it", `cfd-report.md` §12.1). The CFD gain is +13 % layer speed and +21 % part-top h over
the 4020's lower bound, at +7.4 g plus a 3–6 g buck, a weaker minimum sector (−11 %) and +13 %
nozzle loss (`cfd-report.md` §10–§11).

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
- **CAD:** a different duct variant (`with_fan(PARAMS_FINAL, "samesky")`: the plenum enters from the
  left, tabs at X 8 / 20) and therefore a frame regenerated from that interface (the Same Sky's holes
  are Ø4.5, `interfaces.py`). **No buck mount is modelled** (`cad/README.md`). Re-run `validate.py`
  before printing.
- **Calibration:** MPC, shaper and fan checks again (`calibration.md`).

## 4. Tools

| Tool | Used for |
|---|---|
| Soldering iron with temperature control, M2.5 and M3 heat-set insert tips | inserts (`print-settings.md` §3) |
| Flat cold metal block (≈ 20 × 20 mm) | squaring inserts |
| Hex keys 1.5 / 2.0 / 2.5 mm (ball-end 2.0 helps on ISO 7380 M3) | ISO 7380 M3 = 2.0; M3×24 ISO 4762 = 2.5; M2.5×5 BIQU = 2.0 (DIN 912 M2.5); ~M2 anchors = 1.5 (if SHCS); stock M3×4 ultra-low = 2.0 (ESTIMATED) |
| Calipers ±0.05, feeler gauges 0.05–0.5 | coupon, part checks, hole through-length (M7) |
| Gauges: a 2.0 mm and a 3.0 mm drill shank (or feeler stack) | duct lowest point ≥ 2.0 mm above the tip; ≥ 3 mm duct-to-sock clearance (`assembly.md`) |
| Kitchen scale ±1 g | masses (M12) |
| Flush cutters, deburring tool, Ø3.4 and Ø4.0 drills (hand clean-up only) | print clean-up; support removal under the duct |
| Filament dryer, dry box | PC / PA-CF (`print-settings.md` §4) |
| Glue stick | PC / PA-CF bed release |
| Hardened 0.4 nozzle | PA-CF (`print-settings.md` §2.2) |
| Multimeter (DC V with 0.1 mV resolution, mA range), alligator leads, 2 back-probe pins | only for the conditional upgrade (PB6 probe, buck check, `electrical.md` §4) |
| Fine soldering tip, solder, heat gun, IR thermometer (optional) | only for the conditional upgrade (buck wiring and temperature) |
