# Third-party geometry in this folder

These are the stock Creality K1 cover and duct, used only as the STOCK baseline in the CFD
comparison. They are not printable parts of this project and are not in `cad/exports/`.

| File | Derived from | Author | Licence |
|---|---|---|---|
| `stock_duct.step.gz` | "Creality K1 Assembly CAD Model", https://www.printables.com/model/742370-creality-k1-assembly-cad-model (STEP 2024-02-12); the duct solid, moved to the nozzle frame (tip at the origin) | Henlor | CC BY 4.0 (Attribution) |
| `stock_cover.step.gz` | the same model's cover, and "Creality K1 toolhead cover", https://www.printables.com/model/687411 | Henlor | CC BY 4.0 (742370) / CC0 (687411) |

Henlor labels the model "non-official, reverse engineered, some inaccuracies". It is a K1, not a
K1 Max. The transform into the nozzle frame is in `stock_geometry.py`
(`documentation/research/02-mechanical-interfaces.md` §9).

Changes: only the coordinate transform and the selection of solids. The geometry itself is
unmodified.
