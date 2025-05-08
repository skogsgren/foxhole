# Foxhole - Local Semantic Search For Firefox History

Local-first tool to semantically search and explore your Firefox browsing
history using embeddings and natural language. Like a search engine but for
your browser history!

## Documentation

### `IGNORE`

In your data directory a file called `IGNORE` will be created during
installation. Put urls you don't want saved in here, or (imo) most importantly
those pages you keep returning to often like your search engine which will not
provide highly relevant search results for this type of browser history search
(ideally we only want "content" sites in our index).

## DEVELOPMENT INSTALLATION

```
pip3 install -e .[dev]
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

See the `tests` for pytest formatted tests for each respective component, which
are run using: `pytest -s -v file_to_test` or just `pytest -s -v` to run all
the tests in the folder.
