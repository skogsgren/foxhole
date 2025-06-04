# Foxhole - Local Fulltext Search For Firefox History

Local-first tool to store and search your Firefox browsing history in full text.

**Motivation**: browsers only store URL and title in the history. But what if
you don't remember those, only the _content_ of the website? This tools enables
full text search for your browser history.

It works like this: Every time a tab is loaded, the content of that website is
sent using a local host connection, which stores the content in an SQLITE
database. You can then search using either the built-in SQLITE search, `grep`
(see [grepping](#grepping) below), or whatever other method you want.

- **Will this save my bank-statements?** Not if you blacklist the bank's
  webpage (see the notes regarding ignoring webpages under Installation). I
  mean, who am I to judge? Maybe you want that. If you accidentally save
  information you can prune it using the built-in `foxhole-prune` command (see
  section below).

- **I don't trust you.** Me neither. However, the codebase is minimal, and I
  recommend looking through what happens when `foxhole` saves the information.
  The webextension is [here](webextension/background.js) and the native host
  connector is [here](foxhole/_native/host.py).

- **Why SQLITE instead of local storage?** Extensions like
  [Falcon](https://github.com/cennoxx/falcon) utilize local storage, and
  provides a nice frontend for search directly from Firefox.  However, local
  storage can be a hassle. What if you want to transfer data without
  transferring the Firefox profile? What if you want to _do_ something external
  with the browser history? Good luck getting it out from local storage. Here,
  you only have a standard run-of-the-mill SQLITE file.

- **Why not embedding search?** Initially the extension was created with
  embeddings in mind, however, during evaluation the performance was not worth
  the cost in inference time and storage increase. With this implementation you
  can simply do multiple searches, trying different keywords instead.

- **Why can't I just install an extension? Why do I have to install a python
  script as well?** Since browsers are sandboxed, host native messaging is the
  only way to get the data from the browser outside the local machine. This is
  good, seeing as it's harder to write malicious extensions. It does mean
  extension like this are a bit cumbersome to install.

## Installation

```
pipx install foxhole
foxhole-install
```

Then install the Firefox extension.

In your data directory a file called `IGNORE` will be created during
installation. Put urls you don't want saved in here, or (imo) most importantly
those pages you keep returning to often like your search engine which will not
provide highly relevant search results for this type of browser history search
(ideally we only want "content" sites in our index).

## Usage

### Search

Here's an example search:

```
foxhole android phone with buttons
```

Which in my case returns:

```
1628    https://www.reddit.com/r/dumbphones/comments/1dmnm2v/my_ideal_qin_f21_pro_setup/        My ideal Qin F21 Pro setup : r/dumbphones
1626    https://github.com/AlikornSause/Notes-on-QIN-F21-PRO#keypad-and-buttons AlikornSause/Notes-on-QIN-F21-PRO: My notes on the Duoqin F21 pro dumb/feature phone
1646    https://github.com/AlikornSause/Notes-on-QIN-F21-PRO?tab=readme-ov-file#hardware-versions       AlikornSause/Notes-on-QIN-F21-PRO: My notes on the Duoqin F21 pro dumb/feature phone
867     https://xdaforums.com/t/app-4-2-t9-launcher.3002969/    [APP][4.2+] T9 Launcher | XDA Forums
1625    https://xdaforums.com/t/guide-information-guide-for-qin-f21-pro.4726912/        [GUIDE][INFORMATION] Guide for Qin F21 Pro | XDA Forums
752     https://www.reddit.com/r/dumbphones/comments/11zqtl6/my_thoughts_about_the_qin_f21_pro/ My thoughts about the Qin F21 Pro : r/dumbphones
1970    https://old.reddit.com/r/ereader/comments/1018vlb/am_i_missing_something_or_is_an_android_ereader/      Am I missing something or is an Android eReader generally a "bad" idea? : ereader
2859    https://old.reddit.com/r/eink/comments/xuvlwc/budget_eink_smart_devices/        Budget E-Ink Smart Devices : eink
763     https://github.com/bkerler/mtkclient    bkerler/mtkclient: MTK reverse engineering and flash tool
4507    https://shkspr.mobi/blog/2025/05/whatever-happened-to-cheap-ereaders/   Whatever happened to cheap eReaders? – Terence Eden’s Blog
```

FTS5 supports additional search syntax to refine queries. For the complete set
of options, see the [FTS5 Documentation](https://sqlite.org/fts5.html). Key
operators include:

- `AND`: Matches documents containing both terms.  
  **Example**: `foxhole perry AND white` returns documents that include
  both "perry" and "white".

- `OR`: Matches documents containing either term.  
  **Example**: `foxhole perry OR white` returns documents that include
  either "perry" or "white".

- `NOT`: Excludes documents containing the specified term.  
  **Example**: `foxhole perry NOT white` returns documents that include
  "perry" but exclude "white".

- `"<phrase>"`: Matches exact phrases.  
  **Example**: `foxhole "perry white"` returns documents containing the
  exact phrase "perry white", not just the individual terms.

### Grepping

You can also use `grep`/`awk` in a UNIX fashion. The included `foxhole-ls`
command lists all documents as tab-separated rows like (id, url, title, text).
The text column is stripped for new lines to enable grepping.

For example, if you'd like to print the ids, url and title of all documents
containing "perry white" without regards for case:

```
foxhole-ls | grep -i "perry white" | cut -f 1,2,3
```

Which for my current document database returns:

```
9        https://smallville.fandom.com/wiki/Clark_Kent   Clark Kent | Smallville Wiki | Fandom
336      https://smallville.fandom.com/wiki/Jonathan_Kent        Jonathan Kent | Smallville Wiki | Fandom
337      https://smallville.fandom.com/wiki/Martha_Kent          Martha Kent | Smallville Wiki | Fandom
898      https://en.wikipedia.org/wiki/Lana_Lang         Lana Lang - Wikipedia
2103     https://smallville.fandom.com/wiki/Martha_Kent#Smallville_TV_Series     Martha Kent | Smallville Wiki | Fandom
4166     https://en.wikipedia.org/wiki/Perry_White       Perry White - Wikipedia
4167     https://en.wikipedia.org/wiki/Lane_Smith        Lane Smith - Wikipedia
4168     https://en.wikipedia.org/wiki/Jonathan_and_Martha_Kent          Jonathan and Martha Kent - Wikipedia
```

This does take about ~1s per query since the SQLITE API for Python isn't super
fast for reads. If you have SQLITE installed you can do blazingly fast grepping
using for example (if you're on Linux/Mac):

```
sqlite3 ~/.local/share/foxhole/doc.db "SELECT id,url,title,text FROM pages;" | \
    grep -i "perry white" | \
    cut -f 1,2,3 -d "|"
```

Which would be easy to add to your `bash_aliases`.

If you're on Windows/Mac/Linux and the command above isn't working you might
have another location for your data directory. Print that out by running
`foxhole -h`

## Development Installation

```
pip3 install -e .
```

For Windows, make sure that `python3` is installed from the Python website and
is added to PATH.

Install the host connection using:

```
foxhole-install
```

Finally, install the web-extension by going to
[`about:debugging#/runtime/this-firefox`](about:debugging#/runtime/this-firefox)
in Firefox, and adding `manifest.json` using "Load temporary Add-on".
