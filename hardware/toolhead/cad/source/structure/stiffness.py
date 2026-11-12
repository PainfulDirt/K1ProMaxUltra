"""Hand stiffness / first-mode / thermal-drift estimates (no FEA).

All results are ESTIMATED: printed-plastic moduli and CTEs are typical values
(common.MATERIALS), joints are idealised. Use them to rank options and to spot
a mode near the input-shaper band (X 77.6 Hz, Y 52 Hz), not as predictions.
Load case requested by the lead: F = 2 x m x a with a = 20 000 mm/s^2
(stock max_accel, research/02 M5).
"""
from __future__ import annotations

import math

from .common import ASA, PA_CF, PC, E_STEEL, prm
from . import frame as F
from . import probe_mount as PM
from . import reference as R
import interfaces as I

G = "stiffness"
E_BRASS = prm(G, "E_BRASS", 100000.0, "ESTIMATED", "CuZn37 tube, typical 95-110 GPa")
E_FR4_Z = prm(G, "E_FR4_THROUGH_THICKNESS", 5000.0, "ESTIMATED", "FR-4 through-thickness modulus, typical 3-12 GPa")
E_3010 = prm(G, "E_FAN3010_HOUSING", 2500.0, "ESTIMATED", "3010 housing plastic (PBT/PA, grade unknown), 2-3 GPa")
FAN3010_PILLAR_D = prm(G, "FAN3010_PILLAR_D", 6.0, "ESTIMATED",
                       "3010 corner pillar around the screw, effective compression diameter (not measured)")
NU_PC = prm(G, "NU_PC", 0.37, "ESTIMATED", "Poisson ratio of PC, typical 0.37-0.38")
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
    a_tube = math.pi / 4 * (F.PAD_D ** 2 - F.SLEEVE_BORE_CLEAR ** 2)
    k_boss = E * a_tube / F.STOCK_GRIP_ADD
    a_coll = math.pi / 4 * (F.COLLAR_D ** 2 - F.SLEEVE_BORE_CLEAR ** 2)
    k_coll = E * a_coll / F.T
    k_asa = 1 / (1 / k_boss + 1 / k_coll)
    # R-04: the clamped stack in series: brass sleeve (carries the preload), PCB (FR-4 through thickness, 45-deg
    # spread under the sleeve), the 3010's corner pillar; the ASA boss is only pre-compressed 0.1 mm alongside.
    t_pcb = float(I.PCB.ymax - I.PCB.ymin)
    k_sleeve = E_BRASS * math.pi / 4 * (F.SLEEVE_OD ** 2 - F.SLEEVE_ID ** 2) / F.sleeve_len()
    k_pcb = E_FR4_Z * math.pi / 4 * ((F.SLEEVE_OD + t_pcb) ** 2 - 3.4 ** 2) / t_pcb
    l_3010 = float(I.FAN3010.ymax - I.FAN3010.ymin)
    k_3010 = E_3010 * math.pi / 4 * (FAN3010_PILLAR_D ** 2 - 3.4 ** 2) / l_3010
    k_member = 1 / (1 / k_sleeve + 1 / k_pcb + 1 / k_3010)
    k_member_asa = 1 / (1 / k_asa + 1 / k_pcb + 1 / k_3010)
    grip = abs(F.FRONT_Y - float(I.FAN3010.ymax))           # head face .. back of 3010
    k_bolt = E_STEEL * M3_AS / grip
    out = {"carried_mass_g": round(m, 1), "com_y": round(cy, 1), "lever_from_pcb_mm": round(d, 1),
           "load_N (2 x m x 20 m/s2)": round(F_N, 2),
           "clamp stack per PCB screw (N/mm, series)": {
               "brass sleeve": round(k_sleeve), "PCB (FR-4 z)": round(k_pcb), "3010 corner pillar": round(k_3010),
               "member with sleeve": round(k_member), "member if ASA carried it (before R-04)": round(k_member_asa),
               "note": "the 3010 housing is the softest link either way (as in the stock clamp, which also ran "
                       "through PCB + 3010); the sleeve takes the ASA (creep at 45-60 C) out of the preload path"}}
    for label, kj in (("optimistic (preloaded bolt + clamped stack)", k_bolt + k_member),
                      ("pessimistic (clamped stack in compression only)", k_member)):
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
                   "two PCB screws thread into the carriage's brass inserts (UPPER_PATTERN_HOLES_TARGET, DERIVED). "
                   "Duct cantilever: see duct_estimates().")
    out["4th anchor (right stock cover-screw insert, review R-04)"] = anchor4_evaluation(out)
    return out


ANCHOR4 = {"insert": tuple(I.COVER_SCREWS[1]), "tab_x": (22.4, 24.0), "z": (float(I.HEATSINK.zmin), 38.8)}


def anchor4_evaluation(frame_out: dict) -> dict:
    """R-04 option: a frame arm to the right stock cover-screw insert (COVER_SCREWS X +22.6, Y -2.2, Z 35.35, M3x4
    low-head along X). Geometry probed on the Henlor carriage (validation cache): at X >= 24.2 nothing is in the
    way from Y -28.9 to +1, Z 31.35..39.35; the insert boss face is at X ~22.4, so a 1.6 mm tab X 22.4..24.0 sits where
    the stock cover wall sat (stock cover X +-24.0, 02:C4) and the stock screw is reused. Not built - see verdict."""
    x0, x1 = ANCHOR4["tab_x"]
    z0, z1 = ANCHOR4["z"]
    _, yi, zi = ANCHOR4["insert"]
    L = yi - F.BACK_Y                                   # arm from the plate back to the insert
    A = (x1 - x0) * (z1 - z0)
    k_ax = ASA.E_mpa.value * A / L
    zc = sum(z for _, z in I.MODULE_MOUNT_HOLES) / len(I.MODULE_MOUNT_HOLES)
    k_th = k_ax * (zc - zi) ** 2
    base = frame_out["rocking on the 3-screw pattern, pessimistic (clamped stack in compression only)"]["k_theta_Nmm_per_rad"]
    i_z = (x1 - x0) * (z1 - z0) ** 3 / 12
    return {"arm_mm": [round(x1 - x0, 1), round(z1 - z0, 1), round(L, 1)], "axial_k_N_per_mm": round(k_ax),
            "pitch_k_added_Nmm_per_rad": round(k_th), "vs_3_screw_pessimistic": f"+{100 * k_th / base:.0f} %",
            "arm_Z_bending_k_N_per_mm": round(3 * ASA.E_mpa.value * i_z / L ** 3, 1),
            "sock_distance_mm": round(math.hypot(x0 - I.SOCK.xmax, max(0.0, z0 - I.SOCK.zmax)), 1),
            "verdict": "fits the stock geometry but NOT added: (1) the 29 mm arm runs along Y at mid height, an unsupported "
                       "horizontal overhang in the frame's upside-down print orientation (needs supports or a separate "
                       "bolt-on part); (2) it needs a notch in the cover's right wall behind Y -33.5; (3) at Z >= 31.9 it "
                       "is ~10.6 mm from the sock (DD-07 asks ~14 mm for heatsink-level ASA); (4) it adds little: the pitch "
                       "gain is small and the R-04 creep issue is handled by the brass sleeves. Revisit as a separate PC "
                       "bracket if the 10-h torque audit shows preload loss."}


def duct_estimates(duct_shape, tabs: list, density_g_cm3: float) -> dict:
    """R-22: duct cantilever. Rigid duct pivoting about the line through its two tab holes (pitch about X); spring =
    the two tab pads (PC tab 2.5 + ASA lug, in bending over the 7 x 7 pad) - upper bound - and, in series, the
    tab arms in torsion (2.5 x 6 PC, from duct_generator tab_arms) - lower bound. The thin posts from the arms
    down to the plenum and the duct's own bending are ignored (both make it softer)."""
    import numpy as np
    import trimesh
    v, f = duct_shape.tessellate(0.05, 0.3)
    m = trimesh.Trimesh(np.array([(q.X, q.Y, q.Z) for q in v]), np.array(f), process=True)
    m.density = density_g_cm3 / 1000.0                    # g/mm3 -> mass in g, inertia in g.mm2
    yc = sum(t["hole_centre"][1] for t in tabs) / len(tabs)
    zc = sum(t["hole_centre"][2] for t in tabs) / len(tabs)
    com = m.center_mass
    J = float(m.moment_inertia[0, 0]) + m.mass * ((com[1] - yc) ** 2 + (com[2] - zc) ** 2)
    bb = duct_shape.bounding_box()
    face_y = min(t["face_y"] for t in tabs)
    E_pc, E_asa = PC.E_mpa.value, ASA.E_mpa.value
    G_pc = E_pc / (2 * (1 + NU_PC))
    rows, k_up, k_lo = [], 0.0, 0.0
    for t in tabs:
        px, py, pz = t["pad"]
        i_pad = px * pz ** 3 / 12
        i_lug = math.pi * F.INSERTS["M3"].boss_d ** 4 / 64 if hasattr(F, "INSERTS") else i_pad
        k_pad = 1 / (py / (E_pc * i_pad) + (F.BACK_Y - face_y) / (E_asa * i_lug))
        L_arm = abs(t["hole_centre"][0] - t["arm_from_x"])
        b_, t_ = 6.0, py                                   # arm section Z 6 (z +-3) x Y (pad thickness)
        beta = 1 / 3 * (1 - 0.63 * t_ / b_)                # Roark rectangle torsion constant (approx.)
        k_arm = G_pc * beta * b_ * t_ ** 3 / max(L_arm, 1e-6)
        rows.append({"id": t["id"], "pad_k_Nmm_per_rad": round(k_pad), "arm_len_mm": round(L_arm, 1),
                     "arm_torsion_k_Nmm_per_rad": round(k_arm)})
        k_up += k_pad
        k_lo += 1 / (1 / k_pad + 1 / k_arm)
    f = lambda k: math.sqrt(k * 1e-3 / (J * 1e-9)) / (2 * math.pi)
    return {"lever_mm (tab mating face -> rear end)": round(bb.max.Y - face_y, 1),
            "lever_mm (tab hole line -> rear end)": round(bb.max.Y - yc, 1),
            "mass_g": round(m.mass, 2), "com": [round(c, 1) for c in com], "J_about_tab_line_gmm2": round(J),
            "tabs": rows, "pitch_mode_Hz_upper (pads only)": round(f(k_up)),
            "pitch_mode_Hz_lower (pads + arm torsion)": round(f(k_lo)),
            "note": "rigid-body pitch about the tab line; posts and duct bending ignored (both lower it further). "
                    "Target > 2 x 77.6 Hz. A third tab near the rear (review R-22) or arms of real section raise it."}


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
