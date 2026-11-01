"""Parametric part-cooling duct generator for the K1 Max toolhead (build123d), mm, nozzle frame.

    from ducts import build_ducts, PARAM_SETS, PARAMS_FINAL
    parts = build_ducts(PARAMS_FINAL)       # dict name -> build123d Part/Solid

Returned parts:
    air            internal air path (all fans), CFD and checks
    body           printed duct body (shell, wall >= 1.2 mm) incl. fan sockets and mount tabs
    body_cfd       the shell the CFD sees (no sockets/tabs) + fan stubs, one solid
    fan_<id>       envelope box of each fan (clearance checks, assembly)
    stub_<id>      the CFD fan-outlet stub block of each fan
  and build_info(params, parts) gives inlet/outlet/port geometry, checks, mass and the interface.

Design concept (see documentation/cfd-report.md): the duct is a *nozzle end* (manifold around the
sock + wedge ports) and a *feed transition* from the fan outlet (DD-01). Ports are wedges: vertical
outlet face, ceiling rising outward at >= 45 deg (printable upright without support), floor at a
shallow angle; the jet leaves between the two. All internal ceilings are >= 45 deg so the part prints
upright (fan socket up) with no support in the air path; build_info() checks this face by face.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
from build123d import Axis, Solid, Wire

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))           # cad/source -> interfaces
sys.path.insert(0, str(HERE))
import interfaces as I                          # noqa: E402
from geom import (Chain, RoundedRectPath, Section, bend_sections, box_solid, fuse_all,  # noqa: E402
                  inscribed_diameter, offset_convex, poly_area, poly_gable, poly_rect,
                  ray_exit_box, sec, unit)

T_WALL = 1.2
DUCT_MIN_Z = float(I.DUCT_MIN_Z)
HZC = float(I.HOT_ZONE_CLEARANCE)
S = I.SOCK
# sock + hot-zone clearance: nothing printed inside this box (it spans Z 1.9..33.3 so, together
# with DUCT_MIN_Z, the whole sock footprint is excluded)
CB = (S.xmin - HZC, S.xmax + HZC, S.ymin - HZC, S.ymax + HZC, S.zmin - HZC, S.zmax + HZC)
# MicroProbe body keep-out: flange footprint (21.93 x 15.6) around (0, +20.3), down to Z 1.
# ESTIMATED (body shape MISSING, DD-03); owned by Structure, used here only to stay clear.
PROBE_KEEPOUT = (-11.0, 11.0, float(I.PROBE_BODY_Y[0]), float(I.PROBE_BODY_Y[1]), 1.0, 32.0)
# 3010 intake: a 25 x 25 window in front of the 3010 must stay open (lead's requirement)
INTAKE_WINDOW_MIN = 25.0

DENSITY = {"ASA": 1.07, "PC": 1.20}
FAN_MASS_G = {"4020": float(I.BLOWER_4020_STOCK.mass_g), "5015": float(I.BLOWER_5015_SUNON.mass_g)}
FAN_SPEC = {"4020": I.BLOWER_4020_STOCK, "5015": I.BLOWER_5015_SUNON}
PQ_DIR = HERE.parents[2] / "components/fans/pq-curves"

X, Y, Z = np.eye(3)


# ============================================================================ fans
FAN_SPEC["delta"] = I.BLOWER_5015_DELTA
# Same Sky CBM-5015BF-175-459-22 (12 V, 4-wire PWM): not in interfaces.py yet (request filed in the CFD
# report). Frame 51.2 x 51.6 x 15 VERIFIED (datasheet); outlet assumed Delta-like ESTIMATED; mass = series
# maximum 31.4 g (series range 23.2-31.4, not given per model).
FAN_SPEC["samesky"] = I.BlowerSpec("Same Sky CBM-5015BF-175-459-22 (12 V 4-wire PWM)", (51.2, 51.6, 15.0),
                                   (12.2, 17.6), I.Dim(31.4, "ESTIMATED", "series max, research/03 s10"),
                                   "samesky_CBM-5015BF-175-459-22_digitized.csv",
                                   notes="12 V: needs a 24->12 V buck on the toolhead (research/03 s10)")
FAN_MASS_G["samesky"] = 31.4


def _outlet_dims(ftype):
    """(along fan thickness, along the outlet edge) of the outlet opening, mm."""
    if ftype in ("delta", "samesky"):
        return 12.2, 17.6      # VERIFIED inside 17.6 x 12.2 (17.6 along the edge, 12.2 across the 15 mm frame)
    if ftype == "5015":
        return I.BLOWER_5015_SUNON.outlet          # (12.5 along t, 19.5 along w) ESTIMATED
    return I.BLOWER_4020_STOCK.outlet               # (17, 13) ESTIMATED


FRAME_FRONT_Y = float(I.PCB_COMPONENT_ZONE.ymin) - 2.0      # structure/frame.py plate front face (-33.5)
FAN_BACK_Y = FRAME_FRONT_Y - 3.0                             # structure stub: 3 mm plenum for the 3010 intake
STOCK_FAN_SCREWS_XZ = [(-18.65, 60.3), (16.05, 25.6)]       # stock 4020 diagonal pair (02:C7); the third
#   stock screw (16.05, 60.3) is not used: 4.5 mm from the PCB screw (12, 58.3) < 6.75 required by the frame


def fan_front(ftype="4020", x_right=None, y_back=FAN_BACK_Y, zf=None):
    """Blower in the front bay, stock-like: face in the XZ plane, intake facing -Y, outlet on the bottom
    edge blowing -Z at its RIGHT end (stock handedness, 02:C8).
    4020: X/Z = the stock pose centre (STOCK_4020_POS), rear face 3 mm in front of the frame plate
    (structure/cooling.py stub), i.e. Y -56.5..-36.5; screws = stock diagonal pair.
    5015 (Sunon / Delta): 51 mm wide, so it must stay inside X -31..24.2 in the XY-joint band and out of
    LIDAR_RESERVED_BODY (X <= -24 for Y >= -36): X -27..24 at the same rear-face Y (-36.5)."""
    sp = FAN_SPEC[ftype]
    w, h, t = sp.frame
    oa, ob = _outlet_dims(ftype)
    SP = I.STOCK_4020_POS
    if ftype == "4020":
        cx, cz = (SP.xmin + SP.xmax) / 2, (SP.zmin + SP.zmax) / 2
        x0, z0 = cx - w / 2, cz - h / 2
    else:
        x0 = (24.0 if x_right is None else x_right) - w
        z0 = SP.zmin + 0.49 if zf is None else zf
    if zf is not None:
        z0 = zf
    box = (x0, x0 + w, y_back - t, y_back, z0, z0 + h)
    oc = np.array([x0 + w - ob / 2, y_back - t + 1.5 + oa / 2 if ftype == "4020" else y_back - t / 2, z0])
    if ftype == "4020":
        holes = STOCK_FAN_SCREWS_XZ
        st = "stock 4020 diagonal screw pair (02:C7, Henlor), same as structure/cooling.py stub"
    else:
        e = 4.5
        holes = [(x0 + e, z0 + h - e), (x0 + w - e, z0 + e)]
        st = "ESTIMATED generic 5015 diagonal holes (Delta drawing not checked)"
    return {"type": ftype, "box": box, "outlet_c": oc.tolist(), "outlet_u": [-1, 0, 0], "outlet_v": [0, 1, 0],
            "outlet_a": ob, "outlet_b": oa, "blow": [0, 0, -1], "intake": [0, -1, 0],
            "holes": [{"xyz": [xx, y_back - t / 2, zz], "axis": [0, 1, 0], "d": sp.hole_d, "through_length": t,
                       "status": st} for xx, zz in holes],
            "spec": sp.name, "mass_g": float(sp.mass_g)}


def fan_right_low(ftype="4020", x0=31.5, y_front=-16.0, zb=4.3):
    """Second blower for D: right side BELOW the XY-joint band (Z < 44.3, where X is not limited),
    face in the YZ plane, intake facing +X, outlet on the FRONT edge (blowing -Y) at its bottom end."""
    sp = FAN_SPEC[ftype]
    w, h, t = sp.frame
    oa, ob = _outlet_dims(ftype)
    box = (x0, x0 + t, y_front, y_front + w, zb, zb + h)
    oc = np.array([x0 + t / 2, y_front, zb + ob / 2])
    e = 3.5
    holes = [(y_front + e, zb + h - e), (y_front + w - e, zb + e)]
    return {"type": ftype, "box": box, "outlet_c": oc.tolist(), "outlet_u": [1, 0, 0], "outlet_v": [0, 0, 1],
            "outlet_a": oa, "outlet_b": ob, "blow": [0, -1, 0], "intake": [1, 0, 0],
            "holes": [{"xyz": [x0 + t / 2, yy, zz], "axis": [1, 0, 0], "d": sp.hole_d, "through_length": t,
                       "status": "ESTIMATED"} for yy, zz in holes],
            "spec": sp.name, "mass_g": float(sp.mass_g)}


# ============================================================================ parameter sets
PORT_DEFAULT = {"w": 6.0, "h": 3.0, "z_ob": None, "alpha_f": 5.0, "alpha_c": 45.0,
                "w_back": None, "yaw": 0.0, "margin": 1.15, "overlap": 0.8, "root": 3.0}
MANIFOLD_DEFAULT = {"d": 6.0, "W": 9.0, "z0": 4.5, "H_in": None, "H_margin": 0.4, "H_min": 5.0}
# front plenum: from under the front fan's outlet straight back (+Y) into the manifold front
PLENUM_DEFAULT = {"y": [-55.0, -21.5], "x": [12.2, 12.0], "w": 13.0, "hs": 6.0, "z0": 4.5, "drop_z": 10.5}


def _p(**kw):
    p = copy.deepcopy(PORT_DEFAULT)
    p.update(kw)
    return p


def _plenum(**kw):
    d = copy.deepcopy(PLENUM_DEFAULT)
    d.update(kw)
    return d


def params_S1():
    return {
        "name": "S1", "label": "S: 1x4020 front bay (stock-like pose), front plenum + horseshoe manifold, 5 wedge ports",
        "t": T_WALL,
        "fans": {"F": fan_front("4020")},
        "manifolds": [{"id": "M", "fan": "F", "az0": 231.5, "az1": 52.0, **MANIFOLD_DEFAULT,
                       "feed": {"kind": "front_plenum", "plenum": _plenum()}}],
        "ports": [_p(az=a, manifold="M") for a in (240, 275, 320, 0, 35)],
    }


def params_REF():
    return {
        "name": "REF", "label": "REF: single-jet CONCEPT, 1x4020 front bay, single front slot (secondary reference)",
        "t": T_WALL,
        "fans": {"F": fan_front("4020")},
        "manifolds": [],
        "ports": [_p(az=270, w=16.0, h=3.5, w_back=18.0, L=7.0)],
        "direct_feeds": [{"fan": "F", "port": 0, "plenum": _plenum(x=[12.2, 0.0], w=13.0)}],
    }


def params_D1():
    return {
        "name": "D1", "label": "D: 2x4020 (front bay + low right side), independent manifolds, 5 ports",
        "t": T_WALL,
        "fans": {"F": fan_front("4020"), "R": fan_right_low("4020")},
        "manifolds": [
            {"id": "MF", "fan": "F", "az0": 231.5, "az1": 292.0, **MANIFOLD_DEFAULT,
             "feed": {"kind": "front_plenum", "plenum": _plenum(x=[12.2, 1.0])}},
            {"id": "MR", "fan": "R", "az0": 300.0, "az1": 52.0, **MANIFOLD_DEFAULT,
             "feed": {"kind": "right_low", "end": [22.0, -21.5], "bend_r": 9.0, "w": 12.0, "hs": 7.0}}],
        "ports": [_p(az=240, w=8.0, manifold="MF"), _p(az=275, w=8.0, manifold="MF"),
                  _p(az=320, w=7.0, manifold="MR"), _p(az=0, w=7.0, manifold="MR"),
                  _p(az=35, w=7.0, manifold="MR")],
    }


def params_U1():
    p = params_S1()
    p.update(name="U1", label="U: 1x Sunon 5015 (owned) front bay, S1 nozzle end")
    p["fans"] = {"F": fan_front("5015")}
    return p


def params_UD1():
    p = params_S1()
    p.update(name="UD1", label="U-Delta: 1x Delta BFB0524HH 5015 front bay, S1 nozzle end")
    p["fans"] = {"F": fan_front("delta")}
    return p


def params_US1():
    p = params_S1()
    p.update(name="US1", label="U-SameSky: 1x Same Sky CBM-5015BF (12 V PWM) front bay, S1 nozzle end")
    p["fans"] = {"F": fan_front("samesky")}
    return p


PARAM_SETS = {"REF": params_REF, "S1": params_S1, "D1": params_D1, "U1": params_U1, "UD1": params_UD1,
              "US1": params_US1}


def get_params(name):
    if name in PARAM_SETS:
        return PARAM_SETS[name]()
    raise KeyError(name)


def manifold_path(m):
    return RoundedRectPath(CB[0], CB[1], CB[2], CB[3], m["d"])


def manifold_poly(m, H_in):
    W = m["W"]
    return poly_gable(W, H_in, W / 2, b0=0.0), W        # a in [-W/2, W/2]; shifted below


def port_geometry(p, t, paths):
    """Compute the wedge port in the nozzle frame. Returns dict with sections etc."""
    az = math.radians(p["az"])
    rh = np.array([math.cos(az), math.sin(az), 0.0])             # radial (outward)
    yaw = math.radians(p.get("yaw", 0.0))
    dh = -(math.cos(yaw) * rh + math.sin(yaw) * np.cross(Z, rh))  # horizontal jet direction
    th = unit(np.cross(Z, -dh))                                   # lateral (left of the jet)
    z_ob = p["z_ob"] if p["z_ob"] is not None else DUCT_MIN_Z + 0.2 + t / math.cos(math.radians(p["alpha_f"]))
    z_ot = z_ob + p["h"]
    ta_f, ta_c = math.tan(math.radians(p["alpha_f"])), math.tan(math.radians(p["alpha_c"]))
    w = p["w"]
    # outlet distance: smallest r such that all outer outlet corners clear CB by the margin
    r = ray_exit_box(p["az"], *CB[:4])
    lat = w / 2 + t

    def clear(rr):
        c = rr * rh
        for f in np.linspace(-1, 1, 41):          # whole outlet edge, not only its corners
            q = c + f * lat * th
            if CB[0] - p["margin"] < q[0] < CB[1] + p["margin"] and CB[2] - p["margin"] < q[1] < CB[3] + p["margin"]:
                return False
        return True
    while not clear(r):
        r += 0.05
    r_o = r
    # back end: where the port enters its manifold (or a fixed length for direct-fed ports)
    if p.get("manifold"):
        path = paths[p["manifold"]]
        s = path.s_at_azimuth(p["az"])
        r_path = float(np.linalg.norm(path.at(s)[0]))
        L = r_path - r_o + p["overlap"]
    else:
        L = p.get("L", 7.0)
    w_b = p["w_back"] if p["w_back"] is not None else w * (r_o + L) / r_o
    c_o = r_o * rh
    c_b = c_o - L * dh
    zf_b, zc_b = z_ob + L * ta_f, z_ot + L * ta_c
    s_out = sec((c_o[0], c_o[1], 0.0), th, Z, poly_rect(w, p["h"], -w / 2, z_ob),
                outer=poly_rect(w + 2 * t, p["h"] + t / math.cos(math.radians(p["alpha_f"])) +
                                t / math.cos(math.radians(p["alpha_c"])), -w / 2 - t,
                                z_ob - t / math.cos(math.radians(p["alpha_f"]))))
    s_back = sec((c_b[0], c_b[1], 0.0), th, Z, poly_rect(w_b, zc_b - zf_b, -w_b / 2, zf_b),
                 outer=poly_rect(w_b + 2 * t, zc_b - zf_b + t / math.cos(math.radians(p["alpha_f"])) +
                                 t / math.cos(math.radians(p["alpha_c"])), -w_b / 2 - t,
                                 zf_b - t / math.cos(math.radians(p["alpha_f"]))))
    # jet: bisector of floor and ceiling at the outlet
    a_j = math.radians((p["alpha_f"] + p["alpha_c"]) / 2)
    z_c = (z_ob + z_ot) / 2
    aim_r = r_o - (z_c - I.LAYER_HEIGHT * -1 * -1 + 0.2) / math.tan(a_j)  # radius where bisector hits Z -0.2
    aim_r = r_o - (z_c + 0.2) / math.tan(a_j)
    # root: constant-section extension deeper into the manifold (clean junction, no slivers)
    if p.get("manifold") and p.get("root", 0) > 0:
        s_root = s_back.moved(-dh * p["root"])
        secs = (s_root, s_back, s_out)
    else:
        secs = (s_back, s_out)
    # square-ended top lip: the 45-deg ceiling meets the vertical outlet face in a knife edge; a
    # chamfer prism (inward, 45 deg, wall-thick) makes the lip end perpendicular to the ceiling
    tq = t
    ca, sa = math.cos(math.radians(p["alpha_c"])), math.sin(math.radians(p["alpha_c"]))
    tip = np.array([c_o[0], c_o[1], z_ot])
    p1 = tip + tq * (sa * dh + ca * Z)                     # perpendicular to the ceiling, toward the nozzle/up
    p2 = tip + Z * (tq / ca)                               # top of the vertical end face
    hw = w / 2 + t
    tri = [tip, p1, p2]
    lip = [[q + sgn * hw * th for q in tri] for sgn in (-1, 1)]
    return {"az": p["az"], "r_o": r_o, "L": L, "w": w, "w_back": w_b, "h": p["h"], "z_ob": z_ob, "z_ot": z_ot,
            "lip_tris": lip, "secs": secs,
            "z_back": [zf_b, zc_b], "c_out": [c_o[0], c_o[1], z_c], "dir_h": dh.tolist(), "lat": th.tolist(),
            "area_mm2": w * p["h"], "jet_bisector_deg": math.degrees(a_j), "aim_r_at_part_top": aim_r,
            "sections": (s_back, s_out),
            "min_channel_mm": min(w, p["h"]), "inscribed_d_outlet": inscribed_diameter(poly_rect(w, p["h"]))}


def required_H_in(m, ports_geo, z0):
    """Inner wall height so every port's back section fits under the manifold's inner wall top."""
    need = 0.0
    for g in ports_geo:
        need = max(need, g["z_back"][1] - z0 + m["H_margin"])
    return need


def build_chains(params):
    t = params["t"]
    chains = []
    info = {"ports": [], "manifolds": [], "feeds": []}
    paths = {m["id"]: manifold_path(m) for m in params["manifolds"]}
    pgeo = [port_geometry(p, t, paths) for p in params["ports"]]
    lips = []
    for p, g in zip(params["ports"], pgeo):
        g.pop("sections")
        secs = g.pop("secs")
        lips.append(g.pop("lip_tris"))
        chains.append(Chain(f"port_{p['az']}", list(secs), t=t, start="cap", end="open", role="port",
                            meta={"manifold": p.get("manifold"), "az": p["az"]}))
        info["ports"].append(g)
    info["_lips"] = lips

    for m in params["manifolds"]:
        path = paths[m["id"]]
        mine = [g for p, g in zip(params["ports"], pgeo) if p.get("manifold") == m["id"]]
        W = m["W"]
        s0, s1 = path.s_at_azimuth(m["az0"]), path.s_at_azimuth(m["az1"])
        # inner-wall height: what each port needs at its azimuth, interpolated along the path
        # (so the manifold is only as tall as the local port roots require)
        sp, hp = [], []
        for g in mine:
            sg = path.s_at_azimuth(g["az"])
            if sg < s0:
                sg += path.L
            sp.append(sg)
            hp.append(max(m["H_min"], g["z_back"][1] - m["z0"] + m["H_margin"]))
        order = np.argsort(sp)
        sp, hp = np.array(sp)[order], np.array(hp)[order]
        if m["H_in"] is not None:
            hp = np.full_like(hp, m["H_in"])
        ss = path.samples(s0, s1)
        extra = [x for x in sp if ss[0] + 0.5 < x < ss[-1] - 0.5]
        ss = sorted(set(ss + extra))
        H_in = float(hp.max()) if len(hp) else m["H_min"]
        secs = []
        for k, s in enumerate(ss):
            pxy, nrm = path.at(s)
            Hk = float(np.interp(s, sp, hp)) if len(hp) else m["H_min"]
            poly = poly_gable(W, Hk, W / 2, b0=0.0)
            poly = [(a + W / 2, b) for a, b in poly]       # a from the inner face (0) outward (W)
            u = np.array([nrm[0], nrm[1], 0.0])
            secs.append(Section(np.array([pxy[0], pxy[1], m["z0"]]), u, Z.copy(), poly))
        chains.append(Chain(f"manifold_{m['id']}", secs, t=t, start="cap", end="cap", role="manifold",
                            meta={"id": m["id"]}))
        poly0 = [(a + W / 2, b) for a, b in poly_gable(W, H_in, W / 2, b0=0.0)]
        info["manifolds"].append({"id": m["id"], "fan": m["fan"], "W": W, "H_in": H_in,
                                  "H_in_profile": [[round(float(a), 2), round(float(b), 2)] for a, b in zip(sp - s0, hp)],
                                  "z0": m["z0"],
                                  "apex_z": m["z0"] + H_in + W / 2, "area_mm2": poly_area(poly0),
                                  "az": [m["az0"], m["az1"]], "path_length": ss[-1] - ss[0],
                                  "inscribed_d": inscribed_diameter(poly0)})
        chains += feed_chains(params, m, params["fans"][m["fan"]], t, info, H_in)

    for df in params.get("direct_feeds", []):
        chains += direct_feed_chain(params, df, pgeo[df["port"]], t, info)
    return chains, info


def _lean_t(secs, t):
    """Wall offset so the perpendicular wall thickness stays >= t on leaning transition walls."""
    lean = 0.0
    for a, b in zip(secs[:-1], secs[1:]):
        n = unit(b.c - a.c) if np.linalg.norm(b.c - a.c) > 1e-9 else a.normal()
        for pa, pb in zip(a.pts(), b.pts()):
            e = np.asarray(pb) - np.asarray(pa)
            if np.linalg.norm(e) < 1e-9:
                continue
            lean = max(lean, math.acos(min(1.0, abs(float(unit(e) @ n)))))
    return t / math.cos(min(lean, math.radians(60))), math.degrees(lean)


def down_chain(name, fan, x, y, z, t, settle=2.0):
    """Vertical transition from a -Z blowing fan outlet to a horizontal rect (x range, y range) at z."""
    oc = np.array(fan["outlet_c"], float)
    a, b = fan["outlet_a"], fan["outlet_b"]
    uu, vv = X.copy(), -Y.copy()                       # u x v = -Z = flow
    # outlet rect in X/Y: outlet_u is +-X with size a, outlet_v is +-Y with size b
    s0 = Section(oc.copy(), uu, vv, poly_rect(a, b))
    s1 = s0.moved([0, 0, -settle])
    s2 = Section(np.array([(x[0] + x[1]) / 2, (y[0] + y[1]) / 2, z]), uu, vv, poly_rect(x[1] - x[0], y[1] - y[0]))
    secs = [s0, s1, s2]
    t_eff, lean = _lean_t(secs, t)
    return Chain(name, secs, t=t_eff, start="open", end="cap", role="feed", meta={"lean_deg": lean})


def plenum_chain(name, pl, t, end_poly=None):
    """Horizontal gable-roofed channel along +Y from pl['y'][0] (closed front) to pl['y'][1]."""
    y0, y1 = pl["y"]
    x0, x1 = pl["x"]
    n = 4
    secs = []
    for k in range(n + 1):
        f = k / n
        c = np.array([x0 + f * (x1 - x0), y0 + f * (y1 - y0), pl["z0"]])
        poly = poly_gable(pl["w"], pl["hs"], pl["w"] / 2, b0=0.0)
        if end_poly is not None and k == n:
            poly = end_poly
        secs.append(Section(c, -X.copy(), Z.copy(), poly))     # (-X) x Z = +Y = flow
    return Chain(name, secs, t=t, start="cap", end="cap", role="plenum")


def feed_chains(params, m, fan, t, info, H_in):
    fd = m["feed"]
    out = []
    if fd["kind"] == "front_plenum":
        pl = fd["plenum"]
        oc = np.array(fan["outlet_c"])
        a, b = fan["outlet_a"], fan["outlet_b"]
        # drop into the plenum's front part, keeping inside the plenum's walls
        x = [max(oc[0] - a / 2, pl["x"][0] - pl["w"] / 2 + 0.5), min(oc[0] + a / 2, pl["x"][0] + pl["w"] / 2 - 0.5)]
        y = [max(oc[1] - b / 2, pl["y"][0] + 1.0), oc[1] + b / 2]
        ch = down_chain(f"feed_{m['fan']}", fan, x, y, pl["drop_z"], t)
        pc = plenum_chain(f"plenum_{m['fan']}", pl, t)
        out = [ch, pc]
        info["feeds"].append({"fan": m["fan"], "kind": "front_plenum", "inlet_area_mm2": a * b,
                              "drop_area_mm2": (x[1] - x[0]) * (y[1] - y[0]),
                              "plenum_area_mm2": abs(poly_area(pc.sections[0].poly)), "t_eff": ch.t,
                              "lean_deg": ch.meta["lean_deg"],
                              "centerline": [s.c.tolist() for s in ch.sections] +
                                            [(s.c + np.array([0, 0, pl["hs"] / 2])).tolist() for s in pc.sections]})
    elif fd["kind"] == "right_low":
        out = [right_low_chain(fan, fd, m, t, info, H_in)]
    else:
        raise ValueError(fd["kind"])
    return out


def right_low_chain(fan, fd, m, t, info, H_in):
    """Horizontal outlet (blowing -Y): roofed expansion, 90 deg bend toward -X, run into the manifold."""
    oc = np.array(fan["outlet_c"], float)
    a, b = fan["outlet_a"], fan["outlet_b"]            # a along X (lateral), b along Z
    uu, vv = X.copy(), Z.copy()                        # X x Z = -Y = flow
    zb = oc[2] - b / 2
    s0 = Section(np.array([oc[0], oc[1], zb]), uu, vv, poly_gable(a, b, 0.0, b0=0.0))
    s1 = s0.moved([0, -1.5, 0])
    w, hs = fd["w"], fd["hs"]
    s2 = Section(np.array([oc[0], oc[1] - 1.5 - w / 2 - 1.0, max(zb, m["z0"] + 0.3)]), uu, vv,
                 poly_gable(w, hs, w / 2, b0=0.0))
    bend = bend_sections(s2, -Z, fd["bend_r"], 90.0, n=6)        # -Y -> -X
    endc = np.array([fd["end"][0], fd["end"][1], m["z0"] + 0.4])
    hs_end = max(3.0, H_in - 1.2)
    end = Section(endc, bend[-1].u, bend[-1].v, poly_gable(w, hs_end, min(w / 2, 3.0), b0=0.0))
    secs = [s0, s1, s2] + bend + [end]
    info["feeds"].append({"fan": m["fan"], "kind": "right_low", "inlet_area_mm2": a * b,
                          "end_area_mm2": abs(poly_area(end.poly)), "t_eff": t,
                          "centerline": [(s.c + np.array([0, 0, 4.0])).tolist() for s in secs]})
    return Chain(f"feed_{m['fan']}", secs, t=t, start="open", end="cap", role="feed", meta={"fan": m["fan"]})


def direct_feed_chain(params, df, g, t, info):
    """REF: front fan -> plenum -> straight into a single port (no manifold)."""
    fan = params["fans"][df["fan"]]
    zb0, zb1 = g["z_back"]
    cb = np.array(g["c_out"][:2]) - (g["L"] - 0.8) * np.array(g["dir_h"][:2])
    pl = copy.deepcopy(df["plenum"])
    pl["y"] = [pl["y"][0], float(cb[1])]
    pl["x"] = [pl["x"][0], float(cb[0])]
    pl["z0"] = min(pl["z0"], zb0 - 0.2)
    w_end = g["w_back"] + 1.0
    hs_end = max(3.0, zb1 - pl["z0"] + 0.3 - w_end / 2 + 0.5)
    pc = plenum_chain(f"plenum_{df['fan']}", pl, t, end_poly=poly_gable(w_end, hs_end, w_end / 2, b0=0.0))
    oc = np.array(fan["outlet_c"])
    a, b = fan["outlet_a"], fan["outlet_b"]
    x = [max(oc[0] - a / 2, pl["x"][0] - pl["w"] / 2 + 0.5), min(oc[0] + a / 2, pl["x"][0] + pl["w"] / 2 - 0.5)]
    y = [max(oc[1] - b / 2, pl["y"][0] + 1.0), oc[1] + b / 2]
    ch = down_chain(f"feed_{df['fan']}", fan, x, y, pl["drop_z"], t)
    info["feeds"].append({"fan": df["fan"], "kind": "direct", "inlet_area_mm2": a * b,
                          "drop_area_mm2": (x[1] - x[0]) * (y[1] - y[0]),
                          "plenum_area_mm2": abs(poly_area(pc.sections[0].poly)), "t_eff": ch.t,
                          "centerline": [s.c.tolist() for s in ch.sections] +
                                        [(s.c + np.array([0, 0, 3.0])).tolist() for s in pc.sections]})
    return [ch, pc]


def fan_stub(fan, t, depth=3.0, margin=2.5):
    """CFD fan-outlet stub: a block whose face in the outlet plane caps the feed opening."""
    oc = np.array(fan["outlet_c"], float)
    a, b = fan["outlet_a"], fan["outlet_b"]
    u, v = np.array(fan["outlet_u"], float), np.array(fan["outlet_v"], float)
    blow = np.array(fan["blow"], float)
    half = np.abs(u) * (a / 2 + margin) + np.abs(v) * (b / 2 + margin)
    lo = oc - half
    hi = oc + half
    up = -blow
    lo = np.minimum(lo, lo + up * depth)
    hi = np.maximum(hi, hi + up * depth)
    # flatten along the blow axis: from the outlet plane upstream by depth
    ax = int(np.argmax(np.abs(blow)))
    lo[ax], hi[ax] = sorted([oc[ax], oc[ax] + up[ax] * depth])
    return box_solid(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])


def fan_socket(fan, t, depth=4.0, clearance=1.0):
    """Printed socket that slides over the fan outlet nozzle (fan-side lip ESTIMATED 1.0 mm)."""
    oc = np.array(fan["outlet_c"], float)
    a, b = fan["outlet_a"], fan["outlet_b"]
    u, v = np.array(fan["outlet_u"], float), np.array(fan["outlet_v"], float)
    up = -np.array(fan["blow"], float)
    ai, bi = a + 2 * clearance, b + 2 * clearance
    outer = Section(oc, u, v, poly_rect(ai + 2 * T_WALL, bi + 2 * T_WALL))
    inner = Section(oc - up * 0.5, u, v, poly_rect(ai, bi))
    from geom import loft_sections
    o = loft_sections([outer, outer.moved(up * depth)])
    i = loft_sections([inner, inner.moved(up * (depth + 1.0))])
    # the fan outlet opening itself through the socket floor is already the feed air
    return o - i


TAB_LEFT = (-7.5, 19.5)       # (x, z) of the left duct-to-frame screw (structure stub uses X -7.5, Z 19.5)
TAB_RIGHT = (24.0, 22.5)      # right screw: right of the feed drop, under the fan's right edge


def mount_tabs(params, info):
    """Duct-to-frame attach points: M3 screws along +Y from the front into heat-set inserts in frame lugs
    (structure/frame.py builds a lug from the mating face back to the plate, bridged up to the plate's
    bottom edge Z 24.5). The duct tabs sit in front of the fan's rear plane (mating face Y = FAN_BACK_Y),
    below the fan and outside every air path, so screw heads are reachable from the front.
      left : an arm from the plenum's left wall to X -7.5, Z 19.5 (stub position)
      right: a tab on the feed drop's right wall at X 24.0, Z 22.5 (the frame lug bridges over the plenum,
             whose roof is below Z 18.7 there)"""
    tabs = []
    if not params["manifolds"] and not params.get("direct_feeds"):
        return tabs
    for tid, (x, z) in (("T_left", TAB_LEFT), ("T_right", TAB_RIGHT)):
        tabs.append({"id": tid, "xyz": [x, FAN_BACK_Y - 1.25, z], "axis": [0, 1, 0], "screw": "M3",
                     "face_y": FAN_BACK_Y, "pad": [7.0, 2.5, 7.0],
                     "note": "duct tab, mating face in the fan's rear plane; M3 along +Y into a frame lug insert"})
    return tabs


def tab_arms(params, tabs):
    """Connect each tab to the duct body (arm along X at the tab's Y/Z band)."""
    arms = []
    for tb in tabs:
        x, y, z = tb["xyz"]
        y0, y1 = y - tb["pad"][1] / 2, y + tb["pad"][1] / 2
        if tb["id"] == "T_left":
            xr = PLENUM_DEFAULT["x"][0] - PLENUM_DEFAULT["w"] / 2 + 0.5     # into the plenum's left wall
            arms.append(box_solid(x, xr, y0, y1, z - 3.0, z + 3.0))
            # the arm meets the plenum wall below its roof eave
            arms.append(box_solid(xr - 2.0, xr, y0, y1, PLENUM_DEFAULT["z0"], z + 3.0))
        else:
            arms.append(box_solid(17.5, x, y0, y1, z - 3.0, z + 3.0))
    return arms


def tab_solids(tabs):
    """(blocks, holes) for the tabs; holes are cut after every union so arms cannot refill them."""
    blocks, holes = [], []
    for tb in tabs:
        x, y, z = tb["xyz"]
        px, py, pz = tb["pad"]
        ax = int(np.argmax(np.abs(tb["axis"])))
        blocks.append(box_solid(x - px / 2, x + px / 2, y - py / 2, y + py / 2, z - pz / 2, z + pz / 2))
        L = [px, py, pz][ax] + 2
        cyl = Solid.make_cylinder(1.7, L)
        if ax == 0:
            cyl = cyl.rotate(Axis.Y, 90)
        elif ax == 1:
            cyl = cyl.rotate(Axis.X, -90)
        c = np.array([x, y, z])
        c[ax] -= L / 2
        holes.append(cyl.translate(tuple(c)))
    return blocks, holes


# ============================================================================ main API
def build_ducts(params, with_print_extras=True):
    """Build all solids for a parameter set. Returns dict name -> Solid/Part."""
    t = params["t"]
    chains, info = build_chains(params)
    air = fuse_all([c.air() for c in chains])
    lip_solids = []
    for a, b in info.pop("_lips", []):
        wa = Wire.make_polygon([tuple(q) for q in a], close=True)
        wb = Wire.make_polygon([tuple(q) for q in b], close=True)
        lip_solids.append(Solid.make_loft([wa, wb], ruled=True))
    outer = fuse_all([c.outer_solid() for c in chains] + lip_solids)
    shell = (outer - air).clean()
    parts = {"air": air, "shell": shell}
    stubs = {}
    for fid, fan in params["fans"].items():
        stubs[fid] = fan_stub(fan, t)
        parts[f"stub_{fid}"] = stubs[fid]
        parts[f"fan_{fid}"] = box_solid(*fan["box"])
    parts["body_cfd"] = fuse_all([shell] + list(stubs.values()))
    if with_print_extras:
        extras = [fan_socket(f, t) for f in params["fans"].values()]
        tabs = mount_tabs(params, info)
        blocks, holes = tab_solids(tabs)
        extras += blocks + tab_arms(params, tabs)
        body = fuse_all([shell] + extras) - air
        for h in holes:
            body = body - h
        parts["body"] = body.clean()
        info["tabs"] = tabs
    parts["_info"] = info
    parts["_chains"] = chains
    return parts


# ============================================================================ checks / mass / interface
KEEP_OUT = {
    "sock+3mm (HOT_ZONE_CLEARANCE)": CB,
    "heatsink": (I.HEATSINK.xmin, I.HEATSINK.xmax, I.HEATSINK.ymin, I.HEATSINK.ymax, I.HEATSINK.zmin, I.HEATSINK.zmax),
    "3010 fan": (I.FAN3010.xmin, I.FAN3010.xmax, I.FAN3010.ymin, I.FAN3010.ymax, I.FAN3010.zmin, I.FAN3010.zmax),
    "PCB": (I.PCB.xmin, I.PCB.xmax, I.PCB.ymin, I.PCB.ymax, I.PCB.zmin, I.PCB.zmax),
    "PCB component zone": (I.PCB_COMPONENT_ZONE.xmin, I.PCB_COMPONENT_ZONE.xmax, I.PCB_COMPONENT_ZONE.ymin,
                           I.PCB_COMPONENT_ZONE.ymax, I.PCB_COMPONENT_ZONE.zmin, I.PCB_COMPONENT_ZONE.zmax),
    "extruder": (I.EXTRUDER.xmin, I.EXTRUDER.xmax, I.EXTRUDER.ymin, I.EXTRUDER.ymax, I.EXTRUDER.zmin, I.EXTRUDER.zmax),
    **{f"LIDAR_RESERVED_{nm}": (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)
       for nm, b in (("OPTICAL", I.LIDAR_RESERVED_OPTICAL), ("BODY", I.LIDAR_RESERVED_BODY))},
    "PROBE_ADAPTER_785004": (I.PROBE_ADAPTER_785004.xmin, I.PROBE_ADAPTER_785004.xmax, I.PROBE_ADAPTER_785004.ymin,
                             I.PROBE_ADAPTER_785004.ymax, I.PROBE_ADAPTER_785004.zmin, I.PROBE_ADAPTER_785004.zmax),
    "probe body (ESTIMATED keep-out)": PROBE_KEEPOUT,
    "below DUCT_MIN_Z": (-200, 200, -200, 200, -100, DUCT_MIN_Z),
    "XCARRIAGE": (I.XCARRIAGE.xmin, I.XCARRIAGE.xmax, I.XCARRIAGE.ymin, I.XCARRIAGE.ymax, I.XCARRIAGE.zmin, I.XCARRIAGE.zmax),
    "X-joint band right (X>RIGHT_LIMIT_X in Z 44.3..91.8)": (float(I.RIGHT_LIMIT_X), 400, -200, 200, I.XY_JOINT_BAND_Z[0], I.XY_JOINT_BAND_Z[1]),
    "X-joint band left (X<LEFT_LIMIT_X in Z 44.3..91.8)": (-400, float(I.LEFT_LIMIT_X), -200, 200, I.XY_JOINT_BAND_Z[0], I.XY_JOINT_BAND_Z[1]),
    "rear limit (Y>REAR_LIMIT_Y below Z30)": (-200, 200, float(I.REAR_LIMIT_Y), 200, -100, 30.0),
}
SOFT_LIMITS = {"FRONT_LIMIT_Y (MISSING)": ("y", "min", float(I.FRONT_LIMIT_Y)),
               "RIGHT_LIMIT_X (MISSING)": ("x", "max", float(I.RIGHT_LIMIT_X))}


def _vol_intersect(a, b):
    try:
        r = a & b
        return float(r.volume) if r is not None else 0.0
    except Exception:
        return float("nan")


def overhang_report(air, openings, limit_deg=45.0, up=(0, 0, 1), body=None):
    """Area of internal air-path surface that faces downward more steeply than `limit_deg` from
    vertical in the given print orientation (`up` = print Z in the nozzle frame).
    Air-solid outward normals point into the wall; a ceiling has n.up > cos(limit)."""
    up = unit(up)
    cl = math.cos(math.radians(limit_deg))
    bad, total, worst = 0.0, 0.0, 0.0
    for f in air.faces():
        c = np.array(tuple(f.center()))
        if any(o(f) for o in openings):
            continue
        try:
            n = np.array(tuple(f.normal_at(f.center())))
        except Exception:
            continue
        if body is not None:                      # skip air faces with no wall behind them
            q = c + n * 0.3
            if not body.is_inside(tuple(q)):
                continue
        A = f.area
        total += A
        cosang = float(n @ up)
        if cosang > cl + 1e-3:
            bad += A
            worst = max(worst, math.degrees(math.acos(min(1.0, cosang))))
    return {"print_up": list(up), "limit_deg": limit_deg, "air_surface_mm2": total,
            "overhang_area_mm2": bad, "worst_face_angle_from_horizontal_deg": (90 - worst) if bad else None}


def build_info(params, parts):
    """Checks, mass, ports and the duct interface for a built parameter set."""
    info = parts["_info"]
    body = parts.get("body", parts["shell"])
    rep = {"name": params["name"], "label": params["label"]}
    # --- keep-outs
    ko = {}
    solids = {"duct body": body}
    for fid in params["fans"]:
        solids[f"fan {fid}"] = parts[f"fan_{fid}"]
    for kname, b in KEEP_OUT.items():
        kb = box_solid(*b)
        for sname, sol in solids.items():
            if sname.startswith("fan") and kname in ("below DUCT_MIN_Z",):
                continue
            v = _vol_intersect(sol, kb)
            if v > 1e-3:
                ko[f"{sname} x {kname}"] = round(v, 3)
    rep["keepout_violations_mm3"] = ko
    bb = [body.bounding_box()] + [parts[f"fan_{f}"].bounding_box() for f in params["fans"]]
    lo = np.min([tuple(b.min) for b in bb], axis=0)
    hi = np.max([tuple(b.max) for b in bb], axis=0)
    rep["envelope"] = {"min": lo.round(2).tolist(), "max": hi.round(2).tolist()}
    soft = {}
    if lo[1] < float(I.FRONT_LIMIT_Y):
        soft["FRONT_LIMIT_Y"] = round(float(I.FRONT_LIMIT_Y) - lo[1], 2)
    soft["width_right_of_nozzle_mm"] = round(float(hi[0]), 2)
    soft["width_left_of_nozzle_mm"] = round(float(-lo[0]), 2)
    rep["soft_limit_excess_mm"] = soft
    rep["intake_window_3010"] = intake_window(params, body)
    # --- printability (upright, fan socket up). Openings: port outlets and fan outlets.
    openings = []
    for g in info["ports"]:
        c = np.array(g["c_out"])
        dh = np.array(g["dir_h"])
        openings.append(lambda f, c=c, dh=dh: abs(float((np.array(tuple(f.center())) - c) @ dh) - 0.0) < 1.3
                        and abs(float(np.array(tuple(f.normal_at(f.center()))) @ dh)) > 0.99)
    for fan in params["fans"].values():
        oc = np.array(fan["outlet_c"])
        bl = np.array(fan["blow"])
        openings.append(lambda f, oc=oc, bl=bl: abs(float((np.array(tuple(f.center())) - oc) @ bl)) < 1.3
                        and abs(float(np.array(tuple(f.normal_at(f.center()))) @ bl)) > 0.99)
    rep["printability"] = {
        "orientation": "upright (nozzle-frame +Z = print Z), fan socket on top, external supports only under the lips",
        "air_path_overhangs": overhang_report(parts["air"], openings, body=body),
        "wall_mm": params["t"],
        "min_channel_mm": min([g["min_channel_mm"] for g in info["ports"]] +
                              [m["inscribed_d"] for m in info["manifolds"]] + [99]),
    }
    # --- mass (nozzle end within 15 mm of the heater in PC, everything in PC for simplicity of
    # a one-piece print; ASA figure given for comparison)
    v_body = float(body.volume) / 1000.0
    hb = I.HEATER_BODY
    near = box_solid(hb.xmin - 15, hb.xmax + 15, hb.ymin - 15, hb.ymax + 15, hb.zmin - 15, hb.zmax + 15)
    v_near = _vol_intersect(body, near) / 1000.0
    m_fans = sum(f["mass_g"] for f in params["fans"].values())
    rep["mass"] = {"body_volume_cm3": round(v_body, 3), "volume_within_15mm_of_heater_cm3": round(v_near, 3),
                   "mass_all_PC_g": round(v_body * DENSITY["PC"], 2), "mass_all_ASA_g": round(v_body * DENSITY["ASA"], 2),
                   "mass_PC_near_ASA_rest_g": round(v_near * DENSITY["PC"] + (v_body - v_near) * DENSITY["ASA"], 2),
                   "fans_g": m_fans, "fan_types": {k: f["type"] for k, f in params["fans"].items()},
                   "total_PC_g": round(v_body * DENSITY["PC"] + m_fans, 2),
                   "notes": "4020 mass ESTIMATED 18 g; Sunon 5015 28.4 g; screws/inserts not included"}
    rep["ports"] = [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()} for g in info["ports"]]
    rep["outlet_area_total_mm2"] = round(sum(g["area_mm2"] for g in info["ports"]), 2)
    rep["manifolds"] = info["manifolds"]
    rep["feeds"] = [{k: v for k, v in f.items() if k != "centerline"} for f in info["feeds"]]
    rep["tabs"] = info.get("tabs", [])
    return rep


def intake_window(params, body):
    """3010 intake: the 3010 (behind the PCB) breathes through the gap between the PCB components
    (Y -31.5, ESTIMATED) and whatever sits in front of it, as in stock (stock 4020 rear face Y -30.2).
    Report that gap over the 3010 face (X -15..15, Z 31.3..61.3) and its open side area."""
    zone_front = I.PCB_COMPONENT_ZONE.ymin
    win = box_solid(-15.0, 15.0, -80.0, zone_front, I.FAN3010.zmin, I.FAN3010.zmax)
    ymax_front = -80.0
    for fid, fan in params["fans"].items():
        b = fan["box"]
        if b[1] > -15 and b[0] < 15 and b[5] > I.FAN3010.zmin and b[4] < I.FAN3010.zmax and b[3] <= zone_front + 5:
            ymax_front = max(ymax_front, b[3])
    try:
        cut = body & win
        if cut is not None and cut.volume > 1e-3:
            ymax_front = max(ymax_front, cut.bounding_box().max.Y)
    except Exception:
        pass
    gap = zone_front - ymax_front
    stock_gap = zone_front - I.STOCK_4020_POS.ymax
    return {"ok": gap >= stock_gap, "gap_mm": round(gap, 2), "stock_gap_mm": round(stock_gap, 2),
            "open_side_area_mm2": round(max(gap, 0) * 2 * (I.FAN3010.zmax - I.FAN3010.zmin), 1),
            "note": "gap between PCB component zone front and the part-fan rear face over the 3010; stock is "
                    f"{stock_gap:.1f} mm (fan overlaps the ESTIMATED zone), so >= stock keeps the stock intake path"}


def interface_json(params, rep, version, final=False):
    fans = {}
    for fid, f in params["fans"].items():
        fans[fid] = {"type": f["type"], "spec": f["spec"], "envelope_box": {"xmin": f["box"][0], "xmax": f["box"][1],
                                                                            "ymin": f["box"][2], "ymax": f["box"][3],
                                                                            "zmin": f["box"][4], "zmax": f["box"][5]},
                     "intake_normal": f["intake"], "outlet_centre": f["outlet_c"], "outlet_blow_dir": f["blow"],
                     "outlet_size_mm": [f["outlet_a"], f["outlet_b"]],
                     "screw_bosses": f["holes"], "mass_g": f["mass_g"],
                     "status": "ESTIMATED outlet size and hole positions (generic frames); measure (M7)"}
    return {
        "schema": "k1-toolhead duct interface",
        "version": version, "final_mount_points": final,
        "frame": "nozzle frame: origin nozzle tip, +X right, +Y rear, +Z up, mm",
        "duct_param_set": params["name"], "label": params["label"],
        "fans": fans,
        "fan_mounting": "fans are held by the cooling-module frame (Structure) through their own corner holes; "
                        "screw_bosses give hole centre, axis and length through the fan frame. The duct's fan socket "
                        "slides over the fan outlet nozzle (4 mm deep, 1.0 mm clearance per side, ESTIMATED).",
        "duct_attach_points": [{"id": t["id"], "hole_centre": [round(v, 3) for v in t["xyz"]],
                                "screw": t["screw"], "screw_axis": t["axis"],
                                "mating_face": {k: round(v, 3) for k, v in t.items() if k.startswith("face_")},
                                "tab_size_mm": t["pad"], "note": t["note"]}
                               for t in rep.get("tabs", [])],
        "duct_envelope": rep["envelope"],
        "keep_clear_for_duct": "the duct body's space: see duct_envelope and the STEP; the frame must not enter "
                               "the duct air path or come within 3 mm of the sock (interfaces.HOT_ZONE_CLEARANCE)",
        "duct_materials": "nozzle end PC or PA-CF (DD-07); printed upright, fan socket up",
        "duct_mass_g": rep["mass"]["mass_all_PC_g"],
        "keepout_violations_mm3": rep["keepout_violations_mm3"],
        "soft_limit_excess_mm": rep["soft_limit_excess_mm"],
        "intake_window_3010": rep["intake_window_3010"],
    }


def export_part(params, outdir, parts=None):
    """Write STEP/STL of the printed body and the air path + the build report."""
    from build123d import export_step, export_stl
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    parts = parts or build_ducts(params)
    export_step(parts["body"], str(outdir / f"duct_{params['name']}.step"))
    export_stl(parts["body"], str(outdir / f"duct_{params['name']}.stl"))
    export_step(parts["air"], str(outdir / f"air_{params['name']}.step"))
    rep = build_info(params, parts)
    (outdir / f"duct_{params['name']}_report.json").write_text(json.dumps(rep, indent=2, default=float))
    return rep


if __name__ == "__main__":
    import time
    name = sys.argv[1] if len(sys.argv) > 1 else "S1"
    t0 = time.time()
    P = get_params(name)
    parts = build_ducts(P)
    rep = build_info(P, parts)
    print(json.dumps(rep, indent=1, default=float)[:6000])
    print("time", time.time() - t0)


def write_interface_file(params, version, final=False, path=None):
    """Build the parameter set and write duct_interface.json next to this file."""
    parts = build_ducts(params)
    rep = build_info(params, parts)
    js = interface_json(params, rep, version, final)
    js["generated_by"] = "cad/source/ducts/duct_generator.py::write_interface_file"
    js["status_note"] = ("v0: PROVISIONAL. Fan pose (front bay, stock-like) and the duct envelope are stable; "
                         "attach-point positions will move with the CFD iterations. Do not machine/print the frame "
                         "against these until final_mount_points is true.") if not final else \
        "FINAL mount points for the released duct parameter set (PARAMS_FINAL)."
    path = Path(path) if path else HERE / "duct_interface.json"
    path.write_text(json.dumps(js, indent=2, default=float))
    return js


def wall_report(shape, n=3000, seed=1, tol=0.02):
    """Local wall thickness by inward rays from sampled surface points (same method as
    cad/source/validate.py): stats + the thinnest sample locations."""
    import tempfile
    import trimesh
    from build123d import export_stl
    f = Path(tempfile.mkdtemp()) / "b.stl"
    export_stl(shape, str(f), tolerance=tol, angular_tolerance=0.1)
    m = trimesh.load(str(f), force="mesh")
    pts, fidx = trimesh.sample.sample_surface(m, n, seed=seed)
    nrm = m.face_normals[fidx]
    tri = m.triangles
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    out, where = [], []
    for p, nv in zip(pts, nrm):
        d = -nv
        pv = np.cross(d, e2)
        det = (e1 * pv).sum(1)
        ok = np.abs(det) > 1e-12
        inv = np.zeros_like(det)
        inv[ok] = 1.0 / det[ok]
        tv = p - v0
        u = (tv * pv).sum(1) * inv
        qv = np.cross(tv, e1)
        v = (qv * d).sum(1) * inv
        t = (e2 * qv).sum(1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
        if hit.any():
            out.append(float(t[hit].min()))
            where.append(p)
    a = np.array(out)
    order = np.argsort(a)[:12]
    return {"samples": int(a.size), "min_mm": round(float(a.min()), 3), "p1_mm": round(float(np.percentile(a, 1)), 3),
            "share_below_0.8": round(float((a < 0.8).mean()), 4), "share_below_1.1": round(float((a < 1.1).mean()), 4),
            "thinnest": [[round(float(a[i]), 3)] + np.round(where[i], 2).tolist() for i in order]}


# The released design (updated as the CFD iterations conclude; see documentation/cfd-report.md).
PARAMS_FINAL = params_S1()
