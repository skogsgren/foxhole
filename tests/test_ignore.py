from foxhole.prune import is_ignored

URLS = [
    "https://github.com/skogsgren/foxhole/issues",
    "https://github.com/skogsgren/dot-files",
    "https://docs.google.com",
    "https://google.com/search?jkkjasdkja",
    "https://github.com/skogsgren/foxhole/issues",
]


def test_ignore_fn():
    for url in URLS:
        print(url, is_ignored(url))


test_ignore_fn()
