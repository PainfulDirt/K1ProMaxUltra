# 03 - Fans and cooling (Agent 3: fan research and cooling engineering)

Scope: the fans we own, the stock K1 Max toolhead fans, the toolhead's fan electrics, candidate fans to buy, P-Q curves for CFD, a pre-CFD operating-point estimate, and a recommended configuration.

Status labels used throughout:

- **VERIFIED**: read directly from a manufacturer datasheet (URL given).
- **SECONDARY**: from a retailer, distributor or forum page, or from a manufacturer page that was read only through a search-engine extract (cited).
- **DIGITIZED**: read off a manufacturer curve.
- **ESTIMATED**: my own arithmetic or assumption. The method is stated each time.
- **INFERRED**: deduced from firmware config, not measured. Used for electrical topology.

> **Update (network restored): see [§10](#10-verified-data-network-restored).** Manufacturer datasheets were since downloaded and their P-Q curves digitized into new `*_digitized.csv` / `*_proxy-scaled.csv` files. Sections 1-9 are kept as written, and the ESTIMATED CSVs are unchanged, because the CFD campaign is using them.
>
> **Important limitation, read first.** This session's network policy blocks every manufacturer and distributor host. Blocked hosts include www.sunon.com, www.sunonusa.com, www.fansco.com, www.delta-fan.com, www.mouser.com, www.digikey.com, cdn-reichelt.de, www.tme.eu, bttwiki.com, pastebin.com and printables.com, for both WebFetch and curl. Only GitHub could be reached directly. All fan numbers below therefore come from **web-search extracts** of the cited pages. The datasheet PDFs could not be opened, and no P-Q curve could be digitised.
>
> As a result:
> - **No value in this document is VERIFIED.** Manufacturer numbers are at best SECONDARY.
> - **Every P-Q curve is ESTIMATED.** Each one is a generic curve shape anchored on the published shut-off pressure and free-air flow.
>
> To upgrade the curves to DIGITIZED, do one of these, then re-run `operating_point.py` after replacing the shape tables:
> - allow those domains in the environment's network settings (Network access, then Allowed domains), or
> - drop the PDFs into `scratchpad/ref/fans/`.

---

## 1. Fans we own

| Item | Sunon **MF40202VX-1000U-G99** | Sunon **MF50152VX-1L02C-A99** |
|---|---|---|
| Type | **Axial** (tube-axial), not a blower: "Fan Tubeaxial 24VDC Square 40 mm" (DigiKey) - SECONDARY | **Centrifugal blower** (5015 radial) - SECONDARY |
| Size | 40 × 40 × 20 mm - SECONDARY | 50 × 50 × 15 mm nominal - SECONDARY. The sibling Sunon blower sheet MF50151VX-1B00U-A99 gives a 51.7 mm frame |
| Voltage | **24 VDC** (Sunon code digit "2" = 24 V) - SECONDARY (DigiKey/SOS) | **24 VDC** - SECONDARY (resellers). Caution: one reseller lists the same specs under the 12 V MF50151VX |
| Current | 39 mA rated (DigiKey, SOS); 45 mA max (RS, for the -A99 sibling) - SECONDARY | 70 mA rated / 81 mA max - SECONDARY (reseller). A second listing says "0.7 A-0.81 A", an obvious typo |
| Power | 0.94 W - SECONDARY | 1.95 W - SECONDARY |
| Speed | 8000 rpm - SECONDARY | 6000 rpm ±10 % - SECONDARY. Another listing gives 5000 rpm / 40 dBA |
| Max flow | 10.8 CFM (0.302 m³/min = 5.10e-3 m³/s) - SECONDARY | 4.8 CFM (2.27e-3 m³/s) - SECONDARY |
| Max static pressure | 0.290 inH2O = **72.2 Pa** - SECONDARY (DigiKey, Chipsfind) | 0.76 inH2O = **189 Pa** - SECONDARY (reseller, 3DPBlog) |
| Noise | 27.5 dBA - SECONDARY | 43.8 dBA - SECONDARY |
| Bearing | Vapo (Sunon fluid) - SECONDARY | MagLev (Sunon) - SECONDARY |
| Wires / connector | **3 wires: +24 V, GND, tach (FG)**; no PWM wire - SECONDARY (DigiKey "3 Wire Leads"). Connector not listed | **2 wires (+, -)**; no tach, no PWM; XH2.54-2P on some listings - SECONDARY |
| Mass | 29.03 g - SECONDARY (DigiKey -A99/-G99 listing) | 28.37 g - SECONDARY (reseller) |
| Life | 70 000 h @ 40 °C - SECONDARY | not found |
| P-Q curve | not obtained. CSV is **ESTIMATED** (axial shape) | not obtained. CSV is **ESTIMATED** (blower shape) |

Notes:

- **Datasheet status.** No Sunon datasheet for the exact **-1L02C** suffix was found. It looks like an OEM/lead-wire variant of the 24 V Sunon 5015 MagLev blower; a 4-pin **PWM** variant, MF50152VX-1L01C-Q99, also exists (eBay.de listing, SECONDARY). The closest Sunon sheet, for the 12 V MF50151VX-1B00U-A99 ([fansco copy](https://www.fansco.com/datasheets/sunon/MF50151VX-1B00U-A99.pdf), [TME copy](https://www.tme.eu/Document/b30ea71fee61d11101012e50df6ac0ad/MF50151VX-A99-DTE.pdf)), gives 0.155 A, 5.4 CFM, 0.97 inH2O and 6000 rpm. The real 24 V curve may therefore sit between 189 and 242 Pa. The script carries this as an uncertainty band.
- **Name trap.** **MF50152VX-1000U-A99** (no "1L02C") is a 50 × 15 **axial** fan: 18.6 CFM, 0.31 inH2O, 55/64 mA ([reichelt copy of the Sunon sheet](https://cdn-reichelt.de/documents/datenblatt/C800/SUN_MF50152VX-1.pdf)). Do not use its numbers for our blower.
- **Role of the 4020 axial.** It is a hotend (heat-sink) fan candidate. At 72 Pa it is a poor ducted part-cooling fan (see section 6).

Sources:

- MF40202VX: [DigiKey](https://www.digikey.com/en/products/detail/sunon-fans/MF40202VX-1000U-G99/7927786), [SOS Electronic](https://www.soselectronic.com/en-us/products/sunon/mf40202vx-1000u-g99-375391), [Chipsfind](https://www.chipsfind.com/part-item/01750959-MF40202VX-1000U-G99), [RS (-A99)](https://uk.rs-online.com/web/p/axial-fans/2025408).
- MF50152VX-1L02C: [3Dandy](https://3dandy.com/product/1642/sunon-5015-195w-24v-blower-fan-2pin-mf50152vx-1l02c-a99), [Newegg](https://www.newegg.com/lemincrash-mf50152vx-1l02c-a99/p/2S7-09CJ-00003), [eBay](https://www.ebay.com/itm/364477240013), [west3d](https://west3d.com/products/sunon-5015-premium-blower-fan-maglev-suspension-bearing-24v), [okmarts](https://okmarts.com/sunon-fan-mf50152vx-1l02c-a99.html).

## 2. Stock K1 Max fans

| Fan | Where / Klipper name | Spec | Status |
|---|---|---|---|
| **Part-cooling ("model") fan** | Toolhead front, on the nozzle board. `[fan]` | **4020 blower, 24 V, 0.3 A, 12 000 rpm ±10 %, 40 × 40 × 20 mm, 4-pin** (connector reported as XH2.54-4P *or* 1.25-4P by different sellers). Retailer type code **CHT4024BY-W20C** (unconfirmed). Creality part no. 4004110132. Flow "6.4 CFM" (K1C listing; the same listing also claims "<25 dB, sleeve bearing", which is implausible at 0.3 A / 12 000 rpm). **No static-pressure figure is published anywhere.** | SECONDARY ([3DPrintingCanada K1/K1 Max](https://3dprintingcanada.com/products/official-creality-k1-k1-max-4020-blower-fan), [K1C](https://3dprintingcanada.com/products/official-creality-k1c-4020-blower-fan), [digitec](https://www.digitec.ch/en/s1/product/creality-4020-blower-fan-filament-cooling-for-k1c-and-k1-max-3d-printer-accessories-47334487), [makerparts3d](https://makerparts3d.com/products/4020-blower-fan-dc-24v-0-3a-for-creality-k1-k1-max)) |
| **Hotend / heat-sink ("throat") fan** | Toolhead, heat sink. `[heater_fan hotend]` | **3010 axial, 24 V, 0.1 A, 12 000 rpm, 30 × 30 × 10 mm, 1.25-3P (3-wire with tach)**. Type EFC-03A24L, Creality SKU 3205010322 / 4004110133. Early K1/K1 Max use a standard 3010; newer K1 Max/K1C use a proprietary 3010 (TH3D). No flow or pressure data published. | SECONDARY ([3dprintingusa](https://3dprintingusa.com/products/official-creality-k1-k1-max-3010-axial-fan), [makerlab](https://www.makerlab-electronics.com/products/creality-3010-axial-fan-for-k1-k1-max-4004110133), [TH3D guide](https://www.th3dstudio.com/2025/03/26/get-the-right-fans-for-your-creality-k1-series-weve-got-you-covered-%E2%9C%85/)) |
| Auxiliary side blower (not toolhead) | Left side of frame, main board **PB1**. `[fan_generic auxiliary]` | 24 V, **0.80 A** blower; frame size not published | SECONDARY ([spool3d](https://spool3d.ca/creality-k1-auxillary-side-blower-fan/)) |
| Chamber exhaust (not toolhead) | Rear, main board **PC0**. `[fan_generic chamber]` + `[temperature_fan chamber_fan]` (watermark, 35 °C) | Size not confirmed (a 6025 listing could not be tied to this position) | — |
| Electronics fans | Main board PB2 (always on); 6015 control-box fan | 24 V | SECONDARY ([fysetc](https://www.fysetc.com/products/fan-3010-axial-4020-blower-6015-hydraulic-24v-creality-k1)) |

**Stock part-fan P-Q (ESTIMATED).** No Creality data exists, so I characterised it by fan affinity from the only 24 V 4020 blower with retailer P/Q data, the GDSTIME GDB4020 (6500 rpm, 3.67 CFM, 0.46 inH2O; [3DPrintingCanada](https://3dprintingcanada.com/products/gdstime-4020-24v-premium-fan-with-ball-bearing), SECONDARY):

- Q scales with n: 3.67 × 12000/6500 = **6.8 CFM**. This agrees with the 6.4 CFM listing, which supports the scaling.
- ΔP scales with n²: 114.6 Pa × (12000/6500)² = **391 Pa**.
- Power scales with n³: 1.5 W × 6.3 = 9.4 W, against the listed 0.3 A × 24 V = 7.2 W. Same order of magnitude.

The CSV uses Qmax 6.4 CFM and ΔPmax 390 Pa, with an uncertainty band of 250-500 Pa. **This is the least certain curve in the set.** If it holds, the stock 4020 has ~1.8-2× the pressure of any 6000 rpm 5015. Measure it before CFD relies on it (section 9).

## 3. Toolhead electrics (K1 Max nozzle board)

**Sources:**

- Pellcorp `k1/patches/fan_control.cfg` and `rpi/printers/creality-k1m-2024.cfg` ([github.com/pellcorp/creality](https://github.com/pellcorp/creality), cloned).
- Creality stock printer.cfg v1.0.2 header and fan sections ([quocanhcgd/Creality-K1](https://github.com/quocanhcgd/Creality-K1/blob/main/printer.cfg)).
- Stock-firmware fan notes ([meteyou/creality-k1 fans.cfg](https://github.com/meteyou/creality-k1/blob/main/klipper/config/addons/fans.cfg)).
- No schematic of the nozzle board is public.

**MCU and supply.** The nozzle MCU is a **GD32F303CBT6** (stock printer.cfg header: "Nozzle_mcu: chip: GD32F303CBT6, version CR-K1-MAX-NOZZLE-V1.0.0"; the same chip appears on the PCBA_G "NOZZLE-C-V13" board listings). Fans are supplied at **24 V**. Every stock toolhead fan is a 24 V part.

| Channel | Pins (nozzle_mcu) | Pellcorp/Kalico config | Topology (INFERRED) | Known load |
|---|---|---|---|---|
| **1 - part fan (4-pin)** | **PB8** = PWM, inverted (`!`); **PB6** = enable; **PB3** = tach (commented out) | `[fan] pin: !nozzle_mcu:PB8`, `enable_pin: nozzle_mcu:PB6`, `cycle_time: 0.0100` (100 Hz), `hardware_pwm: false`, `# tachometer_pin: ^nozzle_mcu:PB3`, `# tachometer_poll_interval: 0.0008`. Stock Creality firmware drove PB6 as a `static_digital_output` and PB8 as `[output_pin fan0]`, 0-255 | PB8 drives the fan's **PWM control wire** through an open-collector stage (hence the inversion). PB6 switches the fan's supply so the fan is truly off at 0 %. **This channel is built for a 4-wire PWM fan.** A 2- or 3-wire fan on it would only switch on/off via PB6. | 0.3 A (stock 4020) |
| **2 - hotend fan (3-pin)** | **PB5** = switch; **PB4** = tach | `[heater_fan hotend] pin: nozzle_mcu:PB5`, `tachometer_pin: ^nozzle_mcu:PB4`, `heater_temp: 40` (default cycle_time 0.010, software PWM, runs at fan_speed 1.0) | Switched output (probably a low-side MOSFET) with tach input. Software PWM is possible but makes the tach reading unreliable. | 0.1 A (stock 3010) |

**Free outputs.** None are documented. The other used nozzle-MCU pins are: PB0-2 (extruder stepper), PB7 (heater), PA0 (thermistor), PB10/11 (TMC UART), PA4-7 (accelerometer SPI) and PA10 (switch input). **The toolhead therefore offers at most two independently controllable fan channels, and only one of them is a proper PWM channel.**

**Current limits.** Not published, and no schematic. The only demonstrated loads are **0.3 A on channel 1** and **0.1 A on channel 2** (ESTIMATED as safe ceilings: demonstrated, not rated). Anything above those needs the board inspected (identify the MOSFET or transistor and the trace/connector rating) or a separate driver.

**Tach.** At 12 000 rpm with 2 pulses per revolution the tach runs at 400 Hz, so a poll interval of 2.5 ms or less is needed. Pellcorp left the 0.8 ms poll commented out. Tach on PB4 is active for the hotend fan. Klipper only reports rpm unless a macro acts on it.

**Hardware PWM.** STM32F1-family timers do exist on PB8 (TIM4_CH3) and PB6/PB5. However, Pellcorp deliberately uses software PWM at 100 Hz, and whether the MCU firmware on the nozzle board supports hardware PWM there was not verified. 100 Hz on a 4-wire fan's PWM input works in practice (stock behaviour), even though fan specs usually call for ~25 kHz.

**Klipper/Kalico control.**
- Independent fans are possible with `[fan]` (M106), `[fan_generic]` (SET_FAN_SPEED), `[heater_fan]`, `[controller_fan]` and `[multi_pin]` (one logical fan on several pins), as long as each has its own pin.
- **MPC coupling.** `tuning.cfg` sets `[extruder] cooling_fan: fan`. In `printer.cfg.save_config`, `fan_ambient_transfer = 0.0800, 0.0892, 0.0995, 0.1062, 0.1148, 0.1149, 0.1166` W/K from fan 0 → 100 %. The stock part fan therefore raises the block's heat loss by **+46 %**: about **+8 W of the 60 W heater** at ΔT ≈ 225 K. Any new duct changes this, so after a fan or duct change re-run `MPC_CALIBRATE HEATER=extruder FAN_BREAKPOINTS=7` (the user's Forced_Calibration macro already does this).
- Kalico's MPC models **one** cooling fan, so dual part fans should be driven by **one** command (one logical fan) to keep the model valid.
- **Where the fan sections live.** Neither `printer.cfg` nor `tuning.cfg` contains fan sections. They come from Pellcorp's `fan_control.cfg` on the printer, so any change would be an override in `tuning.cfg`.

**Driving 12 V or 5 V fans from the 24 V outputs.**
- A buck converter (24 → 12 V or 5 V, ≥0.5 A, e.g. an MP1584-class module) on the toolhead would supply the fan's +.
  - Channel 2 (switched, assumed low-side) can still switch the fan's −.
  - Channel 1's PWM wire can still drive a 4-wire 12 V fan's PWM input, provided the PWM input is open-collector tolerant (normal for 4-wire fans).
- Costs: ~3-6 g, a heat source on a hot toolhead, an extra failure point, and a measurement needed of whether channel 1 switches + or −.
- **Never use series resistors, or two 12 V fans in series**: unequal loads and stall/start-up problems.
- **Verdict: a bad idea here.** 24 V versions exist for every useful size (4010/4020 axial, 4020/5015 blowers), so buy 24 V. The only exception is a 12 V/5 V-only premium fan (e.g. Noctua) for silence, which is not needed.

## 4. Purchase candidates

| Candidate | Type / size | V / I / P | rpm | Qmax | ΔPmax | Noise | Mass | Wires | Price seen | Status / source |
|---|---|---|---|---|---|---|---|---|---|---|
| **Creality 4020 blower** (stock part, 4004110132) | blower 40×40×20 | 24 V / 0.3 A / ~7.2 W | 12 000 | 6.4 CFM | ~390 Pa (ESTIMATED, 250-500) | not credible ("<25 dB") | not found | **4 (PWM + tach)** | TH3D 4020 layer fan $13.99 | SECONDARY / ESTIMATED (section 2) |
| **Delta BFB0524HH** (-F00 = tach, -R00 = locked-rotor) | blower 51×51×15 | 24 V (14-27.6 V) / 0.11 A typ, 0.16 A max / 2.64 W | 6500 | 4.59 CFM | 0.866 inH2O = 22.00 mmH2O = **215.7 Pa** | 45 dBA (48 max) | 28.1 g | 2 or 3 (no PWM wire) | $9.8-14.7 (distributors) | SECONDARY: [delta-fan.com BFB0524HH-F00](https://www.delta-fan.com/products/BFB0524HH-F00.html), [FansCo Delta sheet](https://www.fansco.com/uploads/2024/01/BFB0524HH-Delta.pdf), [Mouser](https://www.mouser.com/en/ProductDetail/Delta-Electronics/BFB0524HH-F00?qs=Tx9Tc1LIQ%252BEMmOU6Kpl%252BcQ%3D%3D), [Master Electronics](https://masterelectronics.com/en/delta-fans/bfb0524hh-11251815.html) |
| Delta BFB0524H-R00 | blower 51×51×15 | 24 V / 0.09 A / 2.16 W | 5500 | — | 0.709 inH2O | — | — | 3 | — | SECONDARY ([delta-fan.com](https://www.delta-fan.com/products/dc-centrifugal-fans/BFB0524H-R00.html)); weaker than -HH |
| GDSTIME GDB5015 24 V | blower 50×50×15 | 24 V / 0.1 A / 2.2 W | 6000 | 5.36 CFM (4.42-5.36) | 0.79-1.21 inH2O (conflicting) | 32-43 dBA | not found | 2 (XH2.54) | — | SECONDARY ([hotend.eu](https://www.hotend.eu/p/gdstime-radial-fan-blower-5015-24v-dual-ball), [3dprintingusa](https://3dprintingusa.com/products/gdstime-5015-24v-premium-blower-fan-with-ball-bearing)); data unreliable |
| GDSTIME GDB4020 24 V | blower 40×40×20 | 24 V / 0.06-0.07 A / 1.5 W | 6500 | 3.67 CFM | 0.46 inH2O (115 Pa) | 32.5 dBA | — | 2 | — | SECONDARY; too weak, used only as the affinity reference |
| Sunon MF50152VX-1L01C-Q99 | blower 5015 PWM | 24 V / 1.95 W | — | (as -1L02C?) | — | — | — | **4 (PWM)** | — | SECONDARY (eBay.de title only); the PWM twin of our blower, worth finding a datasheet for |
| 4010 axial (hotend) | Sunon MF40102VX-1Q03C-A99 | 24 V / 80 mA / 1.92 W | 10 000 | 11 CFM | not listed | 36.8 dBA | — | — | — | SECONDARY ([LCSC](https://www.lcsc.com/product-detail/C456910.html)) |
| 3010 blower (TH3D) | blower 30×30×10 | 24 V / 0.06 A | 9500 | 1.9 CFM | not listed | 29 dBA | — | — | — | SECONDARY ([TH3D](https://www.th3dstudio.com/product/th3d-3010-blower-fan-24v-dual-ball-bearing/)); too weak for part cooling |
| 5020 blowers | NMB BM5020-05W-B40 (24 V, 5.6 CFM, 0.74 inH2O, partly obsolete); Mechatronics B5020L24B (6.0 CFM, 0.20 inH2O) | — | — | — | — | — | — | — | — | SECONDARY ([DigiKey](https://www.digikey.co.uk/en/products/detail/mechatronics-fan-group/B5020L24B-BSR/5209733)); no gain over a 5015, heavier |
| 45×45 blowers | Delta BFB04512VHD (45×45×20, **12 V only**, 6.01 CFM, 14.15 mmH2O); BFB04512HHA (45×45×10, 12 V, 0.555 inH2O) | — | — | — | — | — | — | — | — | SECONDARY; no 24 V 45 mm Delta blower found |
| "4028 turbo" | no manufacturer datasheet for a 24 V 40×28 *blower* was found in this session | | | | | | | | | not pursued; no data |
| **CPAP: Wonsmart WS7040-24-V200** (BIQU/BTT "Universal Turbo Kit") | BLDC centrifugal, ~60 mm Ø, 15 mm outlet (Mellow) | 24 V / 0.8-2.7 A / up to 68 W; needs **WS2403DY01V04 driver** (9-29 V, 0-5 V or PWM speed input, 15 g) | ≤45 000 | 14.7 CFM (BTT) / 22-25.5 m³/h (Wonsmart) | **6.5-6.6 kPa** | ~65 dBA class (Wonsmart page title) | 78-80 g + driver 15 g + hose | driver | kit $66.70-75.99 | SECONDARY ([BTT wiki](https://bttwiki.com/Universal%20Turbo%20Kit.html), [Wonsmart](https://www.wonsmartmotor.com/blog/wonsmart-ws7040-24-v200-specifications-and-benefits/), [3DJake](https://www.3djake.com/biqu/universal-turbo-kit)) |

**Outlet dimensions.** These were not obtainable without the drawings (network block). Measure them on the parts, or read them from the datasheet drawings, before the duct CAD is frozen.

## 5. P-Q curve CSVs

Files are in `hardware/toolhead/components/fans/pq-curves/`, generated by `../operating_point.py`. Each holds 11 points from shut-off to free delivery.

| CSV | End points | Shape |
|---|---|---|
| `sunon_MF50152VX-1L02C-A99.csv` | 2.265e-3 m³/s, 189.3 Pa (SECONDARY) | ESTIMATED blower |
| `sunon_MF40202VX-1000U-G99.csv` | 5.097e-3 m³/s, 72.2 Pa (SECONDARY) | ESTIMATED axial |
| `creality_K1_stock_4020_blower.csv` | 3.020e-3 m³/s (SECONDARY), 390 Pa (**ESTIMATED**) | ESTIMATED blower |
| `delta_BFB0524HH.csv` (top-3 purchase) | 2.166e-3 m³/s, 215.7 Pa (SECONDARY) | ESTIMATED blower |
| `gdstime_GDB5015_24V.csv` (backup) | 2.529e-3 m³/s, 196.8 Pa (SECONDARY, low end of the conflicting range) | ESTIMATED blower |
| `wonsmart_WS7040-24-V200.csv` (top-3 purchase) | 6.937e-3 m³/s, 6600 Pa (SECONDARY) | ESTIMATED cpap |

The stock 4020 CSV doubles as the third purchase candidate, the Creality 4020.

**Header lines.** Every file starts with `# nHeaderLine=N`; skip N lines in the OpenFOAM `csv` reader. The header lines carry the source URLs, conversions and per-end-point status. The header row is `Q_m3_per_s,dP_Pa`.

**For CFD:**
- **Kinematic pressure.** Incompressible solvers use kinematic pressure, so divide ΔP by ρ (1.20 kg/m³ at 20 °C; ~1.11 at 45 °C chamber).
- **Density.** At constant rpm, a fan's ΔP scales with ρ, and so does a K·Q² duct. Flow at the operating point therefore barely depends on chamber temperature, while ΔP and fan power do.
- **PWM duty.** Use the affinity laws: Q ∝ n and ΔP ∝ n².

**Generic shapes used (p/pmax at q/qmax = 0, 0.1 … 1.0), all ESTIMATED:**
- blower: 1.00, .97, .92, .85, .77, .68, .58, .47, .34, .18, 0
- axial (with stall saddle): 1.00, .86, .76, .70, .66, .61, .53, .43, .30, .16, 0
- cpap: 1.00, .99, .97, .93, .87, .79, .69, .57, .42, .23, 0

The stock 3010 hotend fan has no data at all, so no CSV is provided. Characterise it by measurement if it is kept.

## 6. Duct model and operating points (PRE-CFD ESTIMATE)

**Model.** The duct is modelled as ΔP = K·Q², with K = Σζ · ρ / (2 A_out²). All loss coefficients ζ are referred to the outlet velocity, and ρ = 1.20 kg/m³. Fan static pressure must cover the outlet dynamic pressure, so the exit loss is ζ = 1.

| Duct | A_out | Σζ (exit + contraction + bends + friction) | K [Pa/(m³/s)²] | ΔP at 1 CFM |
|---|---|---|---|---|
| low resistance | 120 mm² (2 × 60) | 1.0 + 0.1 + 0.2 + 0.1 = 1.4 | 5.83e7 | 13 Pa |
| **medium** (lead's 2 × 40 mm² example) | 80 mm² | 1.0 + 0.3 + 0.5 + 0.4 = 2.2 | **2.06e8** | 46 Pa |
| high (narrow focused slots) | 50 mm² (2 × 25) | 1.0 + 0.5 + 1.0 + 1.0 = 3.5 | 8.4e8 | 187 Pa |

**Worked example (medium):** K = 2.2 × 1.2 / (2 × (80e-6)²) = 2.64 / 1.28e-8 = 2.06e8. At Q = 0.89 L/s: ΔP = 2.06e8 × (0.89e-3)² = 163 Pa, and v_out = 0.89e-3 / 80e-6 = 11.1 m/s.

**How the ζ values were chosen:**
- Bends: two 90° bends at ζ ≈ 0.6-1.0 each at duct velocity, with duct cross-section ≈ 1.5-2 × A_out, so (A_out/A_duct)² ≈ 0.25-0.45 when referred to the outlet.
- Friction: laminar slot flow (Re ≈ 1000-1500 at D_h ≈ 2 mm, so f ≈ 64/Re ≈ 0.05), L/D_h ≈ 5-20.
- Contraction: 0.1 (rounded) to 0.5 (sharp).

**Hotend heat sink.** Modelled as K_hs giving 12.5 / 25 / 50 Pa at 2 CFM (ESTIMATED; typical fin pack plus shroud).

**CPAP hose.** 15 mm ID × 1.5 m, Blasius friction (f = 0.316 Re^-0.25), plus fittings ζ = 1.5 at hose velocity.

Results below are from `operating_point.py`. Each cell gives total Q / outlet velocity / fan ΔP.

**A - single part fan, whole outlet area**

| Fan | low K | medium K | high K |
|---|---|---|---|
| Creality stock 4020 (ΔPmax ESTIMATED) | 4.04 CFM / 15.9 m/s / 212 Pa | **2.56 CFM / 15.1 m/s** (2.12-2.82 over the 250-500 Pa band) | 1.38 CFM / 13.0 m/s |
| Delta BFB0524HH | 2.97 / 11.7 | **1.89 / 11.1** | 1.02 / 9.6 |
| GDSTIME GDB5015 | 3.04 / 12.0 | 1.86 / 11.0 (to 2.23 at the 1.21 inH2O claim) | 0.99 / 9.3 |
| Sunon MF50152VX-1L02C (owned) | 2.90 / 11.4 | **1.80 / 10.6** (to 1.99 at 0.97 inH2O) | 0.96 / 9.1 |
| Sunon MF40202VX axial (owned) | 2.07 / 8.1 | 1.16 / 6.8 (operating in the stall region) | 0.60 / 5.6 |

**B - two identical fans, symmetric, each feeding half of the same total outlet area (totals)**

| Fans | low K | medium K | high K |
|---|---|---|---|
| 2 × stock 4020 | 4.86 / 19.1 | 2.78 / 16.4 | 1.42 / 13.4 |
| 2 × Delta BFB0524HH | 3.59 / 14.1 | 2.06 / 12.1 | 1.05 / 9.9 |
| 2 × Sunon 5015 (owned) | 3.42 / 13.5 | 1.95 / 11.5 | 0.99 / 9.3 |

**Key results:**

1. **Two fans into the same outlet area add little flow** in medium and high-resistance ducts: +5 to +15 %, because each half-duct has 4× the K. The gain only appears if the outlet area grows with the number of fans.
   - Give each fan its own 80 mm² outlet (160 mm² total) and the flow doubles at the same velocity: 2 × 1.80 = **3.6 CFM** for the owned Sunons, **3.8 CFM** for the Deltas.
   - Dual symmetric fans therefore buy **flow plus symmetric coverage**, not jet velocity.
2. **A 6000-6500 rpm 5015 is weaker in pressure than the (estimated) stock 12 000 rpm 4020.** In the same medium duct, one Sunon or Delta 5015 gives ~70-75 % of the stock flow. Two 5015s sharing the stock outlet area still do not beat the single stock fan. Two 5015s with doubled outlet area deliver ~1.4× the stock flow, at lower outlet velocity (~11 vs 15 m/s).
3. **The 4020 axial is not a ducted part fan.** It delivers 1.2 CFM at 6.8 m/s while operating in its stall region, which is noisy and has an uncertain curve.

**C - dedicated hotend fan.** The Sunon MF40202VX on a heat sink gives **2.10 / 2.88 / 3.95 CFM** (high / medium / low K_hs) at 49-55 Pa, at 27.5 dBA and 39 mA. That is a large flow margin for a heat sink, and the fan is quieter than a 12 000 rpm 3010. On a 30 mm heat sink it needs a 40 → 30 mm transition, which adds loss and roughly 29 g against a few grams for a 3010.

**D - CPAP (WS7040, 100 %, through hose + medium duct).** It gives **8.6 CFM at 50.6 m/s outlet velocity** (fan at 4.7 kPa), and 5.3-10.7 CFM across the K range. Matching the stock fan's medium-duct flow needs only ~30 % speed.

- **Strengths:** pressure reserve. The fan sits off the toolhead; only the hose and duct are on it.
- **Costs:**
  - It needs its own driver and up to 2.7 A at 24 V wired from the PSU, not from the toolhead board.
  - Its speed signal is 0-5 V or PWM. No toolhead output is free, so it would need e.g. the main board's aux-fan output PB1 plus a level interface.
  - The hose drags on a 20 000 mm/s² CoreXY toolhead.
  - It is loud.
  - The K1 Max already has the side aux blower for bulk cooling.

**Electrical and noise budget per configuration:**

| Config | Toolhead channels used | Current (24 V) | Fits stock board? | Noise / mass |
|---|---|---|---|---|
| A: stock-type 4020 on ch1 + hotend fan on ch2 | 2 of 2 | 0.3 + 0.04-0.1 A | **yes, as stock** | stock |
| A': one 5015 2-wire on ch1 | 2 | 0.08 A | on/off only (PB6) unless modified | +28 g, 44-45 dBA |
| B: 2 × 4-wire blowers paralleled on ch1 (one logical fan) | 2 | 0.6 A (2 × 4020) or ~0.16 A (2 × 5015) | 2 × 4020 = **2× the demonstrated load**, so verify the ch1 switch first. 2 × 5015 is fine on current but needs 4-wire (PWM) parts or an added MOSFET | +2 fans |
| B independent (L/R differential control) | 3 needed | — | **no**: needs a toolhead expander/CAN board, and breaks the single-fan MPC model | — |
| C: + MF40202VX hotend | ch2 | 0.039-0.045 A | **yes**, 3-wire with tach is a direct electrical match to PB5/PB4 | quieter, +~25 g |
| D: CPAP | 0 on toolhead + 1 main-board output + interface | up to 2.7 A from the PSU | needs wiring and an interface | loud, 95 g off-toolhead + hose |

## 7. Recommendation (pre-CFD)

**Recommended: configuration B + C, staged.**

1. **Hotend: Sunon MF40202VX-1000U-G99 (owned)** on channel 2 (`[heater_fan hotend] pin: nozzle_mcu:PB5`, `tachometer_pin: ^nozzle_mcu:PB4`).
   - 24 V direct, tach compatible, ~3 CFM through a typical heat sink, 27.5 dBA.
   - Use it if the new toolhead's heat sink can take a 40 mm face. Otherwise keep a 24 V 3010 (stock-type).
2. **Part cooling: two symmetric blowers, driven as ONE logical fan on channel 1** (same PWM and enable). This keeps M106 / slicer control and Kalico's single-fan MPC model valid. Each blower gets **its own outlet of ≈ 40-60 mm²** (total ≥ 80-120 mm²) so the second fan doubles flow instead of fighting the first.
   - **2a (preferred if channel 1 is confirmed for 0.6 A):** two **Creality 4020 4-pin blowers**.
     - Native to channel 1 (PWM wire + enable).
     - Highest estimated pressure (~390 Pa) gives the most margin for a compact, low-mass toolhead duct.
     - Cheap and in stock as Creality spares.
   - **2b (lower current, uses owned parts):** two **24 V 5015 blowers**.
     - The owned Sunon MF50152VX-1L02C is one. Pair it with a second Sunon, or use 2 × Delta BFB0524HH if a datasheet-backed CFD BC is wanted.
     - **Both are 2-wire**, so speed control needs either PWM on the enable pin PB6 (feasibility must be measured) or a small add-on low-side MOSFET.
     - The **4-pin PWM Sunon MF50152VX-1L01C-Q99** avoids the issue, if a datasheet confirms it.
   - Single-fan A remains the zero-modification fallback, i.e. stock electrics with a better duct.
3. **CPAP (D): not recommended as the first step.** Revisit only if CFD shows that the B duct cannot reach the target nozzle-tip velocity, or if very high-speed PLA printing is a goal. Because the side aux blower stays, bulk cooling for bridges is already covered.
4. After any fan or duct change, run `MPC_CALIBRATE ... FAN_BREAKPOINTS=7` and aim the ducts to minimise block impingement. The stock part fan currently adds ~8 W of heat loss at full speed.

**Purchase shortlist:**

| # | Part | Qty | Why | Approx. price |
|---|---|---|---|---|
| 1 | Creality official 4020 blower 24 V 4-pin (4004110132) | 2 (+1 to measure) | 4-wire PWM matches channel 1; highest pressure per gram of the small options; needed anyway to replace the ESTIMATED stock curve with a measured one | ~$10-14 each |
| 2 | Delta BFB0524HH (-F00 for tach) | 2 | Best-documented 24 V 5015 (Delta spec sheet; its P-Q curve can be DIGITIZED once the PDF is reachable); 0.11 A | ~$10-15 each |
| 3 | (conditional) BIQU/BTT Universal Turbo Kit, WS7040-24-V200 + driver | 1 | Only if CFD shows the 5015/4020 options are pressure-limited | $67-76 |

**Not buying:** GDSTIME 5015/4020 (inconsistent data), 5020 or 45 mm blowers (no gain, or 12 V only), "4028 turbo" parts (no datasheet-backed 24 V blower found), and buck converters.

## 8. Electrical notes for implementation (do not apply yet)

```ini
# sketch only - overrides would go in tuning.cfg
[fan]                                   # ch1: one logical part fan (2 blowers in parallel)
pin: !nozzle_mcu:PB8                    # PWM wire(s), open-collector, inverted
enable_pin: nozzle_mcu:PB6              # fan supply
cycle_time: 0.010
tachometer_pin: ^nozzle_mcu:PB3         # only one fan's FG can be wired here
tachometer_poll_interval: 0.0008        # 12000 rpm x 2 ppr = 400 Hz

[heater_fan hotend]                     # ch2
pin: nozzle_mcu:PB5
tachometer_pin: ^nozzle_mcu:PB4
heater: extruder
heater_temp: 50
```

When paralleling 4-wire fans, tie the PWM wires together, connect only one FG wire, and keep the 24 V/GND per fan.

## 9. Open items and measurements before CFD is trusted

1. **Get the datasheet PDFs** (allow the domains, or download manually):
   - Delta BFB0524HH spec (Delta spec sheets normally include a P-Q curve)
   - the Sunon blower sheet MF50151VX-1B00U-A99 and any -1L0xC sheet
   - Sunon MF40202VX
   - Wonsmart WS7040 drawing and curve

   Digitise the curves (WebPlotDigitizer or equivalent) and swap the generic shape tables in `operating_point.py` for the digitised points.
2. **Measure the stock 4020's shut-off pressure.** Cap the outlet and read it with a ±1-2 kPa differential manometer. Also measure free-air flow (bag-fill timing or a vane anemometer in a known-area tube). This replaces the ESTIMATED 390 Pa.
3. **Probe the nozzle-board channel 1** with a multimeter or scope:
   - Does PB6 switch +24 V or GND?
   - Is the PB8 stage open-collector?
   - What are the MOSFET/transistor part numbers?

   This decides 2a vs 2b and the real current ceiling.
4. Measure the outlet dimensions of each blower for the duct CAD.
5. In CFD, test whether the per-fan K assumed here (Σζ 1.4-3.5) is realistic for the actual duct, then re-run the operating points with the CFD-derived K.

## 10. Verified data (network restored)

Manufacturer documents could be downloaded after the network was opened. Sections 1-9 above are left as written, and so are the ESTIMATED CSVs, which the CFD campaign is using. The new curves are in **new files** in `components/fans/pq-curves/`:

- `*_digitized.csv`: a manufacturer curve read off its datasheet.
- `*_proxy-scaled.csv`: a manufacturer curve *shape* scaled to another fan's end points. Status ESTIMATED.

They use the same column format and header convention as before. To get the tables below, run `python3 operating_point.py --digitized [--plot]`; it only reads CSVs. The plot is written to `pq-curves/pq_digitized_vs_estimated.png`.

### 10.1 Documents obtained

All are saved, untrusted, in `scratchpad/ref/fans/`.

| Document | URL | Used for |
|---|---|---|
| Delta "Specification for approval", **BFB0524HH**, sample rev 00, 2003-10-28 (7 pp, scanned) | https://www.delta-fan.com/Download/Spec/BFB0524HH.pdf | specs, P&Q curve (p.5), dimensions (p.6) |
| Delta spec **BFB0524HH-F00**, 2013-07-17 (9 pp) | https://www.delta-fan.com/Download/Spec/BFB0524HH-F00.pdf | cross-check only |
| Sunon spec **MF40202VX-1000U-G99**, D04115420G-01, rev 2021-05-18 (Sunon document, FansCo-hosted) | https://www.fansco.com/datasheets/sunon/MF40202VX-1000U-G99.pdf | specs, curve (p.5, vector), FG tach (p.8) |
| Sunon spec **MF50151VX-1B00U-A99** (12 V 5015 MagLev blower), D05073850G-00, 2020-08-18 | https://www.fansco.com/datasheets/sunon/MF50151VX-1B00U-A99.pdf | nearest Sunon blower sheet to our MF50152VX-1L02C (p.7, vector curve) |
| Sunon catalogue "DC Brushless Fan & Blower" (240-A) | https://www.sunon.com/en/MANAGE/Docs/PRODUCT/286/360/Sunon%20DC%20Brushless%20Fan%20&%20Blower_(240-A).pdf | blower range check (p.83-85) |
| Same Sky **CBM-40B** series datasheet, 2025-11-04 | https://www.sameskydevices.com/product/resource/cbm-40b.pdf | 4020 blower with a manufacturer P-Q curve (CBM-4020B-160-367), proxy for the stock fan |
| Delta BFB04512VHD spec (45×45×20, 12 V) | https://www.delta-fan.com/Download/Spec/BFB04512VHD.pdf | downloaded, not used (12 V, 4500 rpm, different frame) |

**Not obtained:**
- **No Sunon sheet exists for MF50152VX-1L02C-A99.** It is an OEM suffix. Sunon's catalogue lists only **12 V** 5015 blowers (MF50151Vx-B000 family).
- **No manufacturer data exists for the Creality stock 4020** (type code "CHT4024BY-W20C").
- The Wonsmart WS7040 curve was not re-checked.
- Mouser, DigiKey, TME and Reichelt still refused or timed out (403/520), and were not needed.

### 10.2 What the datasheets confirm or change

| Fan | Now VERIFIED (datasheet) | Change vs sections 1-4 |
|---|---|---|
| **Sunon MF40202VX-1000U-G99** | 24 VDC (op. 8-27.6 V, start 8 V); **39 mA / max 45 mA**; 0.94 W / max 1.08 W (safety 1.11 W); 8000 rpm ±15 %; 10.8 CFM; 0.29 inH2O; 27.5 dBA; **29 g**; Vapo bearing (p.3; the cover says "MagLev Motor Fan"); auto-restart + polarity protection; 70 000 h @ 40 °C. **G99 = auto-restart + F-type FG**: open collector, V+ ≤ 27.6 V, If ≤ 5 mA, VL ≤ 0.5 V, **2 pulses/rev**. That works with `^nozzle_mcu:PB4` and Klipper's default ppr = 2 | All earlier SECONDARY numbers confirmed. Max current and the FG electrical spec are new |
| **Sunon MF50151VX-1B00U-A99** (12 V sibling of our blower) | 12 VDC; 0.155 / max 0.179 A; 1.86 / max 2.15 W; 6200 rpm ±15 %; **5.4 (min 4.6) CFM; 0.97 (min 0.65) inH2O**; 42.2 (max 47.5) dBA; 30 g; Vapo; 2 wires, 305 mm #26AWG; frame 51.7 × 51.6 × 15 mm | The reseller figures for our 24 V **MF50152VX-1L02C** (4.8 CFM / 0.76 inH2O, SECONDARY) are **affinity-consistent with this impeller at 88.9 % speed**: 0.889² × 0.97 = 0.766 inH2O vs 0.76, within 1 %. They are also inside Sunon's min limits. So our blower is very likely the same aero design at ~5500-6000 rpm. Its end points stay SECONDARY, but its curve **shape** is now DIGITIZED |
| **Delta BFB0524HH** | 24 V (14-27.6 V); 0.11 (max 0.16) A; 2.64 (max 3.84) W; 6500 rpm (ref); **0.130 (min 0.095) m³/min = 4.59 (min 3.35) CFM**; **22.00 (min 15.72) mmH2O = 0.866 (min 0.619) inH2O**; 45 (max 48) dBA; **28 ± 5 g**; two ball bearings; 50 000 h @ 40 °C; locked rotor: "current will shut down" (p.2) and winding impedance protection (p.3); 2 wires UL1061 #26, 340 mm; frame 51.0 × 51.3 × 15.0 mm; **outlet 20.0 × 15.0 mm outside, 17.6 × 12.2 mm inside (≈ 215 mm²)** | Typical values confirmed. New: the limited (minimum) spec and the outlet dimensions. Note that the minimum-spec unit has only 71-73 % of typical pressure and flow |
| **Same Sky CBM-4020B-160-367** (stock-fan proxy) | 12 V; 0.08 / max 0.12 A; 0.96 / max 1.44 W; 6000 rpm ±10 %; 2.66 CFM; 0.19 inH2O; 36.7 dBA; "-22" suffix = PWM + tach | Affinity to 12 000 rpm (Q × 2, ΔP × 4, P × 8) gives **5.3 CFM / 191 Pa / 7.7 W**. The listed stock power 24 V × 0.3 A = 7.2 W matches. The listed 6.4 CFM is 17 % higher. The earlier GDSTIME-based estimate gave 6.8 CFM / 391 Pa / 9.4 W. The two published 4020 impellers differ by **2.4×** in pressure coefficient, so the stock fan is only bracketed: **190-390 Pa shut-off**. Still ESTIMATED, still needs measuring |

### 10.3 Digitizing method and error

| CSV | Method | Points | Error estimate | Self-check against the datasheet table |
|---|---|---|---|---|
| `delta_BFB0524HH_digitized.csv` (DIGITIZED) | Scanned page rendered at 300 dpi. Frame found from solid lines (0-0.14 m³/min, 0-24 mmH2O). Column-by-column trace of the dark curve, with dashed grid and leader line masked: 990 raw points. Resampled to 21 uniform Q points plus the two polyline kinks (0.040, 0.073 m³/min) | 23 | ±0.05 mmH2O (±0.5 Pa), ±0.0005 m³/min | 21.98 mmH2O / 0.1302 m³/min vs 22.00 / 0.130 (≤ 0.2 %) |
| `sunon_MF40202VX-1000U-G99_digitized.csv` (DIGITIZED) | The curve is a **vector** polyline. Its 93 vertices were read from the PDF (PyMuPDF `get_drawings`) and mapped to the axis frame. Resampled to 31 Q points | 31 | < ±0.5 % full scale (stroke width) | 0.290 inH2O / 10.80 CFM, exact |
| `sunon_MF50151VX-1B00U-A99_digitized.csv` (DIGITIZED) | Vector filled outline. Centre line = mid-point of the upper and lower edges on 1 pt scan lines. 21 Q points | 21 | < ±0.5 % FS | 0.966 inH2O / 5.40 CFM vs 0.97 / 5.4 |
| `samesky_CBM-4020B-160-367_digitized.csv` (DIGITIZED) | Embedded raster (1528 × 792 px). The **11 plotted measurement markers** were found by dark-pixel density and their centroids taken | 12 | ±0.01 CFM, ±0.03 mmH2O | 0.192 inH2O / 2.65 CFM vs 0.19 / 2.66 (≤ 1 %) |
| `sunon_MF50152VX-1L02C-A99_proxy-scaled.csv` (ESTIMATED, DIGITIZED shape) | MF50151VX curve × (Q 0.8889, ΔP 0.7901) | 21 | shape as above; end points ±(SECONDARY) | 191 Pa / 4.80 CFM |
| `creality_K1_stock_4020_blower_proxy-scaled.csv` (ESTIMATED, DIGITIZED shape) | CBM-4020B curve × (Q 2, ΔP 4) | 12 | the real stock fan could be +100 % in ΔP | 191 Pa / 5.31 CFM |

All curves are at rated voltage and ~25 °C. The Sunon axial curve has a genuine **positive-slope stall saddle** at 5.2-6 CFM, so ΔP is non-monotonic there. OpenFOAM's table lookup copes with it. The hotend operating points (2-3.4 CFM) lie to the left of the saddle.

### 10.4 How far the ESTIMATED curves were off

In this table, "dev" = (estimated − digitized) / digitized, so + means the estimate was too high. Operating points use the same ducts as section 6. The stock row compares against the CBM-4020B proxy, which is itself an estimate.

| Curve | Shut-off ΔP: est → real | dev | Free-air Q: est → real | dev | Max ΔP error along the curve (% of real ΔPmax) | Medium-K flow: est → real | dev |
|---|---|---|---|---|---|---|---|
| Delta BFB0524HH | 216 → 216 Pa | **0 %** | 4.59 → 4.60 CFM | **0 %** | 15 % (generic shape too low in the middle; real curve is flatter to 0.073 m³/min, then near-linear) | 1.89 → 1.99 CFM | **−5 %** (low K −5 %, high K −2 %) |
| Sunon MF40202VX (axial) | 72 → 72 Pa | **0 %** | 10.8 → 10.8 CFM | **0 %** | 28 % (real stall saddle deeper: ~26-27 Pa at 4.5-6.5 CFM vs ~40-45 Pa estimated) | 1.16 → 1.14 CFM; heat sink medium 2.88 → 2.65 CFM | **+2 %**; **+9 %** (heat sink low K +16 %, high K +4 %) |
| Sunon MF50152VX-1L02C (owned), vs proxy-scaled | 189 → 191 Pa | **−1 %** | 4.80 → 4.80 CFM | **0 %** | 11 % (real curve sags in the middle) | 1.80 → 1.70 CFM | **+6 %** (low +6 %, high +5 %) |
| …same fan, if it matches the Sunon catalogue blower | 189 → 242 Pa | −22 % | 4.80 → 5.40 CFM | −11 % | 22 % | 1.80 → 1.91 CFM | −6 % |
| Creality stock 4020, vs CBM proxy | 390 → 191 Pa | **+104 %** | 6.40 → 5.31 CFM | **+20 %** | 109 % | 2.56 → 1.72 CFM | **+49 %** (low +48 %, high +48 %) |

**Summary.** For the three fans with real datasheets, the published end points were right, and only the generic shape was off. The shape error was 11-28 % of ΔPmax locally, but only **2-9 %** in delivered flow at the operating point.
- The **Delta** estimate was slightly pessimistic.
- The **Sunon blower** and **axial** estimates were slightly optimistic.
- The one large error is the **stock 4020**. Its shut-off pressure was never published, and the second, manufacturer-curve proxy halves it.

### 10.5 Does this change the ranking or the recommendation?

**Ranking (single fan, medium K):**
- **Before:** stock 4020 (2.56 CFM) > Delta (1.89) ≈ GDSTIME (1.86) > owned Sunon 5015 (1.80) ≫ 4020 axial (1.16).
- **After:** **Delta BFB0524HH (1.99)** > Sunon catalogue blower (1.91) > stock 4020 proxy (1.72) ≈ owned Sunon (1.70) ≫ axial (1.14).
- **Dual symmetric, shared area:** 2 × Delta 2.10 > 2 × stock-proxy 1.88 ≈ 2 × owned Sunon 1.84.
- The stock fan drops from first to joint third. With its 190-390 Pa bracket it could still be anywhere from equal to the owned Sunon up to best, but **no manufacturer-backed curve supports "highest pressure"** any more.

**Recommendation changes:**
1. **Hotend fan:** unchanged. Sunon MF40202VX-1000U-G99 on channel 2 (PB5, tach PB4). Its FG spec is now verified compatible. Digitized flow through the assumed heat sink is 2.0-3.4 CFM.
2. **Part cooling:** the preference flips from 2a to **2b**: two symmetric **24 V 5015 blowers**, one logical fan, each with its own 40-60 mm² outlet.
   - **Delta BFB0524HH** is the first choice. It has the best verified curve and ~17 % more flow than our Sunon at medium K. With separate outlets, two Deltas give ≈ 4.0 CFM.
   - Our Sunon is the second unit or the backup.
   - Option 2a (2 × Creality 4020 at 0.6 A) loses its main argument. Its only remaining advantage is being native 4-pin PWM.
   - Because both preferred blowers are **2-wire**, the open electrical item is now central: speed control needs PWM on PB6 or a small low-side MOSFET driven from channel 1. Probing channel 1 is the next hardware step.
3. **Shortlist:**
   - **Delta BFB0524HH × 2**: now #1, ~$10-15 each.
   - **Creality 4020 × 1**: only to measure the stock curve (was × 2-3).
   - CPAP kit: unchanged, conditional.
4. **CFD (for the coordinator):**
   - Switch finalists to `delta_BFB0524HH_digitized.csv` and `sunon_MF40202VX-1000U-G99_digitized.csv`.
   - For our Sunon blower, use `sunon_MF50152VX-1L02C-A99_proxy-scaled.csv`. Use `sunon_MF50151VX-1B00U-A99_digitized.csv` as the upper bound.
   - For the stock fan, run **both** `creality_K1_stock_4020_blower.csv` (390 Pa) and `creality_K1_stock_4020_blower_proxy-scaled.csv` (191 Pa) as bounds until it is measured.
   - The section 6 conclusion still holds: dual fans sharing one outlet area add only 5-15 % flow.

### 10.6 Nozzle-board fan channels: Pellcorp docs check

I searched pellcorp.github.io/creality-wiki (source cloned from github.com/pellcorp/creality-wiki) for nozzle-board, fan, PB6/PB8 and MOSFET content.
- It has **no nozzle-board schematic, no fan-output current rating, and nothing on whether PB6 switches high- or low-side**. The section 3 topology therefore stays INFERRED, and the 0.3 A / 0.1 A demonstrated loads stay the only limits. Probe the board before relying on more.
- One relevant fact (`rpi_faq.md`, `nozzle_wipe.md`): Pellcorp moved the part fan from `[fan_generic part]` to `[fan]` "to mitigate performance issues that were causing klipper to crash with a move queue overflow". `M106 P0` is not supported; plain `M106` addresses the part fan, and P1/P2 address chamber/auxiliary.
- Practical consequence: keep the part fan(s) as the single `[fan]` object. If a new fan object is added on `nozzle_mcu`, test it under a heavy print before trusting it.

## 11. Sunon.cz order options

**Shop survey (2026-11-01).** I crawled every DC category on https://www.sunon.cz/ (24 V, 12 V, 5 V, 48 V, miniature, new): 1813 product URLs, 581 of them in the 24 V category. The candidate product pages and every datasheet PDF used are saved in `scratchpad/ref/sunoncz/`.

- **Prices** are CZK including 21 % VAT. The price without VAT is in brackets.
- **Stock:** "Skladem (N ks)" means in stock. "Na dotaz" means on request: not stocked, lead time unknown.
- **Status labels:** specs are VERIFIED where I read them from the Sunon sheet. Price and stock are SECONDARY (shop page).

### 11.1 What the shop does and does not carry

1. **No 24 V blower smaller than 75 × 75 × 30 mm.** The only 24 V blowers are PF75302B1/B2/B3 (7530, 86-88 g), in A99/F99/G99/H99/Q99/S99 variants.
2. **Small blowers are 12 V only:**
   - MF50151Vx-1B00U and EF50151Bx-1B00U (5015)
   - MF50201Vx-1B00U (5020)
   - MF60151Vx-1B00U (6015)

   There are **no 40 × 40 or 45 × 45 blowers** at any voltage.
3. **No 24 V 3010 or 4010 axial.** 3010s are 12 V only (MF30101V1/V2, HA30101V3). The only 24 V 40 mm axials are 40 × 40 × 20 (MF40202Vx) and 40 × 40 × 28 (GF40282Bx, 58.5 dBA).
4. **Nothing from our 24 V MF50152VX blower family.** Every MF50152Vx in the shop is the 1000U **axial**.
5. **Shop parameter tables contain errors.** Use the Sunon sheets instead:
   - The MF40202VX-1000U-G99 page says "12 VDC, 40.7 dBA" and links the MF40201VX sheet.
   - The EF50151BX-1B00U-G99 page links the EF50151B2 sheet.
6. **Suffix key** (Sunon catalogue p.80):
   - A99: 2 wires
   - F99: + R-type locked-rotor alarm
   - G99: + **FG tach**
   - H99: + PWM
   - Q99: R + PWM
   - S99: **FG + PWM** (4 wires)

### 11.2 Candidates

| Part (sunon.cz) | Type | V | I rated / max | rpm | Q max | ΔP max | dBA | Wires | Mass | Stock | Price CZK | Curve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [MF50151VX-1B00U-**G99**](https://www.sunon.cz/ventilator-dc-blower-12v-50x50x15mm-mf50151vx-1b00u-g99/) | 5015 blower, Vapo/MagLev | 12 | 0.155 / 0.179 A | 6200 | 5.4 CFM | 0.97 inH2O (242 Pa) | 42.2 | 3 (FG) | 30 g | Na dotaz | **122.76** (101.45) | DIGITIZED (identical to -A99 to < 0.01 %) |
| [MF50151VX-1B00U-A99](https://www.sunon.cz/ventilator-dc-blower-12v-51-7x51-6x15mm-mf50151vx-1b00u-a99/) | same aero | 12 | same | 6200 | 5.4 | 0.97 | 42.2 | 2 | 30 g | Na dotaz | 133.65 (110.45) | `sunon_MF50151VX-1B00U-A99_digitized.csv` |
| [EF50151BX-1B00U-A99](https://www.sunon.cz/ventilator-dc-blower-12v-51-6x51-7x15mm-ef50151bx-1b00u-a99/) | 5015 blower, 2 ball | 12 | 0.150 A | 6200 | 5.4 | 0.97 | 45.8 | 2 | 31 g | **Skladem (100)** | 352.44 (291.27) | DIGITIZED (catalogue curve) |
| [EF50151BX-1B00U-G99](https://www.sunon.cz/ventilator-dc-blower-12v-51-7x51-6x15mm-ef50151bx-1b00u-g99/) | same, FG | 12 | 0.150 A | 6200 | 5.4 | 0.97 | 45.8 | 3 (FG) | 31 g | Na dotaz | 289.08 (238.91) | as above |
| [MF50201V1-1B00U-A99](https://www.sunon.cz/ventilator-dc-blower-12v-50x50x20mm-mf50201v1-1b00u-a99/) / [-F99](https://www.sunon.cz/ventilator-dc-blower-12v-50x50x20mm-mf50201v1-1b00u-f99/) | 5020 blower | 12 | 0.124 A | 5300 | 5.8 | 0.66 (165 Pa) | 34.8 | 2 / 3 (R) | 34 g | Skladem (4320 / 2283) | 160.38 / 114.84 | DIGITIZED |
| [MF60151VX-1B00U-A99](https://www.sunon.cz/ventilator-dc-blower-12v-60x60x15mm-mf60151vx-1b00u-a99/) / [-G99](https://www.sunon.cz/ventilator-dc-blower-12v-60x60x15mm-mf60151vx-1b00u-g99/) | 6015 blower | 12 | 0.130 A | 4500 | 6.2 | 0.71 (177 Pa) | 37.7 | 2 / 3 (FG) | 36 g | Skladem (13) / Na dotaz | 200.97 / 127.71 | DIGITIZED |
| [PF75302B1-1B00U-**S99**](https://www.sunon.cz/ventilator-dc-blower-24v-75x75x30mm-pf75302b1-1b00u-s99/) | 7530 blower, ball | **24** | 0.115 / 0.133 A | 3400 | 15.5 | 0.57 (142 Pa) | 42.0 | **4 (FG + PWM)** | 88 g | Na dotaz | 285.12 (235.64) | DIGITIZED |
| [MF30101V1-1000U-G99](https://www.sunon.cz/ventilator-dc-axialni-12v-30x30x10mm-mf30101v1-1000u-g99/) (hotend, optional) | 3010 axial, Vapo | 12 | 55 mA | 11 500 | 9.3 m³/h (5.5 CFM) | 6.35 mmH2O (62 Pa) | 23 | 3 (FG) | 8 g | Skladem (146) | 195.03 (161.18) | specs SECONDARY (shop); not digitized |
| [MF40202V1-1000U-G99](https://www.sunon.cz/ventilator-dc-axialni-24v-40x40x20mm-mf40202v1-1000u-g99/) | 4020 axial (slower sibling of ours) | 24 | 32 mA | 7000 | 15.04 m³/h | 5.59 mmH2O | 25.5 | 3 (FG) | 30 g | Skladem (6294) | 126.72 | not needed |

Where the specs come from:
- MF50151VX: Sunon sheets D05073850G-00 and `mf50151vx-1b00u-g99.pdf`.
- EF50151BX: Sunon catalogue 240-A p.83.
- MF50201V1, MF60151VX and PF75302B1: Sunon sheets linked from the shop.

The PF75302B1-S99 sheet also gives its PWM input: 22-28 kHz (25 kHz typ.), VH 2.1-5 V, minimum start duty 10 %, 50 % duty gives 2200 rpm, and an unconnected input runs at full speed. Its operating range is 20.4-27.6 V.

### 11.3 Operating points (PRE-CFD, same ducts as section 6; `operating_point.py --sunoncz`)

Single fan, whole outlet area. Each cell is Q in CFM / outlet velocity. The last two columns relate mass to flow and to the X input-shaper frequency (DD-01: about 1 % per 9 g).

| Fan | Medium K | High K | Mass | CFM/g at medium K | X-shaper cost per fan |
|---|---|---|---|---|---|
| Stock 4020, upper bound (390 Pa, ESTIMATED) | 2.56 / 15.1 m/s | 1.38 | ? | — | — |
| Delta BFB0524HH (not at sunon.cz) | **1.99** / 11.7 | **1.04** | 28 g | **0.071** | 3.1 % |
| **Sunon EF50151BX-1B00U** | **1.95** / 11.5 | **1.04** | 31 g | 0.063 | 3.4 % |
| **Sunon MF50151VX-1B00U** | **1.91** / 11.3 | **1.02** | 30 g | 0.064 | 3.3 % |
| Sunon MF60151VX-1B00U (6015) | 1.79 / 10.6 | 0.93 | 36 g | 0.050 | 4.0 % |
| Stock 4020, lower bound (CBM proxy) | 1.72 / 10.1 | 0.93 | ? | — | — |
| Sunon MF50152VX-1L02C (owned, proxy) | 1.70 / 10.0 | 0.91 | 28.4 g | 0.060 | 3.2 % |
| Sunon PF75302B1 (7530) on the toolhead | 1.70 / 10.0 | 0.86 | 88 g | 0.019 | 9.8 % |
| Sunon MF50201V1-1B00U (5020) | 1.55 / 9.2 | 0.85 | 34 g | 0.046 | 3.8 % |

**Dual symmetric fans, each with its own outlet (medium / high K):**

| Pair | Medium K | High K | Mass |
|---|---|---|---|
| 2 × Delta | 3.98 | 2.08 | 56 g |
| 2 × EF50151BX | 3.91 | 2.07 | 62 g |
| 2 × MF50151VX | 3.83 | 2.05 | 60 g |
| 2 × MF60151VX | 3.59 | 1.86 | 72 g |
| 2 × owned MF50152VX | 3.40 | 1.82 | 57 g |
| 2 × MF50201V1 | 3.11 | 1.70 | 68 g |

**PF75302B1 off the toolhead,** through a 1.5 m × 15 mm hose: 1.93 / 1.39 / 0.82 CFM (low / medium / high K). That is less than one 5015 mounted on the toolhead.

**Ranking (flow at medium-high K, then mass):**
1. Delta BFB0524HH (reference, not sold here)
2. **EF50151BX ≈ MF50151VX**, tied within the ±1-2 % digitizing and curve tolerance; MF50151VX is 1 g lighter, 3.6 dB quieter and much cheaper
3. MF60151VX
4. owned MF50152VX ≈ stock lower bound
5. MF50201V1
6. PF75302B1

The two Sunon 5015s deliver **+12-15 % flow over the blower we own** and come within 2-4 % of the Delta.

### 11.4 Electrical: can the part-fan channel control their speed?

- **No toolhead-sized 24 V 4-wire PWM blower exists at sunon.cz.** The only 24 V PWM blower is **PF75302B1-1B00U-S99**, flagged here explicitly. It is not usable:
  - It is 75 × 75 × 30 mm and 88 g: 9.8 % of X-shaper frequency per fan.
  - Its PWM input is specified at 22-28 kHz, while channel 1 runs 100 Hz software PWM (`cycle_time 0.010`). Hardware PWM on PB8 is unverified.
  - Off the toolhead it delivers less flow than a single 5015 (11.3).
- **Every toolhead-sized candidate is 12 V, with 2 wires (A99) or 3 wires (G99 = FG tach).** None has a PWM wire. Using one needs:
  1. A **24 → 12 V buck** on the toolhead. Two MF50151VX at max current draw 0.36 A at 12 V, about 0.2 A at 24 V, which is inside the stock channel's demonstrated 0.3 A. Module mass is ~3-5 g, ESTIMATED.
  2. The **same speed-control add-on that a 2-wire 24 V Delta needs:** a logic-level low-side MOSFET switching the fans' negative leg.
     - Its gate is driven by the channel-1 PWM-wire signal: PB8's open-collector stage plus a pull-up on the add-on board.
     - The buck is fed from the PB6-switched supply.
     - This keeps Klipper's single `[fan]` (M106) and the MPC model unchanged. It is INFERRED and must be checked against the channel-1 probe measurement (section 9, item 3).
  3. The **G99 FG output** is open collector, so it can go to PB3 (`tachometer_pin: ^nozzle_mcu:PB3`, 2 pulses per revolution) for one of the pair.
- **Compared with the Delta:** the Sunon option costs one extra buck and ~2 g per fan, and gains a FG tach and 3 dB lower noise. Aerodynamically the two are equivalent.

### 11.5 Recommended sunon.cz order

| # | Part | Qty | Why | Price |
|---|---|---|---|---|
| 1 | **MF50151VX-1B00U-G99** | **3** | Best flow per gram at sunon.cz. Quietest of the strong 5015s. FG tach for PB3. Two for the dual-blower configuration, one to bench-measure (shut-off pressure, free flow, FG) and keep as a spare | 3 × 122.76 = **368 CZK** incl. VAT (on request) |
| 1-alt | EF50151BX-1B00U-A99 (in stock) | 3 | Only if the on-request lead time is unacceptable. Same flow (+2 %), ball bearing, 45.8 dBA, 2 wires, +1 g | 3 × 352.44 = 1057 CZK |
| 2 (optional) | MF30101V1-1000U-G99 | 1 | Only if the 12 V rail is built anyway and a documented 3010 hotend fan is wanted (DD-04 keeps the 3010 size). There is **no 24 V 3010 at sunon.cz**; otherwise keep the stock 24 V Creality 3010 | 195.03 CZK (in stock) |

**Do not order:**
- PF75302B1, any suffix: too heavy, and its PWM is out of spec for the board.
- MF50201V1 (5020): −19 % flow and +4 g against MF50151VX.
- MF60151VX (6015): −6 % flow and +6 g.
- MF40202V1: we already own the faster MF40202VX.

The 24→12 V buck and the MOSFET add-on are not sold at sunon.cz.

**If ordering outside sunon.cz is acceptable,** 2 × Delta BFB0524HH (24 V) is still marginally the better pick: +4 % flow, −2 g per fan, and no buck.

### 11.6 For the CFD agent

- **Add** `sunon_MF50151VX-1B00U-A99_digitized.csv`. It already exists from section 10, and the -G99 curve is identical, so it covers the recommended -G99.
- **Optionally add** `sunon_EF50151BX-1B00U-A99_digitized.csv`. It is within 2 % of the MF50151VX, so only needed if the in-stock alternative is chosen.
- `sunon_MF50201V1-1B00U-F99_digitized.csv`, `sunon_MF60151VX-1B00U-G99_digitized.csv` and `sunon_PF75302B1-1B00U-S99_digitized.csv` are written for completeness. **They are not finalists.**
