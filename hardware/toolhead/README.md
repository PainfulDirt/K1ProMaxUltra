# K1 Max toolhead: new part-cooling module (architecture A+)

A replacement for the stock front cover and part-cooling duct of this Creality K1 Max. It keeps
everything that the printer's calibrations depend on: the stock carriage, hotend, extruder, nozzle
PCB, 3010 hotend fan, **the fitted stock 4020 blower**, the LiDAR and the MicroProbe, all in their
current positions. What is new:

- a **cooling-module frame** (ASA) on the nozzle PCB's three screw holes, which carries the 4020
  and the duct;
- the **S7 duct** (PC): a plenum and a horseshoe manifold around the sock, open on the LiDAR side,
  with 5 angled ports just outside a 3 mm sock clearance;
- a light **cover** (ASA) that slides off forward without unplugging anything;
- later, a stiffer **MicroProbe mount** (PA-CF), not released yet.

The electrics are unchanged (stock PB8 / PB6 / PB3). **No printer config file in the repo is
changed by this project.** After fitting, MPC must be re-calibrated (`MPC_CALIBRATE`).

The design is decided (`documentation/design-decisions.md`, DD-01…DD-07). The fan count was decided
by CFD: a second fan failed the DD-01 selection rule, and no fan swap earned a clear margin over
the stock 4020. A Same
Sky CBM-5015BF with a 24→12 V buck is a documented conditional upgrade only.

**Nothing has been printed, fitted or measured yet.** All performance numbers below are simulated
or estimated.

## Status

| Part | File (`cad/exports/{3mf,stl,step}/`) | Material | Mass (100 % infill) | Status |
|---|---|---|---|---|
| Fit-check coupon | `fitcheck_coupon` | ASA | 2.89 g | **PRINT FIRST** |
| Cooling-module frame | `cooling_module_frame` | ASA | 5.84 g | FIT-CHECK FIRST |
| Cover | `cover` | ASA | 6.42 g | FIT-CHECK FIRST |
| Duct body (S7) | `duct_body` | PC (or PA-CF) | 9.24 g | FIT-CHECK FIRST |
| MicroProbe mount | `probe_mount` | PA-CF | 11.45 g | NOT RELEASED (M8) |
| Stock 4020 blower | — (reused) | — | — | unchanged |
| Electrical, printer config | — | — | — | unchanged |

| Work package | State |
|---|---|
| Research (repo, sensors, mechanics, fans, CFD method) | done: `documentation/research/01..04` |
| Architecture and decisions | done: `documentation/design-decisions.md` |
| CFD comparison and duct optimisation | done on the L2 mesh: `documentation/cfd-report.md`. The L3 mesh check of S7 is pending |
| CAD, validation, exports | done: `cad/`; `validate.py` gives **0 FAIL / 4 WARN** (all four accepted, `cad/README.md`) |
| User documentation | done: this page and `documentation/` |
| Measurements from the user | open: `documentation/missing-information.md` (priority 1: M2, M6, M8, M9, M10) |
| Prints, fit checks, physical tests | not started: `documentation/validation.md` §4 |

## Headline results

| Result | Value | Tag | Source |
|---|---|---|---|
| Layer air speed around the nozzle, S7 vs stock duct, same 4020 | 8.84 vs 1.83 m/s (×4.8) at the lower 4020 bound; 13.34 vs 3.47 (×3.8) at the upper | SIMULATED | `cfd-report.md` §10 |
| Weakest of 8 directions | 6.28 vs 0.35 m/s (×18), lower bound | SIMULATED | §10 |
| Part-top heat-transfer coefficient (thermal proxy) | 147 vs 42 W/m²K (×3.5), lower bound | SIMULATED | §11 |
| Price: extra nozzle + sock heat loss at 100 % fan | +6.2 … +6.8 W (about 10 % of the 60 W heater) | SIMULATED (proxy, indicative) | §11 |
| LiDAR window region air speed | 0.17 vs 0.087 m/s (moving downward, away from the windows) | SIMULATED | §13.1 |
| Moving-mass change | −0.6 … +8.4 g | ESTIMATED | `cad/exports/validation_report.md` |
| X / Y input shaper | 76.9 … 77.7 Hz (77.6 today) / 51.8 … 52.0 Hz (52.0 today) | ESTIMATED (today's values MEASURED) | validation report |
| Front extent | −58.2 vs −55.0 for the stock cover (3.2 mm further forward) | DESIGN | validation report |
| CAD checks | 0 FAIL / 4 WARN | GEOMETRIC | validation report |
| Measured performance | none yet | — | `documentation/validation.md` |

Full comparison, row by row with tags: `documentation/stock-vs-new.md`.

## How to proceed

1. **Print and check the fit-check coupon** (ASA, about 10 min): `documentation/print-settings.md`
   §5. It confirms the PCB pads, the insert hole size and the probe seat.
2. **Send the priority-1 measurements** (`documentation/missing-information.md`): M2, M6 (including
   what the LiDAR bracket screws into), M8, M9, M10. Also measure the 4020 (M7): outlet and screw-hole
   through-length set the fan screw length and the duct socket.
3. **Print the fit-check parts**: frame, cover, duct (`documentation/print-settings.md`), and
   assemble with the checks after each step (`documentation/assembly.md`).
4. **Calibrate**: MPC first, then z_offset, LiDAR check, twist, shaper, PA, first layer
   (`documentation/calibration.md`).
5. **Physical tests V1–V8** (`documentation/validation.md` §4): the stock 4020's P–Q curve,
   port and layer air speeds, heater penalty, overhang and bridge prints, LiDAR windows, thermal soak.
   V1 and V5/V6 together decide whether the Same Sky upgrade is worth it.

## Documentation

| File | Content |
|---|---|
| [`documentation/assembly.md`](documentation/assembly.md) | step-by-step assembly, checks after each step, disassembly and rollback |
| [`documentation/bill-of-materials.md`](documentation/bill-of-materials.md) | printed parts, screws, inserts, tools; the conditional Same Sky upgrade |
| [`documentation/print-settings.md`](documentation/print-settings.md) | per-part print settings, PC / PA-CF profiles, heat-set inserts, drying, the coupon procedure |
| [`documentation/calibration.md`](documentation/calibration.md) | post-install calibration with pass criteria; rollback; the proposed fan-off rule for LiDAR scans |
| [`documentation/electrical.md`](documentation/electrical.md) | the part-fan channel (unchanged); the Same Sky + buck upgrade path; PB6 probing |
| [`documentation/maintenance.md`](documentation/maintenance.md) | opening the toolhead, duct removal, nozzle change, cleaning, inspection intervals |
| [`documentation/validation.md`](documentation/validation.md) | what is simulated, checked in CAD, estimated, and what still has to be tested |
| [`documentation/stock-vs-new.md`](documentation/stock-vs-new.md) | stock vs new, every row tagged MEASURED / SIMULATED / ESTIMATED / DESIGN |
| [`documentation/design-decisions.md`](documentation/design-decisions.md) | DD-01…DD-07: architecture, LiDAR, probe, hotend fan, fan count, CFD method, materials |
| [`documentation/cfd-report.md`](documentation/cfd-report.md) | the CFD campaign: method, candidates, iterations, final S7, mesh/domain checks, test plan |
| [`documentation/missing-information.md`](documentation/missing-information.md) | what the user still has to measure (M#) |
| [`documentation/research/`](documentation/research/) | 01 repo and sensors, 02 mechanical interfaces, 03 fans and cooling, 04 toolchain and CFD method |
| [`cad/README.md`](cad/README.md) | CAD structure, parameters, release rule, accepted WARNs, CAD-side BOM |
| [`cad/exports/validation_report.md`](cad/exports/validation_report.md) | current CAD checks, masses, shaper estimate, dependencies per part |
| [`STATUS.md`](STATUS.md) | session snapshot from 2026-11-01 (before the CFD result); superseded by this page |

## Folders

| Folder | Content |
|---|---|
| `cad/source/` | build123d sources: `interfaces.py` (shared values with VERIFIED / DERIVED / ESTIMATED / MISSING tags), `structure/` (frame, cover, probe mount, coupon, references, stiffness), `ducts/` (S7 generator and its `duct_interface.json`), `assembly.py`, `validate.py`, `export.py` |
| `cad/exports/` | `3mf/`, `stl/`, `step/` per part plus the assembly STEP; `validation_report.{md,json}`, `export_manifest.json` |
| `simulations/cfd/` | `pipeline/` (OpenFOAM case builder and post-processing), `cases/` (case driver, stock geometry, summaries), `validation/` (pipeline validation case), `results/` (one folder per case with `results.json` and figures; `summary.{csv,json}`) |
| `components/fans/` | fan P–Q curves (`pq-curves/`), `operating_point.py`, example Kalico snippets (`klipper/`, not active) |
| `documentation/` | everything a user needs (table above) |
| `tools/` | `setup_env.sh` (toolchain install), lock files, `cad_selftest.py` |

## Rebuild and validate

From the repository root:

```bash
sudo bash hardware/toolhead/tools/setup_env.sh          # once: OpenFOAM v2512, build123d venv in /opt/k1th
bash hardware/toolhead/tools/setup_env.sh --check       # verify the toolchain

/opt/k1th/venv/bin/python hardware/toolhead/cad/source/validate.py   # ~1.5 min -> cad/exports/validation_report.{md,json}; exit 1 on FAIL
/opt/k1th/venv/bin/python hardware/toolhead/cad/source/export.py     # STEP / 3MF / STL + assembly STEP, re-opened and verified

source /opt/k1th/env.sh                                  # sets $K1_PY and FOAM_BASHRC
cd hardware/toolhead/simulations/cfd/cases
$K1_PY run_cases.py S7:part:proxy                        # one CFD case, L2 mesh, 4 ranks (about 16–34 min)
$K1_PY run_cases.py S7:part:proxy --level 3              # the pending L3 mesh check
```

- `validate.py --cooling ducts` checks against the duct interface explicitly (identical while the
  interface is final). `--no-stock-cache` uses the interface boxes instead of the Henlor stock
  solids; the solids cache is optional and generated once with `cad/source/structure/stock_cache.py`
  (`cad/README.md`).
- CFD case syntax, thermal restarts and fan swaps: `documentation/cfd-report.md` §1.
- After any CAD change: `validate.py`, then `export.py`, then update the masses and statuses in
  `documentation/bill-of-materials.md` and `print-settings.md`.

## Open points

- Priority-1 measurements (M2, M6, M8, M9, M10) and the 4020's dimensions (M7).
- The cover's front wall sits 0.5 mm in front of the fan face where the fan screw heads are;
  screw heads are not modelled in `validate.py` (`documentation/assembly.md` step 7).
- The duct's own stiffness is not estimated (`documentation/validation.md` §2.4).
- The S7 L3 mesh result (`cfd-report.md` §13.2).
- No print or physical test yet (`documentation/validation.md` §4).
