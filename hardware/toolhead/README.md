# K1 Max toolhead: new part-cooling module (architecture A+)

A replacement for the stock front cover and part-cooling duct of this Creality K1 Max. It keeps
everything that the printer's calibrations depend on: the stock carriage, hotend, extruder, nozzle
PCB, 3010 hotend fan, **the fitted stock 4020 blower**, the LiDAR and the MicroProbe, all in their
current positions. What is new:

- a **cooling-module frame** (ASA) on the nozzle PCB's three screw holes, which carries the 4020
  and the duct;
- the **S8 duct** (HT resin from a print service, DD-07a): a plenum and a horseshoe manifold around
  the sock, open on the LiDAR side, with 4 angled ports 4.54 mm from the sock, a flat base at 3.0 mm
  above the nozzle tip, and nothing behind Y +9.8;
- a light **cover** (ASA) that slides off forward without unplugging anything;
- later, a stiffer **MicroProbe mount** (PA-CF), not released yet.

The electrics are unchanged (stock PB8 / PB6 / PB3). **No printer config file in the repo is
changed by this project.** After fitting, MPC must be re-calibrated (`MPC_CALIBRATE`).

The design is decided (`documentation/design-decisions.md`, DD-01…DD-07a). The fan count was decided
by CFD: a second fan failed the DD-01 selection rule, and no fan swap earned a clear margin over
the stock 4020. The Same Sky CBM-5015BF, the only fan with a usable margin, does not fit this
frame/cover architecture (`cfd-report.md` §17.8). The Phase 6 independent review is done and its
fixes are integrated (`documentation/review/phase6-review.md`, "Resolution status").

**Nothing has been printed, fitted or measured yet.** All performance numbers below are simulated
or estimated.

## Status

| Part | File (`cad/exports/{3mf,stl,step}/`) | Material | Mass (100 % infill) | Status |
|---|---|---|---|---|
| Fit-check coupon | `fitcheck_coupon` | ASA | 2.99 g | **PRINT FIRST** |
| Cooling-module frame | `cooling_module_frame` | ASA | 6.64 g | FIT-CHECK FIRST |
| Cover | `cover` | ASA | 6.34 g | FIT-CHECK FIRST |
| Duct body (S8) | `duct_body` | HT resin, 238 °C class, from a print service, 2 pieces (DD-07a); fallbacks PC, MJF PA12 | 9.4 g (PC density 1.20 as a placeholder) | FIT-CHECK FIRST |
| MicroProbe mount | `probe_mount` | PA-CF | 11.45 g | NOT RELEASED (M8) |
| Stock 4020 blower | — (reused) | — | — | unchanged |
| Electrical, printer config | — | — | — | unchanged |

| Work package | State |
|---|---|
| Research (repo, sensors, mechanics, fans, CFD method) | done: `documentation/research/01..04` |
| Architecture and decisions | done: `documentation/design-decisions.md` |
| CFD comparison and duct optimisation | done: first round S1–S7 (§5–§16), review round S8 with laminar, L3, plate, probe-body, skewed-inlet and long-average checks and a closed thermal balance (§17): `documentation/cfd-report.md` |
| Phase 6 independent review | done, fixes integrated: `documentation/review/phase6-review.md` |
| CAD, validation, exports | done: `cad/`; `validate.py` gives **0 FAIL / 7 WARN** (all seven accepted, `cad/README.md`) |
| User documentation | done: this page and `documentation/` |
| Measurements from the user | open: `documentation/missing-information.md` (priority 1: M2, M6, M7, M8, M9, M10, M11) |
| Prints, fit checks, physical tests | not started: `documentation/validation.md` §4 |

## Headline results

S8 against the stock duct with the same 4020, at the lower (conservative) 4020 bound, on a 20 mm
part proxy, steady RANS k-ω SST on the L2 mesh, with STOCK re-run in the same round and the same
settings. The bracketed spread is over the robustness checks of `cfd-report.md` §17.5 (laminar, L3
mesh, 120 mm plate, probe body as a wall, skewed fan outlet, long averaging window).

| Result | Value | Tag | Source |
|---|---|---|---|
| Layer air speed around the nozzle (annulus r 1–6 mm, 0.5 mm above the part) | 9.38 vs 2.12 m/s: **×4.4** (×4.3–5.3); ×4.2 at the upper 4020 bound | SIMULATED | `cfd-report.md` §0, §17.5 |
| Weakest of 8 directions | 5.51 vs 0.36 m/s: ×15 (×12–30). Quote it only as "an order of magnitude": the least repeatable metric | SIMULATED | §17.5 |
| Part top, near-wall speed r ≤ 5 | 7.53 vs 1.68 m/s: ×4.5 (×4.5–5.8) | SIMULATED | §17.5 |
| Part side faces −X / +X / −Y / +Y | every face above stock: ×5.8 / ×12 / ×2.0 / ×4.4 (−Y ×2.0–2.5 in every variant). Per-face values are known to about a factor of 2 | SIMULATED | §17.6 |
| Part-top heat-transfer coefficient (thermal proxy, energy balance closed to −0.03 % / −0.5 %) | 134 vs 40 W/m²K (×3.3); heat removed from the part 20.9 vs 10.4 W (×2.0) | SIMULATED (proxy) | §17.7 |
| Price: extra heater demand at 100 % fan | about +7.6 W (nozzle +3.1, sock +4.5 at an ESTIMATED 150 °C sock surface), about 13 % of the 60 W heater | SIMULATED (proxy) + ESTIMATED sock temperature | §17.7 |
| LiDAR, fan 100 %, upper 4020 bound, nozzle 3 mm above a bare bed | laser line 0.041 vs 0.18 m/s mean (less than stock); window region 0.17 vs 0.087 m/s mean | SIMULATED | §13.1 |
| Moving-mass change | +3.1 … +12.0 g, assuming the new probe mount replaces the 785004 adapter; with the 785004 kept (the baseline until M8) about 0.6–0.9 g less | ESTIMATED | `cad/exports/validation_report.md` |
| X / Y input shaper | 76.6 … 77.3 Hz (77.6 today) / 51.6 … 51.9 Hz (52.0 today) | ESTIMATED (today's values MEASURED) | validation report |
| Duct pitch mode on its three tabs | 1530 … 2742 Hz (rigid duct; E = 2200 MPa placeholder until the resin TDS is known) | ESTIMATED | validation report |
| Front extent | −58.2 vs −55.0 for the stock cover (3.2 mm further forward) | DESIGN | validation report |
| Duct to sock / duct lowest point above the tip | 4.54 mm / 3.0 mm (flat base) | DESIGN | validation report |
| CAD checks | 0 FAIL / 7 WARN | GEOMETRIC | validation report |
| Measured performance | none yet | — | `documentation/validation.md` |

The S7 first-round numbers (×4.8, ×14–18, ×3.5 h, +6.2 W) are superseded and S7's thermal W values
are withdrawn (`cfd-report.md` §17.5, §17.7).

Full comparison, row by row with tags: `documentation/stock-vs-new.md`.

## How to proceed

1. **Print and check the fit-check coupon** (ASA, about 10 min): `documentation/print-settings.md`
   §5. It confirms the PCB pads, the insert hole size and the probe seat.
2. **Send the priority-1 measurements** (`documentation/missing-information.md`): M2, M6 (including
   what the LiDAR bracket screws into), M8, M9, M10, M11. Also measure the 4020 (M7): its outlet, hole
   positions, hole type and through-length set the fan screw length and resolve the hole-vs-outlet
   contradiction in the CAD.
3. **Order and print the fit-check parts**: the duct in HT resin from a print service (two pieces),
   the frame and cover in ASA (`documentation/print-settings.md`). Buy the hardware
   (`documentation/bill-of-materials.md`). Assemble with the checks after each step
   (`documentation/assembly.md`).
4. **Calibrate**: clearances and the rear keep-out jog, MPC, then z_offset, LiDAR check, twist,
   shaper, PA, first layer, slicer fan percentages (`documentation/calibration.md`).
5. **Audit after the first 10 hot hours**: resin tabs and frame screws (`documentation/maintenance.md`
   §5).
6. **Physical tests V1–V8** (`documentation/validation.md` §4): the stock 4020's P–Q curve, the
   socket seal and port speeds, the layer air speed per face, heater penalty, overhang and bridge
   prints, LiDAR windows, thermal soak. V8 with M20 decides the resin's heat margin.

## Documentation

| File | Content |
|---|---|
| [`documentation/assembly.md`](documentation/assembly.md) | step-by-step assembly, checks after each step, disassembly and rollback |
| [`documentation/bill-of-materials.md`](documentation/bill-of-materials.md) | printed parts, the resin duct order, screws, washers, inserts, sleeves, seal, tools; the Same Sky option (not buildable as modelled) |
| [`documentation/print-settings.md`](documentation/print-settings.md) | the HT-resin duct order, per-part FDM settings (FDM duct only as a fallback), PC / PA-CF profiles, heat-set inserts, drying, the coupon procedure |
| [`documentation/calibration.md`](documentation/calibration.md) | post-install calibration with pass criteria; rollback; the proposed fan-off rule for LiDAR scans |
| [`documentation/electrical.md`](documentation/electrical.md) | the part-fan channel (unchanged); the Same Sky + buck path (not buildable as modelled, kept as a record); PB6 probing |
| [`documentation/maintenance.md`](documentation/maintenance.md) | opening the toolhead, duct removal, nozzle change, cleaning, inspection intervals |
| [`documentation/validation.md`](documentation/validation.md) | what is simulated, checked in CAD, estimated, and what still has to be tested |
| [`documentation/stock-vs-new.md`](documentation/stock-vs-new.md) | stock vs new, every row tagged MEASURED / SIMULATED / ESTIMATED / DESIGN |
| [`documentation/design-decisions.md`](documentation/design-decisions.md) | DD-01…DD-07a: architecture, LiDAR, probe, hotend fan, fan count, CFD method, materials, the HT-resin duct |
| [`documentation/cfd-report.md`](documentation/cfd-report.md) | the CFD campaign: method, candidates, the first round to S7, the review round to the released S8 (§17), mesh/domain checks, test plan |
| [`documentation/review/phase6-review.md`](documentation/review/phase6-review.md) | the Phase 6 independent review (R-01…R-29) and its resolution status |
| [`documentation/missing-information.md`](documentation/missing-information.md) | what the user still has to measure (M#) |
| [`documentation/research/`](documentation/research/) | 01 repo and sensors, 02 mechanical interfaces, 03 fans and cooling, 04 toolchain and CFD method |
| [`cad/README.md`](cad/README.md) | CAD structure, parameters, release rule, accepted WARNs, CAD-side BOM |
| [`cad/exports/validation_report.md`](cad/exports/validation_report.md) | current CAD checks, masses, shaper estimate, dependencies per part |
| [`STATUS.md`](STATUS.md) | current state, next steps and open decisions |

## Folders

| Folder | Content |
|---|---|
| `cad/source/` | build123d sources: `interfaces.py` (shared values with VERIFIED / DERIVED / ESTIMATED / MISSING tags), `structure/` (frame, cover, probe mount, coupon, references, stiffness), `ducts/` (duct generator, released set S8, and its `duct_interface.json` v4-final), `assembly.py`, `validate.py`, `export.py` |
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
$K1_PY run_cases.py S8:part:proxy                        # one CFD case, L2 mesh, 4 ranks (about 16–34 min)
$K1_PY run_cases.py S8:part:proxy --level 3              # the L3 mesh check (about 50 min)
```

- `validate.py --cooling ducts` checks against the duct interface explicitly (identical while the
  interface is final). `--no-stock-cache` uses the interface boxes instead of the Henlor stock
  solids; the solids cache is optional and generated once with `cad/source/structure/stock_cache.py`
  (`cad/README.md`).
- CFD case syntax, thermal restarts and fan swaps: `documentation/cfd-report.md` §1.
- After any CAD change: `validate.py`, then `export.py`, then update the masses and statuses in
  `documentation/bill-of-materials.md` and `print-settings.md`.

## Open points

- Priority-1 measurements (M2, M6, M7, M8, M9, M10, M11). M7 decides the fan screw length and the
  hole-vs-outlet contradiction; M20 (sock temperature) decides the resin's heat margin.
- The duct's own bending is not estimated: the pitch-mode estimate assumes a rigid duct, and its
  modulus is a placeholder until the resin TDS is known (`documentation/validation.md` §2.4).
- The fan socket needs a seal (Kapton tape or thin foam): unsealed, its 0.25 mm slots leak about 11 %
  of the fan flow (ESTIMATED, `cfd-report.md` §17.9).
- No print or physical test yet (`documentation/validation.md` §4).
