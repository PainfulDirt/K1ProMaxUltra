"""Cooling-module interface: the adapter that reads the Duct/CFD agent's
cad/source/ducts/duct_interface.json + build_ducts(params), and a STUB fallback.

Current state: the JSON is v3-final (final_mount_points: true, param set S7: one
stock 4020 in the front bay + the S7 multi-port duct), so assembly.py's default
COOLING_SOURCE = "auto-final" builds the REAL duct body. The stub below is only a
fallback (COOLING_SOURCE = "stub", or a JSON without final mount points) and
reproduces the pre-CFD placeholder (1 x 4020 at the stock pose + a box duct).

Switch in cad/source/assembly.py:  COOLING_SOURCE = "auto-final" | "ducts" | "auto" | "stub"

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

from .common import bx, prm, cyl_y, PartSpec, group_params, FRAME_FRONT_Y, PARAMS, screw_mass_g
import interfaces as I
from interfaces import Dim

G = "cooling_stub"
DUCTS_DIR = Path(I.__file__).resolve().parent / "ducts"
DUCT_JSON = DUCTS_DIR / "duct_interface.json"

# ---- STUB layout (fallback only; all STUB) ----------------------------------
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
# Blower inlet ring diameter (the cover's intake aperture is sized from it). No datasheet value for the stock
# 4020 (or the 5015s) is in interfaces.py; 28 is the value this adapter always used.
FAN_INLET_D = prm("fan", "FAN_INLET_D", 28.0, "ESTIMATED",
                  "4020 blower inlet ring diameter, generic 40 mm blower frames (not in interfaces.py); measure (M7)")
FAN_NOZZLE_DEPTH = prm("fan", "FAN_NOZZLE_DEPTH", 4.0, "ESTIMATED",
                       "outlet nozzle height above the outlet plane = duct socket depth (duct_interface.json "
                       "fan_mounting: 'slides over the fan outlet nozzle (4 mm deep ...)'); real shape M7")
FAN_HOLE_D = prm("fan", "FAN_HOLE_D", 3.4, "ESTIMATED",
                 "fan corner holes modelled as Ø3.4 through-holes (interfaces BlowerSpec.hole_d, untagged there); the "
                 "stock M3x18 grip suggests tapping holes instead (review R-03) - M7")
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
    duct_air: object = None                         # internal air path of the real duct (checks only)
    duct_tabs: list = field(default_factory=list)   # duct_generator tab records (xyz, pad, arm_from_x, face_y)
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
        "intake": {"center": [0.0, y0, (z0 + z1) / 2], "normal": [0, -1, 0], "d": FAN_INLET_D},
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
    model_of = {"4020": "BLOWER_4020_STOCK", "5015": "BLOWER_5015_SUNON", "5015D": "BLOWER_5015_DELTA",
                "5015SS": "BLOWER_5015_SAMESKY", "5015SUNON": "BLOWER_5015_SUNON"}
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
            bosses.append({"pos": pos, "axis": ax, "screw": "M3", "kind": "insert", "status": b.get("status", ""),
                           "through_length": b.get("through_length")})
        fans.append({"id": fid, "model": model_of.get(str(f.get("type")), "BLOWER_4020_STOCK"), "envelope": env,
                     "intake": {"center": c, "normal": n, "d": FAN_INLET_D}, "screw_bosses": bosses,
                     "mass_g": f.get("mass_g"),
                     "outlet": {"centre": f.get("outlet_centre"), "size": f.get("outlet_size_mm"),
                                "blow": f.get("outlet_blow_dir")} if f.get("outlet_centre") else None})
    mounts = []
    for t in d.get("duct_attach_points", []):
        hc, mf = t["hole_centre"], t.get("mating_face", {})
        pos = [hc[0], mf.get("face_y", hc[1]), mf.get("face_z", hc[2])] if "face_y" in mf else \
              [hc[0], hc[1], mf.get("face_z", hc[2])]
        mounts.append({"id": t.get("id"), "pos": pos, "axis": t["screw_axis"], "screw": t.get("screw", "M3"),
                       "kind": "insert", "optional": "optional" in t.get("note", ""), "note": t.get("note", ""),
                       "hole_centre": hc, "tab_size": t.get("tab_size_mm")})
    return {"schema": d.get("schema"), "status": "FINAL" if d.get("final_mount_points") else
            f"PROVISIONAL {d.get('version', '')}", "fans": fans, "duct_mounts": mounts,
            "duct_param_set": d.get("duct_param_set"), "duct_materials": d.get("duct_materials", "PC")}


def fan_solid(env, outlet, bosses):
    """Blower solid (R-02): the envelope minus the band the duct socket occupies (FAN_NOZZLE_DEPTH above the
    outlet plane), plus the outlet nozzle (outlet rectangle from duct_interface.json, that depth), minus the
    corner holes (FAN_HOLE_D over through_length). Falls back to the envelope box (stub). Returns
    (solid, nozzle or None). Everything here is ESTIMATED until the 4020 is measured (M7)."""
    box = bx(*env)
    if not outlet or not outlet.get("centre") or [round(v, 6) for v in (outlet.get("blow") or [])] != [0, 0, -1]:
        return box, None
    (cx, cy, cz), (sx, sy) = outlet["centre"], outlet["size"]
    if abs(cz - env[4]) > 1e-6:
        return box, None
    zt = env[4] + FAN_NOZZLE_DEPTH
    nozzle = bx(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, env[4], zt)
    solid = bx(env[0], env[1], env[2], env[3], zt, env[5]) + nozzle
    for b in bosses:
        ax, L = b["axis"], b.get("through_length")
        if [round(v, 6) for v in ax] != [0, 1, 0] or not L:
            continue
        x, y, z = b["pos"]                       # rear face; the hole runs forward over the through-length
        solid = solid - cyl_y(x, z, y + 0.01, y - L - 0.01, FAN_HOLE_D)
    return solid, nozzle


def _from_dict(d: dict, is_stub: bool, source: str) -> CoolingInterface:
    d = _convert_ducts_schema(d)
    ci = CoolingInterface(is_stub=is_stub, source=source, status=d.get("status", "?"), raw=d)
    for f in d.get("fans", []):
        spec = getattr(I, f.get("model", ""), None)
        env = f.get("envelope")
        if env is None:
            raise KeyError(f"duct_interface fan {f.get('id')}: 'envelope' [xmin..zmax] required")
        solid, nozzle = fan_solid(env, f.get("outlet"), f.get("screw_bosses", []))
        mass = f.get("mass_g") or (float(spec.mass_g) if spec is not None else None)
        ci.fans.append({"id": f.get("id"), "model": f.get("model", "fan"), "solid": solid, "mass_g": mass,
                        "screw_bosses": f.get("screw_bosses", []), "envelope": env,
                        "intake": f.get("intake"), "outlet": f.get("outlet"), "nozzle": nozzle,
                        "notes": "STUB pose" if is_stub else f"pose from {source}"})
    ci.duct_mounts = d.get("duct_mounts", [])
    for m in ci.duct_mounts + [b for f in ci.fans for b in f["screw_bosses"]]:
        if "pos" not in m or "axis" not in m:
            raise KeyError(f"mount point without pos/axis: {m}")
    return ci


G_REAL = "cooling_real"
DUCT_TAB_SCREW_LEN = prm(G_REAL, "DUCT_TAB_SCREW_LEN", 6.0, "DESIGN",
                         "M3x6 ISO 7380: duct tab 2.5 (duct_interface tab_size) + 3.5 into the 4 mm frame insert")
# interfaces.py values the duct geometry or its position relative to the nozzle depends on (the duct
# generator reads them, or the frame/PCB chain the duct bolts to does). DERIVED ones are listed for
# completeness; the ESTIMATED ones drive the release status.
DUCT_INTERFACE_DEPS = [
    "SOCK", "HEATER_BODY", "HEATSINK", "HOT_ZONE_CLEARANCE", "DUCT_MIN_Z",            # nozzle end vs hot zone (M1)
    "PROBE_BODY_Y", "PROBE_ADAPTER_785004",                                          # probe keep-out (M8)
    "PCB", "PCB_HOLES", "MODULE_MOUNT_BEARING_Y", "PCB_COMPONENT_ZONE",               # frame chain -> fan rear plane / tabs (M10)
    "STOCK_4020_POS", "FAN3010",                                                     # fan XZ pose, 3010 intake window
    "LIDAR_RESERVED_OPTICAL", "LIDAR_RESERVED_BODY", "LIDAR_LINE_CENTER_XY_AT_Z3",   # LiDAR keep-outs (M6)
    "FRONT_LIMIT_Y", "RIGHT_LIMIT_X",
]


def _status_word(text: str, default: str = "ESTIMATED") -> str:
    w = (text or "").strip().split(" ")[0].upper()
    return w if w in ("VERIFIED", "DERIVED", "ESTIMATED", "MISSING", "STUB", "DESIGN") else default


def _register_duct_deps(d: dict) -> list[str]:
    """Register the duct body's own dependencies (values from duct_interface.json, statuses from the
    JSON / research M-items) and return the full dependency list for the release table."""
    def reg(name, value, status, source):
        PARAMS[name] = (G_REAL, Dim(value, status, source))
        return name
    names = []
    fans = d.get("fans") if isinstance(d.get("fans"), dict) else {}
    for fid, f in fans.items():
        st = _status_word(f.get("status", ""))
        names.append(reg(f"DUCT_FAN_{fid}_OUTLET_SIZE", tuple(f.get("outlet_size_mm", ())), st,
                         f"duct_interface.json fans.{fid}: {f.get('spec', f.get('type'))}; {f.get('status', '')} "
                         f"(missing-information M7); the duct fan socket fits over this outlet"))
        names.append(reg(f"DUCT_FAN_{fid}_SCREW_HOLES",
                         tuple(tuple(b["xyz"]) + (b.get("through_length"),) for b in f.get("screw_bosses", [])), st,
                         f"duct_interface.json fans.{fid}.screw_bosses (x, y, z, through_length): {f.get('status', '')} "
                         f"(M7); sets the frame fan standoffs and the fan front face"))
        e = f.get("envelope_box", {})
        names.append(reg(f"DUCT_FAN_{fid}_ENVELOPE", tuple(e.get(k) for k in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")),
                         "ESTIMATED", f"duct_interface.json fans.{fid}.envelope_box: XZ at the STOCK_4020_POS centre "
                         f"(DERIVED), rear face 3 mm in front of the frame plate (DESIGN), thickness = screw "
                         f"through-length (ESTIMATED, M7)"))
    if d.get("fan_mounting"):
        names.append(reg("DUCT_FAN_SOCKET_FIT", 1.0, "ESTIMATED", "duct_interface.json fan_mounting: socket 4 mm "
                         "deep, 1.0 mm clearance per side over the fan outlet nozzle (ESTIMATED; outlet M7)"))
    names.append(reg("DUCT_HOTEND_VERSION", 2023.0, "ESTIMATED",
                     "SOCK / HEATER_BODY / NOZZLE_* are the 2023 ceramic hotend; a 'Unicorn' hotend changes the "
                     "stack by 1.6 mm (missing-information M1) and moves the ports relative to the tip"))
    return ["DUCT_MOUNT_POINTS_FINAL", "FAN_NOZZLE_DEPTH", "FAN_HOLE_D"] + names + DUCT_INTERFACE_DEPS


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
    deps = _register_duct_deps(d)
    if bd is not None:
        if params is None:
            gp = getattr(mod, "get_params", None) or (lambda n: getattr(mod, "PARAM_SETS")[n]())
            params = gp(ci.raw.get("duct_param_set") or "S1")
        out = bd(params)
        mat = "PC" if "PC" in str(ci.raw.get("duct_materials", "PC")) else "PA-CF"
        body = out.get("body") if isinstance(out, dict) else None
        if body is None:
            raise KeyError("build_ducts() returned no 'body' part")
        ci.duct_air = out.get("air") if isinstance(out, dict) else None
        info = out.get("_info", {}) if isinstance(out, dict) else {}
        ci.duct_tabs = [dict(t, hole_centre=list(t["xyz"])) for t in info.get("tabs", [])]
        n_tabs = len(ci.duct_mounts)
        hw = [(f"M3x{DUCT_TAB_SCREW_LEN:.0f} ISO 7380 (duct tab to frame lug insert)", n_tabs,
               screw_mass_g(3, DUCT_TAB_SCREW_LEN))] if n_tabs else []
        parts.append(PartSpec("duct_body", body, "printed", mat, (0.95, 0.55, 0.10), deps=deps,
                              print_rot=(0.0, 0.0, 0.0), hardware=hw,
                              notes=f"owned by the Duct/CFD agent (cad/source/ducts, param set "
                                    f"{ci.raw.get('duct_param_set')}); status {ci.status}. "
                                    f"{ci.raw.get('duct_materials', 'PC')}. Print upright as modelled "
                                    f"(nozzle-frame +Z = print Z, fan socket up)."))
    else:
        from build123d import import_step
        for b in d.get("duct_bodies", []):
            s = import_step(str(DUCTS_DIR / b["step"]))
            parts.append(PartSpec(f"duct_{b['id']}", s, "printed", b.get("material", "PC"), (0.95, 0.55, 0.10),
                                  deps=deps, notes="owned by Duct/CFD agent (STEP)"))
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
