#!/usr/bin/env python3
"""STOCK baseline geometry for the CFD comparison (K1 stock part-cooling: cover + duct + 4020).

Source CAD: Henlor, "Creality K1 assembly" (Printables 742370, CC BY 4.0) - parts
"Creality K1 Fan Duct v5", "toolhead-cover-cad v38" (the same cover Henlor published as Printables
687411, public domain) and "Blower Fan 4020 v14", moved to the nozzle frame with
interfaces.HENLOR_TO_NOZZLE. Credit: Henlor. The duct is a reverse-engineered thin shell; its outlet
slots are approximate (research/02 C6).

    $K1_PY stock_geometry.py STEP_DIR OUTDIR [--env part|lidar] [--curve estimated|proxy]

STEP_DIR holds stock_duct.step, stock_cover.step (nozzle frame), as cached in cases/stock/.
The 4020 is modelled as its envelope box (interfaces.STOCK_4020_POS) with the outlet (17 x 13,
interfaces.BLOWER_4020_STOCK, at the bottom-right corner per 02:C8) as the fan inlet patch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from build123d import import_step

HERE = Path(__file__).resolve().parent
TH = HERE.parents[2]
sys.path.insert(0, str(TH / "cad/source/ducts"))
sys.path.insert(0, str(TH / "simulations/cfd/pipeline"))
from duct_generator import I, box_solid  # noqa: E402
from export_for_cfd import case_config, export_env  # noqa: E402
from geometry import export_patches  # noqa: E402

COVER_CLIP_Z = 32.0


def _unzip(p):
    """Accept name.step or name.step.gz (the repo keeps the gzipped copies)."""
    import gzip
    import tempfile
    if p.exists():
        return str(p)
    gz = Path(str(p) + ".gz")
    tmp = Path(tempfile.mkdtemp()) / p.name
    tmp.write_bytes(gzip.decompress(gz.read_bytes()))
    return str(tmp)


def stock_fan():
    b = I.STOCK_4020_POS
    a_t, a_w = I.BLOWER_4020_STOCK.outlet          # 17 along the thickness (Y), 13 along the edge (X)
    oc = np.array([b.xmax - a_w / 2, (b.ymin + b.ymax) / 2, b.zmin])
    return {"type": "4020", "box": (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax), "outlet_c": oc.tolist(),
            "outlet_u": [-1, 0, 0], "outlet_v": [0, 1, 0], "outlet_a": a_w, "outlet_b": a_t,
            "blow": [0, 0, -1], "intake": [0, -1, 0], "holes": [], "spec": I.BLOWER_4020_STOCK.name,
            "mass_g": float(I.BLOWER_4020_STOCK.mass_g)}


def build(step_dir, outdir, env="part", curve="estimated"):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("*.stl"):
        f.unlink()
    duct = import_step(_unzip(Path(step_dir) / "stock_duct.step"))
    cover = import_step(_unzip(Path(step_dir) / "stock_cover.step"))
    duct = duct.solids()[0] if duct.solids() else duct
    cs = cover.solids()
    cover = cs[0] if len(cs) == 1 else cover
    cover = cover & box_solid(-60, 60, -80, 40, 0, COVER_CLIP_Z)
    fan = stock_fan()
    b = fan["box"]
    oc = np.array(fan["outlet_c"])
    a, bb = fan["outlet_a"], fan["outlet_b"]
    # fan body clipped above the domain; outlet = a 0.5 mm recess in its bottom face (own B-rep face)
    body = box_solid(b[0], b[1], b[2], b[3], b[4], 50.0)
    recess = box_solid(oc[0] - a / 2, oc[0] + a / 2, oc[1] - bb / 2, oc[1] + bb / 2, b[4] - 1.0, b[4] + 0.5)
    fanbody = body - recess
    zin = b[4] + 0.5

    def is_inlet(f):
        if f.geom_type.name != "PLANE":
            return False
        bx = f.bounding_box()
        return abs(bx.min.Z - zin) < 1e-6 and abs(bx.max.Z - zin) < 1e-6
    c = export_patches(fanbody, {"inlet_F": is_inlet}, default="fan", outdir=outdir)
    c.update(export_patches(duct, {}, default="stock_duct", outdir=outdir))
    c.update(export_patches(cover, {}, default="stock_cover", outdir=outdir))
    c.update(export_env(outdir, env))
    import trimesh
    area = float(trimesh.load(outdir / "inlet_F.stl", force="mesh").area)
    params = {"name": "STOCK", "label": "STOCK: K1 stock cover + duct (Henlor 742370/687411) + 4020 at the stock pose",
              "fans": {"F": fan}}
    info = {"ports": [], "feeds": [{"fan": "F", "kind": "stock",
                                    "centerline": [oc.tolist(), (oc + [0, 0, -1.5]).tolist(),
                                                   (oc + [0, 0, -3.0]).tolist(), (oc + [0, 0, -5.0]).tolist(),
                                                   [8.0, -20.0, 18.0], [0.0, -12.0, 10.0]]}]}
    rep = {"outlet_area_total_mm2": None, "mass": {"note": "stock cover+duct ~23.8 g measured (02 C1/C4), 4020 24 g"}}
    cfg = case_config(params, rep, info, {"inlet_F": area}, env=env, curve=curve, name=f"STOCK_{env}_{curve}")
    s = cfg["surfaces"]
    s.pop("duct")
    s["fan"] = {"file": "fan.stl", "type": "wall", "level": [2, 3], "feature_level": 2}
    s["stock_duct"] = {"file": "stock_duct.stl", "type": "wall", "level": [3, 3], "feature_level": 3}
    s["stock_cover"] = {"file": "stock_cover.stl", "type": "wall", "level": [3, 3], "feature_level": 3}
    s["inlet_F"]["level"] = [3, 3]
    # the stock slots are at Z 7..10 around the sock: refine that band too
    cfg["refinement_boxes"].append({"name": "stock_slots", "min": [-21, -20, 5.5], "max": [21, 6, 11.5], "level": 3})
    cfg["_design"]["source"] = "Henlor Printables 742370 (CC BY 4.0) / 687411 (public domain)"
    (outdir / "case.json").write_text(json.dumps(cfg, indent=1, default=float))
    (outdir / "geometry_report.json").write_text(json.dumps(
        {"inlet_area_mm2": area, "tris": c, "cover_clip_z": COVER_CLIP_Z, "fan": fan}, indent=1, default=float))
    print(json.dumps({"tris": c, "inlet_area": area}, indent=1))
    return outdir / "case.json"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step_dir")
    ap.add_argument("outdir")
    ap.add_argument("--env", default="part")
    ap.add_argument("--curve", default="estimated")
    a = ap.parse_args()
    build(a.step_dir, a.outdir, a.env, a.curve)
