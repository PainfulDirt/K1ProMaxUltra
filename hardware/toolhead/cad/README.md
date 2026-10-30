# K1 Max toolhead: structure CAD (architecture A+)

Parametric build123d models of the parts that replace the stock front cover (DD-01), the
MicroProbe mount (DD-03), the fit-check coupon, the assembly, automated validation and
manufacturing exports. The duct air paths and duct bodies belong to the Duct/CFD agent
(`source/ducts/`); this side reads their `duct_interface.json` and never edits it.

Frame for every file: origin at the nozzle tip, +X printer right, +Y printer rear, +Z up, mm.
Every number comes from `source/interfaces.py`, or is a named parameter with a status and a
source (`structure/common.py::prm`), or is flagged. `validate.py` lists each printed part's
ESTIMATED / MISSING / STUB dependencies.

## Status (what to print)

| Part | File | Material | Mass (solid) | Release |
|---|---|---|---|---|
| Fit-check coupon | `exports/*/fitcheck_coupon.*` | ASA | ~2.9 g | **PRINT FIRST** (≈10 min) |
| Cooling-module frame | `exports/*/cooling_module_frame.*` | ASA | ~5.3 g | NOT RELEASED (cooling interface is a stub or provisional; PCB pads ESTIMATED, M10) |
| Cover | `exports/*/cover.*` | ASA | ~7.0 g | NOT RELEASED (follows the fan/duct pose) |
| MicroProbe mount | `exports/*/probe_mount.*` | PA-CF (PC acceptable) | ~11.4 g | NOT RELEASED (785004 anchor unconfirmed, M8) |

Masses assume 100 % infill (upper bound). Densities ASA 1.07, PC 1.20, PA-CF 1.15 g/cm³ are
typical TDS values (ESTIMATED); use the datasheet of the spool you buy. Current numbers, checks
and the full dependency list: `exports/validation_report.md` (stub) and
`exports/validation_report_ducts.md` (the Duct agent's provisional interface).

### Print the coupon first
`fitcheck_coupon` is printed face down, with no supports. It checks, on the real printer:
1. **PCB interface.** Put three M3×30 screws through the coupon into the PCB holes, one stock
   screw at a time. The coupon reproduces the frame's own boss code:
   - Ø5.8 neck through the PCB "2nd plate" holes;
   - boss length 9.2 mm, bridging the component zone;
   - the compression pad at the fourth pattern corner.

   Every pad must sit flat. Nothing on the PCB may touch the plate. The window must line up
   with the PCB fan cutout. If a pad lands on a component, report its X/Z (M10).
2. **Probe seat.** Heat-set two M2.5 inserts. The MicroProbe flange must drop into the fence,
   and the BIQU M2.5×5 screws must reach. The fence notch marks the connector (rear) side.
3. **M3 insert hole.** Heat-set one M3 insert into the boss on the ring (the hole size the
   frame uses).

If an insert is loose or splits, change `INSERT_*_HOLE_D` in `structure/common.py` and
re-export. The heat-set hole sizes are vendor-typical (ESTIMATED).

## Workflow

```bash
source /opt/k1th/env.sh                          # build123d 0.13 venv as $K1_PY
cd hardware/toolhead
$K1_PY cad/source/assembly.py                    # build everything, print a part table
$K1_PY cad/source/validate.py                    # checks -> cad/exports/validation_report.{json,md}; exit 1 on FAIL
$K1_PY cad/source/validate.py --cooling ducts    # same against the Duct agent's interface -> *_ducts.{json,md}
$K1_PY cad/source/export.py                      # STEP/3MF/STL + assembly STEP, re-opened and verified
```

- `validate.py` takes about 3 min. `--samples N` sets the number of wall-thickness rays.
  `--no-stock-cache` forces the box references.
- **Stock solids (optional, recommended).** Henlor's reverse-engineered K1 assembly (Printables
  742370, CC BY) gives real carriage/heatsink/PCB/3010/extruder solids for the interference
  checks. Generate the cache once with
  `python -I cad/source/structure/stock_cache.py <creality-k1-assembly-alpha-v001.step> [outdir]`
  (or set `K1TH_STOCK_CACHE`). The cache stays outside the repository. Exports never contain
  third-party geometry: the assembly STEP uses the boxes from `interfaces.py`.
- Export tolerances, documented in `export.py`:

  | Check | Tolerance |
  |---|---|
  | STEP round trip | 1 solid, dV/V < 1e-6, bbox 1e-3 mm |
  | 3MF / STL | 1 object, dV/V < 5e-3, bbox 0.05 mm; STL watertight |
  | Assembly STEP | same named, coloured leaves and groups, per-leaf dV/V < 1e-6 |

  STEP headers carry a timestamp, so re-exports are identical in content but not byte for byte.

## Layout of `source/`

| File | Content |
|---|---|
| `interfaces.py` | shared interface values (owned by the lead; read-only here) |
| `structure/common.py` | parameter registry (`prm`), materials, inserts/screws, helpers, `PartSpec`, release rule |
| `structure/reference.py` | non-printed references: nozzle, heater, sock, heatsink, 3010, PCB (+ fan cutout from the K1C gerber, + Henlor "2nd plate"), extruder, belt retainers, rods, probe body/pin, keep-outs (component zone, LiDAR optical/body boxes, laser sheet), replaced stock parts |
| `structure/stock_cache.py` | Henlor solids → nozzle-frame STEP cache (validation only) |
| `structure/cooling.py` | cooling interface: STUB + adapter for `ducts/duct_interface.json` + `build_ducts()` |
| `structure/frame.py` | cooling-module frame |
| `structure/cover.py` | cover |
| `structure/probe_mount.py` | MicroProbe mount |
| `structure/coupon.py` | fit-check coupon |
| `structure/stiffness.py` | hand stiffness / first-mode / thermal-drift estimates |
| `assembly.py` | part list, `COOLING_SOURCE` switch, grouped and coloured assembly compound |
| `validate.py` / `export.py` | checks / exports |

## Parameter map (main ones; all are in the report with status and source)

| Part | Driven by `interfaces.py` | Own parameters (DESIGN unless noted) |
|---|---|---|
| frame | `MODULE_MOUNT_HOLES`, `MODULE_MOUNT_BEARING_Y` (−22.3), `MODULE_MOUNT_PAD_D`, `PCB_COMPONENT_ZONE` (plate back at −31.5), `PCB`, `FAN3010_PATTERN_CZ`, `LIDAR_RESERVED_BOXES`, `RIGHT_LIMIT_X` | `FRAME_PLATE_T` 2.0; `FRAME_ZMAX` 71.8 (below the carriage strain relief); `FRAME_XMAX` 20; `FRAME_WINDOW_R` 15 (teardrop, intake ≥ 625 mm²); `FRAME_RIB_DEPTH` 2.0; `FRAME_BOSS_D` 7.5 with a Ø5.8 neck (Henlor 2nd-plate holes Ø6.2, DERIVED); `FRAME_FOURTH_PAD_ON` (ESTIMATED); `FRAME_PCB_SCREW_LEN` 30 (3× M3×30 ISO 7380 replace stock M3×18/18/20); cover screws `COVER_SCREW_X/Y`; tie slots `FRAME_TIE_*` |
| cover | `PCB`, `XCARRIAGE`, `RIGHT_LIMIT_X`, LiDAR boxes | `COVER_HALF_W` 24.0 (stock width, DERIVED); `COVER_WALL` 1.2; `COVER_GAP` 1.0; `COVER_ZMIN` 24; top wall stops in front of the strain relief (`CARRIAGE_STRAIN_RELIEF_YMIN`, DERIVED 02:N16) |
| probe mount | `PROBE_*`, `PROBE_BODY_Y`, `PROBE_ADAPTER_785004`, `PROBE_ADAPTER_SCREWS`, `REAR_LIMIT_Y`, `SOCK` | 785004 relations from 01 §H.1 (`PM_SEAT_TO_ANCHOR_Z` 27.05, `PM_SEAT_TO_TOP_Z` 32.5, `PM_MATING_FACE_Y` 16.9, `PM_FRONT_LOW_Y` 13.4, windows, Ø2.4/Ø4.2 anchor holes); carriage tabs from Henlor (`PM_TAB_*`); `PM_PAD_T` 4; `PM_WALL` 2.4; pocket 0.8 deep; M2.5 inserts; `PM_ANCHOR_CONFIRMED_M8` (MISSING) |
| coupon | same as frame bosses + probe flange | `COUPON_*` |
| stub cooling | `STOCK_4020_POS` (XZ centre), `BLOWER_4020_STOCK` | `STUB_*` (status STUB) |

## Changing the fan / duct variant

1. The Duct/CFD agent publishes `source/ducts/duct_interface.json` and `build_ducts(params)`.
2. In `source/assembly.py`, `COOLING_SOURCE` is the only switch:

   | Value | Behaviour |
   |---|---|
   | `auto-final` (default) | the real ducts once the JSON says `final_mount_points: true`, else the stub |
   | `ducts` | forces the real ducts |
   | `stub` | forces the placeholder |

3. `structure/cooling.py::_convert_ducts_schema` maps the Duct agent's schema onto the internal one:
   - fans with `envelope_box`;
   - `screw_bosses` with `xyz` / `axis` / `through_length`: the mount point is placed on the fan face toward the frame;
   - `duct_attach_points` with `hole_centre` / `screw_axis` / `mating_face`.

   The internal schema is documented at the top of that file.
4. Frame mount rules. A point that breaks them is not built and appears as a FAIL in the report:
   - The screw runs along +Y into a brass heat-set insert in the frame. Other axes are skipped (a WARN if the point is marked optional).
   - The point lies on the plate (standoff) or below it (lug, bridged sideways if needed). It cannot sit beside the plate where the plate is cut for `LIDAR_RESERVED_BOXES`.
   - It stays ≥ 6.8 mm (insert boss r 3.6 + head clearance r 3.15) from every PCB screw axis. Otherwise the standoff blocks the PCB screw's install path (checked as "driver access").
5. Run `validate.py --cooling ducts`, then switch the default when it passes.

## Design notes

- **Frame.**
  - 2.0 mm ASA plate directly in front of the PCB component zone, with front ribs open at Z 36…56 so the plenum between plate and fan is fed from the sides.
  - Teardrop window (assembly-down point), so it prints upside down without support, in front of the PCB fan cutout. The cutout was found in the K1C gerber: R 13.7 clipped at X ±12, ≈559 mm².
  - Bosses bear on the PCB around the three screws. A compression pad at the fourth corner backs the lower fan screw.
  - The plate stays out of the LiDAR boxes. Only the unavoidable screw column at PCB hole (−12, 34.3) enters `LIDAR_RESERVED_BODY` (allow-listed; that box overlaps the stock PCB, 3010, heatsink and carriage).
  - Heat-set inserts for every screw the frame takes (fan, duct, cover): service cycles, 45 °C chamber, no thread creep in ASA.
- **Cover.**
  - 1.2 mm ASA, ±24.0 wide (inside `RIGHT_LIMIT_X` 24.2 in the XY-joint band).
  - Two M3×6 screws from the top into the frame shelf.
  - Open at the bottom and rear, so it slides forward without unplugging the LiDAR, probe or fan, and without removing the duct.
  - Front vents over the fan intake; side and top vents over the plenum (3010 intake path).
  - Left wall cut back out of the LiDAR boxes.
  - Reusing the stock carriage cover screws (X ±22.6, Y −2.2, Z 35.35) would need an arm through `LIDAR_RESERVED_BODY` on the left, so they are not used.
- **Probe mount.**
  - Drop-in replacement for Printables 785004 on the same two carriage tabs.
  - The bores sit at the same offset from the anchor as in 785004, so the pin lands where it does today whatever the pin-to-hole offset is (1.0 in `interfaces.py`, 2.75 in the V1 STEP).
  - Stiffer than 785004: PA-CF, a closed box section, a flange locating pocket, and M2.5 inserts.
  - The load path cannot be shorter: the anchor height is set by the carriage.
  - Printed upside down, no supports.
- **Stiffness** (hand estimates, `structure/stiffness.py`; numbers in the report):
  - Frame rocking on the 3 screws is ≥ 1 kHz.
  - The lower fan screw is the weak spot. With the fourth pad its local mode is in the kHz range. Without it (if M10 shows the pad cannot bear), the estimate falls to about 150 Hz, near 2 × the X shaper frequency.
  - Probe mount: sub-µm deflection. Thermal growth of the 27 mm printed path is about 11 µm per 10 K (PA-CF), against about 19 µm for a PLA/PETG 785004.

## BOM (per toolhead)

| Item | Qty | Note |
|---|---|---|
| M3×30 ISO 7380 | 3 | replace the stock PCB screws (M3×18 ×2 into carriage inserts, M3×20 into the heatsink) |
| M3 brass heat-set insert, short (hole Ø4.0) | 6 (stub) | 2 fan, 2 duct, 2 cover |
| M3×6 ISO 7380 | 2 | cover |
| M3 × (fan thickness + 4) | 2 | fan to frame (length follows the fan) |
| M2.5 brass heat-set insert (hole Ø3.6) | 2 | probe |
| M2.5×5 | 2 | probe (BIQU kit) |
| ~M2 screws | 2 | probe mount to carriage tabs: reuse 785004's |
| cable ties 2.5 mm | 3 | frame top corners, probe mount roof |
