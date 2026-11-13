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

Each scan creates `results\\available_plates_YYYYMMDD_HHMMSS.txt` with the settings
used, every available plate, and totals. If the app folder isn't writable, results go
to `Documents\\FloridaPlateChecker\\results`.

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

## VirusTotal Security Scans

The release executable and supporting source/build files were submitted to
[VirusTotal](https://www.virustotal.com/) for analysis. The results below are
provided for transparency.

### Release executable

| File | Result | Report |
|---|---:|---|
| `FloridaPlateChecker.exe` | **1/71 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/f066bf12141d61348fd0515ef7eceee5c94895f93c62e2f3808dcc7ffeeb0351) |

The single detection was reported by **Skyhigh (SWG)** as
`BehavesLike.Win64.Backdoor.rc`. This is an antivirus vendor's heuristic
classification, not proof that the application contains a backdoor.

### Source code and build files

| File | Result | Report |
|---|---:|---|
| `plate_checker_cli.py` | **0/60 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/8240f45888ad629951198ccf6b5c76d57aa4700faf12c069134e08902d38de55) |
| `plate_checker_gui.py` | **0/62 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/85969953d071577e4e4230140efb64c632a3021df77ea12b7f04f5f2852d34c9) |
| `plate_core.py` | **0/62 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/72444f80d45d21743c379f413fa1d00f060f4bed49521a2e1e9d467b3826214f) |
| `build.bat` | **0/60 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/37807d989dcb2c6834bbde0bfa222f04018dfbc54fc44a4dc55b02870f30c82e) |
| `installer.iss` | **0/59 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/356b044216338f81ee1740929f200848e8d88f5982fefd017c137cf6c742d274) |
| `make_icon.py` | **0/62 detections** | [View VirusTotal report](https://www.virustotal.com/gui/file/06506d3ea8b714c489bfe77c3727a4821f50b1cb9544d7129c9f8e5e6610ed12) |

VirusTotal results are point-in-time scans and can change as antivirus vendors
update their detections. The executable's isolated detection is disclosed above so
users can review the full report and make their own assessment.

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
3. Find the app in `dist\\FloridaPlateChecker\\` and a shareable zip next to it.
4. Optional: install [Inno Setup](https://jrsoftware.org/isinfo.php) first and
   `build.bat` will also produce a Setup.exe in `installer_output\\`.
5. The icon (`app.ico`) and Windows file details (`version_info.txt`) are already set up. Edit `version_info.txt` to put your own name in the exe's Properties, and run `tools\\make_icon.py` (needs `pip install pillow`) if you want to regenerate the icon.

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
