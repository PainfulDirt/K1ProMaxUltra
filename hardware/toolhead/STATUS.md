# Toolhead project status (2026-11-12)

The design is complete in CAD and CFD, and the Phase 6 review findings are worked in. The released
duct is **S8**. **Nothing is released for printing except the fit-check coupon.** No part has been
printed and nothing has been measured on the printer yet. Start at [README.md](README.md).

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
- **CFD and duct optimization:** `documentation/cfd-report.md` (§0 summary, §17 review round); all runs
  in `simulations/cfd/results/`
  - **Decision: one stock 4020 (the fitted one) with the S8 multi-port duct.** Rejected: a second
    fan, the Delta and the owned Sunon. The Same Sky 5015 is not buildable in this frame/cover
    architecture (`cfd-report.md` §17.8).
  - S8 vs the stock duct with the same fan, STOCK re-run in the same round with the same settings, at
    the lower (conservative) 4020 bound, 20 mm part proxy, steady RANS k-ω SST (SIMULATED):
    - layer air speed ×4.4 (×4.3–5.3 over the robustness checks of §17.5; ×4.2 at the upper bound);
    - weakest of 8 sectors ×15 (×12–30, "an order of magnitude": the least repeatable metric);
    - part top near-wall speed ×4.5 (×4.5–5.8);
    - every side face of the part above stock (lowest: the −Y face, ×2.0–2.5);
    - thermal proxy with a closed energy balance (−0.03 % / −0.5 %): part-top h ×3.3, heat removed
      from the part ×2.0.
  - Price: about +7.6 W heater demand at 100 % fan (nozzle +3.1 W, sock +4.5 W at an ESTIMATED 150 °C
    sock surface). `MPC_CALIBRATE` is mandatory after fitting.
  - The S7 first-round claims (×4.8, ×14–18, ×3.5 h, +6 W) are superseded. S7's thermal W values came
    from an unclosed energy balance and are withdrawn.
- **Phase 6 independent review:** `documentation/review/phase6-review.md` (1 critical, 12 major,
  12 minor, 4 notes). Done, and its fixes are integrated: rear footprint (S8 ends at Y +9.8), flat
  base, real 4020 solid and four-sided socket, blind insert holes, brass compression sleeves, a third
  duct tab, robustness CFD runs, closed thermal balance, DD-07 by HDT, quantitative V8, mandatory
  rear keep-out jog. The per-finding status is in the review's "Resolution status" table. Open: what
  waits for measurements or the user (M7, M10, M11, M20; the 785004 reprint), the tagging clean-up in
  `interfaces.py` (R-19), and two small leftovers (R-26 cache default, R-28 research/04 heading).
  Count: 21 fixed, 6 partly, 2 user.
- **CAD integrated with the S8 duct:** `cad/`
  - `validate.py`: **0 FAIL / 7 WARN**, the 7 WARNs explained in `cad/README.md`
    (`cad/exports/validation_report.md`);
  - exports in `cad/exports/` verified;
  - masses at 100 % infill: frame 6.64 g ASA, cover 6.34 g ASA, duct 9.4 g (HT resin, PC density
    1.20 as a placeholder), probe mount 11.45 g PA-CF, coupon 2.99 g ASA;
  - moving mass +3.1 … +12.0 g vs stock, counting the new probe mount in place of the 785004 (about
    0.6–0.9 g less while the 785004 stays); X shaper 76.6 … 77.3 Hz (77.6 today), Y 51.6 … 51.9 Hz
    (52.0 today). All ESTIMATED.
- **Documentation:** in `documentation/`
  - BOM, electrical (no change for the baseline), calibration, print settings, maintenance;
  - assembly, validation, stock-vs-new.

## Next steps, in order

1. **User:** print the fit-check coupon (`cad/exports/3mf/fitcheck_coupon.3mf`) and check it as
   described in `documentation/print-settings.md` §5.
2. **User:** the Priority-1 measurements in `documentation/missing-information.md`:
   - M2 (confirmation), M6 (LiDAR, including where its bracket is fixed), M8 (probe mount), M9
     (clearances), M10 (PCB), M11 (curl and snag clearance);
   - M7 (4020 outlet, hole positions, hole type and through-length): it decides the fan screw length
     and the hole-vs-outlet contradiction.
3. Update `interfaces.py` with the measurements, re-run `validate.py` and `export.py`, and release
   the parts that become fully confirmed.
4. **User:** order the duct, two pieces in HT resin (238 °C class, full thermal post-cure) from a
   print service (`documentation/print-settings.md`, DD-07a), and buy the hardware
   (`documentation/bill-of-materials.md`): M3 washers, seal foam or Kapton tape, the BT4M brass tube.
   Reprint the 785004 probe adapter in ASA, PC or PA-CF (R-27).
5. Print the frame and cover (ASA), fit everything (`documentation/assembly.md`) and run
   `calibration.md`. The rear keep-out jog (D.4) and `MPC_CALIBRATE` (E) are mandatory.
6. After the first 10 hot hours: torque and crack audit of the resin tabs and the frame
   (`documentation/maintenance.md` §5).
7. Physical tests V1–V8 (`documentation/validation.md` §4). V1, the 4020 fan curve, needs a spare
   4020. V8 with M20 decides the resin's heat margin.

## Decisions taken by the user

- Duct body material: **HT resin** (238 °C class, full thermal post-cure), from a print service,
  two pieces (`design-decisions.md` DD-07a). PC or MJF PA12 are the fallbacks.

## Open decisions for the user

- Optional purchase: one spare Creality 4020 (4004110132) for V1 and M7.
- "Part fan off during LiDAR scans" is proposed, not applied, because it changes printer config
  (`calibration.md` §6).
- Slicer fan percentages after fitting (`calibration.md` L): a slicer-profile change.
- `DUCT_MIN_Z = 2.4` in `interfaces.py` (`cfd-report.md` §16 R7): requested, not applied, because
  `duct_generator.py` builds S8 from the current value.

## Rebuilding the environment

```bash
sudo bash hardware/toolhead/tools/setup_env.sh      # OpenFOAM v2512, build123d, pyvista, ...
bash hardware/toolhead/tools/setup_env.sh --check
/opt/k1th/venv/bin/python hardware/toolhead/cad/source/validate.py
```
