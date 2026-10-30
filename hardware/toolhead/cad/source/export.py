#!/usr/bin/env python3
"""Manufacturing + assembly exports, then re-open and verify every file.

    python cad/source/export.py [--cooling stub|ducts|auto]

Writes (all mm):
  cad/exports/step/<part>.step   print-oriented, on the plate at Z 0, one solid
  cad/exports/3mf/<part>.3mf     same orientation, one object, unit = millimetre
  cad/exports/stl/<part>.stl     same orientation
  cad/exports/step/k1max_toolhead_assembly.step   nozzle frame, named + coloured parts in groups
        printed_parts / stub_cooling_module / reference_stock_parts / keepout_volumes / replaced_stock_parts
        (reference geometry = interfaces.py boxes only; no third-party solids are exported)
  cad/exports/export_manifest.json

Verification tolerances (documented, fail loudly):
  STEP part     : 1 solid, |dV|/V < 1e-6, bbox corners within 1e-3 mm   (exact B-rep round trip)
  3MF / STL     : 1 object, |dV|/V < 5e-3, bbox corners within 0.05 mm (tessellation, 0.01 mm chord)
                  STL also watertight
  assembly STEP : same leaf names as the in-memory model, per-leaf |dV|/V < 1e-6, every leaf coloured,
                  every group present
STEP files carry a timestamp in their header, so they are reproducible in content, not byte-for-byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import trimesh  # noqa: E402
from build123d import Compound, Mesher, Unit, export_step, export_stl, import_step  # noqa: E402

import assembly  # noqa: E402

OUT = HERE.parent / "exports"
LIN_DEF, ANG_DEF = 0.01, 0.1
TOL = {"step_dv": 1e-6, "step_bb": 1e-3, "mesh_dv": 5e-3, "mesh_bb": 0.05}
FAILS: list[str] = []


def _bb(s):
    b = s.bounding_box()
    return [b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z]


def _cmp(tag, v_ref, bb_ref, v, bb, dv_tol, bb_tol):
    dv = abs(v - v_ref) / v_ref
    dbb = max(abs(a - b) for a, b in zip(bb_ref, bb))
    ok = dv < dv_tol and dbb < bb_tol
    print(f"[{'PASS' if ok else 'FAIL'}] {tag}: dV/V={dv:.2e} dBB={dbb:.2e} mm")
    if not ok:
        FAILS.append(tag)
    return {"dV_rel": dv, "dBB_mm": dbb, "pass": ok}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cooling", default=assembly.COOLING_SOURCE)
    args = ap.parse_args()
    parts, ci = assembly.build_parts(args.cooling, use_stock_cache=False)
    for d in ("step", "3mf", "stl"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    man = {"cooling_source": ci.source, "is_stub": ci.is_stub, "tolerances": TOL, "parts": {}, "assembly": {}}

    for p in [q for q in parts if q.printed()]:
        po = p.print_oriented()
        solid = po.solids()[0]
        solid.label = p.name
        v0, bb0 = solid.volume, _bb(solid)
        f_step, f_3mf, f_stl = OUT / "step" / f"{p.name}.step", OUT / "3mf" / f"{p.name}.3mf", OUT / "stl" / f"{p.name}.stl"
        export_step(solid, str(f_step))
        export_stl(solid, str(f_stl), tolerance=LIN_DEF, angular_tolerance=ANG_DEF)
        m = Mesher(unit=Unit.MM)
        m.add_shape(solid, linear_deflection=LIN_DEF, angular_deflection=ANG_DEF)
        m.add_meta_data("k1th", "part", p.name, "xs:string", False)
        m.write(str(f_3mf))
        rec = {"material": p.material, "category": p.category, "volume_mm3": round(v0, 3),
               "bbox_print": [round(v, 3) for v in bb0], "files": {}}
        # --- re-open
        r = import_step(str(f_step))
        n = len(r.solids())
        if n != 1:
            FAILS.append(f"{p.name} STEP has {n} solids")
        rec["files"]["step"] = {"path": str(f_step.relative_to(OUT.parent)), "sha256_16": sha(f_step), "solids": n,
                                **_cmp(f"{p.name} STEP", v0, bb0, r.volume, _bb(r), TOL["step_dv"], TOL["step_bb"])}
        r3 = Mesher().read(str(f_3mf))
        if len(r3) != 1:
            FAILS.append(f"{p.name} 3MF has {len(r3)} objects")
        rec["files"]["3mf"] = {"path": str(f_3mf.relative_to(OUT.parent)), "sha256_16": sha(f_3mf), "objects": len(r3),
                               **_cmp(f"{p.name} 3MF", v0, bb0, sum(s.volume for s in r3), _bb(Compound(r3)),
                                      TOL["mesh_dv"], TOL["mesh_bb"])}
        tm = trimesh.load(str(f_stl))
        bbs = list(tm.bounds[0]) + list(tm.bounds[1])
        rec["files"]["stl"] = {"path": str(f_stl.relative_to(OUT.parent)), "sha256_16": sha(f_stl),
                               "watertight": bool(tm.is_watertight),
                               **_cmp(f"{p.name} STL", v0, bb0, float(tm.volume), bbs, TOL["mesh_dv"], TOL["mesh_bb"])}
        if not tm.is_watertight:
            FAILS.append(f"{p.name} STL not watertight")
        man["parts"][p.name] = rec

    # --- assembly
    asm = assembly.assembly_compound(parts)
    f_asm = OUT / "step" / "k1max_toolhead_assembly.step"
    export_step(asm, str(f_asm))
    ref = {}
    for g in asm.children:
        for leaf in g.children:
            ref[leaf.label] = (g.label, leaf.volume)
    back = import_step(str(f_asm))
    got, groups, uncoloured = {}, set(), []
    for g in back.children:
        groups.add(g.label)
        for leaf in g.children:
            got[leaf.label] = leaf.volume
            if leaf.color is None:
                uncoloured.append(leaf.label)
    missing = sorted(set(ref) - set(got))
    extra = sorted(set(got) - set(ref))
    bad_v = {k: (ref[k][1], got[k]) for k in ref if k in got and abs(got[k] - ref[k][1]) > TOL["step_dv"] * max(ref[k][1], 1)}
    want_groups = {g.label for g in asm.children}
    ok = not missing and not extra and not bad_v and not uncoloured and want_groups <= groups
    print(f"[{'PASS' if ok else 'FAIL'}] assembly STEP: {len(got)}/{len(ref)} named leaves, groups {sorted(groups)}, "
          f"missing {missing}, extra {extra}, volume mismatches {list(bad_v)}, uncoloured {uncoloured}")
    if not ok:
        FAILS.append("assembly STEP round trip")
    man["assembly"] = {"path": str(f_asm.relative_to(OUT.parent)), "sha256_16": sha(f_asm), "leaves": len(got),
                       "groups": sorted(groups), "parts": {k: {"group": v[0], "volume_mm3": round(v[1], 3)}
                                                           for k, v in ref.items()}, "pass": ok}
    man["failures"] = FAILS
    (OUT / "export_manifest.json").write_text(json.dumps(man, indent=1, default=float))
    print(f"\n{'ALL EXPORTS VERIFIED' if not FAILS else 'EXPORT VERIFICATION FAILED: ' + '; '.join(FAILS)}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
