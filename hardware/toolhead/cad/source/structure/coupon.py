"""Fit-check coupon: PRINT THIS FIRST (ASA, ~3-4 g, ~10 min).

It reproduces, with the production parameters, only the interfaces whose
values are DERIVED/ESTIMATED, so they can be checked on the real printer
before anything large is printed:

A. PCB interface (same code paths as the frame): the three Ø3.4 PCB holes on
   the 24 mm pattern, Ø6.5 boss pads (MODULE_MOUNT_PAD_D) 7.6 long (bridging
   PCB_COMPONENT_ZONE; necked to Ø5.8 through the Ø6.2 holes of the PCB "2nd
   plate" seen in Henlor's model), the 4th-corner pad, and a 1.6 mm
   plate at the frame's back-face plane with the fan window.
   Check: the 3 screws enter the PCB holes square; every pad seats flat on
   bare PCB (no component under a pad, plate clear of all connectors/plugs);
   the window lines up with the PCB fan cutout.
B. MicroProbe pattern: two M2.5 heat-set insert bosses at 17.0 mm and a fence
   around the flange outline (21.93 x 15.60 + 0.1/side), i.e. the probe-mount
   seat. Check: inserts install cleanly, the probe drops into the fence, the
   BIQU M2.5x5 screws reach. The probe's connector side is the fence side
   marked by the notch.
C. One M3 insert boss (frame insert size).
Built in the nozzle frame at the frame's plate position (part A), printed
front face down. It is not part of the assembly.
"""
from __future__ import annotations

from .common import PartSpec, bx, cyl_y, prm, INSERTS, INSERT_DEPTH_EXTRA, CLEAR, group_params
from . import frame as F
import interfaces as I

G = "coupon"
T = prm(G, "COUPON_PLATE_T", 1.6, "DESIGN", "4 layers stiff enough to hold the pattern")
RING_HALF = prm(G, "COUPON_RING_HALF", 16.0, "DESIGN", "plate half-size around the 24 mm pattern")
WIN_R = prm(G, "COUPON_WINDOW_R", 12.5, "DESIGN", "material saver; shows the PCB fan cutout")
TAB_GAP = prm(G, "COUPON_PROBE_TAB_DZ", 2.0, "DESIGN", "probe tab below the ring")


def build() -> PartSpec:
    cz = float(I.FAN3010_PATTERN_CZ)
    yb = F.BACK_Y
    yf = yb - T
    y_pcb = float(I.MODULE_MOUNT_BEARING_Y)
    z0, z1 = cz - RING_HALF, cz + RING_HALF
    part = bx(-RING_HALF, RING_HALF, yf, yb, z0, z1) - cyl_y(0, cz, yf - 1, yb + 1, 2 * WIN_R)
    part += F.pcb_bosses(back_y=yb, collar=False)
    holes = [cyl_y(x, z, y_pcb + 1, yf - 1, CLEAR["M3"]) for x, z in I.MODULE_MOUNT_HOLES]

    # C. M3 insert test boss (on the ring, right side, mid height)
    m3 = INSERTS["M3"]
    xb, zb = RING_HALF - m3.boss_d / 2, cz
    part += cyl_y(xb, zb, yb - 0.5, yb + m3.length + INSERT_DEPTH_EXTRA, m3.boss_d)
    holes.append(cyl_y(xb, zb, yf - 1, yb + m3.length + INSERT_DEPTH_EXTRA + 1, m3.hole_d))

    # B. probe tab: flange plane mapped onto the coupon plane (assembly Y -> coupon Z)
    fw, fd = float(I.PROBE_FLANGE[0]), float(I.PROBE_FLANGE[1])
    c, lip, rim = 0.1, 1.0, 0.8
    ins = INSERTS["M2.5"]
    boss_h = ins.length + INSERT_DEPTH_EXTRA - T
    tz1 = z0 - TAB_GAP + 0.01
    tz0 = tz1 - fd - 2 * (c + lip)
    tx = fw / 2 + c + lip
    tab = bx(-tx, tx, yf, yb, tz0, tz1)
    tab += bx(-RING_HALF, RING_HALF, yf, yb, tz1 - 0.02, z0 + 0.01)          # bridge to the ring
    fence = bx(-tx, tx, yb - 0.01, yb + boss_h + rim, tz0, tz1) - bx(-fw / 2 - c, fw / 2 + c, yb - 1, yb + 10,
                                                                     tz0 + lip, tz1 - lip)
    # notch in the fence on the connector (back-face) side = coupon +Z side
    fence -= bx(-2.0, 2.0, yb + boss_h, yb + 10, tz1 - lip - 0.5, tz1 + 0.5)
    tab += fence
    hole_line_z = tz1 - lip - c - float(I.PROBE_FLANGE_TO_BACK)
    for sx in (-1, 1):
        x = sx * float(I.PROBE_HOLE_SPACING) / 2
        tab += cyl_y(x, hole_line_z, yb - 0.5, yb + boss_h, ins.boss_d)
        holes.append(cyl_y(x, hole_line_z, yf - 1, yb + boss_h + 1, ins.hole_d))
    # lighten the tab centre (inside the fence, between the inserts)
    holes.append(bx(-5.0, 5.0, yf - 1, yb + 1, tz0 + lip + 1.5, tz1 - lip - 1.5))
    part += tab
    for h in holes:
        part -= h
    deps = ["MODULE_MOUNT_HOLES", "MODULE_MOUNT_PAD_D", "MODULE_MOUNT_BEARING_Y", "PCB_COMPONENT_ZONE",
            "FAN3010_PATTERN_CZ", "PROBE_HOLE_SPACING", "PROBE_HOLE_D", "PROBE_FLANGE", "PROBE_FLANGE_TO_BACK",
            "INSERT_M3_HOLE_D", "INSERT_M25_HOLE_D", "FRAME_FOURTH_PAD_ON", "PCB_PLATE2_YMIN", "PCB_PLATE2_HOLE_D"] + list(group_params(G))
    return PartSpec("fitcheck_coupon", part, "fitcheck", "ASA", (0.95, 0.85, 0.20), deps=deps,
                    print_rot=(90, 0, 0), in_assembly=False,
                    notes="PRINT FIRST. Same material as the frame so shrinkage matches.")
