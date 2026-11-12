#!/usr/bin/env python3
"""Automated design checks for the K1 Max toolhead structure.

    python cad/source/validate.py [--cooling auto-final|ducts|auto|stub] [--samples N] [--no-stock-cache]

Writes cad/exports/validation_report.{json,md}. Exit code 1 if any check FAILs
(WARN/INFO never fail). Checks:
  1. per printed part: OCC validity, single solid, watertight mesh, volume,
     mass, bbox, sample-based minimum wall, overhang share in print orientation;
  2. pairwise interference (printed/stub vs everything, reference vs reference
     skipped) with an allow-list of intended contacts;
  3. clearances: hot zone, LiDAR boxes + laser sheet, DUCT_MIN_Z, rear limit,
     PCB component zone, 3010 intake area, the real duct's air path, the
     cover's clearance to duct/frame, the frame's fan/duct mount points;
     soft envelope limits;
  4. moving-mass budget vs stock and the X/Y input-shaper shift (f ~ 1/sqrt(m));
  5. stiffness estimates (structure/stiffness.py);
  6. per-part dependency on ESTIMATED/MISSING/STUB values -> release status.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import trimesh  # noqa: E402

import assembly  # noqa: E402
import interfaces as I  # noqa: E402
from build123d import Pos, Rot  # noqa: E402
from structure import common, frame, stiffness, reference, probe_mount, cover  # noqa: E402
from structure.common import bx, ibox, cyl_y, MATERIALS  # noqa: E402

EXPORTS = HERE.parent / "exports"
VOL_TOL = 1e-3            # mm3: overlaps below this are numerical noise (touching faces)
PEN_TOL = 0.1             # mm: overlap thinner than this with a reverse-engineered stock solid = contact (model accuracy)
CONTACT_TOL = 0.01        # mm: closer than this = contact
MIN_WALL = 0.8            # mm: 2 extrusion lines at 0.4 (DESIGN)
WALL_FAIL_SHARE = 0.005   # FAIL if more than 0.5 % of sampled surface is thinner than MIN_WALL
OVERHANG_DEG = 45.0

# Intended contacts / overlaps: (part A, part B prefix, kind, reason)
ALLOW = [
    ("cooling_module_frame", "ref_pcb", "contact", "boss pads bear on the PCB front face / 4th pad on the 2nd plate"),
    ("cooling_module_frame", "stock_pcb", "contact", "boss pads bear on the PCB front face / 4th pad on the 2nd plate"),
    ("cooling_module_frame", "ref_blower_", "contact", "fan screw standoffs"),
    ("cooling_module_frame", "stub_duct_placeholder", "contact", "duct-to-frame mount lugs"),
    ("cooling_module_frame", "duct_body", "contact", "duct-to-frame mount lugs"),
    ("cover", "cooling_module_frame", "contact", "cover top wall bears on the frame shelf top (Z FRAME_ZMAX), "
     "clamped by the 2 cover screws; elsewhere >= COVER_YIELD_CLEAR (separate check)"),
    ("probe_mount", "ref_microprobe_body", "contact", "probe flange seat"),
    ("probe_mount", "stock_carriage", "contact", "anchor: roof bears on the carriage tab tops (anchor-shifted carriage)"),
    ("stub_duct_placeholder", "ref_blower_", "contact", "duct inlet on the blower outlet"),
    ("duct_body", "ref_blower_", "overlap", "duct fan socket slides over the fan outlet nozzle (not in the envelope box)"),
]

ANCHOR_FAMILY = {"stock_carriage", "stock_bushing_1", "stock_bushing_2", "stock_x_rod_1", "stock_x_rod_2",
                 "stock_belt_retainer_1", "stock_belt_retainer_2", "ref_x_rod_1", "ref_x_rod_2"}

# Keep-out boxes that overlap stock parts by design (interfaces.py consistency check):
# (box name, stock part, max X penetration from the box's inner face, reason)
KEEPOUT_STOCK_EXPECTED = [
    ("LIDAR_RESERVED_BODY", "stock_carriage", I.LIDAR_RESERVED_BODY.xmax - I.XCARRIAGE.xmin,
     "expected: LIDAR_RESERVED_BODY is module + bracket (interfaces.py) and the stock bracket attaches to the "
     "toolhead's left side (research/01 sH.2; 02 s7 item 2 lists the LiDAR bracket holes on the carriage). The "
     "box's inner face X -24.0 (stock cover width) lies 1.2 mm inside the carriage's left face X -25.2 (02:N1): "
     "that slab is where the bracket seats. Box kept as is until M6 (bracket position)"),
]

RESULTS = {"checks": [], "parts": {}, "interference": [], "clearance": {}, "mass": {}, "stiffness": {},
           "release": {}, "unconfirmed_global": []}


def check(name, status, detail="", **data):
    RESULTS["checks"].append({"check": name, "status": status, "detail": detail, **data})
    print(f"[{status:4s}] {name}: {detail}")


def allowed(a, b):
    for x, y, kind, why in ALLOW:
        if (a.startswith(x) and b.startswith(y)) or (b.startswith(x) and a.startswith(y)):
            return kind, why
    return None, None


def to_mesh(shape, tol=0.02):
    v, f = shape.tessellate(tol, 0.2)
    m = trimesh.Trimesh(np.array([(p.X, p.Y, p.Z) for p in v]), np.array(f), process=True)
    m.merge_vertices()
    trimesh.repair.fix_normals(m)          # consistent outward winding for the ray test
    return m


def vol(shape):
    try:
        return shape.volume if shape is not None else 0.0
    except Exception:
        return 0.0


def bbox_overlap(a, b, pad=0.05):
    A, B = a.bounding_box(), b.bounding_box()
    return not (A.max.X + pad < B.min.X or B.max.X + pad < A.min.X or A.max.Y + pad < B.min.Y or
                B.max.Y + pad < A.min.Y or A.max.Z + pad < B.min.Z or B.max.Z + pad < A.min.Z)


# ---------------------------------------------------------------- walls / overhang
def _ray_dist(o, d, v0, e1, e2, eps=0.03):
    """Nearest hit distance > eps of ray (o, d) with all triangles (Moller-Trumbore, numpy)."""
    pv = np.cross(d, e2)
    det = (e1 * pv).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.zeros_like(det)
    inv[ok] = 1.0 / det[ok]
    tv = o - v0
    u = (tv * pv).sum(1) * inv
    qv = np.cross(tv, e1)
    v = (qv * d).sum(1) * inv
    t = (e2 * qv).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > eps)
    if not hit.any():
        return None, None
    k = np.where(hit)[0][np.argmin(t[hit])]
    return float(t[k]), int(k)


WEDGE_WALL_DEG = 20.0     # thin ray between faces closer than this to parallel = a thin WALL; else an edge tip


def wall_thickness(mesh, n=1500, seed=1):
    """Sample n surface points; cast a ray inward along -normal; distance to the
    next surface = local wall thickness (sample-based, ESTIMATED by nature).
    Each thin ray (< MIN_WALL) is also classified by the angle between the sampled
    face and the face it hits: (near-)parallel faces = a thin wall; faces meeting at
    a wedge angle >= WEDGE_WALL_DEG = the tip of an acute convex edge (the ray
    leaves through the neighbouring face). Classification is diagnostic only:
    the PASS/WARN/FAIL rule uses all thin rays."""
    pts, fidx = trimesh.sample.sample_surface(mesh, n, seed=seed)
    nrm = mesh.face_normals[fidx]
    tri = mesh.triangles
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    out, thin = [], []
    for p, nv in zip(pts, nrm):
        dd, k = _ray_dist(p, -nv, v0, e1, e2)
        if dd is not None:
            out.append(dd)
            if dd < MIN_WALL:
                wedge = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, float(nv @ mesh.face_normals[k])))))
                thin.append((dd, wedge, [round(float(c), 2) for c in p]))
    a = np.array(out)
    walls = [t for t in thin if t[1] < WEDGE_WALL_DEG]
    edges = [t for t in thin if t[1] >= WEDGE_WALL_DEG]
    return {"samples": int(a.size), "of": int(n), "min_mm": round(float(a.min()), 3),
            "p1_mm": round(float(np.percentile(a, 1)), 3), "p5_mm": round(float(np.percentile(a, 5)), 3),
            "share_below_min_wall": round(float((a < MIN_WALL).mean()), 4),
            "thin_rays_parallel_faces": len(walls), "thin_rays_acute_edges": len(edges),
            "acute_edge_wedge_deg": [round(min(t[1] for t in edges)), round(max(t[1] for t in edges))] if edges else None,
            "thinnest": [[round(t[0], 3), round(t[1]), t[2]] for t in sorted(thin)[:8]]}


def overhang(mesh):
    n = mesh.face_normals
    area = mesh.area_faces
    zmin_tri = mesh.triangles[:, :, 2].min(axis=1)
    zmax_tri = mesh.triangles[:, :, 2].max(axis=1)
    bed = (zmax_tri < 0.01) & (n[:, 2] < -0.99)
    down = (n[:, 2] < -0.01) & ~bed
    steep = (n[:, 2] < -math.sin(math.radians(OVERHANG_DEG))) & ~bed
    flat = (n[:, 2] < -0.99) & ~bed
    tot = area.sum()
    return {"total_area_mm2": round(float(tot), 1), "bed_contact_mm2": round(float(area[bed].sum()), 1),
            "downward_area_mm2": round(float(area[down].sum()), 1),
            "overhang_gt45_mm2": round(float(area[steep].sum()), 1),
            "overhang_gt45_share_of_total": round(float(area[steep].sum() / tot), 4),
            "overhang_gt45_share_of_downward": round(float(area[steep].sum() / max(area[down].sum(), 1e-9)), 4),
            "horizontal_ceilings_mm2 (bridges)": round(float(area[flat].sum()), 1)}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cooling", default=assembly.COOLING_SOURCE)
    ap.add_argument("--samples", type=int, default=1500)
    ap.add_argument("--no-stock-cache", action="store_true", help="use interface boxes instead of Henlor solids")
    args = ap.parse_args()

    RESULTS["_suffix"] = "" if args.cooling == assembly.COOLING_SOURCE else f"_{args.cooling}"
    parts, ci = assembly.build_parts(args.cooling, use_stock_cache=not args.no_stock_cache)
    stock_mode = any(p.name.startswith("stock_") for p in parts)
    RESULTS["stock_reference"] = "Henlor 742370 solids (local cache)" if stock_mode else "interfaces.py boxes"
    check("stock reference geometry", "PASS" if stock_mode else "WARN",
          RESULTS["stock_reference"] + ("" if stock_mode else " - carriage not checked (run structure/stock_cache.py)"))
    by = {p.name: p for p in parts}
    RESULTS["cooling_source"] = {"source": ci.source, "is_stub": ci.is_stub, "status": ci.status}
    check("cooling interface", "WARN" if ci.is_stub else "PASS",
          f"{ci.source} ({'STUB - real ducts not integrated' if ci.is_stub else ci.status})")

    printed = [p for p in parts if p.printed()]
    asm_movers = [p for p in parts if p.category in ("printed", "stub") and p.in_assembly]
    refs = [p for p in parts if p.category == "reference"]   # includes stock_* solids in cache mode

    # ---- 1. per part ---------------------------------------------------------
    for p in printed:
        s = p.shape
        sols = s.solids()
        mat = MATERIALS[p.material]
        po = p.print_oriented()
        m = to_mesh(po)
        bb, pb = s.bounding_box(), po.bounding_box()
        info = {"material": p.material, "category": p.category, "is_valid": bool(s.is_valid), "n_solids": len(sols),
                "watertight": bool(m.is_watertight), "volume_mm3": round(s.volume, 2),
                "mass_g": round(s.volume * mat.density.value / 1000, 2),
                "density": f"{mat.density.value} g/cm3 ({mat.density.status}: {mat.density.source})",
                "bbox_nozzle_frame": [round(v, 2) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)],
                "bbox_print": [round(v, 2) for v in (pb.size.X, pb.size.Y, pb.size.Z)],
                "print_rot_deg": p.print_rot, "mesh_volume_mm3": round(float(m.volume), 2)}
        info["wall"] = wall_thickness(m, args.samples)
        # thinnest-sample locations back to the nozzle frame (the mesh is print-oriented)
        rs = Rot(*p.print_rot) * s
        rb = rs.bounding_box()
        to_nozzle = (Pos(-(rb.min.X + rb.max.X) / 2, -(rb.min.Y + rb.max.Y) / 2, -rb.min.Z) * Rot(*p.print_rot)).inverse()
        for t in info["wall"]["thinnest"]:
            q = (to_nozzle * Pos(*t[2])).position
            t[2] = [round(q.X, 2), round(q.Y, 2), round(q.Z, 2)]
        info["overhang"] = overhang(m)
        info["hardware"] = [{"item": h[0], "qty": h[1], "mass_g_each": round(h[2], 2)} for h in p.hardware]
        RESULTS["parts"][p.name] = info
        ok = s.is_valid and len(sols) == 1 and m.is_watertight
        check(f"{p.name}: solid", "PASS" if ok else "FAIL",
              f"valid={s.is_valid} solids={len(sols)} watertight={m.is_watertight} V={s.volume:.0f} mm3 "
              f"m={info['mass_g']} g ({p.material})")
        w = info["wall"]
        st = "FAIL" if w["share_below_min_wall"] > WALL_FAIL_SHARE else ("WARN" if w["min_mm"] < MIN_WALL else "PASS")
        thin_txt = ""
        if w["thin_rays_parallel_faces"] + w["thin_rays_acute_edges"]:
            thin_txt = (f"; thin rays: {w['thin_rays_parallel_faces']} between parallel faces (thin wall), "
                        f"{w['thin_rays_acute_edges']} at acute convex edges"
                        + (f" (wedge {w['acute_edge_wedge_deg'][0]}..{w['acute_edge_wedge_deg'][1]} deg)" if w["acute_edge_wedge_deg"] else "")
                        + f"; thinnest at {w['thinnest'][0][2]} (nozzle frame)")
        check(f"{p.name}: min wall (sampled, {w['samples']} rays)", st,
              f"min {w['min_mm']} / p1 {w['p1_mm']} mm; {100 * w['share_below_min_wall']:.2f} % < {MIN_WALL} mm" + thin_txt)
        o = info["overhang"]
        check(f"{p.name}: overhang > {OVERHANG_DEG:.0f} deg (print orientation)", "INFO",
              f"{100 * o['overhang_gt45_share_of_total']:.1f} % of surface, {100 * o['overhang_gt45_share_of_downward']:.0f} % "
              f"of downward faces; flat ceilings (bridges) {o['horizontal_ceilings_mm2 (bridges)']} mm2")

    for issue in getattr(by["cooling_module_frame"], "issues", []):
        check("cooling interface mount point", "WARN" if "optional - skipped" in issue else "FAIL", issue)

    # ---- 2. interference ------------------------------------------------------
    cands = asm_movers + refs
    for i, a in enumerate(cands):
        for b in cands[i + 1:]:
            if a.category == "reference" and b.category == "reference":
                continue
            if a.category == "stub" and b.category == "stub" and not (
                    a.name.startswith("stub_duct") or b.name.startswith("stub_duct")):
                continue
            sa, sb, note = a.shape, b.shape, ""
            if "probe_mount" in (a.name, b.name) and (a.name in ANCHOR_FAMILY or b.name in ANCHOR_FAMILY):
                # the probe mount is located by the carriage tabs: check it against the carriage
                # moved so its tab holes coincide with the interfaces.py anchor (HENLOR_SHIFT)
                sh = Pos(*probe_mount.HENLOR_SHIFT)
                if a.name in ANCHOR_FAMILY:
                    sa = sh * sa
                else:
                    sb = sh * sb
                note = " [carriage anchor-shifted by %s]" % (probe_mount.HENLOR_SHIFT,)
            if not bbox_overlap(sa, sb):
                continue
            ov = vol(sa & sb)
            dist = 0.0 if ov > VOL_TOL else sa.distance_to(sb)
            kind, why = allowed(a.name, b.name)
            row = {"a": a.name, "b": b.name, "overlap_mm3": round(ov, 4), "distance_mm": round(dist, 4),
                   "allowed": kind, "reason": why, "note": note}
            if ov > VOL_TOL and (a.name.startswith("stock_") or b.name.startswith("stock_")):
                ib = (sa & sb).bounding_box()
                pen = min(ib.size.X, ib.size.Y, ib.size.Z)
                if pen < PEN_TOL:
                    note += f" [penetration {pen:.3f} mm < {PEN_TOL}: reverse-engineered model tolerance]"
                    row["note"] = note
                    ov_eff = 0.0
                else:
                    ov_eff = ov
            else:
                ov_eff = ov
            if ov_eff > VOL_TOL:
                st = "PASS" if kind == "overlap" else "FAIL"
            elif dist < CONTACT_TOL:
                st = "PASS" if kind else "WARN"
            else:
                continue
            row["status"] = st
            RESULTS["interference"].append(row)
            check(f"interference {a.name} x {b.name}", st,
                  f"overlap {ov:.3f} mm3, gap {dist:.3f} mm" + (f" - allowed: {why}" if kind else "") + note)
    if not any(r["status"] == "FAIL" for r in RESULTS["interference"]):
        check("interference: no unintended overlaps", "PASS", f"{len(cands)} solids checked pairwise")

    # ---- 3. clearances -------------------------------------------------------
    C = RESULTS["clearance"]
    hz = float(I.HOT_ZONE_CLEARANCE)
    hot = [ibox(I.SOCK), ibox(I.HEATER_BODY)]
    for p in asm_movers:
        d = min(p.shape.distance_to(h) for h in hot)
        C.setdefault("hot_zone_mm", {})[p.name] = round(d, 2)
        check(f"hot zone {p.name}", "PASS" if d >= hz else "FAIL", f"{d:.2f} mm to sock/heater (>= {hz})")

    allow_regions = frame.lidar_allow_regions()
    zones = [(n, ibox(getattr(I, n))) for n in ("LIDAR_RESERVED_OPTICAL", "LIDAR_RESERVED_BODY")]
    zones.append(("LIDAR_LASER_SHEET", by["keepout_lidar_laser_sheet"].shape))
    for p in asm_movers:
        for zn, z in zones:
            inter = p.shape & z
            v = vol(inter)
            v_allowed = 0.0
            if v > VOL_TOL and p.name == "cooling_module_frame":
                for reg, why in allow_regions:
                    v_allowed += vol(inter & reg)
            resid = v - v_allowed
            dist = 0.0 if v > VOL_TOL else p.shape.distance_to(z)
            C.setdefault("lidar", {})[f"{p.name} x {zn}"] = {"intrusion_mm3": round(v, 3),
                                                             "allow_listed_mm3": round(v_allowed, 3),
                                                             "gap_mm": round(dist, 2)}
            if resid > VOL_TOL:
                check(f"LiDAR {zn} vs {p.name}", "FAIL", f"intrudes {resid:.2f} mm3")
            elif v > VOL_TOL:
                check(f"LiDAR {zn} vs {p.name}", "WARN",
                      f"{v:.1f} mm3 inside, all allow-listed: {'; '.join(w for _, w in allow_regions)} "
                      f"(interface conflict, see report)")
            else:
                check(f"LiDAR {zn} vs {p.name}", "PASS", f"clear by {dist:.2f} mm")
    # stock parts that the reserved boxes overlap (interfaces.py consistency)
    for zn, z in zones[:2]:
        box = getattr(I, zn)
        for r in refs:
            inter = r.shape & z
            v = vol(inter)
            if v <= VOL_TOL:
                continue
            ib = inter.bounding_box()
            depth = box.xmax - ib.min.X                 # penetration from the box's inner (+X) face
            C.setdefault("lidar_box_overlaps_stock", {}).setdefault(zn, {})[r.name] = {
                "overlap_mm3": round(v, 2), "x_range": [round(ib.min.X, 2), round(ib.max.X, 2)],
                "depth_from_inner_face_mm": round(depth, 2)}
            exp = [e for e in KEEPOUT_STOCK_EXPECTED if e[0] == zn and r.name.startswith(e[1])]
            if exp and depth <= exp[0][2] + PEN_TOL:
                check(f"interfaces: {zn} overlaps {r.name}", "INFO",
                      f"{v:.0f} mm3, X {ib.min.X:.2f}..{ib.max.X:.2f} ({depth:.2f} mm from the box face, "
                      f"<= {exp[0][2]:.2f}) - {exp[0][3]}")
            else:
                check(f"interfaces: {zn} overlaps {r.name}", "WARN",
                      f"{v:.0f} mm3, X {ib.min.X:.2f}..{ib.max.X:.2f} ({depth:.2f} mm deep) - unexpected, check the box (M6)")

    # real duct air path: nothing else may enter it (the duct owns it)
    if ci.duct_air is not None:
        for p in asm_movers:
            if p.name.startswith("duct_"):
                continue
            v = vol(p.shape & ci.duct_air)
            dist = 0.0 if v > VOL_TOL else p.shape.distance_to(ci.duct_air)
            C.setdefault("duct_air_path", {})[p.name] = {"overlap_mm3": round(v, 3), "gap_mm": round(dist, 2)}
            check(f"duct air path vs {p.name}", "FAIL" if v > VOL_TOL else "PASS",
                  f"overlap {v:.3f} mm3, gap {dist:.2f} mm to the S7 internal air volume")

    # the cover yields to the duct and to the frame's duct lugs (only the shelf contact is intended)
    cv = by["cover"]
    cyc = cover.YIELD_CLEAR
    below_shelf = cv.shape & bx(-300, 300, -300, 300, -100, frame.ZMAX - 0.01)
    for other in [d.name for d in ci.duct_parts if d.category == "printed"] + ["cooling_module_frame"]:
        dist = below_shelf.distance_to(by[other].shape)
        C.setdefault("cover_clearance_mm", {})[other] = round(dist, 3)
        check(f"cover clearance to {other} (below the shelf contact plane)", "PASS" if dist >= cyc - 1e-6 else "FAIL",
              f"{dist:.2f} mm (>= COVER_YIELD_CLEAR {cyc}); cover side-wall bottoms Z "
              f"{ {('left' if k < 0 else 'right'): round(v, 2) for k, v in getattr(cv, 'wall_bottoms', {}).items()} }")

    # part-fan intake through the cover: measured on the cover solid, not taken from cover.py's own numbers
    for ap in getattr(cv, "intake_apertures", []):
        cx, cz = ap["centre_xz"]
        y0, y1 = ap["y_front_wall"]
        a_in = math.pi / 4 * ap["d_inlet"] ** 2
        a_ap = math.pi / 4 * ap["d_aperture"] ** 2
        blk_in = vol(cv.shape & cyl_y(cx, cz, y0 - 0.5, y1 + 0.5, ap["d_inlet"])) / cover.WALL
        blk_ap = vol(cv.shape & cyl_y(cx, cz, y0 - 0.5, y1 + 0.5, ap["d_aperture"])) / cover.WALL
        open_in, open_ap = a_in - blk_in, a_ap - blk_ap
        C.setdefault("cover_fan_intake", []).append({**ap, "inlet_disc_mm2": round(a_in, 1), "open_over_inlet_mm2": round(open_in, 1),
                                                     "open_over_inlet_pct": round(100 * open_in / a_in, 2),
                                                     "aperture_open_mm2": round(open_ap, 1)})
        ok = open_in >= 0.999 * a_in and ap["d_aperture"] >= ap["d_inlet"] + 2 - 1e-9
        check(f"cover: 4020 intake aperture at X {cx:.1f}, Z {cz:.1f}", "PASS" if ok else "FAIL",
              f"Ø{ap['d_aperture']:.1f} fully open ({ap['ribs']} ribs), {open_ap:.0f} mm2; over the Ø{ap['d_inlet']:.1f} inlet "
              f"disc (FAN_INLET_D, ESTIMATED M7) {open_in:.0f} of {a_in:.0f} mm2 open = {100 * open_in / a_in:.1f} % "
              f"(want 100 %, aperture >= inlet + 2 mm); front wall {cover.GAP} mm in front of the intake face")
    va = getattr(cv, "vent_area", {})
    if va:
        C["cover_vent_area_mm2"] = va
        check("cover: 3010 plenum vents (side + top slots; bottom and rear also open)", "INFO",
              f"side {va.get('plenum_side_vents_mm2')} mm2 + top {va.get('plenum_top_slots_mm2')} mm2; "
              f"the 3010 itself draws through the frame window (checked above)")

    # the frame really provides the fan screw bosses and the duct-tab lugs at the interface points
    fr_s = by["cooling_module_frame"].shape
    ins = common.INSERTS["M3"]
    mounts = [(f"fan {f['id']} screw", b) for f in ci.fans for b in f["screw_bosses"]] + \
             [(f"duct tab {m.get('id') or ''}", m) for m in ci.duct_mounts]
    for tag, m in mounts:
        x, y, z = m["pos"]
        depth = ins.length
        hole = cyl_y(x, z, y + 0.05, y + depth, ins.hole_d - 0.1)
        ring = cyl_y(x, z, y + 0.05, y + depth, ins.boss_d - 0.4) - cyl_y(x, z, y, y + depth + 1, ins.hole_d + 0.2)
        face = cyl_y(x, z, y + 0.02, y + 0.3, ins.boss_d - 0.4) - cyl_y(x, z, y, y + 1, ins.hole_d + 0.2)
        v_hole, v_ring, v_face = vol(fr_s & hole), vol(fr_s & ring), vol(fr_s & face)
        f_ring, f_face = v_ring / max(vol(ring), 1e-9), v_face / max(vol(face), 1e-9)
        ok = v_hole <= VOL_TOL and f_ring > 0.95 and f_face > 0.95
        C.setdefault("frame_mount_points", {})[tag] = {"pos": [round(v, 2) for v in m["pos"]], "hole_free_mm3": round(v_hole, 3),
                                                      "boss_fill": round(f_ring, 3), "mating_face_fill": round(f_face, 3)}
        check(f"frame provides {tag} at ({x:.2f}, {y:.2f}, {z:.2f})", "PASS" if ok else "FAIL",
              f"Ø{ins.hole_d} insert hole open ({v_hole:.3f} mm3 material), boss Ø{ins.boss_d} {100 * f_ring:.0f} % solid, "
              f"mating face at Y {y:.2f} {100 * f_face:.0f} % solid; screw along {m['axis']}")

    zmin_lim = float(I.DUCT_MIN_Z)
    for p in asm_movers:
        zm = p.shape.bounding_box().min.Z
        check(f"DUCT_MIN_Z {p.name}", "PASS" if zm >= zmin_lim - 1e-6 else "FAIL", f"lowest Z {zm:.2f} (>= {zmin_lim})")
    check("DUCT_MIN_Z probe pin (exempt: stock purchased part, today's state)", "INFO",
          f"stowed tip Z {float(I.PROBE_STOWED_TIP_Z):.2f} < DUCT_MIN_Z {zmin_lim} - unchanged by this design")

    ry = float(I.REAR_LIMIT_Y)
    rear_box = bx(-200, 200, ry, 300, -50, 30)
    for p in asm_movers + [by["ref_microprobe_body"]]:
        v = vol(p.shape & rear_box)
        ymax = p.shape.bounding_box().max.Y
        st = "PASS" if v <= VOL_TOL else "FAIL"
        check(f"rear limit {p.name}", st, f"max Y {ymax:.2f}; volume behind Y {ry} below Z 30: {v:.3f} mm3")
    pm_y = by["probe_mount"].shape.bounding_box().max.Y
    check("probe_mount rear vs today's 785004 rear (keep-out zones unchanged)",
          "PASS" if pm_y <= I.PROBE_ADAPTER_785004.ymax + 1e-6 else "WARN",
          f"{pm_y:.2f} vs {I.PROBE_ADAPTER_785004.ymax}")

    zone = ibox(I.PCB_COMPONENT_ZONE)
    boss_cols = None
    for x, z in list(I.MODULE_MOUNT_HOLES) + [frame.fourth_corner()]:
        c = cyl_y(x, z, -40, -20, max(frame.BOSS_D, frame.F_PAD4_D) + 0.02)
        boss_cols = c if boss_cols is None else boss_cols + c
    for p in asm_movers:
        v = vol(p.shape & zone)
        v_ok = vol(p.shape & zone & boss_cols) if p.name == "cooling_module_frame" else 0.0
        st = "PASS" if v - v_ok <= VOL_TOL else "FAIL"
        if v > VOL_TOL or st == "FAIL":
            check(f"PCB component zone {p.name}", st, f"{v:.1f} mm3 inside, {v_ok:.1f} mm3 are the boss pads (allowed)")
    area = frame.intake_area()
    C["frame_3010_intake_area_mm2"] = round(area, 1)
    check("3010 intake through the frame", "PASS" if area >= 625 else "FAIL",
          f"{area:.0f} mm2 open (>= 625 = 25x25); PCB fan cutout itself ~559 mm2 (K1C gerber)")

    # X ends: carriage stalls against the right XY joint inside XY_JOINT_BAND_Z (hard right, soft left)
    zb0, zb1 = I.XY_JOINT_BAND_Z
    rl, ll = float(I.RIGHT_LIMIT_X), float(I.LEFT_LIMIT_X)
    for p in asm_movers:
        vr = vol(p.shape & bx(rl, rl + 200, -300, 300, zb0, zb1))
        vl = vol(p.shape & bx(ll - 200, ll, -300, 300, zb0, zb1))
        band = p.shape & bx(-300, 300, -300, 300, zb0, zb1)
        ext = band.bounding_box() if band is not None and vol(band) > 0 else None
        txt = f"X {ext.min.X:.1f}..{ext.max.X:.1f} in Z {zb0}..{zb1}" if ext else "not in the band"
        check(f"XY-joint band right {p.name}", "FAIL" if vr > VOL_TOL else "PASS", f"{txt} (RIGHT_LIMIT_X {rl}, hard)")
        if vl > VOL_TOL:
            check(f"XY-joint band left {p.name}", "WARN", f"{txt} beyond LEFT_LIMIT_X {ll} (ESTIMATED)")

    # PCB screws M3x30 vs the stock carriage / heatsink (tips must not bottom out)
    if stock_mode:
        L = frame.SCREW_LEN
        for x, z in I.MODULE_MOUNT_HOLES:
            tip_y = frame.FRONT_Y + L
            core = cyl_y(x, z, tip_y - 3.0, tip_y, 2.5)
            hits = {n: round(vol(core & by[n].shape), 3) for n in ("stock_carriage", "stock_heatsink") if n in by}
            st = "PASS" if all(v <= VOL_TOL for v in hits.values()) else "WARN"
            check(f"M3x{L:.0f} PCB screw at ({x}, {z}): last 3 mm vs stock solids", st,
                  f"tip at Y {tip_y:.1f}; material in the way {hits} (0 = runs in a modelled hole/air)")

    # PCB screws must stay installable from the front once the frame is printed
    fr = by["cooling_module_frame"].shape
    for x, z in I.MODULE_MOUNT_HOLES:
        path = cyl_y(x, z, frame.FRONT_Y - 0.05, frame.FRONT_Y - 25.0, frame.HEAD_CLEAR_D)
        v = vol(fr & path)
        check(f"PCB screw ({x}, {z}) driver access through the frame", "PASS" if v <= VOL_TOL else "FAIL",
              f"{v:.3f} mm3 of frame in the Ø{frame.HEAD_CLEAR_D:.1f} access path (the fan comes off first)")

    # probe anchor cross-check: interfaces' 785004 placement vs Henlor's carriage tabs
    sh = probe_mount.HENLOR_SHIFT
    check("probe anchor: interfaces.py vs Henlor carriage", "WARN" if max(abs(v) for v in sh) > 0.5 else "PASS",
          f"Henlor tab holes Y {probe_mount.HENLOR_TAB_HOLE_Y}, tab top Z {probe_mount.HENLOR_TAB_TOP_Z} vs anchor "
          f"Y {probe_mount.ANCHOR_Y:.2f}, Z {probe_mount.Z_ANCHOR:.2f} -> shift {sh}. The mount copies 785004's "
          f"anchor-to-probe relation, so the real pin position is unchanged; only the nozzle-frame placement (pin "
          f"offset 1.0 vs 2.75, flange Z) is uncertain - M8")
    C["probe_anchor_shift_mm"] = sh

    allp = asm_movers + [by["ref_microprobe_body"]] + [p for p in parts if p.name.startswith("ref_blower_")]
    xs = [(p.shape.bounding_box(), p.name) for p in allp]
    ymin = min(xs, key=lambda t: t[0].min.Y)
    xmax = max(xs, key=lambda t: t[0].max.X)
    xmin = min(xs, key=lambda t: t[0].min.X)
    C["extents"] = {"front_min_y": [round(ymin[0].min.Y, 2), ymin[1]], "right_max_x": [round(xmax[0].max.X, 2), xmax[1]],
                    "left_min_x": [round(xmin[0].min.X, 2), xmin[1]]}
    fan_front = min((p.shape.bounding_box().min.Y for p in parts if p.name.startswith("ref_blower_")), default=None)
    exc = float(I.FRONT_LIMIT_Y) - ymin[0].min.Y
    C["extents"]["front_excess_mm"] = round(max(exc, 0.0), 2)
    check("soft: front extent vs FRONT_LIMIT_Y (DERIVED safe bound)", "PASS" if exc <= 0 else "WARN",
          f"{ymin[0].min.Y:.1f} ({ymin[1]}) vs {float(I.FRONT_LIMIT_Y)}: {max(exc, 0):.1f} mm past"
          + (f"; fan front face {fan_front:.1f} ({float(I.FRONT_LIMIT_Y) - fan_front:+.1f} by itself), cover = fan front "
             f"- COVER_GAP {cover.GAP} - COVER_WALL {cover.WALL}. Soft limit (M9: front clearance at Y -2 unmeasured)"
             if fan_front is not None and ymin[1] == "cover" else ""))
    check("right extent (all Z; the hard limit is the XY-joint band check)", "INFO",
          f"{xmax[0].max.X:.1f} ({xmax[1]}) vs RIGHT_LIMIT_X {float(I.RIGHT_LIMIT_X)}")
    check("soft: left extent of new parts", "INFO", f"{xmin[0].min.X:.1f} ({xmin[1]}); LiDAR side is limited by its own module")

    # ---- 4. mass budget --------------------------------------------------------
    M = RESULTS["mass"]
    added = {}
    for p in parts:
        if p.category in ("printed",) and p.in_assembly or p.name.startswith("stub_duct"):
            mat = MATERIALS[p.material]
            added[p.name] = round(p.shape.volume * mat.density.value / 1000, 2)
    hw = sum(q * mg for p in parts for _, q, mg in p.hardware)
    added["hardware (screws, inserts)"] = round(hw, 2)
    n_fans = len(ci.fans)
    fan_mass = float(I.BLOWER_4020_STOCK.mass_g)
    added_fans = (n_fans - 1) * fan_mass          # the stock 4020 is reused; extra fans are added mass
    if added_fans:
        added["extra part fan(s)"] = added_fans
    removed = {"stock cover (+duct, without fan; 23.8 g measured K1, 32-32.5 K1 Max reports)": (23.8, 32.5),
               "785004 probe adapter (8.55 cm3, PLA/PETG 1.24-1.27, ESTIMATED)": (8.55 * 1.24, 8.55 * 1.27),
               "stock PCB screws x3 (M3x18/18/20, replaced by M3x30)": (3 * common.screw_mass_g(3, 20),) * 2}
    a_sum = sum(added.values())
    r_lo = sum(v[0] for v in removed.values())
    r_hi = sum(v[1] for v in removed.values())
    dm = (a_sum - r_hi, a_sum - r_lo)
    M.update({"added_g": added, "added_total_g": round(a_sum, 1), "removed_g": {k: [round(x, 1) for x in v]
                                                                             for k, v in removed.items()},
              "delta_g_range": [round(dm[0], 1), round(dm[1], 1)],
              "basis": "solid-volume mass (100 % infill = upper bound) of every printed assembly part "
                       + ("(stub duct mass is a placeholder)" if ci.is_stub else "incl. the real duct body")
                       + "; hardware = screws + inserts incl. fan and duct-tab screws; stock 4020 reused "
                         "(BLOWER_4020_STOCK.mass_g ESTIMATED, moves, no change); removed = stock cover+duct, "
                         "785004 adapter, stock PCB screws"})
    shaper = {}
    for ax, f0, ms in (("X", 77.6, (400, 450, 500)), ("Y", 52.0, (820, 880, 960))):
        shaper[ax] = {f"m={m0} g": [round(f0 * math.sqrt(m0 / (m0 + d)), 2) for d in dm] for m0 in ms}
    M["shaper_Hz_for_delta_range"] = shaper
    check("moving mass vs stock", "INFO",
          f"added {a_sum:.1f} g, removed {r_lo:.1f}..{r_hi:.1f} g -> delta {dm[0]:+.1f}..{dm[1]:+.1f} g; "
          f"X shaper {shaper['X']['m=450 g'][1]:.1f}..{shaper['X']['m=450 g'][0]:.1f} Hz (77.6 now), "
          f"Y {shaper['Y']['m=880 g'][1]:.1f}..{shaper['Y']['m=880 g'][0]:.1f} Hz (52.0 now)")

    # ---- 5. stiffness ----------------------------------------------------------
    def com(shape):
        c = shape.center()
        return (c.X, c.Y, c.Z)
    blower = next(p for p in parts if p.name.startswith("ref_blower_"))
    carried = [{"name": blower.name, "mass_g": blower.mass_override_g, "com": com(blower.shape),
                "inertia_extra_gmm2": blower.mass_override_g * (40 ** 2 + 20 ** 2) / 12}]
    for n in ("cover", "cooling_module_frame") + tuple(p.name for p in ci.duct_parts):
        p = by[n]
        carried.append({"name": n, "mass_g": p.shape.volume * MATERIALS[p.material].density.value / 1000,
                        "com": com(p.shape)})
    fan_screws = [(b["pos"][0], b["pos"][2]) for f in ci.fans for b in f["screw_bosses"]]
    RESULTS["stiffness"]["frame"] = stiffness.frame_estimates(carried, fan_screws)
    RESULTS["stiffness"]["probe_mount"] = stiffness.probe_estimates(added["probe_mount"])
    fr = RESULTS["stiffness"]["frame"]
    for k, v in fr.items():
        if isinstance(v, dict) and "first_mode_Hz" in v:
            check(f"frame mode estimate: {k}", "PASS" if v["first_mode_Hz"] > 2 * 77.6 else "WARN",
                  f"{v['first_mode_Hz']} Hz (want > 2 x 77.6 Hz)")

    # ---- 6. dependencies / release ---------------------------------------------
    RESULTS["unconfirmed_global"] = [list(r) for r in I.all_unconfirmed()]
    for p in printed + [d for d in ci.duct_parts if d.category == "stub"]:
        rows, seen = [], set()
        for n in p.deps:
            if n in seen:
                continue
            seen.add(n)
            st, val, src = common.resolve_dep(n)
            rows.append((n, st, str(val)[:60], src))
        unconf = [r for r in rows if r[1] in ("ESTIMATED", "MISSING", "STUB", "UNKNOWN")]
        rel = common.release_status(rows, "fitcheck" if p.category == "fitcheck" else "")
        if p.category == "stub":
            rel = "STUB (not a deliverable)"
        RESULTS["release"][p.name] = {"status": rel, "unconfirmed": [list(r) for r in unconf],
                                      "n_deps": len(rows)}
        check(f"release {p.name}", "INFO", f"{rel}; {len(unconf)} unconfirmed of {len(rows)} dependencies")
    unknown = [(p, r) for p, v in RESULTS["release"].items() for r in v["unconfirmed"] if r[1] == "UNKNOWN"]
    if unknown:
        check("dependency names resolve", "FAIL", str(unknown))

    write_reports()
    n_fail = sum(c["status"] == "FAIL" for c in RESULTS["checks"])
    n_warn = sum(c["status"] == "WARN" for c in RESULTS["checks"])
    print(f"\n{n_fail} FAIL, {n_warn} WARN -> {EXPORTS / ('validation_report' + RESULTS['_suffix'] + '.md')}")
    return 1 if n_fail else 0


def write_reports():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    sfx = RESULTS.get("_suffix", "")
    (EXPORTS / f"validation_report{sfx}.json").write_text(json.dumps(RESULTS, indent=1, default=str))
    L = ["# Validation report - K1 Max toolhead structure", "",
         f"Cooling module: `{RESULTS['cooling_source']['source']}` "
         f"({'STUB' if RESULTS['cooling_source']['is_stub'] else 'real ducts'}). Generated by `cad/source/validate.py`.", "",
         "## Summary of checks", "", "| Status | Check | Detail |", "|---|---|---|"]
    order = {"FAIL": 0, "WARN": 1, "PASS": 2, "INFO": 3}
    for c in sorted(RESULTS["checks"], key=lambda c: order[c["status"]]):
        L.append(f"| {c['status']} | {c['check']} | {c['detail'].replace('|', '/')} |")
    L += ["", "## Printed parts", "", "| Part | Material | Mass g (solid) | Volume mm3 | Print bbox mm | Min wall / p1 mm "
          "| Overhang >45 deg share | Release |", "|---|---|---|---|---|---|---|---|"]
    for n, d in RESULTS["parts"].items():
        rel = RESULTS["release"].get(n, {}).get("status", "")
        L.append(f"| {n} | {d['material']} | {d['mass_g']} | {d['volume_mm3']} | {' x '.join(str(round(v, 1)) for v in d['bbox_print'])} "
                 f"| {d['wall']['min_mm']} / {d['wall']['p1_mm']} | {100 * d['overhang']['overhang_gt45_share_of_total']:.1f} % | {rel} |")
    L += ["", "Densities: ASA 1.07, PC 1.20, PA-CF 1.15 g/cm3 (lead-specified, typical TDS values: ESTIMATED). "
          "Masses are solid-volume (100 % infill) upper bounds.", "",
          "## Moving mass and input shaper", "", "```", json.dumps(RESULTS["mass"], indent=1), "```", "",
          "## Stiffness estimates (hand calculations, ESTIMATED)", "", "```", json.dumps(RESULTS["stiffness"], indent=1),
          "```", "", "## Release status and unconfirmed dependencies", ""]
    for n, d in RESULTS["release"].items():
        L += [f"### {n}: **{d['status']}**", "", "| Name | Status | Value | Source |", "|---|---|---|---|"]
        for r in d["unconfirmed"]:
            L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
        L.append("")
    L += ["## All ESTIMATED/MISSING values in interfaces.py", "", "| Name | Status | Source |", "|---|---|---|"]
    for r in RESULTS["unconfirmed_global"]:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} |")
    L += ["", "## Clearances (raw)", "", "```", json.dumps(RESULTS["clearance"], indent=1), "```"]
    (EXPORTS / f"validation_report{sfx}.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
