"""Cooling-module frame (DD-01): bolts to the three PCB holes
(MODULE_MOUNT_HOLES) with longer screws of the stock thread; bosses bear on
the PCB front face and bridge PCB_COMPONENT_ZONE. It carries the part fan and
the duct body at the mount points published by the cooling interface (with
the default COOLING_SOURCE "auto-final" these are the Duct/CFD agent's FINAL
points from ducts/duct_interface.json: the 4020's two diagonal screws and the
duct tabs T_left / T_right), the cover screws and two cable tie-downs.

Layout (nozzle frame, looking from the front):
  - 2.0 mm plate (FRAME_PLATE_T) in the XZ plane directly in front of the component zone;
  - teardrop window in front of the 3010 / PCB fan cutout (hotend-fan intake);
  - perimeter ribs on the front face, open at Z 36..56 on both sides so the
    plenum between plate and blower is fed from the sides;
  - the plate stays out of LIDAR_RESERVED_BOXES (+0.5 mm margin);
  - fan screws: standoffs from the fan's rear face through the plate, M3 inserts;
  - duct tabs: lugs from the tab mating face (fan rear plane) back to the plate,
    below the plate's bottom edge, bridged sideways when beside the plate; the
    frame yields to the duct body wherever they meet (duct geometry has priority);
  - top shelf with 2 M3 inserts for the cover; tie-down blocks left/right.
Fasteners: brass heat-set inserts everywhere the frame takes a screw (fan,
duct, cover): repeated service cycles and a 45 C chamber rule out
self-tapping into ASA (thread wear, creep).
Print orientation: upside down (top shelf + top edge on the bed), plate
vertical; bosses print as horizontal cylinders.
"""
from __future__ import annotations

import math

from build123d import Polyline, make_face, extrude, Pos, Plane

from .common import (PartSpec, bx, cyl_y, cyl_z, prm, INSERTS, INSERT_DEPTH_EXTRA, CLEAR,
                     BUTTON_HEAD, screw_mass_g, INSERT_MASS_G, group_params, FRAME_PLATE_T, FRAME_BACK_Y,
                     FRAME_FRONT_Y)
from . import cooling as C
import interfaces as I

G = "frame"

# ---- parameters ------------------------------------------------------------
BACK_Y = FRAME_BACK_Y                     # plate back = front of PCB_COMPONENT_ZONE
T = FRAME_PLATE_T
FRONT_Y = FRAME_FRONT_Y
ZMIN = float(I.PCB.zmin)                  # plate bottom = PCB bottom edge
ZMAX = prm(G, "FRAME_ZMAX", 71.8, "DESIGN",
           "PCB top 71.4 + 0.4; stays under the carriage cable strain relief (Z +72.3, 02:N16)")
XMAX = prm(G, "FRAME_XMAX", 20.0, "DESIGN", "inside the PCB width (22.05) and RIGHT_LIMIT_X 24.2 with the cover")
LIDAR_MARGIN = prm(G, "FRAME_LIDAR_MARGIN", 0.5, "DESIGN", "gap to LIDAR_RESERVED_BOXES")
XMIN_TOP = -XMAX
LIDAR_BOXES = tuple(I.LIDAR_RESERVED_BOXES)
WIN_R = prm(G, "FRAME_WINDOW_R", 15.0, "DESIGN", "3010 intake: open area >= 25x25 after boss collars")
WIN_FLAT_Z = prm(G, "FRAME_WINDOW_FLAT_Z", 30.0, "DESIGN", "teardrop flat (bridge <= 10 mm when printed upside down)")
from . import reference as REF
PAD_D = min(float(I.MODULE_MOUNT_PAD_D), REF.PCB_PLATE2_HOLE_D - 0.4)   # passes the 2nd-plate Ø6.2 holes
BOSS_D = prm(G, "FRAME_BOSS_D", 7.5, "DESIGN", "boss in front of the PCB 2nd plate (Y < -28.9)")
NECK_Y = REF.PCB_PLATE2_Y0 - 0.3
COLLAR_D = prm(G, "FRAME_COLLAR_D", 8.0, "DESIGN", "ISO 7380 M3 head 5.7 + 1.15 per side, within the plate")
FOURTH_PAD = prm(G, "FRAME_FOURTH_PAD_ON", 1.0, "ESTIMATED",
                 "compression-only pad at the 4th pattern corner (12, 34.3), bearing on the PCB 2nd plate "
                 "(Henlor, meaning unclear) - useless if that plate is not a real part (M10)")
RIB_D = prm(G, "FRAME_RIB_DEPTH", 2.0, "DESIGN", "front ribs; leaves 1 mm to the fan back in the plenum")
RIB_W = prm(G, "FRAME_RIB_W", 2.0, "DESIGN", "5 lines")
SIDE_OPEN = (prm(G, "FRAME_SIDE_OPEN_Z0", 36.0, "DESIGN", "plenum side inlet, ribs interrupted"),
             prm(G, "FRAME_SIDE_OPEN_Z1", 56.0, "DESIGN", "plenum side inlet, ribs interrupted"))
SHELF_T = prm(G, "FRAME_SHELF_T", 3.0, "DESIGN", "cover-screw shelf")
SHELF_X = prm(G, "FRAME_SHELF_HALF_W", 14.0, "DESIGN", "shelf half-width")
COVER_SCREW_X = prm(G, "COVER_SCREW_X", 9.0, "DESIGN", "2 x M3 vertical cover screws at X +-9")
COVER_SCREW_Y = prm(G, "COVER_SCREW_Y", -44.0, "DESIGN", "in front of the plate, above the fan")
TIE_SLOT = (1.6, 3.0)        # tie band thickness x width allowance (2.5 mm ties)
TIE_BAR = prm(G, "FRAME_TIE_BAR", 2.0, "DESIGN", "plate-edge bar the cable ties wrap around (top corners)")
TIE_Z = prm(G, "FRAME_TIE_Z", 65.0, "DESIGN", "tie slots above the boss collars / fan standoffs, through the shelf rib")
STOCK_GRIP_ADD = abs(BACK_Y - float(I.MODULE_MOUNT_BEARING_Y))   # 9.2 (boss) ...
SCREW_EXTRA = STOCK_GRIP_ADD + T                                 # ... + plate = 11.2 mm longer than stock
# Stock: 2 x M3x18 BHCS upper (into carriage inserts), M3x20 BHCS lower (into the heatsink) - 02:N6/N7.
HEAD_CLEAR_D = BUTTON_HEAD["M3"][0] + 0.6     # ISO 7380 M3 head + driver clearance
LUG_COVER_GAP = prm(G, "FRAME_LUG_COVER_GAP", 1.0, "DESIGN", "side lugs stay this far below the plate bottom (cover edge)")
FAN_SCREW_LEN = prm(G, "FRAME_FAN_SCREW_LEN", 24.0, "DESIGN",
                    "fan screw = fan through-length 20 (ESTIMATED, M7) + insert 4; BOM 'M3 x (fan thickness + 4)'")
SCREW_LEN = prm(G, "FRAME_PCB_SCREW_LEN", 30.0, "DESIGN",
                "3 x M3x30 ISO 7380: upper tip 0.8 deeper than stock (stock 18+11.2=29.2; carriage hole depth "
                "behind the insert checked against the Henlor carriage); lower 7.3 mm in the heatsink (stock 8.5)")


def fourth_corner():
    """The corner of the 24 mm pattern that has no PCB hole (3010 lower-right screw)."""
    cz, h = float(I.FAN3010_PATTERN_CZ), float(I.FAN3010_PATTERN) / 2
    corners = {(sx * h, cz + sz * h) for sx in (-1, 1) for sz in (-1, 1)}
    left = [c for c in corners if all(abs(c[0] - x) + abs(c[1] - z) > 0.01 for x, z in I.MODULE_MOUNT_HOLES)]
    assert len(left) == 1
    return left[0]


def pcb_bosses(back_y=None, collar=True):
    """Screw bosses at the PCB holes (+ the compression pad at the 4th corner), from
    the PCB front face to the plate back face `back_y`; collars inside the plate."""
    back_y = BACK_Y if back_y is None else back_y
    y_pcb = float(I.MODULE_MOUNT_BEARING_Y)
    out = None
    for x, z in I.MODULE_MOUNT_HOLES:
        b = cyl_y(x, z, y_pcb, NECK_Y, PAD_D) + cyl_y(x, z, NECK_Y + 0.01, back_y - 0.5, BOSS_D)
        if collar:
            b += cyl_y(x, z, back_y, FRONT_Y, COLLAR_D)
        out = b if out is None else out + b
    if FOURTH_PAD:
        x4, z4 = fourth_corner()
        out += cyl_y(x4, z4, REF.PCB_PLATE2_Y0, back_y - 0.5, F_PAD4_D)
        if collar:
            out += cyl_y(x4, z4, back_y, FRONT_Y, COLLAR_D)
    return out


F_PAD4_D = float(I.MODULE_MOUNT_PAD_D)


def lidar_cut(y0=-80.0, y1=40.0):
    """Union of the LiDAR reserved boxes grown by LIDAR_MARGIN (clipped to y0..y1)."""
    cut = None
    for b in LIDAR_BOXES:
        m = LIDAR_MARGIN
        ya, yb = max(b.ymin - m, y0), min(b.ymax + m, y1)
        if ya >= yb:
            continue
        c = bx(b.xmin - m, b.xmax + m, ya, yb, b.zmin - m, b.zmax + m)
        cut = c if cut is None else cut + c
    return cut


def left_edge(z: float) -> float:
    """Leftmost plate X at height z (plate Y range lies inside the boxes' Y range)."""
    x = XMIN_TOP
    for b in LIDAR_BOXES:
        if b.ymin - LIDAR_MARGIN < BACK_Y and b.ymax + LIDAR_MARGIN > FRONT_Y and \
                b.zmin - LIDAR_MARGIN <= z <= b.zmax + LIDAR_MARGIN:
            x = max(x, b.xmax + LIDAR_MARGIN)
    return x


def plate_inside(x: float, z: float) -> bool:
    return ZMIN <= z <= ZMAX and left_edge(z) <= x <= XMAX


def lidar_allow_regions():
    """Intended intrusion into LIDAR_RESERVED_BODY: the screw column at a PCB hole
    that lies inside the box (the stock PCB, its screw and the 3010 already sit
    there, so the box overlaps stock hardware - interface conflict, M6)."""
    out = []
    for x, z in I.MODULE_MOUNT_HOLES:
        if not plate_inside(x, z) or not plate_inside(x - COLLAR_D / 2, z):
            out.append((cyl_y(x, z, float(I.MODULE_MOUNT_BEARING_Y) + 0.01, FRONT_Y - 0.01, COLLAR_D + 0.4),
                        f"PCB hole ({x}, {z}) screw column: mandatory, box overlaps the stock PCB/3010/heatsink"))
    return out


def window_face_solid():
    cz = float(I.FAN3010_PATTERN_CZ)
    c45 = WIN_R * math.cos(math.radians(45))
    zt = cz - c45
    xf = c45 - (zt - WIN_FLAT_Z)
    tri = make_face(Polyline((-c45, 0, zt), (c45, 0, zt), (xf, 0, WIN_FLAT_Z), (-xf, 0, WIN_FLAT_Z), close=True))
    tri_s = extrude(tri, amount=20, dir=(0, 1, 0), both=True)
    circ = cyl_y(0, cz, -20, 20, 2 * WIN_R)
    return Pos(0, (BACK_Y + FRONT_Y) / 2, 0) * (circ + tri_s)


def plate_outline_solid(y0, y1):
    s = bx(XMIN_TOP, XMAX, min(y0, y1), max(y0, y1), ZMIN, ZMAX)
    c = lidar_cut()
    return s - c if c is not None else s


def _mount(m):
    """Boss / lug for one cooling-interface mount point (heat-set insert, screw along +Y
    from the front). Returns (solid, hole, issue): solid/hole None + an issue string when
    the point cannot be built (the validator reports it as an interface conflict)."""
    ax = [round(v, 6) for v in m["axis"]]
    tag = m.get("id") or str([round(v, 2) for v in m["pos"]])
    if ax != [0, 1, 0]:
        kind = "optional - skipped" if m.get("optional") else "NOT BUILT"
        return None, None, f"{tag}: axis {ax} not supported by the frame (only +Y screws) - {kind}"
    ins = INSERTS[m.get("screw", "M3")]
    x, y, z = m["pos"]
    D = ins.boss_d
    r = D / 2
    if y > FRONT_Y + 1e-6:
        return None, None, f"{tag}: lies behind the frame front face (Y {y} > {FRONT_Y}) - NOT BUILT"
    for hx, hz in I.MODULE_MOUNT_HOLES:
        dd = ((x - hx) ** 2 + (z - hz) ** 2) ** 0.5
        if dd < r + HEAD_CLEAR_D / 2:
            return None, None, (f"{tag}: {dd:.2f} mm from the PCB screw ({hx}, {hz}); a boss here blocks that "
                                f"screw's install path (needs >= {r + HEAD_CLEAR_D / 2:.2f}) - NOT BUILT")
    if plate_inside(x, z):
        solid = cyl_y(x, z, y, BACK_Y, D)                           # standoff, through the plate
    elif z < ZMIN:                                                  # lug below the plate
        solid = cyl_y(x, z, y, BACK_Y, D) + bx(x - r, x + r, y, BACK_Y, z, ZMIN + RIB_W)
        x_in = min(max(x, left_edge(ZMIN) + r), XMAX - r)
        if abs(x_in - x) > 1e-6:                                    # bridge sideways to the plate,
            zt = min(ZMIN - LUG_COVER_GAP, z + r)                   # under the cover's bottom edge
            solid = cyl_y(x, z, y, BACK_Y, D) + bx(x - r, x + r, y, BACK_Y, z - r, zt) + \
                bx(min(x, x_in) - r, max(x, x_in) + r, y, BACK_Y, z - r, zt) + \
                bx(x_in - r, x_in + r, y, BACK_Y, z - r, ZMIN + RIB_W)
    else:
        return None, None, f"{tag}: beside the plate at (X {x}, Z {z}) where the plate is cut for LIDAR_RESERVED_BODY - NOT BUILT"
    cut = lidar_cut()
    if cut is not None and (solid & cut) is not None and (solid & cut).volume > 1e-3:
        return None, None, f"{tag}: its boss would enter LIDAR_RESERVED_BOXES - NOT BUILT"
    depth = ins.length + INSERT_DEPTH_EXTRA
    hole = cyl_y(x, z, y - 0.01, y + depth, ins.hole_d)
    return solid, hole, None


def build(cooling) -> PartSpec:
    cz = float(I.FAN3010_PATTERN_CZ)
    plate = plate_outline_solid(FRONT_Y, BACK_Y)
    plate = plate - window_face_solid()

    # front ribs: bottom, sides (interrupted at the plenum inlets)
    yr = FRONT_Y - RIB_D
    ribs = bx(XMIN_TOP, XMAX, yr, FRONT_Y + 0.01, ZMIN, ZMIN + RIB_W)
    for z0, z1 in ((ZMIN, SIDE_OPEN[0]), (SIDE_OPEN[1], ZMAX)):
        ribs += bx(XMAX - RIB_W, XMAX, yr, FRONT_Y + 0.01, z0, z1)
        # left rib follows the (LiDAR-stepped) left edge
        zs = sorted({z0, z1} | {v for b in LIDAR_BOXES for v in (b.zmin - LIDAR_MARGIN, b.zmax + LIDAR_MARGIN)
                                if z0 < v < z1})
        for za, zb_ in zip(zs[:-1], zs[1:]):
            xl = left_edge((za + zb_) / 2)
            ribs += bx(xl, xl + RIB_W, yr, FRONT_Y + 0.01, za, zb_)
    # horizontal rib under the shelf ties the top corners together
    ribs += bx(XMIN_TOP, XMAX, yr, FRONT_Y + 0.01, ZMAX - SHELF_T - RIB_W, ZMAX)
    cut = lidar_cut()
    part = plate + (ribs - cut if cut is not None else ribs)

    # PCB bosses (bear on the PCB front face, bridge the component zone)
    part += pcb_bosses()
    holes = [cyl_y(x, z, float(I.MODULE_MOUNT_BEARING_Y) + 1.0, FRONT_Y - 1.0, CLEAR["M3"])
             for x, z in I.MODULE_MOUNT_HOLES]
    # screw-head seats on the plate front face: clear the ribs around each ISO 7380 head
    holes += [cyl_y(x, z, FRONT_Y + 0.01, FRONT_Y - RIB_D - 1.0, HEAD_CLEAR_D)
              for x, z in I.MODULE_MOUNT_HOLES]

    # cover shelf + insert bosses (vertical, from the top)
    ys = COVER_SCREW_Y - INSERTS["M3"].boss_d / 2
    part += bx(-SHELF_X, SHELF_X, ys, FRONT_Y + 0.01, ZMAX - SHELF_T, ZMAX)
    zb = ZMAX - INSERTS["M3"].length - INSERT_DEPTH_EXTRA
    for sx in (-1, 1):
        part += cyl_z(sx * COVER_SCREW_X, COVER_SCREW_Y, zb, ZMAX, INSERTS["M3"].boss_d)
        holes.append(cyl_z(sx * COVER_SCREW_X, COVER_SCREW_Y, zb - 0.01, ZMAX + 0.01, INSERTS["M3"].hole_d))

    # cable tie-down slots through the plate at the top corners (left: probe lead to the
    # TOUCH port on the LiDAR side; right: part-fan lead). Ties wrap the plate-edge bar.
    for sx in (-1, 1):
        xe = XMAX if sx > 0 else XMIN_TOP
        xa = xe - sx * TIE_BAR
        holes.append(bx(min(xa, xa - sx * TIE_SLOT[0]), max(xa, xa - sx * TIE_SLOT[0]), FRONT_Y - RIB_D - 1,
                        BACK_Y + 1, TIE_Z, TIE_Z + TIE_SLOT[1]))

    # cooling-interface mounts (fan screw bosses + duct mount points)
    issues = []
    for m in [b for f in cooling.fans for b in f["screw_bosses"]] + list(cooling.duct_mounts):
        s_, h, issue = _mount(m)
        if issue:
            issues.append(issue)
            continue
        part += s_
        holes.append(h)
    for h in holes:
        part -= h
    # the duct body (Duct/CFD agent) has priority over frame ribs/lugs: the frame yields
    for dp in getattr(cooling, "duct_parts", []):
        if dp.category == "printed":
            part -= dp.shape
            if len(part.solids()) != 1:
                issues.append(f"frame split into {len(part.solids())} pieces after yielding to {dp.name} "
                              f"(a lug/bridge crosses the duct) - largest kept")
                part = max(part.solids(), key=lambda q: q.volume)

    n_ins = 2 + sum(len(f["screw_bosses"]) for f in cooling.fans) + len(cooling.duct_mounts) - len(issues)
    hw = [(f"M3x{SCREW_LEN:.0f} ISO 7380 (replace the stock M3x18 / M3x18 / M3x20 PCB screws; frame adds "
           f"{SCREW_EXTRA:.1f} mm)", 3, screw_mass_g(3, SCREW_LEN)),
          ("M3 brass heat-set insert (fan, duct, cover)", n_ins, INSERT_MASS_G["M3"]),
          ("M3x6 ISO 7380 (cover)", 2, screw_mass_g(3, 6))]
    for f in cooling.fans:     # fan screws: through the fan frame into the frame inserts
        n_fs = len(f["screw_bosses"])
        if n_fs:
            hw.append((f"M3x{FAN_SCREW_LEN:.0f} (fan frame through-length + insert; fan to frame)", n_fs,
                       screw_mass_g(3, FAN_SCREW_LEN)))
    deps = ["MODULE_MOUNT_HOLES", "MODULE_MOUNT_SCREW", "MODULE_MOUNT_PAD_D", "MODULE_MOUNT_BEARING_Y",
            "PCB_COMPONENT_ZONE", "PCB", "FAN3010_PATTERN_CZ", "UPPER_PATTERN_HOLES_TARGET",
            "HEATSINK_FRONT_HOLE_D", "LIDAR_RESERVED_OPTICAL", "LIDAR_RESERVED_BODY", "INSERT_M3_HOLE_D"] + list(group_params(G))
    deps += list(group_params(C.G)) if cooling.is_stub else (
        ["DUCT_MOUNT_POINTS_FINAL"] + [n for n in C.PARAMS if n.startswith("DUCT_FAN_") and
                                       (n.endswith("_SCREW_HOLES") or n.endswith("_ENVELOPE"))])
    spec = PartSpec("cooling_module_frame", part, "printed", "ASA", (0.25, 0.45, 0.80), deps=deps,
                    print_rot=(180, 0, 0), hardware=hw,
                    notes=_material_note(part) + " PCB screws M3x%.0f (stock + %.1f mm)." % (SCREW_LEN, SCREW_EXTRA))
    spec.issues = issues
    return spec


def _material_note(part) -> str:
    """DD-07 wording from the geometry. DD-07: PC/PA-CF for parts below the heatsink (Z < HEATSINK.zmin)
    within 15 mm of the sock; ASA at heatsink level, naming the frame's PCB bosses (~14 mm) as acceptable."""
    from .common import ibox
    sock = ibox(I.SOCK)
    zh = float(I.HEATSINK.zmin)
    d_all = part.distance_to(sock)
    cols = None
    for x, z in list(I.MODULE_MOUNT_HOLES) + ([fourth_corner()] if FOURTH_PAD else []):
        c = cyl_y(x, z, -60, 0, max(BOSS_D, F_PAD4_D, COLLAR_D) + 0.02)
        cols = c if cols is None else cols + c
    rest_low = (part - cols) & bx(-300, 300, -300, 300, -100, zh)
    d_low = rest_low.distance_to(sock) if rest_low is not None and rest_low.volume > 1e-6 else float("inf")
    boss_zmin = min(z for _, z in I.MODULE_MOUNT_HOLES) - max(BOSS_D, F_PAD4_D) / 2
    return (f"ASA (DD-07): nearest point {d_all:.1f} mm from the sock = the PCB boss columns at Z "
            f"{min(z for _, z in I.MODULE_MOUNT_HOLES):.1f} (heatsink level, which DD-07 names as acceptable in ASA; "
            f"their lower edge reaches Z {boss_zmin:.2f}, {zh - boss_zmin:.1f} mm below the heatsink bottom Z {zh}). "
            f"Everything else below the heatsink (plate edge, duct lugs) is {d_low:.1f} mm from the sock"
            + (" - inside DD-07's 15 mm: needs PC/PA-CF." if d_low < 15.0 else ", outside DD-07's 15 mm hot zone."))


def intake_area():
    """Open area of the frame window minus boss collars (mm2) at the plate mid-plane."""
    s = window_face_solid()
    for x, z in I.MODULE_MOUNT_HOLES:
        s = s - cyl_y(x, z, -50, 0, COLLAR_D)
    if FOURTH_PAD:
        x4, z4 = fourth_corner()
        s = s - cyl_y(x4, z4, -50, 0, COLLAR_D)
    clip = plate_outline_solid(FRONT_Y, BACK_Y)
    win = s & clip
    return win.volume / T
