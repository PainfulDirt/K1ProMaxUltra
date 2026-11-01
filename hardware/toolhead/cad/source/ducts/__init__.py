"""Part-cooling ducts for the K1 Max toolhead (Duct-Design & CFD agent).

API:
    build_ducts(params) -> dict of build123d solids ("body", "air", "body_cfd", "fan_<id>", "stub_<id>")
    build_info(params, parts) -> checks, mass, ports, tabs
    PARAM_SETS[name]() -> parameter set (STOCK is a CFD-only baseline, see simulations/cfd/cases)
    PARAMS_FINAL -> the released parameter set
    write_interface_file(params, version, final) -> duct_interface.json
"""
from .duct_generator import (PARAM_SETS, PARAMS_FINAL, build_ducts, build_info, get_params,  # noqa: F401
                             interface_json, wall_report, write_interface_file)
