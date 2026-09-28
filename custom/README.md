# custom/

Things that live outside `printer_data` and are recreated by `k1max-boot.sh`
(run at every boot from `/etc/init.d/S54k1max`, before Klipper starts, and
after every update):

| File | What it does |
|---|---|
| `mesh_edge_extend.py` | Kalico plugin providing `BED_MESH_EXTEND`; linked into `klipper/klippy/plugins/` |
| `k1max-boot.sh` | recreates the plugin link and `/etc/init.d/S54k1max`, installs the crontab, starts `crond` |
| `S54k1max` | the init script itself (copied to `/etc/init.d/`) |
| `crontab` | runs `check-updates.sh` every night at 4:00 |
| `check-updates.sh` | checks Pellcorp and Kalico for new commits and writes `UPDATES.md` to the config folder (installs nothing) |
| `update.sh` | backs up overrides (and pushes to GitHub), updates Pellcorp or Kalico, re-links, checks Klipper is `ready`; used by the `PRINTER_UPDATE_*` macros |
