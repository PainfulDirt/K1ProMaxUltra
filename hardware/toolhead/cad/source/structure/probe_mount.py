"""MicroProbe V2 mount (DD-03): drop-in, stiffer replacement for today's
Printables 785004 adapter, at an identical pin position.

Anchor (default, the only variant built): the two toolhead features today's
785004 hangs on (interfaces.PROBE_ADAPTER_SCREWS, 2 x ~M2 vertical, heads at the
top face, shanks ending in two side windows that receive the toolhead tabs;
toolhead mating face ~Y +16.9 above Z +41.8; research/01 §H.1). All of that is
ESTIMATED until M8 (one photo + calipers) -> NOT RELEASED.

Pin position: the probe bores sit at the same place relative to the anchor
screws as in 785004 (bores on the line Y = PROBE_BODY_Y.max - FLANGE_TO_BACK =
+21.3, anchors at +20.1), so the pin lands wherever it is today whatever the
true pin-to-hole offset is (1.0 assumed in interfaces vs 2.75 in the V1 STEP).

Changes vs 785004 (why it is stiffer / more stable):
  - PA-CF (E ~5 GPa vs ~2-3.5 GPa PLA/PETG; CTE ~40e-6 vs ~70e-6) - DD-07, < 15 mm from the heater;
  - closed box-section column (walls 2.4 / 1.3) instead of an open skirt;
  - the flange sits in a 0.8 mm locating pocket (X/Y located by the flange
    edges, not by the M2.5 screws' clearance);
  - M2.5 brass heat-set inserts for the probe screws (no thread creep);
  - same envelope, rear face not behind 785004's (Y +29.1) so the keep-out
    zones measured with 785004 stay valid.
The vertical load path cannot get shorter with this anchor: the anchor height
(tab tops ~Z +53.3) is set by the toolhead. The heatsink cross-hole alternative
(13.8 mm path) is blocked by LIDAR_RESERVED_BODY (see stiffness.py / report).
Print: upside down (top face on the bed), PA-CF, 100 % infill or >= 5 walls.
"""
from __future__ import annotations

from build123d import Polyline, make_face, extrude

from .common import PartSpec, bx, cyl_z, prm, INSERTS, INSERT_DEPTH_EXTRA, group_params, INSERT_MASS_G, screw_mass_g
from . import reference as R
import interfaces as I

G = "probe_mount"
A = I.PROBE_ADAPTER_785004
ANCHORS = [(float(x), float(y)) for x, y in I.PROBE_ADAPTER_SCREWS]
ANCHOR_Y = sum(y for _, y in ANCHORS) / len(ANCHORS)
HALF_W = prm(G, "PM_HALF_W", 17.0, "ESTIMATED", "785004 envelope X -17.0..+17.1 (01 §H.1)")
SEAT_TO_ANCHOR = prm(G, "PM_SEAT_TO_ANCHOR_Z", 27.05, "DERIVED",
                     "785004 STL: flange seat -> window top (= carriage tab top, the bearing face) 01 §H.1")
SEAT_TO_TOP = prm(G, "PM_SEAT_TO_TOP_Z", 32.5, "DERIVED", "785004 STL height (01 §H.1)")
Z_SEAT = float(I.PROBE_MOUNT_FACE_Z)
Z_ANCHOR = Z_SEAT + SEAT_TO_ANCHOR
TOP_Z = Z_SEAT + SEAT_TO_TOP
REAR_Y = min(float(A.ymax), float(I.REAR_LIMIT_Y))     # never behind today's adapter
MATE_Y = prm(G, "PM_MATING_FACE_Y", 16.9, "ESTIMATED",
             "785004 block face above Z 41.8 (01 §H.1); Henlor carriage rear wall = anchor + (-3.4) (+0.2 gap)")
FRONT_LOW_Y = prm(G, "PM_FRONT_LOW_Y", 13.4, "ESTIMATED",
                  "785004 skirt front below Z 41.8 (01 §H.1); clears the Henlor carriage lower wall by ~0.6")
STEP_Z = prm(G, "PM_STEP_Z", 41.8, "ESTIMATED", "785004 skirt/block step (01 §H.1); 45 deg chamfer below it")
# carriage tabs (Henlor 742370 carriage, relative to their vertical hole axis = the anchor screw axis)
TAB_HALF_X = prm(G, "PM_TAB_HALF_X", 2.3, "DERIVED", "Henlor carriage rear tabs 4.1-4.6 wide around the hole")
TAB_REAR = prm(G, "PM_TAB_REAR_DY", 1.8, "DERIVED", "Henlor tab rear face = hole axis + 1.8")
TAB_H = prm(G, "PM_TAB_H", 4.9, "DERIVED", "Henlor tab Z 49.5..54.4")
WIN_CLEAR = prm(G, "PM_WINDOW_CLEAR", 0.4, "DESIGN", "per side around the carriage tabs")
WIN_Z0 = Z_ANCHOR - prm(G, "PM_WINDOW_H", 9.3, "DERIVED", "785004 window height (01 §H.1)")
ANCHOR_CLEAR_D = prm(G, "PM_ANCHOR_CLEAR_D", 2.4, "DERIVED", "785004 top holes, ~M2 (01 §H.1)")
ANCHOR_CBORE = (prm(G, "PM_ANCHOR_CBORE_D", 4.2, "DERIVED", "785004 counterbore (01 §H.1)"),
                prm(G, "PM_ANCHOR_CBORE_DEPTH", 2.95, "DERIVED", "785004 counterbore depth (01 §H.1)"))
PAD_T = prm(G, "PM_PAD_T", 4.0, "DESIGN", "flange seat plate above the pocket")
POCKET = (prm(G, "PM_POCKET_DEPTH", 0.8, "DESIGN", "flange locating pocket (flange is 2.1 thick)"),
          prm(G, "PM_POCKET_CLEAR", 0.1, "DESIGN", "per side, printed PA-CF"))
WALL = prm(G, "PM_WALL", 2.4, "DESIGN", "box-section wall (6 lines)")
CABLE = (prm(G, "PM_CABLE_HALF_X", 5.0, "DESIGN", "PicoBlade lead + plug through the body (785004: 11 x 4)"),
         prm(G, "PM_CABLE_Y0", 24.2, "ESTIMATED", "above the probe connector at the back of the body"),
         prm(G, "PM_CABLE_Y1", 27.8, "DESIGN", "leaves a 1.3 mm rear wall"))
TIE_SLOT = (1.6, 3.2)
TIE_BAR = prm(G, "PM_TIE_BAR", 1.5, "DESIGN", "roof bar the probe-lead tie wraps around")
# Henlor carriage tab-hole axis, for the cross-check in validate.py (not used for geometry)
HENLOR_TAB_HOLE_Y = prm(G, "HENLOR_TAB_HOLE_Y", 22.9, "DERIVED", "Henlor carriage rear-tab Ø2.0 holes, spacing 24.1")
HENLOR_TAB_TOP_Z = prm(G, "HENLOR_TAB_TOP_Z", 54.4, "DERIVED", "Henlor carriage rear-tab top face")
HENLOR_SHIFT = (0.0, ANCHOR_Y - HENLOR_TAB_HOLE_Y, Z_ANCHOR - HENLOR_TAB_TOP_Z)
ANCHOR_CONFIRMED = prm(G, "PM_ANCHOR_CONFIRMED_M8", 0.0, "MISSING",
                       "DD-03: carriage-side anchor of 785004 not confirmed by the user (M8 photo + calipers); "
                       "Henlor puts it (0, +2.8, +0.6) mm from the interfaces placement")


def build() -> PartSpec:
    fw = float(I.PROBE_FLANGE[0])
    c = POCKET[1]
    z_seat0 = Z_SEAT - POCKET[0]
    z_pad1 = Z_SEAT + PAD_T
    # side profile (YZ): front 13.4 below the step (45 deg chamfer), 16.9 above; rear REAR_Y
    ch = MATE_Y - FRONT_LOW_Y
    prof = [(FRONT_LOW_Y, z_seat0), (REAR_Y, z_seat0), (REAR_Y, TOP_Z), (MATE_Y, TOP_Z),
            (MATE_Y, STEP_Z), (FRONT_LOW_Y, STEP_Z - ch)]
    body = extrude(make_face(Polyline(*[(-HALF_W, y, z) for y, z in prof], close=True)),
                   amount=2 * HALF_W, dir=(1, 0, 0))
    holes = []
    # flange pocket (open at the front: the flange front edge stays 0.9 proud, as with 785004)
    holes.append(bx(-fw / 2 - c, fw / 2 + c, FRONT_LOW_Y - 1, R.PROBE_BACK_Y + c, z_seat0 - 0.01, Z_SEAT))
    # closed box section; cable runs through it
    cx = min(abs(x) for x, _ in ANCHORS) - TAB_HALF_X - WIN_CLEAR - 2.0     # 2 mm wall to the windows
    holes.append(bx(-cx, cx, MATE_Y + WALL, CABLE[2], z_pad1 + 2.0, TOP_Z - 2.5))
    holes.append(bx(-(HALF_W - WALL), HALF_W - WALL, MATE_Y + WALL, CABLE[2], z_pad1 + 2.0, WIN_Z0 - 2.0))
    holes.append(bx(-CABLE[0], CABLE[0], CABLE[1], CABLE[2], z_seat0 - 1, TOP_Z + 1))
    # windows that receive the carriage tabs + anchor screw holes + counterbores
    for x, y in ANCHORS:
        w = TAB_HALF_X + WIN_CLEAR
        holes.append(bx(x - w, x + w, MATE_Y - 1, y + TAB_REAR + WIN_CLEAR, WIN_Z0, Z_ANCHOR))
        holes.append(cyl_z(x, y, Z_ANCHOR - 0.5, TOP_Z + 1, ANCHOR_CLEAR_D))
        holes.append(cyl_z(x, y, TOP_Z - ANCHOR_CBORE[1], TOP_Z + 1, ANCHOR_CBORE[0]))
    # probe screws: M2.5 heat-set inserts from the seat
    ins = INSERTS["M2.5"]
    for x, y in R.PROBE_HOLES:
        holes.append(cyl_z(x, y, Z_SEAT - 1, Z_SEAT + ins.length + INSERT_DEPTH_EXTRA, ins.hole_d))
    # cable-tie slot through the roof next to the cable exit: the tie goes down the
    # cable channel, through the cavity and up this slot, cinching the lead to the bar
    xs = -CABLE[0] - TIE_BAR
    holes.append(bx(xs - TIE_SLOT[0], xs, CABLE[1], CABLE[2], TOP_Z - 4.0, TOP_Z + 1))
    part = body
    for hh in holes:
        part -= hh
    deps = ["PROBE_X", "PROBE_Y", "PROBE_MOUNT_FACE_Z", "PROBE_HOLE_SPACING", "PROBE_FLANGE", "PROBE_FLANGE_TO_BACK",
            "PROBE_BODY_Y", "PROBE_ADAPTER_785004", "PROBE_ADAPTER_SCREWS", "REAR_LIMIT_Y", "HOT_ZONE_CLEARANCE",
            "SOCK", "XCARRIAGE", "INSERT_M25_HOLE_D"] + list(group_params(G))
    hw = [("M2.5x5 (BIQU kit) into M2.5 heat-set inserts", 2, screw_mass_g(2.5, 5)),
          ("M2.5 heat-set insert", 2, INSERT_MASS_G["M2.5"]),
          ("~M2 anchor screws, reuse 785004's (size/length MISSING, M8) - reused, no added mass", 2, 0.0)]
    return PartSpec("probe_mount", part, "printed", "PA-CF", (0.15, 0.15, 0.15), deps=deps,
                    print_rot=(180, 0, 0), hardware=hw,
                    notes="NOT RELEASED until M8 confirms the 785004 anchor (photo + calipers)")
