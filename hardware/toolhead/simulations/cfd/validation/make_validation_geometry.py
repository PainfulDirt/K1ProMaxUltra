#!/usr/bin/env python3
"""Validation duct geometry (build123d), all dimensions in mm.

Nozzle axis = Z through the origin, nozzle tip at z = 0.
Duct channel (inside dims, 20 mm wide in Y, extruded profile in XZ):
  * vertical inlet leg 15 (X) x 20 (Y), x in [35,50], from z = 35 (fan face) down to z = 20.5
  * 90 deg bend about the Y axis through (x=30, z=20.5), radii 5 / 20 mm
  * linear contraction x 30 -> 10 from 15 mm to 2 mm high (flat floor at z = 0.5)
  * 2 x 20 mm slot exit at x = 10, z in [0.5, 2.5], jet pointing -X at the nozzle
Walls 1.2 mm. A 5 mm "fan stub" block caps the inlet; its exposed face (15x20 at z=35)
is the `inlet` patch. Nozzle: cone r 0.5 -> 3 mm over z 0..3, cylinder r 3 to z = 10.

Writes <out>/duct.stl, inlet.stl, nozzle.stl (+ STEP of each body).
"""
import sys
from pathlib import Path

from build123d import (Box, Cone, Cylinder, Plane, Polygon, Pos, Circle, Rectangle,
                       export_step, extrude, offset, Kind, Location)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pipeline"))
from geometry import export_patches, planar_face_at  # noqa: E402

T = 1.2          # wall thickness
W = 20.0         # channel width (Y)
Z_FAN = 35.0     # inlet (fan) face height


def channel_profile(extend_top=0.0, land=False):
    """2D channel outline in local (x, z) coordinates (sketch plane XY -> mapped to XZ)."""
    leg = Polygon((35, 20.5), (50, 20.5), (50, Z_FAN + extend_top), (35, Z_FAN + extend_top), align=None)
    ring = Pos(30, 20.5) * (Circle(20) - Circle(5))
    quad = Polygon((30, 20.5), (50, 20.5), (50, 0.5), (30, 0.5), align=None)
    bend = ring & quad
    contr = Polygon((30, 0.5), (30, 15.5), (10, 2.5), (10, 0.5), align=None)
    prof = leg + bend + contr
    if land:  # carry the slot through the exit plane so the cut is clean
        prof = prof + Polygon((5, 0.5), (12, 0.5), (12, 2.5), (5, 2.5), align=None)
    return prof


def build():
    inner2d = channel_profile(extend_top=6.0, land=True)
    outer2d = offset(channel_profile(), T, kind=Kind.INTERSECTION)
    inner = extrude(Plane.XZ * inner2d, amount=W / 2, both=True)
    outer = extrude(Plane.XZ * outer2d, amount=W / 2 + T, both=True)
    # clip the outer shell: exit plane x >= 10, top at the fan face
    clip = Pos(40, 0, (Z_FAN - 20) / 2) * Box(60, 60, Z_FAN + 20)
    clip = clip & Pos(10 + 50, 0, 0) * Box(100, 100, 200)
    shell = (outer & clip) - inner
    fan = Pos(42.5, 0, Z_FAN + 2.5) * Box(15 + 2 * T, W + 2 * T, 5)
    body = shell + fan
    nozzle = Pos(0, 0, 0) * Cone(0.5, 3.0, 3.0, align=None) + Pos(0, 0, 3) * Cylinder(3, 7, align=None)
    return body, nozzle


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    body, nozzle = build()
    assert body.is_valid and nozzle.is_valid
    export_step(body, str(out / "duct_body.step"))
    export_step(nozzle, str(out / "nozzle.step"))
    inlet_pred = planar_face_at("z", Z_FAN, normal_sign=-1)
    c1 = export_patches(body, {"inlet": inlet_pred}, default="duct", outdir=out)
    c2 = export_patches(nozzle, {}, default="nozzle", outdir=out)
    inl = [f for f in body.faces() if inlet_pred(f)]
    info = {"body_volume_mm3": body.volume, "inlet_area_mm2": sum(f.area for f in inl),
            "n_inlet_faces": len(inl), "tris": {**c1, **c2},
            "bbox_body": [tuple(body.bounding_box().min), tuple(body.bounding_box().max)]}
    print(info)
    assert abs(info["inlet_area_mm2"] - 300.0) < 1e-6, "inlet face not isolated"
    return info


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "validation_geom")
