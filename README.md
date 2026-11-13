# Florida Plate Checker

A small Windows app that checks whether Florida personalized license plates are
available, using the FLHSMV plate-check service. Pick a pattern (like two letters)
or a word list, press **Start**, and it lists every plate that comes back available.

> **Unofficial tool.** Not affiliated with or endorsed by FLHSMV. Results are only a
> snapshot, so always confirm on the official site before ordering a plate.

## Quick start (Windows)

1. Unzip the download, or run the installer.
2. Open **FloridaPlateChecker.exe**.
   - If Windows SmartScreen says "Windows protected your PC", click
     **More info → Run anyway**. This happens with any new unsigned app.
3. Choose what to check, then click **Start scan**.
4. Available plates appear in the left list and are saved automatically to the
   `results` folder. Use **Copy all available** or **Open results folder**.

## Settings explained

| Setting | What it does |
|---|---|
| Plates to check | A built-in pattern, a custom pattern, or the dictionary file |
| Custom pattern | `L` = any letter, `D` = any digit. `LLD` = two letters then a digit (`AB1`) |
| Dictionary min/max length | Only use words with this many characters (1-7) |
| How many | `all`, or a number to limit the scan |
| Order | Sequential (A, B, C...) or Random |
| Parallel requests | How many plates are checked at once. Lower is gentler |
| Pause between batches | Wait time between groups of 25 plates |

Patterns are limited to 1,000,000 combinations (for example `LLLL` works, `LLLLL` doesn't).

## Using your own word list

`plate_dictionary.txt` sits next to the app: one word per line. Anything that isn't
A-Z / 0-9 is ignored, and words are uppercased and de-duplicated. Edit it with
Notepad and restart the scan.

## Results

Each scan creates `results\available_plates_YYYYMMDD_HHMMSS.txt` with the settings
used, every available plate, and totals. If the app folder isn't writable, results go
to `Documents\FloridaPlateChecker\results`.

## Troubleshooting

- **Lots of ERROR lines / "site may be blocking you"**: the site is rate-limiting
  you. Click Stop, wait 10-30 minutes, then lower *Parallel requests* and raise
  *Pause between batches*.
- **"plate_dictionary.txt wasn't found"**: keep that file in the same folder as the
  .exe.
- **Antivirus flags the app**: this is a common false positive for apps built with
  PyInstaller. Build it yourself from source (below) if you'd rather not trust the
  download.
- **The site changed and everything errors**: the app depends on the layout of the
  DHSMV page, so a site update can break it. Check for a newer version.

## Run from source

```
pip install -r requirements.txt
python plate_checker_gui.py      # the app
python plate_checker_cli.py      # console version
```
Requires Python 3.9+ (tkinter is included with the standard Windows installer).

## Build the .exe yourself

1. Install Python from python.org (tick **Add Python to PATH**).
2. Double-click **build.bat**.
3. Find the app in `dist\FloridaPlateChecker\` and a shareable zip next to it.
4. Optional: install [Inno Setup](https://jrsoftware.org/isinfo.php) first and
   `build.bat` will also produce a Setup.exe in `installer_output\`.
5. The icon (`app.ico`) and Windows file details (`version_info.txt`) are already set up. Edit `version_info.txt` to put your own name in the exe's Properties, and run `tools\make_icon.py` (needs `pip install pillow`) if you want to regenerate the icon.

## Files

| File | Purpose |
|---|---|
| `plate_checker_gui.py` | The desktop app |
| `plate_checker_cli.py` | Console version |
| `plate_core.py` | Shared scanning engine |
| `plate_dictionary.txt` | Word list |
| `build.bat` / `installer.iss` | Build and installer scripts |
| `app.ico`, `logo.png`, `version_info.txt` | Icon, header logo, exe file properties |
| `tools/make_icon.py` | Regenerates the icon (developers only) |
| `LICENSE` | MIT license |

## Responsible use

This tool sends many requests to a government website. Keep the settings gentle,
don't run it around the clock, and follow the site's terms of use. You are
responsible for how you use it.

## License

[MIT](LICENSE)
