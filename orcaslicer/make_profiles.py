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

def process_name(h, n):
    return f"{h:.2f}mm {label(h, n)} @{BRAND} {n:.1f}"

START_GCODE = (
    "; START_PRINT: glass soak, hot Z re-home, adaptive mesh, nozzle wipe,\n"
    "; load-cell nozzle touch (Z=0), line purge - see tuning.cfg on the printer\n"
    "SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]\n"
    "START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single]\n"
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

# ---------------------------------------------------------------- processes
for n, p in NOZZLES.items():
    outer, inner, sparse, solid, top_s, gap, bridge, support, first = p["speed"]
    a = p["accel"]
    for h in p["layers"]:
        fine = h / n <= 0.3
        name = process_name(h, n)
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
            "outer_wall_speed": str(round(outer * (0.75 if fine else 1))),
            "inner_wall_speed": str(inner),
            "sparse_infill_speed": str(sparse),
            "internal_solid_infill_speed": str(solid),
            "top_surface_speed": str(top_s),
            "gap_infill_speed": str(gap),
            "bridge_speed": str(bridge),
            "support_speed": str(support),
            "support_interface_speed": str(round(support * 0.6)),
            "initial_layer_speed": str(first),
            "initial_layer_infill_speed": str(first),
            "travel_speed": "500",
            # input shaper: X 3hump_ei 77.6Hz, Y ei 52Hz -> Klipper suggests
            # <= ~4400-5800 mm/s^2 for crisp corners, so keep walls around there
            "default_acceleration": str(a["default"]),
            "outer_wall_acceleration": str(a["outer"]),
            "inner_wall_acceleration": str(a["inner"]),
            "top_surface_acceleration": str(a["top"]),
            "travel_acceleration": str(a["travel"]),
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
    "ABS":  dict(parent="Creality Generic ABS @K1-all", nozzle=260, bed=100, density=1.04, heat=1.6,
                 vol=16, pa=0.04, chamber=60, aux=0, fan=(0, 30), flow=0.98),
    "ASA":  dict(parent="Creality Generic ASA @K1-all", nozzle=260, bed=100, density=1.07, heat=1.6,
                 vol=16, pa=0.04, chamber=60, aux=0, fan=(0, 30), flow=0.98),
}
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
        "compatible_printers": all_printers,
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
        "filament_start_gcode": ["; filament start gcode\n"
                                 f"MPC_SET HEATER=extruder FILAMENT_DENSITY={fmt(m['density'])} FILAMENT_HEAT_CAPACITY={fmt(m['heat'])}\n"
                                 f"M141 S{m['chamber']}"],
    })

print("written to", OUT)
