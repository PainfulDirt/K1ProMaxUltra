"""Shared helpers for the structure parts: parameter registry, materials,
hardware (screws / heat-set inserts), geometry shortcuts and the PartSpec
record that assembly / validate / export consume.

Status vocabulary (extends interfaces.py):
    VERIFIED / DERIVED / ESTIMATED / MISSING  - as in interfaces.py
    DESIGN  - a free design choice made here (justified in `source`)
    STUB    - placeholder for something another agent owns (duct interface)
Release rule (validate.py):
    any MISSING or STUB dependency  -> NOT RELEASED
    else any ESTIMATED dependency   -> FIT-CHECK FIRST
    else                            -> RELEASED
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import _SRC  # noqa: F401  (puts cad/source on sys.path)
import interfaces as I
from interfaces import Dim

from build123d import (Axis, Box, Cylinder, Location, Pos, Rot, Solid, Compound,
                       Part)

# --------------------------------------------------------------------------
# Parameter registry: every number a part uses that is not in interfaces.py
# --------------------------------------------------------------------------
PARAMS: dict[str, tuple[str, Dim]] = {}   # name -> (group, Dim)


def prm(group: str, name: str, value: float, status: str, source: str) -> float:
    """Register a named parameter and return its float value."""
    PARAMS[name] = (group, Dim(value, status, source))
    return float(value)


def group_params(group: str) -> dict[str, Dim]:
    return {n: d for n, (g, d) in PARAMS.items() if g == group}


def resolve_dep(name: str):
    """Return (status, value, source) for an interfaces.py name or a registered param."""
    if name in PARAMS:
        d = PARAMS[name][1]
        return d.status, d.value, d.source
    obj = getattr(I, name, None)
    if obj is None:
        return "UNKNOWN", None, "not found"
    st = getattr(obj, "status", "DERIVED-LIST")   # plain lists (PCB_HOLES...) are DERIVED in interfaces.py
    if isinstance(obj, (tuple, list)) and any(hasattr(o, "status") for o in obj):
        rank = ["MISSING", "ESTIMATED", "MEASURED-BY-USER", "DERIVED", "VERIFIED"]   # tuple of Dims: worst one
        sts = [o.status for o in obj if hasattr(o, "status")]
        st = min(sts, key=lambda x: rank.index(x) if x in rank else 0)
        val = tuple(getattr(o, "value", o) for o in obj)
        return st, val, "; ".join(sorted({getattr(o, "source", "") for o in obj if hasattr(o, "source")}))
    val = getattr(obj, "value", None)
    if val is None and hasattr(obj, "xmin"):
        val = (obj.xmin, obj.xmax, obj.ymin, obj.ymax, obj.zmin, obj.zmax)
    if val is None:
        val = obj
    return st, val, getattr(obj, "source", "interfaces.py")


# --------------------------------------------------------------------------
# Materials (DD-07). Densities: values specified by the tech lead, typical of
# filament TDS sheets -> ESTIMATED until the chosen spool's TDS is used.
# E and CTE are typical printed-part values (ESTIMATED) for the hand
# stiffness / drift estimates only.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Material:
    name: str
    density: Dim          # g/cm3
    E_mpa: Dim            # printed, in-plane
    cte: Dim              # 1/K
    colour: tuple


ASA = Material("ASA", Dim(1.07, "ESTIMATED", "lead-specified; typical ASA TDS 1.05-1.10"),
               Dim(1900, "ESTIMATED", "typical ASA TDS 1.8-2.0 GPa, printed XY"),
               Dim(95e-6, "ESTIMATED", "typical ASA 90-100e-6/K"), (0.20, 0.22, 0.25))
PC = Material("PC", Dim(1.20, "ESTIMATED", "lead-specified; typical PC TDS 1.19-1.20"),
              Dim(2200, "ESTIMATED", "typical PC 2.0-2.4 GPa"),
              Dim(68e-6, "ESTIMATED", "typical PC 65-70e-6/K"), (0.85, 0.85, 0.80))
PA_CF = Material("PA-CF", Dim(1.15, "ESTIMATED", "lead-specified ~1.15; PA12-CF TDS 1.06-1.20"),
                 Dim(5000, "ESTIMATED", "printed PA-CF XY 4-8 GPa, Z far lower"),
                 Dim(40e-6, "ESTIMATED", "printed PA-CF XY 25-60e-6/K"), (0.10, 0.10, 0.10))
MATERIALS = {m.name: m for m in (ASA, PC, PA_CF)}

E_STEEL = 200000.0       # MPa, textbook
E_ALU = 69000.0          # MPa, textbook
CTE_ALU = 23e-6          # 1/K, textbook

# --------------------------------------------------------------------------
# Hardware. Clearance holes: ISO 273 "medium" (VERIFIED by standard).
# Heat-set inserts: short brass inserts (CNC-Kitchen / ruthex class); hole
# sizes are the vendors' typical recommendations -> ESTIMATED, check the
# datasheet of the inserts actually bought and adjust here. The fit-check
# coupon prints every insert hole size used.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class InsertSpec:
    thread: str
    hole_d: float
    length: float
    min_wall: float

    @property
    def boss_d(self) -> float:
        return self.hole_d + 2 * self.min_wall


INSERTS = {
    "M2":   InsertSpec("M2", prm("hw", "INSERT_M2_HOLE_D", 3.2, "ESTIMATED", "typical M2 short insert hole"), 3.0, 1.5),
    "M2.5": InsertSpec("M2.5", prm("hw", "INSERT_M25_HOLE_D", 3.6, "ESTIMATED", "typical M2.5 short insert hole"), 4.0, 1.6),
    "M3":   InsertSpec("M3", prm("hw", "INSERT_M3_HOLE_D", 4.0, "ESTIMATED", "typical M3 short insert hole (OD 4.6-5.0)"), 4.0,
                       (prm("hw", "INSERT_M3_BOSS_D", 8.5, "DESIGN",
                            "R-20: >= 1.75 mm of plastic around a 5.0 mm (max) insert knurl") - 4.0) / 2),
}
INSERT_M3_KNURL_OD_MAX = prm("hw", "INSERT_M3_KNURL_OD_MAX", 5.0, "ESTIMATED",
                             "upper end of typical M3 short insert OD 4.6-5.0 (same source as INSERT_M3_HOLE_D)")
INSERT_FLOOR = prm("hw", "INSERT_FLOOR", 0.8, "DESIGN",
                   "R-03: every insert hole is blind with >= 0.8 mm (2 lines) of floor, so an over-long screw stops "
                   "on the floor instead of entering what lies behind (the PCB component zone for the fan screws)")
TIP_MARGIN_MIN = prm("hw", "SCREW_TIP_MARGIN_MIN", 0.5, "DESIGN",
                     "screw tip to hole floor: ISO 4759-1 grade A length tolerance js15 (+-0.24 for L 3-6, +-0.42 for L 18-30) + melt")
THREAD_ENGAGE_MIN = prm("hw", "THREAD_ENGAGE_MIN", 2.5, "DESIGN", "M3 into a brass insert: >= 5 threads (pitch 0.5)")
INSERT_DEPTH_EXTRA = prm("hw", "INSERT_DEPTH_EXTRA", 1.0, "DESIGN", "melt/screw-tip relief below insert")
CLEAR = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4}            # ISO 273 medium
BUTTON_HEAD = {"M3": (5.7, 1.65), "M2.5": (4.7, 1.5)}   # ISO 7380 dk, k
SHCS_HEAD = {"M3": (5.5, 3.0), "M2.5": (4.5, 2.5)}      # ISO 4762 dk, k


def screw_mass_g(d: float, length: float) -> float:
    """Steel cap screw mass: core cylinder + head (ESTIMATED, +-20 %)."""
    head = 0.5 if d >= 3 else 0.3
    return 7.85e-3 * math.pi / 4 * (0.85 * d) ** 2 * length + head


INSERT_MASS_G = {"M2": 0.12, "M2.5": 0.18, "M3": 0.25}   # ESTIMATED brass short inserts

# Shared between frame.py and the cooling stub. ducts/duct_generator.py repeats the same plate front
# (FRAME_FRONT_Y = PCB_COMPONENT_ZONE.ymin - 2.0) to put the fan's rear face 3 mm in front of it: keep
# FRAME_PLATE_T and that line in step (a fan face behind the plate front is a "NOT BUILT" FAIL in validate.py).
FRAME_PLATE_T = prm("frame", "FRAME_PLATE_T", 2.0, "DESIGN",
                    "5 lines; front bay depth is the binding constraint (component zone -31.5 .. FRONT_LIMIT -55)")
FRAME_BACK_Y = float(I.PCB_COMPONENT_ZONE.ymin)
FRAME_FRONT_Y = FRAME_BACK_Y - FRAME_PLATE_T

# --------------------------------------------------------------------------
# Geometry helpers (all in the nozzle frame)
# --------------------------------------------------------------------------


def bx(xmin, xmax, ymin, ymax, zmin, zmax) -> Part:
    return Pos((xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2) * Box(
        xmax - xmin, ymax - ymin, zmax - zmin)


def ibox(b: "I.Box", pad: float = 0.0) -> Part:
    return bx(b.xmin - pad, b.xmax + pad, b.ymin - pad, b.ymax + pad, b.zmin - pad, b.zmax + pad)


def cyl_y(x, z, y0, y1, d) -> Part:
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, (lo + hi) / 2, z) * Rot(90, 0, 0) * Cylinder(d / 2, hi - lo)


def cyl_z(x, y, z0, z1, d) -> Part:
    lo, hi = min(z0, z1), max(z0, z1)
    return Pos(x, y, (lo + hi) / 2) * Cylinder(d / 2, hi - lo)


def cyl_x(y, z, x0, x1, d) -> Part:
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos((lo + hi) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, hi - lo)


def as_solid(shape) -> Solid:
    """Return a single Solid (fuse if needed); raise if the result is not one solid."""
    sols = shape.solids()
    if len(sols) != 1:
        fused = sols[0]
        for s in sols[1:]:
            fused = fused.fuse(s)
        sols = fused.solids()
        if len(sols) != 1:
            raise ValueError(f"part is {len(sols)} disconnected solids")
    return sols[0]


# --------------------------------------------------------------------------
# Part record
# --------------------------------------------------------------------------
@dataclass
class PartSpec:
    name: str
    shape: object                       # build123d Solid/Part in the nozzle frame
    category: str                       # printed | fitcheck | stub | reference | keepout
    material: str | None = None         # key of MATERIALS for printed parts
    colour: tuple = (0.6, 0.6, 0.6)
    deps: list = field(default_factory=list)     # names (interfaces.* or PARAMS)
    print_rot: tuple = (0.0, 0.0, 0.0)  # XYZ Euler (deg) applied before dropping to the bed
    notes: str = ""
    mass_override_g: float | None = None   # purchased/reference parts with a known mass
    in_assembly: bool = True
    hardware: list = field(default_factory=list)  # (description, qty, mass_g_each)

    def printed(self) -> bool:
        return self.category in ("printed", "fitcheck")

    def print_oriented(self):
        """Solid rotated to its print orientation, centred in XY, resting on Z = 0."""
        s = self.shape
        rx, ry, rz = self.print_rot
        s = Rot(rx, ry, rz) * s
        bb = s.bounding_box()
        return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * s


def release_status(dep_rows, role: str = "") -> str:
    sts = {r[1] for r in dep_rows}
    if role == "fitcheck":
        return "PRINT FIRST (fit-check coupon; it exists to confirm the ESTIMATED values)"
    if "MISSING" in sts or "STUB" in sts or "UNKNOWN" in sts:
        return "NOT RELEASED"
    if "ESTIMATED" in sts:
        return "FIT-CHECK FIRST"
    return "RELEASED"
