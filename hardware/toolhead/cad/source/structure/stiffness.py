"""Hand stiffness / first-mode / thermal-drift estimates (no FEA).

All results are ESTIMATED: printed-plastic moduli and CTEs are typical values
(common.MATERIALS), joints are idealised. Use them to rank options and to spot
a mode near the input-shaper band (X 77.6 Hz, Y 52 Hz), not as predictions.
Load case requested by the lead: F = 2 x m x a with a = 20 000 mm/s^2
(stock max_accel, research/02 M5).
"""
from __future__ import annotations

import math

from .common import ASA, PA_CF, E_STEEL
from . import frame as F
from . import probe_mount as PM
from . import reference as R
import interfaces as I

A_MAX = 20.0          # m/s^2 (20 000 mm/s^2)
SF = 2.0
M3_AS = 5.03          # mm2 tensile stress area, ISO 898


def _f_hz(k_n_per_mm: float, m_g: float) -> float:
    return math.sqrt(k_n_per_mm * 1e3 / (m_g * 1e-3)) / (2 * math.pi)


def _pattern_r2(axis: int) -> float:
    pts = [p[axis] for p in I.MODULE_MOUNT_HOLES]
    c = sum(pts) / len(pts)
    return sum((p - c) ** 2 for p in pts)


def frame_estimates(carried: list[dict], fan_screws: list) -> dict:
    """carried: [{'name', 'mass_g', 'com': (x, y, z), 'inertia_extra_gmm2'}] hung on the frame."""
    m = sum(c["mass_g"] for c in carried)
    cy = sum(c["mass_g"] * c["com"][1] for c in carried) / m
    d = abs(cy - float(I.MODULE_MOUNT_BEARING_Y))
    F_N = SF * m * 1e-3 * A_MAX
    E = ASA.E_mpa.value
    a_tube = math.pi / 4 * (F.PAD_D ** 2 - 3.4 ** 2)
    k_boss = E * a_tube / F.STOCK_GRIP_ADD
    a_coll = math.pi / 4 * (F.COLLAR_D ** 2 - 3.4 ** 2)
    k_coll = E * a_coll / F.T
    k_member = 1 / (1 / k_boss + 1 / k_coll)
    grip = abs(F.FRONT_Y - float(I.FAN3010.ymax))           # head face .. back of 3010
    k_bolt = E_STEEL * M3_AS / grip
    out = {"carried_mass_g": round(m, 1), "com_y": round(cy, 1), "lever_from_pcb_mm": round(d, 1),
           "load_N (2 x m x 20 m/s2)": round(F_N, 2)}
    for label, kj in (("optimistic (preloaded bolt + boss)", k_bolt + k_member),
                      ("pessimistic (boss in compression only)", k_member)):
        r2 = min(_pattern_r2(0), _pattern_r2(1))
        k_th = kj * r2                                      # N.mm/rad, 3 joints
        J = sum(c["mass_g"] * ((c["com"][1] - float(I.MODULE_MOUNT_BEARING_Y)) ** 2) + c.get("inertia_extra_gmm2", 0)
                for c in carried)                           # g.mm2
        # units: k_th N.mm/rad = 1e-3 N.m/rad ; J g.mm2 = 1e-9 kg.m2
        f_rock = math.sqrt((k_th * 1e-3) / (J * 1e-9)) / (2 * math.pi)
        delta = F_N * d ** 2 / k_th
        out[f"rocking on the 3-screw pattern, {label}"] = {
            "k_joint_N_per_mm": round(kj), "k_theta_Nmm_per_rad": round(k_th), "deflection_at_com_um": round(delta * 1e3, 2),
            "first_mode_Hz": round(f_rock)}
    # local: each fan screw standoff -> nearest plate support (PCB boss or 4th pad), out of plane (Y)
    t, rw, rd, bstrip = F.T, F.RIB_W, F.RIB_D, 20.0
    a1, a2 = bstrip * t, rw * rd
    yc = (a1 * t / 2 + a2 * (t + rd / 2)) / (a1 + a2)
    I_strip = bstrip * t ** 3 / 12 + a1 * (t / 2 - yc) ** 2 + rw * rd ** 3 / 12 + a2 * (t + rd / 2 - yc) ** 2
    supports = list(I.MODULE_MOUNT_HOLES) + ([F.fourth_corner()] if F.FOURTH_PAD else [])
    fan_m = carried[0]["mass_g"]
    for label, sup in (("with 4th pad", supports), ("without 4th pad (M10/2nd plate not real)",
                                                    list(I.MODULE_MOUNT_HOLES))):
        rows = []
        for x, z in fan_screws:
            L = max(min(((x - sx) ** 2 + (z - sz) ** 2) ** 0.5 for sx, sz in sup) - F.COLLAR_D / 2, 1.0)
            k = 3 * E * I_strip / L ** 3                     # plate strip cantilever, out of plane (Y)
            m_share = fan_m / max(len(fan_screws), 1)        # each screw carries its share
            rows.append({"screw_xz": [round(x, 2), round(z, 2)], "to_support_mm": round(L, 1),
                         "k_N_per_mm": round(k, 1),
                         "deflection_um": round(SF * m_share * 1e-3 * A_MAX / k * 1e3, 1),
                         "first_mode_Hz": round(_f_hz(k, m_share))})
        out[f"fan out-of-plane (Y) on plate, {label}"] = {
            "I_strip_mm4": round(I_strip, 1), "per_screw": rows,
            "first_mode_Hz": min(r["first_mode_Hz"] for r in rows)}
    out["note"] = ("Rocking modes are far above the shaper band; the weak link is the plate between the lower fan screw "
                   "and the nearest support, so the compression pad at the 4th pattern corner matters (M10). The upper "
                   "two PCB screws thread into an unknown part (UPPER_PATTERN_HOLES_TARGET, MISSING): if it is plastic, "
                   "k_joint can fall well below the pessimistic case. Duct cantilever: owned by the Duct agent; keep its "
                   "first mode > 150 Hz (2x X shaper) - a 30-40 mm thin-wall PC duct hung only at Z 22 needs its own rib.")
    return out


def probe_estimates(mount_mass_g: float) -> dict:
    E = PA_CF.E_mpa.value
    L = PM.Z_ANCHOR - float(I.PROBE_MOUNT_FACE_Z)          # tab top (anchor) .. flange seat
    bo, ho = 2 * PM.HALF_W, PM.REAR_Y - PM.MATE_Y
    bi, hi = 2 * (PM.HALF_W - PM.WALL), PM.CABLE[2] - (PM.MATE_Y + PM.WALL)
    Ixx = (bo * ho ** 3 - bi * hi ** 3) / 12          # resists Y bending
    Iyy = (ho * bo ** 3 - hi * bi ** 3) / 12          # resists X bending
    m = 6.0 + 0.5 * mount_mass_g
    Fh = SF * m * 1e-3 * A_MAX
    res = {"column_length_mm": round(L, 2), "Ixx_mm4": round(Ixx), "Iyy_mm4": round(Iyy),
           "inertial_load_N": round(Fh, 3)}
    for ax, Iv in (("Y", Ixx), ("X", Iyy)):
        k = 3 * E * Iv / L ** 3
        res[f"{ax}: k_N_per_mm"] = round(k)
        res[f"{ax}: deflection_um"] = round(Fh / k * 1e3, 3)
        res[f"{ax}: first_mode_Hz"] = round(_f_hz(k, m))
    dT = 10.0
    res["thermal Z drift per 10 K (PA-CF column)"] = f"{L * PA_CF.cte.value * dT * 1e3:.1f} um"
    res["thermal Z drift per 10 K (785004 if PLA/PETG ~70e-6/K)"] = f"{L * 70e-6 * dT * 1e3:.1f} um"
    L_hs = R.HS_XHOLE_Z - float(I.PROBE_MOUNT_FACE_Z)
    res["option heatsink cross-hole (02:H14)"] = (
        f"printed path {L_hs:.1f} mm -> {L_hs * PA_CF.cte.value * dT * 1e3:.1f} um/10 K, clamp lever ~18 mm, "
        f"k >> 1000 N/mm; BLOCKED: its left cheek (X -17.9..-14.1, Y -3..10, Z 34..47) lies in "
        f"LIDAR_RESERVED_BODY, and the hole's function is MISSING (may hold the carriage clamp)")
    L_e8 = 63.5 - float(I.PROBE_MOUNT_FACE_Z)
    res["option extruder bottom screws (02:E8)"] = (
        f"printed path ~{L_e8:.1f} mm -> {L_e8 * PA_CF.cte.value * dT * 1e3:.1f} um/10 K; E8 holes (Y +10.1) sit "
        f"0.1 mm inside the heatsink rear face (Y +10.2), so a bracket must pass through the MISSING heatsink-to-"
        f"carriage gap: not buildable without carriage data")
    res["verdict"] = ("Stiffness is not the limit for any option (sub-um deflection, kHz modes); the anchor joint "
                      "(2 x ~M2 into unknown toolhead tabs) and thermal growth of the printed path are. The 785004 "
                      "anchor is the default because it is proven in service at today's pin position; PA-CF + closed "
                      "section cut thermal drift ~40 % vs a PLA/PETG 785004. The heatsink option halves the path but "
                      "is blocked by the LiDAR body box until M6.")
    return res
