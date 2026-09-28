# Axis twist calibration with the load cells instead of the paper test
#
# At spots along X, the Microprobe measures the bed and the nozzle touches the
# same spot with the load cells. The difference between the two varies along
# X by the carriage twist; that variation becomes [axis_twist_compensation].
#
# Lives in pellcorp-overrides/custom and is symlinked into klippy/plugins.
#
# This file may be distributed under the terms of the GNU GPLv3 license.


class TwistTouch:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.passes = config.getint("passes", 2, minval=1)
        self.samples = config.getint("samples", 3, minval=1)
        self.points = config.getint("points", 7, minval=3)
        # a spot whose passes disagree by more than this makes the run invalid
        self.max_pass_diff = config.getfloat("max_pass_diff", 0.04, above=0.0)
        # never apply a result this far from the current values
        self.max_change = config.getfloat("max_change", 0.1, above=0.0)
        self.gcode = self.printer.lookup_object("gcode")
        self.gcode.register_command(
            "AXIS_TWIST_TOUCH_CALIBRATE",
            self.cmd_AXIS_TWIST_TOUCH_CALIBRATE,
            desc=self.cmd_AXIS_TWIST_TOUCH_CALIBRATE_help,
        )

    def _run(self, script):
        self.gcode.run_script_from_command(script)

    cmd_AXIS_TWIST_TOUCH_CALIBRATE_help = (
        "Measure axis twist with the load cells (nozzle) against the probe"
    )

    def cmd_AXIS_TWIST_TOUCH_CALIBRATE(self, gcmd):
        atc = self.printer.lookup_object("axis_twist_compensation", None)
        if atc is None:
            raise gcmd.error("AXIS_TWIST_TOUCH_CALIBRATE: no [axis_twist_compensation]")
        probe = self.printer.lookup_object("probe")
        lc = self.printer.lookup_object("load_cell_probe").get_printer_probe()
        x_off, y_off = probe.get_offsets()[:2]
        x0, x1, y = atc.calibrate_start_x, atc.calibrate_end_x, atc.calibrate_y
        n = self.points
        xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
        samples = gcmd.get_int("SAMPLES", self.samples, minval=1)

        old = (
            list(atc.z_compensations),
            atc.compensation_start_x,
            atc.compensation_end_x,
        )

        def restore(msg):
            atc.z_compensations = old[0]
            atc.compensation_start_x = old[1]
            atc.compensation_end_x = old[2]
            gcmd.respond_info(
                "Axis twist: %s, keeping the current compensation" % (msg,)
            )

        # measure without any compensation applied
        atc.clear_compensations("X")
        gcmd.respond_info(
            "Axis twist: %d spots X%.0f-X%.0f at Y%.0f, %d passes"
            % (n, x0, x1, y, self.passes)
        )
        diffs = {x: [] for x in xs}
        try:
            self._run("G90\nG0 Z5 F900")
            # the first nozzle tap after a wipe reads off, throw it away
            self._run(
                "G0 X%.2f Y%.2f F9000\nG0 Z2 F900\nLOAD_CELL_PROBE SAMPLES=1\nG0 Z5 F900"
                % (xs[0], y)
            )
            for p in range(self.passes):
                order = xs if p % 2 == 0 else list(reversed(xs))
                for x in order:
                    self._run(
                        "G0 Z5 F900\nG0 X%.2f Y%.2f F9000\n"
                        "PROBE SAMPLES=%d SAMPLES_RESULT=median"
                        % (x - x_off, y - y_off, samples)
                    )
                    probe_z = probe.last_z_result
                    self._run(
                        "G0 Z5 F900\nG0 X%.2f Y%.2f F9000\nG0 Z2 F900\n"
                        "LOAD_CELL_PROBE SAMPLES=%d SAMPLES_RESULT=median"
                        % (x, y, samples)
                    )
                    diffs[x].append(probe_z - lc.last_z_result)
                self._run("G0 Z5 F900")
        except self.printer.command_error as e:
            restore("measuring failed (%s)" % (e,))
            return

        spread = max(max(v) - min(v) for v in diffs.values())
        if self.passes > 1 and spread > self.max_pass_diff:
            restore("passes disagree by %.3fmm" % (spread,))
            return
        means = [sum(diffs[x]) / len(diffs[x]) for x in xs]
        avg = sum(means) / len(means)
        comp = [avg - m for m in means]
        if len(old[0]) == len(comp):
            change = max(abs(a - b) for a, b in zip(comp, old[0]))
            if change > self.max_change:
                restore("result differs %.3fmm from the current values" % (change,))
                return
        # Klipper looks the value up by the nozzle X at the moment it probes,
        # which is the spot minus the probe x_offset
        start, end = x0 - x_off, x1 - x_off
        atc.z_compensations = comp
        atc.compensation_start_x = start
        atc.compensation_end_x = end
        configfile = self.printer.lookup_object("configfile")
        section = "axis_twist_compensation"
        configfile.set(section, "z_compensations", ", ".join("%.6f" % c for c in comp))
        configfile.set(section, "compensation_start_x", "%.1f" % start)
        configfile.set(section, "compensation_end_x", "%.1f" % end)
        gcmd.respond_info(
            "Axis twist: %s (probe-nozzle offset %.3f, pass spread %.3f). "
            "In use now, saved by the next SAVE_CONFIG"
            % (", ".join("%+.3f" % c for c in comp), avg, spread)
        )


def load_config(config):
    return TwistTouch(config)
