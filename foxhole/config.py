import os
import sys
from pathlib import Path

MODELSPEC = "sentence-transformers/all-MiniLM-L6-v2"

if sys.platform.startswith("linux"):
    DATADIR = Path.home() / ".local" / "share" / "foxhole"
    MANIFESTDIR = Path.home() / ".mozilla" / "native-messaging-hosts"

elif sys.platform == "darwin":
    DATADIR = Path.home() / "Library" / "Application Support" / "foxhole"
    MANIFESTDIR = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Mozilla"
        / "NativeMessagingHosts"
    )

elif sys.platform == "win32":
    localappdata = os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    DATADIR = Path(localappdata) / "foxhole"
    MANIFESTDIR = (
        Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming")
        / "Mozilla"
        / "NativeMessagingHosts"
    )

else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")

DATADIR = DATADIR.expanduser().resolve()
MANIFESTDIR = MANIFESTDIR.expanduser().resolve()

DOCPATH = (DATADIR / "doc.db").expanduser().resolve()
VECPATH = (DATADIR / "vec.chroma").expanduser().resolve()

ignore_list_path = DATADIR / "IGNORE"
ignore_list_path.touch(exist_ok=True)
IGNORE_LIST = ignore_list_path.read_text().splitlines()

TEST_QUERIES = [
    "superman",
    "machine learning",
]
