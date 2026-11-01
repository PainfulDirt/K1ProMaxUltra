# Toolhead project status (paused 2026-11-01)

Work in progress: nothing here is released for printing except the fit-check coupon.

## Done

- **Phase 1 research:** `documentation/research/01..04`
  - 01: repo, LiDAR and MicroProbe
  - 02: stock mechanics, with the carriage taken from Henlor's reverse-engineered K1 CAD
  - 03: fans; manufacturer curves digitized; sunon.cz and EU sourcing
  - 04: CAD/CFD toolchain and CFD method
- **Phase 2 architecture:** "A+" (`documentation/design-decisions.md`)
  - stock carriage, hotend, extruder, PCB and 3010 are kept;
  - both sensor positions are unchanged;
  - a new cooling module and cover mount on the PCB holes;
  - CFD decides the number of fans.
- **Shared interfaces:** `cad/source/interfaces.py`. Every value carries a VERIFIED / DERIVED /
  ESTIMATED / MISSING status.
- **Structure CAD:** `cad/source/structure/`, with assembly, validation and exports. Validation
  currently gives 0 FAIL / 7 WARN using a stub cooling module.

## In progress (stopped mid-run)

- **CFD comparison and duct optimization:** `cad/source/ducts/`, `simulations/cfd/cases/`,
  `simulations/cfd/results/` and `documentation/cfd-report.md`.
  - Done: one production case, the STOCK baseline with the lower-bound 4020 curve.
    `results/summary.csv` has its numbers.
  - The duct interface (`ducts/duct_interface.json`) is v0 and **not final**. It violates the
    structure-agent mount rules; see `cad/exports/validation_report_ducts.md`.

## Next steps, in order

1. CFD, in this priority:
   1. STOCK with the upper-bound 4020 curve;
   2. S (one 4020, multi-outlet) and D (two blowers);
   3. U-Delta and U-SameSky (CBM-5015BF);
   4. ≥ 3 optimization iterations on the winner;
   5. final mount points;
   6. L2/L3 mesh check;
   7. thermal proxy against STOCK.
2. Switch `COOLING_SOURCE` in `cad/source/assembly.py` once the mount points are final. Then run
   `validate.py` and `export.py`.
3. Design the mounts for the chosen fan's 24→12 V buck converter / MOSFET (DD-05).
4. Documentation: BOM, assembly, print settings, calibration, stock-vs-new comparison.
5. Independent engineering review (Phase 6), then fix its findings.

## Waiting on the user

- The Priority-1 measurements in `documentation/missing-information.md`: LiDAR module (M6), probe
  mount (M8), PCB photos (M10), clearances (M9).
- Print the fit-check coupon: `cad/exports/3mf/fitcheck_coupon.3mf`.
- The fan order waits for the single-vs-dual CFD result. Options are in research/03 §11–12.

## Rebuilding the environment

```bash
sudo bash hardware/toolhead/tools/setup_env.sh      # OpenFOAM v2512, build123d, pyvista, ...
bash hardware/toolhead/tools/setup_env.sh --check
/opt/k1th/venv/bin/python hardware/toolhead/cad/source/validate.py
```
