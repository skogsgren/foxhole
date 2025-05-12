import argparse
import sqlite3
import tkinter as tk
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-i", type=Path, required=True, help="Path to input database")
parser.add_argument("-o", type=Path, required=True, help="Path to output database")
args = parser.parse_args()

out_path = args.o
input_conn = sqlite3.connect(args.i)
input_conn.row_factory = sqlite3.Row
input_cur = input_conn.cursor()
input_cur.execute("SELECT * FROM results")
rows = list(input_cur.fetchall())

if not out_path.exists():
    out_conn = sqlite3.connect(out_path)
    out_conn.execute("""
        CREATE TABLE annotations (
            query TEXT,
            system TEXT,
            id TEXT,
            title TEXT,
            text TEXT,
            url TEXT,
            rank INTEGER,
            label TEXT,
            annotation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            UNIQUE (query, system, id)
        )
    """)
    out_conn.commit()
    out_conn.close()

output_conn = sqlite3.connect(out_path)
output_conn.row_factory = sqlite3.Row
output_cur = output_conn.cursor()
output_cur.execute("SELECT query, system, id FROM annotations")
existing_keys = set((r["query"], r["system"], r["id"]) for r in output_cur.fetchall())

rows = [r for r in rows if (r["query"], r["system"], r["id"]) not in existing_keys]
current = 0
labels = []


def next_entry(label):
    global current
    row = rows[current]
    row = dict(row)
    row["label"] = label
    output_cur.execute(
        """
        INSERT INTO annotations (query, system, id, title, text, url, rank, label)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            row["query"],
            row["system"],
            row["id"],
            row["title"],
            row["text"],
            row["url"],
            row["rank"],
            row["label"],
        ),
    )
    output_conn.commit()
    current += 1
    if current >= len(rows):
        root.destroy()
        return
    update_display()


def update_display():
    id_label.config(text=f"ID: {rows[current]['id']}")
    query_label.config(text=f"Query: {rows[current]['query']}")
    title_label.config(text=f"Title: {rows[current]['title']}")
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, rows[current]["text"])
    progress_label.config(text=f"{current} / {len(rows)}")


root = tk.Tk()
root.title("SQLite Annotator")

header_frame = tk.Frame(root)
header_frame.pack(fill="x")

id_label = tk.Label(header_frame, text="", anchor="w")
id_label.pack(fill="x")

query_label = tk.Label(header_frame, text="", anchor="w")
query_label.pack(fill="x")

title_label = tk.Label(header_frame, text="", anchor="w")
title_label.pack(fill="x")

text_frame = tk.Frame(root)
text_frame.pack(fill="both", expand=True)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side="right", fill="y")

text_box = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set)
text_box.pack(fill="both", expand=True)
scrollbar.config(command=text_box.yview)

button_frame = tk.Frame(root)
button_frame.pack()

progress_label = tk.Label(root, text="")
progress_label.pack()

tk.Button(button_frame, text="Not relevant", command=lambda: next_entry(0)).pack(
tk.Button(button_frame, text="(0) Not relevant", command=lambda: next_entry(0)).pack(
    side="left"
)
tk.Button(button_frame, text="(1) Relevant", command=lambda: next_entry(1)).pack(
    side="left"
)
tk.Button(button_frame, text="(2) Highly relevant", command=lambda: next_entry(2)).pack(
    side="left"
)

update_display()
root.mainloop()
