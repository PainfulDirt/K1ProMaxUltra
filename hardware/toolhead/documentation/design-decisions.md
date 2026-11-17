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
7. **The fan curves.** After network access was opened, the Delta, Same Sky and Sunon curves were
   digitized from the manufacturer datasheets (research/03 §10). The stock Creality 4020 has no
   published curve, so it is bracketed by two bounds, 191 and 390 Pa shut-off (ESTIMATED). CFD with
   these curves ranks designs reliably. Absolute flow rates stay conditional until the 4020 is
   bench-measured (`cfd-report.md` §15, V1).

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

**Outcome (CFD campaign, all [RAN] on the L2 mesh).** The feed is **S: one stock 4020 with the S8
multi-port nozzle end** (`cfd-report.md` §0, §17). The first round (§8–§12) chose the feed with S7. The
Phase 6 review round (§17) replaced S7 by S8: S7 reached Y +27.5 behind the nozzle (R-01), had no bed
contact, a socket inside the fan model and an unclosed thermal balance. S8 keeps S7's fan pose, plenum
and manifold, ends the manifold at Y +8.6 and uses four 7.5 × 3 mm ports instead of five.

First round (S7, kept as the record of the fan decision; STOCK = the first STOCK run):

| Result at the conservative 4020 curve (191 Pa) | STOCK duct | S7, 1 × 4020 | D2, 2 × 4020 | S7 + Same Sky 5015 |
|---|---|---|---|---|
| Layer annulus speed, Z +0.3 [m/s] | 1.83 | 8.84 | 8.40 | 9.99 |
| Weakest of 8 sectors [m/s] | 0.35 | 6.28 | 3.51 | 5.61 |
| Δ moving mass vs stock, fan + duct only [g] | 0 | +6.1 | +33.0 | +14.2 (+3–6 g buck) |

The S7 thermal-proxy values of that round (part-top h, heater W) came from an unclosed energy balance
(review R-08). They are withdrawn and are not quoted here.

Review round (released S8; STOCK run again in the same round with the same settings; the spread over
the robustness checks of `cfd-report.md` §17.5 in brackets):

| Result at the conservative 4020 curve (191 Pa), 20 mm part | STOCK duct | **S8, 1 × 4020** | Ratio |
|---|---|---|---|
| Layer annulus speed, Z +0.3 [m/s] | 2.12 | **9.38** | ×4.4 (×4.3–5.3; ×4.2 at the upper bound) |
| Weakest of 8 sectors [m/s] | 0.36 | **5.51** | ×15 (×12–30: an order of magnitude) |
| Part top r ≤ 5, near-wall speed [m/s] | 1.68 | 7.53 | ×4.5 (×4.5–5.8) |
| Side faces −X / +X / −Y / +Y, near-wall speed [m/s] | 0.78 / 0.29 / 1.43 / 0.10 | 4.49 / 3.35 / 2.93 / 0.45 | ×5.8 / ×12 / ×2.0 / ×4.4 |
| Part-top h, r ≤ 5 (thermal proxy, balance closed to −0.5 % / −0.03 %) [W/m²K] | 40 | **134** | ×3.3 |
| Heat removed from the part, top + sides [W] | 10.4 | 20.9 | ×2.0 |
| Extra heater demand at 100 % fan [W] | — | +7.6 | nozzle +3.1, sock +4.5 at an ESTIMATED 150 °C sock |

Reading against the selection rule:
- The second fan (D) fails all three conditions (first round, on S7): −5 % layer speed, −44 % weakest
  sector, +24 % nozzle impingement, +27 g and a fan beside the nozzle. It is rejected.
- No fan swap earned a clear margin on S7 (first round):
  - Delta: −10 % as a minimum-spec unit, +10 % typical;
  - Same Sky: +13 % typical, inside its own tolerance and inside the ±20 % spread of the 4020's
    unknown curve.
- The 4020 stays. The Same Sky CBM-5015BF was meant as the conditional upgrade, but **it is not
  buildable in this architecture** (review R-13, `cfd-report.md` §17.8):
  - its 51.6 mm wide housing needs 51.6 + 1.0 mm stall margin + 2 × 1.7 mm cover wall and gap =
    56.0 mm inside the XY-joint band, where 55.2 mm is available (X −31.0 ESTIMATED … +24.2 hard);
  - no other pose helps.

  It would need an open-sided or asymmetric cover and an accepted 0 mm stall margin. S8SS was not run.

**Per-face criterion (added after review R-11, `cfd-report.md` §17.6).** The annulus and sector
metrics alone hid a face that S7 cooled less than stock. So, in addition to the rule above: at the
conservative fan bound, on the 20 mm part, each of the four side faces must have near-wall |U| (0.3 mm
off the top 3 mm of the face) **≥ STOCK's** at the same settings. A face counts as worse only if it
is below **0.8 × STOCK in two independent runs** (a mesh level, a turbulence model or a repeat),
because single-run face values scatter by about a factor of 2.
- **S7 fails it on −X** (the LiDAR side): 0.69 against STOCK's 0.79 m/s on L2, 0.49 on L3.
- **S8 passes it**: every face is above STOCK in every variant run; the lowest ratio is −Y ×2.0
  (×2.0–2.5 over the variants).
- D2 (−X 6.90, −Y 4.73 m/s) would have passed on faces and failed on the annulus and nozzle
  impingement as before.

The price of the gain: about +7.6 W heater demand at 100 % fan, about 13 % of the 60 W heater (the
sock share scales with the ESTIMATED 150 °C sock surface, M20). It is the reason `MPC_CALIBRATE` is
mandatory after fitting. The S7-era +6.2 / +6.8 W came from an unclosed balance and are withdrawn.

**Would reverse it.**
- The V1 bench test measures the 4020 at its lower bound **and** the V5/V6 test prints show
  insufficient cooling. That re-opens the fan choice (the Same Sky only with a different cover, see
  above), not two fans.
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
bracket are measured (M6).

Airflow and the LiDAR:
- Air movement does not disturb laser triangulation at a 25 mm stand-off (ESTIMATED). Air's
  dn/dT is about −1e-6 per K. A 20 K gradient across the 25 mm path bends the beam by about
  2e-5 rad, which moves the spot by about 0.3 µm. That is below the module's 1–2 µm repeatability.
- What matters is that **no part enters the sheet or the camera view**, and that the ducts **do not
  blow fumes or debris onto the windows**. CFD reports the velocity at the window region.

**CFD check [RAN]** (`cfd-report.md` §13.1, nozzle 3 mm above a bare bed, fan at 100 %, upper 4020
bound as the worst case):
- S8 gives 0.041 m/s mean at the laser line, less than STOCK's 0.18: it has no port on the left, and
  its swirl turns the front-left jet back toward the part. At the window region S8 gives 0.17 m/s mean
  (0.34 max) against STOCK's 0.087 (0.18). S7 gave 0.87 / 0.17 m/s (first round, superseded).
- At the window height the air moves downward, toward the jets. That is **no evidence of transport
  toward the windows in this model**, not a demonstration that fumes stay away: the model is
  isothermal (no hot plume, no buoyancy) and has no module body (review R-21). V7 is the evidence.
- No duct part enters `LIDAR_RESERVED` or the laser sheet. The tightest duct clearance is 1.41 mm to
  the ESTIMATED optical box (validation report).

**Operating rule (proposed, not applied):** run LiDAR scans with the part fan off. The repo's macros do
not guarantee this in every path:
- `_LIDAR_PRINT_SCAN` (`tuning.cfg`) runs `FIRST_LAYER_SCAN` at the layer-2 change, when the slicer
  may already have switched the fan on;
- the PA and cross test prints in `custom/lidar.py` set the fan themselves (`M106 S0` / `S128`).

Whether the air at the laser line affects the readings at all is unknown: the 0 % fan case was not
simulated, and air movement itself is not expected to bend the beam (above). V7 (`cfd-report.md` §15)
checks it on the printer. Adding `M106 S0` before the scan is a config change, so it is left to the
user (`calibration.md`).

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

Before D can be released, confirm with the PB6 probing procedure in `electrical.md` that the
channel's power switch can carry the summed fan current. Today it is proven only to 0.3 A.

How the add-ons are allowed (revised after the electrical review):
- **2-wire 24 V fans** (Delta BFB0524HH, the owned Sunon) get speed control from a low-side MOSFET
  add-on driven by the PWM signal.
- **4-wire fans** (stock 4020, Same Sky CBM-5015BF) are **never** put behind a low-side switch.
  With the ground switched, current can leak through their PWM and tach wires. They keep PB6/PB8
  as on the stock board. The Same Sky also needs a 24→12 V buck and `cycle_time: 0.002`.

The original wording ("a MOSFET module switched by PB6" for any fan) is withdrawn.

MPC `fan_ambient_transfer` must be re-measured after any duct or fan change.

**Outcome.** CFD chose one stock 4020 (DD-01), so the baseline needs no add-on and no channel change:
stock PB8/PB6/PB3, 0.3 A. `electrical.md` §2 records the buck design for the Same Sky, which is not buildable in this architecture (R-13, `cfd-report.md` §17.8).
The MOSFET add-on for 2-wire fans is rejected: it survives as a short note in `electrical.md` §6 and in
the git history. The text above about feed D and the add-ons is kept as the record of the decision.

## DD-06: CFD method

The full write-up is research/04. In short:
- steady incompressible RANS with k-ω SST;
- fans as P–Q curve inlets (`fanPressure`);
- a nozzle environment of nozzle, sock, heatsink, a 20 mm printed-part proxy whose top is 0.2 mm
  under the tip, and the bed;
- production mesh level L2. On the released S8, L2 → L3 moves the annulus by −10 %, the weakest sector
  by −21 % and the part top by −3 %, and the S8/STOCK ratios by −3 %, −20 % and +4 %; per-face values
  move by −11 … +19 % (`cfd-report.md` §17.5, §17.6). The means are converged within the scatter
  band, the weakest sector is not.
- run-to-run scatter: re-meshing the same geometry moves single-run means by about ±8–10 %, the
  weakest sector by ±20–30 % and a single side face by a factor of about 2 (STOCK repeat +16 %,
  §17.3). Headline ratios are therefore quoted with the spread over a set of robustness checks
  (laminar, L3, plate, probe body, skewed inlet, long averaging; §17.5).

Results rank designs; absolute velocities carry about ±20–30 % uncertainty plus the fan-curve
uncertainty. Airflow is not cooling: the finalists get a heat-transfer proxy run, labelled as such.
Since the review round, h and W are quoted only from proxy runs whose energy balance closes to ≤ 5 %
(S8 −0.03 %, STOCK −0.5 %; `cfd-report.md` §17.7).

## DD-07: Materials

Revised after the Phase 6 review (R-07, R-17, R-27). The first version used a 15 mm distance rule
and a community anecdote. It is replaced by a rule based on what a part sees and on the
filament's heat-deflection temperature (HDT, ISO 75 at 0.45 MPa, from the spool's TDS).

| Parts | Requirement | Reason |
|---|---|---|
| **Duct body:** the whole part. In S8 its port lips are 4.54 mm from the sock and the manifold wall 7.8 mm, across still air, and the fan is often at 0–30 % for ABS/ASA | **HDT ≥ 130 °C at 0.45 MPa**: pure PC, or annealed PA-CF. A PC blend qualifies only if its own TDS meets the HDT. ASA does not | The review's 1-D estimate (REVIEWER-ESTIMATE, fan off, chamber 45 °C) puts the inner manifold wall at about 99 / 121 / 143 / 157 °C for a sock surface of 120 / 150 / 180 / 200 °C. The sock temperature is MISSING (M20). PC blends are typically around 110–120 °C HDT and pure PC about 135–140 °C (ESTIMATED; check the spool) |
| Parts that see the sock or block directly within about 15 mm, below the heatsink bottom (Z < +31.9) | PC or PA-CF | radiation and the convective plume from the heater |
| Parts at heatsink level or above, or that see the sock only edge-on through the heatsink and the 3010 intake stream. For example, the frame's PCB bosses: lower edge at Z 30.55, 13.7 mm from the sock | ASA is acceptable | the review estimates about 55–65 °C in operation (REVIEWER-ESTIMATE). That is below ASA's Tg of about 100 °C with margin |
| Cover, frame, everything else | ASA or ABS | Tg about 100 °C; the chamber runs at 45 °C during ABS prints |
| **Anywhere on the toolhead** | **no PLA or PETG** | Today's 785004 probe adapter (material unknown, possibly PLA/PETG) sits 5.1 mm from the sock box. Reprint the same, unchanged STL in PC or PA-CF (it is below the heatsink and within 15 mm of the sock, row 2) before or with this build (review R-27). Its geometry, and so the probe calibration, does not change |

What decides it physically: test V8 (`validation.md` §4). Thermocouples on the sock bottom and on the
manifold's inner face, nozzle at 300 °C, chamber 45 °C, fan 0 %, at least 4 h. Measure the lip Z
before and after. Pass: the inner face stays at least 15 K below the filament's HDT, and lip Z changes
by less than 0.1 mm.

Fallbacks if V8 fails:
- the duct revision's larger manifold-to-sock clearance;
- aluminium tape on the manifold's inner face, as a radiation shield;
- annealed PA-CF.

### DD-07a: Duct body from a print service (HT resin or MJF PA12)

The user asked (2026-11-12) to have the duct printed in a high-temperature resin. **This is
accepted for the duct body only**, under the same rule as above: HDT ≥ 130 °C at 0.45 MPa **in the
post-cure state the service actually delivers**, checked against the TDS. The geometry does not
change, and V8 applies unchanged with the resin's HDT.

Datasheet values below are vendor TDS figures as quoted by search results on 2026-11-12. The vendor
PDFs could not be opened from this environment, so treat them as ESTIMATED and re-check the
TDS of the exact material the service names before ordering.

| Option | HDT at 0.45 MPa | Elongation at break | Fits DD-07? | Main risk for this part |
|---|---|---|---|---|
| Formlabs High Temp Resin, full post-cure (UV + thermal) | 238 °C | about 2 % (2.3 %), notched Izod about 17–18 J/m | yes, with a large margin | brittle |
| Weerg "High Temp Pro" resin (Italian service, its own TDS) | 238 °C | 2.4 % | yes | brittle |
| Arkema N3D-HT511 | 130 °C at 0.455 MPa | 7 % | borderline, no V8 margin | marginal HDT |
| JLC3DP "JLC Temp Resin" | 101 °C (test load not stated) | — | **no** | fails the HDT rule |
| Generic "high temp" / "HT" hobby resins | varies widely | — | only with a TDS showing ≥ 130 °C at 0.45 MPa | the name alone means nothing |
| **MJF PA12** (HP 3D HR PA 12; JLC3DP, Weerg, Protolabs, Craftcloud …) | 175 °C (ASTM D648) | 15 % Z / 20 % XY | yes | smaller HDT margin than HT resin; porous, rough surface |

Thermal margin: the review's inner-wall estimate goes up to about 157 °C at a 200 °C sock
(REVIEWER-ESTIMATE; sock temperature M20 MISSING). V8 passes when the wall stays at least 15 K below
HDT. That leaves 66 K of margin for a 238 °C resin, 3 K for PA12, and none for a 130 °C resin. So
**HT resin has the best thermal margin of any option in this project**, PC included (HDT about 135–140 °C).

What the resin choice changes. These are conditions, not optional advice:

1. **Brittleness.** At about 2 % elongation the part cracks rather than bends.
   - The three M3 tabs (T_left, T_right, T_3) clamp resin directly. Put an M3 washer under each
     head, and tighten only until the tab seats: a brittle tab cracks from over-torque, it does
     not creep.
   - S8's flat base and port lips sit 3.0 mm above the nozzle tip (`duct_interface.json` v4). A
     curled-up print, or a nozzle crash, chips a resin lip; PC or PA12 would bend. Keep a
     **spare duct**: order two.
   - The fan socket is a 0.25 mm clearance fit, not a press fit, so it does not load the resin.
     Do not glue or force the fan into it.
2. **Internal channels.** The plenum, manifold and ports are enclosed. They are open at both ends
   (fan socket and port outlets), so resin can drain and they can be washed.
   - Ask the service to flush every port with solvent until clean. Uncured resin left in a channel
     stays soft, lowers the HDT locally and can drip onto the nozzle.
   - Ask for the **full thermal post-cure** listed in the TDS. UV does not reach the inside of the
     channels, and the HDT above is only valid after the full cure.
3. **Supports.** Orientation is the service's choice. State in the order: **no support contact points
   on the outlet lips, inside the ports or on the socket faces.** The outlets set the CFD result;
   support stubs left inside a port change it.
4. **Inspect on delivery.** Check every outlet is fully open, as `print-settings.md` "Duct supports
   and checks" describes. Check the tabs for cracks. Check the lip height with the duct sitting on a
   flat surface.
5. **Mass.** It is close to the PC part, but take the density from the TDS and re-run `export.py`
   for the exact value.

**Not** covered by this: the frame, cover and probe mount. They take heat-set inserts, and a
thermoset resin does not soften for inserts. They stay as in the table above.

**Decision (user, 2026-11-12): the duct body is HT resin**, 238 °C class (HDT at 0.45 MPa per the
TDS, after the full thermal post-cure), ordered from a print service, two pieces. PC and MJF PA12
stay as fallbacks. The conditions above apply.

**Lead's recommendation (before the decision).**
- HT resin (238 °C class, full post-cure) is acceptable and gives the most heat margin. It is the
  better choice if V8 or M20 shows a hot sock.
- MJF PA12 is the more robust choice against crashes and over-torque, but its heat margin over the
  157 °C estimate is small.
- Either way, the user's V8 soak decides.

Sources:
- [Formlabs High Temp Resin](https://formlabs.com/store/materials/high-temp-resin/)
- [Weerg High Temp Pro TDS](https://weerg.com/hubfs/Datasheets/Datasheets%202024/ENG/EN_ResinaAltetemperaturepro.pdf)
- [Arkema N3D-HT511 TDS](https://sartomer.arkema.com/files/live/sites/shared_arkema/files/downloads/sartomer/N3XTDIMENSION%20TECH%20DATA%20SHEETS/TDS_N3D-HT511.pdf)
- [JLC Temp Resin](https://jlc3dp.com/help/article/jlc-temp-resin)
- [HP PA 12 data sheet (Sculpteo copy)](https://www.sculpteo.com/media/imagecontent/HP%20Strong%20and%20Flexible%20Data%20Sheet.pdf)
- [Weerg PA12 TDS](https://weerg.com/hubfs/Datasheets/Datasheets%202024/ENG/EN_NylonPA12.pdf)
