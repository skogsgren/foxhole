import json
import os
import shutil
import stat
import sys
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
    if sys.platform == "win32":
        import winreg

        manifest["path"] = str(DATADIR / "host.bat")
        bat_file = f"""@echo off
python -u \"{str(DATADIR / "host.py")}\"
        """
        with open(manifest_path, "w") as mf, open(DATADIR / "host.bat", "w") as bf:
            json.dump(manifest, mf)
            bf.write(bat_file)
        print("Successfully altered manifest to use .bat script instead")

        key_path = "Software\\Mozilla\\NativeMessagingHosts\\foxhole_host"
        key_value = str(MANIFESTDIR / "foxhole_host.json")
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, key_value)
        winreg.CloseKey(key)
        print(f"Successfully updated key for {key_path}")

    print(f"Successfully installed native messaging host to {MANIFESTDIR}")
    print(f"foxhole DATADIR={str(DATADIR)}")
