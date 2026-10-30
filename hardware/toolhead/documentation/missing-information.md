# Information needed from you

These items can't be found in the repo, in reachable CAD, or from manufacturer sites. Manufacturer
sites are blocked in this session; see M16. The IDs (M#) are referenced from
`cad/source/interfaces.py` and the validation report. Every printed part lists the M# it waits
for.

Measure with calipers (±0.05 mm). Take photos square-on with a ruler in frame.

**Z measured "from the nozzle tip":** put a flat block under the nozzle, touch it to the tip, and
measure up from the block.
**X/Y measured "to the nozzle":** measure to the side of the nozzle and add half its diameter.

## Priority 1: blocks printing anything except the fit-check coupon

| ID | What | Why |
|---|---|---|
| M2 | **Toolhead with the front cover removed.** Photos from all 6 sides. Then:<br>• the thread and length of the three PCB screws (they pass through the PCB and the 3010 fan);<br>• what the two upper screws (about Z +58 above the tip) thread into;<br>• for every other hole or thread on the carriage, its X/Y/Z position relative to the nozzle tip;<br>• how the heatsink is held. | The cooling module bolts to the PCB holes; the probe mount needs a metal anchor. |
| M6 | **LiDAR module:**<br>• outline L × W × H;<br>• bracket screw positions relative to the nozzle;<br>• X/Y/Z of the centre of each optical window, and which one emits;<br>• a photo from below with the laser on. | Replaces the conservative `LIDAR_RESERVED` box. |
| M8 | **Current MicroProbe mount:**<br>• is it Printables 785004? Please send its STL/STEP (Printables is blocked here);<br>• which toolhead screws it uses;<br>• retracted and deployed pin-tip Z relative to the nozzle tip;<br>• the probe body's rearmost Y. | Probe mount design and the rear limit. |
| M9 | **Clearance at the travel limits**, as gap and at which Z:<br>• at X −2 and X 306.5 (Y ≈ 150): the gap from the toolhead's left/right extremes to the XY joints;<br>• at Y −2: the gap from the front of the cover to the door/frame;<br>• at Y max in a clear zone (X 105): the gap from the stock rear to the frame. | Fixes `FRONT_LIMIT_Y` / `RIGHT_LIMIT_X`, which are currently soft placeholders. |
| M10 | **Nozzle PCB, both sides:** connector positions, the height of the tallest component on the front face, and the copper/components around the three mounting holes. | Boss pads and the connector zone. |

## Priority 2: improves accuracy of CFD, mass and electrics

| ID | What | Why |
|---|---|---|
| M1 | Hotend version: 2023 ceramic or "Unicorn" (photo of the heater and nozzle). Do you plan a hotend change? | The stack height differs by 1.6 mm. |
| M5 | Stock cover:<br>• mass with and without the 4020;<br>• the two cover-screw positions;<br>• duct outlet: lowest edge Z above the tip, outlet position and cross-section. | A real stock baseline for CFD. |
| M7 | The 4020's **outlet opening** (inside W × H), and the 4020 and 3010 masses. | Fan inlet patch and mass budget. |
| M12 | Kitchen-scale weights (±1 g): cover, 4020, 3010, probe + mount, LiDAR + bracket. | Mass budget. |
| M13 | **Moving-mass test, no disassembly:**<br>• run `SHAPER_CALIBRATE`;<br>• tape a known ~50 g mass rigidly to the toolhead and run it again;<br>• keep both CSV sets.<br>Effective mass = Δm / ((f0/f1)² − 1). | Replaces the 400–500 g estimate. |
| M15 | Toolhead board, part-fan channel:<br>• does PB6 switch +24 V or GND?<br>• MOSFET part numbers.<br>(Multimeter on the 4-pin fan plug: measure each pin against the 24 V and GND inputs with the fan at 0 % and 100 %.) | Decides whether two blowers can share the channel (DD-05). |
| M16 | Fan datasheets. Either:<br>• allow these domains in the environment's network settings: `sunon.com`, `sunonusa.com`, `delta-fan.com`, `mouser.com`, `digikey.com`, `printables.com`, `api.printables.com`; or<br>• put the PDFs for the Sunon MF40202VX / MF50152VX and the Delta BFB0524HH in the session. | Real P–Q curves instead of fitted ones. |
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

Nothing has to be bought before the CFD comparison finishes. Conditional candidates (research/03):
- a second Creality 4020 blower (4-pin, 24 V), if dual feed wins;
- one spare 4020 to measure the real fan curve;
- a small 24 V logic-level MOSFET module, if the channel can't carry two blowers.
