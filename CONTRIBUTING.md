# Contributing

Thanks for helping. This guide rests on one unit and one battery, so reports from other setups are worth more than anything else.

## Field reports

If you run a DRS-240 or DRS-480, please share how it behaves. Use the **Field report** form in the issue tracker. The most useful reports include:

- The model and, if you have a Modbus tool that can read it, the firmware revision (registers 0x008C to 0x008E). The package doesn't read it.
- The battery: chemistry, voltage, capacity, and whether it has its own battery management system.
- The DIP switch positions and whether CN12 pins 7 and 8 are linked.
- The load current.
- What happens after a power outage: does the battery current turn positive when AC returns?
- What happens after hours on AC power: does the battery current stay near zero?

Numbers beat impressions. A screenshot of the battery chart from the dashboard is often enough.

## Fixes and additions

Open a pull request, or an issue if you want to discuss a change first.

- **Documentation** follows the Microsoft Writing Style Guide: second person, present tense, sentence-style headings, one idea per sentence.
- **Say where a fact comes from.** "The manual, section 5.3.1", "measured on a DRS-240-24 on 2026-12-01", or "not tested". Don't fill gaps with guesses.
- **Don't paste the manual.** Cite the section number and link to the official download page. The same goes for battery datasheets.
- **Package changes** that alter what is measured, counted, or alerted need a note on how you tested them.

## Before you submit

Remove private data from text, YAML, logs, and screenshots: IP addresses, host names, domains, serial numbers (including the one in the `/dev/serial/by-id/` path), chat and device IDs, names, and locations. Use placeholders such as `A1B2C3D4`.

Run the checks:

```sh
yamllint .
npx markdownlint-cli2
python .github/scripts/check_links.py
```

The same checks run on every pull request, together with a configuration check of the packages by Home Assistant itself.

## Licensing of contributions

By contributing, you agree that your text and images are licensed under [CC BY 4.0](LICENSE) and your code and YAML under the [MIT License](LICENSE-CODE).
