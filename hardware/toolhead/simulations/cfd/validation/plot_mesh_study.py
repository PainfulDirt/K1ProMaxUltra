#!/usr/bin/env python3
"""Mesh-sensitivity summary for the validation study: reads results/validation_summary.json,
computes the Celik et al. (2008) / Roache Grid Convergence Index on the three flow-rate levels,
writes results/mesh_study.json and results/mesh_study.png."""
import json
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
S = json.loads((HERE / "results/validation_summary.json").read_text())
runs = sorted([k for k in S if k.startswith("val_flowrate_L")], key=lambda k: S[k]["cells"])
METRICS = {"slot_U_mean_flux": "slot exit flux-weighted mean |U| [m/s]",
           "annulus_Umag_mean": "annulus (r<5 mm, z=-0.5) mean |U| [m/s]",
           "p_total_inlet_Pa": "inlet total pressure = system dP [Pa]",
           "dp_total_inlet_to_slot_Pa": "duct total-pressure loss [Pa]"}


def gci(f1, f2, f3, r21, r32, Fs=1.25):
    """f1 = finest. Returns (p_observed, f_extrapolated, GCI_fine) or Nones if oscillatory."""
    e21, e32 = f2 - f1, f3 - f2
    if e21 == 0 or e32 == 0 or e21 * e32 < 0:
        return None, None, abs(e21 / f1) * Fs if f1 else None   # oscillatory: report |e21| bound
    s = np.sign(e32 / e21)
    p = 1.0
    for _ in range(100):
        q = math.log((r21 ** p - s) / (r32 ** p - s))
        p = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
    fext = (r21 ** p * f1 - f2) / (r21 ** p - 1)
    return p, fext, Fs * abs(e21 / f1) / (r21 ** p - 1)


out = {"runs": runs, "cells": [S[k]["cells"] for k in runs], "metrics": {}}
if len(runs) == 3:
    N3, N2, N1 = out["cells"]
    r21, r32 = (N1 / N2) ** (1 / 3), (N2 / N3) ** (1 / 3)
    out["r21"], out["r32"] = r21, r32
    for m in METRICS:
        f3, f2, f1 = [S[k][m] for k in runs]
        p, fext, g = gci(f1, f2, f3, r21, r32)
        out["metrics"][m] = {"values_coarse_to_fine": [f3, f2, f1], "p_observed": p,
                             "extrapolated": fext, "GCI_fine": g,
                             "change_L2_to_L3_rel": (f1 - f2) / f2, "change_L1_to_L2_rel": (f2 - f3) / f3}

fig, axs = plt.subplots(1, len(METRICS), figsize=(13, 3.2))
h = [(1.0 / n) ** (1 / 3) * 1e2 for n in out["cells"]]
for ax, (m, lab) in zip(axs, METRICS.items()):
    ax.plot(h, [S[k][m] for k in runs], "o-", color="#2a78d6", lw=2, ms=6)
    for hi, k in zip(h, runs):
        ax.annotate(k[-2:], (hi, S[k][m]), textcoords="offset points", xytext=(4, 4), fontsize=8, color="#52514e")
    fx = out["metrics"].get(m, {}).get("extrapolated")
    if fx is not None:
        ax.axhline(fx, color="#8a8984", ls="--", lw=1)
        ax.annotate("Richardson extrap.", (min(h), fx), textcoords="offset points", xytext=(0, 4), fontsize=7, color="#52514e")
    ax.set_title(lab, fontsize=8, loc="left")
    ax.set_xlabel("h ~ N^(-1/3) (x100)")
    ax.grid(True, color="#e6e6e3")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
fig.suptitle("Validation duct, fixed Q = 0.45 L/s: mesh sensitivity", x=0.01, ha="left", fontsize=10)
fig.tight_layout()
fig.savefig(HERE / "results/mesh_study.png", dpi=110)
(HERE / "results/mesh_study.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=1))
