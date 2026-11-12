# K1 Max toolhead: structure CAD (architecture A+)

Parametric build123d models of the parts that replace the stock front cover (DD-01), the
MicroProbe mount (DD-03), the fit-check coupon, the assembly, automated validation and
manufacturing exports. The duct air paths and duct bodies belong to the Duct/CFD agent
(`source/ducts/`); this side reads their `duct_interface.json` and never edits it.

**Current state.** The CFD phase is finished. The baseline is **one stock Creality 4020 blower in
the front bay plus the S7 multi-port duct** (`ducts/duct_generator.py`, param set S7;
`duct_interface.json` v3-final, `final_mount_points: true`). `assembly.py` (`COOLING_SOURCE =
"auto-final"`) therefore builds the real duct body, and the frame and cover are built around it:

- fan envelope X −21.3…18.7, Y −56.5…−36.5, Z 23.4…63.4, held on its two diagonal screws
  (−18.65, 60.3) and (16.05, 25.6);
- duct body Z 2.44…27.4, bolted to frame lugs at T_left (−7.5, −37.75, 19.5) and
  T_right (24.0, −37.75, 22.5), M3 along +Y.

The placeholder stub in `structure/cooling.py` is only a fallback. A Same Sky 5015 (+ 24→12 V buck)
is a conditional upgrade, not the baseline: no buck mount is modelled.

Frame for every file: origin at the nozzle tip, +X printer right, +Y printer rear, +Z up, mm.
Every number comes from `source/interfaces.py`, or is a named parameter with a status and a
source (`structure/common.py::prm`), or is flagged. `validate.py` lists each printed part's
ESTIMATED / MISSING / STUB dependencies.

## Status (what to print)

| Part | File | Material | Mass (solid) | Release |
|---|---|---|---|---|
| Fit-check coupon | `exports/*/fitcheck_coupon.*` | ASA | 3.0 g | **PRINT FIRST** (≈10 min) |
| Cooling-module frame | `exports/*/cooling_module_frame.*` | ASA | 6.3 g | FIT-CHECK FIRST (PCB pads and component zone ESTIMATED, M10; 4020 holes, thickness and hole type ESTIMATED, M7; insert size; sleeve tube ESTIMATED until bought) |
| Cover | `exports/*/cover.*` | ASA | 6.34 g | FIT-CHECK FIRST (follows the 4020 front face and inlet diameter, M7; LiDAR boxes, M6) |
| Duct body (S7) | `exports/*/duct_body.*` | PC (or PA-CF, 8.9 g) | 9.2 g | **does not pass validation** (4 FAILs below, review R-01/R-02/R-05). The release table still says FIT-CHECK FIRST, from its dependencies alone. S8 is in progress |
| MicroProbe mount | `exports/*/probe_mount.*` | PA-CF (PC acceptable) | 11.5 g | NOT RELEASED (785004 anchor unconfirmed, M8) |

Masses assume 100 % infill (upper bound). Densities ASA 1.07, PC 1.20, PA-CF 1.15 g/cm³ are
typical TDS values (ESTIMATED); use the datasheet of the spool you buy. The duct body is owned by
the Duct/CFD agent; it is exported here as printed: upright as modelled (fan socket up, nozzle-frame
+Z = print Z), PC or PA-CF (DD-07: within 15 mm of the heater). Current numbers, checks and the full
dependency list: `exports/validation_report.md` (default source) and
`exports/validation_report_ducts.md` (`--cooling ducts`, identical while the JSON is final).

Validation today (`validate.py` with the S7 duct, Henlor stock cache present): **4 FAIL, 9 WARN**.
The phase 6 review (`documentation/review/phase6-review.md`) added several checks. All four FAILs
and three of the WARNs are on the S7 duct or the fan/duct interface, and they are the targets for S8:

| Status | Check | S7 result | Target |
|---|---|---|---|
| FAIL | rear footprint (R-01) | 191 mm² / 758 mm³ of the duct lies outside the MicroProbe body + 785004 footprint behind Y +10, below Z 30 (excess X 13.7…31.0, Y 10.0…27.3, Z 2.4…18.1) | nothing outside that footprint, or re-measure keep-out zones 1/3/4 with the duct fitted |
| FAIL | duct bed contact (R-05) | 0 mm² flat on the plate, upright | ≥ 100 mm² (WARN below, FAIL at 0) |
| FAIL | duct × 4020 solid (R-02) | 1.23 mm³: the T_right arm enters the modelled outlet nozzle at X 17.25…18.7, Y −39…−38, Z 24.4…25.5 | ≤ 0.5 mm³, and only inside the socket band |
| FAIL | lower fan screw shank (R-02) | the Ø3 shank at (16.05, 25.6) cuts the duct's T_right arm: 2.43 mm³ at X 16.5…17.5, Y −39…−36.5, Z 24.2…25.5 | clear |
| WARN | lower fan screw head | 0.299 mm from the duct socket | ≥ 0.5 mm (`HEAD_MIN_GAP`, R-15) |
| WARN | fan hole vs outlet (R-02) | 154 mm³ of the lower Ø3.4 fan bore lies inside the ESTIMATED outlet column | M7: the hole positions and the outlet contradict each other |
| WARN | duct cantilever (R-22) | pitch mode 113…598 Hz. The weak link is the tab arms in torsion. Lever 64.0 mm from the tab face (the review's ~64 is confirmed) | > 155 Hz: a third tab, or arms of real section |
| WARN | duct min wall 0.37 mm | acute-edge ridges at the port roots, not a thin wall (see below) | — |
| WARN | fan screw tips (×2) | M3×24 ends 0.20 mm from the new 0.8 mm insert floor; the safe length is 22.5…23.7 mm, and no standard ISO 7380 length fits | decided by M7 (fan through-length and hole type, R-03) |
| WARN | front extent −58.2 vs `FRONT_LIMIT_Y` −55 | soft limit (M9); the 4020 alone reaches −56.5 | — |
| WARN | probe anchor | M8 | — |
| WARN | frame fan-plate mode without the 4th pad, 147 Hz | M10 | — |

Duct min wall: every thin ray sits on an acute convex edge (66–85°; 42–86° in a denser 8000-ray
scan, 0.43 % of rays), and none lies between parallel faces. They are the 65° ridges where each 25°
port floor steps 0.6–1.1 mm down onto the manifold floor, plus the port-side/manifold junctions.
These are inside the air path.

The tolerance stack-up (R-16, INFO) assumes ±0.2 mm per screw-in-clearance joint and ±0.2 mm per
printed part.
- Duct position: worst case 0.62 mm, RSS 0.35 mm. This exceeds the S7 margins of 0.35 mm (hot zone)
  and 0.44 mm (`DUCT_MIN_Z`), so S8 needs more margin.
- Fan screw head vs its cover hole: worst case 0.8 mm, RSS 0.4 mm, against 0.5 mm radial clearance.

`LIDAR_RESERVED_BODY` overlapping the stock carriage by 1.2 mm in X is reported as INFO: the box's
inner face (X −24, stock cover width) lies inside the carriage's left face (X −25.2), which is
where the LiDAR bracket seats. The box stays as is until M6.

Moving mass vs stock: **+1.2 … +10.1 g**. This counts printed parts at 100 % infill, all
screws/inserts and the 3 brass sleeves, minus the stock cover+duct, the 785004 adapter and the stock
PCB screws. X shaper 76.7…77.5 Hz at an X moving mass of 450 g (77.6 Hz today); Y 51.7…52.0 Hz.

### Print the coupon first
`fitcheck_coupon` is printed face down, with no supports. It checks, on the real printer:
1. **PCB interface.** The coupon's Ø3.4 bores sit over the Ø5.7 heads of the stock screws, so a
   stock screw cannot stay in a hole the coupon covers. Swap all three in one go:
   - hold the PCB flat against the 3010 with one hand;
   - take all three stock screws out;
   - offer the coupon;
   - start all three M3×30 by hand, each with an M3 washer, before tightening any. The coupon plate
     is 1.6 mm thick against the frame's 2.0 mm, and the washer restores the screw depth.

   The frame uses the same swap (`documentation/assembly.md` step 4). The coupon reproduces the
   frame's own boss code:
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

- `validate.py` takes about 2 min. Since the phase 6 review it also checks:
  - **rear footprint (R-01):** behind Y +10 and below Z 30, every part including the duct and the fan must
    stay inside the MicroProbe body + 785004 XY footprint the rear keep-out zones were measured with;
  - **the 4020 as a solid (R-02):** body + ESTIMATED outlet nozzle + corner bores. It is checked like a
    printed part against stock solids, the LiDAR boxes and the travel limits. Only the socket band and
    ≤ 0.5 mm³ of duct may overlap it;
  - **screw shanks and tips:** for every added screw, the tip must leave ≥ 2.5 mm of thread engagement in
    its insert and stop ≥ 0.5 mm short of the blind-hole floor (R-02/R-03);
  - **inserts:** the wall around every insert knurl (R-20);
  - **bed contact:** each part in its own print frame (R-05);
  - **estimates and stack-up:** a duct cantilever mode estimate (R-22) and a tolerance stack-up (R-16).

  It also models every added screw's ISO 7380 head and a straight
  driver path (Ø6.3 driver, fallback Ø3.0 for a 2.0 mm hex key, 25 mm long). Heads are checked against
  every printed and stock solid (an overlap is a FAIL). Each path is checked against the parts fitted at
  that screw's assembly step (frame → fan → duct → cover; the probe mount and stock parts are always
  there), and again with everything fitted (service, INFO). `--samples N` sets the number of wall-thickness rays.
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
  | STEP round trip | 1 solid, OCC-valid, closed, dV/V < 1e-6, bbox 1e-3 mm |
  | 3MF / STL | 1 object, dV/V < 5e-3, bbox 0.05 mm; STL watertight, consistent winding |
  | Assembly STEP | same named, coloured leaves and groups, per-leaf dV/V < 1e-6 |

  STEP headers carry a timestamp, so re-exports are identical in content but not byte for byte.

## Layout of `source/`

| File | Content |
|---|---|
| `interfaces.py` | shared interface values (owned by the lead; read-only here) |
| `structure/common.py` | parameter registry (`prm`), materials, inserts/screws, helpers, `PartSpec`, release rule |
| `structure/reference.py` | non-printed references: nozzle, heater, sock, heatsink, 3010, PCB (+ fan cutout from the K1C gerber, + Henlor "2nd plate"), extruder, belt retainers, rods, probe body/pin, keep-outs (component zone, LiDAR optical/body boxes, laser sheet), replaced stock parts |
| `structure/stock_cache.py` | Henlor solids → nozzle-frame STEP cache (validation only) |
| `structure/cooling.py` | cooling interface: adapter for `ducts/duct_interface.json` + `build_ducts()` (duct body, air path, duct dependencies), STUB fallback |
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
| cover | `PCB`, `XCARRIAGE`, `RIGHT_LIMIT_X`, LiDAR boxes, fan envelope | `COVER_HALF_W` 24.0 (stock width, DERIVED); `COVER_WALL` 1.2; `COVER_GAP` 0.5 (front wall to fan face); `COVER_INTAKE_MARGIN` 1.0 (intake aperture = `FAN_INLET_D` 28, ESTIMATED M7, + 2 = Ø30, fully open); `COVER_ZMIN` 24; `COVER_YIELD_CLEAR` 0.3 (right wall bottom raised to Z 26.4 over T_right); top wall stops in front of the strain relief (`CARRIAGE_STRAIN_RELIEF_YMIN`, DERIVED 02:N16) |
| probe mount | `PROBE_*`, `PROBE_BODY_Y`, `PROBE_ADAPTER_785004`, `PROBE_ADAPTER_SCREWS`, `REAR_LIMIT_Y`, `SOCK` | 785004 relations from 01 §H.1 (`PM_SEAT_TO_ANCHOR_Z` 27.05, `PM_SEAT_TO_TOP_Z` 32.5, `PM_MATING_FACE_Y` 16.9, `PM_FRONT_LOW_Y` 13.4, windows, Ø2.4/Ø4.2 anchor holes); carriage tabs from Henlor (`PM_TAB_*`); `PM_PAD_T` 4; `PM_WALL` 2.4; pocket 0.8 deep; M2.5 inserts; `PM_ANCHOR_CONFIRMED_M8` (MISSING) |
| coupon | same as frame bosses + probe flange | `COUPON_*` |
| duct body (Duct/CFD agent) | `SOCK`, `HEATER_BODY`, `HOT_ZONE_CLEARANCE`, `DUCT_MIN_Z`, `PROBE_BODY_Y`, `PROBE_ADAPTER_785004`, `PCB_COMPONENT_ZONE`, `STOCK_4020_POS`, `FAN3010`, LiDAR boxes | from `duct_interface.json`: `DUCT_FAN_F_OUTLET_SIZE`, `DUCT_FAN_F_SCREW_HOLES`, `DUCT_FAN_F_ENVELOPE` (ESTIMATED, M7), `DUCT_FAN_SOCKET_FIT`, `DUCT_HOTEND_VERSION` (M1), `DUCT_MOUNT_POINTS_FINAL`; `DUCT_TAB_SCREW_LEN` 6 |
| stub cooling (fallback) | `STOCK_4020_POS` (XZ centre), `BLOWER_4020_STOCK` | `STUB_*` (status STUB) |

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
   - It stays ≥ 6.35 mm from every PCB screw axis (Ø4.0 insert hole + 1.2 mm wall + head clearance r 3.15).
     The Ø8.5 boss is trimmed where a PCB screw's Ø6.3 driver path passes. Fan standoffs also stay 0.3 mm
     inside the cover's side walls.
   - Every insert hole is blind with a 0.8 mm floor (R-03): insert 4.0 + relief, shortened to fit the
     available boss length (4.2 mm deep in the 5.0 mm standoffs and lugs).
5. Run `validate.py --cooling ducts`, then switch the default when it passes.

## Design notes

- **Frame.**
  - 2.0 mm ASA plate directly in front of the PCB component zone, with front ribs open at Z 36…56 so the plenum between plate and fan is fed from the sides.
  - Teardrop window (assembly-down point), so it prints upside down without support, in front of the PCB fan cutout. The cutout was found in the K1C gerber: R 13.7 clipped at X ±12, ≈559 mm².
  - Bosses bear on the PCB around the three screws. A compression pad at the fourth corner backs the lower fan screw.
  - **Brass compression sleeves (R-04).** Each PCB boss carries an Albion Alloys BT4M brass tube
    (4.0 OD × 0.45 wall, ID 3.1; sold in 305 mm lengths, cut to 11.10 mm), in a Ø4.1 bore.
    - The sleeve is 0.1 mm shorter than the ASA stack from the PCB face to the head seat (11.2 mm).
      The head compresses the boss by 0.1 mm and then lands on the brass, so the preload runs metal → PCB → 3010.
    - The lower-left boss (screw into the heatsink) has a close-fit Ø4.05 bore. It locates the frame on
      the hotend through that screw (R-16); ream it to fit.
    - The neck through the PCB 2nd-plate holes keeps a 0.85 mm wall.
    - Clamp stiffness per screw: the 3010 corner pillar (ESTIMATED) is the soft link, as in the stock clamp.
      The member is 3.9 kN/mm with sleeves, against 1.6 kN/mm if the ASA carried the load.
    - Tag: ESTIMATED until bought.
  - **4th anchor evaluated, not added (R-04).** Option: the right stock cover-screw insert
    (X 22.6, Y −2.2, Z 35.35).
    - On the Henlor carriage nothing is in the way at X ≥ 24.2 from Y −28.9 to +1. A 1.6 mm tab at
      X 22.4…24.0 would sit where the stock cover wall sat and reuse the stock screw.
    - Not added, for four reasons:
      - its 29 mm arm along Y is an unsupported overhang in the frame's print orientation;
      - it needs a notch in the cover;
      - it would sit about 10.6 mm from the sock;
      - it adds only about +11 % pitch stiffness, and the sleeves already deal with ASA creep.
    - It could come back as a separate PC bracket if the 10-hour torque audit shows preload loss.
  - **R-17 (boss lower edge).** The PCB boss at Z 34.3 cannot reach Z ≥ 31.9:
    - with a 0.85 mm wall round the Ø4.1 bore, its lowest point would still be Z ≈ 31.4;
    - the hole position is fixed by the PCB (DERIVED);
    - its lower edge stays at Z 30.55, 13.7 mm from the sock, and the manifest note states this.
    - Rewording DD-07 to a distance-and-view-factor rule is a docs decision; the alternative is a PC frame.
  - The plate stays out of the LiDAR boxes (2.5 mm from `LIDAR_RESERVED_OPTICAL`, 4.0 mm from
    `LIDAR_RESERVED_BODY`). `frame.lidar_allow_regions()` would allow-list a PCB screw column if a
    box ever reached one; with the current boxes none does.
  - Heat-set inserts for every screw the frame takes (fan, duct, cover): service cycles, 45 °C chamber, no thread creep in ASA.
- **Frame and the S7 duct.** `validate.py` checks that the frame really provides the four
  interface points (two 4020 screws, T_left, T_right): open Ø4.0 insert hole, solid boss (Ø8.5,
  R-20), solid mating face at Y −36.5.
  - Plastic round a Ø5.0 knurl is 1.80 mm on every insert boss.
  - Exception: the upper-left fan boss, trimmed by a PCB driver path and the cover clearance, has
    1.35 mm on 18 % of its ring (INFO, justified). The frame stays 1.2 mm outside the duct air path and 13.7 mm from the sock
  (≥ `HOT_ZONE_CLEARANCE` 3). Where frame lugs and the duct body meet, the frame yields.
- **Cover.**
  - 1.2 mm ASA, ±24.0 wide (inside `RIGHT_LIMIT_X` 24.2 in the XY-joint band).
  - Two M3×6 screws from the top into the frame shelf. The top wall's underside bears on the shelf
    top: this is the only intended frame contact. Everywhere else the cover clears the frame by ≥ 0.3 mm.
  - Yields to the duct: the right wall's bottom edge is raised from Z 24.0 to 27.05 over its whole
    length. This clears the frame's T_right lug (Ø8.5, top Z 26.75) and the duct's tab by ≥ 0.3, and
    the cover still slides off forward.
  - Front wall 0.5 mm in front of the 4020 intake face, front at Y −58.2.
  - **Fan screw heads.** The two M3×24 ISO 7380 fan screws go in from the front. Their heads
    (Ø5.7 × 1.65) stand proud of the fan face into the front wall: they reach Y −58.15, against a
    wall from −58.2 to −57.0. The front wall therefore has Ø6.7 through-holes at (−18.65, 60.3) and
    (16.05, 25.6). The 0.5 mm radial clearance (R-15) covers the RSS of the tolerance stack, 0.4 mm.
    The lower hole is a U-notch at the wall's bottom edge.
    - The heads sit in the holes, 0.05 mm behind the front face, so the front limit is unchanged.
    - A 2.0 mm hex key, or a Ø6.3 driver, reaches both screws with the cover on. Use ISO 7380 only:
      an ISO 4762 head is 3.0 mm tall and would stand 1.3 mm proud of the cover (R-15).
    - Whether the 4020's holes are counterbored is unknown (M7) and is not assumed; a counterbore
      would only add clearance.
  - **4020 intake fully open.** A Ø30 round aperture (inlet ring `FAN_INLET_D` 28 + 2 × 1.0) sits
    centred on the intake at X −1.3, Z 43.4, with no grille and no ribs. A grille 0.5 mm in front of
    the impeller eye would throttle the blower, and the CFD fan model has no cover. `validate.py`
    measures the aperture on the solid: 707 mm² open, and the Ø28 inlet disc is 100 % open
    (616 mm²).
    - The inlet diameter is the 28 mm the cooling adapter always used. It is not in
      `interfaces.py` and was untagged before; it is now registered as ESTIMATED (M7).
    - The 4020's own frame stays behind the opening, so the impeller is no more exposed than on a
      bare fan.
  - Open at the bottom and rear, so it slides forward without unplugging the LiDAR, probe or fan, and without removing the duct.
  - Side and top vents over the plenum: 183 + 53 mm², unchanged; the bottom and rear are also open.
    The 3010 draws through the frame window, 693 mm², unchanged.
  - Left wall cut back out of the LiDAR boxes, through its full thickness: a partial cut left a
    0.7 mm sliver.
  - The left stock cover-screw insert is blocked by `LIDAR_RESERVED_BODY`. For the right one, see the
    frame's 4th-anchor note.
  - Cover-screw inserts: blind holes 6.0 mm deep (insert 4 + 2 mm relief, R-20) with a 0.8 mm floor.
    The M3×6 tip ends 1.2 mm above the floor.
- **Probe mount.**
  - Drop-in replacement for Printables 785004 on the same two carriage tabs.
  - The bores sit at the same offset from the anchor as in 785004, so the pin lands where it does today whatever the pin-to-hole offset is (1.0 in `interfaces.py`, 2.75 in the V1 STEP).
  - Stiffer than 785004: PA-CF, a closed box section, a flange locating pocket, and M2.5 inserts.
  - The load path cannot be shorter: the anchor height is set by the carriage.
  - Printed upside down, no supports.
- **Stiffness** (hand estimates, `structure/stiffness.py`; numbers in the report):
  - Frame rocking on the 3 screws is ≥ 1.27 kHz. The clamped stack is brass sleeve + PCB + 3010.
  - Duct cantilever (R-22): rigid-body pitch about the tab line, 113…598 Hz.
    - The upper bound counts the pads only; the lower bound adds the tab arms in torsion.
    - J = 8880 g·mm²; lever 64 mm.
    - It needs a third tab or stiffer arms (WARN).
  - The lower fan screw is the weak spot. With the fourth pad its local mode is in the kHz range. Without it (if M10 shows the pad cannot bear), the estimate falls to about 150 Hz, near 2 × the X shaper frequency.
  - Probe mount: sub-µm deflection. Thermal growth of the 27 mm printed path is about 11 µm per 10 K (PA-CF), against about 19 µm for a PLA/PETG 785004.

## BOM (per toolhead)

| Item | Qty | Note |
|---|---|---|
| M3×30 ISO 7380 | 3 | replace the stock PCB screws (M3×18 ×2 into carriage inserts, M3×20 into the heatsink) |
| M3 brass heat-set insert, short (hole Ø4.0, OD ≤ 5.0) | 6 | 2 fan, 2 duct (T_left, T_right), 2 cover; all in Ø8.5 bosses, blind holes with a 0.8 mm floor |
| Brass tube Albion Alloys BT4M, 4.0 × 0.45 (ID 3.1), 305 mm | 1 length | cut 3 × 11.10 mm compression sleeves for the PCB bosses (R-04); ESTIMATED until bought |
| M3×24 ISO 7380 | 2 | 4020 to frame: fan through-length 20 (ESTIMATED, M7) + 4 (`FRAME_FAN_SCREW_LEN`); heads in the cover's Ø6.7 holes. The tip ends 0.2 mm from the insert-hole floor; the safe length is 22.5…23.7. Decide after M7 (R-03) |
| M3 washer ISO 7089 | 3 | coupon only (restores the frame's 2.0 mm plate depth on the 1.6 mm coupon) |
| M3×6 ISO 7380 | 2 | duct tabs to frame lugs (tab 2.5 + 3.5 into the insert, `DUCT_TAB_SCREW_LEN`) |
| M3×6 ISO 7380 | 2 | cover |
| M2.5 brass heat-set insert (hole Ø3.6) | 2 | probe |
| M2.5×5 | 2 | probe (BIQU kit) |
| ~M2 screws | 2 | probe mount to carriage tabs: reuse 785004's |
| cable ties 2.5 mm | 3 | frame top corners, probe mount roof |
| stock 4020 blower | 1 | reused |

No 24→12 V buck or Same Sky 5015 hardware in the baseline (conditional upgrade only).
