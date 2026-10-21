import sqlite3

con = sqlite3.connect(r'C:\Users\USER\.omniroute\storage.sqlite')
cur = con.cursor()

print("=== KEY_VALUE (non-secret namespaces/keys) ===")
rows = cur.execute("SELECT namespace, key, substr(value, 1, 100) FROM key_value WHERE key NOT LIKE '%key%' AND key NOT LIKE '%token%' AND key NOT LIKE '%secret%'").fetchall()
for r in rows:
    print(r)

print("\n=== COMBOS ===")
rows = cur.execute("SELECT id, name, sort_order FROM combos").fetchall()
for r in rows:
    print(r)

print("\n=== MODEL_COMBO_MAPPINGS ===")
rows = cur.execute("SELECT id, pattern, combo_id, priority, enabled, description FROM model_combo_mappings").fetchall()
for r in rows:
    print(r)

print("\n=== PROVIDER_CONNECTIONS (NON-SENSITIVE FIELDS ONLY) ===")
rows = cur.execute("SELECT id, provider, auth_type, name, priority, is_active, default_model FROM provider_connections").fetchall()
for r in rows:
    print(r)

print("\n=== PROVIDER_NODES ===")
rows = cur.execute("SELECT id, type, name, prefix, api_type, base_url FROM provider_nodes").fetchall()
for r in rows:
    print(r)

print("\n=== RECENT CALL LOGS (last 5) ===")
rows = cur.execute("SELECT id, timestamp, model, requested_model, provider, status, error_summary, error_type FROM call_logs ORDER BY id DESC LIMIT 5").fetchall()
for r in rows:
    print(r)
