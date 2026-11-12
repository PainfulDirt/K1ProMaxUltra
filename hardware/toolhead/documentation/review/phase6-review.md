# Phase 6: independent engineering review of the A+ toolhead (S7 duct, frame, cover)

Reviewer: independent (did not design this). Date: 2026-11-12. Branch `claude/zen-lovelace-twtjt2`
against `main` (merge base `421aee1`).

Tags used for the reviewer's own numbers, so they are not confused with the project's:
- **REVIEWER-GEOMETRY**: measured by me on the committed STEP exports or the `assembly.py` build with
  build123d, using scripts outside the repo;
- **REVIEWER-ESTIMATE**: my hand calculation with stated assumptions;
- **REVIEWER-RAN**: I ran it in this session.

Nothing in this review was printed, fitted or measured on the printer.

## Summary verdict

**Not ready to fit. Print only the fit-check coupon.** This is a well-documented, honest project
and its arithmetic checks out. Its main simulation numbers match the raw result files. The
toolchain reproduces: I re-ran `validate.py` and got 0 FAIL / 4 WARN, identical to the committed
report. But the review found:

1. **One CRITICAL issue (R-01).** The duct's rear-right arm extends behind and to the right of
   the probe, at Z 3.3–18 above the tip. The rear keep-out zones were never measured for that
   space. The validator's rear check ignores X, and the calibration procedure explicitly skips the
   rear keep-out jog for this build. Within currently allowed travel, the duct can plausibly strike
   the Z-rod housings at the middle-rear and right-rear.
2. **Fan, socket and screw interface (R-02, R-03).** This interface does not hold together:
   - the modelled lower-right fan screw passes through the modelled fan outlet;
   - the duct's T_right arm intersects that screw's shank;
   - the stock fixing (M3×18) implies tapping holes, not 20 mm clearance holes;
   - the fan insert holes open into the PCB component zone, while three documents say an
     over-long screw "bottoms out".

   All of this passes validation only because duct–fan overlap is allow-listed without a limit and
   screw shanks are not checked.
3. **Thermal and materials claims (R-07, R-08).** These are not supported at the level the
   documents state:
   - nothing estimates the fan-off soak of a PC wall 3.35 mm from a sock of unknown temperature;
   - the S7 thermal proxy's energy balance is off by about 50 %, and differently in each case,
     which undermines the ×3.5 h, the +6.2 W and the "Same Sky +21 % h" numbers.
4. **The fan/duct decision (one stock 4020 + S7) is reasonable.** It is the right engineering
   direction and is not overturned. But the headline ×4.8 has never been tested against a
   turbulence-model change (the method's own laminar bracketing check), a STOCK mesh check, a
   larger part proxy, or the missing probe body. On the part's left face, S7 is **worse** than
   stock (R-09 to R-11). Before the first ABS/PETG print, the slicer fan percentages need a retune
   plan (R-12).

The repository rules are respected:
- only `README.md` at the root changed (+4 lines);
- no printer configuration was touched;
- no stock geometry was taken from screenshots.

The exceptions are tagging and single-source discipline in `interfaces.py` and the duct generator
(R-19), and a PLA/PETG part that stays 5 mm from the heater (R-27).

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| MAJOR | 12 |
| MINOR | 12 |
| NOTE | 4 |

## Findings

### R-01 — CRITICAL — The duct's rear-right arm can hit the Z-rod housings inside the allowed travel

**Evidence**

The duct body (REVIEWER-GEOMETRY, `cad/exports/step/duct_body.step` placed in the nozzle frame):

| Slice | X | Z |
|---|---|---|
| behind Y +20 | 12.3…28.5 | 3.3…18.1 |
| behind Y +25 | 12.3…23.4 | 3.3…14.9 |

Its maximum Y is +27.5.

The rear keep-outs (`tuning.cfg:886-902`) were measured with the MicroProbe as the rearmost body
(X ±11, Y to 28.1; `interfaces.py:137`), with ~3 mm left at the housings:
- "Y293 at X150" (middle);
- "Y302 at X286" and "Y287 at X306.5" (right).

The duct now occupies space 1–17 mm to the right of the probe body at almost the same Y, and at
probe-body height.

**What the checks do**
- `validate.py:570-576` tests only "volume behind Y 31 below Z 30". It is blind to X, so the arm
  passes.
- `calibration.md:128` runs the rear keep-out jog "only if a part behind the nozzle changed (new
  probe mount, or anything past Y +29.1)", so for this build the jog is **skipped**.

**Example interferences** (REVIEWER-ESTIMATE). These assume the housing faces sit about 3 mm
behind the probe positions measured in `tuning.cfg`. The housing shapes between the measured
points are unknown.

| Nozzle position | Allowed today? | Duct reaches (absolute) | Housing face | Overlap |
|---|---|---|---|---|
| X 107–130, Y ≥ ~297 | yes: zone1 starts at X 130 | X 119–158, Y ~324+ | middle housing, Y ≈ 324 (probe stopped at Y 293 + 28.1 + 3) | up to several mm |
| (285, 301.9) | yes | X 297–313, Y 326–329 | right-corner housing, Y ≈ 318 at absolute X 295–318 (probe stopped at Y 287) | up to about 10 mm |

**Why it matters**
- It is a collision during normal travel near the back edge. Printable area there is allowed.
- The struck part is a PC duct whose inner face is 3.35 mm from the hot sock. A hit can push the
  manifold onto the sock, break the duct or frame lugs, or skip steps.

**Fix**
1. Before any print, make step D.4 mandatory for this build. Jog at Z 0.2–5 with the duct fitted:
   - at the four points listed in D.4;
   - along the right side at X 266…306.5 at the zone3/zone4 borders;
   - at X 105…130 near Y max, next to zone1.
2. Extend the rear check in `validate.py`. Compare the full XY footprint of every part behind
   Y ≈ +10 (below Z 30) against the footprint the zones were measured with (probe body and 785004),
   and FAIL on any excess.
3. Then either:
   - re-measure zones 1, 3 and 4 with the duct fitted (a `[keep_out]` and Orca bed-shape change for
     the user to approve); or
   - trim the rear-right manifold end and the 35° port root to X ≤ 11 behind Y +12.

---

### R-02 — MAJOR — The fan, socket and duct interface is self-contradictory, and a validator allow-list hides it

**Evidence** (REVIEWER-GEOMETRY unless noted)

1. The lower-right fan hole goes through the modelled outlet:
   - fan outlet: centre (12.2, −46.5, 23.4), 13 × 17 (`duct_interface.json`), so X 5.7–18.7 and
     Y −55…−38;
   - lower-right fan hole at (X 16.05, Z 25.6), Ø3.4, along Y over 20 mm;
   - 154 mm³ of that hole cylinder lies inside the outlet column (Z 23.4–27.4).

   A real blower cannot have a mounting bore through its discharge channel. Either the hole
   positions (DERIVED from Henlor's *generic* fan, research/02 C7) or the outlet (ESTIMATED, C8,
   "low confidence") are wrong.
2. The duct socket is two plates:
   - X 3.5–4.7 and X 19.7–20.9, full fan depth Y −56.5…−36.5, Z 23.4–27.4;
   - the left plate is *inside* the 40 × 40 fan envelope;
   - duct ∩ fan envelope = 105.5 mm³, at X 3.5…18.7, Z 23.4…27.4 (`validate.py` reports 105.35).
3. The Ø3.0 shank of the lower fan screw intersects the duct body by **2.44 mm³**, at X 16.5–17.55,
   Y −39.0…−36.5, Z 24.2–25.5. That region is the arm from the socket to T_right.
4. Two validator rules let all this pass:
   - `validate.py:61` allow-lists `duct_body × ref_blower_` as kind "overlap" with no volume or
     region limit, so any duct–fan collision passes (`[PASS] interference duct_body x
     ref_blower_1… overlap 105.350 mm3`);
   - `validate.py:206-235` models only screw heads and driver paths, never shanks or tips.
5. The CFD body (`duct_generator.py` docstring, "body_cfd: no sockets/tabs") assumes a sealed inlet
   on the envelope's bottom face. The printed part assumes a 4 mm outlet nozzle that protrudes with
   1 mm clearance. These are two different fan geometries.

**Why it matters**
- Exactly where the frame, duct and fan meet, the design depends on a fan model that cannot be
  physically right.
- Once M7 is measured, the duct inlet, socket, T_right arm and possibly the plenum position will
  move. The CFD inlet may move too.
- The validator reports this region as clean.

**Fix**
1. Treat M7 as priority 1: outlet position and shape, whether a nozzle protrudes and its outer
   size, hole positions, and whether the holes are through-holes.
2. Model the 4020 as a real solid (body plus outlet nozzle) instead of a box.
3. Replace the unlimited "overlap" allowance with an explicit socket region and a small volume
   cap.
4. Add shank and tip cylinders for every screw to the interference pass.
5. Re-run one CFD case with the corrected inlet.

---

### R-03 — MAJOR — Fan screw holes: the stock evidence contradicts through-bolting, and an over-long screw goes into the PCB zone, not "bottoms out"

**Evidence**

The stock 4020 is fixed by **3 × M3×18** along Y from the stock cover (research/02:431, C7):
- the cover front is at Y −55 and the fan front at −49.4;
- so at most about 12.4 mm of an M3×18 can sit in the 19.2 mm thick fan;
- for that to hold, the fan's holes must be tapping holes that grip the screw, not Ø3.4 clearance
  holes.

The design assumes Ø3.4 through-holes, 20 mm long (`interfaces.py:191` `hole_d=3.4`, untagged;
`duct_interface.json` `through_length: 20.0`), with M3×24 into frame inserts.

The frame's fan insert hole is a **through-hole** into the PCB component zone:
- depth = insert 4 + 1 (`frame.py:206-208`), from Y −36.5 to −31.5;
- −31.5 is the plate's back face, `BACK_Y = PCB_COMPONENT_ZONE.ymin` (`frame.py:41`);
- REVIEWER-GEOMETRY: no material on either fan-screw axis from Y −36.4 to −30.0.

Three documents say the opposite:
- `bill-of-materials.md:53`: "M3×25 would bottom out exactly at 5.0", and "M3×24 would bottom out";
- `maintenance.md:97-98`: "A longer screw bottoms out in the 5.0 mm insert hole";
- `assembly.md:130`: "If a screw goes tight before the fan is seated, it is too long".

**Why it matters**
- A screw 1 mm too long enters the component zone.
- About 2.6 mm further it meets the PCB "2nd plate" or components.
- With a through-hole, "goes tight" happens only when the tip is already pressing on the nozzle
  board. The documented check would therefore damage the board instead of preventing damage.
- Drilling the fitted stock fan's holes to 3.4 mm to through-bolt it also destroys its stock
  M3×18 grip, which breaks the rollback with the same fan.

**Fix**
1. Close the insert hole with a ≥ 0.8 mm floor (blind hole), or add a hard stop.
2. Add a fan-screw tip check to `validate.py`.
3. Correct the three documents.
4. Decide the fastening after M7. If the holes are tapping holes:
   - through-drill a *spare* 4020 and keep the fitted one intact for rollback; or
   - change the joint, for example frame ears or straps that clamp the fan, or thread-forming
     screws into the fan from the front with the standoffs used only as stops.

---

### R-04 — MAJOR — The PCB screw clamp stack is now mostly polymer and carries the whole new cantilever

**Evidence**
- The three M3×30 screws now clamp, in series:
  - ASA boss and plate: 11.2 mm (`frame.py:72-73`, `STOCK_GRIP_ADD` 9.2 + `T` 2.0);
  - the PCB;
  - the 3010's plastic frame (10.4 mm);
  - then the carriage inserts or the heatsink (`assembly.md` step 4: "the same screws hold the
    PCB and the 3010").
- The frame carries the 4020 (24 g), the duct (9.2 g), the cover (6.4 g) and itself (5.8 g):
  about 45 g whose CoM sits about 25 mm in front of the PCB face (REVIEWER-ESTIMATE from part
  masses and CoMs).
- In the stock design the cover and the 4020 hung on the cover's two side screws into carriage
  inserts (research/02 C5).
- `stiffness.py:40-47` counts only ASA in the member stiffness. The PCB and the 3010 housing are not
  in series in the model.
- `maintenance.md:143` already asks for a re-snug every 200 h, which is a symptom of the expected
  relaxation.

**Why it matters**
- ASA creeps under screw preload at 45–60 °C (45 °C chamber, heatsink nearby). So does the 3010's
  plastic.
- Preload loss loosens the PCB, the 3010 and the frame together. The duct pose (3.35 mm sock gap,
  0.44 mm Z margin) and the fan-plate mode (147 Hz without the 4th pad) depend on that clamp.

**Fix**
1. Put metal compression sleeves (thin brass or steel tubes) through the three bosses so the
   preload path is metal → PCB.
2. Add a fourth anchor to the carriage where possible, for example the right stock cover-screw
   insert at X +22.6, Z 35.35. The left one is blocked by the LiDAR box.
3. Add a torque audit after the first 10 hot hours.
4. Include the PCB and the 3010 in the joint stiffness estimate.

---

### R-05 — MAJOR — The duct has no flat bed contact; "printable upright" depends on supports under nearly the whole underside

**Evidence**
- The validator's duct record shows `bed_contact_mm2: 0.0` (`cad/exports/validation_report.json`).
  It is not flagged, because `validate.py:186` treats only down-facing faces at Z < 0.01 as bed
  contact.
- REVIEWER-GEOMETRY on the print-oriented STL:
  - only 10 mesh vertices lie within 0.3 mm of the lowest point (the chamfered lip edges);
  - 1 660 mm² of down-facing (> 45°) faces sit within 1 mm above it: the manifold and plenum
    underside at about Z 3.3 in the nozzle frame, 0.86 mm above the lips at 2.44.
- `print-settings.md:19,33-57` asks for supports "under the manifold, the plenum underside and the
  outer lip bottoms", a brim "outer only", and support blockers "over every one of the 5 outlets".

**Why it matters**
- In PC, a part that touches the plate only on five lip edges, over about 0.7 mm of support,
  is a likely warp or detach failure.
- The lips are the clearance-critical features: 0.44 mm margin to `DUCT_MIN_Z`, and the 6 × 3 mm
  outlet height. They carry the support scars.

**Fix**
- Make the underside co-planar with the lip bottoms, or add a sacrificial flat foot ring at the
  lip plane that is cut off after printing.
- Alternatively, re-orient and accept supports elsewhere, or print on a raft and re-measure the
  ports.
- Make `validate.py` report bed-contact area in the part's own print frame.

---

### R-06 — MAJOR — The lowest point drops from 6.4/7.1 to 2.44 mm above the tip; snagging risk is not assessed

**Evidence**
- `stock-vs-new.md` §5 "Lowest point": stock duct +7.1, cover lip +6.4, S7 lips +2.44.
- `DUCT_MIN_Z` = 2.0 (`interfaces.py:219`) rests only on "nozzle wipe drags 0.15 mm into PEI;
  glass flex and blobs".
- Bed-edge features (M11) are priority 3 (`missing-information.md`).
- ABS and ASA run at 0–30 % fan (research/01:279-284), so they curl.

**Why it matters**
- Curled overhang edges, blobs, purge lines, glass-retention features or a wipe strip that a 7 mm
  duct used to clear can now strike thin PC lips.
- The lips sit 3.35 mm from the hot sock: a strike pushes the manifold toward it. The stock
  design's clearance from below is lost without a requirement replacing it.

**Fix**
1. Raise M11 to priority 1.
2. Write a "curl/snag clearance" requirement, and quantify the CFD cost of 3–4 mm lips.
3. Add to V5 a deliberately curling ABS overhang print, and check the lips afterwards.
4. Confirm that Z-hop and travel settings in the Orca profiles clear 2.44 mm.

---

### R-07 — MAJOR — The duct material near the heater (PC at 3.35 mm, fan off) is not demonstrated

**Evidence**
- DD-07 (`design-decisions.md:237`) rests on a community anecdote ("covers warped … fan off at
  260 °C") and a 15 mm rule.
- The sock surface temperature is MISSING (`cfd-report.md` §16 R6). The 3 mm clearance is
  ESTIMATED (`interfaces.py:230`).
- No document estimates the fan-off wall temperature.
- V8 (`cfd-report.md:695`) is 2 h at 280 °C, fan 0 %, judged by caliper only. It measures no
  temperature.
- This user's ABS/ASA profiles run at 0–30 % fan in a 45 °C chamber, so the "fan-off" condition
  is routine, not an edge case.

**Reviewer's estimate** (REVIEWER-ESTIMATE, 1-D, no conduction along the duct):
- the manifold inner wall faces the sock across 3.35 mm of still air:
  - conduction about 10 W/m²K;
  - radiation about 11 W/m²K;
  - about 21 W/m²K in total;
- behind it is an enclosed channel and an outer wall to the 45 °C chamber: about 6–10 W/m²K.

| Sock surface | Inner wall |
|---|---|
| 120 °C | ≈ 99 °C |
| 150 °C | ≈ 121 °C |
| 180 °C | ≈ 143 °C |
| 200 °C | ≈ 157 °C |

Typical TDS heat-deflection temperatures (ESTIMATED, check the spool): PC blends about 110–120 °C,
pure PC about 135–140 °C, annealed PA-CF higher.

**Why it matters**
- At plausible sock temperatures, a PC-blend manifold runs at or above its HDT.
- It is a cantilever with a 0.44 mm Z margin and a 0.35 mm sock margin, so creep sag or lip
  distortion is a credible failure mode.

**Fix**
1. Make V8 quantitative:
   - thermocouples on the sock bottom and on the manifold inner face;
   - nozzle at 300 °C, chamber 45 °C, fan 0 %, at least 4 h;
   - measure lip Z before and after.
2. Specify the filament by HDT, for example ≥ 130 °C at 0.45 MPa, or annealed PA-CF.
3. Consider 4–5 mm clearance for the manifold inner face (the ports can stay), or a reflective
   aluminium-tape shield on that face.

---

### R-08 — MAJOR — The thermal-proxy results come from solutions whose energy balance does not close, and differently in each case

**Evidence** (REVIEWER-RAN reading of `results.json`, `thermal.balance`)

| Case | Walls in [W] | Open boundaries out [W] | Excess |
|---|---|---|---|
| S7, lower bound | 34.39 | 50.48 | **+46.8 %** |
| S7, upper bound | — | — | +55.5 % |
| S7 + Same Sky | — | — | +11.5 % |
| STOCK, lower bound | — | — | +2.2 % |
| STOCK, upper bound | — | — | +2.9 % |

- `postprocess.py:290-358` computes h from the final-iteration T and a wall-function diffusivity.
  The balance uses the last `hflux` sample.
- `cfd-report.md:470-474` asserts that S7's h is "more likely under-estimated" and "the ranking
  does not depend on this". Neither claim is demonstrated: a spurious source of about 16 W next to
  34 W of wall input can bias near-wall T either way.
- DD-01 (`design-decisions.md:114`), `calibration.md:163`, `stock-vs-new.md:45` and
  `validation.md:156` restate this as "closes only to 47–56 %". That is a different statement: the
  outflow is 147–156 % of the input, not 47–56 % of it.

**Why it matters**
- These numbers all come from the unclosed solutions:
  - ×3.5 part-top h;
  - ×2.0 heat removed;
  - +6.2/+6.8 W heater demand;
  - "Same Sky +21 % h", which compares an 11 % case with a 47 % case.
- The comparison is not "same method, same error". The error depends on the case.

**Fix**
1. Solve the scalar on the time-averaged flow (re-projected for continuity), or run a short
   time-accurate (URANS) average with T.
2. Require balance closure ≤ 5 % before quoting h or W.
3. Until then, label these values "proxy, energy balance unclosed" and fix the wording in the four
   documents.

---

### R-09 — MAJOR — The headline ×4.8 has had none of the robustness checks the method itself prescribes

**Evidence**
- `research/04:54`: "A laminar run (`--set solver.turbulence=laminar`) is a cheap bracketing check
  for any final design. If the two models disagree on the ranking, that is a red flag."
  `summary.csv` contains no laminar case.
- `research/04:63`: test inlet-profile sensitivity "by imposing a skewed profile". Not done.
  S7's feed drop is 13 mm, and the weakest sector is the least robust metric.
- STOCK, the denominator of every ratio, was never run at L3 (`cfd-report.md:599`). Its
  reverse-engineered slot outlets are "approximate" (§14.4).
- 21 of 30 rows in `summary.csv` are `converged: False` (750-iteration cap).
  `export_for_cfd.py:231` disables the probe criterion (`tol_probe 1e9`) and relaxes the residual
  caps to 1e-2/3e-2. The probe change is not mentioned in the report.
- Per-face side metrics change by 29–33 % from L2 to L3 (see R-11).

**Why it matters**
- At Re about 10³, SST runs fully turbulent. S7 (close wedge jets) and STOCK (distant slot jets
  along the sock) are different jet types.
- A turbulence-model change can move the two differently. "Rankings robust" and "±20–30 %" are
  therefore assertions, not results.

**Fix** (all cheap on this machine, at 16–50 min each)
1. Laminar runs of STOCK and S7 at the lower bound.
2. STOCK at L3.
3. One S7 run with a skewed outlet profile.

Quote the resulting spread as the uncertainty of ×4.8 and of the weakest-sector ratio.

---

### R-10 — MAJOR — The part proxy and the modelled environment bias the stock-versus-new comparison

**Evidence**
- The part proxy is a 20 × 20 mm block (`interfaces.py:234`).
- STOCK's side jets "land outside the 20 mm part" at X ±12–13 (`cfd-report.md:204`). On a larger
  part they would land on the part and spread toward the nozzle as wall jets.
- `export_for_cfd.py` includes no MicroProbe body, although it sits at Y 12.5–28.1 right behind
  the nozzle, down to low Z. It also includes no LiDAR module (`grep` of the file; §3 lists the
  omitted bodies without mentioning the probe).
- The K1 Max auxiliary side fan (`[fan_generic auxiliary]`, PB1; research/01:265) runs at 70 % for
  PLA and is not modelled. Neither is its interaction with a duct that is open on the left.

**Why it matters**
- ×4.8 is the gain *on a 20 mm part, near the nozzle, with no probe and no aux fan*.
- On large parts the stock deficit is probably smaller (REVIEWER-ESTIMATE, direction only).
- The probe body shapes exactly the rear sectors and the +Y face that DD-01 and V5 care about.

**Fix**
1. Run STOCK and S7 once with a large plate proxy (for example 120 × 120 mm) and the probe body
   as a wall.
2. State the headline with its conditions in `README.md`, the root `README.md` and `STATUS.md`.
3. Run V5 with the aux fan both on and off.

---

### R-11 — MAJOR — On the part's left face S7 is worse than stock; "side faces about 4×" is driven by one face; D2 was rejected on the annulus only

**Evidence** (`summary.csv` `side3_Unear_by_face`, lower bound)

| Face | STOCK [m/s] | S7 L2 [m/s] | S7 L3 [m/s] |
|---|---|---|---|
| −X (left) | 0.79 | **0.69** | 0.49 |
| +X | 0.32 | 6.35 | — |
| +Y | 0.09 | 0.63 | — |
| −Y | 1.29 | 2.87 | 1.93 |

Thermal proxy h by face:

| Face | STOCK [W/m²K] | S7 [W/m²K] |
|---|---|---|
| −X | 44 | **37** |
| −Y | 80 | 89 |
| +X | 21 | 148 |

- From L2 to L3, the per-face values move by 29–33 % (−X −29 %, −Y −33 %).
- `cfd-report.md:416` says "side faces about 4×". That is the four-face mean, dominated by +X
  (×20).
- D2 gives −X 6.90 and −Y 4.73 (about 10× and 1.6× S7). DD-01's rejection
  (`design-decisions.md:104-105`) weighs only the r 1–6 mm annulus symmetry and minimum sector.

**Why it matters**
- Walls and overhangs facing −X (the LiDAR side) are predicted to cool *less* than today.
- The documentation's direction-dependence messages and V5 expectations do not say so.

**Fix**
1. Report the faces separately everywhere, and state "−X worse than stock".
2. Add a per-face criterion to DD-01.
3. In V5, compare −X and +Y walls against stock prints.
4. Treat per-face values as not mesh-converged.

---

### R-12 — MAJOR — There is no plan to retune slicer fan percentages after a ×3.5–4.8 airflow change

**Evidence**
- Orca profiles (research/01:279-286):
  - ABS/ASA part fan 0–30 %;
  - PETG 30–80 %;
  - PLA 100 % with aux fan 70 %;
  - overhang fan inherited from the Creality presets.
- None of `calibration.md`, `print-settings.md` or `validation.md` mentions re-tuning them.

**Why it matters**
- At the same percentage, the layer sees several times the stock air.
- Expect weaker layer bonding and more warping or cracking in ABS/ASA, and possibly PETG bridging
  and adhesion changes. These would be caused by the retrofit but read as "the duct is bad".

**Fix**
1. Add a calibration step: provisional ABS/ASA and PETG fan maxima at about 1/3–1/2 of today's
   values (REVIEWER-ESTIMATE, a starting point only).
2. Tune with layer-adhesion and warp coupons, then record the result. This is a slicer-profile
   change, so it is the user's decision.

---

### R-13 — MAJOR — The Same Sky "conditional upgrade" violates the hard X limit and does not fit the cover

**Evidence**
- `duct_generator.py:117`: `x0 = RIGHT_LIMIT_X - w`. The Same Sky box is X −27.4…24.2, Z 23.4…74.6,
  inside the XY-joint band (S7SS `_geometry`).
- Its right face is exactly at the hard stall limit 24.2 (`interfaces.py:225-228`: X homes by
  stalling against the right joint). That is 0 mm margin.
- It is 51.6 mm wide, so no ±24.0 cover can enclose it. Any wall exceeds 24.2.
- `design-decisions.md:110` still says "it fits the same bay".

**Why it matters**
- The documented fallback for "not enough cooling" is not buildable as described.
- At 0 mm margin, the fan housing becomes the part that stalls against the joint when X homes.

**Fix**
- State the conflict in DD-01, `cfd-report.md` §12.1 and `electrical.md` §2.
- Require ≥ 1 mm margin, an open-sided cover or a different pose, and re-run the S7SS case
  afterwards.

---

### R-14 — MINOR — The socket clearance and open joint leak air; CFD assumes a sealed inlet

**Evidence**
- The socket is two side plates with "1.0 mm clearance per side, ESTIMATED"
  (`duct_interface.json` "fan_mounting"). Nothing seals the Y faces (R-02).
- The CFD body has no socket and a sealed stub.

**Reviewer's estimate** (REVIEWER-ESTIMATE):
- leak area 30–60 mm², Cd 0.6;
- on the lower-bound 4020 curve, the duct flow falls by about 7–12 %, with 0.26–0.48 L/s escaping
  at the socket.
- That loss is the same size as the fan-swap margins DD-01 decided on.

**Fix**
- After M7, set a 0.2–0.3 mm fit and add a seal (foam, or Kapton tape).
- Write the seal into `assembly.md` and add it to the V2 checks.

### R-15 — MINOR — Screw-head clearances pass by margins smaller than print and part tolerances; the ISO 4762 option is unvalidated

**Evidence**
- `validate.py` log: the lower fan screw head is 0.299 mm from the duct body. The rule is
  `HEAD_MIN_GAP` 0.3 − `CONTACT_TOL` 0.01 (`validate.py:201,284`), so it passes by 0.009 mm.
- The cover holes are Ø6.3 for Ø5.7 heads, 0.3 mm radial (`cad/README.md:192-197`), on ESTIMATED
  hole positions.
- `bill-of-materials.md:53` and `maintenance.md:39` allow ISO 4762 or DIN 912 (2.5 mm hex). Its
  head is 3.0 mm tall (`common.py` `SHCS_HEAD`): it would stand 1.3 mm proud of the cover front
  (Y −59.5). None of this is modelled.

**Fix**
- Specify ISO 7380 only.
- Make the cover holes Ø7 or slotted after M7.
- Set `HEAD_MIN_GAP` above the FDM tolerance (≥ 0.5 mm).

### R-16 — MINOR — Validator coverage gaps, and clearances checked at nominal only

**Evidence**
- Reference-versus-reference pairs are skipped (`validate.py:396`), so the fan box is never
  checked against stock solids, LiDAR boxes or travel limits. REVIEWER-GEOMETRY: it clears them
  today (2.75 mm to `LIDAR_RESERVED_BODY`, 5.0 mm to the component zone), but nothing enforces it.
- There are no shank or tip checks (R-02, R-03), bed contact assumes Z = 0 (R-05), and the rear
  check ignores X (R-01).
- The frame is located only by three M3 screws in Ø3.4 bores, and the duct by two M3 in clearance
  holes plus a 1 mm socket. No tolerance stack exists for:
  - the 0.35 mm margin on `HOT_ZONE_CLEARANCE`;
  - the 0.44 mm margin on `DUCT_MIN_Z`.

**Fix**
1. Check reference parts that move with the toolhead (fans) like printed parts.
2. Add a worst-case stack-up, about ±0.2 mm per joint and ±0.2 mm print.
3. Add a locating feature to at least one frame–PCB joint (for example a close-fit boss in the
   lower-left hole).

### R-17 — MINOR — The ASA frame boss is inside DD-07's own hot-zone wording

**Evidence**
- DD-07 (`design-decisions.md:237`): "any part below the heatsink (Z < +31.9) within 15 mm of the
  sock surface" must be PC or PA-CF.
- `export_manifest.json` frame note: the boss's lower edge reaches Z 30.55, 13.7 mm from the sock,
  in ASA.
- REVIEWER-ESTIMATE: about 55–65 °C in operation (radiation from the sock, in the 3010 intake
  stream), so the practical risk is low.

**Fix:** either reword DD-07 (as a distance-and-view-factor rule) or make the frame PC.

### R-18 — MINOR — Heater headroom has not been checked at maximum flow, and the nozzle-tip gradient is ignored

**Evidence** (REVIEWER-ESTIMATE for the Orca "PLA Speed Benchy" profile: 255 °C, 32 mm³/s, 100 % fan,
`filament_heat_capacity` 1.8, ambient 35 °C)

| | Stock | S7 |
|---|---|---|
| Fan loss term | 0.1166 W/K → 25.7 W | 0.145 W/K → 31.9 W |
| Plus extrusion (15.7 W) | 41 W | 48 W |
| Share of the 60 W heater | 69 % | 79 % |

- `calibration.md` E.3 tests static power only.
- The cone near-wall speed rises ×7.5 and the sock bottom ×16. The tip and melt run cooler than
  the block thermistor, and this changes with fan duty.

**Fix**
- Add a max-flow purge test at the hottest temperature with fan 100 %, and record the heater duty.
- Check flow consistency at fan 0 % and 100 %.

### R-19 — MINOR — Tagging and single-source discipline (rule compliance)

**Evidence**

In `interfaces.py`:
- values held as plain tuples or floats with status only in comments (`all_unconfirmed()` misses
  them):
  - `PCB_HOLES`, `HEATSINK_FRONT_HOLES`, `COVER_SCREWS`, `X_RODS_YZ`, `XY_JOINT_BAND_Z`,
    `LIDAR_LINE_X`;
  - `PROBE_ADAPTER_SCREWS` (comment says ESTIMATED);
- `BlowerSpec.outlet` and `hole_d` are untagged (`interfaces.py:185-199`);
- `LIDAR_DISTANCE_ORIGIN_Z` uses the status "MEASURED-BY-USER", which is outside the four-tag
  scheme and is treated as confirmed;
- `UPPER_PATTERN_HOLES_TARGET` is DERIVED at line 83 but described as MISSING at line 89.
  `stiffness.py` also says MISSING.

In `duct_generator.py`, values are hard-coded although the file header forbids it:
- `STOCK_FAN_SCREWS_XZ` (:81);
- `PROBE_KEEPOUT` X ±11 (:48);
- `DENSITY` (:52);
- `FAN_MASS_G["samesky"]` (:65);
- `FRAME_FRONT_Y` (:79).

None of the CFD requests R1–R6 (`cfd-report.md` §16) were applied.

**Fix:** convert these to `Dim`/`Box`, add R1–R6 to `interfaces.py`, and fail `validate.py` on an
unknown status.

### R-20 — MINOR — Insert boss walls are thin, and the cover screws can bottom out

**Evidence**
- `common.py:117`: hole Ø4.0 with `min_wall` 1.6 gives a Ø7.2 boss. With OD 4.6–5.0 inserts, 1.1–1.3 mm
  of ASA remains around the knurl.
- Cover M3×6: the seat is at Z 73.0, so the tip is at 67.0. The hole bottom is at 66.8
  (`frame.py:243`). That leaves 0.2 mm, against a typical ±0.24 mm length tolerance plus melt
  pushed into the relief.

**Fix:** Ø8.5–9 bosses, M3×5 cover screws, or a 2 mm relief.

### R-21 — MINOR — The LiDAR "fumes not promoted" conclusion comes from a model without the module and without buoyancy

**Evidence**
- `export_for_cfd.py:188-193`: the window plane sits in free air. There is no module body, and the
  model is isothermal (no hot plume).
- DD-02 (`design-decisions.md:151`) states "fumes are not carried onto the windows".

**Fix**
- Soften the claim to "no evidence of"; V7 remains the evidence.
- Optionally add the module box to the LiDAR-environment case.

### R-22 — MINOR — The duct cantilever lever is understated, and its mode is still unestimated

**Evidence**
- `cfd-report.md:718` and `maintenance.md:140` say "about 45 mm".
- The tab plane is at Y −36.5…−37.75 and the rear-right end at Y +27.5, so the lever is about
  64 mm.
- Pitch stiffness about X comes only from two 7 × 7 mm, 2.5 mm thick PC tab pads.
- `validation.md` §2.4 confirms that no estimate exists.

**Fix:** a hand estimate or tap test, and decide on the proposed third tab before release.

### R-23 — MINOR — Documentation contradictions and stale statements

| Where | Says | Should say or check |
|---|---|---|
| `README.md:98` | `STATUS.md` = "session snapshot from 2026-11-01 (before the CFD result); superseded" | `STATUS.md` is dated 2026-11-12 and includes CFD. Fix one of them |
| `design-decisions.md:228` (DD-06) | L2 "mesh-independent to about 1.5 % on averaged metrics" | the S7 L3 check: side faces −7 %, per-face up to −33 %, weakest sector −21.5 % |
| DD-01:114, calibration:163, stock-vs-new:45, validation:156 | "balance closes only to 47–56 %" | outflow exceeds wall input by 47–56 % (R-08) |
| `cfd-report.md:654` | the 4020 bounds change layer speed "by ±50 %" | +51 % lower→upper, about ±20 % about the midpoint (as `validation.md` §1.4 and M16 say) |
| `cfd-report.md:149` vs `:531` | feed contraction "221 → about 150 mm²" vs "221 → 208 mm²" | update §5.2 |
| `cfd-report.md:87` vs the metric used | "annulus r 1–6 at Z −0.1" | every result uses Z +0.3 (0.5 mm above the part) |
| `missing-information.md:19` (M8) | "Printables is blocked here" | research/01 H.1 later downloaded the 785004 STL |
| `STATUS.md:25` vs `README.md` | +6 W "ESTIMATED from the proxy" vs "SIMULATED (proxy, indicative)" | one tag |
| root `README.md:128` | "about 4.8×" | add "at the lower 4020 bound (3.8× at the upper), 20 mm part proxy" |
| `missing-information.md` | M7 is priority 2 | `README.md` already asks for it with priority 1, and it decides fit (R-02, R-03). Make it priority 1 |
| `maintenance.md:39` vs `cad/README.md:192` | fan screws ISO 4762 (2.5 mm hex) vs ISO 7380 | ISO 7380 (R-15) |
| `cad/README.md:107-108` | "Exports never contain third-party geometry" | true for `cad/exports/`, but Henlor STEP is committed under `simulations/cfd/cases/stock/` (R-26) |

### R-24 — MINOR — The Klipper example snippets need a verification step

**Evidence and fix**
- *Include order.* Adding `[include part_fan.cfg]` "as the LAST line of tuning.cfg" does not
  guarantee precedence over Pellcorp's `fan_control.cfg`, which may be read later. Add a check of
  `printer.configfile.settings.fan` after `FIRMWARE_RESTART` to every example, and to
  `electrical.md` §5.
- *Proposed LiDAR macro* (`calibration.md` §6). It restores `printer.fan.speed`, which Klipper
  reports after `max_power` scaling. That is harmless at `max_power: 1.0`, but note it.
- *Same Sky buck.* Inrush into the buck's input capacitors through PB6 happens at every
  kick-start. It is unverified against the unknown PB6 switch.

### R-25 — MINOR — A conservative ESTIMATED PCB component zone pushes the whole stack 7 mm forward

**Evidence**
- `duct_interface.json` `intake_window_3010.stock_gap_mm: -1.3`: the stock 4020 itself overlaps the
  ESTIMATED zone.
- The frame plate's position comes from that zone (`duct_generator.py:79`, `common.py:138`).
- As a result:
  - the fan sits 7.1 mm forward of stock;
  - the cover 3.2 mm past the front soft limit (the WARN);
  - more mass sits forward.

**Fix:** after M10, move the plate back to the real component height.

### R-26 — NOTE — Third-party geometry and non-reproducible provenance

**Evidence**
- `simulations/cfd/cases/stock/stock_duct.step.gz` (Henlor, CC BY 4.0) and `stock_cover.step.gz` are
  committed without an attribution or licence file beside them.
- `stock_cache.py:19-21` defaults to a session-specific scratchpad path.
- research/01:444 cites scratchpad paths for the downloaded references, which are not in the repo.

**Fix:** add `ATTRIBUTION.md` next to the STEP files, and make the cache path configurable with a
neutral default.

### R-27 — NOTE — A PLA/PETG part stays 5 mm from the heater in the baseline build

**Evidence**
- The baseline keeps the 785004 adapter (`assembly.md` §1). Its material is ESTIMATED PLA/PETG
  (validation report mass basis).
- REVIEWER-GEOMETRY: its box is 5.1 mm from the sock box.
- The project rule says no PLA/PETG near the hotend.

**Fix:** reprint the unchanged 785004 STL in ASA, PC or PA-CF now. This needs no M8 data.

### R-28 — NOTE — Naming and model consistency

**Evidence**
- research/04 §8 "Validation case" is numerical verification (mesh and boundary conditions). There
  is no experimental validation yet, which the documents do acknowledge elsewhere.
- The STOCK fan inlet patch is 198.8 mm² and the S7 patch 221 mm², for the same fan
  (`results.json` `inlets`). It is a small effect, but undocumented.

### R-29 — NOTE — The moving-mass headline includes an unreleased part

**Evidence:** "−0.7 … +8.3 g" assumes the PA-CF probe mount replaces the 785004
(`validation.md` §3), but the baseline keeps the 785004. `stock-vs-new.md` notes the 0.6–0.9 g
difference; `README.md` and `STATUS.md` do not.

## Checked and found sound

- **Branch scope.**
  - Outside `hardware/toolhead/`, only the root `README.md` changed (+4 lines: a layout row and a
    roadmap entry).
  - There are no deletions anywhere. `*.cfg`, `custom/`, `orcaslicer/` and `helper/` are untouched.
  - `__pycache__` is ignored and untracked.
- **`validate.py` reproduces** (REVIEWER-RAN, outputs redirected to the scratchpad, repo
  untouched):
  - 0 FAIL / 4 WARN;
  - the committed `validation_report.md` is identical to the regenerated one;
  - `_ducts` is identical.
- **Headline numbers match the raw files.**

  | Case | Raw value | Report |
  |---|---|---|
  | `S7_part_proxy_L2` annulus mean | 8.8346 | 8.84 |
  | `STOCK_part_proxy_L2` annulus mean | 1.8296 | 1.83 (ratio 4.83) |
  | S7 sectors | min 6.2796 at 315–360° | matches |
  | S7 L3 | 8.772 / 4.930 | matches |
  | wall regions (S7, STOCK, D2) | e.g. S7 cone 7.174, STOCK part top 1.383, D2 cone 8.874 | match |
  | thermal Q (S7) | nozzle 4.38, sock 9.76 | match |
  | thermal Q (STOCK) | nozzle 1.16, sock 6.77 | match |

  Derived figures are correct:
  - +6.21 / +6.72 W;
  - ×1.99 / ×1.80 heat removed;
  - the D2 deltas: +41 % Q, −5 % layer, −44 % weakest sector, +24 % cone;
  - the Same Sky deltas: +22 % Q, +13 % layer, −11 % weakest sector, +13 % cone.
- **CFD hygiene.**
  - Global mass imbalance is ≤ 0.1 % in every case.
  - The averaged metrics are stable from the 750- to the 950-iteration runs (S7 annulus 8.835 →
    8.818).
  - The `fanPressure` operating point sits on the curve.
  - The domain-size check is reasonable.
  - A plausibility cross-check holds: STOCK's simulated forced loss at 100 % fan (8.0 W) is about
    MPC's measured fan term (0.0366 W/K, about 8 W).
  - The part-top h magnitudes agree in order with a flat-plate estimate (REVIEWER-ESTIMATE).
- **The fan decision logic at the lower bound** is sound, given the stated uncertainties. The
  Delta and the second 4020 are rejected for good reasons. The Same Sky correctly stays
  conditional on V1.
- **LiDAR geometry.**
  - The duct's leftmost point is X −15.78, against −18 for the optical box. The laser sheet is
    5.2 mm away (REVIEWER-GEOMETRY).
  - The sheet direction in `lidar_sheet_y()` is consistent with `lidar_y_per_z`.
  - No new part enters the reserved boxes.
- **X-joint band (baseline).** The cover is ±24.0, the frame ≤ 20.0 and the duct stays outside the
  band. These are the same margins as stock.
- **Screws and access.**
  - PCB screw arithmetic: 7.3 mm in the heatsink, upper screws 0.8 mm deeper than stock.
  - Head and driver-access checks are real modelled-geometry checks.
  - The service order (fan off before the PCB screws, hex key for T_right) is documented.
- **Fan mounting load path.** The fan's CoM (−1.3, 43.4) lies 0.3 mm from the line through its two
  diagonal screws, so in-plane inertial loads go straight into the screws.
- **ASA frame and cover temperatures** in the 45 °C chamber are acceptable (REVIEWER-ESTIMATE,
  frame boss about 55–65 °C).
- **Electrical.**
  - The baseline really changes nothing.
  - DD-05's "no low-side switch for 4-wire fans" is correct.
  - The tachometer poll arithmetic is correct.
  - The proposed LiDAR fan-off macro matches the real `_FIRST_LAYER_AFTER` and the
    `first_layer_armed` status field in `custom/lidar.py`. It is correctly left unapplied.
- **Rollback.**
  - The stock parts and screws are bagged.
  - The include-line removal is documented.
  - The MPC, z_offset, shaper and twist restore paths, and the commit note from step A, are
    documented.
- **Honesty of labelling.** Simulated, estimated and design values are consistently separated. The
  "nothing printed or measured" statements are accurate.

## What this review ran

- `git diff --stat` / `--name-status` against `origin/main`.
- `validate.py` through a wrapper that redirects `EXPORTS` to the scratchpad (about 1.5 min).
- build123d checks on `cad/exports/step/duct_body.step` and the `assembly.py` build: overlaps,
  shank intersections, slices, bed contact, extents and clearances.
- A short Python read of `simulations/cfd/results/*/results.json` and `summary.csv`.
- No CFD run was started or stopped. No repository file other than this one was written.

## Resolution status (2026-11-12, after the review round)

Added after the review, by the project, not by the reviewer. Each row was checked against the files
named. Status: **fixed** (the fix the finding asks for is in the design and the documents), **partly**
(part of it is done; the rest is named), **open** (not done), **user** (waits for a measurement,
test or action by the user). Nothing has been printed or measured yet, so no fix is confirmed on the
printer.

| R | Severity | Status | Where, and what remains |
|---|---|---|---|
| R-01 | CRITICAL | fixed | S8 ends at Y +9.8 (`cfd-report.md` §17.1, §17.4); `validate.py` checks the XY footprint behind Y +10 below Z 30 against the probe body + 785004 (validation report, rear footprint PASS for every part); rear keep-out jog mandatory (`calibration.md` D.4). The jog itself is still to be done on the printer |
| R-02 | MAJOR | partly | Fixed: the 4020 is a solid in `validate.py` (body + ESTIMATED nozzle + bores), the socket is four-sided with 0.25 mm clearance and 0.000 mm³ inside the fan (cap 0.5 mm³), screw shanks and tips are checked, the fan screw clears the socket by 0.60 mm (`cfd-report.md` §17.9), a skewed-inlet CFD run was made (§17.5). Open: the hole-vs-outlet contradiction (validation WARN, 154 mm³) until M7 (`missing-information.md`) |
| R-03 | MAJOR | partly | Fixed: every insert hole is blind with a 0.8 mm floor; fan-screw tip check in `validate.py` (WARN, safe length 22.5…23.7 mm); `bill-of-materials.md` F6, `maintenance.md` §3 and `assembly.md` step 5 corrected. User: the hole type and through-length (M7) decide the screw length and whether the joint changes; drill only a spare 4020 (`assembly.md` step 2.5) |
| R-04 | MAJOR | fixed | BT4M brass sleeves in the three PCB bosses (`cad/README.md`, BOM F11, `assembly.md` step 3.3); 4th anchor evaluated and not added, with reasons (`cad/README.md`, validation INFO); PCB and 3010 in the clamp stiffness (validation report stiffness); torque audit after the first 10 hot hours (`maintenance.md` §5) |
| R-05 | MAJOR | fixed | flat base at Z 3.0, 1378 mm² bed contact; bed contact checked in each part's own print frame (validation report); `print-settings.md` updated |
| R-06 | MAJOR | partly | Fixed: lowest point raised to 3.0 (flat base); CFD cost of 3.0 / 3.5 mm lips measured (`cfd-report.md` §17.3); M11 is priority 1 and asks for the Z-hop; a curling ABS print is in V5 (`validation.md` §4.3). Open: no snag requirement beyond `DUCT_MIN_Z`; the requested `DUCT_MIN_Z = 2.4` is not applied (`cfd-report.md` §16 R7). User: M11 |
| R-07 | MAJOR | fixed | V8 quantitative (thermocouples, 300 °C, fan 0 %, ≥ 4 h, lip height; `validation.md` V8); materials by HDT ≥ 130 °C at 0.45 MPa (DD-07); duct in HT resin, 238 °C class (DD-07a); sock clearance 4.54 mm, manifold wall 7.8 mm. User: M20 and V8 |
| R-08 | MAJOR | fixed | frozen-mean scalar method, balance closes to −0.03 % (S8) / −0.5 % (STOCK), ≤ 5 % acceptance (`cfd-report.md` §17.7); S7's thermal W values withdrawn in DD-01, `calibration.md` E, `stock-vs-new.md`, `validation.md` |
| R-09 | MAJOR | fixed | laminar, STOCK L3, skewed inlet and long-average runs; the spread is quoted with every headline (×4.4, ×4.3–5.3; `cfd-report.md` §17.5); the probe criterion is documented (§13.4) |
| R-10 | MAJOR | fixed | 120 × 120 mm plate and probe body as a wall run (`cfd-report.md` §17.5); headline with its conditions in `README.md`, `STATUS.md` and the root `README.md`; V5 with the aux fan on and off (`cfd-report.md` §15, `validation.md` V5) |
| R-11 | MAJOR | fixed | faces reported separately (`cfd-report.md` §17.6, `stock-vs-new.md`, `validation.md`); per-face criterion in DD-01 (S7 fails on −X, S8 passes); V3 and V5 judged per face; per-face values flagged as known to about a factor of 2 |
| R-12 | MAJOR | fixed | `calibration.md` L (provisional fan maxima, coupons, profile change left to the user). User: the retune |
| R-13 | MAJOR | fixed | not buildable stated in DD-01, `cfd-report.md` §12.1 and §17.8, `electrical.md` §2.1, `bill-of-materials.md` §3 |
| R-14 | MINOR | fixed | four-sided socket at 0.25 mm; leak estimated (11 % unsealed; `cfd-report.md` §17.9); seal in `assembly.md` step 6 and BOM F12; checked in `calibration.md` C and V2 |
| R-15 | MINOR | fixed | ISO 7380 only (BOM F6, `maintenance.md` §0, `cad/README.md`); cover holes Ø6.7, 0.5 mm radial; `HEAD_MIN_GAP` 0.5 (`validate.py`) |
| R-16 | MINOR | fixed | the 4020 is checked like a printed part (LiDAR, XY band, rear footprint in the validation report); stack-up ±0.2 per joint and print (worst case 0.62 mm, INFO); close-fit Ø4.05 locating bore at the lower-left PCB screw (`cad/README.md`) |
| R-17 | MINOR | fixed | DD-07 rewritten by HDT and by what a part sees; the frame boss stays ASA with that reasoning (`cad/README.md` R-17 note) |
| R-18 | MINOR | fixed | max-flow headroom test with pass limits (`calibration.md` E.4) |
| R-19 | MINOR | partly | Fixed: `FRAME_FRONT_Y` in `duct_generator.py` now derives from `interfaces.PCB_COMPONENT_ZONE`; the fan geometry lives in one place (`FAN4020_M7`). Open: the plain tuples in `interfaces.py` (`PCB_HOLES`, `HEATSINK_FRONT_HOLES`, `COVER_SCREWS`, `X_RODS_YZ`, `XY_JOINT_BAND_Z`, `LIDAR_LINE_X`, `PROBE_ADAPTER_SCREWS`), the untagged `BlowerSpec.hole_d`, "MEASURED-BY-USER", the "MISSING, M2" comment next to the DERIVED `UPPER_PATTERN_HOLES_TARGET`, `PROBE_KEEPOUT` / `DENSITY` / Same Sky mass hard-coded in `duct_generator.py`, the `cfd-report.md` §16 requests, and no FAIL on an unknown status |
| R-20 | MINOR | fixed | Ø8.5 bosses with 1.80 mm around the knurl; cover holes 6.0 mm deep, the M3×6 tip 1.2 mm above the floor (validation report) |
| R-21 | MINOR | fixed | claim softened to "no evidence of transport" in `cfd-report.md` §13.1, DD-02, `maintenance.md` §4; V7 is the evidence. Not done (optional): the module box in the LiDAR case |
| R-22 | MINOR | fixed | third tab T_3; pitch-mode estimate 1530…2742 Hz on three tabs, lever 46 mm (validation report); tap test in `assembly.md` step 6. The estimate assumes a rigid duct |
| R-23 | MINOR | fixed | every row of the table checked: `README.md` STATUS row, DD-06, the four "47–56 %" sentences, `cfd-report.md` §14.3, §5.2 and §2, M8, the `STATUS.md` tag, the root `README.md` headline, M7 priority 1, `maintenance.md` ISO 7380, the `cad/README.md` export sentence |
| R-24 | MINOR | fixed | include-order check after `FIRMWARE_RESTART` (`electrical.md` §5); the `max_power` note on the proposed LiDAR macro (`calibration.md` §6). The Same Sky buck inrush is moot: the upgrade is not buildable (R-13) |
| R-25 | MINOR | user | the frame plate still sits on the ESTIMATED component zone; move it back after M10 |
| R-26 | NOTE | partly | Fixed: `simulations/cfd/cases/stock/ATTRIBUTION.md`; the cache path is configurable (`K1TH_STOCK_CACHE`). Open: the default in `stock_cache.py` and the reference paths in research/01 are still session scratchpad paths |
| R-27 | NOTE | user | reprint of the unchanged 785004 in ASA, PC or PA-CF in DD-07, `bill-of-materials.md` §1, `assembly.md` §1, `print-settings.md` §1. The reprint itself is the user's |
| R-28 | NOTE | partly | Fixed: the STOCK vs S8 inlet area is quantified (≤ 0.5 % on STOCK's flow, `cfd-report.md` §17.9); `validation.md` §1.3 calls the research/04 case numerical verification. Open: research/04 §8 is still headed "Validation case" |
| R-29 | NOTE | fixed | `README.md`, `STATUS.md`, BOM and `stock-vs-new.md` give the moving mass with the probe mount and say it is 0.6–0.9 g less while the 785004 stays |

Counts: fixed 21, partly 6, open 0, user 2.
