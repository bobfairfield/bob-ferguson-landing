#!/usr/bin/env python3
"""Builds each participant's personal Sharing Library page and short-link redirect pages.

Usage:  python3 build_library.py <output_dir>
Reads participants.json and series.json that sit next to this script.
Video files are expected at <output_dir>/library/<slug>/<series_id>/reel.mp4
"""
import json, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "site"
people = json.load(open(os.path.join(HERE, "participants.json")))
series = json.load(open(os.path.join(HERE, "series.json")))

FOOT_STAR = "*These statements have not been evaluated by the Food and Drug Administration. This product is not intended to diagnose, treat, cure, or prevent any disease."
FOOT_CARET = "^In a two-month study, Vivix+ increased VO2 max by 2.6 to 3.8 mL/(kg·min), equivalent to reversing 6.5 to 9.5 years of typical age-related decline, or 8 years on average."

CAPTIONS = {
 "series-01": {
  "reel":"The only longevity supplement shown to increase VO₂ max without exercise*. +3.2 points. 8 years of cellular aging^. Watch to the end, then see the details at {link}\n\n" + FOOT_STAR + "\n" + FOOT_CARET,
  "story": "{link}",
 }
}
STORY_NOTE = {"series-01": "3.2 points more VO₂ max. 8 years of cellular aging. No exercise.*",
 "series-02": "One happy lady's story.*"}
FOOT_STORY = "This is one person's experience. Individual results vary."
CAPTIONS["series-02"] = {
  "reel": "One happy lady's story, in her own words. Watch to the end, then see the details at {link}\n\n" + FOOT_STAR + "\n" + FOOT_STORY,
  "story": "{link}",
}

HOME = "https://bobfergusonlongevity.com"
PLAUSIBLE = '<script async src="https://plausible.io/js/pa-a3jZtwKU4Lx7RIBy_e41c.js"></script>\n<script>window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};plausible.init()</script>'


def own_domain(p):
    """True when the leader's landing page sits on their own address, not github.io."""
    return "github.io" not in p["landing_url"]


def watch_base(p):
    """Where this leader's watch pages live, as a full address ending in a slash."""
    if own_domain(p):
        return p["landing_url"]
    return f"{HOME}/go/{p['short_slug']}/"


def watch_url(p, s):
    return watch_base(p) + s["watch_slug"] + "/"


def video_url(p, s):
    if p.get("video_base"):
        return p["video_base"] + s["id"] + "/reel.mp4"
    return f"{HOME}/library/{p['slug']}/{s['id']}/reel.mp4"


def poster_url(s):
    return f"{HOME}/library/shared/" + s.get("poster", "poster-reel.jpg")


def preview_url(s):
    return f"{HOME}/previews/{s['watch_slug']}.jpg"


CSS = """
:root{--wine:#4F1026;--wine2:#6C1030;--gold:#C6974F;--cream:#F3EEE0;--card:#FBF8F1;--sage:#5B7A63;--ink:#3a1a26}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--cream);color:var(--ink);font-family:Calibri,Carlito,"Segoe UI",Arial,sans-serif;font-size:20px;line-height:1.5}
h1,h2,h3{font-family:Cambria,Caladea,Georgia,serif;color:var(--wine);line-height:1.2;margin:0 0 .4em}
h1{font-size:34px}h2{font-size:28px}h3{font-size:23px}
.wrap{max-width:720px;margin:0 auto;padding:20px 18px 60px}
.kicker{letter-spacing:.18em;text-transform:uppercase;font-size:14px;color:var(--gold);font-weight:700;margin:6px 0 10px}
.hero{padding:26px 0 8px}
.card{background:var(--card);border-radius:18px;padding:22px 20px;margin:18px 0;box-shadow:0 1px 0 rgba(79,16,38,.06)}
.steps{counter-reset:s;list-style:none;margin:10px 0 0;padding:0}
.steps li{counter-increment:s;position:relative;padding:6px 0 14px 58px;min-height:48px}
.steps li:before{content:counter(s);position:absolute;left:0;top:2px;width:42px;height:42px;border-radius:50%;background:var(--wine);color:#fff;font-family:Cambria,Georgia,serif;font-size:24px;text-align:center;line-height:42px}
.btn{display:block;width:100%;min-height:60px;border:0;border-radius:14px;background:var(--wine);color:#fff;font:700 21px Calibri,Carlito,Arial,sans-serif;padding:14px 18px;margin:10px 0 0;cursor:pointer;text-align:center;text-decoration:none}
.btn.alt{background:#fff;color:var(--wine);box-shadow:inset 0 0 0 2px var(--wine)}
.btn.small{min-height:48px;font-size:18px}
.btn:active{transform:scale(.99)}
.tag{display:inline-block;background:var(--gold);color:#fff;font-weight:700;font-size:14px;letter-spacing:.12em;padding:4px 10px;border-radius:99px;margin-left:8px;vertical-align:middle}
.fmt{border-top:1px solid rgba(79,16,38,.12);padding-top:20px;margin-top:20px}
.fmt:first-of-type{border-top:0;margin-top:8px}
video{width:100%;border-radius:14px;background:#2a0a16;display:block;max-height:70vh}
.note{font-size:17px;color:#6b4a56;margin:8px 0 0}
.status{font-size:18px;background:#fff;border-radius:12px;padding:12px 14px;margin:10px 0 0;display:none}
.cap{white-space:pre-wrap;font-size:17px;background:#fff;border-radius:12px;padding:14px;margin:10px 0 0;display:none}
details{margin:12px 0 0}
summary{cursor:pointer;font-weight:700;color:var(--wine);padding:10px 0;font-size:20px}
table{width:100%;border-collapse:collapse;font-size:19px}
td{padding:10px 8px;vertical-align:top;border-top:1px solid rgba(79,16,38,.12)}
td:first-child{font-weight:700;color:var(--wine);width:38%}
.linkbox{background:#fff;border-radius:12px;padding:12px 14px;word-break:break-all;font-size:18px;margin:8px 0 0}
.fine{font-size:15px;color:#6b4a56}
"""

JS = """
const D = JSON.parse(document.getElementById('data').textContent);
function $(s){return document.querySelector(s)}
async function copyText(t, btn){
  const old = btn.textContent;
  try{ await navigator.clipboard.writeText(t); }
  catch(e){ const ta=document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.focus(); ta.select(); try{document.execCommand('copy')}catch(_){}; document.body.removeChild(ta); }
  btn.textContent = btn.dataset.plain ? 'Copied! Now paste it into your email or text' : 'Copied! Now paste it into Facebook';
  setTimeout(()=>btn.textContent=old, 3500);
}
async function saveShare(url, name, statusId, btn){
  const st = document.getElementById(statusId); st.style.display='block';
  st.textContent = 'Getting your video ready. One moment...';
  try{
    const r = await fetch(url); const b = await r.blob();
    const f = new File([b], name, {type:'video/mp4'});
    if(navigator.canShare && navigator.canShare({files:[f]})){
      st.textContent = 'A menu is opening. Tap "Save Video" to keep it in your Photos, or tap Facebook to post it right now.';
      try{ await navigator.share({files:[f]}); st.textContent='Done. Your video is saved or shared. You can post it from Facebook now.'; return; }
      catch(e){ if(e && e.name==='AbortError'){ st.textContent='No problem. Tap the button again whenever you are ready.'; return; } }
    }
    const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=name; document.body.appendChild(a); a.click(); a.remove();
    st.innerHTML = 'Your video is downloading.<br><b>iPhone:</b> tap the arrow at the top right of Safari, tap your video, tap the Share icon (a square with an arrow), then tap Save Video.<br><b>Android or computer:</b> look in your Downloads folder or Gallery.';
  }catch(e){
    st.innerHTML = 'That did not work. Please tap and hold this link, then choose Download: <a href="'+url+'">'+name+'</a>';
  }
}
function toggleCap(id, btn){ const el=document.getElementById(id); const show = el.style.display!=='block'; el.style.display = show?'block':'none'; btn.textContent = show?'Hide this':'Show me again'; }
(function render(){
  const root = $('#series');
  D.series.forEach((s, si) => {
    const sec = document.createElement('section'); sec.className='card';
    let h = '<h2>'+s.title+(s.is_new?'<span class="tag">NEW</span>':'')+'</h2><p class="note">Added '+s.added+'. '+s.blurb+'</p>';
    s.items.forEach((it, ii) => {
      const id = s.id+'-'+it.kind;
      h += '<div class="fmt"><h3>'+it.label+'</h3><p class="note">'+it.help+'</p>'
        + '<video controls playsinline preload="metadata" poster="'+it.poster+'" src="'+it.src+'"></video>'
        + '<button class="btn" data-act="save" data-i="'+si+'-'+ii+'">1. Save or share this video</button>'
        + '<div class="status" id="st-'+id+'"></div>'
        + (it.caption ? '<button class="btn alt" data-act="copy" data-i="'+si+'-'+ii+'">'+(it.kind==='story'?'2. Copy my link for the story':'2. Copy the caption')+'</button><button class="btn alt small" data-act="cap" data-i="'+si+'-'+ii+'">'+(it.kind==='story'?'Show me the link and words':'Show me the caption')+'</button><div class="cap" id="cap-'+id+'"></div>' : '')
        + '</div>';
    });
    if(s.watch){
      h += '<div class="fmt"><h3>Send it in an email or a text</h3>'
        + '<p class="note">Facebook is not the only way. This link opens a page that <b>plays the video</b> and has <b>your order button</b> right under it. Paste it into an email, a text, or a message. Nothing to save, nothing to attach.</p>'
        + '<div class="linkbox">'+s.watch+'</div>'
        + '<button class="btn alt" data-copy="'+s.watch+'" data-plain="1">Copy a link to the video</button>'
        + '<a class="btn alt small" href="'+s.watch+'" target="_blank" rel="noopener">See what they will see</a>'
        + '</div>';
    }
    sec.innerHTML = h; root.appendChild(sec);
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('button[data-act]'); if(!b) return;
    const [si, ii] = b.dataset.i.split('-').map(Number); const s = D.series[si]; const it = s.items[ii]; const id = s.id+'-'+it.kind;
    if(b.dataset.act==='save') saveShare(it.src, it.filename, 'st-'+id, b);
    if(b.dataset.act==='copy') copyText(it.caption, b);
    if(b.dataset.act==='cap'){ const el=document.getElementById('cap-'+id); if(!el.textContent) el.textContent = it.caption; toggleCap('cap-'+id, b); }
  });
  document.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', () => copyText(b.dataset.copy, b)));
})();
"""

def tools_section(p):
    d = p.get("drive") or {}
    if not d: return ""
    ab = d.get("article_base", "")
    rows = [
      ("How Do You Feel Today?", "A one page checklist. Hand it to someone, or send it, so they can see how they feel today. It is a fillable PDF.", [("Open it", "tools/How-Do-You-Feel-Today.pdf", False), ("Download", "tools/How-Do-You-Feel-Today.pdf", True)]),
      ("Prospect Tracker", "A spreadsheet that keeps track of who you have talked to and what to do next. It opens in Excel or Google Sheets. A computer gives the best view.", [("Download the tracker", "tools/Prospect-Tracker.xlsx", True)]),
      ("Your Business Cards", "Print ready. Take both files to any print shop.", [("Front (PDF)", "tools/Business-Card-Front.pdf", False), ("Back (PDF)", "tools/Business-Card-Back.pdf", False)]),
    ]
    for ec in p.get("extra_cards", []):
        rows.append((ec["label"], "Print ready. Take both files to any print shop.", [("Front (PDF)", ec["front"], False), ("Back (PDF)", ec["back"], False)]))
    if p.get("extra_cards"):
        rows[2] = ("Ann's Business Cards",) + rows[2][1:]
    if d.get("files") is False:
        rows = []
    if ab:
        rows.append(("The Zombie Cell Article", "Easy to read and easy to share. The short one takes about a minute. Your name and link are on it.", [("Short version", ab + "zombie-cells-short/", False), ("Full article", ab + "zombie-cells/", False)]))
    out = '<section class="card"><h2>Your other tools</h2><p class="note">These are yours too. Tap Open it to look at one, or Download to keep a copy.</p>'
    for title, why, btns in rows:
        out += '<div class="fmt"><h3>' + html.escape(title) + '</h3><p class="note">' + html.escape(why) + '</p>'
        for label, href, dlflag in btns:
            out += '<a class="btn alt small" href="' + html.escape(href) + '"' + (' download' if dlflag else ' target="_blank" rel="noopener"') + '>' + html.escape(label) + '</a>'
        out += '</div>'
    return out + '</section>'

WATCH_CSS = """
:root{--wine:#4F1026;--gold:#C6974F;--cream:#F3EEE0;--card:#FBF8F1;--ink:#3a1a26}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--cream);color:var(--ink);font-family:Calibri,Carlito,"Segoe UI",Arial,sans-serif;font-size:20px;line-height:1.5}
h1{font-family:Cambria,Caladea,Georgia,serif;color:var(--wine);line-height:1.2;margin:0 0 .3em;font-size:30px}
.wrap{max-width:560px;margin:0 auto;padding:22px 18px 50px}
.kicker{letter-spacing:.18em;text-transform:uppercase;font-size:13px;color:var(--gold);font-weight:700;margin:0 0 10px}
video{width:100%;border-radius:16px;background:#2a0a16;display:block;max-height:76vh}
.btn{display:block;width:100%;min-height:60px;border:0;border-radius:14px;background:var(--wine);color:#fff;font:700 21px Calibri,Carlito,Arial,sans-serif;padding:16px 18px;margin:16px 0 0;text-align:center;text-decoration:none}
.btn.alt{background:#fff;color:var(--wine);box-shadow:inset 0 0 0 2px var(--wine);min-height:50px;font-size:18px}
.by{font-size:18px;color:#6b4a56;margin:14px 0 0}
.fine{font-size:14px;color:#6b4a56;margin-top:26px}
"""


def footnotes(s):
    tail = FOOT_CARET if s["id"] == "series-01" else FOOT_STORY
    return FOOT_STAR + "<br>" + tail


def watch_page(p, s):
    """A page that plays one video and sends the viewer to this leader's order page."""
    name = html.escape(p["display_name"])
    title = html.escape(s["share_title"])
    desc = html.escape(s["share_desc"])
    order = html.escape(p["landing_url"] + "#order")
    landing = html.escape(p["landing_url"])
    canon = html.escape(watch_url(p, s))
    ev = json.dumps("Watch: " + s["share_title"])
    evo = json.dumps("Click: Watch Order")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}, shared by {name}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="video.other">
<meta property="og:title" content="{title}, shared by {name}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{html.escape(preview_url(s))}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}, shared by {name}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{html.escape(preview_url(s))}">
<style>{WATCH_CSS}</style>
{PLAUSIBLE}
</head>
<body><div class="wrap">
<div class="kicker">Bob Ferguson Longevity</div>
<h1>{title}</h1>
<video controls playsinline preload="metadata" poster="{html.escape(poster_url(s))}" src="{html.escape(video_url(p, s))}"></video>
<p class="by">Shared by {name}.</p>
<a class="btn" id="order" href="{order}">See the details and order</a>
<a class="btn alt" href="{landing}">Learn more first</a>
<p class="fine">{footnotes(s)}</p>
</div>
<script>
try{{ window.plausible && window.plausible({ev}); }}catch(e){{}}
document.getElementById('order').addEventListener('click', function(){{ try{{ window.plausible && window.plausible({evo}); }}catch(e){{}} }});
</script>
</body></html>"""


def page(p):
    link = p["link_url"]
    items_by_series = []
    for s in series:
        caps = CAPTIONS[s["id"]]
        base = (p["video_base"] + f"{s['id']}/") if p.get("video_base") else f"{s['id']}/"
        items = [
          {"kind":"reel","label":"Facebook Reel","help":"For Facebook Reels. In Facebook tap Create, then Reel, then choose this video.","src":base+"reel.mp4","filename":f"{s['id']}-facebook-reel.mp4","poster":"../shared/"+s.get("poster","poster-reel.jpg"),"caption":caps["reel"].replace("{link}", link)},
          {"kind":"story","label":"Facebook Story","help":"For Facebook Stories. In Facebook tap Create, then Story, then choose this video. Add the link with the Link sticker.","src":base+"reel.mp4","filename":f"{s['id']}-facebook-story.mp4","poster":"../shared/"+s.get("poster","poster-reel.jpg"),"caption":"Link for the sticker:\n"+link+"\n\nWords you can add on the story:\n"+STORY_NOTE[s["id"]]+"\n\n"+FOOT_STAR},
        ]
        items_by_series.append({"id":s["id"],"title":s["title"],"added":s["added"],"blurb":s["blurb"],"items":items,"watch":watch_url(p, s),
                                "is_new": s.get("new", s is series[-1])})
    data = {"series": items_by_series}
    short_note = ""
    if p.get("short_slug"):
        short_note = f'<p class="note">Your page address is long, so I made a short link that opens the same page: <b>{html.escape(p["link_text"])}</b>. Orders and visits from it still go to you.</p>'
    first = html.escape(p["first"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{first}'s Sharing Library</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<div class="hero"><div class="kicker">Bob Ferguson Longevity</div>
<h1>{first}, this is your Sharing Library</h1>
<p>Everything you need to share Vivix+&trade; on Facebook lives on this one page. It is just for you. Each video already has <b>your name and your link</b> on it.</p>
<p><b>Keep this page handy.</b> When I add something new, I will email you with a button that brings you straight back here. New things show a gold <span class="tag" style="margin:0">NEW</span> tag.</p></div>

<section class="card"><h2>How to post a video, in 3 steps</h2>
<ol class="steps">
<li><b>Tap "Save or share this video"</b> under the video you want. Choose <b>Save Video</b> so it goes into your Photos.</li>
<li><b>Tap "Copy the caption."</b> The words you will post are copied for you.</li>
<li><b>Open Facebook</b> and start a new post, reel or story. Pick your saved video, then <b>press and hold in the text box and tap Paste.</b></li>
</ol>
<p class="note">Not posting on Facebook? Under each video there is <b>"Copy a link to the video."</b> That link plays the video on its own page with your order button under it, so it works in an email or a text.</p></section>

<div id="series"></div>

{tools_section(p)}

<section class="card"><h2>Your links</h2>
<p class="note">This is where people go to learn and order. Orders credit you.</p>
<div class="linkbox">{html.escape(link)}</div>
<button class="btn alt" data-copy="{html.escape(link)}" data-plain="1">Copy my link</button>
{short_note}
</section>

<section class="card"><h2>What is where</h2>
<table>
<tr><td>This page</td><td>Your videos and captions. Come back here any time you want to post.</td></tr>
<tr><td>Your landing page</td><td>The page your link opens. Customers learn about Vivix+&trade; and order from it.</td></tr>
<tr><td>A link to the video</td><td>For email and texting. It opens a page that plays the video and has your order button under it.</td></tr>
<tr><td>Your other tools</td><td>The checklist, tracker, business cards and article. They are lower on this page.</td></tr>
<tr><td>An email from Bob</td><td>Arrives whenever something new is added. Tap the button in it to open this page.</td></tr>
</table>
<details><summary>How do I get back to this page easily?</summary>
<p><b>iPhone:</b> tap the Share icon at the bottom of Safari, scroll down, tap <b>Add to Home Screen</b>. It will sit on your phone like an app.</p>
<p><b>Android:</b> tap the three dots at the top right of Chrome, then tap <b>Add to Home screen</b>.</p>
<p><b>Or:</b> search your email for <b>Sharing Library</b>. Every email I send about it has those words at the start.</p></details>
<details><summary>The video will not save. What do I do?</summary>
<p>Tap the button again and wait a few seconds. If a menu opens, tap <b>Save Video</b>. On an iPhone, make sure you are using Safari. Still stuck? Reply to my email and tell me what phone you have. I will walk you through it.</p></details>
</section>

<p class="fine">{html.escape(FOOT_STAR)}<br>{html.escape(FOOT_CARET)}</p>
<p class="fine">Please keep the footnotes in your caption when you post. The Copy the caption button already includes them.</p>
</div>
<script type="application/json" id="data">{json.dumps(data).replace("</", "<\\/")}</script>
<script>{JS}</script>
</body></html>"""

def redirect(p):
    t = html.escape(p["landing_url"]); name = html.escape(p["display_name"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vivix+&trade;, shared by {name}</title>
<meta property="og:title" content="Vivix+&trade;, shared by {name}">
<meta property="og:description" content="3.2 points more VO2 max* and 8 years of cellular aging^. See the full story.">
<meta property="og:image" content="https://bobfergusonlongevity.com/previews/vivix.jpg">
<meta property="og:type" content="website">
<meta http-equiv="refresh" content="0;url={t}">
<script>location.replace({json.dumps(p["landing_url"])} + location.search + location.hash);</script>
</head><body style="font-family:Calibri,Arial,sans-serif;background:#F3EEE0;color:#4F1026;padding:30px;font-size:20px">
<p>Taking you to {name}'s page. If nothing happens, <a href="{t}">tap here</a>.</p></body></html>"""

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


watch_count = 0
for p in people:
    write(os.path.join(OUT, "library", p["slug"], "index.html"), page(p))
    if p.get("short_slug"):
        write(os.path.join(OUT, "go", p["short_slug"], "index.html"), redirect(p))
    # Watch pages. Leaders on their own address get theirs staged for their own repo,
    # everyone else gets theirs served from here under their short link.
    for s in series:
        if own_domain(p):
            dest = os.path.join(OUT, "_watch", p["slug"], s["watch_slug"], "index.html")
        else:
            dest = os.path.join(OUT, "go", p["short_slug"], s["watch_slug"], "index.html")
        write(dest, watch_page(p, s))
        watch_count += 1
print("built", len(people), "libraries and", watch_count, "watch pages")
