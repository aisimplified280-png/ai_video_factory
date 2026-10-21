import sqlite3

con = sqlite3.connect(r'C:\Users\USER\.omniroute\storage.sqlite')
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    columns = [col[1] for col in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"Table {t} columns: {columns}")
