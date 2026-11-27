# Modbus register map

This page lists the Modbus registers of the DRS-240-12 that are useful for monitoring, the meaning of the status bits, and what happened when each setting was written on the tested unit. The official register list is in section 5.4 of the Mean Well manual. The "tested unit" columns here are measurements from one DRS-240-12.

> [!WARNING]
> Writing 0 to register 0 (`OPERATION`) switches the output off. On the tested unit it stayed off until the unit was power-cycled by hand. By the manual, writing 1 switches it on again, but that wasn't tested. If your network runs from the DRS, you can't undo a 0 remotely. The [write script](state-of-charge-and-alerts.md#the-register-write-script) in the package refuses this register.

## Link settings

| Setting | Value | Source |
| --- | --- | --- |
| Protocol | Modbus RTU over RS-485 | Section 5.4.1.1 |
| Serial format | 115200 baud, 8 data bits, no parity, 1 stop bit, no flow control | Section 5.4.1.1 |
| Slave ID | 128 + device address (0 to 3). 131 (0x83) with the CN12 address pins open | Section 5.4.1.4, confirmed on the tested unit |
| Minimum time between requests | 50 ms | Section 5.4.1.2 |
| Maximum response time | 12.5 ms | Section 5.4.1.2 |
| Byte order | High byte first | Section 5.4.1.1 |

The manual lists three function codes (section 5.4.1.5):

| Code | Function | Used for |
| --- | --- | --- |
| 0x03 | Read holding registers | Settings and status words |
| 0x04 | Read input registers | Measurements |
| 0x06 | Write single register | Settings |

Other function codes, including 0x10 (write multiple registers), aren't listed and weren't tried.

## Measurements

Read with function 0x04. All values are 16-bit. Multiply the raw value by the scale.

| Address | Name | Scale | Tolerance (12 V model) | Notes |
| --- | --- | --- | --- | --- |
| 80 (0x0050) | `READ_VIN` | 0.1 V | ±5 V | AC input voltage |
| 96 (0x0060) | `READ_VOUT` | 0.01 V | ±0.12 V | Output voltage |
| 97 (0x0061) | `READ_IOUT` | 0.01 A | ±0.2 A | Load current |
| 98 (0x0062) | `READ_TEMPERATURE_1` | 0.1°C, signed | ±5°C | Internal temperature |
| 211 (0x00D3) | `READ_VBAT` | 0.01 V | ±0.12 V | Battery voltage |
| 212 (0x00D4) | `READ_IBAT` | 0.01 A, signed | ±0.2 A | Battery current. Negative means discharging |
| 213 (0x00D5) | `READ_BAT_TEMPERATURE` | 0.1°C, signed | ±5°C | Reads a fixed 25.0°C without the NTC sensor |

The tolerances are from section 5.4.4. The ±0.2 A on the battery current matters: in the rest state the tested unit reads 0.01 A to 0.04 A, and that reading can't tell you the true idle current.

The manual defines the scales through the `SCALING_FACTOR` registers (192 to 194). The scales above were checked against readings on the tested unit instead: output and battery voltage agree within 0.01 V when they should, and the timeouts read their documented defaults.

## Status words

Read with function 0x03.

### FAULT_STATUS, address 64 (0x0040)

| Bit | Value | Name | Meaning |
| --- | --- | --- | --- |
| 0 | 1 | `FAN_FAIL` | Not supported |
| 1 | 2 | `OTP` | Internal over temperature |
| 2 | 4 | `OVP` | Output over-voltage |
| 3 | 8 | `OLP` | Output overload |
| 4 | 16 | `SHORT` | Short circuit |
| 5 | 32 | `AC_FAIL` | AC power missing or out of range |
| 6 | 64 | `OP_OFF` | "DC turned off" in the manual. See the note below |
| 7 | 128 | `HI_TEMP` | High ambient temperature |

`OP_OFF` isn't the state of the load output. On the tested unit it reads 1 whenever the unit runs on battery, with the output live. Don't treat it as a fault.

### CHG_STATUS, address 184 (0x00B8)

| Bit | Value | Name | Meaning |
| --- | --- | --- | --- |
| 0 | 1 | `FULLM` | Charge complete |
| 1 | 2 | `CCM` | Constant-current stage |
| 2 | 4 | `CVM` | Constant-voltage stage |
| 3 | 8 | `FVM` | Float stage |
| 7 | 128 | `DCM` | Battery discharging |
| 10 | 1024 | `NTCER` | NTC sensor circuit shorted |
| 11 | 2048 | `BTNC` | No battery detected |
| 12 | 4096 | `BUFFTOF` | Buffering timeout |
| 13 | 8192 | `CCTOF` | CC stage timeout |
| 14 | 16384 | `CVTOF` | CV stage timeout |
| 15 | 32768 | `FVTOF` | Float stage timeout |

> [!IMPORTANT]
> `CCM` shows the stage the charger thinks it's in. It doesn't prove that current flows into the battery. On the tested unit `CHG_STATUS` read 2 for hours while the battery was discharging. Always check `READ_IBAT`.

### SYSTEM_STATUS, address 195 (0x00C3)

| Bit | Value | Name | Meaning |
| --- | --- | --- | --- |
| 1 | 2 | `DC_OK` | Output voltage normal |
| 5 | 32 | `INITIAL_STATE` | Read 0 in every state on the tested unit. Not useful |
| 6 | 64 | `EEPER` | EEPROM access error |
| 7 | 128 | `CHG/UPS` | 0 = charging mode, 1 = UPS mode (on battery) |

Bits 0, 2, 3, and 4 are marked as not supported in the manual.

The UPS-mode bit drops back to 0 at the battery cut-off. If you use it to detect that AC power has returned, you get a false "AC is back" at the moment the battery is empty. Use `AC_FAIL` instead.

### Typical values on the tested unit

| State | `FAULT_STATUS` | `CHG_STATUS` | `SYSTEM_STATUS` |
| --- | --- | --- | --- |
| On AC, charging at constant current | 0 | 2 | 2 |
| On AC, charging at constant voltage | 0 | 4 | 2 |
| On AC, rest state after a 2-stage charge | 0 | 1 | 2 |
| On AC, float stage (3-stage mode) | 0 | 9 | 2 |
| On AC, float stage timed out | 0 | 32768 | 2 |
| On AC, no battery connected | 0 | 2048 | 2 |
| On battery | 96 | 128 | 130 |
| On battery, default curve, after a completed charge | 96 | 129 | 130 |
| After the cut-off, with the force-start pins linked | `AC_FAIL` set | 0 | 0 |
| After `OPERATION` = 0 | 64 | 0 | `DC_OK` clear |

Without the force-start link, the unit doesn't answer at all after the cut-off.

## Settings

Read with function 0x03, write with function 0x06. Ranges and defaults are for the 12 V model, from section 5.4.4.

The last column is the important one. **A register that accepts a write and reads the new value back hasn't necessarily changed anything.**

| Address | Name | Range | Manual default | Tested unit when new | Does a write take effect? |
| --- | --- | --- | --- | --- | --- |
| 0 (0x0000) | `OPERATION` | 0 = off, 1 = on | 1 | 1 | **Yes.** 0 switches the output and the charger off |
| 32 (0x0020) | `VOUT_SET` | 10–14 V, scale 0.01 | 12 V | 12.00 V | **No.** 13.80 V was written and read back. The output stayed at 12.00 V, also after a power cycle |
| 176 (0x00B0) | `CURVE_CC` | 4–20 A, scale 0.01 | 20 A | 15.40 A | **No.** With 6.00 A in the register before the charge began, the knob took the current to 7.07 A. A write during the charge changed nothing either |
| 177 (0x00B1) | `CURVE_CV` | 9–15 V, scale 0.01 | 14.4 V | 14.40 V | Not tested. With a DIP preset the register keeps its value and doesn't show the preset voltage |
| 178 (0x00B2) | `CURVE_FV` | 9 V to `CURVE_CV`, scale 0.01 | 13.8 V | 13.80 V | **No effect seen.** The float stage never held this voltage |
| 179 (0x00B3) | `CURVE_TC` | 0.4–2 A, scale 0.01 | 2 A | 1.54 A | **No.** 0.40 A was written. The charge still ended at 1.53 A |
| 180 (0x00B4) | `CURVE_CONFIG` | Bit field | | 132 | Partly. The temperature compensation bits can be written. The stage and preset bits follow the DIP switches |
| 181 (0x00B5) | `CURVE_CC_TIMEOUT` | 60–64800 min | 600 | 600 | Unknown. Set to 900, never reached |
| 182 (0x00B6) | `CURVE_CV_TIMEOUT` | 60–64800 min | 600 | 600 | Unknown |
| 183 (0x00B7) | `CURVE_FV_TIMEOUT` | 60–64800 min | 600 | 600 | **Not for a running stage.** 60 was written. The float stage was still running 10 hours later. The default of 600 did end a float stage |
| 196 (0x00C4) | `SYSTEM_CONFIG` | Bit field | | 2 | Writing 3 is accepted and reads back as 2 |
| 208 (0x00D0) | `BAT_UVP_SET` | 9.6–12 V, scale 0.01 | 10.44 V | 10.50 V | **Yes.** Set to 11.20 V, the cut-offs came at 11.20–11.23 V |
| 209 (0x00D1) | `Force_BAT_UVP_SET` | 8.4–12 V, scale 0.01 | 8.4 V | 10.00 V | Not tested separately. It's set to the same value as register 208 |
| 210 (0x00D2) | `UPS_CONFIG` | Bit field | 9 | 9 | Reads back. Turning the life test or the periodic wake-up off made no visible difference |
| 224 (0x00E0) | `AC_Fail_LL_SET` | 82–120 V, scale 0.1 | 82 V | 84.0 V | Not tested |
| 225 (0x00E1) | `AC_Fail_HL_SET` | 132–182 V, scale 0.1 | 171.6 V | 171.6 V | Reads back. The effect wasn't tested |
| 226 (0x00E2) | `AC_OK_LL_SET` | 87–125 V, scale 0.1 | 87 V | 89.0 V | Not tested |
| 227 (0x00E3) | `AC_OK_HL_SET` | 137–187 V, scale 0.1 | 182.6 V | 182.6 V | Reads back. The effect wasn't tested |
| 228 (0x00E4) | `TIME_BUFFERING` | 60–64800 min | 600 | 600 | Inactive unless `UPS_CONFIG` bit 2 is set |
| 232 (0x00E8) | `UPS_Delay_Time` | 60–300 s | 60 | 60 | Inactive unless `UPS_CONFIG` bit 4 is set |
| 233 (0x00E9) | `UPS_Shutdown_Time` | 0–60 s | 15 | 15 | Inactive unless `UPS_CONFIG` bit 5 is set |

Notes:

- The tested unit differed from the manual defaults in several registers when new: `CURVE_CC` (15.40 A, which is the maximum charge current in the specification), `CURVE_TC` (1.54 A, 10% of 15.4 A), both low-line AC thresholds, and both cut-off registers.
- The manual gives two different defaults for the force-start cut-off: 8.4 V in section 5.4.4 and 10 V ± 0.3 V in section 5.7.3.
- For 230 V power, the high-line pair of AC thresholds (225 and 227) applies. The AC fail threshold is where the unit switches to the battery. The tested unit runs with lower values, 150.0 V and 165.0 V. The factory values are the right starting point.
- On Modbus the delay and shutdown times are at 0x00E8 and 0x00E9. On CANBus they're one address lower (note in section 5.4.4).
- The identification registers (manufacturer, model, firmware revision, serial number, at 0x0080 to 0x0099) are described in the manual and weren't read on the tested unit.

### CURVE_CONFIG, address 180 (0x00B4)

| Bits | Value | Name | Meaning |
| --- | --- | --- | --- |
| 0–1 | 1, 2 | `CUVS` | Curve: 0 = default, 1 = gel, 2 = flooded, 3 = AGM. Follows DIP 2 and 3 |
| 2–3 | 4, 8 | `TCS` | Temperature compensation: 0 = off, 1 = –3, 2 = –4, 3 = –5 mV/°C per cell. Default 1 |
| 6 | 64 | `STGS` | 0 = 3-stage, 1 = 2-stage. Follows DIP 1. Setting it over Modbus is marked not supported |
| 7 | 128 | `CUVE` | Always 1 |
| 8 | 256 | `CCTOE` | CC timeout indication enable |
| 9 | 512 | `CVTOE` | CV timeout indication enable |
| 10 | 1024 | `FVTOE` | Float timeout indication enable |

Values read on the tested unit with temperature compensation off:

| DIP setting | 3-stage (DIP 1 OFF) | 2-stage (DIP 1 ON) |
| --- | --- | --- |
| Default curve | 128 | 192 |
| Gel preset | 129 | 193 |
| Flooded preset | 130 | 194 |

The factory value, 132, is the default curve in 3-stage mode with –3 mV/°C per cell.

### SYSTEM_CONFIG, address 196 (0x00C4)

| Bits | Name | Meaning |
| --- | --- | --- |
| 0 | `MOD_CTRL` | Modbus control of output voltage, current, and operation. Marked not supported |
| 1–2 | `OPERATION_INIT` | Output state at power-up: 0 = off, 1 = on, 2 = the last value |

The tested unit reads 2: `OPERATION_INIT` = 1, the output switches on by itself at power-up. That's what brings the output back after a battery cut-off.

The current manual (2026.03) also describes bits in the high byte that control how settings are saved to the EEPROM: at once (the default), after a delay, or not at all. It isn't known whether the firmware of the tested unit has them.

### UPS_CONFIG, address 210 (0x00D2)

| Bit | Value | Name | Meaning | Default |
| --- | --- | --- | --- | --- |
| 0 | 1 | `Life_Test_EN` | Periodic battery test | On |
| 1 | 2 | `UPS_OFF_EN` | Shutdown by the button in force-start mode | Off |
| 2 | 4 | `Time_Buff_EN` | Limits the time on battery to `TIME_BUFFERING` | Off |
| 3 | 8 | `Wake_Up_EN` | Periodic wake-up of the battery | On |
| 4 | 16 | `UPS_Delay_EN` | Delayed shutdown on battery | Off |
| 5 | 32 | `UPS_Shutdown_EN` | Timed restart on battery | Off |

The tested unit runs with 8: wake-up on, everything else off.

> [!WARNING]
> Bits 2, 4, and 5 make the unit switch the output off while running on battery. Leave them at 0 unless you want exactly that.

## Writing registers safely

- **Settings are stored in the EEPROM.** The manual doesn't state how many writes the memory survives. Write a register once, by hand. Don't write registers from automations that run on a schedule.
- **Read it back, then check the behavior.** A successful read-back proves only that the unit stored the number.
- **Never write `OPERATION`, `VOUT_SET`, or `SYSTEM_CONFIG` on a unit you can't reach by hand.** In the tests, one `OPERATION` = 0 switched the output off, and the output, with the router on it, stayed off until the unit was power-cycled by hand.
- **A factory reset restores the settings.** Five short presses of the Battery Start button reset the operation, output voltage, charge curve, and AC threshold registers (section 5.10).

## Worked examples

Frames are in hexadecimal, for slave ID 131 (0x83). The last two bytes are the CRC.

Read the battery voltage (function 0x04, address 0x00D3, one register):

```text
Request:   83 04 00 D3 00 01 DE 11
Response:  83 04 02 05 5A 42 45      0x055A = 1370, times 0.01 = 13.70 V
```

Read the charge status (function 0x03, address 0x00B8):

```text
Request:   83 03 00 B8 00 01 1A 0D
Response:  83 03 02 00 01 01 9A      1 = FULLM, the rest state
```

Write the battery cut-off, 11.20 V (function 0x06, address 0x00D0, value 1120 = 0x0460):

```text
Request:   83 06 00 D0 04 60 94 F9
```

The example frames were calculated, not captured from the tested unit. In Home Assistant you don't build frames yourself: the package reads the registers, and `script.drs_write_register` writes them.

## Other models

Nothing here was tested on the 24 V, 36 V, and 48 V models or on the DRS-480. According to the manual, the register addresses are the same and the ranges, defaults, and tolerances differ (section 5.4.4). The voltage thresholds in the Home Assistant package are for a 12 V system.

Next: [Home Assistant setup](home-assistant-setup.md)
