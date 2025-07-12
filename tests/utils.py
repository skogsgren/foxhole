import sqlite3


def _create_dummy_pages_table(path, rows):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("CREATE TABLE pages (id TEXT, url TEXT, title TEXT, text TEXT)")
    c.executemany("INSERT INTO pages VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


def _create_dummy_fts_table(path, rows):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("CREATE VIRTUAL TABLE pages_fts USING fts5(id, url, title)")
    c.execute("CREATE TABLE pages (id TEXT, url TEXT, title TEXT)")
    c.executemany("INSERT INTO pages_fts VALUES (?, ?, ?)", rows)
    c.executemany("INSERT INTO pages VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()
