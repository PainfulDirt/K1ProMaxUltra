"""Cover: light ASA shell over frame, fan and PCB.

- Held by 2 vertical M3x6 button-head screws through the top wall into the
  frame shelf inserts; the top wall's underside bears on the shelf top (the
  only intended frame contact). Remove the screws and slide the cover forward:
  the rear and bottom are open, so the LiDAR lead, probe lead and fan leads stay
  plugged and the duct stays bolted to the frame.
- Yields to the duct body and the frame's duct lugs: a side wall whose bottom
  edge would reach a duct tab or a frame lug is raised over its whole length to
  clear them by COVER_YIELD_CLEAR (whole length, so the cover still slides off
  forward). The duct geometry is owned by the Duct/CFD agent and never changes
  for the cover.
- Left wall is removed (full thickness) wherever it would enter
  LIDAR_RESERVED_BOXES (+0.5 mm): a partial cut would leave a 0.7 mm sliver.
- Front wall COVER_GAP in front of the fan's intake face.
- Part-fan intake: a fully open round aperture (FAN_INLET_D + 2 x
  COVER_INTAKE_MARGIN) centred on the 4020 intake, no grille: the front wall
  sits only COVER_GAP in front of the impeller eye, where a grille would
  throttle the blower (the CFD fan model has no cover).
- Vents: side and top slots over the plenum between frame and fan (3010
  intake path); open bottom and open rear-top (cable exit, in front of the
  carriage strain relief).
Print: front face down (no supports; all vents are vertical holes or slots).
"""
from __future__ import annotations

from build123d import Pos

from .common import PartSpec, bx, cyl_z, cyl_y, prm, CLEAR, group_params
from . import frame as F
from . import cooling as C
import interfaces as I

G = "cover"
WALL = prm(G, "COVER_WALL", 1.2, "DESIGN", "3 perimeters at 0.4 mm; ASA")
GAP = prm(G, "COVER_GAP", 0.5, "DESIGN",
          "front wall inner face to the fan intake face: print tolerance + fan thickness tolerance; brings the "
          "front as close to FRONT_LIMIT_Y as the fan allows (was 1.0)")
YIELD_CLEAR = prm(G, "COVER_YIELD_CLEAR", 0.3, "DESIGN", "min gap from the cover to the duct body and the frame's duct lugs")
ZMIN = prm(G, "COVER_ZMIN", 24.0, "DESIGN", "open bottom: below the PCB bottom edge (24.5), above the duct")
HALF_W = prm(G, "COVER_HALF_W", 24.0, "DERIVED",
             "stock cover width +-24.0 (02:C4); inside RIGHT_LIMIT_X 24.2 in the XY-joint band")
REAR_Y = prm(G, "COVER_SIDE_REAR_Y", float(I.XCARRIAGE.ymin) - 0.5, "DESIGN",
             "side walls end 0.5 in front of the carriage envelope (XCARRIAGE.ymin)")
STRAIN_RELIEF_YMIN = prm(G, "CARRIAGE_STRAIN_RELIEF_YMIN", -32.3, "DERIVED", "02:N16 cable strain relief Y -32.3..-23.8, Z 72.3..91.2")
TOP_REAR_Y = STRAIN_RELIEF_YMIN - 0.5     # top wall stops in front of the strain relief; open behind = cable exit
SLOT_W = prm(G, "COVER_SLOT_W", 2.0, "DESIGN", "plenum vent slot width (finger-safe, prints clean)")
INTAKE_MARGIN = prm(G, "COVER_INTAKE_MARGIN", 1.0, "DESIGN",
                    "fan intake aperture = FAN_INLET_D + 2 x 1.0, fully open (no grille ribs)")
SLOT_P = prm(G, "COVER_SLOT_PITCH", 4.0, "DESIGN", "vent pitch (2 mm bars)")


def _lidar_cut_full_wall(xi):
    """LiDAR keep-out cut for the cover: the boxes grown by the frame's margin; where a box only
    nibbles the left wall (would leave a sliver thinner than WALL) it removes the full wall."""
    cut = None
    for b in F.LIDAR_BOXES:
        m = F.LIDAR_MARGIN
        x1 = b.xmax + m
        if -xi - WALL < x1 < -xi + WALL:
            x1 = -xi + 0.01
        c = bx(b.xmin - m, x1, b.ymin - m, b.ymax + m, b.zmin - m, b.zmax + m)
        cut = c if cut is None else cut + c
    return cut


def wall_bottoms(cooling, frame_shape=None):
    """Bottom Z of the left / right side walls: ZMIN, raised to clear the duct body and the frame
    (its duct lugs) by YIELD_CLEAR where they reach into the wall slab."""
    xi = HALF_W - WALL
    obstacles = [dp.shape for dp in getattr(cooling, "duct_parts", []) if dp.category == "printed"]
    if frame_shape is not None:
        obstacles.append(frame_shape)
    out = {}
    for sx in (-1, 1):
        xa, xb = (xi - YIELD_CLEAR, xi + WALL + YIELD_CLEAR) if sx > 0 else (-xi - WALL - YIELD_CLEAR, -xi + YIELD_CLEAR)
        # slab below the frame shelf (the top-wall contact with the shelf is intended)
        slab = bx(xa, xb, -200, 200, ZMIN - YIELD_CLEAR, F.ZMAX - F.SHELF_T - 0.01)
        z = ZMIN
        for o in obstacles:
            hit = o & slab
            if hit is not None and hit.volume > 1e-6:
                z = max(z, hit.bounding_box().max.Z + YIELD_CLEAR)
        if z > F.SIDE_OPEN[0]:
            raise ValueError(f"cover {'right' if sx > 0 else 'left'} wall would have to start at Z {z:.1f} to clear "
                             f"the duct/frame - reshape the cover instead")
        out[sx] = z
    return out


def build(cooling, frame_shape=None) -> PartSpec:
    xi = HALF_W - WALL
    fan_front = min(f["envelope"][2] for f in cooling.fans) if cooling.fans else F.FRONT_Y - 20
    yi = fan_front - GAP
    zt = F.ZMAX
    outer = bx(-xi - WALL, xi + WALL, yi - WALL, REAR_Y, ZMIN, zt + WALL)
    inner = bx(-xi, xi, yi, REAR_Y + 1, ZMIN - 1, zt)
    shell = outer - inner - bx(-xi - WALL - 1, xi + WALL + 1, TOP_REAR_Y, REAR_Y + 1, zt - 0.01, zt + WALL + 1)
    zb = wall_bottoms(cooling, frame_shape)
    for sx, z in zb.items():
        if z > ZMIN + 1e-6:          # raise this side wall's bottom edge over its whole length
            xa, xb = (xi - 0.01, xi + WALL + 1) if sx > 0 else (-xi - WALL - 1, -xi + 0.01)
            shell -= bx(xa, xb, yi - 0.01, REAR_Y + 1, ZMIN - 1, z)
    cut = _lidar_cut_full_wall(xi)
    if cut is not None:
        shell -= cut
    holes = []
    for sx in (-1, 1):
        holes.append(cyl_z(sx * F.COVER_SCREW_X, F.COVER_SCREW_Y, zt - 1, zt + WALL + 1, CLEAR["M3"]))
    # intake aperture in front of each fan: fully open, inlet ring + 2 x COVER_INTAKE_MARGIN, centred on the
    # intake. No grille: a grille at COVER_GAP in front of the impeller eye would throttle the blower (not in CFD).
    groups = {"fan_intake_aperture": [], "plenum_side_vents": [], "plenum_top_slots": []}
    apertures = []
    for f in cooling.fans:
        it = f.get("intake")
        if not it:
            continue
        cx, _, cz = it["center"]
        d_ap = it.get("d", C.FAN_INLET_D) + 2 * INTAKE_MARGIN
        groups["fan_intake_aperture"].append(cyl_y(cx, cz, yi - WALL - 1, yi + 1, d_ap))
        apertures.append({"centre_xz": [round(cx, 3), round(cz, 3)], "y_front_wall": [round(yi - WALL, 3), round(yi, 3)],
                          "d_aperture": d_ap, "d_inlet": it.get("d", C.FAN_INLET_D), "ribs": 0})
    # side vents over the plenum (frame front .. fan back) and a bit in front of it
    yv0 = F.FRONT_Y - 0.8
    yv1 = yv0 - 12.0
    for sx in (-1, 1):
        xa, xb = (xi - 1.0, xi + WALL + 1.0) if sx > 0 else (-xi - WALL - 1.0, -xi + 1.0)
        for k in range(4):
            z = F.SIDE_OPEN[0] + 1.0 + k * SLOT_P
            groups["plenum_side_vents"].append(bx(xa, xb, yv1, yv0, z, z + SLOT_W))
        # top slots over the plenum, outside the screw shelf
        x_a, x_b = F.SHELF_X + 1.5, xi - 1.0
        groups["plenum_top_slots"].append(bx(min(sx * x_a, sx * x_b), max(sx * x_a, sx * x_b), F.FRONT_Y - 5.0,
                                             F.FRONT_Y - 0.8, zt - 1, zt + WALL + 1))
    # open area of each vent group = material it removes from the closed shell / wall thickness
    vent_area = {}
    for k, hs in groups.items():
        v = 0.0
        for h in hs:
            cut_ = shell & h
            v += cut_.volume if cut_ is not None else 0.0
        vent_area[k + "_mm2"] = round(v / WALL, 1)
        holes += hs
    for h in holes:
        shell -= h
    deps = ["PCB", "XCARRIAGE", "RIGHT_LIMIT_X", "LIDAR_RESERVED_OPTICAL", "LIDAR_RESERVED_BODY",
            "FAN_INLET_D"] + list(group_params(G))
    deps += list(group_params(C.G)) if cooling.is_stub else (
        ["DUCT_MOUNT_POINTS_FINAL"] + [n for n in C.PARAMS if n.startswith("DUCT_FAN_") and n.endswith("_ENVELOPE")])
    spec = PartSpec("cover", shell, "printed", "ASA", (0.85, 0.35, 0.10), deps=deps, print_rot=(90, 0, 0),
                    notes="2 screws from the top; slides forward without unplugging LiDAR / probe / fan")
    spec.wall_bottoms = zb
    spec.vent_area = vent_area
    spec.intake_apertures = apertures
    return spec
