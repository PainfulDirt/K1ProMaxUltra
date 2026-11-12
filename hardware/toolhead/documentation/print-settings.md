# Print settings for the toolhead parts

For the K1 Max with the repo's OrcaSlicer 2.4 profiles (`orcaslicer/`). Part data comes from
`cad/exports/validation_report.md` (S7 duct, `duct_interface.json` v3-final), `cad/README.md`,
`cfd-report.md` §12.3 and the part sources in `cad/source/`. Release state per part is in
`bill-of-materials.md` §1: print the coupon first; the frame, cover and duct are FIT-CHECK FIRST;
the probe mount is NOT RELEASED.

Materials (DD-07): **PC or PA-CF** within 15 mm of the heater (the whole duct body, the probe
mount); **ASA** (or ABS) elsewhere; **no PLA or PETG** anywhere.

**Duct from a print service (DD-07a), chosen by the user (2026-11-12).** Order the duct body in
HT resin, two pieces. It needs HDT ≥ 130 °C at 0.45 MPa after the full post-cure, per the TDS;
order a 238 °C-class resin. The fallbacks are PC (the FDM row below) or MJF PA12. Send the duct STEP or STL, and put the following in the order:
- full thermal post-cure;
- every port flushed clean;
- no support contact on the outlet lips, inside the ports or on the socket faces.

Fitting a resin duct: washers under the three tab screws; tighten only until the tab seats. Order
two (a resin lip chips rather than bends).

## 1. Per part

| Part (file in `cad/exports/{3mf,stl,step}/`) | Material | Orientation (as exported to 3MF) | Layer | Walls | Top / bottom | Infill | Supports | Brim | Notes |
|---|---|---|---|---|---|---|---|---|---|
| **Fit-check coupon** `fitcheck_coupon` | ASA, same spool and settings as the frame, so the shrinkage matches (`coupon.py`) | front face down (`print_rot` 90° X); 10.8 mm tall | 0.16 | 4 | 5 / 5 | 100 % | none (0.3 % > 45°, 13.3 mm² bridges) | none, or 3 mm if the corners lift | **PRINT FIRST**. ≈ 10 min, 2.89 g |
| **Cooling-module frame** `cooling_module_frame` | ASA | upside down: top shelf and top edge on the bed, plate vertical (`print_rot` 180° X); the PCB bosses print as horizontal cylinders | 0.16 (rounder horizontal holes) | 5 (the 2.0 mm plate prints solid) | 6 / 6 | 100 % (the parts are mostly walls; masses are 100 % values) | **none**: the teardrop window and short bridges are designed for it (validation INFO: 8.1 % > 45°, 176.4 mm² flat ceilings) | 5 mm, footprint is narrow and 55.9 mm tall | FIT-CHECK FIRST. 5.84 g. Min wall 0.85 mm, 0.00 % of rays under 0.8 mm (validation PASS) |
| **Cover** `cover` | ASA | front face down (`print_rot` 90° X); all vents are vertical holes or slots | 0.20 | 3 (the 1.2 mm wall = 3 × 0.4 lines, `cover.py`) | 5 / 5 | 100 % | none (validation INFO: 0.3 % > 45°, 30.7 mm² bridges) | 3 mm | FIT-CHECK FIRST. 6.35 g. Cosmetic outer surface on top; seam at the rear edge |
| **Duct body (S7)** `duct_body` | **PC** (or PA-CF) | **upright as modelled**: fan socket up, nozzle-frame +Z = print Z (`print_rot` 0); the lowest points (the port lips, nozzle-frame Z 2.44) are at the bed; 46.8 × 84.0 × 25.0 mm | 0.12 | as many as fit the 1.2 mm wall (3) | 5 / 5 | 100 % | **external only, under the manifold, the plenum underside and the outer lip bottoms** (`cfd-report.md` §12.3, §16). **None in the air path**: every internal ceiling is ≥ 45°, apart from 0.67 mm² of sub-millimetre micro-bridges at the port roots that print as bridges. See "Duct supports" below | 5 mm, **outer only**; trim it clear of the outlet lips | FIT-CHECK FIRST. 9.24 g PC (8.9 g PA-CF). Check every outlet after printing (below) |
| **MicroProbe mount** `probe_mount` | **PA-CF** (PC acceptable) | upside down: top face on the bed (`print_rot` 180° X) | 0.12–0.16 | ≥ 5 | 6 / 6 | 100 % (`probe_mount.py`: "100 % infill or ≥ 5 walls") | none (4.3 % > 45°, 292 mm² bridges) | 5 mm (PA warps) | **NOT RELEASED** (M8). Hardened nozzle; anneal (§4) **before** setting the inserts |

Common settings for all parts:
- 0.4 mm nozzle; seam "Aligned" or "Back", away from mating faces and outlets.
- XY hole compensation 0 and XY contour compensation 0. Insert and screw holes are tuned in CAD
  (`INSERT_*_HOLE_D` in `structure/common.py`) from the coupon result, not in the slicer.
- Elephant-foot compensation 0.1 mm on the coupon and frame (the faces on the bed are mating or
  reference faces), and on the duct (its lips are its lowest point and set the 2 mm bed margin).
- Ironing off.
- Base the process on `0.16mm Optimal Precision @K1 Max Tuned 0.4` (0.20 Standard Precision for
  the cover). "Precision" has the 10 mm³/s quality cap (`orcaslicer/README.md`), and it is the
  right tier for small functional parts.

### Duct supports and checks

The validator's "16.1 % of surface > 45°, 1642 mm² flat ceilings" for the duct counts the
**outside** downward faces: the manifold and plenum undersides and the outer lip bottoms
(`cfd-report.md` §16). Those need supports from the build plate. The inside of the duct needs none.

In Orca:
- supports **on**, type normal (not tree), "on build plate only", so nothing can start on an inside
  floor;
- a **support blocker** over the fan socket opening, the plenum and every one of the 5 outlets, in
  case Orca still proposes anything there;
- top Z distance about 0.2 mm and one interface layer, so the supports come off the PC cleanly
  (ESTIMATED starting values);
- if Orca shows support **inside** a channel in the preview, do not print: the model or the
  settings are wrong.

After printing:
- remove the supports with flush cutters, without levering on the lips;
- check that each of the 5 outlets is open over its full 6 × 3 mm (`cfd-report.md` §12.3): measure
  the port height with calipers or pin gauges, and look for strings or support remnants in the
  ports. A port more than about 0.3 mm under size, or partly blocked, is a reject (ESTIMATED limit);
- check the fan socket: it must slide over the 4020 outlet nozzle without force (CAD: 1.0 mm
  clearance per side, ESTIMATED, M7);
- the lowest point is the lip at Z 2.44 above the nozzle tip in the assembly. If the lips print
  with elephant foot or a support scar, it eats into that 0.44 mm margin over `DUCT_MIN_Z` 2.0.

## 2. OrcaSlicer filament settings

### 2.1 ASA: use "ASA @K1 Max Tuned" (in the repo)

The profile has 260 °C nozzle, 100 °C bed, 16 mm³/s max, PA 0.04, fan 0–30 %, chamber 45 °C
(START_PRINT waits for it) and `M141 S60` (chamber fan held off until 60 °C). Changes for these
parts:

| Setting | Change | Why |
|---|---|---|
| Max volumetric speed | 16 → **10** mm³/s | small parts; the Precision tier caps at 10 anyway |
| Fan min/max | keep 0–30 % | ASA warps with more |
| Overhang/bridge fan | set **40 %** explicitly | the inherited Creality Generic value is unknown (M18); the frame window bridges need some air (ESTIMATED) |
| Min layer time | 8 s | the coupon and probe mount are tiny, and ASA needs time to set (ESTIMATED) |
| Chamber | keep `chamber_temperature 45` → `CHAMBER_TEMP=45` heat soak; keep the lid and door closed | README "Chamber Heat Soak" |
| PA | confirm with `LIDAR_PA_CALIBRATION EXTRUDER_TEMP=260 BED_TEMP=100` | 0.04 is a starting point (`orcaslicer/README.md`) |

### 2.2 PC and PA-CF: new profiles derived from "ASA @K1 Max Tuned"

There is no PC or PA-CF profile in the repo. Duplicate the ASA profile and change the values below.
All values are ESTIMATED starting points: use the spool's TDS.

| Setting | PC | PA-CF | Note |
|---|---|---|---|
| Nozzle °C | 270 (first layer 270) | 270–285 (PA12-CF ~270; PA6-CF higher) | K1 hotend limit 300 °C (Creality spec, SECONDARY). A hardened nozzle conducts worse: +5–10 °C |
| Bed °C | 100 | 90–100 | the K1 Max bed is 100 °C max (SECONDARY) |
| Plate | textured PEI with a thin glue-stick layer (release agent; PC can bond too strongly) | textured PEI with glue stick | the glass + PEI bed (README) |
| Density (Orca and `MPC_SET`) | 1.20 | 1.15 | `structure/common.py` |
| `filament_start_gcode` | `MPC_SET HEATER=extruder FILAMENT_DENSITY=1.20 FILAMENT_HEAT_CAPACITY=1.25` + `M141 S60` | `... FILAMENT_DENSITY=1.15 FILAMENT_HEAT_CAPACITY=1.5` + `M141 S60` | heat capacities ESTIMATED |
| Max volumetric | 10 | 8 | ESTIMATED |
| Flow ratio | 0.95–0.98, calibrate | 0.95–0.98, calibrate | |
| Fan min/max; overhang | 0–20 %; 40 % | 0–20 %; 40 % | |
| Chamber | 45 (heat soak; the macro gives up after 30 min) | 45 | README |
| PA | `LIDAR_PA_CALIBRATION EXTRUDER_TEMP=270 BED_TEMP=100` | same at the PA-CF temperature | |
| **Nozzle** | brass or hardened | **hardened steel required** (CF is abrasive) | see below |
| Drying | must be dry (§4) | must be dry, print from a dry box | |

**Hardened nozzle: check what you have.** The repo's printer profiles say `nozzle_type: brass`,
and the README lists 0.2–1.0 nozzles without saying which are hardened. Creality sells the K1 Max
with a hardened-steel-tipped nozzle (research/02 §4, SECONDARY), but which nozzle is fitted now is
not recorded. Before printing PA-CF:
- confirm the fitted nozzle is hardened steel (a magnet sticks to steel, not to brass or copper);
- check whether the extruder gears are hardened;
- after the nozzle change, follow `maintenance.md` §1 (z_offset, LiDAR offsets, PA).

If no hardened nozzle is available, print the probe mount in **PC** (`probe_mount.py`: "PC
acceptable") and the duct in PC (the duct's default material is PC anyway).

## 3. Heat-set inserts

CAD values are in `structure/common.py`. The hole sizes are ESTIMATED and confirmed by the coupon.

| Insert | Hole Ø (CAD) | Hole depth | Insert length (CAD) | Where |
|---|---|---|---|---|
| M3 brass, short | 4.0 | 5.0 (= 4.0 + 1.0 relief) | 4.0; any length ≤ 4.5 fits | frame: 6 = 2 cover shelf (vertical holes), 2 fan standoffs and 2 duct lugs T_left / T_right (horizontal holes); coupon: 1 |
| M2.5 brass, short | 3.6 | 5.0 | 4.0; ≤ 4.5 | probe mount: 2; coupon: 2 |

Procedure:
1. Part fully cooled, and **after** annealing if it is annealed.
2. Soldering iron with the matching insert tip. Temperature (ESTIMATED; start low and raise
   by 10 °C if the insert needs force):

| Material | Iron |
|---|---|
| ASA | 230–250 °C |
| PC | 260–280 °C |
| PA-CF | 270–290 °C |

3. Set the insert on the hole, straight. Let it sink under its own weight plus light pressure, in
   3–5 s. **Never force it.** Stop **flush to 0.2 mm below** the surface.
4. Remove the iron. Within 2 s, press a cold flat metal block on the insert for 10 s, so it stays
   square and flush.
5. For horizontal holes (frame standoffs): clamp the part so that the hole axis is vertical.
6. Check:
   - an M3 / M2.5 screw runs in by hand without binding;
   - the insert does not spin when the screw is tightened snug (≈ 0.4–0.5 N·m for M3, ≈ 0.25 N·m
     for M2.5, ESTIMATED);
   - there is no bulge or crack on the boss.
7. If an insert is loose: the hole is too big. If a boss bulges or splits: the hole is too small.
   Report the Ø and the CAD side changes `INSERT_*_HOLE_D` in steps of 0.1 mm (cad/README "Print
   the coupon first").

## 4. Drying and annealing

| Material | Drying (before printing) | Annealing | Notes |
|---|---|---|---|
| ASA | 4 h at 65–80 °C if the spool has been open (ESTIMATED) | not needed | |
| PC | ≥ 6 h at 70–90 °C (ESTIMATED; per TDS) | optional: 1–2 h at 110–120 °C, slow oven cool (ESTIMATED; per TDS); relieves stress near the hot zone | measure the part before and after; re-check the fit |
| PA-CF | 8–12 h at 80–100 °C (ESTIMATED; per TDS); keep it in a dry box while printing | recommended if the TDS gives a cycle (it raises HDT strongly for most PA-CF); typically several hours at 80–100 °C (ESTIMATED) | do it **before** the inserts; the part may shrink slightly, so re-measure the probe pocket (21.93 × 15.60 + 0.1 per side) |

## 5. Fit-check coupon procedure

`fitcheck_coupon` reproduces, with the production code, the interfaces whose values are DERIVED or
ESTIMATED (`coupon.py`): the frame's PCB bosses, the probe seat and one M3 insert boss.

**Print** it per §1 (ASA, face down, 100 %, no supports).

**Hardware:**
- 3 × M3×30 ISO 7380;
- **3 × M3 washers ISO 7089 (0.5 mm), under the heads, for the coupon only.** The coupon plate is
  1.6 mm against the frame's 2.0 mm, so without washers the M3×30 tips go 0.4 mm deeper than the
  frame's (which the CAD checked against the carriage: tip at Y −3.5).
- 1 × M3 insert;
- 2 × M2.5 inserts;
- the BIQU M2.5×5 screws.

**Steps:**
1. **Measure the part first** (calipers ±0.05):

| Feature | CAD value | Accept | Source |
|---|---|---|---|
| Overall depth, plate front face to neck tips | 10.8 (1.6 plate + 9.2 boss) | ±0.15 | validation bbox 32.0 × 51.8 × 10.8; `coupon.py` |
| Ring width (X) | 32.0 | ±0.15. Use the error to estimate ASA shrink: (32.0 − measured) / 32.0 | `COUPON_RING_HALF` 16 |
| PCB hole pattern, centre to centre (outer edge minus one Ø) | 24.0 | ±0.10 | `FAN3010_PATTERN` |
| Neck Ø at the PCB end (3×) | 5.8 = min(`MODULE_MOUNT_PAD_D` 6.5, 2nd-plate hole 6.2 − 0.4) | ±0.10 | `frame.py` `PAD_D` |
| Neck step: neck tips to the 4th-corner pad face | 6.34 (PCB face Y −22.3 vs 2nd plate Y −28.64) | ±0.15 | `reference.py` |
| Probe fence inside | 22.13 × 15.80 (flange 21.93 × 15.60 + 0.1 per side) | the probe drops in without force, play ≤ 0.2 | `coupon.py` |
| Probe insert spacing | 17.0 | ±0.10 | `PROBE_HOLE_SPACING` |

2. **Inserts:** set the M3 and the two M2.5 inserts (§3). Note the iron temperature and how each
   went (easy / forced / loose / bulged).
3. **PCB interface,** printer off and cold:
   1. Take the stock cover off (2 × M3×4 at the sides; check the LiDAR bracket and unplug the 4020
      first, `assembly.md` step 2).
   2. Swap the stock PCB screws for the 3 × M3×30 + washers through the coupon. The coupon's bosses
      sit over the screw heads (Ø3.4 bores against a Ø5.7 head), so a stock screw cannot stay in a
      hole the coupon covers. Hold the PCB flat against the 3010 with one hand, take the three stock
      screws out, offer the coupon and start all three M3×30 by hand before tightening any
      (`assembly.md` step 4 describes the same swap for the frame).
   3. Tighten snug only, so the ASA is not crushed.
   4. Check and record:
      - every neck enters its PCB hole square and seats flat on the PCB: a 0.05 feeler must not
        pass under a neck;
      - nothing on the PCB touches the plate, and no neck lands on a component (if one does, note
        its X/Z: M10);
      - the window lines up with the PCB fan cutout (R 13.7 cutout vs the coupon's R 12.5 window);
      - **4th pad** (corner X +12, Z 34.3): does it touch the PCB "2nd plate"? Note the gap with
        feelers. A gap above 0.3 mm, or no 2nd plate at all, means the frame's fan-plate mode
        drops to ~150 Hz (validation WARN 147 Hz). Report it.
      - the hotend fan (3010) still spins freely at > 40 °C nozzle (heat briefly with the coupon
        fitted), and its intake is not blocked.
   5. Refit the stock screws and cover.
4. **Probe seat:** drop the MicroProbe into the fence. Fit the 2 × M2.5×5. Each must engage ≥ 5
   turns (2.9 mm of thread at 0.45 mm pitch) and seat flat without bottoming. The notch marks the
   connector (rear) side.
5. **M3 insert pull check:** screw an M3 screw in and tighten to snug + 1/8 turn. The insert must
   not spin or lift.

**Report back** (to the lead, who updates the CAD):
- the measured dimensions vs the table above;
- the insert verdicts and iron temperatures;
- the 4th-pad gap;
- any component under a neck, with its X/Z;
- photos of the PCB with the coupon on (M10).

Pass for releasing the frame geometry: all dims within tolerance, inserts good, necks flat on
bare PCB, no contact with components.
