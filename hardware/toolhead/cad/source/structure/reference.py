"""Reference (non-printed) models of the stock toolhead, the probe and the
LiDAR keep-outs, in the nozzle frame. Simple envelopes built only from
interfaces.py plus the named parameters below (each with status + source).

Note: LIDAR_RESERVED and the laser sheet are *keep-out volumes* (category
"keepout"); the validator checks printed parts against them, it never treats
them as solids that collide with stock parts.
"""
from __future__ import annotations

from build123d import (Cone, Plane, Polyline, Pos, Rot, extrude, make_face, Cylinder)

from .common import PartSpec, bx, ibox, cyl_x, cyl_y, cyl_z, prm
import interfaces as I

G = "reference"

# ---- parameters not (yet) in interfaces.py ---------------------------------
# PCB fan cutout: K1C gerber Gerber_BoardOutlineLayer.GKO, internal contour =
# circle R 13.70 centred on the 24 mm hole pattern, clipped by two flats 24 mm
# apart (flats through the hole-centre lines, along Z). Mapped to the nozzle
# frame with the same hole correspondence as research/02 P3/P4.
PCB_CUTOUT_R = prm(G, "PCB_FAN_CUTOUT_R", 13.70, "DERIVED", "K1C gerber GKO inner arc (CAD agent, this report)")
PCB_CUTOUT_FLAT_X = prm(G, "PCB_FAN_CUTOUT_FLAT_X", 12.0, "DERIVED", "K1C gerber GKO flats at +-12 from pattern centre")
PCB_HOLE_D = prm(G, "PCB_HOLE_D", 3.4, "DERIVED", "02:P3 / K1C gerber NPTH 3.400")
# Henlor's toolhead-PCB has a second 1.2 mm plate in front of the board (02:N8, "meaning unclear"):
# probably the component/connector tops. It has Ø6.2 access holes at the 3 screw positions only.
PCB_PLATE2_Y0 = prm(G, "PCB_PLATE2_YMIN", -28.64, "DERIVED", "Henlor toolhead-PCB 2nd plate Y -28.64..-27.44 (02:N8)")
PCB_PLATE2_T = prm(G, "PCB_PLATE2_T", 1.2, "DERIVED", "Henlor toolhead-PCB 2nd plate")
PCB_PLATE2_HOLE_D = prm(G, "PCB_PLATE2_HOLE_D", 6.2, "DERIVED", "Henlor 2nd plate screw-access holes")
# Heatsink cross-hole and heat-break grub (research/02 H14/H15)
HS_XHOLE_Y = prm(G, "HS_XHOLE_Y", 2.0, "DERIVED", "02:H14")
HS_XHOLE_Z = prm(G, "HS_XHOLE_Z", 40.5, "DERIVED", "02:H14")
HS_XHOLE_D = prm(G, "HS_XHOLE_D", 4.0, "DERIVED", "02:H14 (function unknown: may be used by the carriage clamp - MISSING M3)")
HS_GRUB_Z = prm(G, "HS_GRUB_Z", 34.9, "DERIVED", "02:H15 M4 grub from the rear at X 0")
# MicroProbe V2 body (BIQU drawing p.5 + V1 STEP for the pin)
PROBE_PIN_OFFSET_V1 = prm(G, "PROBE_PIN_OFFSET_V1", 2.75, "ESTIMATED",
                          "BTT V1 mockup STEP: pin 2.75 off the hole line, away from the back face; interfaces.PROBE_BODY_Y "
                          "assumes 1.0 (mid-body). Not used for geometry; informs the M8 measurement")
PROBE_PIN_D = prm(G, "PROBE_PIN_D", 1.6, "DERIVED", "BTT V1 mockup STEP")
PROBE_FLANGE_T = prm(G, "PROBE_FLANGE_T", 2.10, "VERIFIED", "BIQU V2 drawing")
PROBE_BODY_BOTTOM = prm(G, "PROBE_BODY_BOTTOM", 23.98, "VERIFIED", "BIQU V2 drawing: flange top to body bottom")
PROBE_STOWED = prm(G, "PROBE_STOWED", 25.30, "VERIFIED", "BIQU V2 drawing: flange top to stowed pin tip")
PROBE_BODY_W = prm(G, "PROBE_BODY_W", 12.0, "ESTIMATED", "scaled from the BIQU side view (body width below the flange)")
# LiDAR laser sheet
SHEET_HALF_T = prm(G, "LIDAR_SHEET_HALF_T", 1.0, "ESTIMATED", "LIDAR-NOTES: ~1.8 mm ramp in Y -> +-1 mm slab")

# ---- derived probe placement (DD-03: pin axis at (PROBE_X, PROBE_Y)) --------
# Hole line parallel to X (the only orientation whose Y extent fits under
# REAR_LIMIT_Y), connector/back face toward +Y. The body Y span comes from
# interfaces.PROBE_BODY_Y (01 §H.1, which assumes the pin at mid-body, 1.0 mm in
# front of the hole line). The V1 STEP puts the pin 2.75 off the hole line
# (PROBE_PIN_OFFSET above): the +-1.75 mm difference is M8. It does not move the
# new mount relative to the toolhead, because the mount copies the 785004 bore
# position relative to the 785004 anchor screws (see probe_mount.py).
PROBE_BACK_Y = float(I.PROBE_BODY_Y[1])
PROBE_FRONT_Y = float(I.PROBE_BODY_Y[0])
PROBE_HOLE_LINE_Y = PROBE_BACK_Y - float(I.PROBE_FLANGE_TO_BACK)
PROBE_FLANGE_TOP_Z = float(I.PROBE_MOUNT_FACE_Z)
PROBE_HOLES = [(float(I.PROBE_X) - float(I.PROBE_HOLE_SPACING) / 2, PROBE_HOLE_LINE_Y),
               (float(I.PROBE_X) + float(I.PROBE_HOLE_SPACING) / 2, PROBE_HOLE_LINE_Y)]
assert abs((PROBE_BACK_Y - PROBE_FRONT_Y) - float(I.PROBE_FLANGE[1])) < 0.05, "PROBE_BODY_Y vs flange depth"


def lidar_sheet_solid():
    """Laser sheet as a slab between the lowest bed position (nozzle Z = scan max)
    and the top of LIDAR_RESERVED (module side), X widened by the x_per_z drift."""
    zb = -max(I.LIDAR_SCAN_NOZZLE_Z) - 0.5
    zt_y = I.LIDAR_RESERVED.ymax
    zt = (zt_y - I.lidar_sheet_y(0.0)) / abs(float(I.LIDAR_Y_PER_Z))
    pts = [(I.lidar_sheet_y(zb) - SHEET_HALF_T, zb), (I.lidar_sheet_y(zb) + SHEET_HALF_T, zb),
           (I.lidar_sheet_y(zt) + SHEET_HALF_T, zt), (I.lidar_sheet_y(zt) - SHEET_HALF_T, zt)]
    drift = abs(float(I.LIDAR_X_PER_Z)) * (zt - zb)
    x0, x1 = I.LIDAR_LINE_X[0] - drift, I.LIDAR_LINE_X[1] + drift
    face = make_face(Polyline(*[(x0, y, z) for y, z in pts], close=True))
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def probe_body():
    zt = PROBE_FLANGE_TOP_Z
    fw, fd = float(I.PROBE_FLANGE[0]), float(I.PROBE_FLANGE[1])
    flange = bx(-fw / 2, fw / 2, PROBE_FRONT_Y, PROBE_BACK_Y, zt - PROBE_FLANGE_T, zt)
    for x, y in PROBE_HOLES:
        flange = flange - cyl_z(x, y, zt - 5, zt + 1, float(I.PROBE_HOLE_D))
    body = bx(-PROBE_BODY_W / 2, PROBE_BODY_W / 2, PROBE_FRONT_Y, PROBE_BACK_Y,
              zt - PROBE_BODY_BOTTOM, zt - PROBE_FLANGE_T + 0.01)
    return flange + body


def probe_pin(extended: bool = True):
    zt = PROBE_FLANGE_TOP_Z
    tip = zt - (float(I.PROBE_FLANGE_TO_TIP_EXTENDED) if extended else PROBE_STOWED)
    return cyl_z(float(I.PROBE_X), float(I.PROBE_Y), tip, zt - PROBE_BODY_BOTTOM + 0.5, PROBE_PIN_D)


def pcb():
    p = ibox(I.PCB)
    cz = float(I.FAN3010_PATTERN_CZ)
    cut = cyl_y(0, cz, I.PCB.ymin - 1, I.PCB.ymax + 1, 2 * PCB_CUTOUT_R) & bx(
        -PCB_CUTOUT_FLAT_X, PCB_CUTOUT_FLAT_X, I.PCB.ymin - 1, I.PCB.ymax + 1, cz - 20, cz + 20)
    p = p - cut
    for x, z in I.PCB_HOLES:
        p = p - cyl_y(x, z, I.PCB.ymin - 1, I.PCB.ymax + 1, PCB_HOLE_D)
    return p


def pcb_plate2():
    p = bx(I.PCB.xmin, I.PCB.xmax, PCB_PLATE2_Y0, PCB_PLATE2_Y0 + PCB_PLATE2_T, I.PCB.zmin, I.PCB.zmax)
    for x, z in I.PCB_HOLES:
        p = p - cyl_y(x, z, PCB_PLATE2_Y0 - 1, PCB_PLATE2_Y0 + 2, PCB_PLATE2_HOLE_D)
    return p


def x_rod(i):
    y, z = I.X_RODS_YZ[i]
    return cyl_x(y, z, -70, 70, float(I.X_ROD_D))


def heatsink():
    h = ibox(I.HEATSINK)
    h = h - cyl_x(HS_XHOLE_Y, HS_XHOLE_Z, I.HEATSINK.xmin - 1, I.HEATSINK.xmax + 1, HS_XHOLE_D)
    for x, z in I.HEATSINK_FRONT_HOLES:
        h = h - cyl_y(x, z, I.HEATSINK.ymin - 0.01, I.HEATSINK.ymin + float(I.HEATSINK_FRONT_HOLE_DEPTH),
                      float(I.HEATSINK_FRONT_HOLE_D))
    return h


def nozzle():
    d0, d1 = float(I.NOZZLE_TIP_FLAT_D), float(I.NOZZLE_MAX_D)
    zc = float(I.NOZZLE_CONE_TOP_Z)
    cone = Pos(0, 0, zc / 2) * Cone(d0 / 2, d1 / 2, zc)
    return cone + cyl_z(0, 0, zc - 0.01, float(I.NOZZLE_LENGTH), d1)


def fan3010():
    f = ibox(I.FAN3010)
    for x in (-12.0, 12.0):
        for z in (float(I.FAN3010_PATTERN_CZ) - 12.0, float(I.FAN3010_PATTERN_CZ) + 12.0):
            f = f - cyl_y(x, z, I.FAN3010.ymin - 1, I.FAN3010.ymax + 1, 3.4)
    return f


def build_reference(cooling, use_stock_cache: bool = False) -> list[PartSpec]:
    """Reference parts. `cooling` supplies the blower envelope(s). With
    use_stock_cache the stock carriage/hotend/PCB/3010/extruder are Henlor's real
    solids (validation only, never exported); otherwise boxes from interfaces.py."""
    R = []
    add = lambda n, s, c, cat="reference", **kw: R.append(PartSpec(n, s, cat, None, c, **kw))
    add("ref_nozzle", nozzle(), (0.85, 0.65, 0.20), deps=["NOZZLE_LENGTH", "NOZZLE_MAX_D"])
    add("ref_heater", ibox(I.HEATER_BODY), (0.80, 0.30, 0.20), deps=["HEATER_BODY"])
    add("ref_sock", ibox(I.SOCK), (0.90, 0.45, 0.35), deps=["SOCK"])
    stock = {}
    if use_stock_cache:
        from .stock_cache import load_stock_solids
        stock = load_stock_solids()
    if stock:
        grey = (0.55, 0.55, 0.58)
        for k, sh in stock.items():
            add(f"stock_{k}", sh, grey, notes="Henlor 742370 (CC BY) solid from the local cache - validation only")
        for i in range(len(I.X_RODS_YZ)):            # rods are surface-only in Henlor's file
            if f"x_rod_{i + 1}" not in stock:
                add(f"ref_x_rod_{i + 1}", x_rod(i), (0.7, 0.7, 0.7), deps=["X_RODS_YZ", "X_ROD_D"])
    else:
        add("ref_heatsink", heatsink(), (0.75, 0.75, 0.78), deps=["HEATSINK"])
        add("ref_fan3010", fan3010(), (0.15, 0.15, 0.15), deps=["FAN3010"], mass_override_g=7.0)
        add("ref_pcb", pcb(), (0.10, 0.45, 0.20), deps=["PCB", "PCB_HOLES"])
        add("ref_pcb_plate2", pcb_plate2(), (0.10, 0.35, 0.15), deps=["PCB_PLATE2_YMIN"])
        add("ref_extruder_envelope", ibox(I.EXTRUDER), (0.35, 0.35, 0.40), deps=["EXTRUDER"])
        add("ref_extruder_top_cover", ibox(I.EXTRUDER_TOP_COVER) - ibox(I.EXTRUDER), (0.30, 0.30, 0.35),
            deps=["EXTRUDER_TOP_COVER"])
        for i, b in enumerate(I.BELT_RETAINERS):
            add(f"ref_belt_retainer_{i + 1}", ibox(b), (0.4, 0.4, 0.45), deps=["BELT_RETAINERS"])
        for i in range(len(I.X_RODS_YZ)):
            add(f"ref_x_rod_{i + 1}", x_rod(i), (0.7, 0.7, 0.7), deps=["X_RODS_YZ", "X_ROD_D"])
        add("envelope_xcarriage", ibox(I.XCARRIAGE), (0.5, 0.5, 0.5), cat="replaced", deps=["XCARRIAGE"],
            notes="envelope only (contains PCB/heatsink); real-solid checks need the Henlor cache")
    add("ref_microprobe_body", probe_body(), (0.10, 0.25, 0.70),
        deps=["PROBE_MOUNT_FACE_Z", "PROBE_FLANGE", "PROBE_FLANGE_TO_BACK", "PROBE_BODY_Y"], mass_override_g=6.0)
    add("ref_probe_pin_extended", probe_pin(True), (0.95, 0.95, 0.95), deps=["PROBE_FLANGE_TO_TIP_EXTENDED"])
    add("ref_probe_adapter_785004_REPLACED", ibox(I.PROBE_ADAPTER_785004), (0.6, 0.6, 0.9), cat="replaced",
        deps=["PROBE_ADAPTER_785004"], notes="today's mount (envelope); replaced by probe_mount, not in interference checks")
    for nm in ("STOCK_COVER", "STOCK_DUCT", "STOCK_4020_POS"):
        add("replaced_" + nm.lower(), ibox(getattr(I, nm)), (0.8, 0.8, 0.8), cat="replaced", deps=[nm])
    for i, fan in enumerate(cooling.fans):
        add(f"ref_blower_{i + 1}_{fan['model']}", fan["solid"], (0.05, 0.05, 0.05),
            cat="stub" if cooling.is_stub else "reference",
            mass_override_g=fan["mass_g"], notes=fan.get("notes", ""))
    add("keepout_pcb_component_zone", ibox(I.PCB_COMPONENT_ZONE), (0.9, 0.9, 0.2), cat="keepout",
        deps=["PCB_COMPONENT_ZONE"])
    for nm in ("LIDAR_RESERVED_OPTICAL", "LIDAR_RESERVED_BODY"):
        add("keepout_" + nm.lower(), ibox(getattr(I, nm)), (1.0, 0.1, 0.1), cat="keepout", deps=[nm])
    add("keepout_lidar_laser_sheet", lidar_sheet_solid(), (1.0, 0.0, 0.6), cat="keepout",
        deps=["LIDAR_LINE_CENTER_XY_AT_Z3", "LIDAR_Y_PER_Z"])
    return R
