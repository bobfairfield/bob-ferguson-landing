"""Generate each participant's own Pathway page and write it into their repo.

Pathway is the diagnostic a brand new Ambassador takes before the guide:
fourteen behavioural questions, out comes a starting pathway, a first 30 days
paced to the hours they actually have, and a short brief for whoever is
coaching them. Each participant gets their own copy at <their address>/pathway/
so the coaching brief and the help row point at them, not at Bob.

Reads: _library-tools/participants.json, _library-tools/pathway/template.html
Writes: pathway/index.html in each bobfairfield/<slug>-landing repo,
        and pathway/index.html in this repo for Bob's own address.

Env: LEADER_REPOS_TOKEN, DRY_RUN ("true" to report only, the default),
     ONLY (one slug, optional), SKIP (comma separated slugs, optional).

Run it from the Actions tab with dry run on first.
"""
import os, re, json, base64, urllib.request, urllib.error

TOKEN = os.environ["LEADER_REPOS_TOKEN"]
DRY   = os.environ.get("DRY_RUN", "true").lower() == "true"
ONLY  = os.environ.get("ONLY", "").strip()
SKIP  = {x.strip() for x in os.environ.get("SKIP", "").split(",") if x.strip()}
OWNER = "bobfairfield"

# Toni's repo was created by hand before the <slug>-landing convention existed.
REPO_OVERRIDES = {"toni-parker": "Toni-Parker"}

TOOLS    = "_library-tools"
TEMPLATE = open(os.path.join(TOOLS, "pathway", "template.html"), encoding="utf-8").read()
PEOPLE   = json.load(open(os.path.join(TOOLS, "participants.json"), encoding="utf-8"))


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


def api_raw(path):
    """Raw file contents. The JSON contents API returns an empty body for files
    over 1MB, and several landing pages are larger than that, so read them raw."""
    req = urllib.request.Request("https://api.github.com" + path)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github.raw")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, None


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def pretty_phone(raw):
    """+19132086357 becomes (913) 208-6357. Anything unexpected is returned as is."""
    d = re.sub(r"\D", "", raw or "")
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d) == 10 else (raw or "")


def read_landing(repo):
    """Their landing page, for the brand name and the phone number on it."""
    return api_raw(f"/repos/{OWNER}/{repo}/contents/index.html")


def brand_from(html, fallback):
    m = re.search(r"<title>(.*?)</title>", html or "", re.S)
    if m and "|" in m.group(1):
        return m.group(1).rsplit("|", 1)[1].strip()
    return fallback


def phone_from(html):
    m = re.search(r'tel:([+0-9() .\-]{7,20})', html or "")
    return pretty_phone(m.group(1)) if m else ""


def build(person, brand, phone):
    name    = person["display_name"]
    email   = person["email"]
    landing = person["landing_url"].rstrip("/") + "/"
    start   = landing + "start/"

    bits = [f'Anything here that does not make sense, or does not fit your situation, '
            f'is worth a short conversation. Email {esc(name)} at '
            f'<a href="mailto:{esc(email)}" style="color:var(--wine)">{esc(email)}</a>']
    if phone:
        bits.append(f'or call or text <a href="tel:{re.sub(r"[^0-9+]", "", phone)}" '
                    f'style="color:var(--wine)">{esc(phone)}</a>')
    line = ", ".join(bits) + "."

    out = TEMPLATE
    for token, value in (
        ("{{NAME}}",        esc(name)),
        ("{{BRAND}}",       esc(brand)),
        ("{{EMAIL}}",       esc(email)),
        ("{{START_URL}}",   start),
        ("{{HELP_LINE}}",   line),
    ):
        out = out.replace(token, value)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise SystemExit(f"{person['slug']}: template tokens left unfilled: {set(left)}")
    return out


def put(repo, path, text, message):
    code, f = api("GET", f"/repos/{OWNER}/{repo}/contents/{path}")
    if code == 200 and base64.b64decode(f["content"]).decode("utf-8", "replace") == text:
        return "same"
    body = {"message": message,
            "content": base64.b64encode(text.encode("utf-8")).decode()}
    if code == 200:
        body["sha"] = f["sha"]
    code, _ = api("PUT", f"/repos/{OWNER}/{repo}/contents/{path}", body)
    return "ok" if code in (200, 201) else f"HTTP {code}"


done = skipped = 0
problems = []
for p in PEOPLE:
    slug = p["slug"]
    if ONLY and slug != ONLY:
        continue
    if slug in SKIP:
        print(f"skip  {slug}: in SKIP"); skipped += 1; continue

    repo = REPO_OVERRIDES.get(slug, slug + "-landing")
    code, html = read_landing(repo)
    if code == 404:
        print(f"skip  {slug}: no landing page repo"); skipped += 1; continue
    if html is None:
        problems.append(f"{slug}: could not read the landing page (HTTP {code})"); continue

    brand = brand_from(html, p["display_name"])
    phone = phone_from(html)
    page  = build(p, brand, phone)
    if not phone:
        print(f"note  {slug}: no phone on the landing page, email only")

    if DRY:
        print(f"would write {repo}/pathway/index.html  brand={brand!r} phone={phone or 'none'}")
        done += 1
        continue
    r = put(repo, "pathway/index.html", page, "Add the Pathway diagnostic")
    print(f"{r:>6}  {repo}/pathway/index.html")
    if r in ("ok", "same"):
        done += 1
    else:
        problems.append(f"{slug}: save failed ({r})")

print(f"\n{'Would write' if DRY else 'Wrote'} {done}, skipped {skipped}, problems {len(problems)}")
for x in problems:
    print("PROBLEM", x)
if problems:
    raise SystemExit(1)
