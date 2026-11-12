#!/usr/bin/env python3
"""CAD toolchain self-test (build123d on OCP).

Builds a test solid with a fillet and a hollow channel, exports STEP / STL / 3MF,
re-imports STEP and 3MF and compares volume + bounding box, and checks boolean
intersection / clearance detection between two solids.

Usage:  /opt/k1th/venv/bin/python cad_selftest.py [outdir]
Exit code 0 = all checks passed.
"""
import json
import sys
import tempfile
from pathlib import Path

from build123d import (Box, Cylinder, Mesher, Pos, Rot, export_step, export_stl,
                       fillet, import_step, Axis, Unit)

out = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="cadtest_"))
out.mkdir(parents=True, exist_ok=True)
results = {}
ok = True


def check(name, cond, info=""):
    global ok
    results[name] = {"pass": bool(cond), "info": info}
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {info}")


# 1. test solid: 40x20x15 block, vertical edges filleted r=3, Ø6 channel along X
blk = Box(40, 20, 15)
blk = fillet(blk.edges().filter_by(Axis.Z), radius=3)
part = blk - Rot(0, 90, 0) * Cylinder(3, 50)
v0 = part.volume
bb0 = part.bounding_box()
check("solid_valid", part.is_valid, f"vol={v0:.3f} mm3 faces={len(part.faces())}")

# 2. exports
step_p, stl_p, mf_p = out / "test.step", out / "test.stl", out / "test.3mf"
export_step(part, str(step_p))
export_stl(part, str(stl_p), tolerance=0.01, angular_tolerance=0.1)
m = Mesher(unit=Unit.MM)
m.add_shape(part, linear_deflection=0.01, angular_deflection=0.1)
m.write(str(mf_p))
check("exports_exist", all(p.stat().st_size > 0 for p in (step_p, stl_p, mf_p)),
      f"step={step_p.stat().st_size}B stl={stl_p.stat().st_size}B 3mf={mf_p.stat().st_size}B")

# 3. re-import STEP
rs = import_step(str(step_p))
bb1 = rs.bounding_box()
dv = abs(rs.volume - v0) / v0
dbb = max(abs(a - b) for a, b in zip(tuple(bb0.min) + tuple(bb0.max), tuple(bb1.min) + tuple(bb1.max)))
check("step_roundtrip", dv < 1e-6 and dbb < 1e-6, f"dV/V={dv:.2e} dBB={dbb:.2e} mm")

# 4. re-import 3MF (mesh -> volume is slightly smaller on curved faces)
r3 = Mesher().read(str(mf_p))
vol3 = sum(s.volume for s in r3)
bb3 = r3[0].bounding_box()
dv3 = abs(vol3 - v0) / v0
dbb3 = max(abs(a - b) for a, b in zip(tuple(bb0.min) + tuple(bb0.max), tuple(bb3.min) + tuple(bb3.max)))
check("3mf_roundtrip", dv3 < 2e-3 and dbb3 < 0.02, f"dV/V={dv3:.2e} dBB={dbb3:.2e} mm")

# 5. STL via trimesh (watertight + volume)
import trimesh
tm = trimesh.load(str(stl_p))
check("stl_watertight", tm.is_watertight and abs(tm.volume - v0) / v0 < 2e-3,
      f"watertight={tm.is_watertight} vol={tm.volume:.3f}")

# 6. clearance / interference checks
a = Box(10, 10, 10)
b_hit = Pos(9, 0, 0) * Box(10, 10, 10)      # 1 mm overlap
b_gap = Pos(10.5, 0, 0) * Box(10, 10, 10)   # 0.5 mm gap
inter = (a & b_hit).volume
inter0 = (a & b_gap).volume if (a & b_gap) is not None else 0.0
gap = a.distance_to(b_gap)
check("interference_detect", abs(inter - 100.0) < 1e-6 and inter0 < 1e-9 and abs(gap - 0.5) < 1e-9,
      f"overlap_vol={inter:.3f} (exp 100) noTouchVol={inter0} gap={gap:.3f} (exp 0.5)")

(out / "cad_selftest.json").write_text(json.dumps(results, indent=2))
print("outdir:", out, "ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
