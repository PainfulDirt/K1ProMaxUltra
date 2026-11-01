#!/usr/bin/env python3
"""Re-run only the post-processing of finished cases with the current probe definitions
(adds/updates planes that changed after the case was solved; the flow fields are not touched).

    $K1_PY repost.py SPEC [SPEC ...] [--level 2] [--tag TAG]      (SPEC as in run_cases.py)
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_cases  # noqa: E402

UPDATES = {
    "lidar_window": {"name": "lidar_window", "type": "rect", "origin": [-41.5, -17.5, 21.0], "normal": [0, 0, 1],
                     "u": [1, 0, 0], "half": [16.5, 12.5], "ds_mm": 0.4},
}


def patch(cfg_path):
    cfg = json.loads(Path(cfg_path).read_text())
    planes = cfg["probes"]["planes"]
    names = [p["name"] for p in planes]
    for k, v in UPDATES.items():
        if k in names:
            planes[names.index(k)] = v
    if "annulus_z03" not in names:
        z_eval = next(p["origin"][2] for p in planes if p["name"] == "layer_annulus")
        planes.insert(1, {"name": "annulus_z03", "type": "annulus", "origin": [0, 0, z_eval + 0.4],
                          "normal": [0, 0, 1], "u": [1, 0, 0], "r_in": 1.0, "r_out": 6.0, "sectors": 8,
                          "nr": 30, "ntheta": 144})
    Path(cfg_path).write_text(json.dumps(cfg, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    work = Path(run_cases.run_case.DEFAULT_WORKDIR)
    for spec in a.specs:
        parts = spec.split(":")
        d, env, curve = parts[0], parts[1] if len(parts) > 1 else "part", parts[2] if len(parts) > 2 else "estimated"
        name = f"{d}_{env}_{curve}" + (f"_{a.tag}" if a.tag else "") + f"_L{a.level}"
        patch(work / "geom" / name / "case.json")
        run_cases.run_one(spec, a.level, 4, None, a.tag, steps="post")


if __name__ == "__main__":
    main()
