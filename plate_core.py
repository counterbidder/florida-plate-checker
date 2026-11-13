"""Core logic for Florida Plate Checker. No UI code lives here, so both the
GUI (plate_checker_gui.py) and the console version (plate_checker_cli.py)
share exactly the same scanning engine."""

import itertools
import os
import random
import re
import string
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

APP_NAME = "Florida Plate Checker"
APP_VERSION = "1.0.0"

SERVICE_URL = "https://services.flhsmv.gov/MVCheckPersonalPlate/"
MAX_POOL = 1_000_000  # refuse patterns bigger than this (memory safety)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-CH-UA": '"Not-A.Brand";v="99", "Google Chrome";v="157", "Chromium";v="157"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Origin": "https://services.flhsmv.gov",
    "Referer": SERVICE_URL,
    "Content-Type": "application/x-www-form-urlencoded",
    "Connection": "keep-alive",
}


# --------------------------------------------------------------------------
# Paths (work both as a .py script and as a PyInstaller .exe)
# --------------------------------------------------------------------------
def app_dir():
    """Folder containing the .exe (frozen) or this script (normal Python)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DICTIONARY_FILE = os.path.join(app_dir(), "plate_dictionary.txt")


def results_dir():
    """A writable 'results' folder: next to the app if possible, otherwise
    in Documents (e.g. if the app was installed somewhere read-only)."""
    candidates = (
        app_dir(),
        os.path.join(os.path.expanduser("~"), "Documents", "FloridaPlateChecker"),
    )
    for base in candidates:
        path = os.path.join(base, "results")
        try:
            os.makedirs(path, exist_ok=True)
            probe = os.path.join(path, ".write_test")
            open(probe, "w").close()
            os.remove(probe)
            return path
        except OSError:
            continue
    return os.getcwd()


# --------------------------------------------------------------------------
# Building the list of plates to check
# --------------------------------------------------------------------------
def load_dictionary(min_len=1, max_len=7, path=None):
    """Words from the dictionary file: A-Z/0-9 only, uppercased, de-duplicated,
    filtered by length. Raises FileNotFoundError if the file is missing."""
    path = path or DICTIONARY_FILE
    seen, words = set(), []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            word = line.strip().upper()
            if (word and word not in seen and re.fullmatch(r"[A-Z0-9]+", word)
                    and min_len <= len(word) <= max_len):
                seen.add(word)
                words.append(word)
    return words


def clean_pattern(raw, default="LL"):
    pattern = "".join(c for c in raw.upper() if c in "LD")
    return pattern or default


def pattern_size(pattern):
    return 26 ** pattern.count("L") * 10 ** pattern.count("D")


def generate_pattern_plates(pattern):
    """Every plate matching a pattern, e.g. 'LLD' = 2 letters then a digit."""
    pattern = clean_pattern(pattern)
    if len(pattern) > 7:
        raise ValueError("Florida plates have at most 7 characters.")
    if pattern_size(pattern) > MAX_POOL:
        raise ValueError(
            f"Pattern '{pattern}' has {pattern_size(pattern):,} combinations, "
            f"which is more than the {MAX_POOL:,} limit. Use a shorter pattern "
            f"or the dictionary."
        )
    pools = [string.ascii_uppercase if c == "L" else string.digits for c in pattern]
    return ["".join(combo) for combo in itertools.product(*pools)]


def parse_count(text, maximum):
    """'all' / blank -> maximum; a number -> clamped to 1..maximum.
    Raises ValueError for anything else."""
    text = (text or "").strip().lower()
    if text in ("", "all"):
        return maximum
    return max(1, min(int(text), maximum))


def select_plates(pool, count, randomize):
    count = max(1, min(count, len(pool)))
    return random.sample(pool, count) if randomize else pool[:count]


# --------------------------------------------------------------------------
# Talking to the DHSMV site
# --------------------------------------------------------------------------
def extract_tokens(html):
    """All hidden ASP.NET form fields (__VIEWSTATE etc.) as a dict."""
    tokens = {}
    p1 = re.compile(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\'][^>]*/?>', re.I)
    p2 = re.compile(r'<input[^>]*type=["\']hidden["\'][^>]*value=["\']([^"\']*)["\'][^>]*name=["\']([^"\']+)["\'][^>]*/?>', re.I)
    for m in p1.finditer(html):
        tokens[m.group(1)] = m.group(2)
    for m in p2.finditer(html):
        tokens[m.group(2)] = m.group(1)
    return tokens


def refresh_session():
    """Fresh requests session + form tokens. Returns (session, tokens);
    tokens is None if the site couldn't be reached or looked blocked."""
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        response = session.get(SERVICE_URL, timeout=15)
        response.raise_for_status()
        if "Personalized License Plate Check" not in response.text:
            return session, None
        return session, extract_tokens(response.text)
    except requests.RequestException:
        return session, None


def check_plate(plate, session, tokens):
    """Returns 'AVAILABLE', 'TAKEN' or 'ERROR'."""
    if not tokens:
        return "ERROR"
    payload = {
        "__VIEWSTATE": tokens.get("__VIEWSTATE", ""),
        "__VIEWSTATEGENERATOR": tokens.get("__VIEWSTATEGENERATOR", ""),
        "__EVENTVALIDATION": tokens.get("__EVENTVALIDATION", ""),
        "ctl00$MainContent$txtInputRowOne": plate,
        "ctl00$MainContent$txtInputRowTwo": "",
        "ctl00$MainContent$txtInputRowThree": "",
        "ctl00$MainContent$txtInputRowFour": "",
        "ctl00$MainContent$txtInputRowFive": "",
        "ctl00$MainContent$btnSubmit": "Submit",
    }
    try:
        response = session.post(SERVICE_URL, data=payload, timeout=10)
        if response.status_code != 200:
            return "ERROR"
        text = response.text
        if "AVAILABLE" in text and "NOT AVAILABLE" not in text:
            return "AVAILABLE"
        if "NOT AVAILABLE" in text:
            return "TAKEN"
        lowered = text.lower()
        if "already in use" in lowered or "reserved" in lowered:
            return "TAKEN"
        return "ERROR"
    except requests.RequestException:
        return "ERROR"


# --------------------------------------------------------------------------
# The scan loop
# --------------------------------------------------------------------------
def run_scan(plates, on_result, stop_event=None, on_status=None,
             workers=5, batch_size=25, batch_pause=(2.0, 5.0)):
    """Check plates in batches, with a fresh session per batch.

    on_result(plate, status)  called for every finished plate
    on_status(message)        optional progress / warning messages
    stop_event                threading.Event; set it to stop early
    """
    stop_event = stop_event or threading.Event()
    on_status = on_status or (lambda msg: None)
    batches = [plates[i:i + batch_size] for i in range(0, len(plates), batch_size)]

    for index, batch in enumerate(batches):
        if stop_event.is_set():
            break
        on_status(f"Batch {index + 1} of {len(batches)}")

        session, tokens = refresh_session()
        if not tokens:
            on_status("Couldn't get a session - retrying in 5 seconds...")
            stop_event.wait(5)
            session, tokens = refresh_session()
        if not tokens:
            on_status("Session failed - the site may be blocking requests.")
            for plate in batch:
                on_result(plate, "ERROR")
            stop_event.wait(5)
            continue

        def work(plate, session=session, tokens=tokens):
            if stop_event.is_set():
                return plate, None
            status = check_plate(plate, session, tokens)
            time.sleep(random.uniform(0.05, 0.1))
            return plate, status

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {pool.submit(work, p): p for p in batch}
            for future in as_completed(futures):
                try:
                    plate, status = future.result()
                except Exception:
                    plate, status = futures[future], "ERROR"
                if status is not None:
                    on_result(plate, status)

        if index < len(batches) - 1 and not stop_event.is_set():
            stop_event.wait(random.uniform(*batch_pause))
