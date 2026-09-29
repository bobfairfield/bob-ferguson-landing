"""Render a leader's two Zombie Cell article PDFs.

Usage: python3 render_leader_pdfs.py <repo_slug>

Reads the leader's published article pages straight from their repo (available the
moment the pipeline commits them, before GitHub Pages finishes building), prints each
to PDF in Chromium exactly as the existing leader PDFs were made, and writes
leader-pdfs/<repo_slug>/Zombie-Cell-Problem.pdf and Zombie-Cell-Problem-Short.pdf.
"""
import os, sys, time, urllib.request
from playwright.sync_api import sync_playwright

OWNER = "bobfairfield"
# (page, pdf file, print scale). The one-minute version prints at 85% so it fits one
# page, matching every leader PDF made before this was automated.
ARTICLES = [("zombie-cells", "Zombie-Cell-Problem.pdf", 1.0),
            ("zombie-cells-short", "Zombie-Cell-Problem-Short.pdf", 0.85)]


def fetch(url, tries=10):
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{url}?t={int(time.time())}", headers={"Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"  waiting for {url} ({e})")
            time.sleep(15)


def main(repo_slug):
    out_dir = os.path.join("leader-pdfs", repo_slug)
    os.makedirs(out_dir, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for slug, pdf_name, scale in ARTICLES:
            src = fetch(f"https://raw.githubusercontent.com/{OWNER}/{repo_slug}/main/{slug}/index.html")
            if "Shared by" not in src:
                raise SystemExit(f"{repo_slug}/{slug} is not a personalized article page")
            page = browser.new_page()
            page.set_content(src, wait_until="networkidle")
            page.emulate_media(media="print")
            page.pdf(path=os.path.join(out_dir, pdf_name), prefer_css_page_size=True,
                     print_background=True, scale=scale)
            page.close()
            print(f"  rendered {out_dir}/{pdf_name}")
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1])
