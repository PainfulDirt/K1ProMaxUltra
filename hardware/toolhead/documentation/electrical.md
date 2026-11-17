# Toolhead fan electrics

Scope: the part-cooling fan channel on the nozzle board. The baseline build changes nothing here:
**one stock Creality 4020, the one already fitted, on the stock channel** (DD-01, DD-05,
`cfd-report.md` §12.2). This page records what is known about that channel (§1), the Same Sky
path with its 24→12 V buck (§2; record only, not buildable in this architecture, R-13), fan tuning (§3), the PB6 probing procedure the upgrade
uses (§4), the example Kalico snippets (§5) and, for the record, the rejected options (§6).

Status tags: **VERIFIED** (repo, datasheet), **SECONDARY** (distributor or retailer page, search
snapshot), **DERIVED** (from community CAD), **INFERRED** (deduced from firmware config, not
measured), **ESTIMATED** (my arithmetic or assumption), **MEASURE** (the user has to measure it).

**No printer config file in the repo is changed by this project.** The snippets in
`components/fans/klipper/` are examples, to include from `tuning.cfg` only after review.

## 1. Baseline: stock 4020 on channel 1 (no change)

### 1.1 What is known about channel 1 (part fan)

| Item | Value | Status / source |
|---|---|---|
| Fan | Creality K1 4020 blower, 24 V 0.3 A, 12 000 rpm, 4-wire PWM + tach, lead 60 mm, 1.25-4P | VERIFIED (retailer listings, research/02 F3) |
| Connector | "Model Fan", 4 pins **GND / PWM / FG / FAN+** (K1-NOZZLE-M_V12) | VERIFIED (board photo), research/01 §H.3 |
| Connector pitch | 1.25 mm 4P, but one seller lists XH2.54-4P | SECONDARY, conflicting (research/02 F3, research/03 §2). **MEASURE** before buying any pigtail or extension |
| PWM | `!nozzle_mcu:PB8`, software PWM, `cycle_time: 0.0100` (100 Hz), `hardware_pwm: false` | VERIFIED (Pellcorp `fan_control.cfg`, research/03 §3) |
| PWM stage | open collector, which is why the pin is inverted | INFERRED (research/03 §3) |
| Power enable | `enable_pin: nozzle_mcu:PB6`. Klipper sets it when the fan speed goes above 0 and clears it at 0 | VERIFIED (config); Klipper `fan.py` behaviour |
| High side or low side? | **UNKNOWN.** Whether PB6 switches +24 V or GND is not documented | open: M15. Not needed for the baseline; probe it with §4 only for the upgrade |
| Tach | `^nozzle_mcu:PB3`, commented out in Pellcorp | VERIFIED (config) |
| Current rating | none published; **0.3 A demonstrated** (stock 4020) | research/03 §3 (demonstrated, not rated) |
| Supply | 24 V | VERIFIED (all stock toolhead fans are 24 V parts) |
| Kalico object | must stay one `[fan]`: Pellcorp moved away from `[fan_generic part]` because of move-queue crashes; MPC uses `cooling_fan: fan` | research/03 §10.6; `tuning.cfg` `[extruder]` |

The hotend fan (channel 2: PB5, tach PB4, 3010, 0.1 A) is unchanged (DD-04).

### 1.2 What to do

| Item | Baseline |
|---|---|
| Wiring | none. The fitted 4020 stays plugged into "Model Fan". The fan moves 6–7 mm forward (new envelope Y −56.5…−36.5, stock −49.4…−30.2, `interfaces.py` `STOCK_4020_POS`). Check that the 60 mm lead reaches the socket without tension and without crossing the frame window or the 3010 intake (`assembly.md` step 5). If it does not reach, use a 4-pin extension (pitch: **MEASURE**); never cut the stock lead |
| Add-on (buck, MOSFET) | none |
| Config | none. Pellcorp's `[fan]` stays as it is |
| Optional tach for commissioning | `components/fans/klipper/part_fan_stock4020.cfg` makes the stock values explicit and has the tach lines commented out. Including it is a printer-config change, left to the user (§5) |
| After fitting | **re-run `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7`** (`calibration.md` step E). The duct is new, and the CFD thermal proxy puts the extra nozzle + sock loss at about +7.6 W at 100 % fan (`cfd-report.md` §17.7; the sock share at an ESTIMATED 150 °C sock surface) |

### 1.3 Current budget, channel 1

| Build | Channel 1 at 24 V | vs 0.3 A demonstrated |
|---|---|---|
| stock 4020 × 1 (baseline) | 0.30 A (SECONDARY) | = stock |

Toolhead fan total = channel 1 + 0.1 A (3010 on channel 2, research/03 §2).

## 2. Upgrade path (record only, not buildable as modelled): Same Sky CBM-5015BF + 24→12 V buck

### 2.1 When, and what it involves

**Not buildable in this architecture** (review R-13, DD-01, `cfd-report.md` §17.8): in the XY-joint
band the Same Sky needs 56.0 mm of width with a 1 mm stall margin and a cover wall on both sides,
and 55.2 mm is available. It would need an open-sided or asymmetric cover. This section is kept as the
record of the electrical side. Its original trigger: bench test V1 measures the stock 4020 at its
lower bound **and** the V5/V6 test prints want more cooling (DD-01, `cfd-report.md` §12.1). Parts
and prices: `bill-of-materials.md` §3.

| Item | Upgrade | Source |
|---|---|---|
| Fan | Same Sky CBM-5015BF-175-459-22: **12 V**, 4-wire PWM + tach; PWM 0.2–50 kHz, VIH 2.5–10 V; tach open collector, 2 pulses/rev | research/03 §12.2 (VERIFIED datasheet) |
| Add-on | **24→12 V buck** (§2.2–2.3). **Not** a low-side MOSFET: a 4-wire fan is never put behind a switched ground (DD-05) | DD-05 |
| Channel | stock: PB8 PWM, PB6 supply switch, one logical `[fan]` | DD-05 |
| Current | 0.12 / 0.18 A typical / max at 24 V, inside the 0.3 A demonstrated (§2.6). The §4.4 current check is not needed | §2.6 |
| PB6 probe (§4) | recommended before wiring: it decides whether the tach may go to PB3 (§4.5), gives the rail voltage (the R-78E option needs ≤ 27 V) and checks the PWM pull-up | §4 |
| Config | `cycle_time: 0.002` (the fan's PWM minimum is 200 Hz), `kick_start_time`, `off_below` (`part_fan_samesky.cfg`, example only) | research/03 §12.2 |
| CAD | a different duct variant (`with_fan(PARAMS_FINAL, "samesky")`) and a frame regenerated from it; no buck mount is modelled yet | `cfd-report.md` §12.1, §16; `cad/README.md` |
| Calibration | MPC, shaper (+7.4 g fan + duct, plus the buck), fan function | `calibration.md` |

### 2.2 Buck requirements

| Requirement | Value | Basis |
|---|---|---|
| Input | 24 V nominal, ≥ 15…28 V usable range, no damage at 30 V | 24 V rail; margin for PSU tolerance and transients (ESTIMATED) |
| Output | 12.0 V fixed (±5 %), **no trim pot** | fan rated 12 V; a pot drifts under toolhead vibration (ESTIMATED) |
| Current, 1 fan | **≥ 0.5 A** continuous | CBM 0.33 A max at 12 V (research/03 §12.2) + start-up surge (ESTIMATED 1.5×) |
| Recommendation | a **1 A** module | cooler at 0.33 A |
| Mass | ≤ 3 g incl. leads | 9 g ≈ 1 % X-shaper frequency (design-decisions, Phase 1 finding 5) |
| Size | ≤ 20 × 18 × 11 mm | ESTIMATED. The free volume under the fan in the S7SS layout is about 19 × 12 × 10 mm, so the module needs a place on the frame; none is designed (`cfd-report.md` §16) |
| Switching frequency | ≥ 300 kHz (small inductor) and **not adjustable** | ESTIMATED |
| EMI | fully enclosed or shielded inductor; manufacturer EMC data preferred; place ≥ 20 mm from the thermistor leads and keep its leads short and twisted | ESTIMATED; acceptance test in §2.5 |
| Ambient | ≥ 70 °C operating | chamber 45 °C + heat from the hotend (ESTIMATED) |
| Start-up | soft start; tolerates being switched on and off by PB6 at every M106 0→>0 | the buck is fed from the PB6-switched supply |
| Output capacitance | fan input caps only; stay below the module's max capacitive load | R-78E12-1.0 max 100 µF (SECONDARY) |

### 2.3 Orderable modules (EU)

Prices are snapshots from search results on 2026-11-11 (SECONDARY). Re-check at checkout.

| # | Module | In / out | Package, mass | Notes | EU source, price |
|---|---|---|---|---|---|
| **1 (preferred)** | **TRACO TSR 1-24120** | 15–36 V in; 12 V, 1 A out | SIP3 (7812 footprint); **1.9 g** (RS listing) | fixed output, 400–600 kHz (500 typ.), enclosed module, wide input margin. Pinout 1 = +Vin, 2 = GND, 3 = +Vout (7812-compatible) | DigiKey EU ≈ €5.1–5.2; RS IE €5.93 ex VAT; SOS Electronic €5.46 ex VAT; Bürklin. [DigiKey](https://www.digikey.at/en/products/detail/traco-power/TSR-1-24120/9383773), [RS](https://ie.rs-online.com/web/p/switching-regulators/1247658), [SOS](https://soselectronic.com/en-my/products/tracopower/tsr-1-24120-70571?settings=1) |
| 2 | **RECOM R-78E12-1.0/X9** | **15–27 V** in; 12 V, 1 A | SIP3, epoxy-potted; mass not found (ESTIMATED ≈ 2 g) | cheapest; only 3 V of input headroom above 24 V, so measure the rail first (§4 step 3) | DigiKey EU ≈ €3.43; Bürklin €3.51 incl. VAT. [DigiKey](https://www.digikey.de/en/products/detail/recom-power/R-78E12-1-0-X9/13401697), [Bürklin](https://www.buerklin.com/en/p/recom/dc-dc-converters/r-78e12-1-0-x9/33C6053/) |
| 3 | **Pololu D24V10F12** (#2834) | 12.1–36 V in; 12 V, 1 A | 12.7 × 17.8 × 3.6 mm PCB; **1.0 g** | lightest and flattest; open board, unshielded inductor, no reverse-polarity protection | exp-tech.de €7.96 ex VAT; opencircuit.shop €9.00; botland €10.90. [Pololu](https://www.pololu.com/product/2834/specs), [exp-tech](https://exp-tech.de/en/products/pololu-12v-1a-step-down-voltage-regulator-d24v10f12), [botland](https://botland.store/3022-step-down-voltage-regulator-d24v10f12-12v-1a-pololu-2834.html) |

Not recommended: generic adjustable MP1584 / LM2596 boards (trim pot, no EMC data, inconsistent
quality). Also not recommended: series resistors or two 12 V fans in series (research/03 §3).

The TRACO datasheet host (tracopower.com) could not be fetched from this session. Its weight,
input range and frequency above come from distributor listings (SECONDARY). Read the datasheet's
EMC section before ordering and add its recommended input filter if one is listed.

### 2.4 Wiring

```
 Board "Model Fan" plug                    TSR 1-24120 (or R-78E / Pololu)        Same Sky CBM-5015BF-...-22
 FAN+ (24 V) ───────────────────────────── pin 1 +Vin
                                           pin 3 +Vout (12 V) ───────────────────── red    (+12 V)
 GND ──────────────────────────────┬────── pin 2 GND
                                   └──────────────────────────────────────────────── black  (GND)
 PWM (open collector, inverted) ───────────────────────────────────────────────────── blue   (PWM)
 FG  (PB3) ◄───── only if PB6 is HIGH-side (§4.5) ─────────────────────────────────── yellow (tach)
 optional: 10 µF / 50 V ceramic across pin 1–2 and 10 µF / 25 V across pin 3–2, at the module (ESTIMATED; follow the datasheet)
```

- Wire colours are the Same Sky CBM series convention (yellow tach, blue PWM; research/03 §12,
  CBM-40B wire table). **Check them against the CBM-5015BF datasheet** before soldering.
- **PWM pull-up.** The board's PWM stage is open collector, so the fan must pull the line up
  itself. With the fan powered at 12 V and the blue wire unconnected, measure blue → black: 2.5–5.5 V
  means the fan has an internal pull-up (normal for 4-wire fans). If it reads 0 V, add 22 kΩ from
  the 12 V output to the blue wire and a 5.1 V Zener (BZX84C5V1) from the blue wire to GND. That keeps
  the line inside VIH 2.5–10 V and inside what a stock 4-wire fan would put on the board's stage.
- **Polarity.** The Same Sky reads "high = run", like the stock 4020, so the `!` on PB8 stays.
- **Low-side board** (§4.5): the buck's GND goes to the plug's GND pin, which is then the switched
  one. Do not connect the tach in that case.

### 2.5 Acceptance test after fitting the buck

| Check | Pass | Basis |
|---|---|---|
| Buck output at M106 S255, fan running | 11.4–12.6 V | ±5 % (ESTIMATED) |
| Extruder temperature at 200 °C, steady, M106 S0 vs S255 (after the MPC re-cal) | no new jitter above ±0.1 °C in the temperature graph | ESTIMATED; EMI into the thermistor |
| `MEASURE_AXES_NOISE` (ADXL on the nozzle board), fan off vs fan 100 % | noise rises by no more than ~20 % over the same test with the stock fan | ESTIMATED |
| `klippy.log` during a 1 h print | no `nozzle_mcu` communication errors or "Timer too close" | — |
| Module temperature after 30 min at 100 % in a 45 °C chamber | below the datasheet limit; by touch, not painful (< ~60 °C) | ESTIMATED |

### 2.6 Current budget with the upgrade

The buck is assumed 90 % efficient (ESTIMATED; research/03 used the same). Start-up surge is
ESTIMATED at up to about 2× rated for < 1 s.

| Build | Per fan (rated / max, at the fan's voltage) | Channel 1 at 24 V, typical / max | vs 0.3 A demonstrated |
|---|---|---|---|
| Same Sky × 1 + buck | 0.22 / 0.33 A at 12 V (VERIFIED datasheet) | 0.12 / 0.18 (+ a few mA buck quiescent) | inside |

Added mass (ESTIMATED): buck 1.0–1.9 g plus leads (≈ 2–3 g total).

## 3. Tuning `off_below` and `kick_start_time` (any fan)

Not needed for the baseline unless the stock fan stalls at low duty (Pellcorp's stock fan uses
`off_below: 0`). Do it when a fan model or a `cycle_time` changes.

1. With the fan stopped, send `M106 S{n}` for n = 13, 26, 38, 51, 64, 77 (5–30 %). Wait 5 s at
   each, then `M107`. Note the lowest n that starts the fan **5 times out of 5**.
2. Set `off_below` to that duty plus 0.05 (so S51 → 0.20 + 0.05 = 0.25).
3. From a running fan, step down the same way. If the fan stalls above `off_below`, raise it.
4. Compare with the Orca filament minimum fan speeds: ABS/ASA use 0–30 %, PETG 30–80 % (research/01
   §C.2). Any request below `off_below` turns the fan **off**, so a high `off_below` changes ASA
   cooling. Keep it as low as the fan allows.
5. Any change to `off_below`, `max_power` or `cycle_time` changes the fan-speed → airflow mapping,
   so re-run MPC afterwards (`calibration.md` step E).

## 4. Probing PB6 (high or low side, current) — step by step

Goal: closes M15 and decides the wiring in §4.5. **Needed only for the Same Sky path, which is not buildable in this architecture (R-13)**, not for
the baseline. Time: about 30 min. Tools: a multimeter with alligator-clip leads, two back-probe pins
(or sewing needles), and a phone camera.

**Safety:**
- The fan supply is 24 V DC. That is safe to touch. What you must avoid is a **short between
  neighbouring pins**: the pins are on a 1.25 mm pitch, and FAN+ touching PWM or FG can destroy the
  nozzle MCU's PB3 or PB8.
- Always back-probe the plug from the wire side, with the plug seated. Never probe bare board
  pads. Clip the black lead to the reference first, then touch only one pin with the red lead.
- Run `TURN_OFF_HEATERS` and wait until the nozzle is below 50 °C. Motors stay idle; the steps
  below only use `M106` / `M107`.
- Do not look into the LiDAR windows while the printer is on.

**Reference points:**
- **True GND:** pin 1 (GND) of the **TOUCH** port (5-pin PicoBlade GND / 5V / PA8 / GND / PA9,
  research/01 §B.1). Sanity check: pin 2 reads 5.0 V against it.
- Do **not** use the fan plug's own GND pin as the reference: it is the pin that may be switched.

### 4.1 Topology (fan plugged in)

1. Take the front cover off. Stock cover: 2 × M3×4 screws at the sides, slide forward (research/02
   C5). New cover: 2 × M3×6 on top, slide forward (`assembly.md`). The plug stays seated.
2. Black lead on TOUCH GND. In the Fluidd console, send `M106 S0`, then `M106 S255`. At each
   setting, read the four plug pins:

| Reading (V vs TOUCH GND) | `M106 S0` | `M106 S255` |
|---|---|---|
| FAN+ | … | … |
| GND pin | … | … |
| PWM | … | … |
| FG | … | … |

3. Rail voltage: FAN+ at S255 on a high-side board, or FAN+ at either setting on a low-side board,
   is the 24 V rail at the toolhead. Write it down: the R-78E option needs it ≤ 27 V.

### 4.2 PWM stage (fan unplugged)

4. Unplug the fan. Send `M106 S255` and measure PWM vs TOUCH GND:
   - ≈ 0 V: open collector **without** a pull-up on the board (expected).
   - 3.3 V or 5 V: the board drives or pulls the line up itself. Note which.
5. Plug the fan back in. Send `M106 S26` (10 %) and `M106 S128` (50 %). The DC average of PWM
   should be about 10 % and 50 % of its S255 value. That confirms "line high = fan runs" (the
   reason for the `!` on PB8). If you get about 90 % and 50 % instead, the polarity is the other
   way round: note it, because the snippet's `!` would then have to change.

### 4.3 Current and switch resistance (fan plugged in, `M106 S255`, 2 min warm-up)

6. **Low-side board:** the GND pin vs TOUCH GND at S255 is the voltage drop across the switch:
   R_switch = V / I.
   **High-side board:** measure FAN+ vs TOUCH GND twice, unplugged (no load) and plugged at S255.
   R_switch ≤ ΔV / I. This is an upper bound, because it includes the board and cable drop.
7. Current I: either insert the meter's mA range in series with the FAN+ wire (only with a
   4-pin extension lead you can open; never cut the stock fan lead), or use the rated 0.3 A
   (SECONDARY).
8. Photograph the board around the "Model Fan" connector, both sides (that also covers M10).
   Read the marking codes on the small SOT-23 / SOT-23-6 parts next to it. A P-channel part
   points to a high-side switch, an N-channel one to a low-side switch.

### 4.4 Decision: may the channel carry more than 0.3 A?

Not needed for the baseline (0.30 A) or the single Same Sky (0.18 A max). Kept because it is the
gate for anything that would draw more than 0.3 A from channel 1.

| Condition (all of them) | Then |
|---|---|
| The switch part is identified, its datasheet gives ≥ 1.0 A continuous at the gate drive used, **and** P = I² × R_switch ≤ 0.15 W at the planned current (ESTIMATED limit for a SOT-23 in a 45–60 °C chamber), **and** the connector is a 1.25 mm type rated ≥ 1 A per contact (PicoBlade class; check the datasheet of the type you find) | up to the planned current is OK |
| Anything not met | stay at or below **0.3 A demonstrated** on this channel |

Worked numbers (ESTIMATED): with R_switch = 0.1 Ω, 0.6 A gives 36 mW. With R_switch = 0.5 Ω,
0.6 A gives 0.18 W, which fails.

### 4.5 Decision table

| Measured topology | Stock 4020 (baseline) | Same Sky × 1 + buck (upgrade) |
|---|---|---|
| **High-side** (FAN+ 0 V at S0 and 24 V at S255; GND pin always 0 V) | as stock | buck between FAN+ and GND; tach to PB3 allowed (fan GND = true GND) |
| **Low-side** (FAN+ always 24 V; GND pin ≈ rail-ish at S0 and ≈ 0 V at S255) | as stock (this is the stock design) | buck between FAN+ and the switched GND pin; **do not connect the tach** (when off, the fan's GND floats up and the FG wire could push current into PB3); PWM wire as stock |
| **No switching seen** (FAN+ 24 V and GND 0 V at both settings) | as stock | buck from FAN+/GND, no tach; the fan is then stopped only by 0 % PWM; check the CBM datasheet for its behaviour at 0 % duty before relying on it |
| Stock fan still turns slowly at `M106 S0` | report it | a sneak path through the PWM line; do not build the upgrade until it is explained |

Record the results in `missing-information.md` M15 (owned by the lead).

## 5. Kalico config snippets (examples, not active)

The files are in `hardware/toolhead/components/fans/klipper/`:

| File | Use |
|---|---|
| `part_fan_stock4020.cfg` | baseline: stock values made explicit, with an optional tach. Not needed for the baseline |
| `part_fan_samesky.cfg` | record only (Same Sky not buildable, R-13): Same Sky with the buck (`cycle_time: 0.002`) |
| `part_fan_delta_mosfet.cfg` | rejected option, kept for the record (§6). Do not use |

**How to use one** (a printer-config change, made by the user, not by this project):
1. Copy the chosen file next to `tuning.cfg` on the printer, as `part_fan.cfg`.
2. Add `[include part_fan.cfg]` as the **last** line of `tuning.cfg`. Each snippet re-declares
   `[fan]` with only the options it changes. Klipper merges a re-declared section, and the value read
   **later** wins. So the snippet only takes effect if it is read after Pellcorp's
   `fan_control.cfg`. **That order is not verified:** the repo's `printer.cfg` holds only the
   overrides and includes `tuning.cfg` on its first line, and where the printer's own `printer.cfg`
   includes `fan_control.cfg` is unknown (review R-24).
3. `FIRMWARE_RESTART`, then check what Klipper actually uses, either in the Fluidd console:
   `{action_respond_info(printer.configfile.settings.fan|string)}` inside a one-line macro, or in
   the config dump at the top of `klippy.log`. The `[fan]` values must be the snippet's
   (`cycle_time`, `kick_start_time`, `off_below`). If they are Pellcorp's, move the include line to
   the end of the printer's `printer.cfg`, after the Pellcorp includes, and check again.
4. Run `CONFIG_OVERRIDES` (or `BACKUP_TO_GITHUB`) so the change survives Pellcorp updates.

**Rollback:** delete the include line (and the file), then `FIRMWARE_RESTART`. Pellcorp's stock
`[fan]` applies again. After any change of fan or fan config, re-run MPC (`calibration.md`).

**Tach and MCU load.** Pellcorp left the tach commented out. A 0.8–1.0 ms poll adds timer load to
the nozzle MCU, the one that had move-queue trouble (research/03 §10.6). Enable the tach for
commissioning only. Keep it on only if a long print shows no `nozzle_mcu` timing errors in
`klippy.log`.

Klipper's rule for the poll interval is `tachometer_poll_interval < 30 / (tachometer_ppr × max rpm)`:

| Fan | Max rpm (rated + 10 %) | Limit at ppr 2 | Value used |
|---|---|---|---|
| stock 4020 | 13 200 (12 000 ±10 %, SECONDARY) | 1.14 ms | 0.0008 (Pellcorp's commented value) |
| Same Sky CBM-5015BF | 8 250 (7 500 ±10 %, ESTIMATED tolerance) | 1.82 ms | 0.0010 |

## 6. Rejected options, kept for the record

CFD rejected these (DD-01, `cfd-report.md` §10, §12.1). They are not part of any build.

| Option | Electrical consequence (why it was ever here) | Why rejected |
|---|---|---|
| Two 4020s on channel 1 (feed D) | 0.6 A on a channel proven only to 0.3 A: needed the §4.4 check and a Y-splice with one FG | −5 % layer speed, −44 % weakest sector, +24 % nozzle impingement, +27 g (D2, `cfd-report.md` §10) |
| Delta BFB0524HH-F00 (2-wire 24 V) | needed a low-side MOSFET add-on driven from the PWM pin (DD-05), tach unusable | no clear margin: +10 % typical, −10 % as a minimum-spec unit, +4 g |
| Owned Sunon MF50152VX (2-wire) | as the Delta | below the 4020's lower bound (`cfd-report.md` §8) |

The full MOSFET add-on design (schematic, part list, PWM-frequency notes) is in this file's git
history and in `part_fan_delta_mosfet.cfg`. Should a 2-wire fan ever come back, DD-05's rule still
applies: 2-wire fans behind a low-side switch, 4-wire fans never.
