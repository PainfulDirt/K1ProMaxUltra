#!/usr/bin/env python3
"""Pre-CFD fan operating-point estimate for the K1 Max custom toolhead.

PRE-CFD ESTIMATE ONLY. Fan curves here are anchored on published end points
(max free-air flow and max static pressure); the shape between the end points is
a generic shape (ESTIMATED) because no manufacturer P-Q curve could be opened
or digitised (see documentation/research/03-fans-and-cooling.md, section 1).

What it does
  1. Writes one P-Q CSV per fan to pq-curves/<model>.csv
     (columns Q_m3_per_s,dP_Pa; '#' metadata lines first; the first line says
     how many header lines to skip -> OpenFOAM csv `nHeaderLine`).
  2. Intersects each fan curve with duct system curves dP = K*Q^2
     (low / medium / high resistance) for configurations A, B, C, D and prints
     delivered flow and outlet velocity as a Markdown table.
  3. Optionally plots everything to pq-curves/pq_operating_points.png.

Usage
  python3 operating_point.py              # CSVs + tables (numpy only)
  python3 operating_point.py --plot       # also the PNG (needs matplotlib)
  python3 operating_point.py --no-csv     # tables only

Units: SI. 1 CFM = 4.719e-4 m^3/s, 1 inH2O = 249.09 Pa, 1 mmH2O = 9.80665 Pa.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

CFM = 4.719e-4          # m^3/s per CFM
INH2O = 249.09          # Pa per inH2O
MMH2O = 9.80665         # Pa per mmH2O
RHO = 1.20              # kg/m^3, air at ~20 C (see note on density below)
NU = 1.6e-5             # m^2/s, kinematic viscosity of air at ~30 C

HERE = Path(__file__).resolve().parent
OUT = HERE / "pq-curves"

# --------------------------------------------------------------------------
# Generic normalised curve shapes  p/pmax = f(q/qmax)   (ESTIMATED)
# --------------------------------------------------------------------------
X = np.linspace(0.0, 1.0, 11)
SHAPES = {
    # small radial/forward-curved 50xx/40xx blower: shallow near shut-off,
    # roughly linear in the middle, steeper toward free delivery
    "blower": np.array([1.00, 0.97, 0.92, 0.85, 0.77, 0.68, 0.58, 0.47, 0.34, 0.18, 0.00]),
    # small tube-axial fan: steep drop leaving shut-off, stall saddle at
    # 20-50 % flow, then near-linear to free delivery
    "axial": np.array([1.00, 0.86, 0.76, 0.70, 0.66, 0.61, 0.53, 0.43, 0.30, 0.16, 0.00]),
    # high-speed BLDC (CPAP) blower: flat at low flow, falling faster at high flow
    "cpap": np.array([1.00, 0.99, 0.97, 0.93, 0.87, 0.79, 0.69, 0.57, 0.42, 0.23, 0.00]),
}


@dataclass
class Fan:
    key: str                 # CSV file stem
    name: str
    kind: str                # blower / axial / cpap
    qmax: float              # m^3/s, free air
    pmax: float              # Pa, shut-off
    q_src: str
    p_src: str
    q_status: str
    p_status: str
    sources: list[str] = field(default_factory=list)
    notes: str = ""
    pmax_range: tuple[float, float] | None = None   # Pa, for sensitivity

    def curve(self, pmax: float | None = None):
        p = (self.pmax if pmax is None else pmax) * SHAPES[self.kind]
        return X * self.qmax, p

    def dp(self, q, pmax: float | None = None):
        qq, pp = self.curve(pmax)
        return np.interp(q, qq, pp, right=0.0)


FANS = [
    Fan("sunon_MF50152VX-1L02C-A99", "Sunon MF50152VX-1L02C-A99 (5015 blower, 24 V, owned)",
        "blower", 4.8 * CFM, 0.76 * INH2O,
        "4.8 CFM", "0.76 inH2O", "SECONDARY", "SECONDARY",
        ["https://3dandy.com/product/1642/sunon-5015-195w-24v-blower-fan-2pin-mf50152vx-1l02c-a99",
         "https://www.newegg.com/lemincrash-mf50152vx-1l02c-a99/p/2S7-09CJ-00003",
         "https://www.ebay.com/itm/364477240013"],
        "Reseller spec (24 V, 70/81 mA, 1.95 W, 6000 rpm, 43.8 dBA, 28.37 g, 2-pin). "
        "No Sunon datasheet for the -1L02C suffix was found. Sibling 12 V blower "
        "MF50151VX-1B00U-A99 (Sunon sheet copy at fansco.com) lists 5.4 CFM / 0.97 inH2O, so the "
        "true curve may be higher.",
        (0.76 * INH2O, 0.97 * INH2O)),
    Fan("sunon_MF40202VX-1000U-G99", "Sunon MF40202VX-1000U-G99 (4020 axial, 24 V, owned)",
        "axial", 10.8 * CFM, 0.290 * INH2O,
        "10.8 CFM (0.302 m3/min)", "0.290 inH2O (72.2 Pa)", "SECONDARY", "SECONDARY",
        ["https://www.digikey.com/en/products/detail/sunon-fans/MF40202VX-1000U-G99/7927786",
         "https://www.chipsfind.com/part-item/01750959-MF40202VX-1000U-G99",
         "https://www.soselectronic.com/en-us/products/sunon/mf40202vx-1000u-g99-375391"],
        "Distributor listing of Sunon data (24 V, 39 mA, 0.94 W, 8000 rpm, 27.5 dBA, Vapo, 3 wires "
        "with tach). Tube-axial: unsuitable as a ducted part fan, intended here as hotend fan.",
        None),
    Fan("creality_K1_stock_4020_blower", "Creality K1/K1 Max stock 4020 blower (24 V 0.3 A, 12000 rpm)",
        "blower", 6.4 * CFM, 390.0,
        "6.4 CFM (retailer, K1C 4020 listing)",
        "~390 Pa ESTIMATED by fan affinity from GDSTIME GDB4020 (6500 rpm, 0.46 inH2O) scaled to 12000 rpm",
        "SECONDARY", "ESTIMATED",
        ["https://3dprintingcanada.com/products/official-creality-k1c-4020-blower-fan",
         "https://www.digitec.ch/en/s1/product/creality-4020-blower-fan-filament-cooling-for-k1c-and-k1-max-3d-printer-accessories-47334487",
         "https://3dprintingcanada.com/products/official-creality-k1-k1-max-4020-blower-fan",
         "https://3dprintingcanada.com/products/gdstime-4020-24v-premium-fan-with-ball-bearing"],
        "No manufacturer data exists publicly (retailer type code CHT4024BY-W20C, unconfirmed). "
        "Max pressure is NOT published: 0.46 inH2O * (12000/6500)^2 = 391 Pa. Affinity check on flow: "
        "3.67 CFM * 12000/6500 = 6.8 CFM, consistent with the 6.4 CFM listing. Uncertainty band "
        "250-500 Pa. Measure before trusting.",
        (250.0, 500.0)),
    Fan("delta_BFB0524HH", "Delta BFB0524HH (5015 blower, 24 V, ball)",
        "blower", 4.59 * CFM, 0.866 * INH2O,
        "4.59 CFM (0.130 m3/min)", "0.866 inH2O (22.00 mmH2O, 215.7 Pa)", "SECONDARY", "SECONDARY",
        ["https://www.delta-fan.com/products/BFB0524HH-F00.html",
         "https://www.fansco.com/uploads/2024/01/BFB0524HH-Delta.pdf",
         "https://www.mouser.com/en/ProductDetail/Delta-Electronics/BFB0524HH-F00"],
        "Delta product page / Delta spec copy (24 V, 0.11 A typ, 0.16 A max, 2.64 W, 6500 rpm, "
        "45 dBA, 28.1 g). Values read through a search-engine extract; the PDF itself could not "
        "be opened from this environment (network policy), hence SECONDARY not VERIFIED.",
        None),
    Fan("gdstime_GDB5015_24V", "GDSTIME GDB5015 24 V (5015 blower, dual ball, 6000 rpm)",
        "blower", 5.36 * CFM, 0.79 * INH2O,
        "5.36 CFM (most retailers)", "0.79 inH2O (low end of retailer range 0.79-1.21)", "SECONDARY", "SECONDARY",
        ["https://www.hotend.eu/p/gdstime-radial-fan-blower-5015-24v-dual-ball",
         "https://3dprintingusa.com/products/gdstime-5015-24v-premium-blower-fan-with-ball-bearing",
         "https://kb-3d.com/store/fans/310-5015-ball-bearing-blower-fan-24v.html"],
        "Retailer figures conflict (4.42-5.36 CFM; 0.79-1.21 inH2O). Low pressure used as nominal.",
        (0.79 * INH2O, 1.21 * INH2O)),
    Fan("wonsmart_WS7040-24-V200", "Wonsmart WS7040-24-V200 CPAP blower (+ WS2403 driver)",
        "cpap", 14.7 * CFM, 6600.0,
        "14.7 CFM (BTT wiki); Wonsmart pages 22-25.5 m3/h", "6.6 kPa (BTT wiki); Wonsmart pages 6.5 kPa",
        "SECONDARY", "SECONDARY",
        ["https://bttwiki.com/Universal%20Turbo%20Kit.html",
         "https://www.wonsmartmotor.com/blog/wonsmart-ws7040-24-v200-specifications-and-benefits/",
         "https://www.wonsmartblower.com/medical-blower/24v-high-pressure-6-5kpa-low-noise-65dba-mini.html"],
        "Needs its own BLDC driver (WS2403DY01V04, 9-29 V, 0-5 V or PWM speed input), up to ~2.7 A "
        "at 24 V (supplier page). Mounted off the toolhead, fed through a hose.",
        (6500.0, 6600.0)),
]
FAN = {f.key: f for f in FANS}


# --------------------------------------------------------------------------
# System (duct) curves   dP = K Q^2,  K = sum(zeta) * rho / (2 A_out^2)
# zeta values are all referred to the OUTLET velocity.
# --------------------------------------------------------------------------
@dataclass
class Duct:
    name: str
    a_out: float      # m^2 total outlet area
    zeta: float       # sum of loss coefficients referred to outlet velocity
    detail: str

    @property
    def K(self):
        return self.zeta * RHO / (2.0 * self.a_out ** 2)


DUCTS = [
    Duct("low", 120e-6, 1.4,
         "A_out 120 mm2 (2 x 60 mm2); exit 1.0 + contraction 0.1 + bends 0.2 + friction 0.1"),
    Duct("medium", 80e-6, 2.2,
         "A_out 80 mm2 (2 x 40 mm2); exit 1.0 + contraction 0.3 + bends 0.5 + friction 0.4"),
    Duct("high", 50e-6, 3.5,
         "A_out 50 mm2 (2 x 25 mm2); exit 1.0 + contraction 0.5 + bends 1.0 + friction 1.0"),
]

# hotend heat-sink: dP = K_hs Q^2, ESTIMATED; medium = 25 Pa at 2 CFM through the fins
K_HS = {"low": 12.5 / (2 * CFM) ** 2, "medium": 25.0 / (2 * CFM) ** 2, "high": 50.0 / (2 * CFM) ** 2}

# CPAP hose (configuration D): 15 mm ID, 1.5 m, plus fittings zeta 1.5 on hose velocity
HOSE_D, HOSE_L, HOSE_ZETA = 0.015, 1.5, 1.5


def hose_dp(q):
    a = math.pi * HOSE_D ** 2 / 4
    v = q / a
    re = max(v * HOSE_D / NU, 1.0)
    f = 64.0 / re if re < 2300 else 0.316 * re ** -0.25      # laminar / Blasius
    return (f * HOSE_L / HOSE_D + HOSE_ZETA) * 0.5 * RHO * v ** 2


def operating_point(fan_dp, sys_dp, qmax):
    """Bisection on fan_dp(q) - sys_dp(q) = 0 for q in [0, qmax]."""
    lo, hi = 0.0, qmax
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if fan_dp(mid) - sys_dp(mid) > 0:
            lo = mid
        else:
            hi = mid
    q = 0.5 * (lo + hi)
    return q, float(sys_dp(q))


def solve(fan: Fan, n_fans: int, duct: Duct, hose=False, pmax=None, n_outlet_split=None):
    """n_fans identical fans, each feeding 1/n of the outlet area (symmetric channels).
    Returns total Q, per-fan dP, outlet velocity."""
    a_each = duct.a_out / n_fans
    k_each = duct.zeta * RHO / (2 * a_each ** 2)

    def sysf(q):
        return k_each * q * q + (hose_dp(q) if hose else 0.0)

    q1, p1 = operating_point(lambda q: float(fan.dp(q, pmax)), sysf, fan.qmax)
    qt = q1 * n_fans
    return qt, p1, qt / duct.a_out


# --------------------------------------------------------------------------
def write_csvs():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in FANS:
        q, p = f.curve()
        meta = [
            f"model: {f.name}",
            "columns: Q_m3_per_s (volumetric flow), dP_Pa (static pressure rise, Pa, at rated voltage, ~20-25 C air)",
            f"end point Q_max: {f.q_src} -> {f.qmax:.4e} m3/s  [status {f.q_status}]",
            f"end point dP_max: {f.p_src} -> {f.pmax:.1f} Pa  [status {f.p_status}]",
            f"curve shape between end points: generic '{f.kind}' shape  [status ESTIMATED - not a manufacturer curve]",
            "conversions: 1 CFM = 4.719e-4 m3/s; 1 inH2O = 249.09 Pa; 1 mmH2O = 9.80665 Pa",
            "OpenFOAM: incompressible solvers use kinematic pressure -> divide dP_Pa by rho (1.20 at 20 C, 1.11 at 45 C)",
            "PWM/speed scaling (affinity): Q ~ n, dP ~ n^2",
        ]
        if f.pmax_range:
            meta.append(f"dP_max uncertainty band: {f.pmax_range[0]:.0f}-{f.pmax_range[1]:.0f} Pa")
        meta.append(f"notes: {f.notes}")
        for s in f.sources:
            meta.append(f"source: {s}")
        meta.append("generated by hardware/toolhead/components/fans/operating_point.py; see documentation/research/03-fans-and-cooling.md")
        n_header = len(meta) + 2           # + this count line + column header line
        lines = [f"# nHeaderLine={n_header} (OpenFOAM csv: skip this many lines)"]
        lines += ["# " + m for m in meta]
        lines.append("Q_m3_per_s,dP_Pa")
        lines += [f"{qi:.6e},{pi:.2f}" for qi, pi in zip(q, p)]
        (OUT / f"{f.key}.csv").write_text("\n".join(lines) + "\n")
        print(f"wrote {OUT / (f.key + '.csv')}")


def tables():
    print("\n## Duct system curves (PRE-CFD, ESTIMATED)\n")
    print("| duct | A_out mm2 | sum zeta | K Pa/(m3/s)^2 | dP at 1 CFM (Pa) | detail |")
    print("|---|---|---|---|---|---|")
    for d in DUCTS:
        print(f"| {d.name} | {d.a_out*1e6:.0f} | {d.zeta} | {d.K:.3g} | {d.K*CFM**2:.1f} | {d.detail} |")

    def row(label, fan, n, hose=False, extra=""):
        cells = []
        for d in DUCTS:
            qt, p1, v = solve(fan, n, d, hose=hose)
            cells.append(f"{qt/CFM:.2f} CFM / {qt*1e3:.2f} L/s / {v:.1f} m/s / {p1:.0f} Pa")
        rng = ""
        if fan.pmax_range and not hose:
            d = DUCTS[1]
            lo = solve(fan, n, d, pmax=fan.pmax_range[0])[0] / CFM
            hi = solve(fan, n, d, pmax=fan.pmax_range[1])[0] / CFM
            rng = f"{lo:.2f}-{hi:.2f}"
        print(f"| {label} | " + " | ".join(cells) + f" | {rng} | {extra} |")

    hdr = ("| option | low K: Q / Q / v_out / dP_fan | medium K | high K | medium-K Q range for dP_max band (CFM) | note |\n"
           "|---|---|---|---|---|---|")
    print("\n## A) single part fan, whole outlet area\n")
    print(hdr)
    for k in ["creality_K1_stock_4020_blower", "delta_BFB0524HH", "gdstime_GDB5015_24V",
              "sunon_MF50152VX-1L02C-A99", "sunon_MF40202VX-1000U-G99"]:
        row(FAN[k].name, FAN[k], 1)
    print("\n## B) two identical part fans, symmetric, each feeding half the outlet area (total shown)\n")
    print(hdr)
    for k in ["creality_K1_stock_4020_blower", "delta_BFB0524HH", "gdstime_GDB5015_24V",
              "sunon_MF50152VX-1L02C-A99"]:
        row("2 x " + FAN[k].name, FAN[k], 2)
    print("\n## D) CPAP: WS7040 at 100 % through 1.5 m x 15 mm hose + duct\n")
    print(hdr)
    row(FAN["wonsmart_WS7040-24-V200"].name + " + hose", FAN["wonsmart_WS7040-24-V200"], 1, hose=True)
    # CPAP speed needed to match the stock fan's medium-duct flow (affinity, hose term ~Q^1.75 -> approx)
    q_stock = solve(FAN["creality_K1_stock_4020_blower"], 1, DUCTS[1])[0]
    q_cpap = solve(FAN["wonsmart_WS7040-24-V200"], 1, DUCTS[1], hose=True)[0]
    print(f"\nCPAP speed fraction for the stock-fan medium-duct flow ~ {q_stock/q_cpap:.2f} "
          f"(K*Q^2 systems: Q scales with speed)")

    print("\n## C) hotend fan on heat sink (K_hs ESTIMATED: 12.5 / 25 / 50 Pa at 2 CFM)\n")
    print("| fan | low | medium | high |")
    print("|---|---|---|---|")
    f = FAN["sunon_MF40202VX-1000U-G99"]
    cells = []
    for lvl in ["low", "medium", "high"]:
        q, p = operating_point(lambda q: float(f.dp(q)), lambda q: K_HS[lvl] * q * q, f.qmax)
        cells.append(f"{q/CFM:.2f} CFM / {p:.0f} Pa")
    print(f"| {f.name} | " + " | ".join(cells) + " |")


def plot(path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    series = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
    order = ["creality_K1_stock_4020_blower", "delta_BFB0524HH", "gdstime_GDB5015_24V",
             "sunon_MF50152VX-1L02C-A99", "sunon_MF40202VX-1000U-G99"]
    ink, muted, grid, surf = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.4), facecolor=surf)
    for ax in axes:
        ax.set_facecolor(surf)
        for s in ax.spines.values():
            s.set_color(grid)
        ax.tick_params(colors=muted)
        ax.grid(True, color=grid, lw=0.8)
        ax.set_xlabel("Q  [L/s]   (1 CFM = 0.472 L/s)", color=muted)
        ax.set_ylabel("static pressure  [Pa]", color=muted)

    ax = axes[0]
    qq = np.linspace(0, 3.2e-3, 300)
    for d in DUCTS:
        ax.plot(qq * 1e3, d.K * qq ** 2, color=muted, lw=1.2, ls="--")
        qlab = min(math.sqrt(440 / d.K), 3.1e-3)
        ax.text(qlab * 1e3, d.K * qlab ** 2, f" {d.name} K", color=muted, fontsize=8, va="bottom")
    for c, k in zip(series, order):
        f = FAN[k]
        q, p = f.curve()
        ax.plot(q * 1e3, p, color=c, lw=2, label=f.name)
        qo, po, _ = solve(f, 1, DUCTS[1])
        ax.plot(qo * 1e3, po, "o", ms=8, color=c, mec=surf, mew=2)
    ax.set_xlim(0, 3.2)
    ax.set_ylim(0, 450)
    ax.set_title("Single fan vs duct curves (dots: medium-K operating point)", color=ink, fontsize=10, loc="left")
    ax.legend(fontsize=7.5, frameon=False, labelcolor=ink, loc="upper center",
              bbox_to_anchor=(0.5, -0.14), ncol=2)

    ax = axes[1]
    f = FAN["wonsmart_WS7040-24-V200"]
    q, p = f.curve()
    ax.plot(q * 1e3, p, color=series[5], lw=2, label=f.name)
    qq = np.linspace(0, f.qmax, 300)
    sys = np.array([DUCTS[1].K * x * x + hose_dp(x) for x in qq])
    ax.plot(qq * 1e3, sys, color=muted, lw=1.2, ls="--", label="medium K duct + 1.5 m x 15 mm hose")
    qo, po, _ = solve(f, 1, DUCTS[1], hose=True)
    ax.plot(qo * 1e3, po, "o", ms=8, color=series[5], mec=surf, mew=2)
    ax.set_ylim(0, 7000)
    ax.set_xlim(0, f.qmax * 1e3)
    ax.set_title("Configuration D: CPAP blower through hose (ESTIMATED shape)", color=ink, fontsize=10, loc="left")
    ax.legend(fontsize=7.5, frameon=False, labelcolor=ink, loc="upper center",
              bbox_to_anchor=(0.5, -0.14), ncol=1)
    fig.suptitle("PRE-CFD ESTIMATE - curve shapes are generic (ESTIMATED), end points SECONDARY/ESTIMATED",
                 color=ink, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor=surf)
    print(f"wrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--no-csv", action="store_true")
    a = ap.parse_args()
    if not a.no_csv:
        write_csvs()
    tables()
    if a.plot:
        plot(OUT / "pq_operating_points.png")


if __name__ == "__main__":
    main()
