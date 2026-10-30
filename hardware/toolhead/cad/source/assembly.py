#!/usr/bin/env python3
"""K1 Max toolhead assembly (architecture A+, DD-01) in the nozzle frame.

    python cad/source/assembly.py          # builds and prints a part summary

Cooling module source - THE one-line switch for the fan/duct variant:
    "stub"       : structure/cooling.py stub (1 x 4020 at the stock pose + placeholder duct)
    "ducts"      : cad/source/ducts/duct_interface.json + build_ducts() (Duct/CFD agent), even if provisional
    "auto"       : "ducts" if that JSON exists, else "stub"
    "auto-final" : "ducts" only once the JSON says final_mount_points = true, else "stub" (default:
                   the duct agent asks that the frame is not printed against provisional points)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import structure  # noqa: F401,E402
from build123d import Color, Compound  # noqa: E402
from structure import common, cooling, frame, cover, probe_mount, coupon, reference  # noqa: E402

COOLING_SOURCE = "auto-final"

GROUPS = {"printed": "printed_parts", "stub": "stub_cooling_module", "reference": "reference_stock_parts",
          "keepout": "keepout_volumes", "replaced": "replaced_stock_parts"}


def build_parts(cooling_source: str = COOLING_SOURCE, use_stock_cache: bool = False):
    """Return (parts: list[PartSpec], cooling interface). use_stock_cache swaps the
    stock reference boxes for Henlor's solids (validation only - never exported)."""
    ci = cooling.get_cooling(cooling_source)
    parts = [frame.build(ci), cover.build(ci), probe_mount.build(), coupon.build()]
    parts += ci.duct_parts
    parts += reference.build_reference(ci, use_stock_cache)
    names = [p.name for p in parts]
    assert len(names) == len(set(names)), "duplicate part names"
    return parts, ci


def assembly_compound(parts, include=("printed", "stub", "reference", "keepout", "replaced")) -> Compound:
    groups = []
    for cat, gname in GROUPS.items():
        if cat not in include:
            continue
        kids = []
        for p in parts:
            if p.category != cat or not p.in_assembly:
                continue
            sols = p.shape.solids()
            s = sols[0] if len(sols) == 1 else Compound(children=list(sols))
            s.label = p.name
            s.color = Color(*p.colour)
            kids.append(s)
        if kids:
            groups.append(Compound(children=kids, label=gname))
    return Compound(children=groups, label="k1max_toolhead_A_plus")


if __name__ == "__main__":
    parts, ci = build_parts()
    print(f"cooling source: {ci.source} (stub={ci.is_stub})")
    for p in parts:
        s = p.shape
        bb = s.bounding_box()
        print(f"{p.category:9s} {p.name:42s} V={s.volume:9.1f} mm3  "
              f"bbox X{bb.min.X:7.1f}..{bb.max.X:6.1f} Y{bb.min.Y:7.1f}..{bb.max.Y:6.1f} Z{bb.min.Z:6.1f}..{bb.max.Z:6.1f}")
