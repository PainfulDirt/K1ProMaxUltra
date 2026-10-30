# 02 — Mechanical interfaces & toolhead architecture (K1 Max)

Agent 2 (Mechanical Engineering & Toolhead Architecture), 2026-10-30.

**Conventions.** Origin = nozzle tip; +X = printer right, +Y = toward the printer rear, +Z = up; mm.

**Status tags.**
- **VERIFIED**: a published or primary source (URL or repo file) states it.
- **DERIVED**: I measured it in a CAD file, and the file is named.
- **ESTIMATED**: an engineering estimate. The reasoning is given.
- **MISSING**: not found. Section 7 says how to get it.

Every number from community CAD carries the accuracy of a **reverse-engineered** model, not Creality's.

---

## 0. Summary

- **No official Creality CAD exists for the K1 / K1 Max toolhead.** Creality's GitHub org has only two K1 repos, `K1_Series_Klipper` (firmware) and `K1_Series_Annex` (Fluidd/Mainsail/root guides/pin-outs). No STEP files. I found no 3D download on Creality's pages either (search results only, see §1.3).
- The best CAD available is kemsky's **community, reverse-engineered** models of the stock **hotend, ceramic heater, extruder (+ MOONS round motor), nozzle PCB, 3010 and 4020 fans**. They come from his two GitHub rail-mod repos and are placed in his own (non-stock) carriage. From them I measured the hotend, extruder, PCB and fan-pattern geometry in the nozzle frame (§2). An independent K1C PCB gerber confirms the PCB outline and its screw pattern exactly.
- **What no reachable CAD covers:** the stock **X-carriage** (rod bearing positions, belt clamps, cover screws), the **LiDAR module and bracket**, and the **stock front cover/duct**. These have to come from the user (§7).
- **Stock X axis = 2 rods** (not a rail): about 297 g for both. That is consistent with Ø8 mm × 382 mm steel rods (DERIVED, arithmetic in §3.1).
- **Moving mass (ESTIMATED):** about 450 g on X (range 400–500), about 880 g on Y (range 820–960). +50 g on the toolhead moves the X shaper about −5 % (77.6 → about 73.6 Hz) and Y about −2.7 % (52 → about 50.6 Hz).
- **Ranking:** **A (stock-inspired shroud + ducts, integrated sensor mounts) > B (dual fans, only in an asymmetric, LiDAR-aware form) > C (full custom / remote blower + ring duct).** The reasons are in §6.

---

## 1. Sources and CAD inventory

### 1.1 Network limits of this session

Only `github.com` / `raw.githubusercontent.com` resolve. `printables.com`, `thingiverse.com`, `makerworld.com`, `crealitycloud.com`, `creality.com`, `wiki.creality.com` and `reddit.com` do **not** resolve (DNS failure). For community items on those sites I had only search-result snippets. The page contents and files there are **not inspected**. If the user wants the Printables/Creality Cloud CAD, these hosts must be allowed in the session's network settings, or the user downloads the files manually.

### 1.2 CAD downloaded (scratchpad only; nothing third-party is copied into the repo)

Root: `/tmp/claude-0/-home-user-K1ProMaxUltra/1fc00b30-b973-54a8-8106-390cde6c1256/scratchpad/ref/stock/`

| Path (under root) | What | Licence | Commit |
|---|---|---|---|
| `kemsky_creality-k1-xy-rails-mod/` | K1 rail mod. `src/*.FCStd` + `step/cad_assembly.stpZ` include reverse-engineered **stock hotend (`cad_hotend`), extruder (`cad_extruder`, "K1_Extruder_Assembly_v25" + "MOONS CSE14HRA2L410A-01"), nozzle PCB (`cad_pcb`), 3010, 4020**, plus his own toolhead, cover and spacers (incl. `k1_toolhead_spacer_unicorn`, `k1_toolhead_microprobe_spacer`) | CC BY-NC-SA 4.0 (README) | 1fe4df8, 2026-02-16 |
| `kemsky_creality-k1-max-xy-rails-mod/` | K1 **Max** rail mod. Same stock-part models, K1 Max top frame (`cad_frame_top`), MGN12 rails | CC BY-NC-SA 4.0 | f0a720f, 2026-02-26 |
| `axiomless-cyber_Creality_K1C_toolhead_board/` | Passive replacement **K1C** toolhead PCB, EasyEDA + gerbers | GPL-3.0 | 677f6f3, 2026-01-29 |
| `D3vil-Design_K1-Hardware-Mods/` | D3vil Burner drop-in cover STL (stock-cover replacement), XY-joint STEP | CC BY-NC-SA 4.0 | ab2cd69, 2025-05-26 |
| `Tombraider2006_K1/` | Stock **K1 Max factory config** (`version_config/k1max_1_3_3_5.zip`, unzipped to `../stock/k1max_cfg/`) | MIT | b8c6001, 2026-09-15 |
| `atrushing_Mini_Stealth/` | Mini Stealthburner with Creality K1 extruder adapters (STL) | GPL-3.0 | 44da8c0, 2026-09-29 |

Working files: decompressed assemblies in `.../scratchpad/work/asm_k1/`, `.../work/asm_k1max/`; component dumps in `.../work/asm_k1.json`, `.../work/asm_k1max.json` and `.../work/holes_k1.txt`. Measuring scripts are in `.../scratchpad/scripts/` (`dump_asm.py`, `holes.py`; OCP 8.0.1 + trimesh in `.../scratchpad/mech-venv`, run with `python -I`).

**Licence consequence.** The kemsky and D3vil files are CC BY-NC-SA. We may *reference* their dimensions. If we copy or derive geometry from their files, our part inherits BY-NC-SA. Our own parts should be modelled from measured interface numbers, not by editing their solids. The GPL K1C PCB gerber may be referenced and redistributed under GPL-3.0.

### 1.3 CAD that exists but could not be fetched (candidates for the user to download)

| Item | URL | Licence (per snippet) | Note |
|---|---|---|---|
| "Creality K1 Assembly CAD Model" by Henlor | https://www.printables.com/model/742370-creality-k1-assembly-cad-model | "Creative Commons 4.0" | Labelled reverse-engineered, "some inaccuracies, missing some features". **Most likely place for the stock carriage geometry.** |
| "CREALITY K1max – 3D model (STEP)" by LEOTE | https://www.printables.com/model/1167879-creality-k1max-3d-model, https://www.crealitycloud.com/model-detail/creality-k1max-3d-model-step-format | Non-commercial, attribution | Body/panels. Probably no toolhead detail. |
| K1 toolhead stepper cover, STEP | https://www.printables.com/model/729908-creality-k1-toolhead-stepper-cover | — | "WIP, may contain dimensional inaccuracies" |
| High-performance cover, STEP included | https://makerworld.com/en/models/227416 | "don't sell derivatives" | Has a LiDAR-port-access version |

---

## 2. Interface dimension table (nozzle-tip frame)

**How the DERIVED values were obtained.** I loaded kemsky's K1 assembly (`kemsky_creality-k1-xy-rails-mod/step/cad_assembly.stpZ`) with OpenCascade. I read every component's global bounding box and every cylindrical face (axis, diameter), then moved everything to the nozzle frame. Nozzle axis: X 20.20, Y −24.76; nozzle tip Z 339.8 in that file.

The axes of kemsky's file match ours. Front cover/4020 are at −Y and the extruder motor at +Y, so +Y = rear. The parts named "left" are at −X. No mirroring was needed. Positions of stock parts *relative to each other* are only stock-like where kemsky had to keep them (filament path, shared screws). His carriage, cover and 4020 placement are **his design, not stock**.

### 2.1 Hotend (stock "K1 hotend" model; 2023-style ceramic heater)

| # | Interface | Value | Status / source |
|---|---|---|---|
| H1 | Heater power / voltage | 60 W / 24 V ceramic | VERIFIED: repo `tuning.cfg` `[extruder] heater_power: 60` ("K1 series 60W ceramic heater"); listing https://store.dremc.com.au/products/upgraded-creality-k1-ceramic-heating-block-kit-for-creality-k1-k1-max |
| H2 | Max temp | 300 °C (Creality), firmware `max_temp: 320` | VERIFIED: https://www.creality.com/products/creality-k1-3d-printer (via search snippet); stock `printer.cfg` in `k1max_cfg` |
| H3 | Nozzle: length / max Ø / bore | 23.3 / 6.9 / Ø2.0 | DERIVED: `K1-nozzle` in kemsky asm |
| H4 | Nozzle ↔ heat-break joint (inside heater) | Z ≈ +23.0 | DERIVED: mating faces Ø4.74 at Z 22.8–23.2 |
| H5 | Heat-break: Z span / thread-Ø / bore | Z +22.7 … +42.2; Ø5.95 in heatsink at Z 31.9–42.1; bore Ø2.0 | DERIVED: `Heat-brake` |
| H6 | Heater body (ceramic + ring) envelope | X ±6.1, Y −6.5…+6.5, Z +8.5…+29.1 (body Ø13 at Z 9–12.6; ring Ø10 at Z 12.8–23.8) | DERIVED: `ceramic-heater-*` |
| H7 | Heater mounting plate | 20.4 × 16.2 × 5.3, Z +23.7…+29.0 | DERIVED: `ceramic-heater-mount` |
| H8 | Heater → heatsink fixing | 2 × M2 × 22 SBHC at X ±7.0, Y 0, from Z +24.9 up to +48.4. PTFE insulating sleeves Ø4.0/Ø2.6 × 13 at Z +32.7…+45.7 | DERIVED: `M2 x 22 mm SBHC*`, `PTFE tubes*` |
| H9 | Air gap heater plate → heatsink | 2.9 (Z +29.0 → +31.9) | DERIVED |
| H10 | Silicone sock envelope | X −11.7…+11.8, Y −8.6…+8.3, Z +4.9…+30.3. Bottom hole Ø7 at Z 4.9–7.6 | DERIVED: `Silicone Socks` |
| H11 | **Lowest hot-part clearance above nozzle tip** | heater body bottom +8.5; sock bottom +4.9 | DERIVED |
| H12 | Heatsink envelope | X −13.9…+13.9 (27.8), Y −10.8…+10.2 (21.0), Z +31.9…+56.0 (24.1) | DERIVED: hotend `SOLID` |
| H13 | Heatsink front fixing holes (3010 fan + PCB lower screws) | 2 × Ø3.0 blind along Y, at X ±12.0, Z +34.3, from the front face Y −10.8 to Y +2.0 | DERIVED |
| H14 | Heatsink cross-hole | Ø4.0 along X, through, at Y +2.0, Z +40.5. Also Ø3.0 side hole at Y −2.2, Z +42.8 (X +9.9…+13.7) | DERIVED. Function unknown (clamp/pin?) |
| H15 | Heat-break set screw | M4 grub along Y from the rear (Y +3.5…+6.5), at X 0, Z +34.9 | DERIVED: `M4 x 4mm grub screw` |
| H16 | Heatsink top → extruder bottom gap | 6.2 (kemsky's spacer: 28.2 × 6.2 × 6.2) | DERIVED: `k1_toolhead_spacer.stl`. It is kemsky's spacer, not a stock part. MISSING for stock |
| H17 | Unicorn-hotend variant | kemsky's Unicorn spacer is 4.6 instead of 6.2, so the stack is **1.6 mm different**. The effect on nozzle-tip Z is not derivable | DERIVED: `k1_toolhead_spacer_unicorn.stl` |
| H18 | How the heatsink fixes to the stock carriage | — | MISSING |
| H19 | Nozzle tip → underside of carriage / X rods | — | MISSING |
| H20 | MPC block heat capacity (indicates a small block) | 16.36 J/K | VERIFIED: repo `printer.cfg.save_config` |

### 2.2 Extruder (stock K1 extruder model + MOONS round motor)

| # | Interface | Value | Status / source |
|---|---|---|---|
| E1 | Stock `rotation_distance` / microsteps | 6.9 / 16. No `gear_ratio` line | VERIFIED: stock K1 Max `printer.cfg` (k1max_cfg) |
| E2 | Motor | MOONS **CSE14HRA2L410A-01** (CAD label), round Ø36 body | DERIVED: label in kemsky CAD. Sibling CSE14HRA1L410A-01 = 36 mm, about 85 g (https://biqu.equipment/products/moons-cse14hra1l410a-01-36-stepper-motor). Motor identity on the user's unit: MISSING |
| E3 | Motor axis | along Y, at X +0.3, Z +81.3 | DERIVED |
| E4 | Motor body depth | Y +15.7 … +35.9 (rear face +35.9) | DERIVED |
| E5 | Motor flange holes | 2 holes on a 43.7 mm PCD, at 45° (X −15.4/Z −15.5 and X +15.5/Z +15.5 from the motor axis), Ø2.46 | DERIVED |
| E6 | Dual drive gears | centres X ≈ −7.45 / +7.55, Z ≈ +76.2 (filament on X ≈ 0, Y ≈ −0.4) | DERIVED |
| E7 | Main plate | bottom Z +62.2, top Z +100.4; 38.2 × 7.8 × 38.2 | DERIVED: `main-plate/SOLID002` |
| E8 | Extruder fixing holes, bottom | 2 × vertical (Ø4.2–5.0 counterbore) at X −9.7 / +10.3 (20.0 apart), Y +10.1, Z +63.5…+65.6 | DERIVED. Screw size: MISSING |
| E9 | Extruder fixing holes, sides | horizontal (axis X) at Y +10.1, Z +72.2 (left face) and Z +92.2 (right face) | DERIVED |
| E10 | Extruder outline (cover + motor) | X −20.4…+21.0, Y −5.4…+35.9, Z +60.6…+102.0. Lever to Z +108.1 | DERIVED |
| E11 | Bowden/PTFE inlet (collet) | Z ≈ +87…+95.5, centred X 0 | DERIVED: `Bowden Tube_Collet v4` |
| E12 | Gear reduction ratio | not published | MISSING (gear tooth counts are visible in CAD but unverified) |

### 2.3 Toolhead PCB, fans, cover

| # | Interface | Value | Status / source |
|---|---|---|---|
| P1 | Nozzle MCU | GD32F303CBT6. Drives extruder TMC2209, heater, thermistor, part fan (PB8), hotend fan, ADXL345, filament sensor 2 | VERIFIED: stock `printer.cfg` (k1max_cfg) |
| P2 | **PCB outline** | **44.1 × 46.9 × 1.2** (in kemsky: 44.1 along X, 46.9 along Z) | DERIVED, two independent sources agree: `cad_pcb` (kemsky) and K1C gerber `Gerber_BoardOutlineLayer.GKO` (46.90 × 44.10). K1 Max board itself: not measured |
| P3 | PCB mounting holes | 3 × Ø3.4 on 3 corners of a **24 × 24 mm square** (= 3010 fan pattern). The square is centred on the 44.1 side and **offset 1.65 mm** from centre along the 46.9 side | DERIVED (both sources identical) |
| P4 | PCB position (kemsky, stock-like because it shares the heatsink screws) | plane Y −25.4…−24.2. Holes at X −12/+12 at Z +34.3 & +58.3 (X −12/Z +34.3, X −12/Z +58.3, X +12/Z +58.3). Board Z +24.5…+71.4 | DERIVED. Lower holes coaxial with heatsink holes H13 |
| P5 | PCB connector positions | K1C pin-map: 1–3 heatbreak fan, 4/9 thermistor, 5/7/21 filament, 6/10/12/13 model fan, 8/11/14/20 stepper, 15–19 LiDAR, 22/23 heater. Connectors JST-HY2.0-2P, JST-XHB2.54-2P, 1.25 mm 3/4/5-pin | VERIFIED for **K1C**: https://github.com/axiomless-cyber/Creality_K1C_toolhead_board. Physical XY positions on the K1 Max board: MISSING |
| F1 | Hotend fan | **3010 axial**, 24 V 0.1 A, 12 000 rpm, lead 40 mm, 1.25-3P | VERIFIED: Creality kit listings https://www.amazon.com/Creality-Official-Fans/dp/B0CSKBMYDQ (spec text via search snippet) |
| F2 | Hotend fan position (kemsky) | in front of heatsink, Y −22.1…−11.7. 24 mm holes at X ±12, Z +34.4/+58.4 (centre Z +46.4) | DERIVED |
| F3 | Part-cooling fan | **4020 blower**, 24 V 0.3 A, 12k rpm, lead 60 mm, 1.25-4P | VERIFIED: same listings |
| F4 | Stock 4020 position/duct exit in stock cover | — | MISSING (kemsky's cover is not stock) |
| F5 | 4020 mass | — | MISSING (ESTIMATED 15–20 g, unsourced) |
| C1 | Stock front cover (shroud) mass, without fan | 23.8 g (K1, D3vil measured) / 32–32.5 g (other K1/K1 Max reports) | VERIFIED-ish (community): D3vil README in repo clone; https://makerworld.com/en/models/430181 ("29 g vs 32 g", snippet); https://www.printables.com/model/786832 ("32.5 g → 12.7 g", snippet) |
| C2 | Stock cover fixing | "remove the two screws … slide the cover off" | VERIFIED (community): D3vil README. Screw positions: MISSING |
| C3 | Envelope of a drop-in cover replacement | 52.8 × 86.0 × 64.5 (STL bounding box as printed, front face up, so probably W 52.8 × H 86.0 × D 64.5) | DERIVED: `K1 D3vil Burner Toolhead Cover V3 (D3D).stl` |

### 2.4 Sensors

| # | Interface | Value | Status / source |
|---|---|---|---|
| S1 | MicroProbe V2 position | X 0, **Y +20.3** | VERIFIED: repo `tuning.cfg` `[probe]` |
| S2 | MicroProbe trigger vs nozzle | z_offset 0.831 (probe triggers 0.831 above nozzle contact) | VERIFIED: `printer.cfg.save_config` |
| S3 | MicroProbe mass / length | about 6 g / 25.3 mm | VERIFIED (retailer): https://www.3djake.uk/biqu/microprobe, Newegg listing (snippet) |
| S4 | Probe body Ø, pin stroke, mount geometry | — | MISSING |
| L1 | **LiDAR laser-line centre on the bed (nozzle at Z 3, glass + PEI)** | **X −36.01, Y −21.34** (config uses −36 / −21.2) | VERIFIED: repo `variables.cfg` `lidar_x_offset/-y_offset`, `custom/LIDAR-NOTES.md`, `tuning.cfg [lidar]` |
| L2 | Laser line drift with nozzle height | Y −0.99 mm and X +0.035 per mm of Z, so the laser sheet is inclined **about 45° in the YZ plane** | VERIFIED: LIDAR-NOTES |
| L3 | Line length / extent | about 29 mm (profile x −14.4…+14.8, x runs toward −X), so on the bed **X −50.8 … −21.6** | VERIFIED (x range) / DERIVED (X range = −36 − x) |
| L4 | Working distance | about 25.5 mm with the nozzle 3 mm above the surface. Full coverage only at nozzle 3–5 mm, partial at 8, none at ≥ 10 | VERIFIED: LIDAR-NOTES |
| L5 | Profile tilt from the mounting | 0.031 mm/mm along x (≈ 1.8°) | VERIFIED: LIDAR-NOTES |
| L6 | **Allowed change of LiDAR height relative to the nozzle tip** | about ±1–2 mm before the 25–28 mm window is lost at a scan Z of 3–5 | DERIVED from L4 |
| L7 | Stock Creality laser Y offset (stock plate) | −23.2 | VERIFIED: LIDAR-NOTES |
| L8 | Module outline, mass, bracket, window positions, fixings | — | MISSING. Mass "−89 g with bracket" is one second-hand report (https://printer-hub.ru/en/posts/creality-k1-vs-k1c-vs-k1-max, snippet) |
| L9 | Electrical | USB CH343 (1a86:55d3), power by GPIO PA14. PCB pins 15–19 on K1C | VERIFIED: LIDAR-NOTES; K1C repo |

### 2.5 Carriage, axes, frame

| # | Interface | Value | Status / source |
|---|---|---|---|
| X1 | X guide | **2 rods + carriage** (no linear rail). Stock gantry: rods 297 g, 2 blocks 112 g, carriage 110 g (total 519 g) | VERIFIED (community, single source): https://cults3d.com/en/3d-model/various/creality-k1-max-full-linear-mod-lidar-compatibile-no-root-needed (snippet) |
| X2 | X rod length | 382 mm (Bondtech K1 Max kit: "2 × X-rod … 382 mm") | VERIFIED (retailer): https://ultimate3dprintingstore.com/products/bondtech-lgx-lite-pro-upgrade-kit-for-creality-k1-max (snippet; some listings say 302.5, which is the K1) |
| X3 | X rod Ø | **≈ 8 mm**: 148.5 g / (7.85 g/cm³ × 382 mm) → area 49.5 mm² → Ø 7.94 | DERIVED (from X1 + X2, assuming steel). Confirm with calipers |
| X4 | Rod spacing/orientation, bearing type, belt clamp positions and belt planes rel. nozzle | — | MISSING |
| X5 | Carriage hole pattern ↔ nozzle | — | **MISSING** (no reachable CAD) |
| M1 | X / Y kinematics | CoreXY, `rotation_distance 72` (GT2 36T-equivalent), 32 µsteps | VERIFIED: stock printer.cfg |
| M2 | Travel (nozzle) | X −2 … 306.5 (endstop 306.5), Y −2 … 306 (endstop −2), Z −10 … 305 | VERIFIED: stock printer.cfg; repo keep-out uses X 306.5 |
| M3 | Bed / build | 300 × 300, 300 × 300 × 300 | VERIFIED (brief, Creality spec) |
| M4 | Printer outside | 435 × 462 × 526 | VERIFIED (retailer): https://www.solarbotics.com/product/52522/creality-k1-max-3d-printer (snippet) |
| M5 | Stock max accel / velocity | 20 000 mm/s² / 800 mm/s | VERIFIED: stock printer.cfg |
| M6 | Load-cell touch force | trigger 160 g, safety limit 2000 g (approximate grams) | VERIFIED: `tuning.cfg [load_cell_probe]`. The toolhead and hotend must take ≥ 2 kgf axially without shifting |
| M7 | Input shaper (this printer) | X 3hump_ei 77.6 Hz, Y ei 52.0 Hz (factory sample: X zv 50.6, Y zv 45.4) | VERIFIED: `printer.cfg.save_config`; k1max_cfg |

---

## 3. Motion and clearance envelope

### 3.1 X axis

The stock K1 Max carries the toolhead on **two X rods**, not a rail (X1). The aftermarket MGN12/MGN9 rail mods show this is a known stiffness and ringing weak point (kemsky: "MGN12 rail can be used on X without reinforcement, but it is not rigid enough"; he bolts it to 20 × 10 tube or carbon). The rod diameter of about 8 mm (X3) is DERIVED, not measured. **Our toolhead must reuse the stock carriage** (rod bearings + belt clamps), or the X-axis hardware becomes part of the project. The Bondtech kit is a precedent: it replaces the carriage *and* the rods.

### 3.2 X ends (±X)

Nozzle travel is X −2 … 306.5. The stock toolhead fits that with whatever gap is left to the XY joints. That gap is **MISSING**. Anything wider than the stock toolhead/carriage at joint height costs X travel 1:1, unless that width is above or below the joints. The LiDAR sits on the **left** (laser at X −36), so the left side is already the widest. Required: the toolhead's left/right extremes at each Z band, and the gap to the joints at X = −2 and X = 306.5 (§7).

### 3.3 Rear (+Y)

From the repo keep-out measurements (README, `tuning.cfg [keep_out]`, measured "until ~3 mm gap left"). With the probe at Y +20.3 the reach is:

| Region | Nozzle blocked beyond | Lost vs Y 306 |
|---|---|---|
| Left corner, X −10…19 | Y 292 | 14 mm |
| Middle Z-rod housing, X 130…170 | Y 293 | 13 mm |
| Right housing, X 266…286 | Y 302 (305 at X 266) | 1–4 mm |
| Right corner, X 286+ | Y 287 | 19 mm |

DERIVED rule: to get full Y travel back, the rearmost toolhead feature (at the housing's height) must sit **≥ 13 mm further forward than the current probe body's rear surface** in the middle, and ≥ 19 mm in the right corner. Equivalently, it must be no further back than the stock toolhead's rear, which reached Y 306 (that stock rear extent is MISSING). Moving the probe to the side or front costs mesh reach instead (README).

### 3.4 Front (−Y)

Travel to Y −2. The front cover is the front-most part. The gap to the door/front frame at Y −2 is MISSING. The LiDAR line sits at Y −21.3 and the module is somewhere in front-left (MISSING).

### 3.5 Down (Z) and the bed

The nozzle tip is the lowest point. Parts below the heatsink and around the heater are limited by:
- (a) the load-cell touch and Nozzle Deep Clean, which press 0.15 mm into PEI and drag;
- (b) the first layer at about 0.2 mm;
- (c) the raised glass. LIDAR-NOTES: the glass mod puts the surface 4–5 mm above the stock sticker, so bed-edge features (clips, sticker) are now *below* the print surface.

ESTIMATED rule: duct outlets and the probe pin (retracted) at **≥ 2–3 mm above the nozzle tip**. The stock duct exit height is MISSING; copy it once measured.

### 3.6 Up

Extruder lever top Z +108.1, PTFE/Bowden inlet above that (E10/E11). The clearance to the lid/top frame at Z max is MISSING. The kemsky K1 Max frame top in CAD: 438.3 × 438.3 × 56.6 (not the stock frame).

### 3.7 Laser sheet keep-out (new constraint for any shroud)

Nothing may enter the volume swept by the LiDAR laser sheet:
- X −50.8 … −21.6 (at the bed);
- inclined about 45° in YZ, rising toward **+Y** (toward the nozzle) from the spot at Y −21.3 at the bed. *Orchestrator correction: the original text said −Y. The line moves −0.99 mm in Y per +1 mm of nozzle Z, so the emitter is on the +Y side of the line; see `cad/source/interfaces.py::lidar_sheet_y`;*
- up to the module window.

The receiver's line of sight must also stay clear if the module is a triangulation sensor. Which window is emitter and which is receiver is MISSING. Many community covers needed a "LiDAR gap" (TrueBlueRoo) or a LiDAR-port version (XSvFury).

---

## 4. Hotend and extruder research

- **Stock hotend (2023 K1/K1 Max):**
  - 60 W 24 V ceramic heater, 300 °C (firmware 320);
  - Creality describes a titanium-alloy heatbreak with a copper-alloy nozzle; retail V2 kits say "bi-metal" and a hardened-steel-tip copper nozzle;
  - geometry is in §2.1;
  - nozzle length 23.3 is DERIVED from community CAD. No published drawing was found.
- **Generations:** Creality forum users report that the 2023/2024 and 2025 K1-series hotends differ in design and connector. The **Unicorn** quick-swap nozzle (K1C / "K1 Max 2024") needs the Unicorn-style heater; it does not fit the older block without changing the block. Sources: https://forum.creality.com/t/hot-end-replacement/28364, https://forum.creality.com/t/k1-k1-max-hotends/2276, TH3D: https://www.th3dstudio.com/product/creality-unicorn-style-nozzle-for-k1c-k1-se-k1-max-ender-3-v3-and-ender-3-v3-plus/ (snippets).
  - Creality's Unicorn: titanium-alloy heatbreak with copper/hardened-steel nozzle, "up to 30 mm³/s" (vendor claim).
  - E3D "Obxidian" Unicorn: "up to 45 mm³/s" (https://e3d-online.com/products/e3d-creality-high-flow-obxidian-unicorn-nozzles).
  - Kemsky's 1.6 mm thinner Unicorn spacer (H17) shows the stack height changes.
- **Third-party drop-ins:** Micro-Swiss FlowTech for K1/K1 Max/K1C/K1 SE (https://store.micro-swiss.com/products/micro-swiss-flowtech-hotend-for-creality-k1-k1-max). One forum report says it did not fit a K1 Max. I found **no K1-specific Revo, Rapido, Dragon or Bambu-clone mount**. The full-custom toolheads (Hellfire) use Dragon Ace / Chube Air, which is a different nozzle-tip-to-mount geometry.
- **Effect on our design.** Any hotend change moves the nozzle tip relative to the carriage. That means:
  - the probe z-offset and twist compensation must be re-measured;
  - **the LiDAR's height relative to the nozzle must be held within about ±1–2 mm (L6)**, otherwise the scan Z has to change;
  - LIDAR_OFFSET_CALIBRATION must be re-run (Y shifts 0.99 per mm).

  **Design A and B should not change the hotend.** If a Unicorn upgrade is planned, it should be decided *before* the sensor mounts are frozen. Ask the user which hotend is fitted.
- **Extruder:** stock K1 direct drive, dual-gear, round MOONS 36 mm motor (CAD label), `rotation_distance 6.9`. The reduction ratio is not published (E12). Upgrades exist: Bondtech LGX Lite Pro kit (new carriage + rods + extruder; 695 g net kit), Sherpa Micro on the Hellfire toolhead.

---

## 5. Community and aftermarket survey (search snippets unless noted)

| Project | Architecture | Claims / issues reported | URL |
|---|---|---|---|
| kemsky K1 / K1 Max XY rails mod | MGN9/MGN12 X rail, own toolhead holding the stock hotend/extruder/PCB/3010/4020, Microprobe spacer, Unicorn spacer | MGN12 X needs reinforcement (20 × 10 tube or carbon). Camera mount must be lowered 8 mm. PA-CF/PA-GF recommended ("screw joints loosen in ABS") | https://github.com/kemsky/creality-k1-xy-rails-mod, https://github.com/kemsky/creality-k1-max-xy-rails-mod (**inspected**) |
| Cults "Full Linear Mod (LiDAR & CFS compatible)" | rail X gantry | stock gantry 519 g → 449 g (−70 g) | cults3d link in X1 |
| Bondtech LGX Lite Pro kit for K1 Max | new X-carriage + 2 × 382 mm rods + LGX Lite Pro | 811 g gross / 695 g net kit; "stock K1 Max only" | https://www.bondtech.se/product/lgx-lite-pro-upgrade-kit-for-creality-k1-max/ |
| Hellfire toolhead (MackinsVII) | full custom on a BCJ rail gantry: EVA3/E341M-derived, Sherpa Micro, Dragon Ace/Chube Air, 5015, Beacon, H36/Nitehawk board | LiDAR not kept; no mass given | https://makerworld.com/en/models/2064305 |
| 5015 covers (Mecalogic123, A. Turtsevitch, stat1k, magnetic 5015) | single 5015 replacing the 4020 in a new front cover | **duct outlet warping with fan off at high temp (ABS 260 °C)**, so keep ≥ 10 % fan; PETG "will likely warp"; 5015 needs a MOSFET/soldering (stock 4020 is 4-pin) | https://www.printables.com/model/1647145, https://www.printables.com/model/926434, https://www.printables.com/model/1185257, https://makerworld.com/en/models/968140 |
| Silent covers (5015/5020) | larger blower | 5020 recommended because it also cools the **toolhead MCU in a hot chamber** | https://www.printables.com/model/797223 |
| High-Performance cover (XSvFury / Rick Tucker) | 4020, improved duct; LiDAR-port version | — | https://makerworld.com/en/models/227416, https://www.printables.com/model/696328 |
| Magnetic quick-removal cover v6 | 4020; v6 **reuses the stock duct** | v5 warped at the duct outlet with ASA, fans off; "ASA/ABS or better" | https://makerworld.com/en/models/433126 |
| LiDAR-gap shroud (TrueBlueRoo) | slot in the cover | **stock cover forces LiDAR unplugging at every nozzle change** | https://www.printables.com/model/689557 |
| Skeletonized cover (Alan's Designs) | lightweight shroud | 32.5 g → 12.7 g | https://www.printables.com/model/786832 |
| D3vil Burner | drop-in cover + Knomi | 20.3 g ASA vs stock 23.8 g | repo clone (**inspected**) |
| Extended auxiliary duct (Cults) | second fan on the left | **LiDAR and its metal piece had to be removed to fit the second fan** | https://cults3d.com/en/3d-model/tool/creality-k1-k1-max-extended-axillary-fan-duct-for-dual-fans-and-extra-coverage |
| CPAP duct (Creality Cloud, WS7040) | remote blower + hose | no data inspected | https://www.crealitycloud.com/model-detail/v2-cpap-duct-creality-k1-ws7040 |
| Mini Stealth | Stealthburner-style with K1-extruder adapters | — | https://github.com/atrushing/Mini_Stealth (**inspected**, STL only) |

I found no dual-5015 K1 Max toolhead that keeps the LiDAR. No published cooling measurements (only qualitative claims).

---

## 6. Architecture evaluation

### 6.1 Moving-mass baseline (ESTIMATED)

| Item | Mass (g) | Basis |
|---|---|---|
| Carriage (with rod bearings) | 110 | Cults listing (X1) |
| "Printhead" (extruder, hotend, fans, PCB, cover) | 190 (Creality claim) … 246 (bottom-up) | 190: Creality K1/K1 Max marketing (https://all3dp.com/1/creality-k1-max-3d-printer-review-specs/). 246 bottom-up = motor 85 (sibling spec) + extruder body about 63 (CAD volumes × assumed Al/steel/plastic densities) + hotend about 32 (heatsink 4741 mm³ Al = 12.8; nozzle 421 mm³ Cu = 3.7; heater about 9; sock 2.6; heat-break about 2.5; screws about 1) + 4020 about 17 + 3010 about 7 + PCB about 10 + cover 32 |
| LiDAR + bracket | 89 | single second-hand report (L8) |
| Microprobe + mount | about 11 | 6 g probe (S3) + about 5 g mount (ESTIMATED) |
| Cable/umbilical share | about 20 | ESTIMATED |
| **m_X** | **≈ 420–476 → use 450 (range 400–500)** | sum |
| X rods + 2 XY blocks | 297 + 112 | Cults listing |
| **m_Y** | **≈ 830–885 → use 880 (range 820–960, belts/drag chain)** | m_X + 409 |

**Shaper sensitivity.** f ∝ 1/√m for the belt/rigid-body mode, assuming stiffness is unchanged. Rows are the change in toolhead mass (Δm); columns give f for m = low / mid / high:

| Δm on toolhead | X (77.6 Hz) for m_X 400/450/500 | Y (52.0 Hz) for m_Y 820/880/960 |
|---|---|---|
| −50 g | 83.0 / 82.3 / 81.8 (+6.1 %) | 53.7 / 53.5 / 53.4 (+3.0 %) |
| −25 g | 80.1 / 79.8 / 79.6 | 52.8 / 52.8 / 52.7 |
| +15 g | 76.2 / 76.3 / 76.5 | 51.5 / 51.6 / 51.6 |
| +25 g | 75.3 / 75.5 / 75.7 (−2.7 %) | 51.2 / 51.3 / 51.3 (−1.4 %) |
| +50 g | 73.2 / 73.6 / 74.0 (−5.1 %) | 50.5 / 50.6 / 50.7 (−2.7 %) |
| +65 g | 72.0 / 72.5 / 73.0 | 50.1 / 50.2 / 50.3 |
| +100 g | 69.4 / 70.2 / 70.8 (−9.5 %) | 49.1 / 49.3 / 49.5 (−5.2 %) |

Rule of thumb: Δf/f ≈ −½ Δm/m, so X loses about 1 % per 9 g and Y about 1 % per 18 g. The input shaper's max accel scales with f², so X loses about 2 % of usable accel per 9 g.

The relation only holds for the translational belt mode. Cantilevered masses (fans out at ±40 mm, LiDAR at −36) also lower the **yaw/roll modes** of the carriage on its rods, and those appear as extra peaks. The user can measure the real m_X without taking anything apart (§7, item 14).

### 6.2 Architecture A: stock-inspired (keep carriage, hotend, extruder, PCB, LiDAR; new shroud, ducts, sensor mounts)

- **Reused:** carriage, rods, belts, hotend + heatsink + 3010, extruder + motor, nozzle PCB (MCU, ADXL345, driver), stock LiDAR + bracket (unchanged), Microprobe.
- **Replaced:** front cover/duct (23.8–32.5 g). New shroud with an improved duct for the 4020 (or one 5015). The probe mount is moved from the printed shroud onto the metal heatsink/carriage.
- **Mass change:** shroud −5 … +5 g (24–32 → 25–35 g PA-CF/ASA). Fan: 4020 kept 0, or 5015 in place of 4020 = 25–28 − (15–20 est.) = **+5 … +13 g**. **Total −5 … +18 g** → X ≥ 76 Hz (−2 % worst), Y about 51.5 Hz.
- **Envelope:** the same as the stock cover (≈ 53 × 86 × 65 cover class). It can stay inside the stock left/right/front extremes, so no travel loss. The rear probe stays the limit (§3.3).
- **Rigidity:** best of the three, because the LiDAR geometry and bracket are untouched (L5/L6 hold, no recalibration of the module). The duct is a thin-wall cantilever. Its stiffness only matters for flow, not accuracy. Fix the probe to metal (heatsink/carriage), not to the duct shell: the probe's z_offset 0.831 must stay put within µm–tens of µm.
- **Serviceability:** keep a front cover that can come off without unplugging the LiDAR (a known stock annoyance). Nozzle change stays as stock. Fan swap with 2 screws.
- **Printability:** the shroud prints face-up with supports in the duct, or split into shell + duct half for support-free internal channels.
- **Heat and material:** the outlet sits about 5–10 mm from the sock (H10/H11). Use ASA/ABS minimum, PA-CF/PC preferred at the outlet lips. Community covers warped at outlets with the fan off at 260 °C, so keep ≥ 10 % minimum fan or use a PC/PA lip.
- **Risks:** the 4020 limits peak cooling; a 5015 needs a MOSFET/4-pin adapter (wiring belongs to Agent 3). Little else.

### 6.3 Architecture B: dual part-cooling fans left/right + dedicated 3010

- **Reused:** as A.
- **Conflict:** the **LiDAR occupies the left side** (laser X −50.8…−21.6, module front-left). A symmetric left 5015 collides with the module or the laser sheet. The only community dual-fan K1 Max mod removed the LiDAR. B is only viable as **B′: asymmetric**:
  - right 5015 + a small left blower (4010/4020) placed above/behind the LiDAR, ducted under it, clear of the 45° laser sheet; or
  - both blowers on the right/front with a split duct feeding both sides.
- **Mass change:** 2 × 5015 (50–56) − 4020 (15–20 est.) + bigger shroud (+10…+20) + brackets/wiring (+5) = **+40 … +66 g** → X about 72.5–74.5 Hz (−4 … −6.5 %), Y about 50.2–50.8 Hz.
- **Envelope:** +15 … +25 mm per side over the stock width (ESTIMATED from 5015 = 50 × 50 × 15). That costs X travel 1:1 if it sits at XY-joint height. The joint gap is MISSING.
- **Rigidity:** fans at about ±40 mm add yaw/roll inertia on a 2-rod carriage, so expect new torsional peaks. The fan brackets must not share load paths with the LiDAR or probe mounts.
- **Serviceability:** two fans and two ducts, so more screws. The nozzle reaches from the front if the ducts split.
- **Printability:** two mirrored or non-mirrored ducts. Supports inside the ducts unless split.
- **Heat:** two outlets near the block, same material rules as A.
- **Risks:** LiDAR obstruction (scan noise or occlusion), lost X travel, a 5–7 % X shaper drop, MCU fan-channel count (stock board has one part-fan output, so both fans share it).

### 6.4 Architecture C: full custom (remote blower + 360° / ring duct, new hotend mount, sensor carrier)

- **Reused:** possibly the carriage + rods (or a rail swap, as in kemsky/Hellfire), extruder, PCB. Hotend possibly swapped. The LiDAR moves to a new carrier.
- **Mass change:** −4020 (−15…−20) − stock cover (−24…−33) + ring duct (+10…+20) + new structural body/carrier (+20…+40) + carried hose stub (+10…+20) = **−28 … +27 g**. Moving mass is not the issue. **Hose forces** are: a stiff hose along the gantry adds position-dependent force and damping. It can make the shaper fit worse even when the mass drops, and it adds friction/drag to every move.
- **Envelope:** a ring duct needs about 15–20 mm radius around the nozzle (ESTIMATED). The ring bottom must stay ≥ 2–3 mm above the tip (Deep Clean drags the nozzle into PEI). The laser spot at r ≈ 42 mm is outside the ring, but the inclined laser sheet passes above the ring's front-left quadrant, so the ring must be shaped there.
- **Rigidity:** the best *potential* stiffness, because one carrier references the LiDAR, probe and hotend. But every sensor offset changes: LiDAR offsets (re-measured by `LIDAR_OFFSET_CALIBRATION`), the **LiDAR's internal calibration (sticker cal must not be re-run on the glass)**, probe x/y/z offsets, keep-out zones, twist compensation, mesh limits.
- **Serviceability:** a remote blower is easy to service. A ring duct often blocks nozzle access. A hotend swap means a new mount.
- **Printability:** a ring duct with internal plenums needs supports or split halves. It sits close to the heater, so it needs PC/PA-CF or better.
- **Heat:** the highest exposure (about 360° around the block).
- **Risks:**
  - largest design and verification effort;
  - remote-blower plumbing inside an enclosed chamber (Agent-dependent);
  - lag of cooling response (the hose volume);
  - recalibration of everything;
  - possibly a full carriage/rail redesign.

### 6.5 Ranking

1. **A**: lowest risk. Mass change ≤ +18 g (X ≥ 76 Hz). It keeps the µm-repeatable LiDAR geometry and all measured offsets (probe, keep-out, twist). A is also where the integrated sensor mounts pay off: probe on metal, cover off without unplugging the LiDAR.
2. **B′ (asymmetric dual fan)**: only if A's cooling is proven insufficient (e.g. LiDAR-measured overhang/bridge tests). It costs 40–66 g (X −4…−6.5 %), possibly X travel, and needs careful laser-sheet clearance. A symmetric B is ruled out while the LiDAR stays.
3. **C**: the best theoretical cooling and stiffness, but it changes every calibrated interface on a printer whose value is its calibrations. Hose forces are an unquantified disturbance. Revisit only together with an X-rail rebuild.

---

## 7. What the user must measure or provide

The stock carriage and LiDAR are not in any CAD I could reach. Calipers to ±0.05 mm unless noted. Photograph every item square-on with a ruler in frame.

1. **Hotend version:** photos of the heater block and the nozzle; is it the 2023 type or Unicorn/quick-swap? Is a hotend upgrade planned?
2. **Carriage, cover removed:** photos front, back, left, right, top and bottom. For **every** hole/thread on the carriage (cover screws, heatsink/hotend fixings, extruder fixings, PCB/fan, LiDAR bracket, probe mount, belt clamps), give the X, Y and Z distance to the nozzle tip. Method: measure to the nozzle side with calipers and add half the nozzle Ø; for Z, measure from a block placed under the nozzle tip.
3. **How the heatsink is held** in the carriage (clamp, screws from below or side), and the screw sizes.
4. **X rods:** diameter, centre-to-centre spacing, arrangement (stacked vertically? one front one back?), each rod axis's Y and Z relative to the nozzle tip, bearing type and length.
5. **Belts:** width, pitch, and the clamp location on the carriage; the Z of the upper and lower belt planes and the Y of the belt runs relative to the nozzle tip.
6. **Vertical stack:** nozzle tip → heatsink bottom, → carriage underside, → extruder top/lever top, → PTFE inlet top.
7. **LiDAR module:** outline L × W × H; bracket material (metal/plastic) and mounting screws (size, positions relative to the nozzle); position of each optical window (X, Y, Z of its centre relative to the nozzle tip) and which window emits the laser; photo from below with the laser on (line visible); module mass if it is ever removed.
8. **Stock cover:** mass with and without the 4020; the 4020 mass alone; the two cover screw positions; the duct outlet (lowest edge Z above the nozzle tip; outlet X/Y; outlet cross-section).
9. **Microprobe:** current mount (a photo or its CAD if user-made); retracted pin tip Z and deployed pin tip Z relative to the nozzle tip; probe body rear Y and body Ø.
10. **Clearances at the travel limits:**
    - at X = −2 and X = 306.5 (Y about 150): gap from the toolhead's left/right extremes to the XY joints, and at what Z;
    - at Y = −2: gap from the toolhead front to the door/front frame;
    - at Y max in a clear zone (X 105 or 195): gap from the stock rear and from the probe to the rear frame/Z housing, and the housing height;
    - at Z = 0: Z of the top frame/lid above the extruder top;
    - where the umbilical/cable chain attaches.
11. **Nozzle PCB:** photos of both sides showing the connector positions (and which cable goes where); the cable exit direction.
12. **Bed:** glass thickness + PEI; Z of the glass top relative to the stock plate; any bed clips/screws that stand above the glass near the edges.
13. **Weights (kitchen scale, ±1 g):** 4020 fan, 3010 fan, cover, LiDAR + bracket, probe + mount, and the extruder if it ever comes off.
14. **Moving-mass test (no disassembly):** run `SHAPER_CALIBRATE` as-is. Then tape a known mass Δm (e.g. 50 g of coins) rigidly to the toolhead and run it again. Effective mass = Δm / ((f0/f1)² − 1) per axis. Keep the raw CSVs (`/tmp/calibration_data_*.csv`) of both runs: they also show the torsional peaks.
15. **Thermal:** the chamber temperature during ABS (45 °C target) and, if possible, the cover temperature near the outlet. This decides between ASA and PA-CF/PC.

---

## 8. Notes and open points

- The derived hotend/extruder/PCB numbers come from a single community CAD source. The PCB outline/pattern is confirmed independently by the K1C gerber; the rest is not. **Check H3–H16 and E3–E10 against item 2/6 before freezing any interface.**
- Material heat ratings (ASA/ABS Tg about 100 °C, PC about 145 °C, PA-CF HDT 120–180 °C) are typical-datasheet ESTIMATES, not verified for specific filaments. Take them from the chosen filament's TDS.
- Stock K1 Max factory config files are from a third-party archive (Tombraider2006, firmware 1.3.3.5). The user's own Pellcorp `printer.cfg` limits should be checked against them (the repo's overrides do not restate travel).
