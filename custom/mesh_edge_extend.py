# Extend the bed mesh to the right edge of the bed with load cell nozzle taps
#
# The Microprobe sits 33mm left of the nozzle, so the mesh stops at X273 and
# Klipper holds the last column flat from there to the bed edge. This taps the
# nozzle (load cells) just inside the mesh edge and near the bed edge on a few
# rows, and extends the active mesh with the measured slope.
#
# Only the difference between the two taps in a row is used, so any constant
# offset between nozzle and probe (or a small blob on the nozzle) cancels out.
#
# Lives in printer_data/config and is symlinked into klippy/plugins.
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
import math

from ..extras import bed_mesh


class BedMeshExtend:
    def __init__(self, config):
        self.printer = config.get_printer()
        # nozzle X of the outer taps; the sheet edge is at ~300
        self.edge_x = config.getfloat("edge_x", 296.0)
        # the extended mesh never goes past this X
        self.max_x = config.getfloat("max_x", 300.0)
        self.rows = config.getint("rows", 5, minval=2)
        self.samples = config.getint("samples", 2, minval=1)
        # Z (above the mesh) to travel at between taps
        self.clearance = config.getfloat("clearance", 1.5, above=0.5)
        self.speed = config.getfloat("speed", 150.0, above=0.0)
        # extend when objects reach this far past the mesh edge
        self.margin = config.getfloat("margin", 2.0, minval=0.0)
        # a larger edge-to-mesh difference than this means a bad tap
        self.max_delta = config.getfloat("max_delta", 0.3, above=0.0)
        self.gcode = self.printer.lookup_object("gcode")
        self.gcode.register_command(
            "BED_MESH_EXTEND",
            self.cmd_BED_MESH_EXTEND,
            desc=self.cmd_BED_MESH_EXTEND_help,
        )

    def _objects_max_x(self):
        eo = self.printer.lookup_object("exclude_object", None)
        if eo is None:
            return None
        objects = eo.get_status(self.printer.get_reactor().monotonic()).get(
            "objects", []
        )
        xs = [p[0] for o in objects for p in o.get("polygon", [])]
        return max(xs) if xs else None

    def _tap(self, x, y):
        run = self.gcode.run_script_from_command
        run(
            "G90\nG0 Z%.3f F600\nG0 X%.3f Y%.3f F%d\n"
            "LOAD_CELL_PROBE SAMPLES=%d SAMPLES_RESULT=median"
            % (self.clearance, x, y, self.speed * 60, self.samples)
        )
        lc = self.printer.lookup_object("load_cell_probe").get_printer_probe()
        z = lc.last_z_result
        # Kalico adds axis twist compensation to every probe; it corrects the
        # Microprobe's side offset and does not apply to the nozzle itself
        atc = self.printer.lookup_object("axis_twist_compensation", None)
        if atc is not None:
            z -= atc.get_z_compensation_value([x, y, z])
        run("G0 Z%.3f F600" % (self.clearance,))
        return z

    cmd_BED_MESH_EXTEND_help = (
        "Extend the active bed mesh to the right bed edge using load cell taps"
    )

    def cmd_BED_MESH_EXTEND(self, gcmd):
        bm = self.printer.lookup_object("bed_mesh")
        mesh = bm.get_mesh()
        if mesh is None:
            raise gcmd.error("BED_MESH_EXTEND: no active bed mesh")
        params = dict(mesh.get_mesh_params())
        old_max = params["max_x"]
        force = gcmd.get_int("FORCE", 0)
        target = gcmd.get_float("MAX_X", None)
        if target is None:
            obj_max = self._objects_max_x()
            if obj_max is None:
                target = self.max_x
            else:
                target = obj_max + self.margin
        target = min(target, self.max_x)
        if target <= old_max + 0.5:
            if not force:
                gcmd.respond_info(
                    "BED_MESH_EXTEND: print ends at X%.1f, inside the mesh "
                    "(X%.1f), nothing to do" % (target, old_max)
                )
                return
            target = self.max_x

        # outer tap: near the bed edge, but at least 8mm out from the mesh
        edge_x = min(self.edge_x, max(target, old_max + 8.0))
        y0, y1 = params["min_y"], params["max_y"]
        n = min(self.rows, params["y_count"])
        tap_ys = [y0 + (y1 - y0) * i / (n - 1) for i in range(n)]

        gcmd.respond_info(
            "BED_MESH_EXTEND: extending mesh X%.1f -> X%.1f, tapping X%.1f/X%.1f"
            " on %d rows" % (old_max, target, old_max, edge_x, n)
        )
        # never abort the print over this: on any problem keep the normal mesh
        slopes = []
        try:
            # the first tap after the nozzle wipe reads off (0.02-0.04mm in
            # testing), so make one that is not used
            self._tap(old_max, tap_ys[0])
        except self.printer.command_error as e:
            gcmd.respond_info(
                "BED_MESH_EXTEND: tap failed (%s), keeping the original"
                " mesh" % (e,)
            )
            return
        for y in tap_ys:
            try:
                z_in = self._tap(old_max, y)
                z_out = self._tap(edge_x, y)
            except self.printer.command_error as e:
                gcmd.respond_info(
                    "BED_MESH_EXTEND: tap failed (%s), keeping the original"
                    " mesh" % (e,)
                )
                self.gcode.run_script_from_command("G0 Z%.3f F600" % (self.clearance,))
                return
            delta = z_out - z_in
            if abs(delta) > self.max_delta:
                gcmd.respond_info(
                    "BED_MESH_EXTEND: edge tap at Y%.1f differs %.3fmm from the"
                    " mesh edge, keeping the original mesh" % (y, delta)
                )
                return
            slopes.append(delta / (edge_x - old_max))
            gcmd.respond_info(
                "  Y%5.1f: bed at X%.0f is %+.3fmm vs X%.0f"
                % (y, edge_x, delta, old_max)
            )

        def slope_at(y):
            if y <= tap_ys[0]:
                return slopes[0]
            for i in range(1, len(tap_ys)):
                if y <= tap_ys[i]:
                    t = (y - tap_ys[i - 1]) / (tap_ys[i] - tap_ys[i - 1])
                    return bed_mesh.lerp(t, slopes[i - 1], slopes[i])
            return slopes[-1]

        # new grid with the same column spacing, reaching the target
        x0, x_cnt = params["min_x"], params["x_count"]
        dx = (old_max - x0) / (x_cnt - 1)
        new_cnt = x_cnt + max(1, int(math.ceil((target - old_max) / dx - 1e-6)))
        y_cnt = params["y_count"]
        new_params = dict(params)
        new_params["max_x"] = target
        new_params["x_count"] = new_cnt
        if new_params["algo"] == "lagrange" and new_cnt > 6:
            # lagrange is limited to 6 points per axis
            if y_cnt >= 4:
                new_params["algo"] = "bicubic"
            else:
                new_params["algo"] = "direct"
                new_params["mesh_x_pps"] = new_params["mesh_y_pps"] = 0

        matrix = []
        for j in range(y_cnt):
            y = y0 + (y1 - y0) * j / (y_cnt - 1)
            edge_val = mesh.calc_z(old_max, y)
            slope = slope_at(y)
            row = []
            for i in range(new_cnt):
                x = x0 + (target - x0) * i / (new_cnt - 1)
                if x <= old_max:
                    row.append(mesh.calc_z(x, y))
                else:
                    row.append(edge_val + slope * (x - old_max))
            matrix.append(row)

        new_mesh = bed_mesh.ZMesh(new_params, mesh.get_profile_name())
        try:
            new_mesh.build_mesh(matrix)
            bm.set_mesh(new_mesh)
        except (bed_mesh.BedMeshError, self.printer.command_error) as e:
            # set_mesh leaves no mesh on error, so put the original back
            bm.set_mesh(mesh)
            gcmd.respond_info(
                "BED_MESH_EXTEND: %s, keeping the original mesh" % (e,)
            )
            return
        logging.info(
            "mesh_edge_extend: X%.1f -> X%.1f, %d -> %d columns, slopes %s"
            % (old_max, target, x_cnt, new_cnt, slopes)
        )
        gcmd.respond_info(
            "BED_MESH_EXTEND: mesh now reaches X%.1f (%dx%d)"
            % (target, new_cnt, y_cnt)
        )


def load_config(config):
    return BedMeshExtend(config)
