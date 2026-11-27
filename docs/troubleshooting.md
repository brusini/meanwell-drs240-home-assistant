# Troubleshooting

This page lists problems you can run into with a DRS-240 in Home Assistant, with the likely cause and the fix. Most entries come from things that went wrong during the tests behind this guide.

## Home Assistant gets no answer from the DRS

All `drs_` entities are unavailable, and `binary_sensor.drs_link` is off.

| Check | How |
| --- | --- |
| Is the unit powered? | After a battery cut-off the DRS is completely off until AC power returns. Look at the LEDs |
| Is the serial port right? | Compare `port:` in the package with the path under **Settings** > **System** > **Hardware**. Use the `/dev/serial/by-id/` path |
| Does Home Assistant have the adapter? | In a virtual machine or a container, the USB device has to be passed through |
| Are Data+ and Data− swapped? | Swap the wires on `A+` and `B-` and try again. On RS-485, swapped data wires don't damage anything. The link just stays silent |
| Are the pins right? | RJ45 pins 6, 7, and 8. Check them against the plug, not only against the wire colors |
| Is the slave ID right? | 131 with the CN12 address pins open. If a pin is linked, try 128 to 131 |
| Did you restart? | Adding the Modbus connection needs a full restart of Home Assistant the first time |

If your adapter has transmit and receive LEDs: a blinking transmit LED alone means Home Assistant is asking and nothing answers. Both blinking means the unit answers, and the problem is the slave ID or the settings.

While the DRS is off, the Home Assistant log fills with Modbus errors, about one per sensor per second. That's expected, and it stops when the unit answers again.

## The link came back, but only after a few minutes

That's normal. After the USB adapter was unplugged and plugged in again on the tested system, the Modbus integration reconnected by itself after about 4.5 minutes. After a restart of the DRS, the data was back within 2 minutes. The settings follow up to 5 minutes later, because they're polled every 300 seconds.

## The battery current is negative although AC power is present

Look at `sensor.drs_charge_status_raw`:

- **2:** the "CC but discharging" state. The battery is feeding the load. Follow the steps below.
- **9:** the float stage of 3-stage mode. See [the next entry](#the-battery-loses-charge-every-night-with-ac-power-present).
- **Anything else:** not seen in the tests. Try the steps below, and please report the status values.

1. Interrupt AC power to the DRS for 10 to 20 seconds.
2. Check that the battery current turns positive within a few seconds after AC returns.

Background and numbers are in [When the charge doesn't restart](lifepo4-charging.md#when-the-charge-doesnt-restart).

If the state appears right after you powered the DRS up, give it a few minutes first. In the early tests the unit showed this state after every start. In the final configuration the charge began 22 seconds after the start. The alert for this state waits 20 minutes, so that a slow start doesn't raise it.

## The battery loses charge every night, with AC power present

Check DIP switch 1. In 3-stage mode (DIP 1 OFF, the factory setting), the float stage of the tested unit drained a LiFePO4 battery into the load: about 9 Ah in 10 hours. `sensor.drs_charge_status_raw` reads 9 in that state.

Switch to 2-stage mode. See [The configuration that worked](lifepo4-charging.md#the-configuration-that-worked).

## The charge current isn't what I set

The charge current follows the knob on the panel. The `CURVE_CC` register and `sensor.drs_set_charge_current` don't change it on the tested unit. See [Set the charge current](lifepo4-charging.md#set-the-charge-current).

According to the manual (sections 2.3 and 5.1), the unit also reduces the charge current by itself when the loads need the power: the loads have priority, and the total is limited to 240 W.

## The output is 14 V, not 12 V

That's how the unit works. During a charge the output follows the battery, and after a 2-stage charge it stays at the boost voltage. See [Output voltage](operating-modes.md#output-voltage).

If a load can't take it, put a [DC-DC regulator](hardware-and-wiring.md#a-dc-dc-regulator-for-12-v-loads) in front of that load. `VOUT_SET` won't help.

## Loads reboot or misbehave when the battery is nearly empty

On battery the output equals the battery voltage, and it falls quickly at the end. A router on the tested unit began to reboot in a loop at 11.0 V, while the cut-off was still set below that.

Raise the cut-off voltage above the point where your loads misbehave, or feed them through a DC-DC regulator with a wide input range. See [Set the battery cut-off](lifepo4-charging.md#set-the-battery-cut-off).

## After a battery cut-off, the unit no longer switches to the battery

The battery charges, but at the next outage the output drops. `binary_sensor.drs_backup_blocked` is on.

This happened on the tested unit with CN12 pins 7 and 8 linked.

1. Remove the link between pins 7 and 8.
2. With AC power present, pull the battery fuse, wait a few seconds, and put it back. The unit detects the battery again and charges it. Keep it short: Mean Well describes a wake-up sequence that repeats while no battery is connected, and it moves the output voltage.
3. Test with a short outage.

## A register write succeeded, but nothing changed

Several registers store a value without acting on it. On the tested unit that's true for `VOUT_SET`, `CURVE_CC`, `CURVE_TC`, `CURVE_FV`, and for `CURVE_FV_TIMEOUT` during a running float stage. The full list is in [Settings](modbus-register-map.md#settings).

If you wrote with `script.drs_write_register` and the value didn't even change in Home Assistant, wait: the settings sensors update every 5 minutes. If the script reported an error, the address or the value is outside its [whitelist](state-of-charge-and-alerts.md#the-register-write-script).

## The output is off and OPERATION reads 0

Someone wrote 0 to register 0. On the tested unit the output then stayed off until the unit was power-cycled by hand. A power cycle works because the unit switches the output on at power-up.

By the manual, writing 1 to the register switches the output on again. That wasn't tested. The write script refuses register 0 on purpose, so if a power cycle isn't possible, you'd write the 1 with the Modbus action directly, in **Developer tools** > **Actions**:

```yaml
action: modbus.write_register
data:
  hub: drs240
  slave: 131   # your slave ID
  address: 0
  value: 1
```

This only works while Home Assistant can still reach the unit.

## "Settings changed", or DRS settings OK is off

`binary_sensor.drs_settings_ok` compares the unit with the reference in the package.

- Right after the installation, that's expected until you've set the DIP switches and written the cut-off. If it stays off after that, your unit differs from the reference in the file. See [Match the settings reference](home-assistant-setup.md#7-match-the-settings-reference).
- Later, read the `mismatch` attribute. If many values are back at factory defaults, someone pressed the Battery Start button five times. If `curve_config_raw` changed, someone moved a DIP switch.

## The state of charge says "rough estimate"

The counter hasn't passed a full or an empty point yet, or it lost track during a long gap. One complete charge fixes it: when the unit reports "charge complete" with the battery above 13.9 V, the counter is set to the capacity.

If the percentage is plausible in the rest state but drops too fast or too slowly on battery, check the capacity in `input_number.drs_battery_capacity`. See [How accurate it is](state-of-charge-and-alerts.md#how-accurate-it-is).

## No "AC power is back" message after a cut-off

That's by design. During the cut-off the unit is off, and the AC fail flag becomes unavailable instead of changing from on to off. The "Modbus link is back" message tells you the unit is running again, and includes whether AC is present.

## The battery doesn't charge in the cold

Many LiFePO4 batteries block the charge near 0°C. This didn't happen in the tests, where the battery stayed above 8°C. What you'd expect to see: the DRS shows a charge stage, but the battery current stays near zero. The "battery not recharging" alert is built to fire after 30 minutes in that state.

Warm the battery, or move it. A sensor on the battery and the [battery cold alert](state-of-charge-and-alerts.md#battery-cold-alert) warn you before it happens.

## The Status LED blinks red

Count the blinks between the pauses and look them up in [LEDs and relay contacts](operating-modes.md#leds-and-relay-contacts). The same faults show up as flags on the dashboard.

## The charts on the dashboard show an error

The four charts need the custom card apexcharts-card. Install it with HACS and reload the browser. See [Dashboard](dashboard.md#before-you-start).

## Entities have "_2" at the end of their IDs

An earlier copy of the package, or leftovers from it, already own the original entity IDs. Remove the duplicate file from the `packages` folder, restart, delete the leftover entities under **Settings** > **Devices & services** > **Entities**, and restart again.

## Still stuck

Open an issue with the **Problem** form. Include your DRS model, the DIP switch positions, the values of the three status words, and the battery voltage and current at the moment of the problem.
