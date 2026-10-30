#!/usr/bin/env python3
"""K1 toolhead duct CFD pipeline: STL set -> OpenFOAM case -> mesh -> simpleFoam -> metrics + PNGs.

Run with the toolchain venv:   /opt/k1th/venv/bin/python run_case.py CONFIG.json [options]

    --level N        mesh level (1 = coarse, 2 = medium/default, 3 = fine). Base cell size is
                     domain.cell_mm / ratio**(N-1), ratio = mesh.ratio (default 2**(1/3), i.e.
                     ~2x cells per level). Snappy refinement levels are unchanged.
    --workdir DIR    where cases are written (default $K1_CFD_WORKDIR or the session scratchpad)
    --name NAME      case name (default <config name>_L<level>)
    --np N           MPI ranks (default 4; 1 = serial)
    --steps S        comma list from mesh,solve,post (default all)
    --set key=value  override any config entry, dotted path, JSON value
                     (e.g. --set solver.max_iter=800 --set surfaces.inlet.bc.Q_m3_s=5e-4)

Writes <workdir>/<name>/ (a normal OpenFOAM case) and <workdir>/<name>/results/
results.json + *.png.  Exit code 0 even if not converged; check results.json["convergence"].

CONFIG (JSON; ALL lengths in mm, the pipeline scales to metres; see
validation/validation_case.json for a complete example):
{
  "name": "my_duct",
  "stl_dir": "path/relative/to/config",
  "surfaces": {                               # one STL per patch, union must be watertight
    "duct":   {"file": "duct.stl", "type": "wall", "level": [3, 3], "feature_level": 3},
    "nozzle": {"file": "nozzle.stl", "type": "wall", "level": [4, 4]},
    "inlet":  {"file": "inlet.stl", "type": "inlet", "level": [3, 3],
               "bc": {"kind": "fan", "csv": "../pipeline/fans/example_linear_300Pa.csv"}}
               # or "bc": {"kind": "flowRate", "Q_m3_s": 4.5e-4}
               # or "bc": {"kind": "velocity", "U_m_s": 1.5}   (uniform normal speed)
  },
  "domain": {"min": [...], "max": [...], "cell_mm": 3.2,
             "patches": {"zmin": {"name": "bed", "type": "wall"}}},  # default: atmosphere
                                       # face keys xmin..zmax; types atmosphere|wall|symmetry
  "location_in_mesh": [x, y, z],       # a point in the AIR
  "refinement_boxes": [{"name": "jet", "min": [...], "max": [...], "level": 4}],
  "probes": {
    "planes": [{"name": "slot_exit", "type": "rect", "origin": [...], "normal": [...],
                "u": [...], "half": [hu, hv]},
               {"name": "tip_annulus", "type": "annulus", "origin": [...], "normal": [...],
                "r_in": 0, "r_out": 5, "sectors": 8}],
    "points": [{"name": "lidar", "xyz": [...]}],
    "lines":  [{"name": "duct_centerline", "points": [[...], ...]}]
  },
  "loss_pairs": [["inlet", "slot_exit"]],   # total-pressure loss inlet patch -> plane
  "plots": {"slices": [{"name": "y0", "axis": "y", "value": 0, "range": [[x0, x1], [z0, z1]]}],
            "streamlines": true},
  "fluid": {"nu": 1.6e-5, "rho": 1.16},
  "solver": {"max_iter": 1500, ...}
}
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import re
import shutil
import string
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

PIPE = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPE))
from geometry import write_ascii_stl  # noqa: E402

DEFAULT_WORKDIR = os.environ.get(
    "K1_CFD_WORKDIR",
    "/tmp/claude-0/-home-user-K1ProMaxUltra/1fc00b30-b973-54a8-8106-390cde6c1256/scratchpad/cfd-runs")
FOAM_BASHRC = os.environ.get("FOAM_BASHRC", "/usr/lib/openfoam/openfoam2512/etc/bashrc")
MM = 1e-3

DEFAULTS = {
    "fluid": {"nu": 1.6e-5, "rho": 1.16},          # air ~30 C
    "domain": {"cell_mm": 3.2, "patches": {}},
    "mesh": {"ratio": 2 ** (1 / 3), "n_between": 3, "layers": 0, "parallel_snappy": True,
             "decomp_method": "scotch"},
    "refinement_boxes": [],
    "probes": {"planes": [], "points": [], "lines": []},
    "loss_pairs": [],
    "plots": {"slices": [], "streamlines": True},
    "solver": {
        "max_iter": 1500, "write_interval": 500, "turbulence": "kOmegaSST",
        "consistent": "yes", "relax_p": 0.3, "relax_U": 0.7, "relax_turb": 0.7,
        "n_nonorth": 1, "res_p": 1e-4, "res_U": 1e-5, "res_turb": 1e-5,
        "turb_div": "limitedLinear 1",
        "inlet_intensity": 0.05, "inlet_mixing_length_mm": 1.0,
        "ambient_k": 1.5e-4, "ambient_mixing_length_mm": 5.0,
        # convergence / early stop: over the last `window` iterations (after min_iter) the inlet Q,
        # inlet p and probe |U| must vary less than these relative ranges; residuals below res_*_max.
        # The watchdog then sets stopAt writeNow. Probe |U| is normalised by
        # max(mean|U| at that probe, probe_floor * largest probe |U|).
        "watchdog": True, "min_iter": 300, "window": 100,
        "tol_Q": 0.002, "tol_p": 0.005, "tol_probe": 0.01, "probe_floor": 0.1,
        "res_p_max": 1e-3, "res_U_max": 1e-3, "poll_s": 10,
    },
}
FACES = {"xmin": "(0 4 7 3)", "xmax": "(1 2 6 5)", "ymin": "(0 1 5 4)",
         "ymax": "(3 7 6 2)", "zmin": "(0 3 2 1)", "zmax": "(4 5 6 7)"}


class Tpl(string.Template):
    delimiter = "@"


# --------------------------------------------------------------------------- utils
def deep_update(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep_update(a[k], v)
        else:
            a[k] = v
    return a


def set_dotted(d, key, value):
    ks = key.split(".")
    for k in ks[:-1]:
        d = d.setdefault(k, {})
    try:
        d[ks[-1]] = json.loads(value)
    except json.JSONDecodeError:
        d[ks[-1]] = value


def v3(p, s=MM):
    return "%.9g %.9g %.9g" % tuple(np.asarray(p, float) * s)


def run_foam(cmd: str, case: Path, log: str, np_: int = 1):
    """Run an OpenFOAM command (optionally with mpirun) inside the case dir."""
    label = cmd.split()[0]
    if np_ > 1:
        cmd = f"mpirun --oversubscribe -np {np_} {cmd} -parallel"
    full = f"source {FOAM_BASHRC} >/dev/null 2>&1; cd '{case}' && {cmd} > '{log}' 2>&1"
    env = dict(os.environ, OMPI_ALLOW_RUN_AS_ROOT="1", OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="1",
               OMPI_MCA_btl_vader_single_copy_mechanism="none")
    t0 = time.time()
    r = subprocess.run(["bash", "-c", full], env=env)
    dt = time.time() - t0
    if r.returncode != 0:
        tail = Path(case, log).read_text(errors="replace").splitlines()[-30:]
        raise RuntimeError(f"'{cmd}' failed (rc={r.returncode}), see {case/log}:\n" + "\n".join(tail))
    print(f"  {label:<24s} np={np_:<2d} {dt:7.1f} s", flush=True)
    return dt


def read_fan_csv(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split(",")]
        try:
            rows.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue  # header
    rows.sort()
    if len(rows) < 2:
        raise ValueError(f"fan curve {path}: need >= 2 data rows")
    return np.array(rows)


# --------------------------------------------------------------------------- case writing
def decomp_split(np_, L):
    """Factor np_ into (nx ny nz), giving more pieces to the longest box directions."""
    n, L = [1, 1, 1], np.asarray(L, float).copy()
    rem = np_
    for f in (2, 3, 5, 7):
        while rem % f == 0:
            i = int(np.argmax(L / np.array(n)))
            n[i] *= f
            rem //= f
    if rem > 1:
        n[int(np.argmax(L))] *= rem
    return "%d %d %d" % tuple(n)


def surface_kind(s):
    return s.get("type", "wall")


def block_patches(cfg):
    groups = {}
    for face in FACES:
        spec = cfg["domain"]["patches"].get(face, {"name": "atmosphere", "type": "atmosphere"})
        if isinstance(spec, str):
            spec = {"name": spec if spec != "atmosphere" else "atmosphere", "type": spec}
        g = groups.setdefault(spec["name"], {"type": spec["type"], "faces": []})
        g["faces"].append(FACES[face])
    out = []
    for name, g in groups.items():
        t = {"atmosphere": "patch", "wall": "wall", "symmetry": "symmetry"}[g["type"]]
        out.append(f"    {name} {{ type {t}; faces ( {' '.join(g['faces'])} ); }}")
    return "\n".join(out), {n: g["type"] for n, g in groups.items()}


SOLVER_FILES = ("system/controlDict", "system/fvSchemes", "system/fvSolution", "system/decomposeParDict",
                "constant/transportProperties", "constant/turbulenceProperties")


def write_case(cfg, case: Path, level: int, np_: int, solver_only: bool = False):
    """Create the case from the template. solver_only=True re-renders only SOLVER_FILES
    (keeps the mesh) so solver settings / BCs can change without remeshing."""
    sol = cfg["solver"]
    stl_dir = Path(cfg["stl_dir"])
    if solver_only:
        for rel in SOLVER_FILES:
            shutil.copy(PIPE / "template" / rel, case / rel)
    else:
        if case.exists():
            shutil.rmtree(case)
        shutil.copytree(PIPE / "template", case)
        (case / "constant/triSurface").mkdir(parents=True)
        (case / "results").mkdir()
        (case / "case.foam").touch()

    # --- STL scaling mm -> m, renamed solid per patch
    import trimesh
    for name, s in ({} if solver_only else cfg["surfaces"]).items():
        m = trimesh.load(stl_dir / s["file"], force="mesh", process=False)
        write_ascii_stl(case / f"constant/triSurface/{name}.stl", name, m.triangles, scale=MM)

    # --- fan tables (kinematic pressure: dP / rho)
    for name, s in cfg["surfaces"].items():
        bc = s.get("bc", {})
        if surface_kind(s) == "inlet" and bc.get("kind") == "fan":
            tab = read_fan_csv(bc["csv_resolved"])
            body = "\n".join(f"    ({q:.6e} {dp / cfg['fluid']['rho']:.6e})" for q, dp in tab)
            (case / f"constant/fanCurve_{name}").write_text(f"(\n{body}\n)\n")

    # --- mesh sizes
    cell = cfg["domain"]["cell_mm"] / cfg["mesh"]["ratio"] ** (level - 1)
    lo, hi = np.array(cfg["domain"]["min"], float), np.array(cfg["domain"]["max"], float)
    n = np.maximum(1, np.round((hi - lo) / cell)).astype(int)
    patches_txt, block_types = block_patches(cfg)

    geom, feats, rsurf, rreg, layers, fext = [], [], [], [], [], []
    for name, s in cfg["surfaces"].items():
        geom.append(f"    {name}.stl {{ type triSurfaceMesh; name {name}; }}")
        fl = s.get("feature_level", max(s.get("level", [3, 3])))
        feats.append(f'        {{ file "{name}.eMesh"; level {fl}; }}')
        ptype = "wall" if surface_kind(s) == "wall" else "patch"
        lv = s.get("level", [3, 3])
        rsurf.append(f"        {name} {{ level ({lv[0]} {lv[1]}); patchInfo {{ type {ptype}; }} }}")
        nl = s.get("layers", cfg["mesh"]["layers"] if surface_kind(s) == "wall" else 0)
        if nl:
            layers.append(f"        {name} {{ nSurfaceLayers {nl}; }}")
        fext.append(f"{name}.stl\n{{\n    extractionMethod extractFromSurface;\n"
                    f"    extractFromSurfaceCoeffs {{ includedAngle 150; }}\n"
                    f"    subsetFeatures {{ nonManifoldEdges no; openEdges yes; }}\n    writeObj no;\n}}\n")
        for d_mm, lvl in s.get("distance", []):
            rreg.append(f"        {name} {{ mode distance; levels (({d_mm * MM:.6g} {lvl})); }}")
    for b in cfg["refinement_boxes"]:
        geom.append(f"    {b['name']} {{ type searchableBox; min ({v3(b['min'])}); max ({v3(b['max'])}); }}")
        rreg.append(f"        {b['name']} {{ mode inside; levels ((1e15 {b['level']})); }}")

    # --- inlet turbulence / ambient values
    ambient_k = sol["ambient_k"]
    ambient_om = math.sqrt(ambient_k) / (0.09 ** 0.25 * sol["ambient_mixing_length_mm"] * MM)

    # --- function objects
    fos = ['    solverInfo { type solverInfo; libs ("libutilityFunctionObjects.so"); '
           'fields (U p k omega); writeResidualFields no; }']
    inlets = [k for k, s in cfg["surfaces"].items() if surface_kind(s) == "inlet"]
    walls = [k for k, s in cfg["surfaces"].items() if surface_kind(s) == "wall"] + \
            [k for k, t in block_types.items() if t == "wall"]
    for p in inlets + [k for k, t in block_types.items() if t == "atmosphere"]:
        for tag, op, fld in (("flow", "sum", "phi"), ("pavg", "areaAverage", "p")):
            fos.append(f'    {tag}_{p} {{ type surfaceFieldValue; libs ("libfieldFunctionObjects.so"); '
                       f'writeControl timeStep; writeInterval 1; log false; writeFields false; '
                       f'regionType patch; name {p}; operation {op}; fields ({fld}); }}')
    if walls:
        fos.append('    wallShearStress { type wallShearStress; libs ("libfieldFunctionObjects.so"); '
                   f'writeControl writeTime; log false; patches ({" ".join(walls)}); }}')
        fos.append('    yPlus { type yPlus; libs ("libfieldFunctionObjects.so"); writeControl writeTime; log false; }')
    plocs = monitor_points(cfg)
    if plocs:
        fos.append('    probes { type probes; libs ("libsampling.so"); writeControl timeStep; writeInterval 1; '
                   'log false; fields (U p); probeLocations ( ' + " ".join(f"({v3(q)})" for q in plocs) + " ); }")

    subs = dict(
        end_iter=sol["max_iter"], functions="\n".join(fos),
        # make sure the last iteration is a write time
        write_interval=sol["max_iter"] // max(1, math.ceil(sol["max_iter"] / sol["write_interval"]))
        if sol["max_iter"] % max(1, math.ceil(sol["max_iter"] / sol["write_interval"])) == 0 else sol["max_iter"],
        turb_div=sol["turb_div"], n_nonorth=sol["n_nonorth"], consistent=sol["consistent"],
        res_p=sol["res_p"], res_U=sol["res_U"], res_turb=sol["res_turb"],
        relax_p=sol["relax_p"], relax_U=sol["relax_U"], relax_turb=sol["relax_turb"],
        x0=lo[0] * MM, y0=lo[1] * MM, z0=lo[2] * MM, x1=hi[0] * MM, y1=hi[1] * MM, z1=hi[2] * MM,
        nx=n[0], ny=n[1], nz=n[2], block_patches=patches_txt,
        feature_entries="\n".join(fext), add_layers="true" if layers else "false",
        geometry="\n".join(geom), features="\n".join(feats), refinement_surfaces="\n".join(rsurf),
        refinement_regions="\n".join(rreg), layers="\n".join(layers), n_between=cfg["mesh"]["n_between"],
        loc=v3(cfg["location_in_mesh"]), np=np_, decomp_n=decomp_split(np_, hi - lo),
        decomp_method=cfg["mesh"]["decomp_method"], nu=cfg["fluid"]["nu"],
        sim_type="RAS" if sol["turbulence"] != "laminar" else "laminar", ras_model=sol["turbulence"],
    )
    files = [case / r for r in SOLVER_FILES] if solver_only else \
        list((case / "system").iterdir()) + list((case / "constant").glob("*Properties"))
    for f in files:
        f.write_text(Tpl(f.read_text()).substitute(subs))
    meta = {"level": level, "base_cell_mm": cell, "block_cells": n.tolist(), "block_types": block_types,
            "ambient_k": ambient_k, "ambient_omega": ambient_om}
    (case / "results/case_meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def read_boundary(case: Path):
    txt = (case / "constant/polyMesh/boundary").read_text()
    txt = txt[txt.index("FoamFile"):]
    out = {}
    for m in re.finditer(r"\n\s*(\w+)\s*\n\s*\{([^}]*)\}", txt):
        t = re.search(r"\btype\s+(\w+);", m.group(2))
        nf = re.search(r"nFaces\s+(\d+);", m.group(2))
        if t:
            out[m.group(1)] = {"type": t.group(1), "nFaces": int(nf.group(1))}
    return out


def write_fields(cfg, case: Path, meta):
    sol, fl = cfg["solver"], cfg["fluid"]
    bnd = read_boundary(case)
    kA, omA = meta["ambient_k"], meta["ambient_omega"]
    I, L = sol["inlet_intensity"], sol["inlet_mixing_length_mm"] * MM
    fields = {n: [] for n in ("U", "p", "k", "omega", "nut")}

    def add(name, U, p, k, om, nut):
        for f, txt in zip(("U", "p", "k", "omega", "nut"), (U, p, k, om, nut)):
            fields[f].append(f"    {name}\n    {{\n        {txt}\n    }}")

    for name, b in bnd.items():
        s = cfg["surfaces"].get(name)
        kind = surface_kind(s) if s else meta["block_types"].get(name, "wall")
        if b["type"] in ("symmetry", "symmetryPlane", "empty"):
            t = f"type {b['type']};"
            add(name, t, t, t, t, t)
        elif kind == "wall":
            add(name, "type noSlip;", "type zeroGradient;",
                f"type kqRWallFunction; value uniform {kA};",
                f"type omegaWallFunction; value uniform {omA};",
                "type nutUSpaldingWallFunction; value uniform 0;")
        elif kind == "atmosphere":
            add(name, "type pressureInletOutletVelocity; value uniform (0 0 0);",
                "type totalPressure; p0 uniform 0; value uniform 0;",
                f"type inletOutlet; inletValue uniform {kA}; value uniform {kA};",
                f"type inletOutlet; inletValue uniform {omA}; value uniform {omA};",
                "type calculated; value uniform 0;")
        elif kind == "inlet":
            bc = s["bc"]
            kin = f"type turbulentIntensityKineticEnergyInlet; intensity {I}; value uniform {kA};"
            omin = f"type turbulentMixingLengthFrequencyInlet; mixingLength {L}; value uniform {omA};"
            if bc["kind"] == "fan":
                U = "type pressureInletOutletVelocity; value uniform (0 0 0);"
                p = (f'type fanPressure; direction in; fanCurve {{ type table; '
                     f'file "<constant>/fanCurve_{name}"; outOfBounds clamp; }} p0 uniform 0; value uniform 0;')
            else:
                Q = bc["Q_m3_s_resolved"]
                U = (f"type flowRateInletVelocity; volumetricFlowRate constant {Q:.6e}; "
                     f"extrapolateProfile no; value uniform (0 0 0);")
                p = "type zeroGradient;"
            add(name, U, p, kin, omin, "type calculated; value uniform 0;")
        else:
            raise ValueError(f"unknown patch kind for {name}")

    spec = {"U": ("volVectorField", "[0 1 -1 0 0 0 0]", "(0 0 0)"),
            "p": ("volScalarField", "[0 2 -2 0 0 0 0]", "0"),
            "k": ("volScalarField", "[0 2 -2 0 0 0 0]", f"{kA}"),
            "omega": ("volScalarField", "[0 0 -1 0 0 0 0]", f"{omA}"),
            "nut": ("volScalarField", "[0 2 -1 0 0 0 0]", "0")}
    (case / "0").mkdir(exist_ok=True)
    for f, (cls, dim, init) in spec.items():
        (case / "0" / f).write_text(
            f"FoamFile {{ version 2.0; format ascii; class {cls}; object {f}; }}\n\n"
            f"dimensions {dim};\ninternalField uniform {init};\n\nboundaryField\n{{\n"
            + "\n".join(fields[f]) + "\n}\n")
    return bnd


# --------------------------------------------------------------------------- steps
def step_mesh(cfg, case, np_):
    t = {}
    t["blockMesh"] = run_foam("blockMesh", case, "log.blockMesh")
    t["surfaceFeatureExtract"] = run_foam("surfaceFeatureExtract", case, "log.surfaceFeatureExtract")
    if np_ > 1 and cfg["mesh"]["parallel_snappy"]:
        run_foam("decomposePar -force", case, "log.decomposePar.mesh")
        t["snappyHexMesh"] = run_foam("snappyHexMesh -overwrite", case, "log.snappyHexMesh", np_)
        t["reconstructParMesh"] = run_foam("reconstructParMesh -constant", case, "log.reconstructParMesh")
        for d in case.glob("processor*"):
            shutil.rmtree(d)
    else:
        t["snappyHexMesh"] = run_foam("snappyHexMesh -overwrite", case, "log.snappyHexMesh")
    run_foam("checkMesh -constant", case, "log.checkMesh")
    cm = (case / "log.checkMesh").read_text()
    info = {"time_s": t, "cells": int(re.search(r"cells:\s+(\d+)", cm).group(1)),
            "checkMesh_ok": "Mesh OK." in cm}
    for key, pat in (("max_nonortho", r"Mesh non-orthogonality Max:\s+([\d.eE+-]+)"),
                     ("max_skewness", r"Max skewness = ([\d.eE+-]+)")):
        m = re.search(pat, cm)
        info[key] = float(m.group(1)) if m else None
    return info


def monitor_points(cfg):
    """Probe locations (mm) monitored every iteration: named points + plane origins."""
    pts = [p["xyz"] for p in cfg["probes"]["points"]]
    pts += [p["origin"] for p in cfg["probes"]["planes"]]
    pts += cfg["probes"].get("monitor_points", [])
    return pts


def stability(cfg, case):
    """Return (iteration, dict of relative ranges over the last window, residuals) from postProcessing."""
    from postprocess import series, read_probes, residuals
    sol = cfg["solver"]
    W = sol["window"]
    out = {}
    it = 0
    for name, s in cfg["surfaces"].items():
        if surface_kind(s) != "inlet":
            continue
        for tag in ("flow", "pavg"):
            ser = series(case, f"{tag}_{name}")
            if ser is None or len(ser) < W:
                return 0, None, None
            w = ser[-W:, 1]
            it = int(ser[-1, 0])
            out[f"{tag}_{name}"] = float((w.max() - w.min()) / max(abs(w.mean()), 1e-30))
    pr = read_probes(case)
    if pr is not None and len(pr[0]) >= W:
        mag = np.linalg.norm(pr[1][-W:], axis=2)          # [W, nprobe]
        mean = mag.mean(axis=0)
        ref = np.maximum(mean, sol["probe_floor"] * max(mean.max(), 1e-12))
        rr = (mag.max(axis=0) - mag.min(axis=0)) / ref
        out["probe_Umag_max"] = float(rr.max())
    res = residuals(case)
    rfin = {k: float(v[-1]) for k, v in res.items() if not k.startswith("_") and len(v)}
    return it, out, rfin


def is_stable(cfg, rel, rfin):
    sol = cfg["solver"]
    if rel is None:
        return False
    for k, v in rel.items():
        tol = sol["tol_Q"] if k.startswith("flow") else sol["tol_p"] if k.startswith("pavg") else sol["tol_probe"]
        if v > tol:
            return False
    u = max(rfin.get(c, 0.0) for c in ("Ux", "Uy", "Uz"))
    return rfin.get("p", 1.0) <= sol["res_p_max"] and u <= sol["res_U_max"]


def run_solver_watched(cfg, case, np_):
    """Run simpleFoam; stop it (stopAt writeNow) once the monitors are stable."""
    sol = cfg["solver"]
    cmd = "simpleFoam" if np_ == 1 else f"mpirun --oversubscribe -np {np_} simpleFoam -parallel"
    full = f"source {FOAM_BASHRC} >/dev/null 2>&1; cd '{case}' && {cmd} > log.simpleFoam 2>&1"
    env = dict(os.environ, OMPI_ALLOW_RUN_AS_ROOT="1", OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="1",
               OMPI_MCA_btl_vader_single_copy_mechanism="none")
    t0 = time.time()
    proc = subprocess.Popen(["bash", "-c", full], env=env)
    stopped_at = None
    while proc.poll() is None:
        time.sleep(sol["poll_s"])
        if not sol["watchdog"] or stopped_at is not None:
            continue
        try:
            it, rel, rfin = stability(cfg, case)
        except Exception:
            continue
        if it >= sol["min_iter"] and is_stable(cfg, rel, rfin):
            cd = case / "system/controlDict"
            cd.write_text(re.sub(r"\nstopAt\s+\w+;", "\nstopAt          writeNow;", cd.read_text()))
            stopped_at = it
            print(f"  watchdog: monitors stable at iteration {it} -> stopAt writeNow", flush=True)
    dt = time.time() - t0
    if proc.returncode != 0:
        tail = (case / "log.simpleFoam").read_text(errors="replace").splitlines()[-30:]
        raise RuntimeError("simpleFoam failed:\n" + "\n".join(tail))
    print(f"  {'simpleFoam':<24s} np={np_:<2d} {dt:7.1f} s", flush=True)
    return dt, stopped_at


def step_solve(cfg, case, np_, meta):
    write_fields(cfg, case, meta)
    t = {}
    if np_ > 1:
        t["decomposePar"] = run_foam("decomposePar -force", case, "log.decomposePar")
    t["simpleFoam"], stopped = run_solver_watched(cfg, case, np_)
    if np_ > 1:
        t["reconstructPar"] = run_foam("reconstructPar -latestTime", case, "log.reconstructPar")
    meta["watchdog_stop_iter"] = stopped
    return t


# --------------------------------------------------------------------------- driver
def resolve_config(cfg_path, overrides):
    cfg_path = Path(cfg_path).resolve()
    cfg = copy.deepcopy(DEFAULTS)
    deep_update(cfg, json.loads(cfg_path.read_text()))
    for o in overrides or []:
        k, v = o.split("=", 1)
        set_dotted(cfg, k, v)
    base = cfg_path.parent
    cfg["stl_dir"] = str((base / cfg.get("stl_dir", ".")).resolve())
    for name, s in cfg["surfaces"].items():
        bc = s.get("bc")
        if surface_kind(s) != "inlet":
            continue
        if not bc:
            raise ValueError(f"inlet {name} needs a bc")
        if bc["kind"] == "fan":
            bc["csv_resolved"] = str((base / bc["csv"]).resolve())
        elif bc["kind"] == "flowRate":
            bc["Q_m3_s_resolved"] = float(bc["Q_m3_s"])
        elif bc["kind"] == "velocity":
            import trimesh
            area = trimesh.load(Path(cfg["stl_dir"]) / s["file"], force="mesh").area * MM * MM
            bc["Q_m3_s_resolved"] = float(bc["U_m_s"]) * area
        else:
            raise ValueError(f"unknown bc kind {bc['kind']}")
    return cfg


def merge_timing(case, timing):
    prev = case / "results/timing.json"
    old = json.loads(prev.read_text()) if prev.exists() else {}
    old.update({k: round(v, 2) for k, v in timing.items()})
    old["mesh_solve_post_total"] = round(sum(old.get(k, 0) for k in ("mesh", "solve", "post")), 2)
    prev.write_text(json.dumps(old, indent=2))
    return old


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--workdir", default=DEFAULT_WORKDIR)
    ap.add_argument("--name")
    ap.add_argument("--np", type=int, default=4)
    ap.add_argument("--steps", default="mesh,solve,post")
    ap.add_argument("--set", action="append", dest="overrides")
    a = ap.parse_args(argv)

    cfg = resolve_config(a.config, a.overrides)
    name = a.name or f"{cfg['name']}_L{a.level}"
    case = Path(a.workdir).resolve() / name
    steps = a.steps.split(",")
    timing = {}
    T0 = time.time()
    print(f"[run_case] {name} -> {case}")
    if "mesh" in steps:
        meta = write_case(cfg, case, a.level, a.np)
        t0 = time.time()
        mesh = step_mesh(cfg, case, a.np)
        timing["mesh"] = time.time() - t0
        meta["mesh"] = mesh
        (case / "results/case_meta.json").write_text(json.dumps(meta, indent=2))
        print(f"  cells = {mesh['cells']}  checkMesh_ok = {mesh['checkMesh_ok']}")
    meta = json.loads((case / "results/case_meta.json").read_text())
    if "solve" in steps and "mesh" not in steps:   # refresh solver dicts + fan tables from config
        m2 = write_case(cfg, case, meta["level"], a.np, solver_only=True)
        meta.update({k: m2[k] for k in ("ambient_k", "ambient_omega")})
        for d in case.glob("processor*"):
            shutil.rmtree(d)
        for d in case.iterdir():                  # drop old time directories
            if d.is_dir() and re.fullmatch(r"[0-9.eE+-]+", d.name) and d.name != "0":
                shutil.rmtree(d)
        shutil.rmtree(case / "postProcessing", ignore_errors=True)
    (case / "results/config_resolved.json").write_text(json.dumps(cfg, indent=2))
    if "solve" in steps:
        t0 = time.time()
        meta["solve_time_s"] = step_solve(cfg, case, a.np, meta)
        timing["solve"] = time.time() - t0
        (case / "results/case_meta.json").write_text(json.dumps(meta, indent=2))
    if "post" in steps:
        from postprocess import postprocess
        t0 = time.time()
        res = postprocess(cfg, case, meta)
        timing["post"] = time.time() - t0
        res["timing_s"] = merge_timing(case, timing)
        res["np"] = a.np
        (case / "results/results.json").write_text(json.dumps(res, indent=2))
        print(json.dumps({k: res[k] for k in ("inlets", "convergence")}, indent=1)[:2000])
    else:
        merge_timing(case, timing)
    print(f"[run_case] done in {time.time() - T0:.1f} s -> {case}/results")
    return case


if __name__ == "__main__":
    main()
