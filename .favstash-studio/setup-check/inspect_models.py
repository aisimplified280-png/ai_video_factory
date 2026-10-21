import sqlite3
import json

con = sqlite3.connect(r'C:\Users\USER\.omniroute\storage.sqlite')
cur = con.cursor()

print("=== ALL MODEL ALIASES ===")
rows = cur.execute("SELECT key, value FROM key_value WHERE namespace='modelAliases'").fetchall()
for k, v in rows:
    print(f"  {k} -> {v}")

print("\n=== MODELS IN AGY SYNCED LIST ===")
synced = cur.execute("SELECT key, value FROM key_value WHERE namespace='syncedAvailableModels'").fetchall()
for k, v in synced:
    try:
        data = json.loads(v)
        models = [m.get('id') for m in data if isinstance(m, dict)]
        print(f"Connection {k}: {models}")
    except Exception as e:
        print(f"Error parsing {k}: {e}")

print("\n=== SEARCH CALL LOGS FOR 'gemini-3.1-pro-preview' ===")
rows = cur.execute("SELECT id, timestamp, model, requested_model, provider, status, error_summary, error_type FROM call_logs WHERE requested_model LIKE '%gemini-3.1-pro%' OR model LIKE '%gemini-3.1-pro%' OR error_summary LIKE '%gemini-3.1-pro%' ORDER BY id DESC LIMIT 10").fetchall()
for r in rows:
    print(r)
