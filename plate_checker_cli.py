"""Florida Plate Checker - console version (same engine as the GUI)."""

import os
import random
from datetime import datetime

import plate_core as core

os.system("")  # enables ANSI colors in the Windows console

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def ask(prompt, default=None):
    try:
        value = input(prompt).strip()
    except EOFError:
        value = ""
    return value if value else (str(default) if default is not None else "")


def ask_int(prompt, default, lo, hi):
    while True:
        try:
            value = int(ask(prompt, default))
        except ValueError:
            print("Please enter a number.")
            continue
        if lo <= value <= hi:
            return value
        print(f"Enter a value from {lo} to {hi}.")


def choose():
    print("\n" + "=" * 30)
    print(f"  {core.APP_NAME.upper()}  v{core.APP_VERSION}")
    print("=" * 30)
    print("\n[STEP 1] Choose source")
    print("  1. LL (2 letters)   2. DD (2 digits)   3. LD   4. DL")
    print("  5. Custom pattern (e.g. LLD)")
    print("  6. Dictionary file")
    choice = ask("Enter choice (1-6) [default 1]: ", "1")
    presets = {"1": "LL", "2": "DD", "3": "LD", "4": "DL"}

    try:
        if choice in presets:
            label = presets[choice]
            pool = core.generate_pattern_plates(label)
        elif choice == "5":
            label = core.clean_pattern(ask("Pattern (L=letter, D=digit) [LLL]: ", "LLL"))
            pool = core.generate_pattern_plates(label)
        elif choice == "6":
            lo = ask_int("  Minimum length [1]: ", 1, 1, 7)
            hi = ask_int("  Maximum length [7]: ", 7, 1, 7)
            lo, hi = min(lo, hi), max(lo, hi)
            pool = core.load_dictionary(lo, hi)
            label = f"Dictionary ({lo}-{hi} chars)"
            if not pool:
                print("No words matched. Falling back to LL.")
                label, pool = "LL", core.generate_pattern_plates("LL")
        else:
            label, pool = "LL", core.generate_pattern_plates("LL")
    except FileNotFoundError:
        print(f"Dictionary file not found: {core.DICTIONARY_FILE}")
        return None
    except ValueError as exc:
        print(exc)
        return None

    print(f"[INFO] {len(pool):,} possible plates.")
    print("\n[STEP 2] How many?")
    try:
        count = core.parse_count(ask("Enter count or 'all' [all]: ", "all"), len(pool))
    except ValueError:
        count = len(pool)

    print("\n[STEP 3] Order")
    randomize = ask("1=Sequential, 2=Random [1]: ", "1") == "2"
    plates = core.select_plates(pool, count, randomize)

    print(f"\n  Source: {label}   Count: {len(plates)}   Order: {'Random' if randomize else 'Sequential'}")
    print(f"  Preview: {', '.join(plates[:5])}")
    if ask("\nStart scan? (y/n) [y]: ", "y").lower() == "n":
        return None
    return label, randomize, plates


def main():
    selection = choose()
    if selection is None:
        input("\nPress Enter to exit...")
        return
    label, randomize, plates = selection

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(core.results_dir(), f"available_plates_{stamp}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("Florida DHSMV Available Plates\n")
        f.write(f"Source: {label}\nMode: {'Random' if randomize else 'Sequential'}\n")
        f.write(f"Count: {len(plates)}\nDate: {datetime.now():%Y-%m-%d %H:%M:%S}\n" + "-" * 30 + "\n")
    print(f"\nResults will be saved to: {out}\n{'STATUS':<12} | PLATE\n" + "-" * 25)

    counts = {"AVAILABLE": 0, "TAKEN": 0, "ERROR": 0}
    colors = {"AVAILABLE": GREEN, "TAKEN": RED, "ERROR": YELLOW}

    def on_result(plate, status):
        counts[status] += 1
        print(f"{colors[status]}{status:<12}{RESET} | {plate}")
        if status == "AVAILABLE":
            with open(out, "a", encoding="utf-8") as f:
                f.write(plate + "\n")

    try:
        core.run_scan(plates, on_result, on_status=lambda m: print(f"-- {m}"))
    except KeyboardInterrupt:
        print("\nStopped by user.")

    with open(out, "a", encoding="utf-8") as f:
        f.write("-" * 30 + "\n")
        for key in ("AVAILABLE", "TAKEN", "ERROR"):
            f.write(f"Total {key.title()}: {counts[key]}\n")
    print("-" * 25)
    for key in ("AVAILABLE", "TAKEN", "ERROR"):
        print(f"Total {key.title()}: {counts[key]}")
    print(f"\nResults saved to: {out}")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
