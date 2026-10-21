import sqlite3

con = sqlite3.connect(r'C:\Users\USER\.omniroute\storage.sqlite')
cur = con.cursor()

print("=== LOGS AROUND 04:26 ===")
rows = cur.execute("SELECT timestamp, path, requested_model, model, status, error_summary FROM call_logs WHERE timestamp LIKE '%04:26%' OR timestamp LIKE '%04:27%'").fetchall()
for r in rows:
    print(r)

print("\n=== MODEL ALIASES IN KEY_VALUE ===")
rows = cur.execute("SELECT key, value FROM key_value WHERE namespace='modelAliases'").fetchall()
for r in rows:
    print(r)
