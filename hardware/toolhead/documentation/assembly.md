# Assembly, disassembly and rollback

How to fit the new cooling module (frame, the stock 4020, the S7 duct) and the cover to **this**
K1 Max, and how to go back to stock. Parts, screws and inserts: `bill-of-materials.md`. Printing and
heat-set inserts: `print-settings.md`. Calibration after fitting: `calibration.md`.

Coordinates are in the nozzle frame used everywhere in this project: origin at the nozzle tip, +X
printer right, +Y toward the rear, +Z up, mm. "Front" is −Y.

Nothing here has been done on the printer yet. Steps marked **[M#]** rest on values that are still
ESTIMATED or MISSING (`missing-information.md`); their checks are how those values get confirmed.
Steps marked **INFERRED** follow from the CAD but have not been tried.

**Torque.** No sourced torque values exist for any of these joints. Every screw into a printed
part or a heat-set insert is **snug, plastic boss: do not over-tighten.** (`print-settings.md` §3
uses ≈ 0.4–0.5 N·m for the M3 insert spin check; that figure is ESTIMATED, not a datasheet value.)
The PCB screws go into the carriage's brass inserts and the heatsink's aluminium: snug as well.

## 1. What to do first, in order

| # | What | Where | Gate |
|---|---|---|---|
| 1 | **Print and check the fit-check coupon** (ASA, ≈ 10 min, 2.89 g) | `print-settings.md` §5 | all dims in tolerance, inserts good, necks flat on bare PCB, no component contact, 4th-pad gap recorded |
| 2 | Send the **priority-1 measurements**: M2 (toolhead without cover), M6 (LiDAR module and **what its bracket screws into**), M8 (probe mount), M9 (travel clearances), M10 (PCB) | `missing-information.md` | answered, CAD updated and `validate.py` re-run if anything changed |
| 3 | Measure the 4020 (M7): outlet opening, diagonal-hole through-length, mass. Easiest when it is out of the stock cover (step 2 below) or on the optional spare | `missing-information.md` M7 | sets the fan screw length (BOM F6) and confirms the duct socket and cover |
| 4 | Print the frame (ASA), cover (ASA) and duct (PC). Status FIT-CHECK FIRST | `print-settings.md` §1 | parts measured, supports out of the duct, outlets open |
| 5 | Assemble (§2 below), with the checks after each step | this page | every check passes |
| 6 | Calibrate | `calibration.md` | its §4 acceptance numbers |
| 7 | Physical validation tests V1–V8 | `validation.md` §4 | their pass criteria |

The MicroProbe mount is **not released** (M8). This assembly keeps the 785004 adapter and the probe
exactly as they are. §4 covers the probe mount for later.

## 2. Assembly

You need: the frame with its 6 M3 inserts set, the cover, the duct body, 3 × M3×30 ISO 7380 (F1),
2 × M3×24 or the M7-derived length (F6), 4 × M3×6 ISO 7380 (F4, F5), cable ties (F10); hex keys 2.0
and 2.5 mm, calipers, feeler gauges, a 2.0 mm and a 3.0 mm drill shank (or feeler stacks), a flat
block, a phone camera.

### Step 1. Baseline capture and preparation

1. Run `calibration.md` step A (backup, status, LiDAR dry run, optional shaper mass test).
2. Raise the toolhead well clear of the bed (`G0 Z50`), let the nozzle cool below 50 °C, switch the
   printer off.
3. Take photos of the toolhead from the front, left, right and below before touching anything
   (they also serve M2).

### Step 2. Stock cover and stock duct off; 4020 out of the stock cover

1. **LiDAR first.** Look at how the LiDAR bracket is fixed. A community report says the stock cover
   forces the LiDAR to be unplugged at every nozzle change (research/02 §5), and whether the bracket
   screws into the carriage or into the stock cover is open (**[M6]**). **If the bracket is fixed to
   the stock cover, stop here**: the new cover does not carry the bracket, and the design assumes
   the carriage (`missing-information.md` M6). If the LiDAR lead has to be unplugged to get the
   cover off, note the plug orientation and do not loosen the bracket.
2. Remove the 2 × M3×4 ultra-low SHCS at the sides (X ±22.6, Z 35.35, horizontal into the carriage
   inserts; research/02 C5). Slide the cover forward. The 4020 comes with it, still on its lead:
   unplug it at the board's "Model Fan" socket (back-probe nothing, pull the plug, not the wires).
3. Take the stock duct out of the cover (a separate part inside it; research/02 C6). Keep it.
4. Remove the 4020 from the cover: 3 × M3×18 BHCS (research/02 C7). Keep the screws.
5. **Measure the 4020 now [M7]:**
   - inside of the outlet opening, W × H (CAD: 17 × 13);
   - through-length of the two diagonal holes, at (X −18.65, Z 60.3) and (X 16.05, Z 25.6) in the
     mounted pose (CAD: 20.0). Buy or pick the F6 length by the rule: through-length + 3.5 … 4.5,
     never more than through-length + 5.0;
   - whether those holes are counterbored on the intake side, and how deep (this decides the cover
     check in step 7);
   - its mass (M12).
6. Keep every stock part in a labelled bag: cover, duct, 2 × M3×4, 3 × M3×18. They are the rollback
   (§3).

### Step 3. Prepare the new parts

1. Inserts in the frame (6 × M3 short brass, Ø4.0 holes, ≤ 4.5 mm long): 2 in the cover shelf
   (vertical), 2 in the fan standoffs and 2 in the duct lugs T_left / T_right (horizontal).
   Procedure, iron temperatures and checks: `print-settings.md` §3. For the horizontal holes, clamp
   the frame so the hole axis is vertical.
2. Every insert: flush to 0.2 mm below the face, square, an M3 screw runs in by hand.
3. Duct: supports removed, the 5 outlets open, the socket slides over the 4020 outlet nozzle without
   force (`print-settings.md` "Duct supports and checks"). **[M7]**
4. Trial-fit the cover over the frame on the bench: the top wall sits on the frame shelf and the
   two M3×6 holes line up.

### Step 4. Frame on the PCB holes

The frame bolts to the PCB's three-hole pattern with 3 × M3×30 ISO 7380 that replace the stock
screws: 2 × M3×18 BHCS upper at (X ±12, Z 58.3) into the carriage's brass inserts, and 1 × M3×20
BHCS lower-left at (X −12, Z 34.3) into the heatsink (research/02 N6/N7). The same screws hold the
PCB and the 3010 against the heatsink and carriage. There is no screw at (X +12, Z 34.3); the
frame's compression pad sits at that fourth corner.

The frame's bosses sit over the screw heads (Ø3.4 bores against a Ø5.7 head), so a stock screw
cannot stay in a hole the frame covers. Swap all three in one go:

1. With one hand, hold the PCB flat against the 3010 front face so that neither moves. Keep the PCB
   connectors plugged.
2. Remove the three stock PCB screws (2.0 mm hex). Keep them.
3. Offer the frame: bosses toward the PCB, the window in front of the 3010.
4. Push an M3×30 through the frame's upper-left boss, the PCB and the 3010, and turn it in by hand
   a few turns into the carriage insert. Then the upper-right one, then the lower-left one into the
   heatsink (it is shorter in engagement: 7.3 mm against the stock 8.5, `frame.py`).
5. Snug all three in turn (2.0 mm hex, ISO 7380). Do not over-tighten into the carriage inserts.

Checks after step 4 **[M10] [M2] [M6]**:

| Check | Pass | Basis |
|---|---|---|
| Every boss pad flat on the PCB | a 0.05 mm feeler does not pass under any pad | coupon procedure (`print-settings.md` §5) |
| Nothing on the PCB touches the frame plate; no pad on a component | visual, from the sides with a light | `PCB_COMPONENT_ZONE` ESTIMATED (M10) |
| 4th-corner pad (X +12, Z 34.3) | touches the PCB "2nd plate", or a gap ≤ 0.3 mm. Record it. Without contact the fan-plate mode estimate drops to 147 Hz | validation WARN; M10 |
| Frame window in front of the PCB fan cutout | aligned; the 3010 blades visible through it | 3010 intake 693 mm² open (validation) |
| Frame vs LiDAR module and bracket | visible gap, no contact | CAD 2.50 / 4.00 mm to the ESTIMATED boxes (M6) |
| Screw heads | all three seated on the frame's front face | — |
| Frame to sock | far apart | CAD 13.74 mm |

### Step 5. Fan on the frame

1. The 4020 goes in its stock XZ pose: intake facing forward (−Y), outlet at the bottom-right
   blowing down (−Z), rear face against the frame's two fan standoffs at Y −36.5.
2. 2 × M3×24 (or the M7-derived length, BOM F6) from the front through the diagonal holes at
   (X −18.65, Z 60.3) and (X 16.05, Z 25.6) into the frame inserts. Snug.
3. Plug the fan lead into "Model Fan". Route it to the frame's right top corner and tie it in the
   tie slot (2.5 mm tie).

Checks after step 5 **[M7]**:

| Check | Pass | Basis |
|---|---|---|
| Fan screws | they pull the fan onto the standoffs without bottoming. If a screw goes tight before the fan is seated, it is too long: stop, do not force it into the insert | 5.0 mm insert hole; through-length ESTIMATED (M7) |
| Fan rear face vs the PCB screw heads | gap visible (CAD: heads end at Y −35.15, fan at −36.5) | `frame.py` (3 mm plenum, 1.65 mm head) |
| Fan lead | reaches the socket without tension and does not cross the frame window or the 3010 intake. The fan sits 6–7 mm further forward than stock (`STOCK_4020_POS`): if the lead is short, use a 4-pin extension (pitch: MEASURE, `electrical.md` §1.1), never cut the stock lead | research/02 F3 (lead 60 mm) |
| Fan pose | fan square to the frame, outlet at the bottom-right | `duct_interface.json` |

### Step 6. Duct

The S7 duct hangs on two tabs and its fan socket. Its horseshoe manifold goes around the sock, open
on the LiDAR side, so it is fitted **from below** (INFERRED from the CAD; see `maintenance.md` §0).

1. Keep the probe stowed. Make sure there is room under the nozzle (step 1).
2. Hold the duct level under the toolhead, manifold around the nozzle, socket under the fan outlet.
   Raise it straight up: the manifold rises around the sock, then the socket slides about 4 mm over
   the 4020's outlet nozzle, and the two tabs come to lie flat on the frame lug faces at Y −36.5.
3. M3×6 ISO 7380 from the front into each tab: **T_left** at (X −7.5, Z 19.5), **T_right** at
   (X 24.0, Z 22.5). Snug. Driver access to these two screws is **not** checked by `validate.py`
   (it checks only the PCB screws): confirm that a 2.0 mm key reaches both with the fan fitted.

Checks after step 6 **[M7] [M1] [M8] [M10] [M6]**, nozzle cold:

| Check | Pass | Basis |
|---|---|---|
| **Duct to sock, all round** | a 3.0 mm drill shank (or a 3 mm feeler stack) passes between the sock and every part of the duct: manifold inner face, the 5 ports, both ends of the horseshoe | `HOT_ZONE_CLEARANCE` 3.0 (ESTIMATED); CAD minimum 3.35 mm |
| **Duct lowest point above the nozzle tip** | with the tip resting on a flat block, a 2.0 mm drill shank slides under the duct lips all round | `DUCT_MIN_Z` 2.0 (ESTIMATED); CAD lowest point 2.44 mm |
| Socket on the fan outlet | fully engaged, no visible gap at the joint, no force on the fan | `DUCT_FAN_SOCKET_FIT` 1.0 mm per side (ESTIMATED, M7) |
| Tabs | flat on the lug faces, no gap under the screw heads | `duct_interface.json` mating face Y −36.5 |
| Probe | visible gap between the duct's rear-right end and the probe body / 785004; the stowed pin is not touched (it hangs at Z 1.45, below the duct; unchanged from today) | CAD: the duct stays outside X ±11 behind Y 12.5 (ESTIMATED probe body, M8) |
| LiDAR | looking from the left and from below, no part of the duct is in the laser sheet or under the module's windows | CAD: duct leftmost X −15.8; 2.22 mm to the ESTIMATED optical box (M6) |
| Hotend version | the ports sit evenly around the nozzle, just above the tip level | ports placed for the 2023 ceramic hotend (`DUCT_HOTEND_VERSION`, M1); a Unicorn stack differs by 1.6 mm |
| Rattle | tap the manifold's rear-right end: it must not rattle or flap | about 45 mm lever from the tabs (`cfd-report.md` §16). If it flutters, the fix is a third tab (CAD change) |

If the duct-to-sock gap or the lowest point fails: take the duct off, do not print with it, and
report the measured values. Both rest on ESTIMATED interface values.

### Step 7. Cover

1. Slide the cover on from the front (it is open at the rear and bottom), until its top wall sits on
   the frame shelf.
2. 2 × M3×6 ISO 7380 from the top through the cover into the shelf inserts (X ±9, Y −44). Snug.
   **Do not use M3×8**: it bottoms out.

Checks after step 7 **[M7] [M6] [M9]**:

| Check | Pass | Basis |
|---|---|---|
| **Fan screw heads vs. the cover's front wall** | the cover seats flat on the shelf; both fan-screw heads (X −18.65, Z 60.3 and X 16.05, Z 25.6) sit inside the cover's Ø6.3 holes without touching | the holes follow the ESTIMATED 4020 hole positions (M7). If a head touches, stop and don't force the cover: open the hole with a Ø6.5 drill by hand and report the offset |
| 4020 intake | the Ø30 aperture is centred on the fan's intake and fully open; nothing touches the impeller | validation: 100 % of the Ø28 inlet disc open (inlet Ø ESTIMATED, M7) |
| Left wall vs LiDAR module and bracket | visible gap, no contact | CAD 0.50 mm to the ESTIMATED body box (M6): the tightest LiDAR clearance in the design |
| Right wall bottom vs T_right tab and lug | no contact | CAD ≥ 0.3 mm (wall bottom raised to Z 26.4) |
| Cover vs frame elsewhere | contact only at the shelf | CAD ≥ 0.3 mm elsewhere |
| Removal | the cover slides off forward without unplugging the LiDAR, probe or fan and without removing the duct; slide it back on | `cad/README.md` |
| Front extent | note it: the cover front is at Y −58.2, 3.2 mm further forward than the stock −55.0. The travel check is `calibration.md` step D | validation WARN (M9) |

### Step 8. Cable routing and final cold checks

1. Fan lead: tied at the frame's right top corner (step 5).
2. Probe lead: to the TOUCH port as today. With the 785004 kept, keep today's routing (the third tie
   slot is in the not-yet-released probe mount).
3. LiDAR lead: as today; plugged in if it was unplugged in step 2.
4. Nothing hangs below the LiDAR module or into the laser sheet; no tie end points down there.
5. Move the toolhead by hand along X (printer off): no lead or tie rubs the X rods, the belts, the
   belt retainers or the strain relief.
6. The 3010 intake path through the frame window is unobstructed.

### Step 9. Power up and calibrate

Follow `calibration.md` from step B: probe deploy/retract (`PROBE_DOWN`, `QUERY_PROBE`,
`PROBE_UP`), fan function (C), clearances at the travel limits (D), **MPC (E)** before any print,
then F–L. Do not start a real print before step E.

## 3. Disassembly and rollback to stock

Printer cold (nozzle below 50 °C), toolhead raised (`G0 Z50`), printer off.

1. **Cover:** 2 × M3×6 on top out, slide the cover forward.
2. **Duct:** hold it, 2 × M3×6 out of T_left and T_right, lower it straight down until the socket is
   free and the manifold is below the sock, then out forward (`maintenance.md` §0).
3. **Fan:** 2 × M3×24 out (2.5 mm hex); unplug the lead at "Model Fan".
4. **Frame:** hold the PCB flat against the 3010, take the 3 × M3×30 out, lift the frame off. Refit
   the stock PCB screws: **2 × M3×18 BHCS** upper (X ±12, Z 58.3, into the carriage inserts) and
   **1 × M3×20 BHCS** lower-left (X −12, Z 34.3, into the heatsink). Snug.
5. **4020 into the stock cover:** 3 × M3×18 BHCS (research/02 C7). Refit the stock duct in the cover
   as it came out.
6. **Stock cover on:** plug the 4020 into "Model Fan", plug the LiDAR back if it was unplugged, slide
   the cover on, and fit the 2 × M3×4 ultra-low SHCS at the sides into the carriage inserts
   (research/02 C5).
7. If the new probe mount was fitted (§4): refit the 785004 on the same two anchor screws.
8. **Calibration:** `calibration.md` §5 (MPC re-run or restore, then F, G, K or the saved values).
   No config change has to be undone for the baseline.

## 4. Later: the MicroProbe mount (only after M8)

The probe mount stays **NOT RELEASED** until M8 confirms the 785004's carriage anchor (photo +
calipers). When it is released:
1. Print in PA-CF (PC acceptable), anneal if the TDS gives a cycle, then set the 2 × M2.5 inserts
   (Ø3.6 holes, `print-settings.md` §3, §4).
2. Swap it for the 785004 on the same two carriage tabs with the 785004's ~M2 anchor screws (BOM F9;
   size and length MISSING, M8).
3. Drop the MicroProbe flange into the pocket (notch = connector, rear side) and fit the 2 × BIQU
   M2.5×5.
4. Tie the probe lead in the mount's roof tie slot.
5. Checks: `PROBE_DOWN` / `QUERY_PROBE` / `PROBE_UP`; the rear of the mount at Y 29.10 (785004: 29.1);
   then `calibration.md` F (z_offset within ±0.5 of 0.831, stop above 1.0), H (twist) and D
   (rear keep-outs, only if anything reaches past Y +29.1).

## 5. Which steps rest on unconfirmed data

| Step | Depends on | Status | Confirmed by |
|---|---|---|---|
| 2.1 LiDAR bracket fixing | where the bracket is screwed | MISSING (M6) | looking at it in step 2 |
| 2.5, 5, 7 fan screw length; fan pose | 4020 hole through-length 20.0, hole positions | ESTIMATED (M7) | measuring the 4020 (step 2.5) |
| 3.3, 6 duct socket | 4020 outlet 17 × 13, socket clearance 1.0 per side | ESTIMATED (M7) | socket trial fit |
| 4 frame pads, component zone, 4th pad | `MODULE_MOUNT_PAD_D` 6.5, `PCB_COMPONENT_ZONE`, `FRAME_FOURTH_PAD_ON` | ESTIMATED (M10) | coupon, then step 4 checks |
| 3.1 insert holes | `INSERT_M3_HOLE_D` 4.0 | ESTIMATED | coupon |
| 4 PCB screw targets | the upper two into carriage inserts, the lower into the heatsink | DERIVED from Henlor's K1 model (M2) | step 4 (the stock screws you remove: 18 / 18 / 20 mm) |
| 6 sock clearance, duct height | `HOT_ZONE_CLEARANCE` 3.0, `DUCT_MIN_Z` 2.0 | ESTIMATED | step 6 gauges; test V8 |
| 6 port position vs tip | hotend version 2023 ceramic | ESTIMATED (M1) | step 6 visual; M1 photo |
| 6 probe keep-out | probe body X ±11, Y 12.5…28.1; 785004 envelope | ESTIMATED (M8) | step 6 visual |
| 4, 6, 7 LiDAR clearances | `LIDAR_RESERVED_OPTICAL`, `LIDAR_RESERVED_BODY` | ESTIMATED (M6) | visual in steps 4, 6, 7; `calibration.md` G |
| 7 intake aperture | `FAN_INLET_D` 28 | ESTIMATED (M7) | step 7 visual |
| 7 cover vs fan screw heads | 4020 hole counterbore (if any) | not modelled | step 7 check |
| 7, calibration D front clearance | `FRONT_LIMIT_Y` −55 (soft) | DERIVED, travel unmeasured (M9) | `calibration.md` D |
| 6 duct removal path | horseshoe geometry | INFERRED from CAD | step 6 (fitting it is the same path in reverse) |
