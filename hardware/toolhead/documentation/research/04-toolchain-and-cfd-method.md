# 04 – CAD/CFD toolchain and CFD methodology for part-cooling ducts

Owner: Agent 4 (CFD & CAD toolchain). Status: toolchain installed and validated; methodology defined.
Legend used throughout: **[RAN]** = actually executed in this container, numbers are measured.
**[PROPOSED]** = method defined but not yet executed.

> **Airflow ≠ cooling performance.** Everything validated here is an *isothermal airflow*
> simulation. It tells us how much air a duct delivers, where it goes and how fast it is
> moving. It does not tell us how fast the printed plastic cools. Velocity near the part
> is a reasonable proxy for convective cooling only when we compare similar geometries;
> see §9 for the thermal extension and what each option can and cannot prove.

---

## 1. Software stack (installed by `hardware/toolhead/tools/setup_env.sh`) [RAN]

| Component | Version | Source / how | Notes |
|---|---|---|---|
| OS | Ubuntu 24.04.5 (noble), 4 cores, 15 GB RAM | – | Runs as root, so OpenMPI needs `OMPI_ALLOW_RUN_AS_ROOT=1` |
| **OpenFOAM (ESI / openfoam.com)** | **v2512** (deb `openfoam2512 2512.0-2`) | Official openfoam.com apt repo, via its SourceForge mirror (`downloads.sourceforge.net/project/openfoam/repos/deb`). The `.deb`s are SHA256-pinned in the setup script. | `dl.openfoam.com` and `openfoam.org` are blocked by the egress proxy (HTTP 403), so the repo **GPG key could not be fetched** and the signature was **not verified**. Integrity rests on TLS to sourceforge.net, the `InRelease`→`Packages`→`.deb` hash chain, and the pinned hashes. Ships snappyHexMesh, **cfMesh** (`cartesianMesh`), working **scotch**, and the **`fanPressure`** BC. |
| ~~Ubuntu `openfoam` 1912~~ | v1912 (universe) | apt | **Rejected and purged.** In this build *every* function object aborts with `error in IOstream "sha1"` (so no residual or flow monitoring, no wallShearStress or yPlus), and `libscotchDecomp` is a dummy stub. |
| gmsh | 4.12.1 (apt), 4.15.2 (pip `gmsh` module) | apt + venv | Alternative mesher for STL→volume (tet/hybrid); not used by the pipeline yet |
| Python venv `/opt/k1th/venv` | CPython 3.13.17 (uv 0.11.32) | `uv venv` + `requirements-k1th.lock.txt` (exact pins) | – |
| build123d | 0.13.0 on OCP 8.0.1.1 (`cadquery-ocp-novtk`) | pip | **Primary parametric CAD kernel** |
| CadQuery | 2.7.0 on OCP 7.8.1.1 | separate venv `/opt/k1th/venv-cq` (`--with-cadquery`) | Its OCP 7.8 pin conflicts with build123d's OCP 8.0, so it gets its own venv |
| trimesh / lib3mf | 5.2.0 / 2.5.0 | pip | STL checks, 3MF |
| pyvista / VTK | 0.49.2 / 9.7.1 | pip | Headless offscreen rendering works (OSMesa/Mesa fallback, no X needed); reads OpenFOAM cases directly |
| matplotlib, numpy, scipy | 3.11.2, 2.5.4, 1.18.1 | pip | 2-D plots and integration |
| OpenSCAD | 2021.01 | apt | Headless `openscad -o x.stl x.scad` verified |
| FreeCAD | 1.0.2 (AppImage, extracted) | GitHub release, SHA256-pinned (`--with-freecad`, ~3 GB extracted) | Headless `freecadcmd` verified (reads STEP) |
| xvfb, libosmesa6 | Ubuntu | apt | Not strictly needed; offscreen VTK works without them |

CAD self-test (`tools/cad_selftest.py`) [RAN], all PASS:
- A filleted block (r = 3 mm vertical edges) with a Ø6 through-channel; `is_valid`; 11 faces; V = 10 753.142 mm³.
- Export to STEP, STL and 3MF (build123d `Mesher`).
- STEP round-trip: dV/V = 2e-15 and dBBox = 0.
- 3MF round-trip: dV/V = 2.8e-5 (tessellation), dBBox = 0.
- STL is watertight per trimesh.
- Interference detection: two boxes with 1 mm overlap give an intersection volume of 100.000 mm³ (expected 100). Boxes with a 0.5 mm gap give an empty intersection, and `distance_to` = 0.500 mm. This means clearance checks between toolhead parts can be scripted with `(a & b).volume` and `a.distance_to(b)`.

## 2. Why steady, incompressible RANS with k-ω SST

| Quantity | Value | Consequence |
|---|---|---|
| Jet speeds at duct exits | 5–15 m/s (validation: 11–17 m/s) | Ma = U/c ≤ 15/349 = **0.043 ≪ 0.3**, so density changes from flow are < 0.1 % and **incompressible** is justified |
| Slot 2×20 mm, D_h = 3.64 mm | Re_Dh = U·D_h/ν = 1 100 (5 m/s) … 3 400 (15 m/s); Re_h (slot height) = 625…1 875 | **Laminar–transitional** range (ν = 1.6e-5 m²/s, air at about 30 °C) |
| Duct body 15×20 mm, D_h = 17.1 mm | Re = 1 600 (Q = 0.45 L/s) … 3 600 (Q = 1 L/s) | Transitional |
| Nozzle Ø6 in cross-flow | Re_D = 1 100 … 3 750 | Subcritical bluff body with an unsteady wake |
| Fan outlet | Blower discharge carries high turbulence intensity (O(5–10 %)) and large-scale unsteadiness | Supports a turbulence model despite the modest Re |

Rationale:
- **Steady RANS** is the only option that fits "many duct iterations on 4 cores". A RANS case costs minutes. LES/DES of a slot jet would need roughly 10–100× the cells and time-accurate runs (hours to days).
- **k-ω SST** is the industry default for internal duct flow, separation and impinging jets. It integrates to the wall (ω-equation) or blends with wall functions, and it is less sensitive to free-stream values than k-ω. It is used with `nutUSpaldingWallFunction`, a continuous law of the wall that is valid from y+ ≈ 1 to y+ ≈ 100+, so the mesh-dependent y+ that snappy meshes produce is tolerated.
- **Honest limitation:** at Re of 10³ we are in the regime where RANS is least trustworthy. SST without a transition model assumes fully turbulent flow, so it **over-predicts jet spreading and mixing** and under-predicts the jet's potential-core length. Absolute velocities at the target are therefore uncertain (expect ±20–30 %). **Ranking** of duct variants with the same setup is far more reliable than absolute numbers, and that is how we use it. A laminar run (`--set solver.turbulence=laminar`) is a cheap bracketing check for any final design. If the two models disagree on the ranking, that is a red flag.
- Air is treated as an isothermal Newtonian fluid with ν = 1.6e-5 m²/s and ρ = 1.16 kg/m³ (30 °C). For a 45 °C enclosed chamber use ν = 1.75e-5 and ρ = 1.11 (`fluid` block in the config).

## 3. Fan modelling

- **P–Q curve BC [RAN]:** the inlet patch is the outlet face of a "fan stub" solid. It uses OpenFOAM's `fanPressure` (total-pressure inlet whose total pressure is p0 + ΔP_fan(Q)), with Q evaluated on the patch every iteration, and `pressureInletOutletVelocity` for U. The fan curve CSV (`# comment` lines, header `Q_m3_per_s,dP_Pa`) is converted by the pipeline to an OpenFOAM table of (Q, ΔP/ρ), because simpleFoam uses kinematic pressure. Outside the table it uses `outOfBounds clamp`. The operating point (Q, ΔP) is therefore an *output*: it is where the fan curve meets the system curve of the duct and the open domain.
- **Datasheet caveat:** fan datasheets give *static* pressure versus flow measured on a test plenum. `fanPressure` imposes it as a total-pressure rise at the outlet face. The difference is the outlet dynamic pressure, which is a few Pa at the duct inlet (1.5–3 m/s gives 1–5 Pa). That is small next to 100–300 Pa, but it biases Q slightly high. Datasheet curves of small blowers are also optimistic.
- **Alternatives:** use `flowRateInletVelocity` (fixed Q) to compare ducts at equal flow, or a fixed uniform velocity (`bc.kind = velocity`). Both are supported.
- **What is ignored (limitations):**
  1. Blower swirl and the strongly non-uniform outlet profile (a radial blower's jet hugs the volute's outer wall). The inlet profile is uniform. Ducts that are sensitive to where the air enters will look better than they are. **Mitigation:** keep about 5–10 mm of straight or settling length after the fan in the design, or test sensitivity by imposing a skewed profile.
  2. Fan unsteadiness (blade passing) and fan-induced turbulence. The latter is approximated by a turbulent intensity of 5 % and a mixing length of 1 mm at the inlet.
  3. The fan intake side and recirculation from duct exit back to the intake are not modelled. The intake draws from outside the domain.
  4. The real fan curve at the actual PWM duty. PWM ≠ linear scaling. If needed, scale the curve with the fan laws (Q ∝ n, ΔP ∝ n²).
  5. Several fans (for example two side ducts): each inlet patch gets its own `fanPressure` and finds its own operating point. A shared plenum is handled automatically.

## 4. Boundary conditions (pipeline defaults) [RAN]

| Patch | U | p (kinematic) | k | ω | ν_t |
|---|---|---|---|---|---|
| Fan inlet (fan mode) | `pressureInletOutletVelocity` | `fanPressure`, direction in, p0 = 0 | `turbulentIntensityKineticEnergyInlet` I = 5 % | `turbulentMixingLengthFrequencyInlet` L = 1 mm | calculated |
| Fan inlet (fixed Q) | `flowRateInletVelocity` | zeroGradient | as above | as above | calculated |
| Open box faces ("atmosphere") | `pressureInletOutletVelocity` | `totalPressure` p0 = 0 | `inletOutlet` (k_amb = 1.5e-4 m²/s²) | `inletOutlet` (L = 5 mm) | calculated |
| Walls (duct, nozzle, heater block, optional bed) | noSlip | zeroGradient | `kqRWallFunction` | `omegaWallFunction` | `nutUSpaldingWallFunction` |
| Symmetry (optional) | symmetry | symmetry | symmetry | symmetry | symmetry |

The air domain is a box around the toolhead. Any face can be made a wall: set the bottom face to `wall` to model the bed or the printed part as an impingement plate (§7). The domain should reach at least 25–30 mm beyond the duct exits and the region of interest.

## 5. Mesh strategy [RAN]

- **Geometry contract:** one STL per patch, in mm. The union of all patch STLs must be watertight. Each fan inlet is a face of a closed solid (the "fan stub" block) whose fluid side faces into the duct. This avoids a two-sided inlet baffle.
- `pipeline/geometry.py::export_patches()` tessellates a build123d solid **once** and routes faces to patch files with predicates, so shared edges coincide.
- **Meshing:** `blockMesh` builds a background box (= the air domain, cell size `cell_mm`). Then `surfaceFeatureExtract` runs, followed by `snappyHexMesh` (castellate + snap, with explicit feature snapping), in parallel with scotch. The result is a hex-dominant mesh.
- **Refinement for the validation duct** (L1 base 3.2 mm):
  - Duct walls: level 3 (0.40 mm), which gives ≥ 3 cells across the 1.2 mm wall.
  - Nozzle: level 4 (0.20 mm).
  - Slot box: level 4, so the 2 mm slot gets 10 cells at L1, 12.6 at L2 and 16 at L3.
  - Jet/nozzle box: level 3.
  - Wake box: level 2.
  - nCellsBetweenLevels 2.
- **Thin walls drive the cell count.** Printed ducts with 1.2 mm walls force ≤ 0.4 mm cells on *both* faces of every wall. A 1.6 mm wall in the CFD model is a cheaper approximation when the external shape of the duct doesn't matter.
- **Mesh levels:** `--level N` scales the base cell by 1/2^(1/3) per level, so the cell count roughly doubles per level and the linear refinement ratio is r = 1.26. Snappy levels stay fixed, so every region refines consistently.
- **y+ and walls:**
  - Without prism layers, the first cell centre sits at about half a surface cell (0.1–0.2 mm), which gives y+ ≈ 1–15 in the slot and much lower elsewhere (measured values in §8).
  - That is the buffer layer, where standard log-law wall functions are wrong. Hence the Spalding (all-y+) wall function.
  - Resolving the viscous sublayer properly (y+ < 1 with 10–15 prism layers) would roughly triple the cell count. It matters for wall shear and heat-transfer *on the duct walls*, which is not what we optimise.
  - For heat transfer on the **part surface** (§9), use prism layers (`mesh.layers` or per-surface `layers`) on that patch only.
- cfMesh (`cartesianMesh`) is available as a fallback mesher for very dirty STL. gmsh is available for tet meshes. Neither is wired into the pipeline yet.

## 6. Solver settings and convergence criteria [RAN]

- Solver: `simpleFoam` with SIMPLEC (`consistent yes`). Relaxation: p 0.3, U 0.7, k/ω 0.7.
- Schemes:
  - `linearUpwind` for U (second order) and `limitedLinear 1` for k and ω.
  - `cellLimited Gauss linear 1` gradients.
  - `limited corrected 0.333` Laplacians.
  - One non-orthogonal corrector.
  - GAMG for p.
- Monitors (function objects, written every iteration):
  - `solverInfo` residuals.
  - Q = Σφ and area-averaged p on every inlet and atmosphere patch.
  - `probes` of U and p at every named probe point and at every probe-plane origin.
  - wallShearStress and yPlus at write time.
- **Converged** = OpenFOAM `residualControl` reached (p < 1e-4, U < 1e-5, k/ω < 1e-5), **or** all of the following, checked after at least 300 iterations over a 100-iteration window:
  - inlet Q relative range ≤ 0.2 %;
  - inlet p relative range ≤ 0.5 %;
  - every probe's |U| range ≤ 1 % of max(its mean, 10 % of the fastest probe);
  - initial residuals p ≤ 1e-3 and U ≤ 1e-3.

  A Python **watchdog** in `run_case.py` polls these every 10 s. When they hold, it sets `stopAt writeNow` in controlDict, so the run ends cleanly at the converged state. `results.json → convergence` reports every component (and `stopped_by_watchdog_at`), so a case can be audited. All thresholds can be changed under `solver.*`.
- Global mass balance (inlet Q vs net outflow through the atmosphere) is reported too. It should be < 0.1 %.
- Open jets with a bluff-body wake often stall at residuals of about 1e-4 because the physics is weakly unsteady. Stable integral quantities are the criterion that matters. If a case oscillates, the monitor ranges show it, and the remedy is a `pimpleFoam` time-averaged run (about 5–10× the cost).

## 7. Comparison metrics for duct designs

All are produced automatically by `pipeline/run_case.py` from the config's `probes` block. [RAN] = demonstrated on the validation case.

| # | Metric | How | Status |
|---|---|---|---|
| M1 | **Flow delivered** Q per inlet [m³/s, CFM] and **fan operating point** (Q, ΔP, fraction of Q_max and of shut-off pressure) | Inlet patch Σφ, fan table | [RAN] |
| M2 | **Duct loss** Δp₀ inlet → exit plane [Pa] and system curve | Area-averaged total pressure, inlet patch vs `rect` probe plane at the duct exit | [RAN] |
| M3 | **Exit jet**: Q through the exit plane, area- and flux-weighted mean speed, max speed | `rect` plane | [RAN] |
| M4 | **Nozzle-annulus velocity**: area-weighted mean \|U\| over an annulus r = 0–5 mm around the nozzle axis, at a plane just below the tip (z = −0.5 mm; with a bed/part present, use z = −(layer height)/2) | `annulus` plane, polar sampling | [RAN] |
| M5 | **Symmetry index** of M4: mean \|U\| in 8 × 45° sectors; report min/max and CV (std/mean). Target min/max → 1. | annulus `sectors` | [RAN] |
| M6 | **Part-proxy surface velocity**: set domain `zmin` (or an STL "part" block, for example a 20×20×10 mm tower and an overhang) as a wall at the nozzle tip − layer height. Report area-averaged wall shear and near-wall \|U\| on it. Wall shear is the better convective proxy (Reynolds analogy: h ∝ τ_w·c_p/(U·Pr^(2/3))). | Wall patch stats (`walls.<name>.wss_mean_Pa`) and a plane 0.2 mm above it | Metric code [RAN], part geometry [PROPOSED] |
| M7 | **Nozzle and heater-block impingement (bad)**: area-averaged wall shear and \|U\| at a point 0.6 mm off the nozzle/heater surfaces. Lower is better: air on the nozzle cools the melt zone and makes the heater work harder. | Wall stats on the `nozzle` (and `heaterblock`) patch, probe points | [RAN] |
| M8 | **LiDAR laser-line region** at X −36, Y −21 (relative to nozzle), at layer height: \|U\| at the point, plus a small `rect` plane. Air blowing there can move fine dust or disturb the line; we want it low. | `points` and `planes` | [RAN] (point) |
| M9 | Mass-balance, y+ and convergence flags (QA, not design metrics) | – | [RAN] |

How to compare ducts:
- Always at the **same fan curve** (realistic operating point), and optionally also at the same Q (isolates delivery from the duct's system resistance).
- Use the same domain, probe definitions and mesh level.
- Treat differences below the mesh-sensitivity band (§8) as ties.

## 8. Validation case [RAN]

Geometry (`simulations/cfd/validation/make_validation_geometry.py`, build123d, mm):
- Inside cross-section 15 (x) × 20 (y) at the fan face, z = 35.
- Vertical leg, then a 90° bend (radii 5/20 mm about the y-axis).
- Linear contraction over 20 mm to a 2 × 20 mm slot at x = 10, z = 0.5–2.5, blowing −x.
- Walls 1.2 mm; a 5 mm fan-stub block caps the inlet.
- Nozzle: a cone (r 0.5 → 3 over z 0–3) plus a Ø6 cylinder to z = 10, tip at the origin.
- Air box x −45…60, y −30…30, z −15…45 mm. All six faces open (`totalPressure` 0).

Runs (`run_validation.py`), with mesh, solve and post all scripted:
(a) fixed Q = 4.5e-4 m³/s (U_in = 1.5 m/s) at L1/L2/L3;
(b) `fanPressure` with the example linear curve (300 Pa shut-off, Q_max = 4e-3 m³/s) at L2.

Both runs had the same 4 MPI ranks, ν = 1.6e-5 and ρ = 1.16. Every run was stopped by the convergence watchdog (§6) at about 305 iterations, and every run is flagged `converged: true`. Mass imbalance is < 1e-5, and checkMesh reports OK (max non-orthogonality 43–48°).

| Run | Cells | Mesh [s] | Solve [s] | Total wall [s] | Inlet Q [L/s] | System ΔP (inlet p₀) [Pa] | Slot flux-weighted \|U\| [m/s] | Annulus mean \|U\| [m/s] | Symmetry min/max | Nozzle τ_w,mean [Pa] | LiDAR \|U\| [m/s] | y+ duct mean / max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (a) fixed Q, L1 | 352 009 | 46 | 203 | **257** | 0.450 | 97.4 | 11.18 | 10.84 | 0.650 | 0.070 | 0.113 | 1.2 / 9.5 |
| (a) fixed Q, L2 | 602 008 | 71 | 354 | **433** | 0.450 | 99.6 | 11.00 | 10.92 | 0.566 | 0.084 | 0.121 | 1.0 / 7.9 |
| (a) fixed Q, L3 | 1 105 476 | 122 | 696 | **830** | 0.450 | 99.0 | 11.13 | 10.86 | 0.574 | 0.093 | 0.117 | 0.8 / 7.1 |
| (b) **fanPressure**, L2 | 602 008 | 79 | 374 | **461** | **0.712** (1.51 CFM) | **246.6** | 17.33 | 17.43 | 0.618 | 0.176 | 0.191 | 1.3 / 10.5 |

**Fan operating-point check [RAN].** With the example curve ΔP = 300·(1 − Q/4 L/s), the run settled at Q = 0.7118 L/s and ΔP = 246.6 Pa. That is 17.8 % of Q_max and 82 % of shut-off pressure. The inlet total pressure equals the table value at the achieved Q to within 1e-7, so the BC is doing what it should. As an independent check, take a quadratic system curve through the fixed-Q result (99.6 Pa at 0.45 L/s, so K = 492 Pa/(L/s)²) and intersect it with the fan line: Q = 0.7085 L/s, which agrees with the CFD to **0.5 %**. Takeaway: a 2 mm slot is a high-resistance system. Most of the 247 Pa is the exit dynamic pressure of the 17 m/s jet; the duct's own total-pressure loss is only about 3–5 Pa. Ducts with larger total exit area move the operating point to more flow.

**Mesh sensitivity (fixed Q, L1 → L2 → L3, r ≈ 1.2–1.23 per level) [RAN]**, from `validation/results/mesh_study.{json,png}`:

| Metric | L1 | L2 | L3 | Change L2→L3 | GCI-type bound (1.25·\|Δ\|) |
|---|---|---|---|---|---|
| Annulus mean \|U\| (M4) | 10.84 | 10.92 | 10.86 | −0.5 % | 0.7 % |
| Slot flux-weighted \|U\| (M3) | 11.18 | 11.00 | 11.13 | +1.2 % | 1.5 % |
| System ΔP (inlet p₀) | 97.4 | 99.6 | 99.0 | −0.6 % | 0.7 % |
| Symmetry min/max (M5) | 0.650 | 0.566 | 0.574 | +1.4 % | – |
| Nozzle mean wall shear (M7) | 0.070 | 0.084 | 0.093 | +10 % | **not converged** |
| Duct Δp₀ loss (M2) | 3.3 | 2.8 | 4.9 | – | **noise**: it is a 3–5 Pa difference of two ~99 Pa numbers |
| Point probe `nozzle_front` (3.6, 0, 1.5) | 3.04 | 2.16 | 3.06 | – | **±20–30 %** |

All three sequences are oscillatory (not monotone), so Richardson extrapolation is not applicable. The GCI is reported as the bound 1.25·|f₃ − f₂|/f₃.

Conclusions:
- **L2 (about 0.6 M cells, about 7–8 min) is the production level.** Area- and flux-averaged velocity and pressure metrics are mesh-independent to within ±1.5 %, so duct-to-duct differences smaller than about 3 % are ties.
- **Wall-shear metrics are not mesh-converged** without prism layers. They are usable only for relative comparison at identical meshing, or with layers added.
- **Single-point probes sit in shear layers** and are unreliable (±25 %). Always use area-averaged planes or annuli for decisions. The LiDAR point is fine because it sits in quiet far-field air (≈0.1–0.2 m/s).
- Sampling consistency: the flux recovered through the slot-exit probe plane (cell-value sampling) is 0.4439–0.4556 L/s against the imposed 0.450 L/s (±1.3 %). The fan case gives 0.7016 against 0.7118 L/s (−1.4 %).
- Early stopping is safe. An L1 run continued to 1500 iterations gave an annulus mean |U| of 10.8450 m/s, against 10.8449 m/s when the watchdog stopped it at iteration 305. Residuals flatten after about 250 iterations: Ux ≈ 8e-5, Uy ≈ 4e-4, k and ω ≈ 3e-3, p ≈ 2e-7. That is a plateau, not divergence.

**Flow features seen** (PNGs in `simulations/cfd/validation/results/val_fan_L2/`):
- `slice_y0_Umag.png`, the nozzle plane: the slot jet stays attached as a thin sheet and reaches the nozzle tip with about 20 m/s on the centreline. It hits the cone and passes beneath the tip, with a weak wake behind the nozzle.
- `slice_tip_z-0.5_Umag.png`: in the plane 0.5 mm below the tip, the 20 mm-wide slot jet floods the whole r < 5 mm annulus from one side. The sectors facing the duct are fast and the leeward sectors slow, which gives the 0.57–0.62 symmetry index. That is the expected weakness of a single-sided duct, and M5 measures it.
- `line_duct_centerline.png`: static pressure is flat through the vertical leg and bend. It drops in the last 10 mm of the contraction, where |U| peaks at about 21 m/s.
- `convergence.png`: residual and inlet-Q history.

The full plot set, including `streamlines3d.png`, is in each case's `results/` folder in the work dir.

## 9. Thermal extension [PROPOSED]

Ranked by cost:

1. **Heat-transfer-coefficient proxy from isothermal results (free, today).** Use wall shear or near-wall velocity on a part-proxy wall (M6), converted with the Reynolds/Chilton-Colburn analogy. *Proves:* where air scrubs the part surface and roughly in what proportion. *Doesn't prove:*
   - absolute h;
   - effects at stagnation points and separated regions, where the analogy fails badly (impingement h is high while τ_w → 0);
   - anything about plastic temperature.
2. **Passive scalar / forced convection on a frozen flow field (≈ +10 % cost).** Solve a temperature-like scalar with `scalarTransport` (a function object, or `simpleFoam` + `fvOptions`), with a fixed-temperature heated part wall and ambient inflow, at Pr = 0.71 and Pr_t = 0.85. The local wall heat flux gives h(x) = q/(T_w − T_∞). *Proves:* the relative convective h distribution, including impingement, for a part at uniform temperature. *Doesn't prove:* buoyancy (fine: Gr/Re² ≪ 1 for jets > 2 m/s), conduction in the part, or radiation.

   A cleaner way to get the same result: `buoyantSimpleFoam` with g = 0 (or with g), a heated wall at, say, 200 °C, and air at chamber temperature. That gives variable properties plus h. **Recommended next step.** It needs y+ ≈ 1 prism layers on the part patch, because h is very wall-resolution sensitive. Wall functions for heat transfer in impinging jets are poor.
3. **Conjugate heat transfer (`chtMultiRegionSimpleFoam` / `chtMultiRegionFoam`).** Regions: air, a solid "printed part" (PLA k ≈ 0.13 W/m·K, PETG 0.2), optionally the heater block plus nozzle (aluminium/copper with a heat source) and the heatsink. *Proves:*
   - the steady temperature field of a thin feature (e.g. an overhang or a 0.4 mm wall) under the jet;
   - how much the jet chills the nozzle and heater block, which is a direct heater-power penalty.

   *Doesn't prove:* the transient layer-by-layer cooling that sets print quality. That needs a transient CHT run with a moving or "just-deposited" hot layer (strand at 220 °C cooling to T_g in about 0.5–2 s). It is feasible only as a reduced study (a single 2D/3D strand, `chtMultiRegionFoam`, a few seconds of physical time).
4. **Bench validation (required at some point).** Hot-wire or vane anemometer at the annulus plane; thermocouple or IR measurements on a heated dummy; the standard overhang/bridge test prints. CFD ranks; prints decide.

Runtime estimates on this machine: see §10.

## 10. Runtime on this machine (4 cores) [RAN for isothermal; estimates for thermal]

Measured, 4 MPI ranks, steady isothermal kOmegaSST, watchdog stop at about 300 iterations:

| Case | Cells | snappy (parallel) | Solver | Wall time end to end | Throughput |
|---|---|---|---|---|---|
| L1 | 0.35 M | 46 s | 203 s | 4.3 min | ≈ 0.6 s/iteration |
| **L2 (default)** | 0.60 M | 71–79 s | 354–374 s | **7.2–7.7 min** | ≈ 1.15 s/iteration |
| L3 | 1.11 M | 122 s | 696 s | 13.8 min | ≈ 2.2 s/iteration |

- Cost scales about linearly with cells, at roughly 0.65 µs per cell-iteration on 4 cores. RAM use is about 1 GB per million cells. A two-duct toolhead (both sides plus fan stubs, same refinement) will roughly double the thin-wall cell count, so expect about 1.0–1.3 M cells and 12–16 min at L2.
- That is roughly 4–8 designs per hour.
- A symmetry plane (`domain.patches.ymin = symmetry`) halves the cost for symmetric concepts.
- Without the watchdog (1500 iterations), L1 took 14.7 min. Keep `solver.watchdog` on.

Thermal extensions (§9) are **estimates [PROPOSED]**, on the L2 geometry plus part proxy:

| Method | Mesh | Estimated wall time |
|---|---|---|
| Isothermal + h proxy | as L2 | ≈ 8 min |
| `buoyantSimpleFoam` with a heated wall, prism layers on the part | ≈ 0.9 M cells | 25–40 min |
| `chtMultiRegionSimpleFoam` (air + part + nozzle/heater) | ≈ 1.0 M cells | 45–90 min |
| Transient CHT strand cooling (2–5 s physical) | reduced domain | several hours |

## 11. Pipeline usage

```bash
source /opt/k1th/env.sh            # after tools/setup_env.sh
cd hardware/toolhead/simulations/cfd
# 1. CAD -> per-patch STL (mm) with pipeline/geometry.py::export_patches (see validation/make_validation_geometry.py)
# 2. write a config JSON (template: validation/validation_case.json; schema: run_case.py docstring)
$K1_PY pipeline/run_case.py my_duct.json --level 2 --np 4               # mesh + solve + post
$K1_PY pipeline/run_case.py my_duct.json --level 2 --steps solve,post \
       --set 'surfaces.inlet.bc={"kind":"fan","csv":"pipeline/fans/my_fan.csv"}'   # reuse mesh, new BC
$K1_PY validation/run_validation.py                                     # full validation study
```

- **Inputs:**
  - STL set (`surfaces`: `wall` | `inlet` with `bc` = fan CSV | flowRate | velocity);
  - domain box and face types (atmosphere | wall | symmetry);
  - `location_in_mesh`;
  - refinement boxes;
  - probes (`rect`/`annulus` planes, points, polylines);
  - `loss_pairs`, `plots`, `fluid`, `solver`;
  - mesh level, MPI ranks, work dir (default the session scratchpad `…/scratchpad/cfd-runs`, or `$K1_CFD_WORKDIR`).
- **Outputs** go to `<workdir>/<case>/results/`:
  - `results.json`: mesh, timing, convergence, inlets plus operating point, mass balance, planes, points, lines, walls (area, wall shear, y+), losses;
  - `slice_*_Umag.png`: |U| with in-plane streamlines;
  - `line_*.png`: p and |U| along a polyline;
  - `convergence.png` and `streamlines3d.png`.
- Generated cases stay outside the repo. `simulations/cfd/.gitignore` guards against accidental case output.

## 12. Known limitations / to-do

- No GPG verification of the OpenFOAM debs (key host blocked). See §1.
- RANS at Re ≈ 10³ (transitional); swirl and non-uniform fan inflow ignored; isothermal only.
- Thin-walled ducts dominate the cell count. Prism layers are off by default.
- Steady solver: weakly unsteady wakes show up as plateaued residuals. Use the monitor ranges, and if needed run pimpleFoam time-averaged.
- Probe sampling uses VTK point interpolation (cell → point), so values within about one cell of walls are smoothed.

## 13. Pipeline extensions for the duct study (Duct-Design & CFD agent) [RAN]

These are backward compatible: a config without the new keys runs exactly as before, which is what the
validation case does. The duct results and report are in `documentation/cfd-report.md`.

- **Wall-region probes** (`probes.walls`, `postprocess.wall_region_metrics`): statistics over part of a
  wall patch, filtered by radius about the nozzle axis (`r_min`/`r_max`), height (`z_min`/`z_max`) and the
  outward normal of the solid surface (`normal`). Each region reports:
  - area;
  - area-weighted wall shear stress and y+;
  - area-weighted |U| sampled `delta_mm` (default 0.3 mm) off the wall along the face normal, using
    cell-constant sampling.

  Uses: part-top discs r ≤ 5 / r ≤ 10, the side faces' top 3 mm, the nozzle cone and the sock bottom.
- **Thermal proxy** (`--steps thermal`, `run_case.step_thermal`, `postprocess.thermal_metrics`):
  1. Restarts the converged flow case for `thermal.iters` more SIMPLE iterations, with the
     `scalarTransport` function object solving a passive temperature T (D = ν/Pr + ν_t/Pr_t, with
     Pr 0.71 and Pr_t 0.85).
  2. Boundary conditions: fan inlets and open boundaries at `T_inf`; the walls listed in
     `thermal.walls` at a fixed temperature; every other wall adiabatic.
  3. Wall heat flux per face: q = ρ c_p (ν/Pr + ν_t,w/Pr_t)(T_w − T_P)/d_n, which is the face
     diffusivity the function object itself uses. Then h = q/(T_w − T_inf).
  4. Cross-check: the global enthalpy balance through the open boundaries (`hflux_*` function objects).

  The flow log is kept as `log.simpleFoam`, and the thermal restart log as `log.simpleFoam.thermal`.
  The template files are not changed: `div(phi,T)` and the T solver are added to the case copy only.
  - The T equation gets its own solver (PBiCGStab, tolerance 1e-10, relTol 0), so it is solved fully every
    iteration.
  - It gets an equation relaxation factor of 1. Without one, `scalarTransport` relaxes with factor 0
    and aborts with a floating-point exception in v2512.
  - It uses the conservative `Gauss limitedLinear 1` convection scheme.
- **Iteration averaging** (`solver.average_start`, opt-in): a `fieldAverage` function object averages U, p
  and wall shear from the given iteration. The post-processing then uses UMean/pMean/wallShearStressMean in
  place of the instantaneous fields and records `results["averaging"]`. Watchdog probes that sit inside
  solids (VGREAT values) are ignored. Used by the duct study because its converging jets are weakly
  unsteady (U residual plateau about 5e-3, jet-core probes swinging 2–60 % between iterations).
- **Case driver** (`simulations/cfd/cases/run_cases.py`): geometry → pipeline → results copy →
  `summary.csv/json`.
  - It re-uses the mesh of the same design for a different fan curve, so only the solve and post steps
    run again.
  - `run_queue.sh` runs a dynamic queue file.
  - `repost.py` re-runs post-processing with updated probe definitions.
  - `--steps thermal,post` applies the standard thermal set-up (part 200 °C, nozzle 250 °C, sock 150 °C,
    air 45 °C).
- **Mesh settings for the toolhead cases** (`cad/source/ducts/export_for_cfd.py`):
  - stopping: ≥ 550 iterations, then fan Q and p within 0.4 % over 100 iterations, cap 750;
    averaging from iteration 300;
  - same base cell (3.2 mm at L1, 2.54 mm at L2) and `n_between` 2 as the validation case;
  - duct, sock and part-top surfaces at level 3; nozzle at level 4;
  - level-2 box around the toolhead, level-3 box over the jets (r ≤ 17, Z −0.2…6.5), and a level-4 box
    at the tip (13 × 13 × 1.7 mm).

  Section 4 of the CFD report gives the cell counts.
