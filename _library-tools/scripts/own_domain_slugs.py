"""Print the slug of every leader whose landing page sits on their own address.

Those leaders host their own watch pages, so their pages have to be pushed into
their own repo. Everyone else is served from bobfergusonlongevity.com.

Usage: python own_domain_slugs.py [one-slug]
"""
import json, os, sys

TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
only = (sys.argv[1].strip() if len(sys.argv) > 1 else "")
for p in json.load(open(os.path.join(TOOLS, "participants.json"))):
    if "github.io" in p["landing_url"]:
        continue
    if only and p["slug"] != only:
        continue
    print(p["slug"])
