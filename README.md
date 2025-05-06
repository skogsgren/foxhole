# Foxhole - Local Semantic Search For Firefox History

## DEVELOPMENT INSTALLATION

```
pip3 install -e .
```

For Windows, make sure that `python3` is installed from the Python website and
is added to PATH.

Install the host connection using:

```
foxhole-install
```

Finally, install the `webextension` by going to
[`about:debugging#/runtime/this-firefox`](about:debugging#/runtime/this-firefox)
in Firefox, and adding `manifest.json` using "Load temporary Add-on".
