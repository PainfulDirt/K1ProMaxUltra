# Information needed from you

These items can't be found in the repo, in reachable CAD, or from manufacturer sites. The IDs (M#) are referenced from
`cad/source/interfaces.py` and the validation report. Every printed part lists the M# it waits
for.

Measure with calipers (±0.05 mm). Take photos square-on with a ruler in frame.

**Z measured "from the nozzle tip":** put a flat block under the nozzle, touch it to the tip, and
measure up from the block.
**X/Y measured "to the nozzle":** measure to the side of the nozzle and add half its diameter.

## Priority 1: blocks printing anything except the fit-check coupon

| ID | What | Why |
|---|---|---|
| M2 | **Toolhead with the front cover removed: confirmation only.** The interfaces are now DERIVED from Henlor's reverse-engineered stock K1 CAD (research/02 §9): three M3 PCB screws, the upper two into carriage heat-set inserts and the lower one into the heatsink; the carriage tabs the probe mount uses. Please confirm with:<br>• photos from all 6 sides;<br>• the lengths of the three PCB screws;<br>• that the two upper screws go into brass inserts;<br>• that your K1 Max carriage matches the K1 model (the screw positions in research/02 §9.1). | The cooling module bolts to the PCB holes; the probe mount needs a metal anchor. Henlor's model is a K1, not a K1 Max. |
| M6 | **LiDAR module:**<br>• outline L × W × H;<br>• **what the stock bracket screws into: the carriage or the stock front cover?** The new design assumes the carriage; if it is the cover, the new cover has to carry the bracket;<br>• bracket screw positions relative to the nozzle;<br>• X/Y/Z of the centre of each optical window, and which one emits;<br>• a photo from below with the laser on. | Replaces the conservative `LIDAR_RESERVED` box. |
| M8 | **Current MicroProbe mount:**<br>• is it Printables 785004? Please send its STL/STEP (Printables is blocked here);<br>• which toolhead screws it uses;<br>• retracted and deployed pin-tip Z relative to the nozzle tip;<br>• the probe body's rearmost Y. | Probe mount design and the rear limit. |
| M9 | **Clearance at the travel limits**, as gap and at which Z:<br>• at X −2 and X 306.5 (Y ≈ 150): the gap from the toolhead's left/right extremes to the XY joints;<br>• at Y −2: the gap from the front of the cover to the door/frame;<br>• at Y max in a clear zone (X 105): the gap from the stock rear to the frame. | Fixes `FRONT_LIMIT_Y` / `RIGHT_LIMIT_X`, which are currently soft placeholders. |
| M10 | **Nozzle PCB, both sides:** connector positions, the height of the tallest component on the front face, and the copper/components around the three mounting holes. | Boss pads and the connector zone. |

## Priority 2: improves accuracy of CFD, mass and electrics

| ID | What | Why |
|---|---|---|
| M1 | Hotend version: 2023 ceramic or "Unicorn" (photo of the heater and nozzle). Do you plan a hotend change? | The stack height differs by 1.6 mm. |
| M5 | Stock cover:<br>• mass with and without the 4020;<br>• the two cover-screw positions;<br>• duct outlet: lowest edge Z above the tip, outlet position and cross-section. | A real stock baseline for CFD. |
| M7 | The 4020's **outlet opening** (inside W × H; ESTIMATED 17 × 13), the **through-length of its two diagonal screw holes** (ESTIMATED 20.0), and the 4020 and 3010 masses. | The duct socket fits over the outlet; the fan screw length (BOM F6); the mass budget. |
| M12 | Kitchen-scale weights (±1 g): cover, 4020, 3010, probe + mount, LiDAR + bracket. | Mass budget. |
| M13 | **Moving-mass test, no disassembly:**<br>• run `SHAPER_CALIBRATE`;<br>• tape a known ~50 g mass rigidly to the toolhead and run it again;<br>• keep both CSV sets.<br>Effective mass = Δm / ((f0/f1)² − 1). | Replaces the 400–500 g estimate. |
| M15 | Toolhead board, part-fan channel:<br>• does PB6 switch +24 V or GND?<br>• MOSFET part numbers.<br>(Procedure: `electrical.md` §4.) | **Only needed for the conditional Same Sky upgrade.** CFD chose one stock 4020 on the stock channel (DD-01), so the baseline doesn't need it. |
| M16 | **Closed for the datasheet fans:** the Delta, Same Sky and Sunon curves are digitized (research/03 §10). **Still open for the stock 4020**, which has no published curve. If you have a manometer, run bench test V1 (`cfd-report.md` §15) on a spare 4020. | The 4020's two bounds (191 / 390 Pa) change the absolute cooling by about ±20 %. They don't change the design choice. |
| M14 | Chamber air temperature during an ABS print, and the cover surface near the outlet if you have a thermocouple. | ASA vs PC for the frame. |

## Priority 3: nice to have

| ID | What |
|---|---|
| M3 | X rod diameter, spacing and axis positions; belt clamp positions. Only needed if a later revision replaces the carriage. |
| M4 | Vertical stack heights from the tip: heatsink bottom, carriage underside, extruder top, PTFE inlet. |
| M11 | Glass + PEI thickness; anything near the bed edges that stands above the glass. |
| M17 | The installed base `printer.cfg`, or which K1 Max variant (2023/2024), so travel and rotation_distance can be confirmed. |
| M18 | The overhang/bridge fan values Orca inherits from the Creality Generic presets. |
| M19 | Optional, read-only: the LiDAR's 0x1E calibration bytes and 0x1C temperature, as a baseline. |

## Purchase list

CFD has decided (DD-01): **one stock 4020, the one already fitted.** Nothing has to be bought for
the baseline except hardware (`bill-of-materials.md` §2).
- Optional: **one spare Creality 4020** (4004110132), as a spare and to measure its P–Q curve (V1).
- Conditional upgrade, only if V1 and the test prints call for it: Same Sky CBM-5015BF-175-459-22
  plus a 24→12 V buck (`bill-of-materials.md` §3).
