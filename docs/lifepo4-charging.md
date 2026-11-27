# LiFePO4 charging

The DRS-240 manual lists lithium batteries as supported, but with the factory settings the tested unit slowly drained a LiFePO4 battery while AC power was present. This page explains why, lists what was tried, and describes the configuration that worked, including the two times it didn't.

> [!IMPORTANT]
> **The short version, for a 12 V LiFePO4 battery:**
>
> 1. DIP 1 ON, DIP 2 OFF, DIP 3 ON: 2-stage charging with the flooded preset, 14.2 V, no float stage.
> 2. Leave CN12 pins 7 and 8 open.
> 3. Install the Home Assistant package, so that you can see the battery current and get the alerts.
> 4. Set the charge current with the knob.
> 5. Raise the battery cut-off above the minimum voltage of your loads. The tested unit uses 11.20 V.
> 6. Add a way to interrupt AC power remotely.
>
> This is what worked on one unit with one battery. It isn't a fix from Mean Well, and step 6 is there because it doesn't work every time.

## The problem

The battery is connected to the DRS output all the time. That's what makes the switch-over instant. It also means that the higher voltage wins: when the AC side of the unit delivers less than the battery voltage, the battery supplies the load, even though AC power is present.

On the tested unit that happened in the float stage, and whenever the unit reported a charge stage without actually charging. A likely explanation, not confirmed by Mean Well: in those states the AC side regulates to the rated 12.0 V. That's the output voltage measured after a float timeout, when the unit had isolated the battery. A LiFePO4 battery stays well above 12.0 V until it's nearly empty: the tested battery still read 12.80 V under load at 34%.

There's one state where this doesn't happen: the rest state after a 2-stage charge. There the unit isolates the battery and feeds the loads from AC at the boost voltage. The configuration on this page is built around that state.

The problem showed up in two forms.

**Float discharge.** In 3-stage mode, the float stage is supposed to hold the battery at 13.8 V. On the tested unit it didn't: with the float flag set, the battery fed the whole load. In the first night it delivered 1.45 A for 10 hours, about 9 Ah, and the state of charge fell from 100% to 82%. When the float timeout ended the stage, the unit isolated the battery and did not recharge it.

**"CC but discharging".** After a restart of the DRS, and after some power outages, the unit reported the constant-current stage (`CHG_STATUS` = 2, orange LED), but no current flowed into the battery. The output stayed equal to the battery voltage, and the battery fed the load at the load current. In the early tests this lasted from 10 minutes to more than 8 hours.

A likely reason, also not confirmed by Mean Well: the unit decides whether to charge from the battery voltage, with thresholds that fit lead-acid batteries. In the tests the battery sat at 13.15 V for hours while a quarter of its charge was already gone. By its voltage it looked full.

The lesson for monitoring: **the charge stage doesn't tell you whether the battery is charging. The battery current does.**

## What the manual says

| Topic | Manual | Where |
| --- | --- | --- |
| Battery types | Lead-acid and lithium batteries. One DIP preset is named "AGM and LiFePO4": 14.6 V boost, 14.0 V float | Sections 2.2 and 5.3.4.1 |
| End of a 2-stage charge | The charger output switches off, the load output stays on | Section 5.3.1 |
| Restart after a 2-stage charge | When the battery voltage drops to 80% of the boost voltage | Relay status table in section 5.5 |
| End of a 3-stage charge | The charger enters the float stage | Section 5.3.2 |
| No battery detected | Charging stops. When a battery is detected again, it's charged | Relay status table in section 5.5 |
| Charge timeout | Charging stops, and doesn't resume without a restart | Relay status table in section 5.5 |
| AC power returns in battery-start or force-start mode | The unit switches to AC and recharges the battery | Sections 5.6.4 and 5.7.4 |
| Setting the output voltage over Modbus | Not supported | Section 5.4.1.6, `SYSTEM_CONFIG` bit 0 |
| SBP-001 programmer | CANBus models only | Section 5.3.4.3 |

80% of the boost voltage is 11.52 V on the default curve, 11.36 V with the flooded preset, 11.20 V with the gel preset, and 11.68 V with the AGM and LiFePO4 preset. A lead-acid battery passes those voltages well before it's empty. A LiFePO4 battery reaches them only in the last few percent.

## What was measured

All measurements are from one DRS-240-12 with a 12.8 V, 50 Ah LiFePO4 battery. The bench load was 0.8 A to 1.9 A until October 23, 2026, and about 2.6 A after that.

| Date | Setup | Event | Result |
| --- | --- | --- | --- |
| 2026-10-13 | 3-stage, default curve | AC returned after a deep discharge (battery at 10.78 V) | Charge started at once |
| 2026-10-13 | 3-stage, default curve | Float stage, 10 hours | Battery fed the load at –1.45 A, about 9 Ah. At the float timeout: battery isolated, output 12.00 V, no recharge |
| 2026-10-14 | 3-stage | Full power cycle of the DRS | "CC but discharging" for 80 minutes, until the next change |
| 2026-10-14 | 2-stage, default curve | End of charge | Rest state: battery current 0.03 A, output 14.38 V from AC |
| 2026-10-14 | 2-stage, default curve | 7-minute outage from the rest state | "CC but discharging". No charge in the next 8 hours, through two power cycles, with the battery settling at 13.15 V |
| 2026-10-14 | 3-stage | Battery connection interrupted for a moment | The unit reported "no battery" for 5 seconds, then charged at 6.0 A |
| 2026-10-15 | 2-stage, default curve | 8.5-minute outage from the rest state | "CC but discharging", no charge in the next 15 minutes |
| 2026-10-15 | 3-stage, life test off | Float stage overnight | Battery fed the load again. The life test isn't the cause |
| 2026-10-15 | 3-stage, flooded and gel presets | Float stage | Same drain, –1.5 A, on both presets |
| 2026-10-16 | 2-stage, flooded preset | Rest overnight, 9.5 hours | Battery current 0.01–0.02 A, battery 13.81 V falling to 13.76 V, output 14.19 V. No drain |
| 2026-10-16 | 2-stage, flooded preset | 45-second outage from rest | "CC but discharging" |
| 2026-10-16 | same | A second AC interruption of 5 seconds | Charge started at once, then rest again |
| 2026-10-20 and 2026-10-21 | same, CN12 pins 7 and 8 linked | Outages of 51 seconds, 80 minutes, and 90 seconds from rest | Charge started at once, 3 of 3 |
| 2026-10-21 | same, link removed | 80-second outage from rest | "CC but discharging" |
| 2026-10-26 | same, no link, load 2.6 A | 11 outages from rest: 5 seconds to 15 minutes | Charge started at once, 11 of 11 |
| 2026-10-27 | same | Discharge to the cut-off, AC back after 20 minutes | Charge at 6.11 A at once |
| 2026-10-27 | same | Full restart: AC off, fuse out, fuse in, AC on | Charge at 6.12 A after 22 seconds |
| 2026-10-28 | same | Rest for 12 hours | Battery current 0.02–0.04 A, battery flat at 13.81 V. No drain, no restart of the charge |
| Two weeks on site | same, load 1.5–2.3 A | 69 outages followed by at least 2 minutes of AC | Charge started by itself after 67. Twice the unit stayed in "CC but discharging" |

## What was tried and why it failed

| Attempt | Result |
| --- | --- |
| Raise the output voltage to 13.8 V with `VOUT_SET`, so that AC holds the output above the battery | The register reads back 13.80 V. The output stays at 12.00 V, also after a power cycle |
| Limit the current or extend the charge with `CURVE_CC` and `CURVE_TC` | Both are ignored |
| 3-stage charging on the default curve, the flooded preset, and the gel preset | The float stage drains the battery on all three |
| Turn the battery life test off | No change |
| Shorten the float stage with `CURVE_FV_TIMEOUT` | A value of 60 minutes was written and read back. The running float stage was still going 10 hours later |
| Restart the unit remotely with `OPERATION` = 0, then 1 | The 0 switched the output off, and it took a power cycle by hand to get it back. No charge afterward. Never do this remotely |
| Wait for the battery voltage to fall | No charge after 3 hours at 13.15 V |
| SBP-001 programmer | Only for the CANBus version |
| Link CN12 pins 7 and 8 (force start) | Recharged after every outage, 3 of 3. But after a battery cut-off, the unit stopped switching to the battery: six outages in a row dropped the output, until the battery fuse was pulled and put back. And after a start from the battery, even interrupting AC power didn't start a charge |
| A relay in the battery line, to make the unit detect the battery again | Should work, because a battery that's detected again is charged. Not built: it puts one more part that can fail into the battery line |
| AGM and LiFePO4 preset, 14.6 V | Not tested. With the +2% tolerance it can reach 14.89 V, above the 14.6 V maximum of the tested battery |

## The configuration that worked

On the unit, with everything switched off:

1. Make sure the DRS has no power: AC off, battery fuse out.
2. Set DIP 1 to ON, DIP 2 to OFF, and DIP 3 to ON. That's 2-stage charging with the flooded preset: 14.2 V boost voltage and no float stage. The switch body is marked `ON` on one side.
3. Check that CN12 pins 7 and 8 are open.
4. Turn the charge current knob to its lowest setting, against the arrow that points to the plus sign. You set the real value later.
5. Put the fuse in and switch AC power on.

Then, with Home Assistant:

1. Install the [package](home-assistant-setup.md). You need it for the next two steps, and its alerts watch the charge from then on.
2. [Set the charge current](#set-the-charge-current) with the knob.
3. [Set the battery cut-off](#set-the-battery-cut-off).
4. Add a [smart plug or relay](hardware-and-wiring.md#a-smart-plug-or-relay-on-the-ac-input) to the AC input.

In Home Assistant, `sensor.drs_active_curve` then reads "2-stage, flooded preset: boost 14.2 V, no float". `CURVE_CONFIG` should read 198 on a unit with factory settings: 128, plus 64 for 2-stage, plus 2 for the flooded preset, plus 4 for the factory temperature compensation setting. The tested unit reads 194, because its temperature compensation was switched off earlier. The 198 is calculated from the bit field, not observed.

Why the flooded preset fits the tested battery:

- Its maker specifies a charge voltage of 14.4 V and a maximum of 14.6 V. With the +2% tolerance the preset can reach 14.48 V, still below the maximum.
- Its BMS balances the cells from 3.55 V per cell, which is 14.2 V for the battery.
- The tested unit measured 14.09 V to 14.20 V at the battery in the constant-voltage stage.

Check the same three points for your battery. See the [checklist](#checklist-for-your-battery).

The tested unit also differs from the factory state in a few registers that you don't need to copy: the life test is off (`UPS_CONFIG` = 8), temperature compensation is off (`CURVE_CONFIG` written as 128), the CC timeout is 900 minutes, the float timeout still holds 60 minutes from an early experiment, and the AC thresholds are lower. None of these made a visible difference in the tests. The full list is in [Match the settings reference](home-assistant-setup.md#7-match-the-settings-reference).

One of them can matter for a bigger battery. The CC stage has a timeout, 600 minutes by default, and by the manual the unit stops charging when it's reached. A full charge has to fit: capacity divided by charge current, in hours, should stay well below 10. The tested 50 Ah battery needs about 8.3 hours of charging at 6.1 A. That fits, but not by much, and the tested unit runs with the timeout raised to 900 minutes. To raise it, write register 181 with the time in minutes, the same way as the cut-off below:

```yaml
action: script.drs_write_register
data:
  address: 181   # CURVE_CC_TIMEOUT
  value: 900     # minutes
```

The script accepts up to 1440 minutes. If you change the timeout, change `cc_timeout` in the [settings reference](home-assistant-setup.md#7-match-the-settings-reference) too. The package also raises a fault alert when the CC stage runs longer than 12 hours, so adjust that limit for a charge that takes longer.

### Set the charge current

The knob has no scale, so you set it while watching the battery current. This is the one adjustment you make on a live unit.

> [!CAUTION]
> The unit is powered while you turn the knob, and the AC terminals are on the same panel. Use an insulated tool, keep your fingers and the tool away from the terminals, and don't touch the Battery Start button next to the knob.

1. Make sure the battery isn't full, so that the charge lasts long enough to adjust. Half an hour on battery gives you several minutes of charging at constant current.
2. With AC power on and the charge running, open `sensor.drs_battery_current` in Home Assistant. It updates every 10 seconds.
3. Turn the knob a little, wait for two readings to see which way the current moved, and repeat until you have the current you want.

The tested unit arrived set to 2.61 A.

How much current:

- Stay within what the battery maker recommends. For the tested 50 Ah battery that's 10 A.
- Stay well below the rating of the battery fuse. The tested system has a 10 A fuse and charges at about 6.1 A.
- More current means more heat. At 6.1 A into the battery plus 2.6 A of load, the internal temperature of the tested unit reached 62.6°C indoors (the room temperature wasn't recorded). The package alerts at 70°C.

At 6.1 A, a full charge of the 50 Ah battery from the cut-off took about 8.3 hours of charging.

The `CURVE_CC` register doesn't limit the current. Don't rely on it.

### Set the battery cut-off

On battery, the output equals the battery voltage. So the cut-off voltage is also the lowest voltage your loads will see. Choose it with three things in mind:

- **Your loads.** Set the cut-off above the voltage where they misbehave. A router on the tested unit started rebooting in a loop at 11.0 V, which is worse than a clean switch-off.
- **The BMS of the battery.** Set the cut-off above the over-discharge protection of the BMS, so that the DRS disconnects first. The BMS of the tested battery trips at 10 V ± 0.5 V.
- **Capacity.** Raising the cut-off costs little with LiFePO4. The voltage falls fast at the end: the tested battery went from 12.0 V to 11.2 V in about 30 minutes at 1.8 A. With the cut-off at 11.20 V it still delivered about 49 Ah of its nominal 50 Ah.

The tested unit uses 11.20 V. The register accepts 9.6 V to 12.0 V, with a tolerance of ±0.12 V (section 5.4.4). The measured cut-offs were at 11.20 V to 11.23 V.

To write it, go to **Developer tools** > **Actions**, switch to YAML mode, paste this, and select **Perform action**. The value is the voltage multiplied by 100:

```yaml
action: script.drs_write_register
data:
  address: 208   # BAT_UVP_SET
  value: 1120    # 11.20 V
```

Register 209 (`Force_BAT_UVP_SET`) is the cut-off for the force-start mode. The tested unit has it at the same value. It only matters if CN12 pins 7 and 8 are linked.

> [!WARNING]
> The DRS stores settings in its EEPROM. Write a register once, by hand. Never write registers from an automation that runs often.

## Results

On the bench, in the final configuration (October 26–28, 2026, load about 2.6 A):

- 11 outages from the rest state, from 5 seconds to 15 minutes: the charge started by itself after every one.
- A discharge to the cut-off delivered about 49 Ah. The unit went silent at 11.20 V. When AC returned, the charge started at 6.11 A at once.
- The recharge put about 50 Ah back. It took 8.5 hours on the clock, including two short test interruptions, and about 8.3 hours of charging.
- After a full restart of the DRS, the charge started after 22 seconds.
- In 12 hours of rest the battery current read 0.02–0.04 A and the battery voltage stayed flat at 13.81 V.

On site (the first two weeks, load 1.5–2.3 A, 138 power outages and 59 hours without AC):

- 69 outages were followed by at least 2 minutes of AC power. The charge started by itself after 67 of them, within seconds, at about 6.1 A.
- 15 outages lasted an hour or more, the longest almost 7 hours. The lowest state of charge was 74%.
- In the rest state the output sat at 14.20 V and the battery at 13.7 V to 14.0 V.

The full numbers are in [Testing and results](testing-and-results.md).

## When the charge doesn't restart

Twice on site, the tested unit went into the "CC but discharging" state after AC power returned.

| Case | Before | Outage | Load | What followed |
| --- | --- | --- | --- | --- |
| First | Rest state, battery full | 15 seconds | 1.63 A | Battery fed the load for 112 minutes, about 3.2 Ah. Ended when AC was switched off for 18 seconds with the smart plug: charge at 6.1 A right after |
| Second, five days later | End of a charge, constant-voltage stage | 10 seconds | 1.59 A | Battery fed the load for 150 minutes, about 4.3 Ah. Ended with the next natural outage, 10 seconds long: charge at 6.13 A 13 seconds after AC returned |

What the two cases, and the earlier bench cases, have in common:

- **A light load.** Every failure on record happened with less than 1.7 A on the output. With 2 A or more, the charge restarted 38 of 38 times on site and 11 of 11 times on the bench. With less than 2 A it restarted 29 of 31 times on site.
- **On site, a very short outage.** Both site failures followed outages of 10 to 15 seconds. After outages longer than 30 seconds, the charge restarted 19 of 19 times. That isn't a rule, though: in the early bench tests, with a load of about 1.5 A, the charge failed to restart after outages of 45 seconds, 80 seconds, 7 minutes, and 8.5 minutes.
- **No pattern beyond that.** The day after the first failure, an outage of similar length, from the same state, at the same load, was followed by a normal charge.

So the failure is intermittent. The load looks like a factor, and on site the length of the outage did too. The cause isn't known.

How to recognize it:

- AC power is present, but `sensor.drs_battery_current` stays negative, at about the load current.
- `CHG_STATUS` reads 2 (CC).
- The output voltage stays equal to the battery voltage and falls slowly. When a charge really starts, the output steps up above the battery voltage within seconds.

What it costs: the battery discharges at the load current for as long as the state lasts. On site, each episode ended about two hours in, with the next interruption of AC power: once a deliberate one, once a natural outage. On a site where AC power never drops, nothing would end it. How far the battery would discharge wasn't tested. By the manual, the next automatic restart of the charge is at 80% of the boost voltage, which is 11.36 V with the flooded preset.

What to do:

1. Let the package tell you. The alert **Battery discharging on AC** fires after 20 minutes in this state. In the second case it fired 20 minutes into the episode.
2. Interrupt AC power to the DRS for 10 to 20 seconds, with the smart plug or by hand. The loads run from the battery in the meantime.
3. Check that the battery current turns positive within a few seconds after AC returns.

On the bench, an interruption of 5 seconds was enough. The one exception: after a start from the battery with the force-start pins linked, interrupting AC power didn't help, and only reconnecting the battery did. That's one more reason to leave those pins open.

**About automating the restart.** An automation that switches the plug off for 10 seconds when this state is detected was designed, but never built or tested, so this repository doesn't include one. If you write your own, limit the number of attempts, make sure the plug always switches on again by itself, and never let it switch off while the battery is low.

## What isn't explained

- Why the same outage sometimes restarts the charge and sometimes doesn't.
- Why the same test failed on the bench on October 16 and 21 and succeeded 11 times on October 26. The differences in between: a heavier load (1.5 A, then 2.6 A), three discharges to the cut-off, one of which left the unit without any power, and the force-start link being fitted and removed.
- Why the float stage doesn't hold the float voltage.
- Whether another firmware version behaves differently. The firmware version of the tested unit wasn't read.

A search in October 2026 found no public report of this behavior with DRS units and LiFePO4 batteries. That doesn't prove there isn't one. If your unit behaves differently, or the same, please open a field report in the issue tracker.

## Checklist for your battery

Before you copy the configuration, check these points against the datasheet of your battery:

- [ ] The maximum charge voltage is above 14.5 V. The flooded preset can reach 14.48 V with its tolerance.
- [ ] The battery reaches its balancing voltage at 14.2 V, or its maker accepts charging at 14.2 V.
- [ ] The recommended charge current is at or above what you set with the knob.
- [ ] The low-voltage protection of the BMS is below your cut-off voltage, including tolerances.
- [ ] You know the lowest temperature at which the battery accepts a charge. If the battery can get colder than that, add a temperature sensor and the [battery cold alert](state-of-charge-and-alerts.md#battery-cold-alert).
- [ ] The capacity is within the range the manual recommends: 20 Ah to 200 Ah for the 12 V model.
- [ ] A full charge fits into the CC timeout: capacity divided by charge current is well below 10 hours, or you raise the timeout.
- [ ] Your loads accept 14.5 V continuously, or run from a DC-DC regulator. That's the 14.2 V of the preset plus its 2% tolerance.

Next: [Modbus register map](modbus-register-map.md)
