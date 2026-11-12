#!/usr/bin/env python3
"""Recreate the CFD geometry (per-patch STL set) and the pipeline case config for a duct design.

    $K1_PY export_for_cfd.py S1 OUTDIR [--env part|lidar] [--json PARAMS.json]

Writes OUTDIR/<patch>.stl and OUTDIR/case.json (pipeline config, stl_dir = "."), plus
OUTDIR/geometry_report.json (checks, mass, ports). The environment model is identical for every
design (documentation/cfd-report.md, "Environment model"):

  nozzle   cone, tip flat d1.0 at Z 0 -> d6.9 at Z 2.5, then a d6.9 cylinder into the sock
  sock     solid block = interfaces.SOCK (heater inside is solid); its d7 bottom opening is filled
           by the d6.9 nozzle body (0.05 mm radial gap closed)
  heatsink block = interfaces.HEATSINK, joined to the sock by a solid neck (heat-break/plate)
  part     PART_PROXY 20 x 20, top at Z -0.2, standing on the bed (BED_Z, wall)      [env part]
  bed      flat wall at Z -3 (nozzle 3 mm above the bed while LiDAR scanning), no part [env lidar]
  air box  X -70..70, Y -80..55, Z bed..45, other faces open (totalPressure 0)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from build123d import Solid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from duct_generator import (CB, I, build_ducts, build_info, get_params, box_solid, fuse_all)  # noqa: E402

PIPE = HERE.parents[2] / "simulations/cfd/pipeline"
sys.path.insert(0, str(PIPE))
from geometry import export_patches  # noqa: E402

FANS_DIR = HERE.parents[2] / "components/fans/pq-curves"
DOMAIN = {"min": [-70.0, -80.0, float(I.BED_Z)], "max": [70.0, 55.0, 45.0]}
SOCK_Z0 = I.SOCK.zmin


def hotend():
    tip_r = float(I.NOZZLE_TIP_FLAT_D) / 2
    R = float(I.NOZZLE_MAX_D) / 2
    zc = float(I.NOZZLE_CONE_TOP_Z)
    cone = Solid.make_cone(tip_r, R, zc)
    cyl = Solid.make_cylinder(R, SOCK_Z0 + 1.0 - zc).translate((0, 0, zc))
    s = I.SOCK
    sock = box_solid(s.xmin, s.xmax, s.ymin, s.ymax, s.zmin, s.zmax)
    h = I.HEATSINK
    neck = box_solid(-10.0, 10.0, -8.0, 8.0, s.zmax - 0.5, h.zmin + 0.5)
    hs = box_solid(h.xmin, h.xmax, h.ymin, h.ymax, h.zmin, h.zmax)
    return fuse_all([cone, cyl, sock, neck, hs])


def part_proxy(env="part"):
    p = I.PART_PROXY
    if env == "plate":       # review R-10: large flat part (120 x 120 mm, same top Z) instead of the 20 mm block
        h = PLATE_HALF
        return box_solid(-h, h, -h, h, p.zmin - 5.0, p.zmax)
    return box_solid(p.xmin, p.xmax, p.ymin, p.ymax, p.zmin - 5.0, p.zmax)   # penetrates the bed


# review R-10 environment variants (ESTIMATED geometry, CFD only)
PLATE_HALF = 60.0
DOMAIN_PLATE = {"min": [-80.0, -85.0, float(I.BED_Z)], "max": [80.0, 75.0, 45.0]}


def probe_body():
    """MicroProbe V2 as a solid wall (ESTIMATED): flange footprint 21.93 x 15.6 (BIQU drawing, VERIFIED) at
    X +-10.97, Y = interfaces.PROBE_BODY_Y (ESTIMATED 12.5..28.1), from the mount face Z 26.75 (ESTIMATED) down
    to the body bottom 23.98 below it (Z 2.77; BIQU drawing), modelled as one box (the real body is narrower
    under the flange); stowed pin (d 2, to Z 1.45) included; plus the 785004 adapter box
    (interfaces.PROBE_ADAPTER_785004, ESTIMATED) clipped at the domain top."""
    zf = float(I.PROBE_MOUNT_FACE_Z)
    y0, y1 = float(I.PROBE_BODY_Y[0]), float(I.PROBE_BODY_Y[1])
    hx = float(I.PROBE_FLANGE[0]) / 2
    body = box_solid(-hx, hx, y0, y1, zf - 23.98, zf)
    pin = Solid.make_cylinder(1.0, zf - 23.98 - float(I.PROBE_STOWED_TIP_Z) + 0.5).translate(
        (float(I.PROBE_X), float(I.PROBE_Y), float(I.PROBE_STOWED_TIP_Z)))
    a = I.PROBE_ADAPTER_785004
    ad = box_solid(a.xmin, a.xmax, a.ymin, a.ymax, a.zmin - 0.5, min(a.zmax, DOMAIN["max"][2] + 5.0))
    return fuse_all([body, pin, ad])


def _bb(f):
    b = f.bounding_box()
    return np.array(tuple(b.min)), np.array(tuple(b.max))


def export_env(outdir, env="part"):
    he = hotend()
    zs = SOCK_Z0

    def is_nozzle(f):
        lo, hi = _bb(f)
        return hi[2] <= zs + 1e-6 and f.geom_type.name in ("CONE", "CYLINDER", "PLANE") and hi[2] - lo[2] >= 0 \
            and max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1])) < 3.6

    def is_sock(f):
        lo, hi = _bb(f)
        return lo[2] >= zs - 1e-6 and hi[2] <= I.SOCK.zmax + 1e-6
    c = export_patches(he, {"nozzle": is_nozzle, "sock": is_sock}, default="heatsink", outdir=outdir)
    if env == "probe":
        c.update(export_patches(probe_body(), {}, default="probe", outdir=outdir))
    if env in ("part", "plate", "probe"):
        p = part_proxy(env)
        top = float(I.PART_PROXY.zmax)
        c.update(export_patches(p, {"part_top": lambda f: f.geom_type.name == "PLANE" and
                                    abs(_bb(f)[0][2] - top) < 1e-6 and abs(_bb(f)[1][2] - top) < 1e-6},
                                default="part_side", outdir=outdir))
    return c


def export_duct(params, outdir, parts=None):
    parts = parts or build_ducts(params, with_print_extras=True)
    body = parts["body_cfd"]
    rules = {}
    for fid, fan in params["fans"].items():
        oc = np.array(fan["outlet_c"], float)
        bl = np.array(fan["blow"], float)
        half = np.abs(np.array(fan["outlet_u"])) * fan["outlet_a"] / 2 + np.abs(np.array(fan["outlet_v"])) * fan["outlet_b"] / 2

        def pred(f, oc=oc, bl=bl, half=half):
            if f.geom_type.name != "PLANE":
                return False
            lo, hi = _bb(f)
            if np.any(lo < oc - half - 1e-4) or np.any(hi > oc + half + 1e-4):
                return False
            n = np.array(tuple(f.normal_at(f.center())))
            return float(n @ bl) > 0.999 and abs(float((np.array(tuple(f.center())) - oc) @ bl)) < 1e-4
        rules[f"inlet_{fid}"] = pred
    counts = export_patches(body, rules, default="duct", outdir=outdir)
    areas = {}
    for name in rules:
        import trimesh
        m = trimesh.load(Path(outdir) / f"{name}.stl", force="mesh")
        areas[name] = float(m.area)
    return parts, counts, areas


def split_inlet(outdir, cfg, fid, frac_xp, Q_Lps):
    """Review R-09 inlet-profile sensitivity: split the fan outlet patch into its -X and +X halves and impose
    fixed flow rates (fraction frac_xp of Q through the +X half = the scroll's outer-wall side of the stock
    4020, whose outlet blows -Z at the fan's right edge). Q is held at the uniform-inlet operating point."""
    import trimesh
    f = Path(outdir) / f"inlet_{fid}.stl"
    m = trimesh.load(f, force="mesh")
    lo, hi = m.bounds
    z = float(lo[2])
    nz = float(np.sign(m.face_normals[:, 2].mean()))
    xm = 0.5 * (lo[0] + hi[0])
    surf = cfg["surfaces"].pop(f"inlet_{fid}")
    for tag, (x0, x1), fr in (("a", (lo[0], xm), 1.0 - frac_xp), ("b", (xm, hi[0]), frac_xp)):
        v = np.array([[x0, lo[1], z], [x1, lo[1], z], [x1, hi[1], z], [x0, hi[1], z]])
        faces = np.array([[0, 1, 2], [0, 2, 3]]) if nz > 0 else np.array([[0, 2, 1], [0, 3, 2]])
        trimesh.Trimesh(v, faces, process=False).export(Path(outdir) / f"inlet_{fid}{tag}.stl")
        s2 = dict(surf, file=f"inlet_{fid}{tag}.stl", bc={"kind": "flowRate", "Q_m3_s": fr * Q_Lps * 1e-3})
        cfg["surfaces"][f"inlet_{fid}{tag}"] = s2
    f.unlink()
    cfg["_design"]["inlet_split"] = {"fan": fid, "fraction_+X_half": frac_xp, "Q_Lps": Q_Lps,
                                     "velocity_ratio_+X/-X": round(frac_xp / (1 - frac_xp), 3)}
    return cfg


def fan_csv(ftype, curve="estimated"):
    names = {("4020", "estimated"): "creality_K1_stock_4020_blower.csv",
             ("4020", "proxy"): "creality_K1_stock_4020_blower_proxy-scaled.csv",
             ("5015", "estimated"): "sunon_MF50152VX-1L02C-A99.csv",
             ("5015", "proxy"): "sunon_MF50152VX-1L02C-A99_proxy-scaled.csv",
             ("delta", "digitized"): "delta_BFB0524HH_digitized.csv",
             ("samesky", "digitized"): "samesky_CBM-5015BF-175-459-22_digitized.csv",
             ("delta", "minspec"): "../../../simulations/cfd/cases/fan_curves/delta_BFB0524HH_minspec.csv",
             ("delta", "estimated"): "delta_BFB0524HH.csv"}
    return str(FANS_DIR / names[(ftype, curve)])


def case_config(params, rep, info, areas, env="part", curve="estimated", name=None):
    surf = {
        "duct": {"file": "duct.stl", "type": "wall", "level": [3, 3], "feature_level": 3},
        "nozzle": {"file": "nozzle.stl", "type": "wall", "level": [4, 4], "feature_level": 4},
        "sock": {"file": "sock.stl", "type": "wall", "level": [3, 3], "feature_level": 3},
        "heatsink": {"file": "heatsink.stl", "type": "wall", "level": [1, 2], "feature_level": 2},
    }
    lidar = env == "lidar"
    if env == "probe":
        surf["probe"] = {"file": "probe.stl", "type": "wall", "level": [2, 3], "feature_level": 2}
    if not lidar:
        surf["part_top"] = {"file": "part_top.stl", "type": "wall", "level": [3, 3], "feature_level": 3}
        surf["part_side"] = {"file": "part_side.stl", "type": "wall", "level": [2, 2], "feature_level": 2}
    for fid, fan in params["fans"].items():
        ft = fan.get("curve_type", fan["type"])
        surf[f"inlet_{fid}"] = {"file": f"inlet_{fid}.stl", "type": "inlet", "level": [3, 3],
                                "bc": {"kind": "fan", "csv": fan_csv(ft, curve)}}
    dom = DOMAIN_PLATE if env == "plate" else DOMAIN
    dmin = list(dom["min"])
    z_eval = -2.9 if lidar else -0.1
    if env == "lidar":
        dmin[2] = -3.0
    planes = [
        {"name": "layer_annulus", "type": "annulus", "origin": [0, 0, z_eval], "normal": [0, 0, 1], "u": [1, 0, 0],
         "r_in": 1.0, "r_out": 6.0, "sectors": 8, "nr": 30, "ntheta": 144},
        {"name": "annulus_z03", "type": "annulus", "origin": [0, 0, z_eval + 0.4], "normal": [0, 0, 1],
         "u": [1, 0, 0], "r_in": 1.0, "r_out": 6.0, "sectors": 8, "nr": 30, "ntheta": 144},
        {"name": "ring_z1", "type": "annulus", "origin": [0, 0, 1.0], "normal": [0, 0, 1], "u": [1, 0, 0],
         "r_in": 4.0, "r_out": 10.0, "sectors": 8, "nr": 30, "ntheta": 144},
    ]
    points, lines, loss = [], [], []
    for g in info["ports"]:
        dh = np.array(g["dir_h"])
        lat = np.array(g["lat"])
        c = np.array(g["c_out"]) + 0.3 * dh
        planes.append({"name": f"port_{g['az']}", "type": "rect", "origin": c.round(4).tolist(),
                       "normal": dh.round(6).tolist(), "u": lat.round(6).tolist(),
                       "half": [g["w"] / 2 + 0.15, g["h"] / 2 + 0.15], "ds_mm": 0.08})
        points.append({"name": f"jet_{g['az']}", "xyz": (np.array(g["c_out"]) + 3.0 * dh).round(3).tolist()})
    for f in info["feeds"]:
        fid = f["fan"]
        cl = [np.array(p) for p in f["centerline"]]
        fan = params["fans"][fid]
        # feed plane: the section 2 (after settling / morph), normal = local flow direction
        k = 2 if len(cl) > 3 else 1
        d = cl[k + 1] - cl[k] if k + 1 < len(cl) else cl[k] - cl[k - 1]
        d = d / np.linalg.norm(d)
        if f["kind"] in ("right", "front_plenum", "direct", "stock"):
            # 2 mm below the outlet of a fan blowing -Z (inside the drop, before it merges with the
            # plenum/manifold); normal = the fan's blow direction
            o = cl[1]
            d = np.array(fan["blow"], float)
        else:
            o = cl[k]
        ext = max(fan["outlet_a"], fan["outlet_b"]) / 2 + 1.5
        u = np.cross(d, [0, 0, 1]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        planes.append({"name": f"feed_{fid}", "type": "rect", "origin": o.round(4).tolist(), "normal": d.round(6).tolist(),
                       "u": (u / np.linalg.norm(u)).round(6).tolist(), "half": [ext, ext], "ds_mm": 0.15})
        loss.append([f"inlet_{fid}", f"feed_{fid}"])
        for g in info["ports"]:
            loss.append([f"inlet_{fid}", f"port_{g['az']}"])
        lines.append({"name": f"feed_{fid}_centerline", "points": [p.round(3).tolist() for p in cl]})
    # LiDAR line region (dedicated check uses the bed at Z -3; here it is the part-top level)
    planes.append({"name": "lidar_line", "type": "rect", "origin": [-36.2, -21.34, z_eval if lidar else -0.5],
                   "normal": [0, 0, 1], "u": [1, 0, 0], "half": [14.6, 1.5], "ds_mm": 0.2})
    # LiDAR window region proxy: just below the module body underside (Z 18..22, research/01 §H)
    # LiDAR window region proxy: 1 mm under the module body (underside ~Z 22, outside the stock cover
    # X <= -24, research/01 H): X -58..-25, Y -30..-5
    planes.append({"name": "lidar_window", "type": "rect", "origin": [-41.5, -17.5, 21.0], "normal": [0, 0, 1],
                   "u": [1, 0, 0], "half": [16.5, 12.5], "ds_mm": 0.4})
    points += [{"name": "lidar_line_centre", "xyz": [-36.0, -21.34, z_eval if lidar else -0.5]},
               {"name": "below_tip", "xyz": [0, 0, z_eval]}]
    walls = []
    if not lidar:
        walls += [{"name": "part_top_r5", "patch": "part_top", "r_max": 5.0},
                  {"name": "part_top_r10", "patch": "part_top", "r_max": 10.0},
                  {"name": "part_top_all", "patch": "part_top"}]
        for nm, nrm in (("xp", [1, 0, 0]), ("xm", [-1, 0, 0]), ("yp", [0, 1, 0]), ("ym", [0, -1, 0])):
            walls.append({"name": f"part_side_{nm}_top3", "patch": "part_side", "z_min": -3.2, "normal": nrm})
    walls += [{"name": "nozzle_all", "patch": "nozzle"},
              {"name": "nozzle_cone", "patch": "nozzle", "z_max": 2.5},
              {"name": "sock_bottom", "patch": "sock", "z_max": SOCK_Z0 + 0.05, "normal": [0, 0, -1]}]
    cfg = {
        "name": name or f"{params['name']}_{env}_{curve}",
        "stl_dir": ".",
        "surfaces": surf,
        "domain": {"min": dmin, "max": dom["max"], "cell_mm": 3.2,
                   "patches": {"zmin": {"name": "bed", "type": "wall"}}},
        "location_in_mesh": [70.0, -75.0, -10.0] if env == "plate" else [55.0, -65.0, max(dmin[2] + 3.0, -10.0)],
        "refinement_boxes": [
            {"name": "near", "min": [-30, -30, dmin[2] if lidar else -3.0], "max": [32, 26, 14], "level": 2},
            {"name": "jets", "min": [-17, -17, -3.0 if lidar else -0.2], "max": [17, 17, 6.5], "level": 3},
            {"name": "tip", "min": [-6.5, -6.5, -3.0 if lidar else -0.2], "max": [6.5, 6.5, 1.5], "level": 4},
        ],
        "probes": {"planes": planes, "points": points, "lines": lines, "walls": walls},
        "loss_pairs": loss,
        "plots": {"slices": [
            {"name": "xz_y0", "axis": "y", "value": 0.0, "range": [[-30, 34], [-3.5 if lidar else -4, 26]]},
            {"name": "yz_x0", "axis": "x", "value": 0.0, "range": [[-36, 28], [-3.5 if lidar else -4, 26]]},
            {"name": "xy_zeval", "axis": "z", "value": z_eval, "range": [[-26, 26], [-26, 26]]},
            {"name": "xy_z4", "axis": "z", "value": 4.0, "range": [[-34, 34], [-34, 30]]}],
            "streamlines": True,
            "camera": {"position": [70, -110, 70], "focal": [2, -4, 6], "up": [0, 0, 1]}},
        "fluid": {"nu": 1.6e-5, "rho": 1.16},
        "mesh": {"n_between": 2},
        # weakly unsteady jets: the residuals plateau (U ~ 5e-3), so stop on the integral monitors
        # (fan Q and p within 0.4 % over 100 iterations) and report fields averaged from iteration 300
        "solver": {"max_iter": 750, "min_iter": 550, "average_start": 300, "tol_Q": 0.004, "tol_p": 0.004,
                   "tol_probe": 1.0e9, "res_p_max": 1.0e-2, "res_U_max": 3.0e-2},
        "_design": {"param_set": params["name"], "env": env, "fan_curve": curve,
                    "outlet_area_total_mm2": rep["outlet_area_total_mm2"],
                    "inlet_areas_mm2": areas, "mass": rep["mass"]},
    }
    if env == "lidar":
        cfg["refinement_boxes"].append({"name": "lidar_line", "min": [-53, -27, -3.0], "max": [-19, -15, 1.0], "level": 2})
        cfg["plots"]["slices"].append({"name": "lidar_yz_xm36", "axis": "x", "value": -36.0,
                                       "range": [[-40, 20], [-3.5, 26]]})
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("param_set")
    ap.add_argument("outdir")
    ap.add_argument("--env", default="part", choices=["part", "lidar", "plate", "probe"])
    ap.add_argument("--curve", default="estimated")
    ap.add_argument("--json", help="parameter set JSON file (instead of a named set)")
    ap.add_argument("--name")
    ap.add_argument("--inlet-split", type=float, help="fraction of Q through the +X half of the fan outlet (R-09)")
    ap.add_argument("--inlet-q", type=float, help="total flow [L/s] with --inlet-split")
    a = ap.parse_args(argv)
    params = json.loads(Path(a.json).read_text()) if a.json else get_params(a.param_set)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.stl"):
        f.unlink()
    parts, counts, areas = export_duct(params, out)
    counts.update(export_env(out, a.env))
    rep = build_info(params, parts)
    info = parts["_info"]
    cfg = case_config(params, rep, info, areas, env=a.env, curve=a.curve, name=a.name)
    if a.inlet_split is not None:
        for fid in params["fans"]:
            split_inlet(out, cfg, fid, a.inlet_split, a.inlet_q)
    (out / "case.json").write_text(json.dumps(cfg, indent=1, default=float))
    (out / "geometry_report.json").write_text(json.dumps(rep, indent=1, default=float))
    (out / "params.json").write_text(json.dumps(params, indent=1, default=float))
    print(json.dumps({"tris": counts, "inlet_areas": areas, "case": str(out / "case.json")}, indent=1))
    return out / "case.json"


if __name__ == "__main__":
    main()
