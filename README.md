# Foxhole - Local Semantic Search For Firefox History

## DEVELOPMENT INSTALLATION

Tested on Debian 12, so YMMV

```
python3 -m venv /path/to/venv
source /path/to/venv/bin/activate
pip3 install .
```

Then install the `webextension` by going to
[`about:debugging#/runtime/this-firefox`](about:debugging#/runtime/this-firefox)
in Firefox, and adding `manifest.json` using "Load temporary Add-on".
