import urllib.request, json
resp = urllib.request.urlopen("http://127.0.0.1:5000/api/jobs", timeout=5)
jobs = json.loads(resp.read())
if not jobs:
    print("No jobs in queue yet")
for jid, j in jobs.items():
    status = j.get("status", "?")
    topic = j.get("topic", "?")
    progress = j.get("progress", 0)
    step = j.get("step", "")
    error = j.get("error", "")
    print(f"[{status}] {topic} — {progress}% — {step} {error}")
    logs = j.get("logs", [])
    for l in logs[-5:]:
        print("  LOG:", l)
