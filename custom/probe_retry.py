# PROBE that survives the Microprobe's rare deploy glitch
#
# The Microprobe reads "triggered" while its pin is stowed. About once in a
# few hundred samples a deploy isn't seen in time and PROBE fails with "Probe
# triggered prior to movement" (2026-11-17: it cancelled a print in the glass
# soak; 140 deploys in a row, hot and with only 60 ms to deploy, all worked).
# PROBE_RETRY takes PROBE's parameters; on exactly that error it stows the
# pin, lifts, waits, goes back to where the probe started and tries again.
# Every other error stops as before. Retries are counted in variables.cfg
# (probe_glitches).
#
#   [probe_retry]
#   retries: 2         # extra tries per PROBE_RETRY (RETRIES= overrides)
#   lift: 3.0          # mm up after a glitch
#   stow_gcode: PROBE_UP   # run first if that macro exists
#
# Lives in pellcorp-overrides/custom and is symlinked into klippy/plugins.
#
# This file may be distributed under the terms of the GNU GPLv3 license.

GLITCH = "triggered prior to movement"
OWN = ("RETRIES",)


class ProbeRetry:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.retries = config.getint("retries", 2, minval=0, maxval=5)
        self.lift = config.getfloat("lift", 3.0, above=0.0, maxval=20.0)
        self.stow = config.get("stow_gcode", "PROBE_UP")
        gcode = self.printer.lookup_object("gcode")
        self.gcode = gcode
        gcode.register_command(
            "PROBE_RETRY", self.cmd_PROBE_RETRY,
            desc="PROBE (same parameters) that retries the Microprobe's"
                 " 'triggered prior to movement' glitch (RETRIES=)")

    def _count(self):
        sv = self.printer.lookup_object("save_variables", None)
        if sv is None:
            return None
        n = int((getattr(sv, "allVariables", None) or {}).get(
            "probe_glitches", 0)) + 1
        self.gcode.run_script_from_command(
            "SAVE_VARIABLE VARIABLE=probe_glitches VALUE=%d" % (n,))
        return n

    def cmd_PROBE_RETRY(self, gcmd):
        retries = gcmd.get_int("RETRIES", self.retries, minval=0, maxval=5)
        params = gcmd.get_command_parameters()
        probe = " ".join(["PROBE"] + ["%s=%s" % (k, v) for k, v in
                                      params.items() if k.upper() not in OWN])
        gm = self.printer.lookup_object("gcode_move")
        x, y, z = gm.get_status()["gcode_position"][:3]
        run = self.gcode.run_script_from_command
        for attempt in range(retries + 1):
            try:
                run(probe)
                return
            except self.printer.command_error as e:
                if GLITCH not in str(e) or attempt == retries:
                    raise
                # Kalico ends the probe's multi-probe session only on the
                # gcode:command_error event, which a caught error never
                # sends: end it here, else the retry runs in a stale session
                pr = self.printer.lookup_object("probe", None)
                if getattr(pr, "multi_probe_pending", False):
                    pr.multi_probe_end()
                n = self._count()
                gcmd.respond_info(
                    "Microprobe: deploy glitch at X%.1f Y%.1f (%s), retry"
                    " %d/%d%s" % (x, y, e, attempt + 1, retries,
                                  "" if n is None else
                                  ", %d so far (probe_glitches)" % (n,)))
                stow = self.stow if self.printer.lookup_object(
                    "gcode_macro %s" % (self.stow,), None) is not None \
                    else None
                run("SAVE_GCODE_STATE NAME=_probe_retry\n%sG90\n"
                    "G0 Z%.3f F600\nG4 P500\nG0 X%.3f Y%.3f Z%.3f F600\n"
                    "RESTORE_GCODE_STATE NAME=_probe_retry" % (
                        stow + "\n" if stow else "", z + self.lift,
                        x, y, z))


def load_config(config):
    return ProbeRetry(config)
