"""Cover: light ASA shell over frame, fan and PCB.

- Held by 2 vertical M3x6 button-head screws through the top wall into the
  frame shelf inserts. Remove them and slide the cover forward/up: the rear and
  bottom are open, so the LiDAR lead, probe lead and fan leads stay plugged and
  the duct stays bolted to the frame.
- Left wall is cut back wherever it would enter LIDAR_RESERVED_BOXES (+0.5 mm).
- Vents: slots in front of the part-fan intake; side and top slots over the
  plenum between frame and fan (3010 intake path); open open rear-top (cable exit, in front of the carriage strain relief).
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
GAP = prm(G, "COVER_GAP", 1.0, "DESIGN", "clearance to enclosed parts")
ZMIN = prm(G, "COVER_ZMIN", 24.0, "DESIGN", "open bottom: below the PCB bottom edge (24.5), above the duct")
HALF_W = prm(G, "COVER_HALF_W", 24.0, "DERIVED",
             "stock cover width +-24.0 (02:C4); inside RIGHT_LIMIT_X 24.2 in the XY-joint band")
REAR_Y = prm(G, "COVER_SIDE_REAR_Y", float(I.XCARRIAGE.ymin) - 0.5, "DESIGN",
             "side walls end 0.5 in front of the carriage envelope (XCARRIAGE.ymin)")
STRAIN_RELIEF_YMIN = prm(G, "CARRIAGE_STRAIN_RELIEF_YMIN", -32.3, "DERIVED", "02:N16 cable strain relief Y -32.3..-23.8, Z 72.3..91.2")
TOP_REAR_Y = STRAIN_RELIEF_YMIN - 0.5     # top wall stops in front of the strain relief; open behind = cable exit
SLOT_W = prm(G, "COVER_SLOT_W", 2.0, "DESIGN", "vent slot width (finger-safe, prints clean)")
SLOT_P = prm(G, "COVER_SLOT_PITCH", 4.0, "DESIGN", "vent pitch (2 mm bars)")


def build(cooling) -> PartSpec:
    xi = HALF_W - WALL
    fan_front = min(f["envelope"][2] for f in cooling.fans) if cooling.fans else F.FRONT_Y - 20
    yi = fan_front - GAP
    zt = F.ZMAX
    outer = bx(-xi - WALL, xi + WALL, yi - WALL, REAR_Y, ZMIN, zt + WALL)
    inner = bx(-xi, xi, yi, REAR_Y + 1, ZMIN - 1, zt)
    shell = outer - inner - bx(-xi - WALL - 1, xi + WALL + 1, TOP_REAR_Y, REAR_Y + 1, zt - 0.01, zt + WALL + 1)
    cut = F.lidar_cut()
    if cut is not None:
        shell -= cut
    holes = []
    for sx in (-1, 1):
        holes.append(cyl_z(sx * F.COVER_SCREW_X, F.COVER_SCREW_Y, zt - 1, zt + WALL + 1, CLEAR["M3"]))
    # front vents in front of each fan intake
    for f in cooling.fans:
        it = f.get("intake")
        if not it:
            continue
        cx, _, cz = it["center"]
        r = it.get("d", 28.0) / 2 + 1.0
        disc = cyl_y(cx, cz, yi - WALL - 1, yi + 1, 2 * r)
        z = cz - r
        while z < cz + r:
            holes.append(bx(cx - r, cx + r, yi - WALL - 1, yi + 1, z, z + SLOT_W) & disc)
            z += SLOT_P
    # side vents over the plenum (frame front .. fan back) and a bit in front of it
    yv0 = F.FRONT_Y - 0.8
    yv1 = yv0 - 12.0
    for sx in (-1, 1):
        xa, xb = (xi - 1.0, xi + WALL + 1.0) if sx > 0 else (-xi - WALL - 1.0, -xi + 1.0)
        for k in range(4):
            z = F.SIDE_OPEN[0] + 1.0 + k * SLOT_P
            holes.append(bx(xa, xb, yv1, yv0, z, z + SLOT_W))
        # top slots over the plenum, outside the screw shelf
        x_a, x_b = F.SHELF_X + 1.5, xi - 1.0
        holes.append(bx(min(sx * x_a, sx * x_b), max(sx * x_a, sx * x_b), F.FRONT_Y - 5.0, F.FRONT_Y - 0.8,
                        zt - 1, zt + WALL + 1))
    for h in holes:
        shell -= h
    deps = ["PCB", "XCARRIAGE", "RIGHT_LIMIT_X", "LIDAR_RESERVED_OPTICAL", "LIDAR_RESERVED_BODY"] + list(group_params(G))
    deps += list(group_params(C.G)) if cooling.is_stub else ["DUCT_MOUNT_POINTS_FINAL"]
    return PartSpec("cover", shell, "printed", "ASA", (0.85, 0.35, 0.10), deps=deps, print_rot=(90, 0, 0),
                    notes="2 screws from the top; slides forward without unplugging LiDAR / probe / fan")
