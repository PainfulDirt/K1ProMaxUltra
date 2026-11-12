#!/usr/bin/env python3
"""Run duct-design CFD cases sequentially: geometry -> pipeline (mesh, solve, post) -> results copy -> summary.

    $K1_PY run_cases.py SPEC [SPEC ...] [--level 2] [--np 4] [--set key=value ...] [--tag TAG]

SPEC = <design>[:<env>[:<curve>]]
    design : a parameter-set name from cad/source/ducts (REF, S1, D1, U1, UD1, S2 ...), a JSON file with
             a parameter set, or STOCK (Henlor stock cover + duct, cases/stock_geometry.py)
    env    : part (default; 20 mm part proxy on the bed)  |  lidar (nozzle 3 mm over a flat bed, no part)
    curve  : estimated (default)  |  proxy (lower-bound 4020 / digitized-shape Sunon)  |  digitized (Delta)

The case name is <design>_<env>_<curve>[_<tag>]_L<level>. Full cases go to the pipeline work dir
($K1_CFD_WORKDIR or the session scratchpad); results.json + selected PNGs are copied to
simulations/cfd/results/<case>/ and summary.csv / summary.json are rebuilt from every results.json.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TH = HERE.parents[2]
CFD = TH / "simulations/cfd"
sys.path.insert(0, str(CFD / "pipeline"))
sys.path.insert(0, str(TH / "cad/source/ducts"))
import run_case  # noqa: E402

RESULTS = CFD / "results"
# thermal proxy (cfd-report §7): part skin 200 C, nozzle 250 C (ABS), sock outer surface 150 C (ESTIMATED),
# fan / chamber air 45 C; heatsink, duct, bed adiabatic
THERMAL_DEFAULT = {"T_inf": 45.0, "walls": {"part_top": 200.0, "part_side": 200.0, "nozzle": 250.0, "sock": 150.0},
                   "iters": 200}
KEEP_PNG = ("slice_xz_y0_Umag.png", "slice_yz_x0_Umag.png", "slice_xy_zeval_Umag.png", "slice_xy_z4_Umag.png",
            "streamlines3d.png", "convergence.png", "slice_lidar_yz_xm36_Umag.png", "line_feed_F_centerline.png")


def geometry(design, env, curve, gdir):
    if design == "STOCK":
        from stock_geometry import build
        return build(HERE / "stock", gdir, env, curve)
    import export_for_cfd
    argv = [design, str(gdir), "--env", env, "--curve", curve]
    if design.endswith(".json"):
        argv = ["custom", str(gdir), "--env", env, "--curve", curve, "--json", design]
    return export_for_cfd.main(argv)


def find_mesh_donor(work, dname, env, curve, tag, level):
    """A finished case of the same design/env/tag/level (any fan curve): its mesh is identical."""
    for d in sorted(work.glob(f"{dname}_{env}_*_L{level}")):
        parts = d.name[len(f"{dname}_{env}_"):-len(f"_L{level}")].split("_", 1)
        if parts[0] == curve or (parts[1] if len(parts) > 1 else "") != tag:
            continue
        if (d / "constant/polyMesh/owner").exists() and (d / "results/case_meta.json").exists():
            return d
    return None


def reuse_mesh(donor, case):
    if case.exists():
        shutil.rmtree(case)
    case.mkdir(parents=True)
    shutil.copytree(donor / "constant", case / "constant")
    shutil.copytree(donor / "system", case / "system")
    (case / "results").mkdir()
    shutil.copy(donor / "results/case_meta.json", case / "results/case_meta.json")
    (case / "case.foam").touch()
    for f in donor.glob("log.*Mesh*"):
        shutil.copy(f, case / f.name)


def run_one(spec, level, np_, sets, tag, keep_png=KEEP_PNG, steps="mesh,solve,post"):
    parts = spec.split(":")
    design = parts[0]
    env = parts[1] if len(parts) > 1 else "part"
    curve = parts[2] if len(parts) > 2 else "estimated"
    dname = Path(design).stem if design.endswith(".json") else design
    name = f"{dname}_{env}_{curve}" + (f"_{tag}" if tag else "") + f"_L{level}"
    work = Path(run_case.DEFAULT_WORKDIR)
    gdir = work / "geom" / name
    t0 = time.time()
    if "mesh" in steps:
        cfg = geometry(design, env, curve, gdir)
        donor = find_mesh_donor(work, dname, env, curve, tag, level)
        if donor is not None and steps == "mesh,solve,post":      # same geometry, other fan curve
            print(f"  reusing mesh of {donor.name}", flush=True)
            reuse_mesh(donor, work / name)
            steps = "solve,post"
    else:
        cfg = gdir / "case.json"
    argv = [str(cfg), "--level", str(level), "--np", str(np_), "--name", name, "--steps", steps]
    for s_ in sets or []:
        argv += ["--set", s_]
    if "thermal" in steps and not any(s_.startswith("thermal") for s_ in sets or []):
        argv += ["--set", "thermal=" + json.dumps(THERMAL_DEFAULT)]
    case = run_case.main(argv)
    out = RESULTS / (name + ("_thermal" if "thermal" in steps else ""))
    out.mkdir(parents=True, exist_ok=True)
    res = json.loads((case / "results/results.json").read_text())
    res["_spec"] = {"design": dname, "env": env, "curve": curve, "tag": tag, "level": level, "sets": sets,
                    "wall_time_total_s": round(time.time() - t0, 1)}
    try:
        res["_geometry"] = json.loads((gdir / "geometry_report.json").read_text())
    except Exception:
        pass
    (out / "results.json").write_text(json.dumps(res, indent=1, default=float))
    for png in keep_png:
        if (case / "results" / png).exists():
            shutil.copy(case / "results" / png, out / png)
    for d in case.glob("processor*"):           # keep the work dir light; reconstructed case remains
        shutil.rmtree(d, ignore_errors=True)
    import summarize
    summarize.main()
    return case, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--np", type=int, default=4)
    ap.add_argument("--set", action="append", dest="sets")
    ap.add_argument("--tag", default="")
    ap.add_argument("--steps", default="mesh,solve,post")
    a = ap.parse_args()
    for spec in a.specs:
        t0 = time.time()
        print(f"===== {spec}", flush=True)
        try:
            run_one(spec, a.level, a.np, a.sets, a.tag, steps=a.steps)
        except Exception as e:  # keep going with the next case
            import traceback
            traceback.print_exc()
            print(f"!!!!! {spec} failed: {e!r}", flush=True)
        print(f"===== {spec} done in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
