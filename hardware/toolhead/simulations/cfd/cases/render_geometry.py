#!/usr/bin/env python3
"""Render a design's printed duct + fan envelopes + hotend/part environment to a PNG (report figure).

    $K1_PY render_geometry.py S1 OUT.png [--json params.json] [--stock]
"""
import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TH = HERE.parents[2]
sys.path.insert(0, str(TH / "cad/source/ducts"))


def mesh_of(shape, tol=0.05):
    import pyvista as pv
    from build123d import export_stl
    f = Path(tempfile.mkdtemp()) / "x.stl"
    export_stl(shape, str(f), tolerance=tol)
    return pv.read(str(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    ap.add_argument("out")
    ap.add_argument("--json")
    a = ap.parse_args()
    import json
    import pyvista as pv
    from duct_generator import build_ducts, get_params
    from export_for_cfd import hotend, part_proxy
    pv.OFF_SCREEN = True
    P = json.loads(Path(a.json).read_text()) if a.json else get_params(a.design)
    parts = build_ducts(P)
    pl = pv.Plotter(off_screen=True, window_size=(1200, 850))
    pl.set_background("white")
    pl.add_mesh(mesh_of(hotend()), color="#c9a46b", opacity=1.0)
    pl.add_mesh(mesh_of(part_proxy()), color="#cfd8e3", opacity=0.6)
    pl.add_mesh(mesh_of(parts["body"]), color="#2a78d6", opacity=0.85, smooth_shading=False)
    for k in P["fans"]:
        pl.add_mesh(mesh_of(parts[f"fan_{k}"], 0.2), color="#8a8984", opacity=0.25, style="surface")
    pl.add_text(P["label"], font_size=10, color="black")
    pl.camera_position = [(150, -190, 120), (5, -12, 18), (0, 0, 1)]
    pl.screenshot(a.out)
    pl.close()


if __name__ == "__main__":
    main()
