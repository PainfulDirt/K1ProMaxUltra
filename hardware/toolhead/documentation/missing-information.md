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
| M8 | **Current MicroProbe mount:**<br>• is it Printables 785004? (Its STL was downloaded later, research/01 H.1; please confirm it is the one fitted, and its material. It is reprinted in ASA, PC or PA-CF either way, review R-27);<br>• which toolhead screws it uses;<br>• retracted and deployed pin-tip Z relative to the nozzle tip;<br>• the probe body's rearmost Y. | Probe mount design and the rear limit. |
| M9 | **Clearance at the travel limits**, as gap and at which Z:<br>• at X −2 and X 306.5 (Y ≈ 150): the gap from the toolhead's left/right extremes to the XY joints;<br>• at Y −2: the gap from the front of the cover to the door/frame;<br>• at Y max in a clear zone (X 105): the gap from the stock rear to the frame. | Fixes `FRONT_LIMIT_Y` / `RIGHT_LIMIT_X`, which are currently soft placeholders. |
| M10 | **Nozzle PCB, both sides:** connector positions, the height of the tallest component on the front face, and the copper/components around the three mounting holes. | Boss pads and the connector zone. |
| M7 | **4020 blower, decisive for fit (review R-02, R-03):**<br>• outlet opening position and inside size (ESTIMATED 13 × 17 at the bottom-right), and whether the outlet protrudes as a nozzle, with its outer size and depth (ESTIMATED 4.0 mm);<br>• the X/Z position of every mounting hole relative to the fan body, and whether the holes are through-holes or tapping holes (the stock fan is held by M3×18, which suggests tapping holes);<br>• the hole through-length (ESTIMATED 20.0);<br>• the 4020 and 3010 masses.<br>Best on the optional spare 4020. | **It still blocks two things.** (1) The **fan screw length**: with the ESTIMATED 20.0 mm through-length the safe length is 22.5…23.7 mm, no standard ISO 7380 length fits, and M3×24 ends 0.2 mm from the blind insert floor (validation WARN); tapping holes would change the joint itself. (2) The **hole-vs-outlet contradiction**: the modelled lower-right hole (16.05, 25.6) lies inside the modelled outlet column (154 mm³ overlap, validation WARN), which a real blower cannot have, so the hole positions or the outlet are wrong. The duct socket (0.25 mm clearance), its screw notch and the T_right arm depend on both. Each value is a one-line change in `cad/source/ducts/duct_generator.py` `FAN4020_M7` (`cfd-report.md` §17.9). |
| M11 | **Curl and snag clearance (review R-06):**<br>• glass + PEI thickness;<br>• anything near the bed edges that stands above the glass (clips, wipe strip, purge area);<br>• the Z-hop used in the Orca profiles. | The S8 duct's lowest point (its flat base) is 3.0 mm above the nozzle tip, against 6.4–7.1 mm on stock. The CFD measured no layer-speed loss for lips at 3.0–3.5 mm (`cfd-report.md` §17.3), so a higher base is possible if M11 asks for it (recheck the −Y face). |

## Priority 2: improves accuracy of CFD, mass and electrics

| ID | What | Why |
|---|---|---|
| M1 | Hotend version: 2023 ceramic or "Unicorn" (photo of the heater and nozzle). Do you plan a hotend change? | The stack height differs by 1.6 mm. |
| M5 | Stock cover:<br>• mass with and without the 4020;<br>• the two cover-screw positions;<br>• duct outlet: lowest edge Z above the tip, outlet position and cross-section. | A real stock baseline for CFD. |
| M12 | Kitchen-scale weights (±1 g): cover, 4020, 3010, probe + mount, LiDAR + bracket. | Mass budget. |
| M13 | **Moving-mass test, no disassembly:**<br>• run `SHAPER_CALIBRATE`;<br>• tape a known ~50 g mass rigidly to the toolhead and run it again;<br>• keep both CSV sets.<br>Effective mass = Δm / ((f0/f1)² − 1). | Replaces the 400–500 g estimate. |
| M15 | Toolhead board, part-fan channel:<br>• does PB6 switch +24 V or GND?<br>• MOSFET part numbers.<br>(Procedure: `electrical.md` §4.) | **Only needed for the Same Sky option**, which is not buildable in this architecture (DD-01). CFD chose one stock 4020 on the stock channel, so the baseline doesn't need it. |
| M16 | **Closed for the datasheet fans:** the Delta, Same Sky and Sunon curves are digitized (research/03 §10). **Still open for the stock 4020**, which has no published curve. If you have a manometer, run bench test V1 (`cfd-report.md` §15) on a spare 4020. | The 4020's two bounds (191 / 390 Pa) change the absolute cooling by about ±20 %. They don't change the design choice. |
| M14 | Chamber air temperature during an ABS print, and the cover surface near the outlet if you have a thermocouple. | ASA vs PC for the frame. |
| M20 | **Sock surface temperature:** a thin thermocouple taped to the bottom of the silicone sock, nozzle at 250 and 300 °C, part fan at 0 % and 100 %. | **It decides the resin margin**: the HT-resin duct's closest point is 4.54 mm from the sock (the manifold's inner wall 7.8 mm), and the review's 1-D estimate (made for S7's 3.35 mm gap, fan off) puts the inner wall at about 99–157 °C for a 120–200 °C sock (DD-07, DD-07a). Against a 238 °C-class resin and V8's 15 K rule that leaves a large margin, but the sock temperature is unmeasured. It also scales the sock share of the +7.6 W heater penalty (the thermal proxy assumes 150 °C). |

## Priority 3: nice to have

| ID | What |
|---|---|
| M3 | X rod diameter, spacing and axis positions; belt clamp positions. Only needed if a later revision replaces the carriage. |
| M4 | Vertical stack heights from the tip: heatsink bottom, carriage underside, extruder top, PTFE inlet. |
| M17 | The installed base `printer.cfg`, or which K1 Max variant (2023/2024), so travel and rotation_distance can be confirmed. |
| M18 | The overhang/bridge fan values Orca inherits from the Creality Generic presets. |
| M19 | Optional, read-only: the LiDAR's 0x1E calibration bytes and 0x1C temperature, as a baseline. |

## Purchase list

CFD has decided (DD-01): **one stock 4020, the one already fitted.** The user decided the duct
material (DD-07a). To buy or order for the baseline (details and screw specs in
`bill-of-materials.md`):
- **the S8 duct body, 2 pieces, in HT resin (238 °C class, HDT at 0.45 MPa after the full thermal
  post-cure per the TDS), from a print service**, with the order conditions in `print-settings.md`
  "Duct from a print service": full thermal post-cure, every channel flushed, no support contact on
  the outlet lips, inside the ports or on the socket faces;
- **3 × M3 washers ISO 7089** (3.2 × 7 × 0.5) for the duct tabs, plus the 3 × M3×6 ISO 7380 tab
  screws (BOM F5, F5a);
- **seal for the fan socket**: Kapton tape, or a 0.5–1 mm thin foam strip (BOM F12);
- **one Albion Alloys BT4M brass tube** (4.0 × 0.45, 305 mm), cut into 3 sleeves of 11.10 mm (BOM F11);
- the other screws and inserts in BOM §2 (M3×30 ×3, the fan screws once M7 sets their length, M3×6
  ×2 for the cover, 7 M3 inserts);
- printed, not bought: the 785004 adapter reprinted in ASA, PC or PA-CF (review R-27).

Optional: **one spare Creality 4020** (4004110132), to measure M7 and its P–Q curve (V1) without
touching the fitted fan, and as a spare.

Not to buy: the Same Sky CBM-5015BF and its buck. The upgrade is not buildable in this frame/cover
architecture (DD-01, `cfd-report.md` §17.8).
