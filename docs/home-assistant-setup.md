# Home Assistant setup

This page shows how to install the DRS-240 package in Home Assistant, how to check that it reads the unit, and which entities it creates. You need the RS-485 link from [Hardware and wiring](hardware-and-wiring.md) first.

The package is one YAML file. It uses the Modbus integration that's built into Home Assistant. You don't need a custom integration.

## Before you start

- **Home Assistant 2024.10 or later.** The package uses the automation syntax introduced in that release. It was tested on Home Assistant OS 18.3 with Core 2026.9.4. The menu paths on this page are those of Home Assistant OS.
- **A way to edit files in the configuration folder,** for example the File editor or Studio Code Server add-on.
- **The USB to RS-485 adapter,** plugged into the Home Assistant host and wired to the DRS.

## Install the package

### 1. Find the serial port

1. Go to **Settings** > **System** > **Hardware**, and select **All hardware**. Depending on the version, it's a button on the page or an entry in the three-dot menu.
2. Search for `tty`.
3. Open the entry for your adapter and copy the path that starts with `/dev/serial/by-id/`.

The path looks like this:

```text
/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A1B2C3D4-if00-port0
```

Use the `by-id` path, not `/dev/ttyUSB0`. The short name can change when you plug in another USB device. The `by-id` path stays the same.

If your installation has no **Hardware** page, for example Home Assistant Container, list the adapters on the host with `ls /dev/serial/by-id/`.

### 2. Turn on packages

1. Create a folder named `packages` in your configuration folder, next to `configuration.yaml`.
2. Add these lines to `configuration.yaml`. If the file already has a `homeassistant:` section, add only the `packages:` line to it.

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

### 3. Copy the package and set three values

1. Copy [`homeassistant/packages/drs240.yaml`](../homeassistant/packages/drs240.yaml) into the `packages` folder. On GitHub, open the file and select **Download raw file**. Or create a file named `drs240.yaml` in the `packages` folder with your editor and paste the content.
2. Open it and search for `SET ME`. There are three places:

   | Value | Where | Default in the file |
   | --- | --- | --- |
   | `SET ME 1`: serial port | `port:` near the top | A placeholder path. Replace the whole path with your `by-id` path |
   | `SET ME 2`: Modbus slave ID | `slave: &drs_slave 131` in the first sensor | 131, correct unless you changed the address pins on CN12 |
   | `SET ME 3`: battery capacity in Ah | `initial:` under `drs_battery_capacity` | 50 |

The slave ID is written once. The `&drs_slave` in front of the number gives it a name, and every other place in the file refers to it as `*drs_slave`. If you need another ID, change only the number and leave `&drs_slave` where it is. If you delete it, the file no longer loads.

### 4. Check the configuration and restart

1. Go to **Developer tools** > **YAML** and select **Check configuration**. If you don't see it, turn on **Advanced mode** in your user profile.
2. If the check passes, restart Home Assistant.

Adding the Modbus connection needs a full restart the first time. After later edits to the package, reloading **Modbus** and **Template entities** on the same page is enough.

### 5. Check the readings

Go to **Developer tools** > **States** and filter for `drs_`. Within a minute you should see values like these:

| Entity | What to expect |
| --- | --- |
| `binary_sensor.drs_link` | On (shown as **Connected**) |
| `sensor.drs_ac_input_voltage` | Your AC voltage |
| `sensor.drs_output_voltage` | The battery voltage while charging or on battery. 14.2 V to 14.4 V in the rest state |
| `sensor.drs_battery_voltage` | The battery voltage. Compare it with a multimeter once |
| `sensor.drs_battery_current` | Positive while charging, close to 0 in the rest state, negative on battery |
| `sensor.drs_charge_status_raw` | 2 or 4 while charging, 1 in the rest state. See [Status words](modbus-register-map.md#status-words) |
| `sensor.drs_set_battery_low_cutoff` and the other settings | They appear within 5 minutes. Settings are polled every 300 seconds |
| `sensor.drs_battery_soc` | A rough estimate at first, or unknown while charging. After the first complete charge it's counted. See [How accurate it is](state-of-charge-and-alerts.md#how-accurate-it-is) |

If everything stays unavailable, see [Troubleshooting](troubleshooting.md#home-assistant-gets-no-answer-from-the-drs).

### 6. Choose where alerts go

Every alert in the package calls one script, `script.drs_notify`. Out of the box it creates a notification in the Home Assistant sidebar. To send alerts to your phone as well, find the `sequence:` block of `drs_notify` in the package and replace it with this one, which has a second action:

```yaml
    sequence:
      - action: notify.persistent_notification
        data:
          title: "{{ title | default('DRS-240') }}"
          message: "{{ message }}"
      - action: notify.mobile_app_your_phone
        data:
          title: "{{ title | default('DRS-240') }}"
          message: "{{ message }}"
```

Replace `notify.mobile_app_your_phone` with a notify action that exists on your system. To find its name, go to **Developer tools** > **Actions** and type `notify.` into the action field. Then reload **Scripts**.

Think about what still works during an outage. If your internet connection runs from the DRS, the alerts reach you only while the battery lasts, which is the reason the low-battery alerts exist.

### 7. Match the settings reference

Do this step last, after you've set the DIP switches and written the battery cut-off. Before that, the sensor is off, and that's correct.

`binary_sensor.drs_settings_ok` compares 13 settings of your unit with a reference list in the package, and turns off when one of them differs. It's there to tell you when a setting changes behind your back.

The reference in the file is the configuration from this guide on a factory unit: the values the tested unit had when it was new, with the three changes this guide makes (2-stage, flooded preset, cut-off at 11.20 V). If you followed [The configuration that worked](lifepo4-charging.md#the-configuration-that-worked) and wrote the cut-off, the sensor should turn on by itself once the settings have been read.

If it stays off:

1. Open `binary_sensor.drs_settings_ok` under **Developer tools** > **States** and read its `mismatch` attribute. It lists every difference as "name, value read, reference".
2. Use the table below to decide, for each line, whether to change the unit or the reference. In most cases you change the reference.
3. To change the reference, search the package for `set ref =`. The list appears twice, once for the state and once for the attribute. Change both.
4. Reload **Template entities**.

| Name in `mismatch` | Reference in the file | Tested unit | What to do if yours differs |
| --- | --- | --- | --- |
| `charge_current` | 15.4 | 6.0 | Put the value read into the reference. It's the content of the register, not the current you set with the knob |
| `boost_voltage`, `float_voltage` | 14.4, 13.8 | 14.4, 13.8 | Put the values read into the reference. With a DIP preset they aren't used |
| `taper_current` | 1.54 | 1.54 | Put the value read into the reference. The register has no effect |
| `curve_config_raw` | 198 | 194 | Check the DIP switches first. 198 and 194 are both 2-stage with the flooded preset, with and without temperature compensation. See [CURVE_CONFIG](modbus-register-map.md#curve_config-address-180-0x00b4) |
| `cc_timeout` | 600 | 900 | Put the value read into the reference. Raise the register if a full charge of your battery takes more than about 8 hours |
| `battery_low_cutoff` | 11.2 | 11.2 | Write the cut-off you chose, and put the same value into the reference |
| `ups_config_raw` | 9 | 8 | Put the value read into the reference. 9 is the factory value |
| `system_config_raw` | 2 | 2 | 2 means the output switches on at power-up. If yours differs, find out why before you rely on the unit |
| `operation` | 1 | 1 | 0 means the output is switched off. See [Troubleshooting](troubleshooting.md#the-output-is-off-and-operation-reads-0) |
| `output_voltage` | 12.0 | 12.0 | Put the value read into the reference. The register has no effect |
| `ac_fail_high_line`, `ac_ok_high_line` | 171.6, 182.6 | 150.0, 165.0 | Put the values read into the reference |

"The value read" is the middle number of each entry in `mismatch`. Your unit can differ from the tested one when new, which is why the reference is yours to edit.

Details are in [Settings watchdog](state-of-charge-and-alerts.md#settings-watchdog).

### Optional: the battery cold alert

If you have a temperature sensor on the battery:

1. Copy [`homeassistant/packages/drs240_battery_cold.yaml`](../homeassistant/packages/drs240_battery_cold.yaml) into the `packages` folder.
2. Search for `SET ME` and replace `sensor.battery_temperature` with the entity ID of your sensor. Keep the `&drs_battery_temp` in front of it: the other two triggers refer to it.
3. Check the three temperature thresholds against the datasheet of your battery.
4. Check the configuration, then reload **Automations** and **Template entities**, or restart.

See [Battery cold alert](state-of-charge-and-alerts.md#battery-cold-alert).

## Entity reference

### Measurements

| Entity | Unit | Updates every | Register |
| --- | --- | --- | --- |
| `sensor.drs_ac_input_voltage` | V | 10 s | `READ_VIN` |
| `sensor.drs_output_voltage` | V | 10 s | `READ_VOUT` |
| `sensor.drs_output_current` | A | 10 s | `READ_IOUT` |
| `sensor.drs_battery_voltage` | V | 10 s | `READ_VBAT` |
| `sensor.drs_battery_current` | A | 10 s | `READ_IBAT` |
| `sensor.drs_internal_temperature` | °C | 30 s | `READ_TEMPERATURE_1` |

### Status

| Entity | Meaning |
| --- | --- |
| `sensor.drs_fault_status_raw`, `sensor.drs_charge_status_raw`, `sensor.drs_system_status_raw` | The three status words as numbers, read every 5 seconds |
| `binary_sensor.drs_ac_fail` | AC power missing or out of range. Use this one to detect an outage |
| `binary_sensor.drs_on_battery` | The load runs from the battery |
| `binary_sensor.drs_dc_ok` | Output voltage normal |
| `binary_sensor.drs_battery_full` | Charge complete (`FULLM`) |
| `binary_sensor.drs_charge_stage_cc`, `_cv`, `_float` | Charge stage reported by the unit |
| `binary_sensor.drs_battery_discharging` | Discharge flag of the unit (`DCM`) |
| `binary_sensor.drs_no_battery_detected` | No battery detected |
| `binary_sensor.drs_overload`, `drs_short_circuit`, `drs_output_over_voltage`, `drs_over_temperature`, `drs_high_ambient_temperature`, `drs_eeprom_error`, `drs_ntc_sensor_shorted` | Fault flags |
| `binary_sensor.drs_cc_stage_timeout`, `_cv_stage_timeout`, `_float_stage_timeout`, `drs_buffering_timeout` | Timeout flags |
| `binary_sensor.drs_dc_off` | The `OP_OFF` bit. For information only. See [the note on this bit](modbus-register-map.md#fault_status-address-64-0x0040) |

### Derived sensors

| Entity | Meaning |
| --- | --- |
| `binary_sensor.drs_link` | The DRS answers on Modbus. Turns off after 30 seconds without data |
| `sensor.drs_battery_charge` | Charge in the battery in Ah, from the counter |
| `sensor.drs_battery_soc` | State of charge in percent |
| `sensor.drs_battery_runtime` | Hours left on battery at the present load. Unknown when not on battery |
| `sensor.drs_battery_runtime_text` | The same as text, for example "7 h 53 min" |
| `sensor.drs_battery_time_text` | One line for every state: time left, time to full, or the state |
| `sensor.drs_active_curve` | The charge curve selected by the DIP switches, as text |
| `binary_sensor.drs_settings_ok` | The settings of the unit match your reference |
| `binary_sensor.drs_cut_off` | Output off without AC while the unit still answers. Seen only with the force-start pins linked |
| `binary_sensor.drs_backup_blocked` | Set after such a cut-off. See [Backup blocked](state-of-charge-and-alerts.md#cut-off-and-backup-blocked) |
| `binary_sensor.drs_ac_outage_reported` | On between the "no AC power" and the "AC power is back" alert |

How the counter works is in [State of charge and alerts](state-of-charge-and-alerts.md).

### Settings read back

21 sensors named `sensor.drs_set_…` show the settings registers, read every 5 minutes. For example `sensor.drs_set_battery_low_cutoff`, `sensor.drs_set_curve_config_raw`, and `sensor.drs_set_ups_config_raw`. The registers behind them are in [Settings](modbus-register-map.md#settings).

### Helpers, scripts, and automations

| Entity | Purpose |
| --- | --- |
| `input_number.drs_battery_capacity` | Battery capacity in Ah. You can change it in the UI, but Home Assistant sets it back to the value in the package at every start, so change it in the file |
| `input_boolean.drs_soc_full_latched`, `input_boolean.drs_soc_calibrated` | Memory of the counter across restarts. Don't switch them by hand |
| `script.drs_notify` | Where alerts go |
| `script.drs_write_register` | Guarded register write |
| `automation.drs_ac_alert`, `drs_low_battery`, `drs_link_lost`, `drs_link_back`, `drs_fault`, `drs_discharge_on_ac`, `drs_not_recharging` | The alerts. The names match the `id` of each automation in the file |
| `automation.drs_soc_flags` | Keeps the two counter helpers in step. Not an alert |
| `automation.drs_battery_cold`, `sensor.drs_battery_cold_reported` | Only with the optional battery cold package: the alert, and the level it reported last |

## Differences from the tested package

The package in this repository is a generalized version of the one that ran on the tested system. The measuring and counting logic is the same. These things differ:

- Entity names and message texts were rewritten for publication. The entity IDs of the sensors and binary sensors are the same, with one exception: the flag of the AC power alert is now `binary_sensor.drs_ac_outage_reported`.
- `input_number.drs_battery_capacity` and `script.drs_notify` are new.
- The serial port is a placeholder, and the slave ID is defined once.
- The battery capacity comes from `input_number.drs_battery_capacity` instead of a fixed number in the template.
- Alerts go through `script.drs_notify` instead of calling a messaging service directly.
- The AC power alert was reduced to the DRS.
- The battery cold alert names its temperature sensor in one place.
- Three `unique_id` values were corrected to match their entity IDs. The automations were renamed so that their entity IDs match their `id`, and two of them got a new `id`: `drs_ac_alert` and `drs_discharge_on_ac`.
- The settings reference holds the configuration from this guide on a factory unit, not the registers of the tested unit. The table in [Match the settings reference](#7-match-the-settings-reference) shows both.

What was checked after these changes: the YAML passes yamllint, and every template in the package was rendered through the template API of the live test system without an error. What wasn't: the published file hasn't run through a power outage on a real system. If **Check configuration** or an alert shows a problem, please open an issue.

## Update or remove the package

To update, replace the file with the new version and carry your own changes over: the three `SET ME` values, the notify action, the settings reference, and any threshold you adjusted. Keep a copy of your old file to compare. The [changelog](../CHANGELOG.md) lists what changed.

To remove the package, delete the file from the `packages` folder and restart Home Assistant. Entities with history stay in the entity list as restored entries until you delete them under **Settings** > **Devices & services** > **Entities**.

Next: [State of charge and alerts](state-of-charge-and-alerts.md)
