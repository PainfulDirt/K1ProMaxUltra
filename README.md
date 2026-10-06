# K1ProMaxUltra

A Creality **K1 Max** tuned for accurate first layers on a **glass bed**. It runs [Pellcorp's Simple AF](https://github.com/pellcorp/creality) firmware with [Kalico](https://github.com/pellcorp/kalico) and uses two sensors together:

- a **Microprobe V2** for homing and the bed mesh,
- the **stock bed load cells** for nozzle-touch Z.

The repo is the printer's live **Pellcorp config overrides** folder. Pellcorp updates install normally and then re-apply everything here, so the printer stays current and keeps its tuning.

## What's different from a stock Simple AF install

| Problem | What this does |
|---|---|
| The mesh seemed to be ignored on the glass bed | **Adaptive Glass Soak**: when the bed reaches 80 °C, the middle of the glass is 0.16 mm low. It then rises 0.25 mm over ~6.5 minutes, and the edges keep moving for 10+ minutes after that, so a mesh taken right away doesn't match the bed by the first layer. Every 40 s, START_PRINT probes the Z-home spot plus the corners of the print's own footprint (from the object outlines, like the adaptive mesh) until none of them moves. A small print in the middle watches 2 spots; a full-bed print watches 5. |
| Z homing cold, meshing hot | **Hot Z re-home** after the soak, then a mesh with `zero_reference_position` at the Z-home spot. |
| First-layer height depends on the probe offset | **True Zero Touch**: first a **Nozzle Deep Clean** on the rear edge of the bed (stock-style: slow hot scrub at 200 °C on fresh lines, then it stays pressed into the PEI while the fan cools it to 160 °C so the residue sets on the bed, then a slow 2 mm/s drag with Z rising that peels the residue off the tip). Then it taps the bed at the mesh zero point with the load cells, and that contact becomes Z=0. The Microprobe checks the result, and if the touch reads early (dirty nozzle) it falls back to Microprobe Z instead of trusting it. |
| Where the Microprobe can reach | The Microprobe sits **20.3 mm behind the nozzle, in line on X** (moved 2026-10-06; it used to be 33 mm to the left). The mesh covers the full width, X 5–295 × Y 20–295. Only the front ~20 mm can't be probed, and Klipper holds the front row flat there. **Adaptive Mesh Extend** (`BED_MESH_EXTEND`, [custom/mesh_edge_extend.py](custom/mesh_edge_extend.py)) was written for the old left-side mount, when the right 27 mm was out of reach, and is off. |
| The probe behind the nozzle hits the Z rod housings at the back | **Keep-out zones** ([custom/keep_out.py](custom/keep_out.py)): measured by stepping the toolhead back until ~3 mm were left. Blocked for the nozzle: back-left corner X 0–19 beyond Y 292, middle X 130–170 beyond Y 293, back-right X 266–286 beyond Y 302 and X 286+ beyond Y 287. Klipper checks every move: travel moves that would cross a zone are routed in front of it, anything else is refused before it moves. The Orca printers have the same zones (the corners are cut out of the bed shape, the middle is the excluded area), so nothing gets sliced there. The end-of-print park is at Y 270, and the Nozzle Deep Clean strip is at the back-left (X 40–100), where the probe clears the frame. |
| The stock LiDAR is dead under Simple AF (Creality's hotplug script switches it off) | **LiDAR** ([custom/lidar.py](custom/lidar.py), [custom/lidar-start.sh](custom/lidar-start.sh)): at boot the LiDAR is kept powered and Creality's `cx_ai_middleware`, still on the printer, is started to drive it. The plugin moves the toolhead and collects height profiles, about 1500 points across a 29 mm laser line, repeatable to 1–2 µm. Because the plate's texture doesn't move, a bare-plate scan is subtracted from every measurement. **LiDAR PA calibration** (`LIDAR_PA_CALIBRATION`) prints a test as a real print, measures it, and sets the pressure advance it finds. Everything is reduced while scanning (580 bins per profile, plain Python a row at a time), because the K1 has ~200 MB of RAM and a heavy job stalls Klipper. |
| ABS/ASA warping in a cold chamber | **Chamber Heat Soak**: the ABS/ASA Orca profiles pass `CHAMBER_TEMP=45`. With the bed at temperature and the chamber fan held off, START_PRINT waits until the chamber air reaches that. It gives up after 30 minutes so a cold room never blocks a print. PLA/PETG pass 0 and skip it. |
| Printing with filament that was unloaded | **Filament check**: the K1 filament sensor sits before the extruder, so it still reports filament after `UNLOAD_FILAMENT`. `LOAD_FILAMENT`/`UNLOAD_FILAMENT` remember the state, and START_PRINT refuses to start (before heating or homing) until the filament is loaded again. |
| Homing and mesh probes triggering at different heights | The Z homing speed now matches the probe speed. At 1 mm/s vs 5 mm/s they triggered 0.03 mm apart. |
| X-rail wobble | **Axis twist compensation**, measured with nozzle touch against the Microprobe at 7 spots. No paper test. The profile is ±0.035 mm. `AXIS_TWIST_TOUCH_CALIBRATE` repeats it inside Klipper (forced every 300 h). |
| Hotend temperature dips when the fan changes speed | **MPC** (Kalico) instead of PID: 0.5 °C overshoot, ±1.5 °C on a 0→100% fan step. |
| The glass changes how the bed heats | Bed PID retuned at 80 °C with the glass on. The input shaper was re-run too (X 3hump_ei 77.6 Hz, Y ei 52 Hz). |
| Calibrations go stale | **Forced calibration intervals**: print hours are counted, and when a calibration is due it runs automatically before the next print. Input shaper + belt data every 200 h, axis twist (load-cell method, [custom/twist_touch.py](custom/twist_touch.py)) every 300 h, hotend MPC + bed PID every 500 h. Results are used right away where Klipper allows it, and saved (SAVE_CONFIG) automatically ~5 minutes after the print ends. |
| Updates | A **nightly check** writes `UPDATES.md` to the config folder, and there are one-click update macros. See below. |

## Layout

```
tuning.cfg               all the printer-side changes above (included from printer.cfg)
printer.cfg, *.cfg       Pellcorp overrides: only the lines that differ from Pellcorp's files
printer.cfg.save_config  SAVE_CONFIG block: probe offset, input shaper, PID/MPC, meshes
custom/
  mesh_edge_extend.py    Kalico plugin: BED_MESH_EXTEND (Adaptive Mesh Extend)
  twist_touch.py         Kalico plugin: AXIS_TWIST_TOUCH_CALIBRATE (load-cell twist calibration)
  keep_out.py            Kalico plugin: keep-out zones (moves around / refuses moves into them)
  lidar.py               Kalico plugin: LiDAR scans and LiDAR PA calibration
  lidar-start.sh         keeps the LiDAR powered and starts Creality's driver (from k1max-boot.sh)
  k1max-boot.sh          recreates the plugin link and starts cron (runs at boot via S54k1max)
  check-updates.sh       nightly: Pellcorp/Kalico update check -> UPDATES.md
  update.sh              saves overrides (+ git push), updates, re-links, checks Klipper
orcaslicer/              OrcaSlicer 2.4 profiles for this printer (5 nozzles, 59 processes: Balanced everywhere, Precision (10 mm3/s quality cap) and Fast where they make a difference, plus Speed Benchy profiles (0.4: 12:28, 0.8: 9:14, 1.0: 8:45), 12 filaments)
```

## Switches and buttons

**Switches** are in Fluidd's *Outputs* panel. They decide what START_PRINT does and are remembered across restarts (`variables.cfg`).

| Switch | Default | Off means |
|---|---|---|
| `Adaptive_Glass_Soak` | on | no waiting for the glass to settle before the mesh |
| `Nozzle_Deep_Clean` | on | True Zero Touch happens without cleaning the nozzle first |
| `True_Zero_Touch` | on | no load-cell touch: Z comes from the Microprobe (`z_offset` 0.876, measured with the load cells) |
| `Adaptive_Mesh_Extend` | off | (for the old left-side probe mount) extends the mesh to the right bed edge |
| `Chamber_Heat_Soak` | on | ABS/ASA prints start without waiting for the chamber to warm up |
| `Forced_Calibration` | on | due calibrations are not run before prints |

Pellcorp's older **Bed_Warp_Stabilisation** (a fixed timer after the bed reaches temperature) is retired: Adaptive Glass Soak replaces it. `k1max-boot.sh` renames it to `_Bed_Warp_Stabilisation`, which hides it in Fluidd, and keeps it off. It does this at every boot and after every update, because Pellcorp updates restore it.

**Buttons** are in Fluidd's *Macros* panel and on the screen. They always run, whatever the switches say.

| Button | Does |
|---|---|
| `ADAPTIVE_GLASS_SOAK` | heats the bed (`BED_TEMP=`, default the current target or 70 °C) and waits until the glass stops moving |
| `NOZZLE_DEEP_CLEAN` | the nozzle clean on its own |
| `TRUE_ZERO_TOUCH` | Nozzle Deep Clean, then set Z=0 by touching the bed with the nozzle |
| `ADAPTIVE_MESH_EXTEND` | extends the loaded mesh to X 300 with nozzle taps |
| `CHAMBER_HEAT_SOAK` | heats the bed (`BED_TEMP=`, default 100 °C) until the chamber air reaches `TEMP=` (default 45 °C) |
| `CALIBRATION_STATUS` | print hours counted and when each forced calibration is due |
| `CALIBRATE_NEXT_PRINT` | `WHAT=shaper\|twist\|heaters\|all`: marks a calibration as due, so it runs before the next print |
| `BACKUP_TO_GITHUB` | saves the config overrides and pushes them here |
| `PRINTER_CHECK_UPDATES`, `PRINTER_UPDATE_PELLCORP`, `PRINTER_UPDATE_KALICO` | see *Updates* |
| `LIDAR_PA_CALIBRATION` | `EXTRUDER_TEMP=`, `BED_TEMP=` (default 250/70, PETG): prints 9 lines at PA 0.00–0.08 around X 130–154, Y 100–220 (keep that area clear) as a normal print with START_PRINT, scans them with the LiDAR, and applies the PA it measures. Put the result in the filament profile. |

## Updates

- **Every night at 4:00**, the printer checks Pellcorp and Kalico for new commits. Nothing is installed automatically. The result goes to `UPDATES.md`, visible in Fluidd under Configuration, and a message appears when the printer is idle. It also says when a Kalico update includes new MCU firmware (which needs a power cycle).
- **`PRINTER_UPDATE_PELLCORP`** / **`PRINTER_UPDATE_KALICO`**: these refuse to run while printing. Otherwise they save the overrides (committing and pushing them here), update, restore the plugin link, and report whether Klipper came back `ready`. The log is `logs/k1max_update.log`.
- **`PRINTER_CHECK_UPDATES`** runs the check on demand.

## Backups to this repo (from the printer itself)

`/usr/data/pellcorp-overrides` on the printer is a git checkout of this repo. Pellcorp's `CONFIG_OVERRIDES` (also run by the update macros) commits and pushes whenever something changed, so this repo always matches the printer.

The printer pushes with its own **deploy key**, which works for this repo only. K1 firmware ships an old dropbear (2019.78), which has two quirks:

- RSA keys sign with SHA-1, which GitHub rejects for git operations (though `ssh -T` still says hello). Use an **ECDSA** key: `dropbearkey -t ecdsa -s 256 -f /usr/data/.ssh/k1max_github_ecdsa`, then add the public part (`dropbearkey -y -f ...`) under *Settings → Deploy keys* with write access.
- git assumes OpenSSH options that dropbear doesn't understand, so set:
  ```
  git config core.sshCommand "dbclient -i /usr/data/.ssh/k1max_github_ecdsa -y"
  git config ssh.variant simple
  ```

## What you need

- **Simple AF** (Pellcorp) from September 2026 or later, installed with the Microprobe option. This build's `S13mcu_update` can also flash the bed MCU.
- **Kalico instead of Klipper**, on Pellcorp's `aug2026` branch, which has the multi-chip `hx711s` load-cell driver and `register_as_probe: False`:
  ```
  cd /usr/data/pellcorp && sh ./installer.sh --klipper-repo kalico aug2026
  ```
  Then **switch the printer off and on**. That flashes the main, nozzle and bed MCUs (bed firmware `bed0_121` or newer has the HX711 support). Check `/usr/data/mcu.versions` afterwards.
- A **Microprobe V2**. The stock load cells stay in place; they're only used for the nozzle touch.

## Using this on your own K1 / K1 Max

This is one specific printer, so read `tuning.cfg` before copying anything. The values **tied to this hardware** are:

- `[probe]` / Microprobe: `x_offset 0`, `y_offset 20.3`, `z_offset` (SAVE_CONFIG, measure it with the load cells: nozzle contact vs Microprobe at the same spot), `zero_reference_position` (the probe position while homing Z: nozzle 153,153 → 153,173.3), and `mesh_min`/`mesh_max` (the probe's reach)
- `[load_cell_probe]`: the load-cell settings. The leveling board needs Pellcorp's Kalico **bed MCU firmware with HX711 support** (bed0_121 or newer). The pins are the stock K1 ones. `reference_tare_counts` must be measured on your printer (read `force_g` with the bed empty). `counts_per_gram` is Pellcorp's K1 value.
- `[axis_twist_compensation]` values (SAVE_CONFIG block), Adaptive Glass Soak thresholds (`_GLASS_SOAK`), the Nozzle Deep Clean strip location (`_TOUCH_NOZZLE_WIPE`, X 40–100 at Y 298), the `[mesh_edge_extend]` edge positions, and the `[keep_out]` zones (measure your own: they depend on the probe mount)

Rough steps on a Simple AF printer that has Kalico and the load-cell bed firmware:

1. Copy `custom/` to `/usr/data/pellcorp-overrides/custom/` and run `custom/k1max-boot.sh`. This has to come **first**: `tuning.cfg` has `[mesh_edge_extend]` and `[keep_out]` sections, and Klipper won't start until the plugin is linked in.
2. Copy `tuning.cfg` to `printer_data/config/` and add `[include tuning.cfg]` to `printer.cfg`, after the probe includes.
3. Change the hardware-specific values above, restart, then run `CONFIG_OVERRIDES` so updates keep your changes.

## Roadmap

- **Open LiDAR driver.** Today the LiDAR is driven by Creality's closed `cx_ai_middleware`. The plan is to record its serial traffic (strace), document the protocol (frames are `AF FF | len16 | src | cmd | payload | checksum16`), and write a plain Python driver. Open question: the `cx_ai_crypto` handshake that udev runs when the LiDAR is plugged in.
- **LiDAR first-layer check.** The same bare-plate subtraction on a real first layer, which gives the true first-layer thickness and checks True Zero Touch with numbers.
- **LiDAR reports on a helper computer.** A Raspberry Pi (a 4B with 1 GB is enough) could fetch the scans from the printer and draw height maps and history, which is too heavy for the K1 itself.
- **Silicone wipe pads** (K2 Plus) for the Nozzle Deep Clean.

## Known limitations

- The nozzle wipe can still leave a thin string hanging off the side of the nozzle. It doesn't affect the touch (the Microprobe check shows a clean contact), and the purge line picks it up. A silicone brush at the back edge would be the proper fix.
- Adaptive Mesh Extend is off by default (see above).
- The LiDAR position (`[lidar]` x/y offset) was measured with a printed cross for this glass + PEI stack; a different plate height moves the laser spot in Y.
- `counts_per_gram` was not weighed on this printer, so load-cell forces in grams are approximate. The touch height doesn't depend on it.

## OrcaSlicer profiles

`orcaslicer/`: import `K1Max-Tuned-OrcaSlicer-profiles.zip` with *File → Import → Import Configs*, then set your printer's address in the printer profile (Connection). See [orcaslicer/README.md](orcaslicer/README.md) for what's inside and why. They match the printer side: the start G-code is just `START_PRINT` (with the filament's chamber temperature: 45 °C for ABS/ASA), layer progress is reported, object labels are on (for the adaptive mesh), jerk is 0 so the corner velocity the input shaper was tuned for is kept, and arc fitting is off.

## Credits

- [Pellcorp / Simple AF](https://github.com/pellcorp/creality), [Kalico](https://github.com/KalicoCrew/kalico), and Pellcorp's [load-cell work](https://github.com/pellcorp/creality/issues/1500) built on OpenCentauri's hx711s driver
- `mesh_edge_extend.py`, `twist_touch.py` and `keep_out.py` are GPLv3, like Klipper and Kalico

Use at your own risk. This drives a hot nozzle into the bed on purpose.
