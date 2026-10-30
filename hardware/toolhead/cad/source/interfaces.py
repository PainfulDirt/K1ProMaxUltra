"""Shared interface definitions for the K1 Max toolhead project.

Single source of truth for every dimension that more than one part (or the CFD
model) depends on. CAD parts, the assembly, the clearance checks and the CFD
geometry all import from here; nothing else may hard-code these numbers.

Coordinate system (all parts, all agents):
    origin = nozzle tip, +X = printer right, +Y = toward printer rear,
    +Z = up, millimetres.

Every value carries a status:
    VERIFIED  - from the printer repo or a manufacturer/primary source
    DERIVED   - measured from community CAD / gerbers (see research/02)
    ESTIMATED - engineering estimate, must be confirmed before printing
    MISSING   - placeholder; the part that uses it is NOT print-ready
The `Dim` objects keep that status attached so validation can list every
unconfirmed number a printable part depends on.

Sources: documentation/research/01-repository-and-sensors.md (sensors),
02-mechanical-interfaces.md (hotend/PCB/extruder, table ids H*, P*, E*, L*),
03-fans-and-cooling.md (fans).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dim:
    value: float
    status: str  # VERIFIED | DERIVED | ESTIMATED | MISSING
    source: str = ""

    def __float__(self) -> float:
        return float(self.value)


@dataclass(frozen=True)
class Box:
    """Axis-aligned box in the nozzle frame."""
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float
    status: str
    source: str = ""

    @property
    def size(self):
        return (self.xmax - self.xmin, self.ymax - self.ymin, self.zmax - self.zmin)

    @property
    def center(self):
        return ((self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2,
                (self.zmin + self.zmax) / 2)


# --------------------------------------------------------------------------
# Hotend stack (stock K1 Max 2023-style ceramic hotend). research/02 §2.1
# --------------------------------------------------------------------------
NOZZLE_LENGTH = Dim(23.3, "DERIVED", "02:H3")
NOZZLE_MAX_D = Dim(6.9, "DERIVED", "02:H3")
NOZZLE_TIP_FLAT_D = Dim(1.0, "ESTIMATED", "typical 0.4 brass/hardened tip flat")
NOZZLE_CONE_TOP_Z = Dim(2.5, "ESTIMATED", "cone height of a typical Volcano-style tip")

HEATER_BODY = Box(-6.1, 6.1, -6.5, 6.5, 8.5, 29.1, "DERIVED", "02:H6")
SOCK = Box(-11.7, 11.8, -8.6, 8.3, 4.9, 30.3, "DERIVED", "02:H10")
SOCK_BOTTOM_HOLE_D = Dim(7.0, "DERIVED", "02:H10")
HEATSINK = Box(-13.9, 13.9, -10.8, 10.2, 31.9, 56.0, "DERIVED", "02:H12")

# Heatsink front fixing holes, shared by the 3010 hotend fan and the PCB.
# Blind, along +Y from the heatsink front face (Y -10.8) to Y +2.0.
HEATSINK_FRONT_HOLES = [(-12.0, 34.3), (12.0, 34.3)]  # (x, z) DERIVED 02:H13
HEATSINK_FRONT_HOLE_D = Dim(3.0, "DERIVED", "02:H13 (thread form MISSING: tapped M3? thread-forming?)")
HEATSINK_FRONT_HOLE_DEPTH = Dim(12.8, "DERIVED", "02:H13")

# 3010 hotend fan + PCB share a 24 mm square pattern centred at X 0, Z 46.3.
FAN3010_PATTERN = Dim(24.0, "DERIVED", "02:P3/F2")
FAN3010_PATTERN_CZ = Dim(46.3, "DERIVED", "02:F2 (holes Z 34.3 / 58.3)")
FAN3010 = Box(-15.0, 15.0, -22.1, -11.7, 31.3, 61.3, "DERIVED", "02:F2 (kemsky placement, stock-like: shares heatsink screws)")
UPPER_PATTERN_HOLES_TARGET = Dim(0.0, "MISSING", "what the Z 58.3 screws thread into (carriage? bracket?) - user measurement M2")

PCB = Box(-22.05, 22.05, -25.4, -24.2, 24.5, 71.4, "DERIVED", "02:P2/P4, two sources agree")
PCB_HOLES = [(-12.0, 34.3), (-12.0, 58.3), (12.0, 58.3)]  # (x, z) DERIVED 02:P3
# Cooling-module / cover mount (DD-01): the three PCB holes, with longer
# screws of the stock thread. Lower-left goes PCB -> 3010 -> heatsink hole;
# the upper two go into whatever the stock upper screws thread into (MISSING,
# M2). Bosses bear on the PCB front face around each hole: pad keep-out
# diameter ESTIMATED until PCB photos (M10) show the copper/components there.
MODULE_MOUNT_HOLES = PCB_HOLES
MODULE_MOUNT_SCREW = Dim(3.0, "ESTIMATED", "M3 assumed (holes Ø3.4 clearance); thread MISSING (M2)")
MODULE_MOUNT_BEARING_Y = Dim(-25.4, "DERIVED", "PCB front face, 02:P4")
MODULE_MOUNT_PAD_D = Dim(6.5, "ESTIMATED", "boss contact diameter on the PCB (M10)")
# Connectors and components on the PCB front face. Real heights MISSING (M10).
PCB_COMPONENT_ZONE = Box(-22.05, 22.05, -33.0, -25.4, 24.5, 71.4, "ESTIMATED", "8 mm allowance for connectors + plugs, M10")

EXTRUDER = Box(-20.4, 21.0, -5.4, 35.9, 60.6, 108.1, "DERIVED", "02:E10")

# --------------------------------------------------------------------------
# Sensors. research/01 and 02 §2.4
# --------------------------------------------------------------------------
# MicroProbe V2 - position is calibrated into the firmware; keep it unchanged
# (design decision DD-03).
PROBE_X = Dim(0.0, "VERIFIED", "tuning.cfg [probe] x_offset")
PROBE_Y = Dim(20.3, "VERIFIED", "tuning.cfg [probe] y_offset")
PROBE_MOUNT_FACE_Z = Dim(26.75, "ESTIMATED", "01: from z_offset 0.831 and 28.10 flange-to-extended-tip")
PROBE_HOLE_SPACING = Dim(17.0, "VERIFIED", "BIQU MicroProbe V2 dimension drawing (01 §B)")
PROBE_HOLE_D = Dim(2.7, "VERIFIED", "BIQU MicroProbe V2 dimension drawing")
PROBE_FLANGE = (Dim(21.93, "VERIFIED", "BIQU drawing"), Dim(15.60, "VERIFIED", "BIQU drawing"))
PROBE_FLANGE_TO_BACK = Dim(6.80, "VERIFIED", "BIQU drawing: hole line to body back face")
PROBE_FLANGE_TO_TIP_EXTENDED = Dim(28.10, "VERIFIED", "BIQU drawing")
PROBE_MAX_AMBIENT_C = Dim(60.0, "VERIFIED", "BIQU manual")
# Current mount (Printables 785004, public domain; user to confirm) - 01 §H.1
PROBE_ADAPTER_785004 = Box(-17.0, 17.1, 13.4, 29.1, 26.75, 59.25, "ESTIMATED",
                           "785004 STL placed by the probe offset; pin-to-hole offset ±2 mm (M8)")
PROBE_ADAPTER_SCREWS = [(-12.05, 20.1), (12.05, 20.1)]  # (x, y), vertical, ~M2, ESTIMATED 01 §H.1
PROBE_BODY_Y = (Dim(12.5, "ESTIMATED", "01 §H.1"), Dim(28.1, "ESTIMATED", "01 §H.1"))
PROBE_STOWED_TIP_Z = Dim(1.45, "ESTIMATED", "01 §H.1: today's stowed pin tip is below DUCT_MIN_Z")

# LiDAR - optical geometry is calibrated; keep the module pose unchanged
# (design decision DD-02). Only the line and sheet are known; the module
# body is not, so a conservative reserved zone is used until measured (M6).
LIDAR_LINE_CENTER_XY_AT_Z3 = (Dim(-36.01, "VERIFIED", "variables.cfg lidar_x_offset"),
                              Dim(-21.34, "VERIFIED", "variables.cfg lidar_y_offset"))
LIDAR_LINE_LENGTH = Dim(29.2, "VERIFIED", "LIDAR-NOTES: profile x -14.4..+14.8")
LIDAR_Y_PER_Z = Dim(-0.986, "VERIFIED", "variables.cfg lidar_y_per_z")
LIDAR_X_PER_Z = Dim(0.0354, "VERIFIED", "variables.cfg lidar_x_per_z")
LIDAR_SCAN_NOZZLE_Z = (3.0, 5.0)  # VERIFIED working window (LIDAR-NOTES)
LIDAR_LINE_X = (-50.8, -21.6)  # DERIVED 02:L3
# The laser sheet comes DOWN toward -Y: emitter is on the +Y (nozzle) side
# of the line. Sheet Y at height z (nozzle frame), with the bed at z = -Zs:
#   y_sheet(z) = y_line + (z + Zs) * |dY/dZ|      (rises toward +Y)
# (research/02 §3.7 originally had the direction reversed - corrected.)
# Reserved space = union of an optical box (laser sheet + camera view, below the
# module) and a body box (module + bracket). research/01 §H: body footprint
# 46.6 (X) x 19.4 (Y), height ~25-28, distance origin ~22.6 above the tip; a body
# centred on the line spans X -59.3..-12.7. Replace both once measured (M6).
LIDAR_RESERVED_OPTICAL = Box(-62.0, -18.0, -36.0, 10.0, -1.0, 22.0, "ESTIMATED",
                             "laser sheet + camera cone below the module (M6)")
LIDAR_RESERVED_BODY = Box(-62.0, -12.0, -36.0, 10.0, 18.0, 50.0, "ESTIMATED",
                          "module body 46.6 x 19.4 x 25-28 + bracket, research/01 §H (M6)")
LIDAR_RESERVED_BOXES = (LIDAR_RESERVED_OPTICAL, LIDAR_RESERVED_BODY)
# Backward-compatible bounding box of both (conservative).
LIDAR_RESERVED = Box(-62.0, -12.0, -36.0, 10.0, -1.0, 50.0, "ESTIMATED",
                     "bounding box of LIDAR_RESERVED_BOXES; prefer the boxes for checks")
LIDAR_BODY_FOOTPRINT = (Dim(46.6, "DERIVED", "01 §H.2 community lid (Printables 1476318)"),
                        Dim(19.4, "DERIVED", "01 §H.2"))
LIDAR_DISTANCE_ORIGIN_Z = Dim(22.6, "MEASURED-BY-USER", "variables.cfg lidar_zero_log, 01 §H")


def lidar_sheet_y(z: float, scan_nozzle_z: float = 3.0) -> float:
    """Y of the laser sheet at height z (nozzle frame) while scanning at nozzle Z=scan_nozzle_z."""
    y0 = float(LIDAR_LINE_CENTER_XY_AT_Z3[1]) + (scan_nozzle_z - 3.0) * float(LIDAR_Y_PER_Z)
    return y0 + (z + scan_nozzle_z) * abs(float(LIDAR_Y_PER_Z))


# --------------------------------------------------------------------------
# Fans. research/03
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class BlowerSpec:
    name: str
    frame: tuple            # (w, h, t) mm, outlet on the h-edge
    outlet: tuple           # (width along t, height along w) mm
    mass_g: Dim
    pq_csv: str             # relative to hardware/toolhead/components/fans/pq-curves
    hole_d: float = 3.4
    notes: str = ""


BLOWER_4020_STOCK = BlowerSpec(
    "Creality K1 stock 4020 blower (24 V 0.3 A, 4-wire PWM)", (40.0, 40.0, 20.0),
    (17.0, 13.0), Dim(18.0, "ESTIMATED", "no published mass; generic 4020 blowers 15-20 g"),
    "creality_K1_stock_4020_blower.csv",
    notes="outlet size ESTIMATED from generic 4020 blowers (M7); P-Q curve ESTIMATED")
BLOWER_5015_SUNON = BlowerSpec(
    "Sunon MF50152VX-1L02C-A99 (24 V, 2-wire)", (51.0, 51.0, 15.0),
    (12.5, 19.5), Dim(28.4, "VERIFIED", "secondary source, research/03"),
    "sunon_MF50152VX-1L02C-A99.csv",
    notes="outlet ESTIMATED from generic 5015 frames; P-Q ESTIMATED")

# --------------------------------------------------------------------------
# Global keep-outs and limits
# --------------------------------------------------------------------------
DUCT_MIN_Z = Dim(2.0, "ESTIMATED", "nozzle wipe drags 0.15 mm into PEI; 2 mm leaves margin for glass flex and blobs")
PROBE_RETRACTED_MIN_Z = Dim(2.0, "ESTIMATED", "retracted pin must clear prints - check with user M8")
# Rearmost allowed point below Z 30 so the rear keep-out zones do not grow.
REAR_LIMIT_Y = Dim(31.0, "ESTIMATED", "785004 adapter rear ~+29.1 ±2 (01 §H.1); exact M8")
# Front/side envelope the toolhead may occupy without losing travel - MISSING (M9).
FRONT_LIMIT_Y = Dim(-60.0, "MISSING", "front clearance at Y min travel (M9)")
RIGHT_LIMIT_X = Dim(45.0, "MISSING", "right clearance at X max travel (M9)")
HOT_ZONE_CLEARANCE = Dim(3.0, "ESTIMATED", "min air gap from sock/heater to any printed part")

# Printed part proxy used by CFD (current layer being printed at 0.2 mm).
LAYER_HEIGHT = 0.2
PART_PROXY = Box(-10.0, 10.0, -10.0, 10.0, -20.2, -0.2, "ESTIMATED", "20 mm cube under the nozzle, CFD only")
BED_Z = -20.2

# Materials (design decision DD-07)
MATERIAL_HOT = "PC or PA-CF (parts within 15 mm of the heater)"
MATERIAL_DEFAULT = "ASA (or ABS)"


FILAMENT_PATH_GEAR_TO_TIP = Dim(65.4, "VERIFIED", "pellcorp docs, 01 §H.3")


def unconfirmed(*objs) -> list[str]:
    """List the non-VERIFIED/DERIVED Dims or Boxes among objs (for validation reports)."""
    out = []
    for o in objs:
        st = getattr(o, "status", None)
        if st in ("ESTIMATED", "MISSING"):
            out.append(f"{st}: {getattr(o, 'value', o)} ({o.source})")
    return out


def all_unconfirmed() -> list[tuple[str, str, str]]:
    """Every ESTIMATED/MISSING module-level value: (name, status, source)."""
    rows = []
    for name, val in globals().items():
        if isinstance(val, (Dim, Box)) and val.status in ("ESTIMATED", "MISSING"):
            rows.append((name, val.status, val.source))
    return rows


if __name__ == "__main__":
    for r in all_unconfirmed():
        print("%-28s %-9s %s" % r)
