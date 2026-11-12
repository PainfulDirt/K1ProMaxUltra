#!/usr/bin/env python3
"""Markdown tables for documentation/cfd-report.md from results/summary.json (keeps the report consistent).

    $K1_PY report_tables.py [main|ops|walls|split|mesh|thermal|all]
"""
import json
import sys
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / "results"


def load():
    return {r["case"]: r for r in json.loads((RES / "summary.json").read_text())}


def f(v, n=2):
    if v is None or v == "" or (isinstance(v, float) and v != v):
        return "–"
    if isinstance(v, float):
        return f"{v:.{n}f}"
    return str(v)


def rel(r, base, k):
    try:
        return f"{100 * (r[k] / base[k] - 1):+.0f} %"
    except Exception:
        return "–"


def table(rows, cols, title=None):
    out = [f"**{title}**", ""] if title else []
    out.append("| " + " | ".join(c[0] for c in cols) + " |")
    out.append("|" + "---|" * len(cols))
    for r in rows:
        out.append("| " + " | ".join(c[1](r) for c in cols) + " |")
    return "\n".join(out)


def main(which="all", cases=None):
    S = load()
    rows = [S[c] for c in (cases or S) if c in S and S[c].get("env") == "part" and S[c].get("level") == 2
            and not c.endswith("_thermal")]
    rows.sort(key=lambda r: (r["design"] != "STOCK", r["curve"], r["design"]))
    base = {cv: next((r for r in rows if r["design"] == "STOCK" and r["curve"] == cv), None)
            for cv in ("proxy", "estimated")}
    out = []
    if which in ("main", "all"):
        cols = [("case", lambda r: r["case"].replace("_part", "").replace("_L2", "")),
                ("Q tot [L/s]", lambda r: f(r.get("Q_total_Lps"), 3)),
                ("ann Z−0.1 mean", lambda r: f(r.get("ann_U_mean"))),
                ("ann Z+0.3 mean [m/s]", lambda r: f(r.get("ann03_U_mean"))),
                ("min sector", lambda r: f(r.get("ann03_U_minsector"))),
                ("min/mean", lambda r: f(r.get("ann03_min_over_mean"))),
                ("CV", lambda r: f(r.get("ann03_cv"))),
                ("ring r4–10 Z1", lambda r: f(r.get("ring1_U_mean"))),
                ("top r≤5 U0.3 / τw", lambda r: f"{f(r.get('top5_Unear'))} / {f(r.get('top5_wss_Pa'), 3)}"),
                ("top r≤10 U0.3 / τw", lambda r: f"{f(r.get('top10_Unear'))} / {f(r.get('top10_wss_Pa'), 3)}"),
                ("sides top3 U0.3 (min face)", lambda r: f"{f(r.get('side3_Unear'))} ({f(r.get('side3_Unear_min'))})"),
                ("cone U0.3 / τw", lambda r: f"{f(r.get('cone_Unear'))} / {f(r.get('cone_wss_Pa'), 3)}"),
                ("sock bottom U0.3", lambda r: f(r.get("sockbot_Unear"))),
                ("Δmass vs stock [g]", lambda r: f(r.get("delta_mass_vs_stock_g"), 1))]
        out.append(table(rows, cols, "Near-nozzle metrics (iteration-averaged fields; m/s unless noted; τw in Pa)"))
        cols2 = [("case", lambda r: r["case"].replace("_part", "").replace("_L2", "")),
                 ("ann Z+0.3 vs STOCK same curve", lambda r: rel(r, base.get(r["curve"]) or base["proxy"], "ann03_U_mean")),
                 ("top r≤5 U vs STOCK", lambda r: rel(r, base.get(r["curve"]) or base["proxy"], "top5_Unear")),
                 ("cone U vs STOCK", lambda r: rel(r, base.get(r["curve"]) or base["proxy"], "cone_Unear")),
                 ("ann sectors Z+0.3 (0°,45°,…,315°)", lambda r: r.get("ann03_sectors", "–"))]
        out.append("")
        out.append(table(rows, cols2, "Relative to STOCK at the same 4020 curve bound (5015 cases vs STOCK lower bound)"))
    if which in ("ops", "all"):
        cols = [("case", lambda r: r["case"].replace("_part", "").replace("_L2", "")),
                ("fan op. point Q [L/s] / ΔP [Pa]", lambda r: " ; ".join(
                    f"{k[2:-4]}: {f(r[k], 3)} / {f(r.get('dP_' + k[2:-4] + '_Pa'), 0)}" for k in r if k.startswith("Q_") and k.endswith("_Lps") and k != "Q_total_Lps")),
                ("Q/Qmax", lambda r: " ; ".join(f(r[k]) for k in r if k.startswith("QfracMax_"))),
                ("outlet area [mm²]", lambda r: f(r.get("outlet_area_mm2"), 0)),
                ("port Σ Q [L/s]", lambda r: f(r.get("port_Q_sum_Lps"), 3)),
                ("jet flux-mean U [m/s]", lambda r: f(r.get("port_U_flux_mean"))),
                ("split % per port", lambda r: r.get("port_split_pct", "–")),
                ("Δp₀ inlet→feed / →ports [Pa]", lambda r: f"{r.get('dp0_inlet_to_feed_Pa', '–')} | {r.get('dp0_inlet_to_ports_Pa', '–')}"),
                ("LiDAR line / window U [m/s]", lambda r: f"{f(r.get('lidar_line_U_mean'), 3)} / {f(r.get('lidar_window_U_mean'), 3)}"),
                ("cells", lambda r: f"{(r.get('cells') or 0) / 1e6:.2f} M"),
                ("iter", lambda r: f(r.get("iterations"))),
                ("wall min", lambda r: f(r.get("wall_min"), 0))]
        out.append("")
        out.append(table(rows, cols, "Fan operating points, flow split, losses, LiDAR region, run statistics"))
    if which in ("mesh",):
        sel = [r for r in S.values() if r.get("tag") in ("", None) and r["case"].startswith(cases[0] if cases else "")
               and not r["case"].endswith("_thermal")]
        sel.sort(key=lambda r: r["level"])
        keys = ["ann03_U_mean", "ann03_U_minsector", "ann03_min_over_mean", "ring1_U_mean", "top5_Unear",
                "top10_Unear", "side3_Unear", "cone_Unear", "sockbot_Unear", "top5_wss_Pa", "cone_wss_Pa",
                "Q_total_Lps"]
        out.append("| metric | " + " | ".join(f"L{r['level']} ({(r['cells'] or 0) / 1e6:.2f} M)" for r in sel)
                   + " | L2→L3 | GCI-type 1.25·|Δ| |")
        out.append("|---|" + "---|" * (len(sel) + 2))
        for k in keys:
            vals = [r.get(k) for r in sel]
            d = ""
            g = ""
            if len(sel) >= 3 and vals[1] and vals[2]:
                d = f"{100 * (vals[2] / vals[1] - 1):+.1f} %"
                g = f"{125 * abs(vals[2] / vals[1] - 1):.1f} %"
            out.append(f"| {k} | " + " | ".join(f(v, 3) for v in vals) + f" | {d} | {g} |")
    if which in ("thermal",):
        T = [r for r in S.values() if r["case"].endswith("_thermal")]
        cols = [("case", lambda r: r["case"].replace("_part", "").replace("_L2_thermal", "")),
                ("h top r≤5", lambda r: f(r.get("h_part_top_r5"), 0)),
                ("h top r≤10", lambda r: f(r.get("h_part_top_r10"), 0)),
                ("h sides top 3 mm (+X/−X/+Y/−Y)", lambda r: "/".join(f(r.get(f"h_part_side_{k}_top3"), 0) for k in ("xp", "xm", "yp", "ym"))),
                ("Q part top+sides [W]", lambda r: f((r.get("Qheat_part_top_patch_W") or 0) + (r.get("Qheat_part_side_patch_W") or 0), 2)),
                ("h nozzle / cone", lambda r: f"{f(r.get('h_nozzle_all'), 0)} / {f(r.get('h_nozzle_cone'), 0)}"),
                ("Q nozzle [W]", lambda r: f(r.get("Qheat_nozzle_patch_W"), 3)),
                ("h sock bottom", lambda r: f(r.get("h_sock_bottom"), 0)),
                ("Q sock [W]", lambda r: f(r.get("Qheat_sock_patch_W"), 2))]
        out.append(table(T, cols, "Thermal proxy (W/m²K unless noted; part 200 °C, nozzle 250 °C, sock 150 °C, air 45 °C)"))
    return "\n".join(out)


if __name__ == "__main__":
    print(main(sys.argv[1] if len(sys.argv) > 1 else "all", sys.argv[2:] or None))
