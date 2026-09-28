# K1ProMaxUltra

A Creality **K1 Max** tuned for accurate first layers on a **glass bed**. It runs [Pellcorp's Simple AF](https://github.com/pellcorp/creality) firmware with [Kalico](https://github.com/pellcorp/kalico) and uses two sensors together:

- a **Microprobe V2** for homing and the bed mesh,
- the **stock bed load cells** for nozzle-touch Z.

The repo is the printer's live **Pellcorp config overrides** folder. Pellcorp updates install normally and then re-apply everything here, so the printer stays current and keeps its tuning.

## What's different from a stock Simple AF install

| Problem | What this does |
|---|---|
| The mesh seemed to be ignored on the glass bed | **Glass soak** (`_GLASS_SOAK`): when the bed reaches 80 °C, the middle of the glass is 0.16 mm low. It then rises 0.25 mm over ~6.5 minutes before it settles, so a mesh taken right away doesn't match the bed by the first layer. START_PRINT now probes the Z-home spot every 40 s until the readings stop changing. That takes ~6.5 min from cold and ~1.5 min if the bed is already hot. |
| Z homing cold, meshing hot | **Hot Z re-home** after the soak, then a mesh with `zero_reference_position` at the Z-home spot. |
| First-layer height depends on the probe offset | **Load-cell nozzle touch**: first the nozzle is wiped on the rear edge of the bed. Then it taps the bed at the mesh zero point with the load cells, and that contact becomes Z=0. The Microprobe checks the result, and if the touch reads early (dirty nozzle) it falls back to Microprobe Z instead of trusting it. |
| The Microprobe can't reach the right 27 mm of the bed (33 mm X offset) | **`BED_MESH_EXTEND`** ([custom/bed_mesh_extend.py](custom/bed_mesh_extend.py)), a Kalico plugin. When a print reaches past X 273, it taps with the nozzle near the mesh edge and near the bed edge on 5 rows, and extends the mesh to X 300 using the measured slope. It only uses the difference between each pair of taps, so constant offsets cancel out. |
| Homing and mesh probes triggering at different heights | The Z homing speed now matches the probe speed. At 1 mm/s vs 5 mm/s they triggered 0.03 mm apart. |
| X-rail wobble | **Axis twist compensation**, measured with nozzle touch against the Microprobe at 7 spots over 4 passes. No paper test. The profile is ±0.035 mm. |
| Hotend temperature dips when the fan changes speed | **MPC** (Kalico) instead of PID: 0.5 °C overshoot, ±1.5 °C on a 0→100% fan step. |
| Bed warmed by the glass | Bed PID retuned at 80 °C. The input shaper was re-run (X 3hump_ei 77.6 Hz, Y ei 52 Hz). |
| Updates | A **nightly check** writes `UPDATES.md` to the config folder, and there are one-click update macros. See below. |

## Layout

```
tuning.cfg               all the printer-side changes above (included from printer.cfg)
printer.cfg, *.cfg       Pellcorp overrides: only the lines that differ from Pellcorp's files
printer.cfg.save_config  SAVE_CONFIG block: probe offset, input shaper, PID/MPC, meshes
custom/
  bed_mesh_extend.py     Kalico plugin, linked into klipper/klippy/plugins
  k1max-boot.sh          recreates the plugin link and starts cron (runs at boot via S54k1max)
  check-updates.sh       nightly: Pellcorp/Kalico update check -> UPDATES.md
  update.sh              saves overrides (+ git push), updates, re-links, checks Klipper
orcaslicer/              OrcaSlicer 2.4 profiles for this printer (5 nozzles, 32 processes, 12 filaments)
```

## Updates

- **Every night at 4:00**, the printer checks Pellcorp and Kalico for new commits. Nothing is installed automatically. The result goes to `UPDATES.md`, visible in Fluidd under Configuration, and a message appears when the printer is idle. It also says when a Kalico update includes new MCU firmware (which needs a power cycle).
- **`K1_UPDATE_PELLCORP`** / **`K1_UPDATE_KALICO`**: these refuse to run while printing. Otherwise they save the overrides (committing and pushing them here), update, restore the plugin link, and report whether Klipper came back `ready`. The log is `logs/k1max_update.log`.
- **`K1_CHECK_UPDATES`** runs the check on demand.

## Using this on your own K1 / K1 Max

This is one specific printer, so read `tuning.cfg` before copying anything. The values **tied to this hardware** are:

- `[probe]` / Microprobe: `x_offset -33`, `z_offset` (SAVE_CONFIG), and `zero_reference_position` (the probe position while homing Z)
- `[load_cell_probe]`: the load-cell settings. The leveling board needs Pellcorp's Kalico **bed MCU firmware with HX711 support** (bed0_121 or newer). The pins are the stock K1 ones. `reference_tare_counts` must be measured on your printer (read `force_g` with the bed empty). `counts_per_gram` is Pellcorp's K1 value.
- `[axis_twist_compensation]` values, `_GLASS_SOAK` thresholds, the wipe strip location (`_TOUCH_NOZZLE_WIPE`, Y 298), and the `[bed_mesh_extend]` edge positions

Rough steps on a Simple AF printer that has Kalico and the load-cell bed firmware:

1. Copy `tuning.cfg` to `printer_data/config/` and add `[include tuning.cfg]` to `printer.cfg`, after the probe includes.
2. Copy `custom/` to `/usr/data/pellcorp-overrides/custom/` and run `custom/k1max-boot.sh`.
3. Change the hardware-specific values above, restart, then run `CONFIG_OVERRIDES` so updates keep your changes.

## OrcaSlicer profiles

`orcaslicer/`: import `K1Max-Tuned-OrcaSlicer-profiles.zip` with *File → Import → Import Configs*, then set your printer's address in the printer profile (Connection). See [orcaslicer/README.md](orcaslicer/README.md) for what's inside and why. They match the printer side: the start G-code is just `START_PRINT`, layer progress is reported, object labels are on (for the adaptive mesh), jerk is 0 so the corner velocity the input shaper was tuned for is kept, and arc fitting is off.

## Credits

- [Pellcorp / Simple AF](https://github.com/pellcorp/creality), [Kalico](https://github.com/KalicoCrew/kalico), and Pellcorp's [load-cell work](https://github.com/pellcorp/creality/issues/1500) built on OpenCentauri's hx711s driver
- `bed_mesh_extend.py` is GPLv3, like Klipper and Kalico

Use at your own risk. This drives a hot nozzle into the bed on purpose.
