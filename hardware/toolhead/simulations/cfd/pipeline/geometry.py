"""Helpers to turn build123d solids into named-patch STL sets for the CFD pipeline.

The whole shape is tessellated ONCE (BRepMesh), then triangles are routed to patch
files face-by-face, so edges shared between patches (e.g. the inlet face and the
duct walls) have identical vertices -> the union of the patch STLs is watertight.

Units: whatever the CAD is in (the pipeline expects millimetres).

Example
-------
    from geometry import export_patches
    export_patches(body, {"inlet": lambda f: is_inlet(f)}, default="duct", outdir="stl")
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

import numpy as np
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location


def tessellate_faces(shape, lin_defl: float = 0.02, ang_defl: float = 0.15):
    """Yield (face, vertices[N,3], triangles[M,3]) with outward-consistent winding."""
    BRepMesh_IncrementalMesh(shape.wrapped, lin_defl, False, ang_defl, True)
    for f in shape.faces():
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f.wrapped, loc)
        if tri is None:
            continue
        trsf = loc.Transformation()
        v = np.array([[p.X(), p.Y(), p.Z()] for p in
                      (tri.Node(i).Transformed(trsf) for i in range(1, tri.NbNodes() + 1))])
        t = np.array([tri.Triangle(i).Get() for i in range(1, tri.NbTriangles() + 1)]) - 1
        if f.wrapped.Orientation() == TopAbs_REVERSED:
            t = t[:, [0, 2, 1]]
        yield f, v, t


def write_ascii_stl(path, name: str, tris: np.ndarray, scale: float = 1.0):
    """tris: [M,3,3] array of triangle vertex coordinates."""
    tris = np.asarray(tris, float) * scale
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1)
    n[ln > 0] /= ln[ln > 0, None]
    with open(path, "w") as fh:
        fh.write(f"solid {name}\n")
        for nn, t in zip(n, tris):
            fh.write(f" facet normal {nn[0]:.6e} {nn[1]:.6e} {nn[2]:.6e}\n  outer loop\n")
            for p in t:
                fh.write(f"   vertex {p[0]:.9e} {p[1]:.9e} {p[2]:.9e}\n")
            fh.write("  endloop\n endfacet\n")
        fh.write(f"endsolid {name}\n")


def export_patches(shape, rules: Dict[str, Callable], default: str, outdir,
                   lin_defl: float = 0.02, ang_defl: float = 0.15) -> Dict[str, int]:
    """Split the faces of `shape` into patches and write <outdir>/<patch>.stl.

    rules   : ordered {patch_name: predicate(face) -> bool}; first match wins.
    default : patch name for faces that match no rule.
    Returns {patch: n_triangles}.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    buckets: Dict[str, list] = {}
    for f, v, t in tessellate_faces(shape, lin_defl, ang_defl):
        name = next((k for k, pred in rules.items() if pred(f)), default)
        buckets.setdefault(name, []).append(v[t])
    counts = {}
    for name, parts in buckets.items():
        tris = np.concatenate(parts)
        write_ascii_stl(outdir / f"{name}.stl", name, tris)
        counts[name] = len(tris)
    return counts


def planar_face_at(axis: str, value: float, normal_sign: int | None = None, tol: float = 1e-6):
    """Predicate: planar face lying in plane <axis>=value (optionally with normal sign)."""
    i = "xyz".index(axis)

    def pred(f):
        if f.geom_type.name != "PLANE":
            return False
        bb = f.bounding_box()
        if abs(tuple(bb.min)[i] - value) > tol or abs(tuple(bb.max)[i] - value) > tol:
            return False
        if normal_sign is None:
            return True
        return np.sign(tuple(f.normal_at())[i]) == normal_sign
    return pred
