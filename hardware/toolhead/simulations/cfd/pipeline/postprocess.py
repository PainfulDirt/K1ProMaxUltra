"""Post-processing for run_case.py: convergence parsing, metrics (results.json) and PNG plots.

Reads the reconstructed latest time with pyvista's OpenFOAM reader. All reported pressures are
STATIC/TOTAL GAUGE pressures in Pa (kinematic p * rho); lengths in mm; flows in m^3/s.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

MM = 1e-3
CFM = 1 / 4.719474e-4          # m^3/s -> CFM
SEQ = "Blues"                  # sequential single-hue map for |U|
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


# ------------------------------------------------------------------ logs / time series
def read_dat(path: Path):
    """Read an OpenFOAM postProcessing .dat (header '# Time ...'). Returns (names, rows[list])."""
    names, rows = None, []
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            toks = line[1:].split()
            if toks and toks[0] == "Time":
                names = toks
            continue
        if line.strip():
            rows.append(line.split())
    return names, rows


def latest_dat(case: Path, fo: str, fname: str):
    d = case / "postProcessing" / fo
    if not d.exists():
        return None
    files = sorted(d.glob(f"*/{fname}*"), key=lambda p: float(p.parent.name))
    if not files:
        return None
    names, rows = [], []
    for f in files:                                   # concatenate restarts
        n, r = read_dat(f)
        names = n or names
        rows += r
    return names, rows


def series(case, fo, fname="surfaceFieldValue.dat"):
    r = latest_dat(case, fo, fname)
    if not r or not r[1]:
        return None
    arr = np.array([[float(x) for x in row[:2]] for row in r[1]])
    return arr  # [:,0]=iter, [:,1]=value


def read_probes(case, field="U"):
    """Return (iters[N], values[N, nprobe, 3]) from the probes function object, or None."""
    d = case / "postProcessing" / "probes"
    if not d.exists():
        return None
    files = sorted(d.glob(f"*/{field}"), key=lambda p: float(p.parent.name))
    its, vals = [], []
    for f in files:
        for line in f.read_text().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            tok = line.split(None, 1)
            vec = re.findall(r"\(([^)]*)\)", tok[1])
            if not vec:
                continue
            its.append(float(tok[0]))
            vals.append([[float(x) for x in v.split()] for v in vec])
    if not its:
        return None
    return np.array(its), np.array(vals)


def residuals(case):
    r = latest_dat(case, "solverInfo", "solverInfo.dat")
    if not r:
        return {}
    names, rows = r
    out = {}
    for j, n in enumerate(names):
        if n.endswith("_initial"):
            vals = []
            for row in rows:
                try:
                    vals.append(float(row[j]))
                except (ValueError, IndexError):
                    vals.append(np.nan)
            out[n[:-8]] = np.array(vals)
    out["_iter"] = np.array([float(row[0]) for row in rows])
    return out


def convergence(cfg, case, inlets, meta=None):
    from run_case import stability, is_stable
    sol = cfg["solver"]
    log = (case / "log.simpleFoam").read_text(errors="replace")
    reached = "SIMPLE solution converged" in log
    m = re.findall(r"ExecutionTime = ([\d.]+) s", log)
    it, rel, rfin = stability(cfg, case)
    stable = is_stable(cfg, rel, rfin)
    return {
        "iterations": it, "max_iter": sol["max_iter"],
        "stopped_by_watchdog_at": (meta or {}).get("watchdog_stop_iter"),
        "residualControl_reached": reached,
        "final_initial_residuals": rfin,
        "monitor_rel_range_last_window": rel,
        "criteria": {k: sol[k] for k in ("window", "tol_Q", "tol_p", "tol_probe", "probe_floor",
                                         "res_p_max", "res_U_max")},
        "converged": bool(reached or stable),
        "solver_execution_time_s": float(m[-1]) if m else None,
    }


# ------------------------------------------------------------------ field access
def load_case(case: Path):
    import pyvista as pv
    r = pv.POpenFOAMReader(str(case / "case.foam"))
    r.set_active_time_value(r.time_values[-1])
    r.enable_all_patch_arrays()
    r.cell_to_point_creation = True
    ds = r.read()
    internal = ds["internalMesh"]
    bnd = ds["boundary"]
    patches = {bnd.get_block_name(i): bnd[i] for i in range(bnd.n_blocks)}
    return internal, patches, float(r.time_values[-1])


def frame(normal, u=None):
    n = np.asarray(normal, float)
    n /= np.linalg.norm(n)
    if u is None:
        u = np.cross(n, [0, 0, 1]) if abs(n[2]) < 0.9 else np.cross(n, [1, 0, 0])
    u = np.asarray(u, float)
    u = u - n * (u @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    return n, u, v


def sample(internal, pts_m):
    import pyvista as pv
    s = pv.PolyData(np.asarray(pts_m, float)).sample(internal)
    valid = s["vtkValidPointMask"].astype(bool)
    return s["U"], s["p"], valid


def patch_stats(patch, rho):
    pd = patch.compute_cell_sizes(length=False, volume=False)
    A = np.abs(pd["Area"])
    n = patch.compute_normals(cell_normals=True, point_normals=False, auto_orient_normals=False,
                              consistent_normals=False, split_vertices=False)["Normals"]
    U = patch.cell_data["U"]
    p = patch.cell_data["p"]
    un = np.einsum("ij,ij->i", U, n)                     # outward-normal velocity
    p0 = p + 0.5 * np.einsum("ij,ij->i", U, U)
    out = {"area_mm2": float(A.sum() / MM ** 2),
           "Q_out_m3_s": float((un * A).sum()),
           "p_static_avg_Pa": float((p * A).sum() / A.sum() * rho),
           "p_total_avg_Pa": float((p0 * A).sum() / A.sum() * rho)}
    for fld, key in (("wallShearStress", "wss"), ("yPlus", "yplus")):
        if fld in patch.cell_data:
            v = patch.cell_data[fld]
            mag = np.linalg.norm(v, axis=1) if v.ndim == 2 else v
            if key == "wss":
                mag = mag * rho
            out[f"{key}_mean{'_Pa' if key == 'wss' else ''}"] = float((mag * A).sum() / A.sum())
            out[f"{key}_max{'_Pa' if key == 'wss' else ''}"] = float(mag.max())
    return out


def plane_metrics(internal, pl, rho):
    n, u, v = frame(pl["normal"], pl.get("u"))
    o = np.asarray(pl["origin"], float) * MM
    if pl.get("type", "rect") == "rect":
        hu, hv = (np.asarray(pl["half"], float) * MM)
        ds = pl.get("ds_mm", min(hu, hv) / MM / 25) * MM
        a = np.arange(-hu + ds / 2, hu, ds)
        b = np.arange(-hv + ds / 2, hv, ds)
        A_, B_ = np.meshgrid(a, b, indexing="ij")
        pts = o + A_.reshape(-1, 1) * u + B_.reshape(-1, 1) * v
        dA = np.full(len(pts), ds * ds)
        theta = None
    else:
        r_in, r_out = pl.get("r_in", 0.0) * MM, pl["r_out"] * MM
        nr, nt = pl.get("nr", 40), pl.get("ntheta", 144)
        dr, dt = (r_out - r_in) / nr, 2 * math.pi / nt
        r = r_in + (np.arange(nr) + 0.5) * dr
        th = (np.arange(nt) + 0.5) * dt
        R, TH = np.meshgrid(r, th, indexing="ij")
        R, TH = R.reshape(-1), TH.reshape(-1)
        pts = o + (R * np.cos(TH))[:, None] * u + (R * np.sin(TH))[:, None] * v
        dA = R * dr * dt
        theta = TH
    U, p, valid = sample(internal, pts)
    w = dA * valid
    Aw = w.sum()
    mag = np.linalg.norm(U, axis=1)
    un = U @ n
    res = {"type": pl.get("type", "rect"), "area_sampled_mm2": float(dA.sum() / MM ** 2),
           "area_fluid_mm2": float(Aw / MM ** 2), "valid_fraction": float(valid.mean())}
    if Aw <= 0:
        return res
    res.update({
        "Q_through_m3_s": float((un * w).sum()),
        "U_normal_mean_area": float((un * w).sum() / Aw),
        "Umag_mean_area": float((mag * w).sum() / Aw),
        "Umag_max": float(mag[valid].max()),
        "p_static_avg_Pa": float((p * w).sum() / Aw * rho),
        "p_total_avg_Pa": float(((p + 0.5 * mag ** 2) * w).sum() / Aw * rho),
    })
    flux = un * w
    if flux.sum() > 0:  # flux-weighted mean speed / total pressure of the throughflow
        fp = np.clip(flux, 0, None)
        res["Umag_mean_flux"] = float((mag * fp).sum() / fp.sum())
        res["p_total_fluxavg_Pa"] = float(((p + 0.5 * mag ** 2) * fp).sum() / fp.sum() * rho)
    if theta is not None:
        ns = pl.get("sectors", 8)
        sec = np.minimum((theta / (2 * math.pi) * ns).astype(int), ns - 1)
        means = []
        for k in range(ns):
            m = (sec == k) & valid
            means.append(float((mag[m] * dA[m]).sum() / dA[m].sum()) if m.any() else float("nan"))
        means = np.array(means)
        res["sector_Umag_mean"] = means.round(4).tolist()
        res["sector_angles_deg_start"] = [360.0 * k / ns for k in range(ns)]
        res["symmetry_min_over_max"] = float(np.nanmin(means) / np.nanmax(means))
        res["symmetry_cv"] = float(np.nanstd(means) / np.nanmean(means))
    return res


def polyline(points_mm, ds_mm=0.25):
    P = np.asarray(points_mm, float)
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        L = np.linalg.norm(b - a)
        k = max(1, int(math.ceil(L / ds_mm)))
        out += [a + (b - a) * t for t in np.linspace(0, 1, k + 1)[1:]]
    out = np.array(out)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(out, axis=0), axis=1))])
    return out, s


# ------------------------------------------------------------------ plots
def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e6e6e3", "grid.linewidth": 0.6,
                         "axes.edgecolor": "#8a8984", "figure.dpi": 130})
    return plt


def plot_slice(internal, sl, rho, out: Path, title, annot=None):
    plt = _mpl()
    ax_i = "xyz".index(sl["axis"])
    ia, ib = [i for i in range(3) if i != ax_i]
    (a0, a1), (b0, b1) = sl["range"]
    ds = sl.get("ds_mm", max(a1 - a0, b1 - b0) / 400)
    a = np.arange(a0, a1 + 1e-9, ds)
    b = np.arange(b0, b1 + 1e-9, ds)
    A_, B_ = np.meshgrid(a, b)
    pts = np.zeros((A_.size, 3))
    pts[:, ia], pts[:, ib], pts[:, ax_i] = A_.ravel(), B_.ravel(), sl["value"]
    U, p, valid = sample(internal, pts * MM)
    mag = np.where(valid, np.linalg.norm(U, axis=1), np.nan).reshape(A_.shape)
    ua = np.where(valid, U[:, ia], 0).reshape(A_.shape)
    ub = np.where(valid, U[:, ib], 0).reshape(A_.shape)
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.set_facecolor("#9a9994")             # solids / outside fluid in grey
    vmax = sl.get("vmax") or np.nanpercentile(mag, 99.5)
    im = ax.pcolormesh(A_, B_, mag, cmap=SEQ, vmin=0, vmax=vmax, shading="auto")
    try:
        ax.streamplot(a, b, ua, ub, color="#0b0b0b", linewidth=0.45, density=1.4, arrowsize=0.6)
    except Exception:
        pass
    for k, (xa, xb, lab) in (annot or {}).items():
        ax.plot(xa, xb, **lab)
    ax.set_aspect("equal")
    ax.set_xlim(a0, a1)
    ax.set_ylim(b0, b1)
    ax.grid(False)
    ax.set_xlabel(f"{'xyz'[ia]} [mm]")
    ax.set_ylabel(f"{'xyz'[ib]} [mm]")
    ax.set_title(title, loc="left")
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("|U| [m/s]")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_line(name, s_mm, p_pa, umag, out):
    plt = _mpl()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7, 4.6), sharex=True)
    a1.plot(s_mm, p_pa, color=CAT[0], lw=2)
    a1.set_ylabel("static p [Pa]")
    a1.set_title(f"Pressure and speed along '{name}'", loc="left")
    a2.plot(s_mm, umag, color=CAT[1], lw=2)
    a2.set_ylabel("|U| [m/s]")
    a2.set_xlabel("distance along line [mm]")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_convergence(case, inlets, rho, out):
    plt = _mpl()
    res = residuals(case)
    fig, axs = plt.subplots(1 + len(inlets), 1, figsize=(7, 2.4 * (1 + len(inlets))), sharex=True)
    axs = np.atleast_1d(axs)
    it = res.get("_iter", [])
    for i, k in enumerate([k for k in ("p", "Ux", "Uy", "Uz", "k", "omega") if k in res]):
        axs[0].semilogy(it, res[k], color=CAT[i], lw=1.2, label=k)
    axs[0].set_ylabel("initial residual")
    axs[0].legend(ncol=6, fontsize=7, frameon=False, loc="upper right")
    axs[0].set_title("Convergence", loc="left")
    for j, name in enumerate(inlets):
        s = series(case, f"flow_{name}")
        if s is not None:
            axs[1 + j].plot(s[:, 0], -s[:, 1] * 1e3, color=CAT[0], lw=1.5)
            axs[1 + j].set_ylabel(f"Q {name} [L/s]")
    axs[-1].set_xlabel("iteration")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_streamlines(internal, patches, cfg, out):
    import pyvista as pv
    pv.OFF_SCREEN = True
    inl = [k for k, s in cfg["surfaces"].items() if s.get("type") == "inlet"]
    seeds = []
    for name in inl:
        pc = patches[name].cell_centers().points
        nrm = patches[name].compute_normals(cell_normals=True, point_normals=False,
                                            auto_orient_normals=False, consistent_normals=False,
                                            split_vertices=False)["Normals"]
        idx = np.linspace(0, len(pc) - 1, min(len(pc), 150)).astype(int)
        seeds.append(pc[idx] - nrm[idx] * 2e-4)
    if not seeds:
        return
    src = pv.PolyData(np.vstack(seeds))
    stl = internal.streamlines_from_source(src, vectors="U", integration_direction="forward",
                                           max_steps=4000, initial_step_length=0.2,
                                           max_length=0.5)
    pl = pv.Plotter(off_screen=True, window_size=(1100, 750))
    pl.set_background("white")
    for i, (k, s) in enumerate(cfg["surfaces"].items()):
        if s.get("type", "wall") == "wall" and k in patches:
            pl.add_mesh(patches[k], color=["#c3c2b7", "#eb6834", "#8a8984"][min(i, 2)], opacity=0.35 if i == 0 else 0.9)
    if stl.n_points:
        stl = stl.compute_cell_sizes()
        pl.add_mesh(stl.tube(radius=1.2e-4) if stl.n_points < 400000 else stl, scalars="U",
                    cmap="Blues", clim=[0, np.percentile(np.linalg.norm(stl["U"], axis=1), 99)],
                    scalar_bar_args={"title": "|U| [m/s]", "color": "black", "vertical": True,
                                     "position_x": 0.88, "position_y": 0.2, "height": 0.6})
    cam = cfg["plots"].get("camera")
    if cam:   # {"position": [mm], "focal": [mm], "up": [..]}
        pl.camera_position = [tuple(np.asarray(cam["position"]) * MM), tuple(np.asarray(cam["focal"]) * MM),
                              tuple(cam.get("up", (0, 0, 1)))]
    else:     # look from -y (front), slightly above, at all wall patches
        b = np.array([patches[k].bounds for k, s in cfg["surfaces"].items() if k in patches])
        lo, hi = b[:, 0::2].min(axis=0), b[:, 1::2].max(axis=0)
        c, d = (lo + hi) / 2, np.linalg.norm(hi - lo)
        pl.camera_position = [tuple(c + d * np.array([0.35, -1.3, 0.55])), tuple(c), (0, 0, 1)]
    pl.screenshot(str(out))
    pl.close()


# ------------------------------------------------------------------ main entry
def postprocess(cfg, case: Path, meta):
    rho = cfg["fluid"]["rho"]
    resdir = case / "results"
    resdir.mkdir(exist_ok=True)
    internal, patches, t = load_case(case)
    cells = internal.copy()          # cell-constant sampling for metrics (conservative fluxes)
    cells.clear_point_data()
    inlets = [k for k, s in cfg["surfaces"].items() if s.get("type") == "inlet"]
    walls = [k for k, s in cfg["surfaces"].items() if s.get("type", "wall") == "wall"] + \
            [k for k, v in meta["block_types"].items() if v == "wall"]
    atm = [k for k, v in meta["block_types"].items() if v == "atmosphere"]

    out = {"case": case.name, "time": t, "level": meta["level"],
           "mesh": {"cells": meta.get("mesh", {}).get("cells", internal.n_cells), "base_cell_mm": meta["base_cell_mm"],
                    **{k: v for k, v in meta.get("mesh", {}).items() if k != "time_s"}},
           "units": {"p": "Pa gauge (rho*p_kinematic)", "length": "mm", "Q": "m^3/s", "U": "m/s"},
           "fluid": cfg["fluid"]}
    out["convergence"] = convergence(cfg, case, inlets, meta)

    out["inlets"] = {}
    for name in inlets:
        st = patch_stats(patches[name], rho)
        s = series(case, f"flow_{name}")
        Q = float(-s[-1, 1]) if s is not None else -st["Q_out_m3_s"]
        bc = cfg["surfaces"][name]["bc"]
        d = {"Q_m3_s": Q, "Q_cfm": Q * CFM, "area_mm2": st["area_mm2"],
             "U_mean_m_s": Q / (st["area_mm2"] * MM * MM),
             "p_static_avg_Pa": st["p_static_avg_Pa"], "p_total_avg_Pa": st["p_total_avg_Pa"],
             "bc": {k: v for k, v in bc.items() if not k.endswith("_resolved")}}
        if bc["kind"] == "fan":
            from run_case import read_fan_csv
            tab = read_fan_csv(bc["csv_resolved"])
            d["fan_dP_at_Q_Pa"] = float(np.interp(Q, tab[:, 0], tab[:, 1]))
            qmax = float(tab[-1, 0])
            if (tab[:, 1] <= 0).any():              # free-delivery point = first zero crossing
                i = int(np.argmax(tab[:, 1] <= 0))
                qmax = float(np.interp(0.0, tab[i - 1:i + 1, 1][::-1], tab[i - 1:i + 1, 0][::-1])) if i else float(tab[0, 0])
            d["fan_Qmax_m3_s"] = qmax
            d["fan_dP_shutoff_Pa"] = float(tab[0, 1])
            d["operating_point"] = {"Q_m3_s": Q, "dP_Pa": d["fan_dP_at_Q_Pa"],
                                    "fraction_of_Qmax": Q / qmax,
                                    "fraction_of_shutoff_pressure": d["fan_dP_at_Q_Pa"] / float(tab[0, 1])}
        out["inlets"][name] = d
    q_in = sum(d["Q_m3_s"] for d in out["inlets"].values())
    q_out = 0.0
    for a in atm:
        s = series(case, f"flow_{a}")
        if s is not None:
            q_out += float(s[-1, 1])
    out["mass_balance"] = {"Q_in_m3_s": q_in, "Q_net_out_atmosphere_m3_s": q_out,
                           "imbalance_rel": (q_out - q_in) / q_in if q_in else None}

    out["planes"] = {pl["name"]: plane_metrics(cells, pl, rho) for pl in cfg["probes"]["planes"]}
    out["points"] = {}
    for pt in cfg["probes"]["points"]:
        U, p, valid = sample(cells, [np.asarray(pt["xyz"], float) * MM])
        out["points"][pt["name"]] = {"xyz_mm": pt["xyz"], "valid": bool(valid[0]),
                                     "U": U[0].round(5).tolist(), "Umag": float(np.linalg.norm(U[0])),
                                     "p_Pa": float(p[0] * rho)}
    out["lines"] = {}
    plots = []
    for ln in cfg["probes"]["lines"]:
        P, s = polyline(ln["points"])
        U, p, valid = sample(internal, P * MM)
        pp, um = np.where(valid, p * rho, np.nan), np.where(valid, np.linalg.norm(U, axis=1), np.nan)
        out["lines"][ln["name"]] = {"length_mm": float(s[-1]), "valid_fraction": float(valid.mean()),
                                    "p_start_Pa": float(pp[valid][0]), "p_end_Pa": float(pp[valid][-1]),
                                    "dp_static_Pa": float(pp[valid][0] - pp[valid][-1]),
                                    "Umag_max": float(np.nanmax(um))}
        f = resdir / f"line_{ln['name']}.png"
        plot_line(ln["name"], s, pp, um, f)
        plots.append(f.name)

    out["walls"] = {w: {k: v for k, v in patch_stats(patches[w], rho).items()
                        if k not in ("Q_out_m3_s",)} for w in walls if w in patches}
    out["losses"] = {}
    for a, b in cfg.get("loss_pairs", []):
        if a in out["inlets"] and b in out["planes"] and "p_total_fluxavg_Pa" in out["planes"][b]:
            out["losses"][f"{a}->{b}"] = {
                "dp_total_Pa": out["inlets"][a]["p_total_avg_Pa"] - out["planes"][b]["p_total_fluxavg_Pa"],
                "dp_static_Pa": out["inlets"][a]["p_static_avg_Pa"] - out["planes"][b]["p_static_avg_Pa"]}

    # plots
    for sl in cfg["plots"].get("slices", []):
        f = resdir / f"slice_{sl['name']}_Umag.png"
        annot = {}
        for pl in cfg["probes"]["planes"]:
            if pl.get("type") == "annulus" and sl["axis"] == "z":
                th = np.linspace(0, 2 * np.pi, 200)
                o = pl["origin"]
                annot[pl["name"]] = (o[0] + pl["r_out"] * np.cos(th), o[1] + pl["r_out"] * np.sin(th),
                                     {"color": CAT[1], "lw": 1.2, "ls": "--"})
        if sl["axis"] == "z":
            for pt in [q for q in cfg["probes"]["points"] if abs(q["xyz"][2] - sl["value"]) <= 1.0]:
                annot[pt["name"]] = ([pt["xyz"][0]], [pt["xyz"][1]],
                                     {"marker": "x", "color": CAT[7], "ms": 8, "mew": 2})
        plot_slice(internal, sl, rho, f, f"|U| on {sl['axis']} = {sl['value']} mm  ({case.name})", annot)
        plots.append(f.name)
    f = resdir / "convergence.png"
    plot_convergence(case, inlets, rho, f)
    plots.append(f.name)
    if cfg["plots"].get("streamlines", True):
        try:
            f = resdir / "streamlines3d.png"
            plot_streamlines(internal, patches, cfg, f)
            plots.append(f.name)
        except Exception as e:  # rendering is best-effort
            out["streamlines_error"] = repr(e)
    out["plots"] = plots
    return out
