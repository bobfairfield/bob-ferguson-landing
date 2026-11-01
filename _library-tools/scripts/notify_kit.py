"""Tell Apps Script the library is live (or broke) so it sends the leader's one kit email.

Usage: python notify_kit.py live|failed
Reads: KIT_MAIL_URL, KIT_MAIL_KEY, L_EMAIL, L_NAME, REPO_SLUG, RUN_URL (all set by the workflow).
A manual run for a leader who has no kit waiting is harmless: Apps Script sends nothing.
"""
import json, os, sys, urllib.request

status = sys.argv[1] if len(sys.argv) > 1 else "live"
url, key = os.environ.get("KIT_MAIL_URL", ""), os.environ.get("KIT_MAIL_KEY", "")
if not url or not key:
    print("KIT_MAIL_URL / KIT_MAIL_KEY not set: no email step")
    sys.exit(0)
body = {
    "key": key, "status": status,
    "leader_email": os.environ.get("L_EMAIL", ""), "leader_name": os.environ.get("L_NAME", ""),
    "repo_slug": os.environ.get("REPO_SLUG", ""), "run_url": os.environ.get("RUN_URL", ""),
}
if status == "failed":
    body["error"] = "The library workflow stopped before finishing."
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print("kit email step:", r.read().decode()[:300])
except Exception as e:
    print("kit email step could not be reached:", e)
    sys.exit(1 if status == "live" else 0)
