# Toolhead fan electrics

Scope: the part-cooling fan channel on the nozzle board, the three fan variants CFD is choosing
between, the two add-ons they may need (24→12 V buck, low-side MOSFET), the PB6 probing procedure
and the Kalico config snippets in `components/fans/klipper/`.

Status tags: **VERIFIED** (repo, datasheet), **SECONDARY** (distributor or retailer page, search
snapshot), **DERIVED** (from community CAD), **INFERRED** (deduced from firmware config, not
measured), **ESTIMATED** (my arithmetic or assumption), **MEASURE** (the user has to measure it).
Nothing here changes the printer config. The snippets are examples, to include from `tuning.cfg`
after review.

> **Variant markers.** Everything that depends on the CFD fan decision is tagged
> **[V-4020]** (stock Creality 4020, 1 or 2), **[V-SS]** (Same Sky CBM-5015BF-175-459-22, 1 or 2)
> or **[V-DELTA]** (Delta BFB0524HH-F00, 1 or 2). Once CFD decides, delete the other variants'
> rows. The count (×1 / ×2) only changes the current budget and the connector harness.

## 1. What is known about channel 1 (part fan)

| Item | Value | Status / source |
|---|---|---|
| Connector | "Model Fan", 4 pins **GND / PWM / FG / FAN+** (K1-NOZZLE-M_V12) | VERIFIED (board photo), research/01 §H.3 |
| Connector pitch | 1.25 mm 4P, but one seller lists XH2.54-4P | SECONDARY, conflicting (research/02 F3, research/03 §2). **MEASURE** before buying a pigtail |
| PWM | `!nozzle_mcu:PB8`, software PWM, `cycle_time: 0.0100` (100 Hz), `hardware_pwm: false` | VERIFIED (Pellcorp `fan_control.cfg`, research/03 §3) |
| PWM stage | open collector, which is why the pin is inverted | INFERRED (research/03 §3) |
| Power enable | `enable_pin: nozzle_mcu:PB6`. Klipper sets it when the fan speed goes above 0 and clears it at 0 | VERIFIED (config); Klipper `fan.py` behaviour |
| **High side or low side?** | **UNKNOWN.** Whether PB6 switches +24 V or GND is not documented anywhere | open: M15 (`missing-information.md`); probe it with §4 |
| Tach | `^nozzle_mcu:PB3`, commented out in Pellcorp | VERIFIED (config) |
| Current rating | none published; **0.3 A demonstrated** (stock 4020) | research/03 §3 (demonstrated, not rated) |
| Supply | 24 V | VERIFIED (all stock toolhead fans are 24 V parts) |
| Kalico object | must stay one `[fan]`: Pellcorp moved away from `[fan_generic part]` because of move-queue crashes; MPC uses `cooling_fan: fan` | research/03 §10.6; `tuning.cfg` `[extruder]` |

The hotend fan (channel 2: PB5, tach PB4, 3010, 0.1 A) is unchanged (DD-04). It is not part of
this document except in the budget (§6).

## 2. Variant wiring overview

| Variant | Fan electrical type | Add-on | Wires to the board connector | Tach to PB3 |
|---|---|---|---|---|
| **[V-4020]** ×1 | 24 V, 4-wire PWM + tach | none (drop-in) | as stock | optional (§7) |
| **[V-4020]** ×2 | same | none, **if** the PB6 switch passes §4.4 for 0.6 A; otherwise not buildable on this channel | PWM wires paralleled, FAN+ and GND per fan to a Y-splice, **one** FG only | optional, one fan |
| **[V-SS]** ×1 / ×2 | **12 V**, 4-wire PWM + tach; PWM 0.2–50 kHz, VIH 2.5–10 V; tach open collector, 2 pulses/rev (research/03 §12.2) | **24→12 V buck** (§3) | FAN+/GND → buck input; buck 12 V → fan red; fan black → GND; blue PWM wire(s) → PWM pin | only if PB6 is high-side (§4.5) |
| **[V-DELTA]** ×1 / ×2 | 24 V, **2-wire** + FG (-F00); no PWM input (research/03 §12.1) | **low-side MOSFET** (§5) | FAN+ → fan red; fan black → MOSFET drain; MOSFET gate from the PWM pin | **no** (FG is meaningless under supply PWM; see §5.4) |

With two fans on one channel they stay **one logical fan** (DD-05): one `[fan]`, one PWM signal, one
MPC model.

## 3. Add-on (a): 24 → 12 V buck for the Same Sky [V-SS]

### 3.1 Requirements

| Requirement | Value | Basis |
|---|---|---|
| Input | 24 V nominal, ≥ 15…28 V usable range, no damage at 30 V | 24 V rail; margin for PSU tolerance and transients (ESTIMATED) |
| Output | 12.0 V fixed (±5 %), **no trim pot** | fan rated 12 V; a pot drifts under toolhead vibration (ESTIMATED) |
| Current, 1 fan | **≥ 0.5 A** continuous | CBM 0.33 A max at 12 V (research/03 §12.2) + start-up surge (ESTIMATED 1.5×) |
| Current, 2 fans | **≥ 1.0 A** continuous | 2 × 0.33 A + surge |
| Recommendation | buy a **1 A** module for both cases | one part number, cooler at 0.33 A |
| Mass | ≤ 3 g incl. leads | 9 g ≈ 1 % X-shaper frequency (DD finding 5) |
| Size | ≤ 20 × 18 × 11 mm, so it fits beside the fan on the frame | ESTIMATED; mount is a CAD open item (STATUS step 3) |
| Switching frequency | ≥ 300 kHz (small inductor) and **not adjustable** | ESTIMATED |
| EMI | fully enclosed or shielded inductor; manufacturer EMC data preferred; place ≥ 20 mm from the thermistor leads and keep its leads short and twisted | ESTIMATED; acceptance test in §3.4 |
| Ambient | ≥ 70 °C operating | chamber 45 °C + heat from the hotend (ESTIMATED) |
| Start-up | soft start; tolerates being switched on and off by PB6 at every M106 0→>0 | the buck is fed from the PB6-switched supply |
| Output capacitance | fan input caps only; stay below the module's max capacitive load | R-78E12-1.0 max 100 µF (SECONDARY) |

### 3.2 Orderable modules (EU)

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

### 3.3 Wiring [V-SS]

```
 Board "Model Fan" plug                    TSR 1-24120 (or R-78E / Pololu)        Same Sky CBM-5015BF-...-22
 FAN+ (24 V) ───────────────────────────── pin 1 +Vin
                                           pin 3 +Vout (12 V) ───────────────────── red    (+12 V)
 GND ──────────────────────────────┬────── pin 2 GND
                                   └──────────────────────────────────────────────── black  (GND)
 PWM (open collector, inverted) ───────────────────────────────────────────────────── blue   (PWM)   [×2: both blue wires here]
 FG  (PB3) ◄───── only if PB6 is HIGH-side (§4.5) ─────────────────────────────────── yellow (tach)  [×2: ONE fan only]
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

### 3.4 Acceptance test after fitting the buck

| Check | Pass | Basis |
|---|---|---|
| Buck output at M106 S255, fan(s) running | 11.4–12.6 V | ±5 % (ESTIMATED) |
| Extruder temperature at 200 °C, steady, M106 S0 vs S255 (after the MPC re-cal) | no new jitter above ±0.1 °C in the temperature graph | ESTIMATED; EMI into the thermistor |
| `MEASURE_AXES_NOISE` (ADXL on the nozzle board), fan off vs fan 100 % | noise rises by no more than ~20 % over the same test with the stock fan | ESTIMATED |
| `klippy.log` during a 1 h print | no `nozzle_mcu` communication errors or "Timer too close" | — |
| Module temperature after 30 min at 100 % in a 45 °C chamber | below the datasheet limit; by touch, not painful (< ~60 °C) | ESTIMATED |

## 4. Probing PB6 (high or low side, current) — step by step

Goal: closes M15 and decides the wiring in §4.5. Time: about 30 min. Tools: a multimeter with
alligator-clip leads, two back-probe pins (or sewing needles), and a phone camera.

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

1. Take the front cover off (stock: 2 × M3×4 screws at the sides, slide forward; research/02 C5).
   The plug stays seated.
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
   way round: note it, because §5 then needs the snippet's `!` removed.

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

| Condition (all of them) | Then |
|---|---|
| The switch part is identified, its datasheet gives ≥ 1.0 A continuous at the gate drive used, **and** P = I² × R_switch ≤ 0.15 W at the planned current (ESTIMATED limit for a SOT-23 in a 45–60 °C chamber), **and** the connector is a 1.25 mm type rated ≥ 1 A per contact (PicoBlade class; check the datasheet of the type you find) | up to the planned current is OK |
| Anything not met | stay at or below **0.3 A demonstrated** on this channel |

Worked numbers (ESTIMATED): with R_switch = 0.1 Ω, 0.6 A gives 36 mW. With R_switch = 0.5 Ω,
0.6 A gives 0.18 W, which fails.

### 4.5 Decision table

| Measured topology | [V-4020] ×1 | [V-4020] ×2 (0.6 A) | [V-SS] ×1 / ×2 (+ buck) | [V-DELTA] ×1 / ×2 (+ MOSFET) |
|---|---|---|---|---|
| **High-side** (FAN+ 0 V at S0 and 24 V at S255; GND pin always 0 V) | drop-in | only if §4.4 passes at 0.6 A | buck between FAN+ and GND; tach to PB3 allowed (fan GND = true GND) | add-on as §5; FG not connected |
| **Low-side** (FAN+ always 24 V; GND pin ≈ rail-ish at S0 and ≈ 0 V at S255) | drop-in (this is the stock design) | only if §4.4 passes; FG from one fan only | buck between FAN+ and the switched GND pin; **do not connect the tach** (when off, the fan's GND floats up and the FG wire could push current into PB3); PWM wire as stock | add-on as §5 (it works with either topology); FG not connected |
| **No switching seen** (FAN+ 24 V and GND 0 V at both settings) | drop-in | as above | buck from FAN+/GND, no tach; the fan is then stopped only by 0 % PWM; check the CBM datasheet for its behaviour at 0 % duty before relying on it | add-on as §5 (the MOSFET does the switching) |
| Stock fan still turns slowly at `M106 S0` | — | — | report it: a sneak path through the PWM line; do not build [V-SS] until it is explained | add-on unaffected |
| 2-fan current would exceed 0.3 A **and** §4.4 fails | — | **not buildable** | 2 × CBM = 0.37 A max at 24 V: also exceeds 0.3 A, so use 1 fan or accept it only at a typical 0.25 A with `max_power: 0.8` (ESTIMATED) | 2 × Delta = 0.32 A max, 0.22 A typical: acceptable margin decision for the lead |

Record the results in `missing-information.md` M15 (owned by the lead).

## 5. Add-on (b): low-side MOSFET for 2-wire 24 V blowers [V-DELTA]

### 5.1 Schematic

The gate is driven from the board's **PWM pin** (the PB8 signal behind its open-collector stage).
When the stage is off, the line is pulled up, so the MOSFET conducts and the fan runs. That is the
same "high = run" polarity a 4-wire fan sees, so the config keeps `!nozzle_mcu:PB8`, and Klipper
still sees one `[fan]`. PB6 keeps cutting the supply at 0 %.

```
 Board "Model Fan" plug
                                                                          Fan 1 (and Fan 2 in parallel)
 FAN+ (24 V) ──●──────────────────────────────────●───────────────────────── red   (+24 V)
               │                                  │
               R1 22 kΩ                           D1  SS14 / 1N5819  (cathode ▲ to FAN+)
               │                                  │
 PWM ──────────●──── R2 100 Ω ────●── G           ●───────────────────────── black (−)
 (open coll.)  │                  │    ┌── D ─────┘
               DZ1 5.1 V          R3   │  Q1  N-MOSFET, logic level
               (BZX84C5V1,        100kΩ│      (IRLML0040, 40 V)
               cathode to PWM)    │    └── S
               │                  │        │
 GND ──────────●──────────────────●────────●
 FG  ── leave unconnected (insulate the Delta's FG wire), see §5.4
```

- **R1 + DZ1** pull the PWM line up to 5.1 V. That is the level a 4-wire fan's own pull-up would
  put on the board's stage, so the stage never sees 24 V. Current when the stage pulls low:
  24 V / 22 kΩ ≈ 1.1 mA. Zener current when high: (24 − 5.1) / 22 kΩ ≈ 0.86 mA. (ESTIMATED)
- **If §4.2 step 4 showed the board already pulls PWM to 3.3/5 V:** leave out R1 and DZ1, and use a
  MOSFET specified at V_GS = 2.5 V (IRLML6344, 30 V, see §5.2).
- **R2** (100 Ω) damps gate ringing. **R3** (100 kΩ) holds the gate off at power-up. If the PWM
  wire is disconnected, R1 drives the gate high and the fan runs at full speed. That is the same
  fail-safe as an unconnected 4-wire PWM input.
- **D1** clamps the inductive kick of the fan leads and motor at every PWM edge.
- **Two fans:** both red wires to FAN+, both black wires to the drain. One D1 across the pair is
  enough.

### 5.2 Part list (per toolhead)

| Ref | Part | Rating needed | Example part | Status |
|---|---|---|---|---|
| Q1 | N-MOSFET, logic level, SOT-23 | V_DS ≥ 40 V (24 V rail + transients), R_DS(on) ≤ 0.1 Ω at V_GS 4.5 V, I_D ≥ 1 A | Infineon **IRLML0040TRPbF** (40 V); 30 V alternatives IRLML6344 or AO3400A only if a 30 V rating is accepted | ratings from memory, **check the datasheet** (ESTIMATED) |
| D1 | Schottky, 1 A, ≥ 40 V | | SS14 (SMA) or 1N5819 (THT) | ESTIMATED |
| DZ1 | Zener 5.1 V, 250–500 mW | | BZX84C5V1 (SOT-23) or BZX79C5V1 (THT) | ESTIMATED |
| R1 | 22 kΩ, ≥ 0.1 W | P = 24² / 22 k = 26 mW | 0805 or 1/4 W THT | ESTIMATED |
| R2 | 100 Ω | | 0805 | — |
| R3 | 100 kΩ | | 0805 | — |
| — | perfboard or SOT-23 adapter, about 15 × 10 mm; heat-shrink over the whole board | | | ESTIMATED mass 1–2 g with leads |
| — | 4-pin pigtail matching the board's "Model Fan" socket | pitch per §1 (**MEASURE**) | buy a spare Creality 4020 lead or a pre-crimped 1.25 mm 4P cable; do not cut the stock fan | — |

Losses at 2 × Delta (0.32 A max): I² × R_DS(on) ≈ 0.32² × 0.056 Ω ≈ 6 mW. Switching losses at
100 Hz are negligible (ESTIMATED).

### 5.3 PWM frequency, coil whine and the Kalico settings

A 2-wire brushless fan has its own commutation electronics. A low-side MOSFET chops the **supply**
of those electronics, not a speed input:

| PWM frequency | What happens | Verdict |
|---|---|---|
| 10–100 Hz (`cycle_time` 0.100–0.010) | Each off-period lets the fan coast on its rotor inertia, while its controller drops out and restarts. Speed follows duty well. You may hear a 100 Hz hum or tick at mid duties. | **Use this.** 0.010 (100 Hz) is Klipper's default and the stock channel's value |
| 200–500 Hz (0.005–0.002) | Usually smoother. Some fans start to lose speed control (the controller never fully restarts) | try it only if the 100 Hz hum bothers you |
| 1–10 kHz | Audible **coil whine** from the windings and the fan's input capacitor, at the frequency where the ear is most sensitive | **avoid** |
| ≥ 20 kHz | Silent, but the fan's input capacitor takes a current spike at every edge, and software PWM cannot reach it (hardware PWM on PB8 is unverified) | not available |

Kalico values for [V-DELTA] (`part_fan_delta_mosfet.cfg`):

| Option | Value | Why |
|---|---|---|
| `cycle_time` | 0.010 | as above |
| `kick_start_time` | 0.5 | Delta's start voltage is 14 V of 24 V (operating range 14–27.6 V, research/03 §10.2). A low duty may not start a stopped blower, so give it 0.5 s at full power (ESTIMATED; Klipper's default is 0.1 s) |
| `off_below` | 0.25, ESTIMATED placeholder | Below this the fan stalls, so it is switched off instead. Tune it as in §5.5 |
| `max_power` | 1.0 | full 24 V available |
| `tachometer_pin` | not set | see §5.4 |

### 5.4 Why the Delta's tach stays unconnected

With supply PWM, the FG output loses power during every off-period, so it only reads correctly at
100 %. With a low-side switch, the fan's negative lead (FG's reference) floats up toward 24 V when
the MOSFET is off. The FG wire could then push current into PB3. Insulate the FG wire. The -F00 is
still the variant to buy (research/03 §12.1: Mouser does not ship the plain BFB0524HH to EU
consumers).

### 5.5 Tuning `off_below` and `kick_start_time` (any variant)

1. With the fan stopped, send `M106 S{n}` for n = 13, 26, 38, 51, 64, 77 (5–30 %). Wait 5 s at
   each, then `M107`. Note the lowest n that starts the fan **5 times out of 5**.
2. Set `off_below` to that duty plus 0.05 (so S51 → 0.20 + 0.05 = 0.25).
3. From a running fan, step down the same way. If the fan stalls above `off_below`, raise it.
4. Compare with the Orca filament minimum fan speeds: ABS/ASA use 0–30 %, PETG 30–80 % (research/01
   §C.2). Any request below `off_below` turns the fan **off**, so a high `off_below` changes ASA
   cooling. Keep it as low as the fan allows.
5. Any change to `off_below`, `max_power` or `cycle_time` changes the fan-speed → airflow mapping,
   so re-run MPC afterwards (`calibration.md` step E).

## 6. Electrical budget, channel 1

At 24 V. Datasheet values from research/03 §10.2 and §12.2. The buck is assumed 90 % efficient
(ESTIMATED; research/03 used the same). Start-up surge is ESTIMATED at up to about 2× rated for
< 1 s.

| Variant | Per fan (rated / max, at the fan's voltage) | Channel 1 at 24 V, typical / max | vs 0.3 A demonstrated |
|---|---|---|---|
| [V-4020] ×1 | 0.30 A at 24 V (SECONDARY) | 0.30 / 0.30 | = stock |
| [V-4020] ×2 | 0.30 A | **0.60 / 0.60** | 2×: only with §4.4 passed |
| [V-SS] ×1 + buck | 0.22 / 0.33 A at 12 V (VERIFIED datasheet) | 0.12 / 0.18 (+ a few mA buck quiescent) | inside |
| [V-SS] ×2 + buck | same | 0.25 / **0.37** | max above 0.3: §4.4 decides |
| [V-DELTA] ×1 + MOSFET | 0.11 / 0.16 A at 24 V (VERIFIED datasheet) | 0.11 / 0.16 (+ 1.1 mA add-on) | inside |
| [V-DELTA] ×2 + MOSFET | same | 0.22 / **0.32** | max marginally above 0.3 |

Toolhead fan total = channel 1 + 0.1 A (3010 on channel 2, research/03 §2).

Added mass (ESTIMATED): buck 1.0–1.9 g plus leads (≈ 2–3 g total), MOSFET add-on 1–2 g. Their
mounting points on the frame are a CAD open item (STATUS "Next steps" 3).

## 7. Kalico config snippets

The files are in `hardware/toolhead/components/fans/klipper/`:

| File | Variant |
|---|---|
| `part_fan_stock4020.cfg` | [V-4020] ×1 or ×2. Stock values made explicit, with an optional tach |
| `part_fan_samesky.cfg` | [V-SS] ×1 or ×2 with the buck |
| `part_fan_delta_mosfet.cfg` | [V-DELTA] ×1 or ×2 with the MOSFET add-on |

**How to use one:**
1. Copy the chosen file next to `tuning.cfg` on the printer, as `part_fan.cfg`.
2. Add `[include part_fan.cfg]` as the **last** line of `tuning.cfg`. Each snippet re-declares
   `[fan]` with only the options it changes. Klipper merges a re-declared section and the later
   value wins, so the include must come after Pellcorp's `fan_control.cfg`, which `tuning.cfg`
   does.
3. `FIRMWARE_RESTART`. Check in `klippy.log` (config dump at start) that `[fan]` shows the new
   values.
4. Run `CONFIG_OVERRIDES` (or `BACKUP_TO_GITHUB`) so the change survives Pellcorp updates.

**Rollback:** delete the include line (and the file), then `FIRMWARE_RESTART`. Pellcorp's stock
`[fan]` applies again. After any change of fan or config, re-run MPC (`calibration.md`).

**Tach and MCU load.** Pellcorp left the tach commented out. A 0.8–1.0 ms poll adds timer load to
the nozzle MCU, the one that had move-queue trouble (research/03 §10.6). Enable the tach for
commissioning. Keep it on only if a long print shows no `nozzle_mcu` timing errors in
`klippy.log`.

Klipper's rule for the poll interval is `tachometer_poll_interval < 30 / (tachometer_ppr × max rpm)`:

| Fan | Max rpm (rated + 10 %) | Limit at ppr 2 | Value used |
|---|---|---|---|
| stock 4020 | 13 200 (12 000 ±10 %, SECONDARY) | 1.14 ms | 0.0008 (Pellcorp's commented value) |
| Same Sky CBM-5015BF | 8 250 (7 500 ±10 %, ESTIMATED tolerance) | 1.82 ms | 0.0010 |
| Delta | — | — | tach not used |
