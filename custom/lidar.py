# K1 Max LiDAR (Creality "AI LiDAR") for Kalico
#
# The LiDAR is a line-laser height sensor on the toolhead: one capture is a
# ~29mm wide height profile (~1500 points, in um) across X. Creality's
# cx_ai_middleware (started by lidar-start.sh) drives it and answers JSON
# requests on a unix socket; this plugin moves the toolhead and collects the
# profiles, so scans can run inside a print.
#
# The K1 has ~200MB of RAM and a slow CPU, and a heavy job starves Klipper
# (MCU "Rescheduled timer in the past"). So everything is reduced while
# scanning: each stop becomes one averaged profile of 580 bins (0.05mm), and
# the analysis is plain Python done a few rows at a time.
#
#   [lidar]
#   x_offset: -36       # laser line centre relative to the nozzle
#   y_offset: -21.2
#   x_dir: -1           # profile x runs towards printer -X
#
# Commands:
#   LIDAR_STATUS
#   LIDAR_SCAN NAME= X= Y0= Y1= [STEP=0.4] [Z=3] [CAPTURES=3]
#       X/Y are where the laser looks (not the nozzle); one profile per Y
#   LIDAR_PA_ANALYZE BASE= SCAN= [APPLY=1]
#       compares the scan of the printed PA test with the bare-plate scan
#   LIDAR_PA_CALIBRATE EXTRUDER_TEMP= BED_TEMP= [PA_START=0] [PA_STEP=0.01]
#       [LINES=9] [X=130] [Y=100]
#       writes the PA test as a print and starts it: START_PRINT (with the
#       bare-plate scan after the nozzle touch, before the purge), the test
#       lines, cool down, scan, analysis, END_PRINT
#
# Lives in pellcorp-overrides/custom and is symlinked into klippy/plugins.
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import array
import json
import math
import os
import socket

ETX = b"\x03"
NAN = float("nan")

# profile bins: 0.05mm from -14.5 to +14.5mm of the laser line
BIN = 0.05
BIN_MIN = -14.5
NBINS = 580


def bin_center(b):
    return BIN_MIN + (b + 0.5) * BIN


def reduce_caps(caps):
    """Average the captures of one stop into NBINS bins (mm, NaN = empty)."""
    s = [0.0] * NBINS
    n = [0] * NBINS
    for c in caps:
        for p in c:
            b = int((p[0] * 0.001 - BIN_MIN) / BIN)
            if 0 <= b < NBINS:
                s[b] += p[2]
                n[b] += 1
    return array.array("f", [s[i] * 0.001 / n[i] if n[i] else NAN
                             for i in range(NBINS)])


def median(v):
    v = sorted(x for x in v if x == x)
    if not v:
        return NAN
    m = len(v) // 2
    return v[m] if len(v) % 2 else 0.5 * (v[m - 1] + v[m])


def linfit(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0, my
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return k, my - k * mx


def line_areas(base, scan, x, x_dir, line_x, half=1.2):
    """Plastic cross-section (mm2) at each line X in one row.

    base/scan: binned distances of the same row without and with the print.
    """
    X = [x + x_dir * bin_center(b) for b in range(NBINS)]
    h = [b - s for b, s in zip(base, scan)]   # plastic is closer
    # drift between the two scans (tilt + offset) from the bare parts
    fx, fy = [], []
    for b in range(NBINS):
        if h[b] == h[b] and abs(h[b]) < 0.08 and all(
                abs(X[b] - lx) > 0.9 for lx in line_x):
            fx.append(X[b])
            fy.append(h[b])
    if len(fx) > 50:
        k, c = linfit(fx, fy)
        h = [v - (k * xx + c) for v, xx in zip(h, X)]
    out = []
    for lx in line_x:
        a, cnt = 0.0, 0
        for b in range(NBINS):
            if abs(X[b] - lx) < half:
                cnt += 1
                if h[b] == h[b]:
                    a += min(max(h[b], -0.05), 0.8) * BIN
        out.append(abs(a) if cnt else NAN)
    return out


W_ACC, W_DEC, EDGE = 8.0, 3.0, 2.0


def pa_fit(ys, A, test):
    """PA from the per-row line areas A[row][line] of the PA test.

    With PA too low a line thins after speeding up and bulges after slowing
    down; too high, the other way round. Per line
      score = extra area after decelerations - missing area after
              accelerations (in mm of line, against its steady sections)
    and a straight line through score vs PA crosses zero at the right PA.
    """
    n = len(test["pa"])
    step = median([abs(b - a) for a, b in zip(ys, ys[1:])])
    bounds, y = [], test["y0"]
    for seglen, v in test["segments"]:
        bounds.append((y, y + seglen, v))
        y += seglen
    nominal = test["height"] * test["width"]

    def med(i, lo, hi):
        lo, hi = min(lo, hi), max(lo, hi)
        v = [A[r][i] for r in range(len(ys)) if lo <= ys[r] <= hi]
        return median(v) if len(v) >= 3 else NAN

    def excess(i, at, d, w, ref):
        lo, hi = sorted((at, at + d * w))
        return sum(A[r][i] - ref for r in range(len(ys))
                   if lo <= ys[r] <= hi and A[r][i] == A[r][i]) * step / ref

    report, scores, steady = [], [], []
    for i in range(n):
        d = test["dirs"][i]
        acc, dec = [], []
        for j in range(len(bounds) - 1):
            a0, a1, va = bounds[j]
            b0, b1, vb = bounds[j + 1]
            # +Y: from segment j into j+1 at a1; -Y: from j+1 into j
            cur, nxt = (va, vb) if d > 0 else (vb, va)
            w = W_ACC if nxt > cur else W_DEC
            if d > 0:
                ref = med(i, b0 + w, b1 - EDGE)
            else:
                ref = med(i, a0 + EDGE, a1 - w)
            if not ref > 0:
                continue
            (acc if nxt > cur else dec).append(excess(i, a1, d, w, ref))
        fast = median([med(i, b[0] + W_ACC, b[1] - W_ACC)
                       for b in bounds if b[2] == test["fast"]])
        steady.append(fast)
        ma = sum(acc) / len(acc) if acc else NAN
        md = sum(dec) / len(dec) if dec else NAN
        scores.append(md - ma)
        report.append(
            "  PA %.3f: line %.3f mm2 (%.0f%%), after accel %+.2f mm,"
            " after decel %+.2f mm, score %+.2f" % (
                test["pa"][i], fast, 100 * fast / nominal, ma, md, md - ma))
    res = {"ok": False, "pa_tested": test["pa"],
           "scores": [round(s, 4) if s == s else None for s in scores],
           "line_area": [round(s, 4) if s == s else None for s in steady]}
    good = [i for i in range(n)
            if scores[i] == scores[i] and steady[i] > 0.3 * nominal]
    if len(good) < 4:
        res["reason"] = "only %d of %d lines were found" % (len(good), n)
    else:
        px = [test["pa"][i] for i in good]
        sy = [scores[i] for i in good]
        k, c = linfit(px, sy)
        my = sum(sy) / len(sy)
        ss = sum((v - my) ** 2 for v in sy)
        r2 = (1 - sum((v - (k * p + c)) ** 2 for p, v in zip(px, sy)) / ss
              if ss > 0 else 0.0)
        res.update({"slope": round(k, 3), "r2": round(r2, 3)})
        if k >= 0:
            res["reason"] = "score doesn't fall with PA (r2 %.2f)" % (r2,)
        else:
            best = -c / k
            res["pa_fit"] = round(best, 4)
            lo, hi = min(test["pa"]), max(test["pa"])
            if best < lo - 0.5 * (hi - lo) / (n - 1) or best > hi:
                res["reason"] = "PA %.3f is outside the tested range" % (best,)
            elif r2 < 0.5:
                res["reason"] = "measurement too noisy (r2 %.2f)" % (r2,)
            else:
                res["ok"] = True
                res["pa"] = round(max(best, 0.0), 4)
    report.append("LiDAR PA fit: %s" % (
        "PA %.4f (r2 %.2f)" % (res["pa"], res["r2"]) if res["ok"]
        else res.get("reason")))
    res["report"] = report
    return res


class Lidar:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object("gcode")
        self.sock_path = config.get("socket", "/tmp/ai_server_uds")
        self.x_offset = config.getfloat("x_offset", -36.0)
        self.y_offset = config.getfloat("y_offset", -21.2)
        self.x_dir = config.getfloat("x_dir", -1.0)
        self.scan_z = config.getfloat("scan_z", 3.0)
        self.captures = config.getint("captures", 3, minval=1)
        self.settle = config.getfloat("settle_time", 0.15, minval=0.0)
        self.speed = config.getfloat("speed", 50.0, above=0.0)
        self.data_dir = config.get(
            "data_dir", "/usr/data/printer_data/lidar")
        self.gcode_dir = config.get(
            "gcode_dir", "/usr/data/printer_data/gcodes")
        self.sock = None
        # name -> {"x", "ys", "rows"}; only the last few scans are kept
        self.scans = {}
        self.pa_test = None
        self.last_result = {}
        for cmd in ("LIDAR_STATUS", "LIDAR_SCAN", "LIDAR_PA_ANALYZE",
                    "LIDAR_PA_CALIBRATE"):
            self.gcode.register_command(
                cmd, getattr(self, "cmd_" + cmd),
                desc=getattr(self, "desc_" + cmd))

    def get_status(self, eventtime):
        return {"last_result": self.last_result}

    def _yield(self):
        self.reactor.pause(self.reactor.monotonic() + 0.001)

    # ---------------------------------------------------- middleware socket
    def _close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

    def _call(self, msg, timeout=10.0):
        # one persistent connection: cx_ai_middleware leaks a descriptor per
        # connection and stops accepting after a few thousand
        err = None
        for attempt in range(2):
            try:
                if self.sock is None:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.settimeout(2.0)
                    s.connect(self.sock_path)
                    s.setblocking(False)
                    self.sock = s
                self.sock.sendall(json.dumps(msg).encode() + ETX)
                buf = b""
                end = self.reactor.monotonic() + timeout
                while not buf.endswith(ETX):
                    try:
                        d = self.sock.recv(1 << 20)
                        if not d:
                            raise OSError("connection closed")
                        buf += d
                        continue
                    except (BlockingIOError, InterruptedError):
                        pass
                    now = self.reactor.monotonic()
                    if now > end:
                        raise OSError("timeout")
                    # wait without blocking the reactor
                    self.reactor.pause(now + 0.005)
                return json.loads(buf[:-1].decode(errors="replace"))
            except (OSError, ValueError) as e:
                err = e
                self._close()
        raise self.printer.command_error(
            "LiDAR: no answer from cx_ai_middleware (%s). Is it running?"
            " (custom/lidar-start.sh)" % (err,))

    def _laser(self, on):
        if on:
            self._call({"control": "set_laser_open"})
            self._call({"control": "open_flow"})
            self._call({"control": "set_point_cloud_level", "level": 0})
        else:
            for c in ("close_flow", "set_laser_close"):
                try:
                    self._call({"control": c})
                except self.printer.command_error:
                    pass

    # ------------------------------------------------------------- scanning
    desc_LIDAR_STATUS = "Check that the LiDAR answers"

    def cmd_LIDAR_STATUS(self, gcmd):
        r = self._call({"control": "get_laser_exposure"})
        gcmd.respond_info(
            "LiDAR ok: exposure %s, offset X%.2f Y%.2f (x_dir %+d), scans in"
            " memory: %s" % (
                r.get("result", {}).get("exposure"), self.x_offset,
                self.y_offset, self.x_dir,
                ", ".join(sorted(self.scans)) or "none"))

    def _scan(self, name, x, y0, y1, step, z, captures):
        toolhead = self.printer.lookup_object("toolhead")
        n = int(round(abs(y1 - y0) / step))
        d = step if y1 >= y0 else -step
        ys = [round(y0 + i * d, 4) for i in range(n + 1)]
        nozzle_x = x - self.x_offset
        rows = []
        start = self.reactor.monotonic()
        self.gcode.run_script_from_command(
            "SAVE_GCODE_STATE NAME=_lidar_scan\nG90\nG0 Z%.3f F600" % (z,))
        self._laser(True)
        try:
            for y in ys:
                self.gcode.run_script_from_command(
                    "G0 X%.3f Y%.3f F%.0f" % (
                        nozzle_x, y - self.y_offset, self.speed * 60.0))
                toolhead.wait_moves()
                self.reactor.pause(self.reactor.monotonic() + self.settle)
                caps = []
                for i in range(captures):
                    r = self._call({"control": "get_point_cloud"})
                    caps.append(r.get("result", {}).get("point_cloud", []))
                rows.append(reduce_caps(caps))
                del caps
        finally:
            self._laser(False)
            self.gcode.run_script_from_command(
                "RESTORE_GCODE_STATE NAME=_lidar_scan")
        scan = {"x": x, "z": z, "x_dir": self.x_dir, "ys": ys, "rows": rows}
        # keep memory bounded: base + scan of one test, plus one spare
        while len(self.scans) >= 3:
            self.scans.pop(next(iter(self.scans)))
        self.scans[name] = scan
        self._save(name, scan)
        return len(ys), self.reactor.monotonic() - start

    def _save(self, name, scan):
        # compact copy for looking at on a PC: distances in um, -1 = empty
        try:
            if not os.path.isdir(self.data_dir):
                os.makedirs(self.data_dir)
            with open(os.path.join(self.data_dir, name + ".json"), "w") as f:
                f.write(json.dumps({k: scan[k] for k in ("x", "z", "x_dir",
                                                         "ys")})[:-1])
                f.write(', "bin": %s, "bin_min": %s, "rows": [' % (
                    BIN, BIN_MIN))
                for i, row in enumerate(scan["rows"]):
                    f.write(("," if i else "") + "[" + ",".join(
                        str(int(v * 1000)) if v == v else "-1"
                        for v in row) + "]")
                    if i % 20 == 19:
                        self._yield()
                f.write("]}\n")
        except OSError:
            pass

    desc_LIDAR_SCAN = "Scan a strip with the LiDAR (X/Y where the laser looks)"

    def cmd_LIDAR_SCAN(self, gcmd):
        name = gcmd.get("NAME")
        rows, secs = self._scan(
            name, gcmd.get_float("X"), gcmd.get_float("Y0"),
            gcmd.get_float("Y1"), gcmd.get_float("STEP", 0.4, above=0.05),
            gcmd.get_float("Z", self.scan_z),
            gcmd.get_int("CAPTURES", self.captures, minval=1))
        gcmd.respond_info("LiDAR scan %s: %d rows in %.0fs" % (
            name, rows, secs))

    # ------------------------------------------------------------- analysis
    desc_LIDAR_PA_ANALYZE = "Find pressure advance from a LiDAR PA test scan"

    def cmd_LIDAR_PA_ANALYZE(self, gcmd):
        base = self.scans.get(gcmd.get("BASE"))
        scan = self.scans.get(gcmd.get("SCAN"))
        if base is None or scan is None:
            raise gcmd.error("LiDAR: scan %s/%s not in memory" % (
                gcmd.get("BASE"), gcmd.get("SCAN")))
        test = self.pa_test
        if test is None:
            tf = os.path.join(self.data_dir, "pa_test.json")
            if not os.path.exists(tf):
                raise gcmd.error("LiDAR: no PA test layout found")
            with open(tf) as f:
                test = json.load(f)
        if base["ys"] != scan["ys"] or base["x"] != scan["x"]:
            raise gcmd.error("LiDAR: base and scan don't cover the same rows")
        line_x = [test["x0"] + i * test["pitch"] for i in range(
            len(test["pa"]))]
        A = []
        for r in range(len(scan["ys"])):
            A.append(line_areas(base["rows"][r], scan["rows"][r], scan["x"],
                                scan["x_dir"], line_x))
            self._yield()   # one row at a time: never block the reactor long
        res = pa_fit(scan["ys"], A, test)
        self.last_result = res
        try:
            with open(os.path.join(self.data_dir, "pa_result.json"), "w") as f:
                json.dump(dict(res, areas=A, ys=scan["ys"]), f)
        except OSError:
            pass
        for line in res["report"]:
            gcmd.respond_info(line)
        if not res["ok"]:
            raise gcmd.error("LiDAR PA: %s" % (res.get("reason"),))
        pa = res["pa"]
        if gcmd.get_int("APPLY", 1):
            # kept for the loaded filament: restored at boot, cleared by
            # UNLOAD_FILAMENT (tuning.cfg)
            self.gcode.run_script_from_command(
                "SET_PRESSURE_ADVANCE ADVANCE=%.4f\n"
                "SAVE_VARIABLE VARIABLE=lidar_pa VALUE=%.4f" % (pa, pa))
        gcmd.respond_info(
            "LiDAR pressure advance: %.4f (kept until UNLOAD_FILAMENT)"
            % (pa,))

    # ------------------------------------------------------- PA test print
    desc_LIDAR_PA_CALIBRATE = "Print and measure a pressure advance test"

    def cmd_LIDAR_PA_CALIBRATE(self, gcmd):
        temp = gcmd.get_float("EXTRUDER_TEMP", above=150.0)
        bed = gcmd.get_float("BED_TEMP", minval=0.0)
        chamber = gcmd.get_float("CHAMBER_TEMP", 0.0, minval=0.0)
        pa0 = gcmd.get_float("PA_START", 0.0, minval=0.0)
        pas = gcmd.get_float("PA_STEP", 0.01, above=0.0)
        lines = gcmd.get_int("LINES", 9, minval=4, maxval=9)
        x0 = gcmd.get_float("X", 130.0)
        y0 = gcmd.get_float("Y", 100.0)
        fast = gcmd.get_float("FAST", 150.0, above=20.0)
        slow = gcmd.get_float("SLOW", 20.0, above=1.0)
        height = gcmd.get_float("HEIGHT", 0.2, above=0.05)
        width = gcmd.get_float("WIDTH", 0.45, above=0.1)
        accel = gcmd.get_float("ACCEL", 5000.0, above=100.0)
        fan = gcmd.get_int("FAN", 64, minval=0, maxval=255)
        pitch = 3.0
        # slow / fast segments along Y; slow ones are long enough to settle
        segs = [(15.0, slow), (20.0, fast), (15.0, slow), (20.0, fast),
                (15.0, slow), (20.0, fast), (15.0, slow)]
        y1 = y0 + sum(s[0] for s in segs)
        x1 = x0 + (lines - 1) * pitch
        cx = (x0 + x1) / 2.0
        toolhead = self.printer.lookup_object("toolhead")
        fil_area = getattr(toolhead.get_extruder(), "filament_area", 2.405)
        epm = height * width / fil_area
        test = {"x0": x0, "pitch": pitch, "y0": y0, "y1": y1,
                "pa": [round(pa0 + i * pas, 4) for i in range(lines)],
                "dirs": [1 if i % 2 == 0 else -1 for i in range(lines)],
                "segments": segs, "fast": fast, "slow": slow,
                "height": height, "width": width}
        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)
        with open(os.path.join(self.data_dir, "pa_test.json"), "w") as f:
            json.dump(test, f)
        self.pa_test = test
        scan = "X=%.2f Y0=%.2f Y1=%.2f" % (cx, y0 - 3, y1 + 3)

        g = ["; LiDAR pressure advance test, written by lidar.py",
             "; PA %s" % (" ".join("%.3f" % p for p in test["pa"]),),
             "SET_PRINT_STATS_INFO TOTAL_LAYER=1",
             "EXCLUDE_OBJECT_DEFINE NAME=lidar_pa_test CENTER=%.1f,%.1f"
             " POLYGON=[[%.1f,%.1f],[%.1f,%.1f],[%.1f,%.1f],[%.1f,%.1f]]" % (
                 cx, (y0 + y1) / 2, x0 - 2, y0 - 2, x1 + 2, y0 - 2,
                 x1 + 2, y1 + 2, x0 - 2, y1 + 2),
             # the bare plate is scanned inside START_PRINT, after the nozzle
             # touch and before heating up and purging (_LIDAR_PRINT_SCAN)
             "SET_GCODE_VARIABLE MACRO=_LIDAR_PRINT_SCAN VARIABLE=x VALUE=%.2f"
             % (cx,),
             "SET_GCODE_VARIABLE MACRO=_LIDAR_PRINT_SCAN VARIABLE=y0 VALUE=%.2f"
             % (y0 - 3,),
             "SET_GCODE_VARIABLE MACRO=_LIDAR_PRINT_SCAN VARIABLE=y1 VALUE=%.2f"
             % (y1 + 3,),
             "START_PRINT EXTRUDER_TEMP=%.0f BED_TEMP=%.0f CHAMBER_TEMP=%.0f"
             % (temp, bed, chamber),
             "SET_PRINT_STATS_INFO CURRENT_LAYER=1",
             "M83", "G90",
             "SET_VELOCITY_LIMIT ACCEL=%.0f" % (accel,),
             "M106 S%d" % (fan,),
             "EXCLUDE_OBJECT_START NAME=lidar_pa_test",
             "G0 Z2 F600",
             "G0 X%.3f Y%.3f F9000" % (x0, y0),
             "G0 Z%.3f F600" % (height,)]
        # serpentine: each line starts where the last one ended, so there
        # are no travels to string across the lines
        for i, pa in enumerate(test["pa"]):
            x = x0 + i * pitch
            d = test["dirs"][i]
            g.append("SET_PRESSURE_ADVANCE ADVANCE=%.4f" % (pa,))
            y = y0 if d > 0 else y1
            for seglen, v in (segs if d > 0 else list(reversed(segs))):
                y += d * seglen
                g.append("G1 X%.3f Y%.3f E%.5f F%.0f" % (
                    x, y, seglen * epm, v * 60.0))
            if i + 1 < lines:
                g.append("G1 X%.3f E%.5f F%.0f" % (
                    x + pitch, pitch * epm, slow * 60.0))
        g += ["G1 E-0.8 F2400",
              "G0 Z3 F600",
              "EXCLUDE_OBJECT_END NAME=lidar_pa_test",
              "M106 S0",
              "SET_VELOCITY_LIMIT ACCEL=%.0f" % (toolhead.max_accel,),
              # cool down over the purge line, in front of the test, so
              # nothing drips onto the lines while they are scanned
              "G0 X%.3f Y%.3f F9000" % (cx, y0 - 12),
              "M104 S150",
              "M106 S255",
              "TEMPERATURE_WAIT SENSOR=extruder MAXIMUM=155",
              "M106 S0",
              "LIDAR_SCAN NAME=pa_scan " + scan,
              "LIDAR_PA_ANALYZE BASE=pa_base SCAN=pa_scan",
              "END_PRINT"]
        fn = "lidar_pa_test.gcode"
        with open(os.path.join(self.gcode_dir, fn), "w") as f:
            f.write("\n".join(g) + "\n")
        gcmd.respond_info(
            "LiDAR PA test: %d lines, PA %.3f-%.3f, X%.0f-%.0f Y%.0f-%.0f;"
            " starting %s" % (lines, test["pa"][0], test["pa"][-1], x0 - 2,
                              x1 + 2, y0 - 2, y1 + 2, fn))
        self.gcode.run_script_from_command(
            "SDCARD_PRINT_FILE FILENAME=%s" % (fn,))


def load_config(config):
    return Lidar(config)
