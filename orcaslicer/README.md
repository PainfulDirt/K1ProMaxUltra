# K1 Max Tuned: OrcaSlicer 2.4 profiles

Made for this printer on 2026-09-28: Simple AF with Kalico, Microprobe V2 plus load cells, glass bed, and the calibration done that day.

## Import

In OrcaSlicer: **File → Import → Import Configs…**, then choose `K1Max-Tuned-OrcaSlicer-profiles.zip`. You can also multi-select the `.json` files in `machine/`, `process/` and `filament/`. Restart Orca if the new printers don't appear.

Then select the printer **K1 Max Tuned (0.4 nozzle)** (or the nozzle you have fitted). Only the processes and filaments that match that nozzle are shown.

The printers inherit from Orca's own *Creality K1 Max* presets, so the bed shape, thumbnails, limits and and the Moonraker upload all carry over (set your printer's address in the printer profile).

## What's inside

| Nozzle | Layer heights (mm) | First layer |
|---|---|---|
| 0.2 | 0.04 · 0.06 · 0.08 · 0.10 · 0.12 · 0.14 | 0.12 |
| 0.4 | 0.06 · 0.08 · 0.12 · 0.16 · 0.20 · 0.24 · 0.28 · 0.32 | 0.20 |
| 0.6 | 0.12 · 0.18 · 0.24 · 0.30 · 0.36 · 0.42 | 0.30 |
| 0.8 | 0.16 · 0.24 · 0.32 · 0.40 · 0.48 · 0.56 | 0.40 |
| 1.0 | 0.20 · 0.30 · 0.40 · 0.50 · 0.60 · 0.70 | 0.50 |

- **Layer heights** run from about 20% of the nozzle size (finest) to 70–80% (coarsest).
- **Filaments:** 12 presets, and each works with all five nozzles:

| Filament | Nozzle / bed °C | Max flow (mm³/s) | PA (0.4) | Notes |
|---|---|---|---|---|
| PLA | 220 / 60 | 20 | 0.04 | |
| PLA Rapid | 225 / 60 | 23 | 0.04 | high-speed PLA, based on Creality's High Speed PLA preset |
| PLA Silk | 220 / 60 | 8 | 0.04 | low flow keeps the shine |
| PLA+ | 225 / 60 | 18 | 0.04 | tougher blend, a bit hotter |
| PLA Matte | 220 / 60 | 18 | 0.04 | |
| PETG | 250 / 70 | 14 | 0.046 | |
| PETG Rapid | 250 / 70 | 18 | 0.046 | the Elegoo Rapid PETG settings that printed the Benchy |
| PETG Silk | 245 / 70 | 8 | 0.046 | low flow keeps the shine |
| PETG+ | 245 / 70 | 14 | 0.046 | |
| PETG Matte | 245 / 70 | 12 | 0.046 | |
| ABS / ASA | 260 / 100 | 16 | 0.04 | chamber fan waits for 60 °C |

  Temperatures vary by brand, so check the range printed on the spool. PETG Rapid is the only row that's been proven on this printer: its PA of 0.046 comes from an Orca PA test on the 0.4 nozzle (0.040–0.052 all looked good). The other PETG variants use the same PA as a starting point, and everything else in the table is a starting point too.

## Speed tiers

**59 profiles.** Every layer height has **Balanced**, and the other two tiers exist only where they change the print (`tier_makes_sense()` in `make_profiles.py`).

| Tier | Where | What |
|---|---|---|
| **Balanced** | every layer height | the everyday profile (original names, e.g. `0.20mm Standard @K1 Max Tuned 0.4`) |
| **Precision** | 0.4, 0.6, 0.8, 1.0 nozzles, fine to standard layers (up to half the nozzle size) | real quality: every feature is capped at **10 mm³/s** melt rate (fully melted plastic, good layer bonding) and accelerations are halved. On big nozzles that is much slower than Balanced: 0.8 at 0.40 mm walls ~30 mm/s, 1.0 at 0.50 mm ~19 mm/s. |
| **Fast** | 0.2 nozzle (all), 0.4 nozzle 0.06–0.12 mm, 0.6 nozzle 0.12 mm | infill, inner walls and travel at full speed (×2, 20000 mm/s²), outer wall kept gentle (×1.2, shaper-limit acceleration) |

Why Fast only there: the stock K1 Max hotend melts ~23 mm³/s of fast PLA, and Orca caps every speed at the filament's max flow, so on standard/coarse layers Balanced is already at that limit. On a 120×120×30 mm block Fast saved 29–41% where it's included (0.2 nozzle at 0.10 mm: 10.0 h → 5.9 h; 0.4 at 0.12 mm: 2.7 h → 1.9 h) and under 11% where it isn't. The 0.2 nozzle has no Precision because it never gets near 10 mm³/s. With a high-flow hotend, raise the filaments' `vol` in `MATERIALS` and re-run the generator: Fast then appears on more layer heights by itself.

## Why the settings are what they are

- **Start G-code** is just `START_PRINT`. The printer does the rest itself: glass soak, hot Z re-home, adaptive mesh, nozzle wipe, load-cell nozzle touch and purge. The stock `T0`, which Klipper doesn't know, and the extra Z moves are removed.
- **Layer progress:** every layer sends `SET_PRINT_STATS_INFO`, so Fluidd and the screen show layer X/Y and "pause at layer" works.
- **Object labels are on.** The adaptive bed mesh reads them.
- **Acceleration:** walls 4000–5000, top surfaces 2500–3000, infill 8000–10000, travel 12000. The input shaper result (X 3hump_ei 77.6 Hz, Y ei 52 Hz) gives crisp corners up to roughly 4400–5800 mm/s².
- **Jerk is 0**, so Orca no longer overrides the printer's corner velocity of 5 (the value the shaper was tuned with). The stock Creality profile forced 20.
- **Arc fitting is off.** Klipper's `[gcode_arcs]` resolution is 1 mm, which would turn small circles into visible facets.
- **Filament start G-code:**
  - `MPC_SET` gives Kalico's MPC hotend control the material's density and heat capacity.
  - `M141` sets the temperature at which the chamber fan kicks in: PLA 35 °C, PETG 40 °C, ABS/ASA 60 °C (so the chamber stays warm).
- **PETG** uses what printed your good Benchy: 250 °C nozzle, 70 °C bed, flow 0.99. PA is 0.046, from your PA test.
- **0.2 nozzle:** Arachne walls, and gap fill only on top and bottom surfaces. Orca 2.4.2's gap fill between walls fails on some models at 0.06 and 0.08 mm layers with this nozzle.

## Still needs calibrating (Orca → Calibration menu)

- **Pressure advance for each nozzle size.** The PA values are for the 0.4 nozzle. The other nozzles need their own values.
- **Max volumetric speed.** The starting values are PLA 20, PETG 14, ABS/ASA 16 mm³/s. These, not the speed settings, are what limit the 0.8 and 1.0 nozzles, so the Orca max-flow test is worth doing if you use those nozzles a lot.
- **Flow ratio** for each filament brand.

## Testing

Every Balanced process, the tiers on every nozzle, and the Fast tier on a large block were sliced on a 3DBenchy with the Orca 2.4.2 command-line slicer, using the full inherited settings, as were all 12 filaments. All sliced with the correct layer heights, line widths, first layers, temperatures and object labels. The GUI import itself hasn't been tried.

## Changing things

`make_profiles.py` regenerates everything: `python3 make_profiles.py out`. All the per-nozzle values are in the `NOZZLES` table at the top, and the per-material values are in `MATERIALS`.
