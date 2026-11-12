# Toolhead project status (2026-11-12)

The design is complete in CAD and CFD. **Nothing is released for printing except the fit-check
coupon.** No part has been printed and nothing has been measured on the printer yet. Start at
[README.md](README.md).

## Done

- **Phase 1 research:** `documentation/research/01..04`
  - 01: repo, LiDAR and MicroProbe
  - 02: stock mechanics, with the carriage taken from Henlor's reverse-engineered K1 CAD
  - 03: fans; manufacturer curves digitized; sunon.cz and EU sourcing
  - 04: CAD/CFD toolchain and CFD method
- **Phase 2 architecture:** "A+" (`documentation/design-decisions.md`)
  - stock carriage, hotend, extruder, PCB and 3010 are kept;
  - both sensor positions are unchanged;
  - a new cooling module and cover mount on the PCB holes.
- **CFD and duct optimization:** `documentation/cfd-report.md`; all runs in `simulations/cfd/results/`
  - **Decision: one stock 4020 (the fitted one) with the S7 multi-port duct.** Rejected: a second
    fan, the Delta and the owned Sunon. The Same Sky 5015 is a conditional upgrade.
  - S7 vs the stock duct with the same fan:
    - layer air speed ×4.8;
    - weakest sector ×14–18;
    - part-top heat transfer ×3.5 (thermal proxy).
  - Price: about +6 W nozzle and sock heat loss at 100 % fan (ESTIMATED from the proxy).
  - Mesh check L1/L2/L3: the means are converged. The weakest sector is not (±27 %).
- **CAD integrated with the final duct:** `cad/`
  - `validate.py`: 0 FAIL / 4 WARN, with the 4 WARNs explained in `cad/README.md`;
  - exports in `cad/exports/` verified.
  - Moving mass −0.7 … +8.3 g vs stock; X shaper 76.9 … 77.7 Hz (77.6 today). Both ESTIMATED.
- **Documentation:** in `documentation/`
  - BOM, electrical (no change for the baseline), calibration, print settings, maintenance;
  - assembly, validation, stock-vs-new.

## Next steps, in order

1. **Phase 6:** an independent engineering review, then fix its findings.
2. **User:** print the fit-check coupon (`cad/exports/3mf/fitcheck_coupon.3mf`) and check it as
   described in `documentation/assembly.md`.
3. **User:** the Priority-1 measurements in `documentation/missing-information.md`:
   - M2 (confirmation), M6 (LiDAR, including where its bracket is fixed), M8 (probe mount), M9
     (clearances), M10 (PCB);
   - M7 (4020 outlet, hole through-length).
4. Update `interfaces.py` with the measurements, re-run `validate.py` and `export.py`, and release
   the parts that become fully confirmed.
5. Print the frame, cover and duct (PC/PA-CF), fit them, and run `calibration.md`. `MPC_CALIBRATE`
   is mandatory.
6. Physical tests V1–V8 (`cfd-report.md` §15). V1, the 4020 fan curve, needs a spare 4020.

## Open decisions for the user

- Optional purchase: one spare Creality 4020 (4004110132) for V1.
- "Part fan off during LiDAR scans" is proposed, not applied, because it changes printer config
  (`calibration.md` §6).

## Rebuilding the environment

```bash
sudo bash hardware/toolhead/tools/setup_env.sh      # OpenFOAM v2512, build123d, pyvista, ...
bash hardware/toolhead/tools/setup_env.sh --check
/opt/k1th/venv/bin/python hardware/toolhead/cad/source/validate.py
```
