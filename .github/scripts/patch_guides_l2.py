"""Add the Level 2 overview graphic to every leader's existing Ambassador guide.

Reads the block from Bob's master guide (start/index.html) and inserts it into
each leader repo's start/index.html, right after the Level 2 intro paragraph.
Leaders whose guide already has it, or has no guide yet, are skipped.
Env: LEADER_REPOS_TOKEN, DRY_RUN ("true" to report only).
"""
import os, json, base64, urllib.request, urllib.error

TOKEN = os.environ["LEADER_REPOS_TOKEN"]
DRY = os.environ.get("DRY_RUN", "true").lower() == "true"
OWNER = "bobfairfield"
ANCHOR = "Ambassadors do not earn compensation for recruiting or sponsoring.</p>\n"

master = open("start/index.html", encoding="utf-8").read()
a = master.index('  <div class="l2map"')
b = master.index("</style>", a) + len("</style>\n")
BLOCK = master[a:b]

def api(method, path, body=None):
    req = urllib.request.Request("https://api.github.com" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {}

people = json.load(open("_library-tools/participants.json"))
done = skipped = 0
problems = []
for p in people:
    repo = p["slug"] + "-landing"
    code, f = api("GET", f"/repos/{OWNER}/{repo}/contents/start/index.html")
    if code == 404:
        print(f"skip  {repo}: no guide yet"); skipped += 1; continue
    if code != 200:
        problems.append(f"{repo}: could not read the guide (HTTP {code})"); continue
    text = base64.b64decode(f["content"]).decode("utf-8")
    if "l2map" in text:
        print(f"skip  {repo}: already has it"); skipped += 1; continue
    if text.count(ANCHOR) != 1:
        problems.append(f"{repo}: Level 2 paragraph not found exactly once"); continue
    new = text.replace(ANCHOR, ANCHOR + BLOCK)
    if DRY:
        print(f"would patch {repo}"); done += 1; continue
    code, _ = api("PUT", f"/repos/{OWNER}/{repo}/contents/start/index.html", {
        "message": "Add Level 2 overview to the Ambassador guide",
        "content": base64.b64encode(new.encode("utf-8")).decode(),
        "sha": f["sha"]})
    if code in (200, 201):
        print(f"patched {repo}"); done += 1
    else:
        problems.append(f"{repo}: save failed (HTTP {code})")
print(f"\n{'Would patch' if DRY else 'Patched'} {done}, skipped {skipped}, problems {len(problems)}")
for x in problems: print("PROBLEM", x)
if problems: raise SystemExit(1)
