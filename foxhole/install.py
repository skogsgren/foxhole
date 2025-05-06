import json
import os
import shutil
import stat
from pathlib import Path

from .config import DATADIR, MANIFESTDIR


def install_native_host():
    DATADIR.mkdir(parents=True, exist_ok=True)

    base_dir = Path(__file__).parent
    shutil.copy2(base_dir / "_native" / "host.py", DATADIR / "host.py")
    shutil.copy2(base_dir / "config.py", DATADIR / "config.py")
    mode = os.stat(DATADIR / "host.py").st_mode
    os.chmod(DATADIR / "host.py", mode | stat.S_IXUSR)

    MANIFESTDIR.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFESTDIR / "foxhole_host.json"
    manifest = {
        "name": "foxhole_host",
        "description": "foxhole Native Messaging Host",
        "path": str(DATADIR / "host.py"),
        "type": "stdio",
        "allowed_extensions": ["foxhole@localhost"],
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully installed native messaging host to {MANIFESTDIR}")
    print(f"foxhole DATADIR={str(DATADIR)}")
