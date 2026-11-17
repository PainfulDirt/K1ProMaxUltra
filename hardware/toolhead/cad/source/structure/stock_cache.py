"""Stock-geometry cache from Henlor's reverse-engineered K1 assembly (Printables
742370, CC BY 4.0, "non-official, some inaccuracies").

The third-party solids are NEVER written into the repository: they are cached
as STEP outside it (default: $K1TH_STOCK_CACHE, else the session scratchpad)
and only validate.py reads them, for real-solid interference checks. Exports use
the box references from interfaces.py.

Regenerate (once, ~2 min, 205 MB input):
    python -I cad/source/structure/stock_cache.py <henlor.step> [<outdir>]
The shift to the nozzle frame is interfaces.HENLOR_TO_NOZZLE.
"""
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_CACHE = os.environ.get(
    "K1TH_STOCK_CACHE",
    "/tmp/claude-0/-home-user-K1ProMaxUltra/1fc00b30-b973-54a8-8106-390cde6c1256/scratchpad/cadcache/henlor_nozzle_frame")

from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_Label
from OCP.collections import Sequence_TDF_Label as Seq
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.gp import gp_Trsf, gp_Vec
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from build123d import Compound, export_step, import_step, Box, Pos

SEL = {  # output name -> substring of the assembly path
    "carriage": "X-carriage:1/X-Carriage:1",
    "belt_retainer_1": "X-carriage:1/belt-retainer:1",
    "belt_retainer_2": "X-carriage:1/belt-retainer:2",
    "bushing_1": "X-carriage:1/SL Brass Bearing 12-14 45mm:1",
    "bushing_2": "X-carriage:1/SL Brass Bearing 12-14 45mm:2",
    "cable_strain_relief": "Cable strain relief:1/=>",
    "heatsink": "K1 Hotend:1/=>[0:1:1:222]",
    "fan3010": "DC fan 3010 v3:2/Component1:1",
    "pcb": "toolhead-PCB:1/=>",
    "extruder_cover_inner": "K1 extruder:1/extruder-cover:1/=>",
    "extruder_main_plate": "K1 extruder:1/main-plate:1/=>",
    "extruder_bracket": "K1 extruder:1/metal braket:1/=>",
    "extruder_motor": "MOONS CSE14HRA2L410A-01:1/=>",
    "extruder_top_cover": "K1Toolhead v66:1/Extruder cover v5:1",
    "cable_chain_end": "cable-chain_toolhead-end v2:1",
    "x_rod_1": "Hollow Linear rod 10 x 302.5 mm v3:1",
    "x_rod_2": "Hollow Linear rod 10 x 302.5 mm v3:2",
}

def extract(path, outdir, d):
    os.makedirs(outdir, exist_ok=True)
    doc = TDocStd_Document(TCollection_ExtendedString("doc"))
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    r.ReadFile(path)
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    tr = gp_Trsf()
    tr.SetTranslation(gp_Vec(*d))


    def name(lab):
        a = TDataStd_Name()
        return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"


    found = {}


    def walk(lab, loc, pn):
        nm = name(lab)
        ref = TDF_Label()
        if st.IsReference_s(lab):
            st.GetReferredShape_s(lab, ref)
            loc = loc.Multiplied(st.GetLocation_s(lab))
            tgt = ref
        else:
            tgt = lab
        pn = pn + [nm]
        if st.IsAssembly_s(tgt):
            cs = Seq()
            st.GetComponents_s(tgt, cs, False)
            for i in range(1, cs.Length() + 1):
                walk(cs.Value(i), loc, pn)
            return
        p = "/".join(pn)
        for key, sub in SEL.items():
            if sub in p and key not in found:
                shp = BRepBuilderAPI_Transform(st.GetShape_s(tgt).Moved(loc), tr, True).Shape()
                found[key] = (p, shp)


    fr = Seq()
    st.GetFreeShapes(fr)
    for i in range(1, fr.Length() + 1):
        walk(fr.Value(i), TopLoc_Location(), [])

    man = {}
    for key, (p, shp) in found.items():
        c = Compound(shp)
        if key.startswith("x_rod"):
            c = c & Pos(0, 0, 0) * Box(140, 400, 400)       # keep X +-70 around the toolhead
        bb = c.bounding_box()
        fn = os.path.join(outdir, key + ".step")
        export_step(c, fn)
        man[key] = {"path": p, "file": os.path.basename(fn), "volume": round(c.volume, 1),
                    "bbox": [round(v, 2) for v in (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)]}
        print(key, man[key]["volume"], man[key]["bbox"])
    missing = sorted(set(SEL) - set(found))
    man["_meta"] = {"source": "Henlor, Printables 742370, CC BY - DO NOT COMMIT", "shift": d, "missing": missing}
    json.dump(man, open(os.path.join(outdir, "manifest.json"), "w"), indent=1)
    print("missing:", missing)



def load_stock_solids(cache_dir=None):
    """{name: Solid/Compound} from the cache, or {} if absent."""
    p = Path(cache_dir or DEFAULT_CACHE)
    man = p / "manifest.json"
    if not man.exists():
        return {}
    m = json.loads(man.read_text())
    out = {}
    for k, v in m.items():
        if k.startswith("_"):
            continue
        f = p / v["file"]
        if f.exists():
            sols = import_step(str(f)).solids()      # plain solids: booleans on imported XCAF
            if sols:                                 # compounds use stale children
                out[k] = sols[0] if len(sols) == 1 else Compound(list(sols))

    return out


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import interfaces as I
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CACHE, I.HENLOR_TO_NOZZLE)
