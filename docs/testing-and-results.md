# Testing and results

This page documents how the DRS-240 setup in this guide was tested, what the tests showed in numbers, what wasn't tested, and how to repeat the important tests on your own system.

## Test setup

| | Bench | Site |
| --- | --- | --- |
| Period | October 12–28, 2026, after first readings without a battery on October 3 | After the bench tests. Data here covers the first two weeks |
| Unit | DRS-240-12, Modbus version | The same unit |
| Battery | 12.8 V, 50 Ah LiFePO4 with BMS, 10 A fuse, 2.5 mm² wire | The same battery, in a room at 8°C to 12°C |
| Load | A router, 0.8 A to 1.9 A, until October 23. Then about 2.6 A, up to 4.4 A with a lamp added | Network equipment, 1.5 A to 2.3 A |
| AC power | Switched by hand, later by a smart relay | A grid with frequent outages |
| Recording | Home Assistant recorder, one sample every 5 to 10 seconds | The same |

The configuration changed during the bench tests. The final configuration, described in [LiFePO4 charging](lifepo4-charging.md#the-configuration-that-worked), was tested from October 26. Results from before that date are marked, and so is everything measured with the force-start pins linked.

The alerts that ran during these tests are earlier versions of the ones in the package, with different message texts and a chat app as the destination. Their logic was refined along the way: the runtime estimate and the handling of the cut-off changed between the two discharges, and the AC power alert got its 5-minute delay later, on site. The alert times of the first discharge come from the earlier version.

## Results at a glance

| Test | Result |
| --- | --- |
| Outages from the rest state, bench, final configuration | 11 of 11 recharged by themselves: 5 seconds to 15 minutes, load 2.6 A |
| Outages on site, with at least 2 minutes of AC afterward | 67 of 69 recharged by themselves. See [When the charge doesn't restart](lifepo4-charging.md#when-the-charge-doesnt-restart) for the other two |
| Discharge to the cut-off | About 49 Ah delivered. The counter reached 0% two minutes before the cut-off. Cut-off at 11.20 V, as set |
| AC power back after the cut-off | Output on by itself, charge at 6.11 A at once, Modbus link back without a restart of Home Assistant |
| Outage 10 minutes after that recovery | Ran on the battery normally |
| Recharge from the cut-off | About 8.3 hours of charging (8.5 hours on the clock, with two short test interruptions), about 50 Ah back in, no BMS trip |
| Full restart of the DRS (AC off, fuse out, fuse in, AC on) | Charge at 6.12 A after 22 seconds |
| Rest on AC power | 12 hours on the bench, up to 15.9 hours on site: battery current reading 0.02–0.04 A, battery voltage flat, no charge restart |
| First charge of the new battery, from 10.78 V | 51.2 Ah accepted, no BMS trip (3-stage mode, before the final configuration) |
| Restart of Home Assistant during a charge and in the rest state | Counter value, full point, and calibration kept |
| USB adapter unplugged for 8 minutes | "No link" alert after 2 minutes. The link came back by itself 4.5 minutes after the adapter was plugged in again |
| Alerts during two full discharges | All arrived: outage, SOC below 30% and 15%, runtime below 1 hour, battery below 11.6 V, link lost, link back |
| Write script called with register 0 (`OPERATION`) | Refused before anything was sent |

## Discharge and recharge in numbers

| | October 22–23 | October 26–27 |
| --- | --- | --- |
| Configuration | Final DIP setting, force-start pins linked | Final configuration |
| Start | Rest state, counter at 50.0 Ah | Rest state, counter at 50.0 Ah |
| Load current | 0.8 A to 1.9 A | 2.6 A to 4.4 A |
| Time to the cut-off | 30 hours 27 minutes | 14 hours 58 minutes |
| Charge delivered, by the counter | 48.7 Ah | 49.5 Ah |
| Cut-off voltage (set: 11.20 V) | 11.22–11.23 V | 11.20 V |
| SOC below 30% alert | 7 hours 7 minutes before the cut-off | 3 hours 34 minutes before |
| SOC below 15% alert | 3 hours 7 minutes before | 1 hour 41 minutes before |
| Runtime below 1 hour alert | 23 minutes before | 53 minutes before |
| Battery below 11.6 V alert | 9.5 minutes before | 4.5 minutes before |
| After the cut-off | Unit still answered on Modbus, output off | Unit silent |

Two things to take from the table. The usable capacity down to 11.20 V was within 3% of the nominal 50 Ah. And the voltage alert comes only minutes before the cut-off, because the voltage of a LiFePO4 battery falls late and fast. The earlier warnings depend on the counter.

The recharge on October 27 started 20 minutes after the cut-off and was interrupted twice on purpose, by a 30-second outage and by the full restart. Its last uninterrupted part: constant current at 6.11–6.12 A for 7 hours 20 minutes, constant voltage from 14.09 V, rest state 9 minutes later. The counter read 48.7 Ah at the start of the constant-voltage stage, and about 1.2 Ah more went in uncounted during a deliberate link test.

The highest internal temperature of the unit was 62.6°C, during that recharge, with 6.1 A into the battery and 2.6 A of load. The room temperature wasn't recorded.

## Two weeks on site

The first two weeks on site, about 315 hours, from the Home Assistant recorder:

| Measure | Value |
| --- | --- |
| AC-fail events | 138 |
| Time without AC power | 58.8 hours of about 315 |
| Outages of 1 hour or more | 15. The longest: 6 hours 58 minutes, about 12.6 Ah drawn |
| Outages shorter than 1 minute | 107, most of them in two bursts |
| Load current | Median 2.15 A. 5th to 95th percentile: 1.54 A to 2.30 A |
| Lowest battery voltage | 13.0 V |
| Lowest state of charge | 74% |
| Battery cut-offs | None |
| Recharge after the second-longest outage, 6 hours 38 minutes and 12.7 Ah | 117 minutes at 6.12 A, then constant voltage at 14.09 V. Rest state 130 minutes after AC returned. The longest outage isn't used here, because a burst of interruptions followed it |
| Rest state | Output 14.20 V, battery settles between 13.7 V and 14.0 V |
| Internal temperature | 25°C to 48°C |
| Charge restarts after an outage | 67 of 69. By load: 38 of 38 at 2 A or more, 29 of 31 below 2 A. By length of the outage: 19 of 19 above 30 seconds, 48 of 50 at 30 seconds or less |

How the outages were counted: an outage is a period with the `AC_FAIL` bit set, sampled every 5 seconds. "Recharged" means a battery current above 0.5 A within 60 seconds after AC returned. Only the 69 outages that were followed by at least 2 minutes of AC count for the restart statistics. In a burst of interruptions, the next outage arrives before the charge can be judged.

## What wasn't tested

- A soak of several days without any outage. The longest rest period is 15.9 hours.
- How far the battery discharges in the "CC but discharging" state if AC power never drops.
- The idle battery current with a clamp meter. The reading of the unit can't resolve it.
- Charging at a battery temperature below 8°C.
- The AGM and LiFePO4 preset, and the default curve in 2-stage mode after October 15.
- The battery life test switched on, in the final configuration.
- The NTC temperature sensor, lead-acid batteries, and temperature compensation.
- The AC threshold registers, the stage timeouts, and the buffering, delay, and shutdown timers.
- The Battery Start button, apart from one press with the force-start pins linked.
- A gap of more than a few minutes in Home Assistant during a discharge.
- Other models: 24 V, 36 V, 48 V, the DRS-480, the CANBus version.
- Other firmware versions. The version of the tested unit wasn't read.
- The published English package through a real outage. See [Differences from the tested package](home-assistant-setup.md#differences-from-the-tested-package).

## Repeat the tests on your system

Do these in order, and stay on site until the first two have passed. The first test starts from a full battery in the rest state, so wait for the first charge to finish. `sensor.drs_charge_status_raw` reads 1 when it has.

> [!WARNING]
> Every test here interrupts AC power to the DRS. Use loads that may lose power. Don't run the discharge test with nobody on site: at the cut-off the output switches off, and if your network runs from it, you lose remote access until AC returns.

1. **Short outage.** With the battery full and the unit in the rest state, switch AC off for 2 minutes.
   - The loads keep running, and `binary_sensor.drs_on_battery` turns on.
   - Switch AC on. Within a minute `sensor.drs_battery_current` must be positive, close to the current you set with the knob.
2. **Repeat it.** Do at least five more outages, including some of 10 to 15 seconds and some at your lowest load. Short outages at a light load are where the tested unit failed to restart the charge. If the battery current stays negative after AC returns, you've found the state. Interrupt AC for 10 to 20 seconds to clear it. That isn't a contradiction: the failure is intermittent, and the same short interruption usually restarts the charge.
3. **Rest.** After the charge completes, leave the system alone for 12 hours. The battery current should read close to 0, the battery voltage should settle and stay flat, and no alert should fire.
4. **Alerts.** Switch AC off for 6 minutes. The "no AC power" alert must arrive after 5. Switch AC on. The "AC power is back" alert must say that the battery is charging.
5. **Link.** Unplug the USB adapter for 3 minutes. The "no Modbus link" alert must arrive. Plug it in again. The link should recover by itself within a few minutes.
6. **Discharge to the cut-off, optional.** This measures your real capacity and proves that the output comes back by itself.
   - Start from the rest state with Home Assistant recording and powered independently of the DRS.
   - Switch AC off and wait. Note when each low-battery alert arrives.
   - At the cut-off the output switches off and the unit stops answering.
   - Switch AC on. The output must come back by itself, and the charge must start.
   - Read how many ampere-hours the counter had counted when it reached 0%. If that's far from your capacity setting, change the setting.

If your results differ from the ones on this page, a [field report](../CONTRIBUTING.md#field-reports) helps everyone who uses this unit.

Next: [Troubleshooting](troubleshooting.md)
