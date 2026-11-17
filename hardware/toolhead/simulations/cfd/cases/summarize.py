#!/usr/bin/env python3
"""Rebuild simulations/cfd/results/summary.{csv,json} from every results/<case>/results.json."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1] / "results"
STOCK_DUCT_G = 2646.7e-3 * 1.20     # Henlor "Creality K1 Fan Duct v5" volume x PC-ish density (comparison only)


def _g(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def row(res, dirname=None):
    sp = res.get("_spec", {})
    r = {"case": dirname or res["case"], "design": sp.get("design"), "env": sp.get("env"), "curve": sp.get("curve"),
         "tag": sp.get("tag"), "level": res.get("level"), "cells": _g(res, "mesh", "cells"),
         "iterations": _g(res, "convergence", "iterations"), "converged": _g(res, "convergence", "converged"),
         "wall_min": round((_g(res, "timing_s", "mesh_solve_post_total") or 0) / 60, 1),
         "mass_imbalance": _g(res, "mass_balance", "imbalance_rel")}
    qt = 0.0
    for name, d in sorted(res.get("inlets", {}).items()):
        f = name.replace("inlet_", "")
        r[f"Q_{f}_Lps"] = round(d["Q_m3_s"] * 1e3, 4)
        r[f"dP_{f}_Pa"] = round(d.get("fan_dP_at_Q_Pa", float("nan")), 1)
        r[f"QfracMax_{f}"] = round(_g(d, "operating_point", "fraction_of_Qmax") or float("nan"), 3)
        qt += d["Q_m3_s"]
    r["Q_total_Lps"] = round(qt * 1e3, 4)
    r["Q_total_cfm"] = round(qt / 4.719474e-4, 3)
    pl = res.get("planes", {})
    an = pl.get("layer_annulus", {})
    if "sector_Umag_mean" in an:
        sec = [x for x in an["sector_Umag_mean"] if x == x]
        mean = an["Umag_mean_area"]
        r["ann_U_mean"] = round(mean, 3)
        r["ann_U_minsector"] = round(min(sec), 3)
        r["ann_min_over_mean"] = round(min(sec) / mean, 3)
        r["ann_cv"] = round(an["symmetry_cv"], 3)
        r["ann_sectors"] = " ".join(f"{x:.2f}" for x in an["sector_Umag_mean"])
    a3 = pl.get("annulus_z03", {})
    if "sector_Umag_mean" in a3:
        sec = [x for x in a3["sector_Umag_mean"] if x == x]
        r["ann03_U_mean"] = round(a3["Umag_mean_area"], 3)
        r["ann03_U_minsector"] = round(min(sec), 3)
        r["ann03_min_over_mean"] = round(min(sec) / a3["Umag_mean_area"], 3)
        r["ann03_cv"] = round(a3["symmetry_cv"], 3)
        r["ann03_sectors"] = " ".join(f"{x:.2f}" for x in a3["sector_Umag_mean"])
    rz = pl.get("ring_z1", {})
    if "Umag_mean_area" in rz:
        r["ring1_U_mean"] = round(rz["Umag_mean_area"], 3)
        sec = [x for x in rz.get("sector_Umag_mean", []) if x == x]
        if sec:
            r["ring1_min_over_mean"] = round(min(sec) / rz["Umag_mean_area"], 3)
    wr = res.get("wall_regions", {})
    for k, short in (("part_top_r5", "top5"), ("part_top_r10", "top10"), ("nozzle_cone", "cone"),
                     ("nozzle_all", "nozzle"), ("sock_bottom", "sockbot")):
        if k in wr:
            r[f"{short}_wss_Pa"] = round(wr[k].get("wss_mean_Pa", float("nan")), 4)
            r[f"{short}_Unear"] = round(wr[k].get("Unear_mean", float("nan")), 3)
    sides = [wr[k] for k in wr if k.startswith("part_side_")]
    if sides:
        A = sum(s["area_mm2"] for s in sides)
        r["side3_wss_Pa"] = round(sum(s.get("wss_mean_Pa", 0) * s["area_mm2"] for s in sides) / A, 4)
        r["side3_Unear"] = round(sum(s.get("Unear_mean", 0) * s["area_mm2"] for s in sides) / A, 3)
        r["side3_Unear_min"] = round(min(s.get("Unear_mean", 0) for s in sides), 3)
        r["side3_Unear_by_face"] = " ".join(f"{k.split('_')[2]}:{wr[k].get('Unear_mean', 0):.2f}"
                                            for k in sorted(wr) if k.startswith("part_side_"))
        for k in wr:                                   # per-face columns (review R-11)
            if k.startswith("part_side_"):
                fc = k.split("_")[2]
                r[f"side_{fc}_Unear"] = round(wr[k].get("Unear_mean", float("nan")), 3)
                r[f"side_{fc}_wss_Pa"] = round(wr[k].get("wss_mean_Pa", float("nan")), 4)
    for k in ("lidar_line", "lidar_window"):
        if "Umag_mean_area" in pl.get(k, {}):
            r[f"{k}_U_mean"] = round(pl[k]["Umag_mean_area"], 3)
            r[f"{k}_U_max"] = round(pl[k]["Umag_max"], 3)
    ports = {k: v for k, v in pl.items() if k.startswith("port_")}
    if ports:
        qs = {k: v.get("Q_through_m3_s", 0.0) for k, v in ports.items()}
        tot = sum(qs.values()) or float("nan")
        r["port_split_pct"] = " ".join(f"{k[5:]}:{100 * q / tot:.0f}" for k, q in qs.items())
        r["port_Q_sum_Lps"] = round(tot * 1e3, 4)
        r["port_U_flux_mean"] = round(sum(v.get("Umag_mean_flux", 0) * qs[k] for k, v in ports.items()) / tot, 2)
    losses = res.get("losses", {})
    fl = {k: v["dp_total_Pa"] for k, v in losses.items() if "->feed_" in k}
    if fl:
        r["dp0_inlet_to_feed_Pa"] = " ".join(f"{k.split('->')[1]}:{v:.1f}" for k, v in fl.items())
    pls = {k: v["dp_total_Pa"] for k, v in losses.items() if "->port_" in k}
    if pls:
        r["dp0_inlet_to_ports_Pa"] = " ".join(f"{k.split('->')[1][5:]}:{v:.0f}" for k, v in pls.items())
    geo = res.get("_geometry", {})
    m = geo.get("mass", {})
    if "mass_all_PC_g" in m:
        r["duct_mass_PC_g"] = m["mass_all_PC_g"]
        r["fans_g"] = m["fans_g"]
        r["delta_mass_vs_stock_g"] = round(m["mass_all_PC_g"] + m["fans_g"] - (STOCK_DUCT_G + 24.0), 1)
        r["outlet_area_mm2"] = geo.get("outlet_area_total_mm2")
    elif sp.get("design") == "STOCK":
        r["duct_mass_PC_g"] = round(STOCK_DUCT_G, 2)
        r["fans_g"] = 24.0
        r["delta_mass_vs_stock_g"] = 0.0
    th = res.get("thermal", {})
    if th:
        r["thermal_method"] = th.get("method", "restart")
        r["thermal_balance_err"] = round(_g(th, "balance", "rel_error") or float("nan"), 4)
        r["thermal_status"] = th.get("status", "proxy, energy balance unclosed"
                                     if abs(_g(th, "balance", "rel_error") or 1) > 0.05 else "balance closed")
    for k, v in th.get("regions", {}).items():
        if "h_mean_W_m2K" in v:
            r[f"h_{k}"] = round(v["h_mean_W_m2K"], 1)
        if "Q_W" in v:
            r[f"Qheat_{k}_W"] = round(v["Q_W"], 3)
    return r


def main():
    rows = []
    for f in sorted(RESULTS.glob("*/results.json")):
        try:
            rows.append(row(json.loads(f.read_text()), f.parent.name))
        except Exception as e:  # noqa: BLE001
            print("skip", f, e)
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(RESULTS / "summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    (RESULTS / "summary.json").write_text(json.dumps(rows, indent=1, default=float))
    return rows


if __name__ == "__main__":
    for r in main():
        print({k: r[k] for k in r if k in ("case", "Q_total_Lps", "ann_U_mean", "ann_min_over_mean", "cone_Unear")})
