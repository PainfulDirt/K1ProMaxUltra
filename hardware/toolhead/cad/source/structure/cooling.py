"""Cooling-module interface: the STUB used until the Duct/CFD agent publishes
cad/source/ducts/duct_interface.json + build_ducts(params), and the adapter
that reads the real one.

Switch in cad/source/assembly.py:  COOLING_SOURCE = "stub" | "ducts" | "auto"

Expected duct_interface.json (what this adapter reads; coordinate frame =
nozzle frame of interfaces.py, mm). Keys in [] are optional:

{
  "schema": "k1th.duct_interface/1",
  "status": "DRAFT" | "FINAL",
  "fans": [ { "id": "part_fan_1",
              "model": "BLOWER_4020_STOCK",            # name of a BlowerSpec in interfaces.py
              "envelope": [xmin, xmax, ymin, ymax, zmin, zmax],   # axis-aligned envelope
              ["intake": {"center": [x,y,z], "normal": [..], "d": 28}],
              "screw_bosses": [ {"pos": [x,y,z], "axis": [0,1,0], "screw": "M3",
                                 ["kind": "insert"|"selftap"]} ] } ],
  "duct_mounts": [ {"pos": [x,y,z], "axis": [0,1,0], "screw": "M3", ["kind": ...]} ],
  ["duct_bodies": [ {"id": "duct_main", "step": "relative/path.step", "material": "PC"} ]]
}
A mount point is the point on the FRAME-side contact face; "axis" is the
screw insertion direction (from the mating part into the frame). The frame
generator currently supports axes along +-Y (fan and duct screws from the
front); any other axis fails loudly so it gets implemented, not ignored.
If build_ducts(params) exists it is preferred over duct_bodies[].step; it must
return {name: solid} or a list of (name, solid, material).
"""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .common import bx, prm, cyl_y, PartSpec, group_params, FRAME_FRONT_Y
import interfaces as I

G = "cooling_stub"
DUCTS_DIR = Path(I.__file__).resolve().parent / "ducts"
DUCT_JSON = DUCTS_DIR / "duct_interface.json"

# ---- STUB layout (all STUB: replaced by the Duct/CFD agent's values) --------
STUB_BLOWER = I.BLOWER_4020_STOCK
STUB_FRAME_FRONT_Y = FRAME_FRONT_Y
STUB_GAP_Y = prm(G, "STUB_BLOWER_GAP_Y", 3.0, "STUB",
                 "plenum between frame plate and blower back (3010 intake through the frame window), 1 mm over the ribs")
# XZ placement copies the stock 4020 (STOCK_4020_POS centre) and its 3 stock screw axes (02:C7, Henlor)
_SP = I.STOCK_4020_POS
STUB_CX = (_SP.xmin + _SP.xmax) / 2
STUB_CZ = (_SP.zmin + _SP.zmax) / 2
# The stock upper-right screw (16.05, 60.3) is NOT used: its standoff would block the
# frame's PCB screw at (12, 58.3) (4.5 mm apart). Diagonal pair only.
STUB_HOLES_XZ = [(prm(G, "STUB_4020_HOLE2_X", -18.65, "STUB", "stock 4020 screw, upper-left (02:C7)"), 60.3),
                 (16.05, prm(G, "STUB_4020_HOLE3_Z", 25.6, "STUB", "stock 4020 screw, lower-right (02:C7)"))]
STUB_DUCT_WALL = prm(G, "STUB_DUCT_WALL", 1.2, "STUB", "placeholder duct shell wall")
STUB_DUCT_TIP_Y = prm(G, "STUB_DUCT_TIP_Y", -12.0, "STUB", "nozzle-end face; sock front -8.6 + 3 clearance")
STUB_DUCT_ZMIN = prm(G, "STUB_DUCT_ZMIN", 3.0, "STUB", ">= DUCT_MIN_Z")
STUB_DUCT_MOUNT_X = prm(G, "STUB_DUCT_MOUNT_X", 7.5, "STUB", "duct-to-frame screws at X +-7.5 (lug stays right of LIDAR_RESERVED_BODY x -12)")
STUB_DUCT_MOUNT_Z = prm(G, "STUB_DUCT_MOUNT_Z", 19.5, "STUB", "below the PCB bottom edge and the fan")
STUB_DUCT_MOUNT_Y = FRAME_FRONT_Y - STUB_GAP_Y          # lug front face = fan back plane


@dataclass
class CoolingInterface:
    is_stub: bool
    source: str
    fans: list = field(default_factory=list)        # dicts: model, solid, mass_g, screw_bosses, notes
    duct_mounts: list = field(default_factory=list)
    duct_parts: list = field(default_factory=list)  # PartSpec
    status: str = "STUB"
    raw: dict = field(default_factory=dict)


def _blower_envelope():
    w, h, t = STUB_BLOWER.frame
    y1 = STUB_FRAME_FRONT_Y - STUB_GAP_Y
    return (STUB_CX - w / 2, STUB_CX + w / 2, y1 - t, y1, STUB_CZ - h / 2, STUB_CZ + h / 2)


def stub_interface() -> CoolingInterface:
    x0, x1, y0, y1, z0, z1 = _blower_envelope()
    fan = {
        "id": "part_fan_1", "model": "BLOWER_4020_STOCK",
        "envelope": [x0, x1, y0, y1, z0, z1],
        "intake": {"center": [0.0, y0, (z0 + z1) / 2], "normal": [0, -1, 0], "d": 28.0},
        "outlet": {"rect": [x1 - STUB_BLOWER.outlet[1], x1, y0 + 1.5, y0 + 1.5 + STUB_BLOWER.outlet[0]], "z": z0},
        "screw_bosses": [{"pos": [x, y1, z], "axis": [0, 1, 0], "screw": "M3", "kind": "insert"}
                         for x, z in STUB_HOLES_XZ],
    }
    mounts = [{"pos": [sx * STUB_DUCT_MOUNT_X, STUB_DUCT_MOUNT_Y, STUB_DUCT_MOUNT_Z],
               "axis": [0, 1, 0], "screw": "M3", "kind": "insert"} for sx in (-1, 1)]
    raw = {"schema": "k1th.duct_interface/0-stub", "status": "STUB", "fans": [fan], "duct_mounts": mounts}
    ci = _from_dict(raw, is_stub=True, source="structure/cooling.py stub")
    ci.duct_parts = [PartSpec("stub_duct_placeholder", _stub_duct(fan), "stub", "PC", (0.95, 0.55, 0.10),
                              deps=list(group_params(G)),
                              notes="STUB duct volume (hollow shell) - replaced by build_ducts()")]
    return ci


def _stub_duct(fan):
    """Placeholder duct: riser under the blower outlet + horizontal nozzle-end
    channel + a tab wall carrying the two duct-to-frame mount points."""
    t = STUB_DUCT_WALL
    ox0, ox1, oy0, oy1 = fan["outlet"]["rect"]
    zt = fan["outlet"]["z"]
    zc = 10.0
    riser_o = bx(ox0 - t, ox1 + t, oy0 - t, oy1 + t, zc - 1, zt)
    riser_i = bx(ox0, ox1, oy0, oy1, zc - 1 + t, zt + 1)
    chan_o = bx(-10.0, ox1 + t, oy0 - t, STUB_DUCT_TIP_Y, STUB_DUCT_ZMIN, zc)
    chan_i = bx(-10.0 + t, ox1, oy0, STUB_DUCT_TIP_Y + 1, STUB_DUCT_ZMIN + t, zc - t)
    body = (riser_o + chan_o) - riser_i - chan_i
    # tab wall up to the mount points (front face of the frame lugs = STUB_DUCT_MOUNT_Y)
    xs = STUB_DUCT_MOUNT_X + 4.5
    tab = bx(-xs, xs, STUB_DUCT_MOUNT_Y - 3.0, STUB_DUCT_MOUNT_Y, zc - 0.5, min(zt, STUB_DUCT_MOUNT_Z + 4.5))
    for sx in (-1, 1):
        tab = tab - cyl_y(sx * STUB_DUCT_MOUNT_X, STUB_DUCT_MOUNT_Z, STUB_DUCT_MOUNT_Y - 4, STUB_DUCT_MOUNT_Y + 1, 3.4)
    return body + tab


def _convert_ducts_schema(d: dict) -> dict:
    """Duct/CFD agent schema ("k1-toolhead duct interface", fans as a dict, envelope_box,
    screw_bosses[xyz, through_length], duct_attach_points[hole_centre, mating_face]) ->
    the internal schema documented at the top of this file."""
    if isinstance(d.get("fans"), list):
        return d
    fans = []
    model_of = {"4020": "BLOWER_4020_STOCK", "5015": "BLOWER_5015_SUNON", "5015D": "BLOWER_5015_DELTA"}
    for fid, f in d["fans"].items():
        e = f["envelope_box"]
        env = [e["xmin"], e["xmax"], e["ymin"], e["ymax"], e["zmin"], e["zmax"]]
        n = f.get("intake_normal", [0, -1, 0])
        c = [(env[0] + env[1]) / 2, env[2] if n[1] < 0 else env[3], (env[4] + env[5]) / 2]
        bosses = []
        for b in f.get("screw_bosses", []):
            ax = b["axis"]
            half = b.get("through_length", 0.0) / 2
            pos = [b["xyz"][i] + ax[i] * half for i in range(3)]     # fan face toward the frame
            bosses.append({"pos": pos, "axis": ax, "screw": "M3", "kind": "insert", "status": b.get("status", "")})
        fans.append({"id": fid, "model": model_of.get(str(f.get("type")), "BLOWER_4020_STOCK"), "envelope": env,
                     "intake": {"center": c, "normal": n, "d": 28.0}, "screw_bosses": bosses,
                     "mass_g": f.get("mass_g")})
    mounts = []
    for t in d.get("duct_attach_points", []):
        hc, mf = t["hole_centre"], t.get("mating_face", {})
        pos = [hc[0], mf.get("face_y", hc[1]), mf.get("face_z", hc[2])] if "face_y" in mf else \
              [hc[0], hc[1], mf.get("face_z", hc[2])]
        mounts.append({"id": t.get("id"), "pos": pos, "axis": t["screw_axis"], "screw": t.get("screw", "M3"),
                       "kind": "insert", "optional": "optional" in t.get("note", ""), "note": t.get("note", "")})
    return {"schema": d.get("schema"), "status": "FINAL" if d.get("final_mount_points") else
            f"PROVISIONAL {d.get('version', '')}", "fans": fans, "duct_mounts": mounts,
            "duct_param_set": d.get("duct_param_set"), "duct_materials": d.get("duct_materials", "PC")}


def _from_dict(d: dict, is_stub: bool, source: str) -> CoolingInterface:
    d = _convert_ducts_schema(d)
    ci = CoolingInterface(is_stub=is_stub, source=source, status=d.get("status", "?"), raw=d)
    for f in d.get("fans", []):
        spec = getattr(I, f.get("model", ""), None)
        env = f.get("envelope")
        if env is None:
            raise KeyError(f"duct_interface fan {f.get('id')}: 'envelope' [xmin..zmax] required")
        solid = bx(*env)
        mass = f.get("mass_g") or (float(spec.mass_g) if spec is not None else None)
        ci.fans.append({"id": f.get("id"), "model": f.get("model", "fan"), "solid": solid, "mass_g": mass,
                        "screw_bosses": f.get("screw_bosses", []), "envelope": env,
                        "intake": f.get("intake"), "outlet": f.get("outlet"),
                        "notes": "STUB pose" if is_stub else f"pose from {source}"})
    ci.duct_mounts = d.get("duct_mounts", [])
    for m in ci.duct_mounts + [b for f in ci.fans for b in f["screw_bosses"]]:
        if "pos" not in m or "axis" not in m:
            raise KeyError(f"mount point without pos/axis: {m}")
    return ci


def real_interface(params: dict | None = None) -> CoolingInterface:
    """Read cad/source/ducts/duct_interface.json and the duct solids (Duct/CFD agent)."""
    if not DUCT_JSON.exists():
        raise FileNotFoundError(f"{DUCT_JSON} not published yet - use COOLING_SOURCE='stub'")
    d = json.loads(DUCT_JSON.read_text())
    ci = _from_dict(d, is_stub=False, source=str(DUCT_JSON))
    final = bool(d.get("final_mount_points", d.get("status") == "FINAL"))
    prm("cooling_real", "DUCT_MOUNT_POINTS_FINAL", 1.0 if final else 0.0, "DERIVED" if final else "MISSING",
        f"duct_interface.json {d.get('version', '')}: final_mount_points={final} (Duct/CFD agent)")
    parts = []
    bd = None
    for modname in ("ducts", "ducts.duct_generator"):
        try:
            mod = importlib.import_module(modname)
            bd = getattr(mod, "build_ducts", None)
            if bd is not None:
                break
        except ImportError:
            continue
    if bd is not None:
        if params is None:
            gp = getattr(mod, "get_params", None) or (lambda n: getattr(mod, "PARAM_SETS")[n]())
            params = gp(ci.raw.get("duct_param_set") or "S1")
        out = bd(params)
        mat = "PC" if "PC" in str(ci.raw.get("duct_materials", "PC")) else "PA-CF"
        body = out.get("body") if isinstance(out, dict) else None
        if body is None:
            raise KeyError("build_ducts() returned no 'body' part")
        parts.append(PartSpec("duct_body", body, "printed", mat, (0.95, 0.55, 0.10), deps=[],
                              notes="owned by the Duct/CFD agent (cad/source/ducts); status " + ci.status))
    else:
        from build123d import import_step
        for b in d.get("duct_bodies", []):
            s = import_step(str(DUCTS_DIR / b["step"]))
            parts.append(PartSpec(f"duct_{b['id']}", s, "printed", b.get("material", "PC"), (0.95, 0.55, 0.10),
                                  notes="owned by Duct/CFD agent (STEP)"))
    ci.duct_parts = parts
    return ci


def get_cooling(source: str = "auto", params: dict | None = None) -> CoolingInterface:
    if source == "stub":
        return stub_interface()
    if source == "ducts":
        return real_interface(params)
    if source == "auto":
        return real_interface(params) if DUCT_JSON.exists() else stub_interface()
    if source == "auto-final":
        final = DUCT_JSON.exists() and bool(json.loads(DUCT_JSON.read_text()).get("final_mount_points"))
        return real_interface(params) if final else stub_interface()
    raise ValueError(source)
