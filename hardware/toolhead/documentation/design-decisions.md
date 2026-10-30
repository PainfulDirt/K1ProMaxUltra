# Design decisions

Every decision lists what it rests on and what would reverse it. Values are tagged as in
`cad/source/interfaces.py`: VERIFIED, DERIVED, ESTIMATED, MISSING. Research inputs are in
`documentation/research/01..04`.

Coordinate system for everything in this project: origin at the nozzle tip, +X printer right,
+Y toward the printer rear, +Z up, mm.

## Phase 1 findings that drive the architecture

1. **The printer's value is in its calibrations.** The probe offset (0, +20.3), z_offset, keep-out
   zones, twist tables, the LiDAR offsets and per-Z slopes, the nozzle-wipe strip and the mesh
   reach all come from the current sensor positions (research/01 §E). Moving a sensor costs a
   full recalibration and edits to hard-coded values in `custom/lidar.py`.
2. **The LiDAR sits on the left and its geometry is narrow.** The laser line runs X −50.8…−21.6 at
   Y −21.3 when the nozzle is 3 mm up. The sheet rises toward +Y at about 45°. The module only
   reads with the nozzle 3–5 mm above the surface, so its height relative to the nozzle has a
   budget of about ±1–2 mm. Software handles the X/Y offsets, the per-Z slopes and the profile
   tilt. It cannot handle yaw: the line must stay parallel to X.
3. **The X-beam twist punishes sensor offsets in Y.** The sensor-minus-nozzle error across X is
   0.267 mm for the probe at Y +20.3 and 0.181 mm for the LiDAR at Y −21.3. It was 0.070 mm for the
   old probe at X −33, Y 0 (MEASURED-BY-USER, research/01 §B.6). The errors are compensated along
   X at one Y.
4. **Two fan channels on the toolhead board, both 24 V.** The part-fan channel is designed for a
   4-wire PWM fan (PB8 PWM, PB6 power switch, PB3 tach). The hotend channel is PB5 with tach PB4.
   Kalico's MPC models one part fan, and that fan raises the block's heat loss by 46 % at 100 %.
5. **Mass sensitivity.** The X moving mass is about 450 g (ESTIMATED, range 400–500). Every +9 g on
   the toolhead costs about 1 % of the X shaper frequency and about 2 % of usable X acceleration.
6. **There is no official CAD.** The hotend, heatsink, PCB and extruder are DERIVED from community
   CAD; the PCB hole pattern is confirmed by a second, independent gerber. The carriage, the LiDAR
   module, the stock cover and the travel-limit clearances are MISSING (`missing-information.md`).
7. **The fan curves are ESTIMATED.** The manufacturer sites are blocked in this session (research/03).
   CFD with these curves ranks designs reliably. Absolute flow rates stay conditional until the
   curves are verified.

## Architecture comparison

All masses are ESTIMATED changes relative to stock (research/02 §6). The X shaper frequency
starts at 77.6 Hz.

| | **A: stock-referenced, re-ducted** | **B: dual part fans** | **C: full custom** |
|---|---|---|---|
| Structure | keep carriage, hotend, extruder, PCB, 3010; new shroud and ducts | as A plus a second blower and duct | new carrier for hotend and sensors, ring duct, remote CPAP blower |
| Part cooling | 1 × stock 4020 (high pressure) with an engineered multi-outlet duct | 2 blowers, independent channels | CPAP via hose, about 8 CFM at high pressure, 360° ring |
| Δ mass | −5 … +18 g | +20 … +66 g, depending on fans | −28 … +27 g, plus hose drag (unquantified) |
| X shaper | ≥ 76 Hz | 72.5 … 75.5 Hz | similar, but the hose adds damping and force that changes with position |
| Envelope | stock-like | +15 … +25 mm per side; a symmetric left fan collides with the LiDAR | ring needs 15–20 mm radius; inclined laser sheet crosses the front-left quadrant |
| Sensors | unchanged, no recalibration | unchanged if the left side stays clear of the LiDAR | everything moves: full recalibration, and `lidar.py` limits edited |
| Electrical | as stock | the 2nd fan shares channel 1: confirm current or add a MOSFET | external 24 V brushless driver |
| Service | cover off without unplugging the LiDAR | more parts | ring ducts block nozzle access |
| Risk | lowest | medium | highest; also the MISSING carriage data |

The mechanical agent ranked A > B′ > C. The fan agent recommended dual blowers. Both concerns are
valid, and they pull in different directions.

## DD-01: Architecture "A+" with the cooling feed decided by CFD

**Decision.**
- Keep the stock carriage, hotend, extruder, nozzle PCB, 3010 hotend fan and both sensor positions.
- Replace the front cover with a new **cooling module** (fan holder(s) plus ducts) and a light
  **cover**.
- Both mount on the PCB's three-hole pattern, which is referenced to the heatsink. The duct
  outlets are therefore located from the hotend itself, not from a loose shell.

The number of part fans is not decided on paper. CFD compares, on the same nozzle environment:

| Feed | Fan(s) |
|---|---|
| reference concept | 1 × 4020, single front jet |
| S | 1 × 4020, multi-outlet duct |
| D | 2 × 4020, independent outlets |
| U | 1 × Sunon 5015 (owned) |

The selection rule:
- The second fan must earn its estimated +20 g by a clear margin in the CFD metrics: velocity
  delivered to the layer around the nozzle, symmetry, and minimum sector.
- It must not add nozzle impingement.
- It must fit outside the LiDAR reserved zone without costing travel.

**Upgrade path.** The duct is split into a **nozzle end** (outlets, optimized by CFD) and a
**feed transition** (fan outlet to nozzle end). A later CPAP or remote-blower feed (Architecture
C's cooling) replaces only the feed transition, not the structure.

**Why not B or C now.**
- B's symmetric form is blocked by the LiDAR, and its asymmetric form costs mass and possibly X
  travel. It is evaluated as feed D inside A+ rather than as a separate structure.
- C throws away the calibrated sensor geometry and needs carriage data we do not have. Its cooling
  advantage stays available through the upgrade path.

**Would reverse it.**
- CFD shows that no front-bay layout clears the LiDAR zone.
- Or the user decides on an X-rail rebuild, which makes C's recalibration cost worth paying.

## DD-02: LiDAR pose stays unchanged

The module, its bracket and its optical pose are not modified in this revision. The new parts keep
out of `LIDAR_RESERVED` and the laser sheet.

Rationale:
- The line is repeatable to 1–2 µm.
- Moving it requires re-running `LIDAR_OFFSET_CALIBRATION` with a temporary edit, because that
  macro refuses changes over 5 mm.
- It also requires editing hard-coded reach values in `custom/lidar.py` and re-running the twist
  calibration.
- Creality's sticker calibration must **not** be re-run with the glass plate fitted.
- Nothing in the cooling design needs the left side, so the cost would buy nothing.

A stiffer and thermally isolated LiDAR bracket is a later candidate, once the module and the stock
bracket are measured (M7).

Airflow and the LiDAR:
- Air movement does not disturb laser triangulation at a 25 mm stand-off (ESTIMATED). Air's
  dn/dT is about −1e-6 per K. A 20 K gradient across the 25 mm path bends the beam by about
  2e-5 rad, which moves the spot by about 0.3 µm. That is below the module's 1–2 µm repeatability.
- What matters is that **no part enters the sheet or the camera view**, and that the ducts **do not
  blow fumes or debris onto the windows**. CFD reports the velocity at the window region.

## DD-03: MicroProbe stays at (0, +20.3); the mount gets stiffer and is referenced to metal

**Alternatives considered:**

| Option | For | Against |
|---|---|---|
| X offset at Y 0 (old position) | about 4× less twist error | loses mesh reach equal to the offset; the user moved the probe on 2026-10-06 specifically to get full-width meshes |
| Closer behind, e.g. Y +15 | about 5 mm less rear keep-out loss and 25 % less twist error | the body would sit about 7 mm from the sock, against a 60 °C ambient rating |

The twist is already compensated (`AXIS_TWIST_TOUCH_CALIBRATE`), so neither gain justifies a full
recalibration.

**Decision:** keep the position, and keep z_offset within the ±1 mm range the existing calibration
flow re-measures anyway. The new probe mount is a separate part bolted to the heatsink/carriage,
not to the duct or cover. Its interface stays **MISSING** until the carriage is measured (M2, M8):
it is designed parametrically but not released for printing.

## DD-04: Keep the stock 3010 hotend fan (fan agent's recommendation not adopted)

The fan agent proposed the owned Sunon MF40202VX (40 × 40 × 20 axial) as the hotend fan. Not adopted:
- It weighs about 29 g against about 7 g for the 3010, which is about +22 g, or about −2.5 % on the
  X shaper.
- It does not fit the 24 mm pattern that the PCB, the 3010 and the heatsink share.
- Nothing in the repo (README known limitations, configs, macros) points to heat creep or works
  around it. That is an absence of evidence, not a measurement.

The design keeps the hotend-fan inlet path open through the cover and keeps its exhaust away from
the print.

**Would reverse it:** heatsink temperature data showing heat creep with ABS at a 45 °C chamber.

## DD-05: One logical part fan

Kalico MPC models a single part fan, and the board has a single part-fan channel. If feed D wins,
both blowers share the PB8 PWM signal (4-wire PWM inputs are high impedance and can be paralleled).

Before D can be released, one of these must be done:
- confirm that the channel's PB6 power switch is good for 0.6 A, or
- power both fans from a small MOSFET module on the toolhead 24 V rail, switched by PB6.

MPC `fan_ambient_transfer` must be re-measured after any duct or fan change.

## DD-06: CFD method

The full write-up is research/04. In short:
- steady incompressible RANS with k-ω SST;
- fans as P–Q curve inlets (`fanPressure`);
- a nozzle environment of nozzle, sock, heatsink, a 20 mm printed-part proxy whose top is 0.2 mm
  under the tip, and the bed;
- production mesh level L2 (mesh-independent to about 1.5 % on averaged metrics).

Results rank designs; absolute velocities carry about ±20–30 % uncertainty plus the fan-curve
uncertainty. Airflow is not cooling: the finalists get a heat-transfer proxy run, labelled as such.

## DD-07: Materials

| Parts | Material | Reason |
|---|---|---|
| Within 15 mm of the heater (duct lips, nozzle end) | PC or PA-CF | ASA's Tg of about 100 °C is too close to the radiant and convective load at the sock. Community covers warped at the outlets with the fan off at 260 °C. |
| Everything else | ASA, or ABS | Tg about 100 °C; the chamber runs at 45 °C during ABS prints |
| Anywhere | no PLA or PETG | |

Exact limits come from the chosen filament's datasheet.
