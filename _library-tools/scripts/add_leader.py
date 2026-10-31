"""Add a leader to participants.json if missing.

Usage: python add_leader.py <repo_slug e.g. nahom-abegaze-landing> --name "Nahom Abegaze" --first Nahom --email x@y.com --short nahom [--leader-dir DIR] [--tools yes|no]
The leader's CNAME file (if any) sets the landing address and the video base.
"""
import os, sys, json, argparse
TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ap = argparse.ArgumentParser()
ap.add_argument("repo_slug"); ap.add_argument("--name", required=True); ap.add_argument("--first")
ap.add_argument("--email", required=True); ap.add_argument("--short", required=True)
ap.add_argument("--leader-dir"); ap.add_argument("--tools", default="yes")
a = ap.parse_args()
slug = a.repo_slug[:-len("-landing")] if a.repo_slug.endswith("-landing") else a.repo_slug
path = os.path.join(TOOLS, "participants.json")
people = json.load(open(path))
if any(x["slug"] == slug for x in people):
    print("already present:", slug); sys.exit(0)
cname = None
if a.leader_dir and os.path.exists(os.path.join(a.leader_dir, "CNAME")):
    cname = open(os.path.join(a.leader_dir, "CNAME")).read().strip()
    if cname.startswith("www."):
        cname = None  # www-only domains are not trusted for video hosting
landing = f"https://{cname}/" if cname else f"https://bobfairfield.github.io/{slug}-landing/"
prefix = a.name.replace(" ", "_")
people.append({
    "slug": slug, "display_name": a.name, "first": a.first or a.name.split()[0], "email": a.email,
    "landing_url": landing, "short_slug": a.short,
    "onscreen_url": f"bobfergusonlongevity.com/go/{a.short}", "link_text": f"bobfergusonlongevity.com/go/{a.short}",
    "link_url": f"https://bobfergusonlongevity.com/go/{a.short}",
    "article_base": landing, "video_base": landing + "library-videos/",
    "drive": {"article_base": landing, "files": a.tools == "yes", "prefix": prefix},
})
json.dump(people, open(path, "w"), indent=1)
print("added", slug)
