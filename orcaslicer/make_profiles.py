#!/usr/bin/env python3
"""OrcaSlicer 2.4 user presets for this K1 Max (Simple AF + Kalico, Microprobe +
load cells, glass bed, 2026-09-28 tuning). Writes machine/process/filament JSON."""
import json, os, sys

OUT = sys.argv[1]
VERSION = "2.3.2.75"          # preset format version of the user's existing presets
BRAND = "K1 Max Tuned"

# per-nozzle machine + process parameters
NOZZLES = {
    # parent system printer, layer heights, first layer, retraction, z-hop,
    # speeds: outer, inner, sparse, solid, top, gap, bridge, support, first layer
    0.2: dict(parent="Creality K1 Max (0.4 nozzle)",
              layers=[0.04, 0.06, 0.08, 0.10, 0.12, 0.14], first=0.12,
              retract=0.8, zhop=0.2, walls=3, generator="arachne",
              top=0.7, bottom=0.5, efc=0.10,
              speed=(100, 150, 150, 120, 80, 80, 20, 80, 30),
              accel=dict(outer=4000, inner=6000, top=2500, default=8000, travel=12000)),
    0.4: dict(parent="Creality K1 Max (0.4 nozzle)",
              layers=[0.06, 0.08, 0.12, 0.16, 0.20, 0.24, 0.28, 0.32], first=0.20,
              retract=0.8, zhop=0.4, walls=2, generator="classic",
              top=1.0, bottom=0.6, efc=0.15,
              speed=(200, 300, 270, 250, 200, 250, 30, 150, 60),
              accel=dict(outer=5000, inner=8000, top=3000, default=10000, travel=12000)),
    0.6: dict(parent="Creality K1 Max (0.6 nozzle)",
              layers=[0.12, 0.18, 0.24, 0.30, 0.36, 0.42], first=0.30,
              retract=1.0, zhop=0.4, walls=2, generator="classic",
              top=1.2, bottom=0.8, efc=0.20,
              speed=(150, 200, 200, 180, 150, 150, 30, 120, 50),
              accel=dict(outer=5000, inner=8000, top=3000, default=10000, travel=12000)),
    0.8: dict(parent="Creality K1 Max (0.8 nozzle)",
              layers=[0.16, 0.24, 0.32, 0.40, 0.48, 0.56], first=0.40,
              retract=1.2, zhop=0.5, walls=2, generator="classic",
              top=1.4, bottom=1.0, efc=0.20,
              speed=(120, 150, 150, 150, 120, 120, 25, 100, 40),
              accel=dict(outer=4000, inner=6000, top=3000, default=8000, travel=12000)),
    1.0: dict(parent="Creality K1 Max (0.8 nozzle)",
              layers=[0.20, 0.30, 0.40, 0.50, 0.60, 0.70], first=0.50,
              retract=1.4, zhop=0.6, walls=2, generator="classic",
              top=1.6, bottom=1.2, efc=0.20,
              speed=(100, 120, 120, 120, 100, 100, 20, 80, 35),
              accel=dict(outer=4000, inner=6000, top=3000, default=8000, travel=12000)),
}

def fmt(x):
    return ("%.3f" % x).rstrip("0").rstrip(".")

def printer_name(n):
    return f"{BRAND} ({n:.1f} nozzle)"

def label(h, n):
    r = h / n
    if r <= 0.2:  return "Extra Fine"
    if r <= 0.3:  return "Fine"
    if r <= 0.45: return "Optimal"
    if r <= 0.55: return "Standard"
    if r <= 0.65: return "Draft"
    if r < 0.75:  return "Extra Draft"
    return "Max"

# speed tiers: multipliers on each nozzle's speeds / accelerations.
# Balanced keeps the original profile names, so existing selections still work.
TIERS = {
    # name:      outer, other speeds, travel, accel: outer, inner, top, default, travel
    "Precision": dict(outer=0.5, speed=0.6, travel=400, acc=(0.5, 0.5, 0.5, 0.5, 0.67)),
    "Balanced":  dict(outer=1.0, speed=1.0, travel=500, acc=(1.0, 1.0, 1.0, 1.0, 1.0)),
    # full speed where it doesn't show (infill, inner walls, travel); the outer
    # wall stays gentle, at the input shaper acceleration limit
    "Fast":      dict(outer=1.2, speed=2.0, travel=800, acc=(1.0, 1.75, 1.0, 2.0, 1.67)),
}
MAX_SPEED = 800
# Precision caps every feature at this melt rate (mm3/s): fully melted plastic
# and good layer bonding, which matters most on big nozzles
QUALITY_FLOW = 10
MAX_ACCEL = 20000

def tier_makes_sense(n, h, tier, nozzle):
    """As few profiles as possible: a tier only where it changes the print.
    Fast: only where it makes the main extrusion (inner walls + infill) at least
    15% faster after Orca's flow cap (speed <= max volumetric speed / line
    width / layer height), judged with the fastest filament. On a 120x120x30
    block that is -31..-43% print time; elsewhere it was under 11%.
    Precision: detail to standard layers (up to half the nozzle size) on the
    0.4-1.0 nozzles; it caps the melt rate at QUALITY_FLOW, so on big nozzles
    it is much slower than Balanced (which runs at the hotend's limit). The 0.2
    nozzle never gets near that flow, its Balanced is already slow."""
    if tier == "Balanced":
        return True
    if tier == "Precision":
        return n in (0.4, 0.6, 0.8, 1.0) and h / n <= 0.5
    flow = max(m["vol"] for k, m in MATERIALS.items() if k != "PLA Speed Benchy")
    inner, sparse = nozzle["speed"][1:3]
    def main(t):
        f = TIERS[t]["speed"]
        cap = flow / (n * 1.125 * h)
        return (min(inner * f, MAX_SPEED, cap) + min(sparse * f, MAX_SPEED, cap)) / 2
    return main("Fast") >= 1.15 * main("Balanced")

def process_name(h, n, tier="Balanced"):
    t = "" if tier == "Balanced" else f" {tier}"
    return f"{h:.2f}mm {label(h, n)}{t} @{BRAND} {n:.1f}"

START_GCODE = (
    "; START_PRINT: chamber heat soak (ABS/ASA), adaptive glass soak, hot Z\n"
    "; re-home, adaptive mesh, nozzle deep clean, true zero touch, line purge\n"
    "SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]\n"
    "START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] CHAMBER_TEMP=[overall_chamber_temperature]\n"
    "M83\n"
    "G92 E0"
)
LAYER_GCODE = ";AFTER_LAYER_CHANGE\n;[layer_z]\nG92 E0\nSET_PRINT_STATS_INFO CURRENT_LAYER={layer_num + 1}"

def write(kind, name, data):
    d = os.path.join(OUT, kind)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".json"), "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------------- machines
user_host = {
    "print_host": "",
    "printer_agent": "moonraker",
    "printer_extruder_id": ["1"],
    "printer_extruder_variant": ["Direct Drive Standard"],
}
for n, p in NOZZLES.items():
    name = printer_name(n)
    write("machine", name, {
        "type": "machine",
        "name": name,
        "inherits": p["parent"],
        "from": "User",
        "instantiation": "true",
        "version": VERSION,
        "printer_settings_id": name,
        **user_host,
        "nozzle_diameter": [fmt(n)],
        "min_layer_height": [fmt(p["layers"][0])],
        "max_layer_height": [fmt(p["layers"][-1])],
        "retraction_length": [fmt(p["retract"])],
        "retraction_speed": ["40"],
        "deretraction_speed": ["40"],
        "z_hop": [fmt(p["zhop"])],
        "machine_start_gcode": START_GCODE,
        "machine_end_gcode": "END_PRINT",
        "layer_change_gcode": LAYER_GCODE,
        "change_filament_gcode": "M600",
        "machine_pause_gcode": "PAUSE",
        "thumbnails": ["96x96", "300x300"],
        "thumbnails_format": "PNG",
        "default_print_profile": process_name(min(p["layers"], key=lambda h: abs(h / n - 0.5)), n),
        "default_filament_profile": [f"PETG @{BRAND}"],
    })

# ---------------------------------------------------------------- filaments
MATERIALS = {
    # Kalico MPC feed-forward uses density/heat capacity; M141 sets the
    # temperature at which the chamber fan starts (pellcorp temperature_fan)
    "PLA":  dict(parent="Creality Generic PLA @K1-all", nozzle=220, bed=60, density=1.25, heat=1.8,
                 vol=20, pa=0.04, chamber=35, aux=70, fan=(100, 100), flow=0.98),
    "PETG": dict(parent="Creality Generic PETG @K1-all", nozzle=250, bed=70, density=1.27, heat=1.8,
                 vol=14, pa=0.046, chamber=40, aux=0, fan=(30, 80), flow=0.99),
    # PLA variants
    "PLA Rapid": dict(parent="Creality Generic PLA High Speed @K1-all", nozzle=225, bed=60, density=1.24, heat=1.8,
                 vol=23, pa=0.04, chamber=35, aux=70, fan=(100, 100), flow=0.98),
    "PLA Silk": dict(parent="Creality Generic PLA Silk @K1-all", nozzle=220, bed=60, density=1.24, heat=1.8,
                 vol=8, pa=0.04, chamber=35, aux=70, fan=(100, 100), flow=0.98),
    "PLA+":     dict(parent="Creality Generic PLA @K1-all", nozzle=225, bed=60, density=1.24, heat=1.8,
                 vol=18, pa=0.04, chamber=35, aux=70, fan=(100, 100), flow=0.98),
    "PLA Matte": dict(parent="Creality Generic PLA Matte @K1-all", nozzle=220, bed=60, density=1.24, heat=1.8,
                 vol=18, pa=0.04, chamber=35, aux=70, fan=(100, 100), flow=0.98),
    # PETG variants (Creality has none; Rapid = the Elegoo Rapid PETG that printed the Benchy)
    # PA 0.046: Orca PA test on PETG Rapid, 0.4 nozzle, 2026-09-28 (0.040-0.052 all looked good)
    "PETG Rapid": dict(parent="Creality Generic PETG @K1-all", nozzle=250, bed=70, density=1.27, heat=1.8,
                 vol=18, pa=0.046, chamber=40, aux=0, fan=(30, 80), flow=0.99),
    "PETG Silk": dict(parent="Creality Generic PETG @K1-all", nozzle=245, bed=70, density=1.27, heat=1.8,
                 vol=8, pa=0.046, chamber=40, aux=0, fan=(30, 60), flow=0.99),
    "PETG+":    dict(parent="Creality Generic PETG @K1-all", nozzle=245, bed=70, density=1.27, heat=1.8,
                 vol=14, pa=0.046, chamber=40, aux=0, fan=(30, 80), flow=0.99),
    "PETG Matte": dict(parent="Creality Generic PETG @K1-all", nozzle=245, bed=70, density=1.27, heat=1.8,
                 vol=12, pa=0.046, chamber=40, aux=0, fan=(30, 70), flow=0.99),
    # for the Speed Benchy processes: fast PLA pushed to the stock K1 hotend's
    # rated maximum (32mm3/s, needs 255C), every fan flat out, 1s layer time
    "PLA Speed Benchy": dict(parent="Creality Generic PLA High Speed @K1-all", nozzle=255, bed=60, density=1.24, heat=1.8,
                 vol=32, pa=0.03, chamber=35, aux=100, fan=(100, 100), flow=0.98,
                 printers=[printer_name(0.4), printer_name(0.8), printer_name(1.0)],
                 extra={"nozzle_temperature_initial_layer": ["250"], "slow_down_layer_time": ["1"],
                        "slow_down_min_speed": ["20"], "close_fan_the_first_x_layers": ["1"]}),
    "ABS":  dict(parent="Creality Generic ABS @K1-all", nozzle=260, bed=100, density=1.04, heat=1.6,
                 vol=16, pa=0.04, chamber=60, aux=0, fan=(0, 30), flow=0.98, chamber_soak=45),
    "ASA":  dict(parent="Creality Generic ASA @K1-all", nozzle=260, bed=100, density=1.07, heat=1.6,
                 vol=16, pa=0.04, chamber=60, aux=0, fan=(0, 30), flow=0.98, chamber_soak=45),
}
# ---------------------------------------------------------------- processes
for n, p, h, tier in [(n, p, h, t) for n, p in NOZZLES.items() for h in p["layers"] for t in TIERS
                      if tier_makes_sense(n, h, t, p)]:
        T = TIERS[tier]
        def sp(v, f=T["speed"], width=n * 1.125):
            v = min(MAX_SPEED, v * f)
            if tier == "Precision":
                v = min(v, QUALITY_FLOW / (width * h))
            return str(max(10, round(v)))
        ac = lambda v, f: str(min(MAX_ACCEL, int(round(v * f / 100.0) * 100)))
        outer, inner, sparse, solid, top_s, gap, bridge, support, first = p["speed"]
        a = p["accel"]
        fine = h / n <= 0.3
        name = process_name(h, n, tier)
        write("process", name, {
            "type": "process",
            "name": name,
            "inherits": "0.20mm Standard @Creality K1Max (0.4 nozzle)",
            "from": "User",
            "instantiation": "true",
            "version": VERSION,
            "print_settings_id": name,
            "compatible_printers": [printer_name(n)],
            "compatible_printers_condition": "",
            "layer_height": fmt(h),
            "initial_layer_print_height": fmt(p["first"]),
            # line widths relative to the nozzle
            "line_width": fmt(n * 1.05),
            "outer_wall_line_width": fmt(n * 1.05),
            "inner_wall_line_width": fmt(n * 1.125),
            "sparse_infill_line_width": fmt(n * 1.125),
            "internal_solid_infill_line_width": fmt(n * 1.05),
            "top_surface_line_width": fmt(n * 1.0),
            "support_line_width": fmt(n * 1.0),
            "initial_layer_line_width": fmt(n * 1.25),
            # shells
            "wall_loops": str(p["walls"]),
            "wall_generator": p["generator"],
            # 0.2: gap fill between walls fails in Orca 2.4.2 (negative line
            # spacing on e.g. Benchy at 0.06/0.08); Arachne covers those gaps
            "gap_fill_target": "topbottom" if n == 0.2 else "everywhere",
            "top_shell_layers": "3",
            "top_shell_thickness": fmt(p["top"]),
            "bottom_shell_layers": "3",
            "bottom_shell_thickness": fmt(p["bottom"]),
            "elefant_foot_compensation": fmt(p["efc"]),
            # speeds; the filament's max volumetric speed caps the big nozzles
            "outer_wall_speed": sp(outer * (0.75 if fine else 1), T["outer"], n * 1.05),
            "inner_wall_speed": sp(inner),
            "sparse_infill_speed": sp(sparse),
            "internal_solid_infill_speed": sp(solid, width=n * 1.05),
            "top_surface_speed": sp(top_s, width=n * 1.0),
            "gap_infill_speed": sp(gap, width=n * 1.0),
            "bridge_speed": str(bridge),
            "support_speed": sp(support),
            "support_interface_speed": sp(support * 0.6),
            "initial_layer_speed": str(first),
            "initial_layer_infill_speed": str(first),
            "travel_speed": str(T["travel"]),
            # input shaper: X 3hump_ei 77.6Hz, Y ei 52Hz -> Klipper suggests
            # <= ~4400-5800 mm/s^2 for crisp corners, so keep walls around there
            "default_acceleration": ac(a["default"], T["acc"][3]),
            "outer_wall_acceleration": ac(a["outer"], T["acc"][0]),
            "inner_wall_acceleration": ac(a["inner"], T["acc"][1]),
            "top_surface_acceleration": ac(a["top"], T["acc"][2]),
            "travel_acceleration": ac(a["travel"], T["acc"][4]),
            "initial_layer_acceleration": "1000",
            "bridge_acceleration": "50%",
            # jerk 0 = Orca emits no SQUARE_CORNER_VELOCITY, so the printer's 5
            # (what the input shaper was tuned with) stays; Creality's 20 overrode it
            "default_jerk": "0", "outer_wall_jerk": "0", "inner_wall_jerk": "0",
            "infill_jerk": "0", "top_surface_jerk": "0", "initial_layer_jerk": "0",
            "travel_jerk": "0",
            # ACCEL_TO_DECEL is obsolete in Kalico (minimum_cruise_ratio instead)
            "accel_to_decel_enable": "0",
            # supports
            "support_top_z_distance": fmt(max(h, 0.1)),
            "support_bottom_z_distance": fmt(max(h, 0.1)),
            "support_object_xy_distance": fmt(n * 0.875),
            # Klipper [gcode_arcs] resolution is 1.0mm, which would facet small
            # arcs; let Orca emit fine line segments instead
            "enable_arc_fitting": "0",
            # object outlines drive the adaptive bed mesh and object exclusion
            "gcode_label_objects": "1",
            "exclude_object": "1",
            "filename_format": "{input_filename_base}_" + f"{n:.1f}" + "n_{layer_height}mm_{filament_type[initial_tool]}_{print_time}.gcode",
        })

# ---------------------------------------------------------------- speed benchy
# Speed 3DBenchy with the "PLA Speed Benchy" filament. On the 0.4 the path
# length (not the flow) is the limit, so it prints extra-wide 0.55mm lines.
SPEED_BENCHY = {0.4: 0.32, 0.8: 0.48, 1.0: 0.60}
for n, h in SPEED_BENCHY.items():
    base = json.load(open(os.path.join(OUT, "process",
                      process_name(h, n) + ".json")))
    # name starts with letters so Orca sorts these below all the layer heights
    name = f"Speed Benchy {h:.2f}mm @{BRAND} {n:.1f}"
    v = "600"
    base.update({
        "name": name, "print_settings_id": name,
        "outer_wall_speed": v, "inner_wall_speed": v, "sparse_infill_speed": v,
        "internal_solid_infill_speed": v, "top_surface_speed": v, "gap_infill_speed": v,
        "travel_speed": "800",
        "default_acceleration": "20000", "outer_wall_acceleration": "20000",
        "inner_wall_acceleration": "20000", "top_surface_acceleration": "20000",
        "travel_acceleration": "20000",
        "wall_loops": "2", "sparse_infill_density": "10%", "sparse_infill_pattern": "lightning",
        "top_shell_layers": "3", "top_shell_thickness": "0",
        "bottom_shell_layers": "2", "bottom_shell_thickness": "0",
        # the first layer stays gentle so it sticks
        "initial_layer_speed": "80", "initial_layer_infill_speed": "120",
        "initial_layer_acceleration": "5000",
        "brim_type": "no_brim", "skirt_loops": "0", "only_one_wall_top": "1",
    })
    if n == 0.4:
        # wider lines = fewer passes; the curvy hull never reaches 600mm/s anyway
        for k in ("line_width", "outer_wall_line_width", "inner_wall_line_width",
                  "sparse_infill_line_width", "internal_solid_infill_line_width",
                  "top_surface_line_width"):
            base[k] = "0.55"
        for k in ("outer_wall_speed", "inner_wall_speed", "sparse_infill_speed",
                  "internal_solid_infill_speed", "top_surface_speed", "gap_infill_speed"):
            base[k] = "800"
    write("process", name, base)

all_printers = [printer_name(n) for n in NOZZLES]
for mat, m in MATERIALS.items():
    name = f"{mat} @{BRAND}"
    bed = str(m["bed"])
    write("filament", name, {
        "type": "filament",
        "name": name,
        "inherits": m["parent"],
        "from": "User",
        "instantiation": "true",
        "version": VERSION,
        "filament_settings_id": [name],
        "compatible_printers": m.get("printers", all_printers),
        "compatible_printers_condition": "",
        "nozzle_temperature": [str(m["nozzle"])],
        "nozzle_temperature_initial_layer": [str(m["nozzle"])],
        "hot_plate_temp": [bed], "hot_plate_temp_initial_layer": [bed],
        "textured_plate_temp": [bed], "textured_plate_temp_initial_layer": [bed],
        "eng_plate_temp": [bed], "eng_plate_temp_initial_layer": [bed],
        "cool_plate_temp": [bed], "cool_plate_temp_initial_layer": [bed],
        "supertack_plate_temp": [bed], "supertack_plate_temp_initial_layer": [bed],
        "filament_density": [fmt(m["density"])],
        "filament_max_volumetric_speed": [str(m["vol"])],
        "filament_flow_ratio": [fmt(m["flow"])],
        "enable_pressure_advance": ["1"],
        "pressure_advance": [fmt(m["pa"])],
        "fan_min_speed": [str(m["fan"][0])],
        "fan_max_speed": [str(m["fan"][1])],
        "additional_cooling_fan_speed": [str(m["aux"])],
        # Chamber Heat Soak on the printer waits for this (0 = no wait)
        "chamber_temperature": [str(m.get("chamber_soak", 0))],
        **m.get("extra", {}),
        "filament_start_gcode": ["; filament start gcode\n"
                                 f"MPC_SET HEATER=extruder FILAMENT_DENSITY={fmt(m['density'])} FILAMENT_HEAT_CAPACITY={fmt(m['heat'])}\n"
                                 f"M141 S{m['chamber']}"],
    })

print("written to", OUT)
