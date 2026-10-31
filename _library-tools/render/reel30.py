import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.argv = [sys.argv[0], "."] + sys.argv[1:]
import reel as R
from reel import W, H, FPS, ROSE, MAROON, font, ease_out, ease_back, clamp, cover, darken, text_layer, paste_anim

DUR = 30.0
NF = int(DUR * FPS)
BEAT = 60 / 128
S1, S2, D1, S4, S5, S6, D2 = 0.5, 4.0, 7.5, 11.25, 16.875, 19.6875, 22.5
import os
SP = os.environ.get("BFL_ASSETS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")) + "/"
DARK = (30, 0, 14)

def pulse(t):
    return math.exp(-(t % BEAT) * 9) if t > 1.9 else 0.0

# ---------- helpers ----------
def vo2_line(size, y, color=(255, 255, 255), suffix=""):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    fb = font("Black", size); fs = font("Black", int(size * 0.45))
    parts = [("VO", fb, 0), ("2", fs, size * 0.58), (" MAX" + suffix, fb, 0)]
    wtot = sum(d.textlength(p[0], font=p[1]) for p in parts)
    x = (W - wtot) / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); xx = x
    for txt, f, dy in parts:
        sd.text((xx, y + dy + 6), txt, font=f, fill=(20, 0, 10, 150)); xx += d.textlength(txt, font=f)
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(layer); xx = x
    for txt, f, dy in parts:
        d.text((xx, y + dy), txt, font=f, fill=color + (255,)); xx += d.textlength(txt, font=f)
    return layer

def stack(layers):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for l in layers: out.alpha_composite(l)
    return out

def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

# panel feather mask
PH = 607
fm = np.ones((PH, W), dtype=np.float32)
fe = 46
ramp = np.linspace(0, 1, fe)
fm[:fe] *= ramp[:, None]; fm[-fe:] *= ramp[::-1][:, None]
FEATHER = Image.fromarray((fm * 255).astype(np.uint8))
PANEL_Y = (H - PH) // 2

def panel_frame(dirn, n, k):
    k = min(max(1, k), n)
    pf = Image.open(f"{SP}{dirn}/{k:04d}.png").convert("RGB")
    crop = pf.crop((370, 0, 370 + 341, PH)).resize((108, 192), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(crop, dtype=np.float32)
    arr = arr * 0.72 + np.array([70, 8, 36], dtype=np.float32) * 0.28
    bg = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    bg.paste(pf, (0, PANEL_Y), FEATHER)
    return bg

# ---------- static layers ----------
L = {}
L["only"] = text_layer(["THE ONLY"], 205, 104, "Black", ROSE, track=6)
L["lsup"] = text_layer(["LONGEVITY", "SUPPLEMENT"], 335, 122, "Black", (255, 255, 255), spacing=1.0)
L["shaklee"] = R.L["shaklee"]
L["without"] = text_layer(["WITHOUT", "EXERCISE*"], 200, 150, "Black", (255, 255, 255), spacing=1.0)
L["points"] = text_layer(["POINTS GREATER"], 1015, 74, "Bold", (255, 255, 255), track=4)
L["vo2big"] = vo2_line(170, 1110, ROSE, "^")
L["months"] = text_layer(["IN JUST 2 MONTHS"], 1420, 58, "Bold", ROSE, track=8)
L["erases"] = text_layer(["ERASES"], 330, 130, "Black", ROSE, track=8)
L["cell"] = text_layer(["OF CELLULAR AGING^"], 1660, 62, "Bold", (255, 255, 255), track=3)
# recap
L["ra"] = stack([text_layer(["+3.2 POINTS"], 300, 134, "Black", ROSE), vo2_line(134, 450, (255, 255, 255), "^")])
L["rb"] = stack([text_layer(["8 YEARS"], 790, 150, "Black", ROSE), text_layer(["OF CELLULAR AGING ERASED^"], 960, 54, "Bold", (255, 255, 255), track=1)])
L["rc"] = text_layer(["WITHOUT", "EXERCISE*"], 1270, 140, "Black", (255, 255, 255), spacing=0.98)
# end card
L["sub"] = text_layer(["NAD+ BOOSTER"], 1010, 54, "Bold", ROSE, track=14)
L["cta"] = None

def pill(txt="bobfergusonlongevity.com"):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    size = 46
    while True:
        f = font("Bold", size); tw = d.textlength(txt, font=f)
        if tw + 90 <= 980 or size <= 28: break
        size -= 2
    pw, ph = tw + 90, 100
    x0, y0 = (W - pw) / 2, 1200
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=50, fill=ROSE + (255,))
    d.text(((W - tw) / 2, y0 + 50 - size * 0.62), txt, font=f, fill=MAROON + (255,))
    return layer
def set_participant(url_text=None, name=None):
    L["cta"] = pill(url_text or "bobfergusonlongevity.com")
    L["shared"] = text_layer(["SHARED BY " + name.upper()], 1335, 46, "Bold", ROSE, track=6, shadow=False) if name else None
L["cta"] = pill()

def foot():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    f = ImageFont_ = __import__("PIL.ImageFont", fromlist=["x"]).truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 25)
    d.rectangle([0, 1560, W, H], fill=(36, 3, 18, 215))
    t1 = "*These statements have not been evaluated by the Food and Drug Administration. This product is not intended to diagnose, treat, cure, or prevent any disease."
    t2 = "^In a two-month study, Vivix+ increased VO2 max by 2.6 to 3.8 mL/(kg·min), equivalent to reversing 6.5 to 9.5 years of typical age-related decline, or 8 years on average."
    y = 1590
    for t in (t1, t2):
        for ln in wrap(t, f, 940):
            d.text((70, y), ln, font=f, fill=(255, 225, 235, 235)); y += 33
        y += 20
    return layer
L["foot"] = foot()

def fade_layer(layer, a):
    l = layer.copy(); l.putalpha(l.split()[3].point(lambda v: int(v * a))); return l

# ring
def ring(p, size=640, w=30):
    S = 2
    c = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    box = [w * S, w * S, (size - w) * S, (size - w) * S]
    d.arc(box, 0, 360, fill=(255, 196, 214, 60), width=w * S)
    if p > 0.002:
        d.arc(box, -90, -90 + 360 * p, fill=ROSE + (255,), width=w * S)
    return c.resize((size, size), Image.LANCZOS)

def counter_layer(txt, y, size, color=(255, 255, 255), font_w="Black"):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); f = font(font_w, size)
    tw = d.textlength(txt, font=f); x = (W - tw) / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); sd.text((x, y + 8), txt, font=f, fill=(20, 0, 10, 170))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(layer)
    d.text((x, y), txt, font=f, fill=color + (255,)); return layer

def flash(img, a, col=(255, 235, 242)):
    if a > 0: img.alpha_composite(Image.new("RGBA", (W, H), col + (int(255 * min(1, a)),)))

def make_frame(i):
    t = i / FPS
    pl = pulse(t)
    if t < S1:
        return R.THUMB
    # ---- scene 1: woman clip ----
    if t < S2:
        img = panel_frame("cw", 105, int((t - S1) * FPS) + 1)
        paste_anim(img, L["only"], (t - 0.95) / 0.5, 50)
        paste_anim(img, L["lsup"], (t - 1.4) / 0.55, 60)
        paste_anim(img, L["shaklee"], (t - 1.0) / 0.6, 20)
        flash(img, 0.0)
    # ---- scene 2: VO2 MAX tension ----
    elif t < D1:
        k = (t - S2) / (D1 - S2)
        bg = cover(R.cells, 1.35 + 0.25 * k + 0.012 * pl, 0.6, 0.5)
        arr = np.asarray(bg, dtype=np.float32)
        arr = arr * 0.45 + np.array(MAROON, dtype=np.float32) * 0.55
        arr = darken(arr, 1.1, top=True, bot=True)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        kk = t - S2
        paste_anim(img, R.L["shown"], kk / 0.4, 40)
        paste_anim(img, R.L["vo2"], (kk - 0.2) / 0.5, 0, scale0=0.72)
        if t > D1 - 0.25:
            flash(img, 0.25 * (t - (D1 - 0.25)) / 0.25, (255, 255, 255))
        flash(img, math.exp(-(t - S2) * 14) * 0.9, (255, 235, 242))
    # ---- scene 3: drop 1, product ----
    elif t < S4:
        k = t - D1
        s_in = 1.0 + 0.22 * math.exp(-k * 7)
        shake = math.exp(-k * 14) * 14
        sx, sy = math.sin(t * 90) * shake, math.cos(t * 77) * shake
        bg = cover(R.hero, s_in * (1.0 + 0.05 * k / (S4 - D1) + 0.010 * pl), 0.5, 0.58, (sx, sy))
        arr = darken(np.asarray(bg, dtype=np.float32), 0.7, top=True, bot=True)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        flash(img, math.exp(-k * 12) if k < 0.6 else 0)
        paste_anim(img, L["without"], (k - 0.05) / 0.45, 0, scale0=1.35)
    # ---- scene 4: +3.2 counter ----
    elif t < S5:
        k = t - S4
        bg = cover(R.cells, 1.5 + 0.12 * k / (S5 - S4) + 0.012 * pl, 0.35, 0.5)
        arr = np.asarray(bg, dtype=np.float32)
        arr = arr * 0.30 + np.array(MAROON, dtype=np.float32) * 0.70
        arr = darken(arr, 1.2, top=True, bot=True)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        p = ease_out((k - 0.25) / 1.5)
        rg = ring(0.8 * p)
        sc = 1.0 + 0.02 * pl
        if sc != 1.0:
            rg = rg.resize((int(rg.width * sc), int(rg.height * sc)), Image.BILINEAR)
        img.alpha_composite(rg, ((W - rg.width) // 2, 640 - rg.height // 2))
        val = 3.2 * p
        paste_anim(img, counter_layer("+%.1f" % val, 640 - 160, 250), min(1, (k - 0.05) / 0.2), 0)
        paste_anim(img, L["points"], (k - 1.3) / 0.4, 30)
        paste_anim(img, L["vo2big"], (k - 1.6) / 0.5, 0, scale0=0.75)
        paste_anim(img, L["months"], (k - 2.3) / 0.5, 30)
        flash(img, math.exp(-k * 14) * 0.8)
    # ---- scene 5: man clip + ERASES / 8 years ----
    elif t < S6:
        k = t - S5
        img = panel_frame("cm", 88, int(k * FPS) + 1)
        paste_anim(img, L["erases"], (k - 0.1) / 0.4, 40)
        yr = int(round(8 * ease_out((k - 0.15) / 1.6)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        f8, fy = font("Black", 360), font("Black", 140)
        tw8, twy = d.textlength(str(yr), font=f8), d.textlength(" YEARS", font=fy)
        x0 = (W - tw8 - twy) / 2; y0 = 1290
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.text((x0, y0 + 8), str(yr), font=f8, fill=(20, 0, 10, 170)); sd.text((x0 + tw8, y0 + 215), " YEARS", font=fy, fill=(20, 0, 10, 170))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(lay)
        d.text((x0, y0), str(yr), font=f8, fill=ROSE + (255,)); d.text((x0 + tw8, y0 + 215), " YEARS", font=fy, fill=(255, 255, 255, 255))
        paste_anim(img, lay, (k - 0.05) / 0.25, 0)
        paste_anim(img, L["cell"], (k - 1.5) / 0.4, 20)
        flash(img, math.exp(-k * 14) * 0.8)
    # ---- scene 6: recap pops ----
    elif t < D2:
        k = t - S6
        bg = cover(R.cells, 1.7 + 0.2 * k / (D2 - S6) + 0.015 * pl, 0.5, 0.45)
        arr = np.asarray(bg, dtype=np.float32)
        arr = arr * 0.3 + np.array(MAROON, dtype=np.float32) * 0.7
        arr = darken(arr, 1.2, top=True, bot=True)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        paste_anim(img, L["ra"], k / 0.3, 0, scale0=0.7)
        paste_anim(img, L["rb"], (k - 2 * BEAT) / 0.3, 0, scale0=0.7)
        paste_anim(img, L["rc"], (k - 4 * BEAT) / 0.3, 0, scale0=0.7)
        for j in range(3):
            flash(img, math.exp(-max(0, k - j * 2 * BEAT) * 16) * 0.35 if k >= j * 2 * BEAT else 0)
        if t > D2 - 0.25:
            flash(img, 0.35 * (t - (D2 - 0.25)) / 0.25, (255, 255, 255))
    # ---- scene 7: drop 2, end card ----
    else:
        k = t - D2
        s_in = 1.0 + 0.22 * math.exp(-k * 7)
        shake = math.exp(-k * 14) * 14
        sx, sy = math.sin(t * 90) * shake, math.cos(t * 77) * shake
        bg = cover(R.hero, s_in * (1.12 + 0.05 * k / (DUR - D2) + 0.010 * pl), 0.5, 0.64, (sx, sy))
        arr = darken(np.asarray(bg, dtype=np.float32), 0.8, top=True, bot=True)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        p = ease_out((k - 0.1) / 0.8)
        img.alpha_composite(Image.new("RGBA", (W, H), (40, 4, 20, int(185 * p))))
        lg = logo_fade(p)
        img.alpha_composite(lg[0], (lg[1], lg[2]))
        paste_anim(img, L["sub"], (k - 0.7) / 0.5, 30)
        paste_anim(img, R.L["shaklee"], (k - 1.2) / 0.5, 20) if False else None
        paste_anim(img, text_layer(["SHAKLEE  ·  LIVE AGE FREE™"], 1100, 38, "SemiBold", (255, 255, 255), track=8, shadow=False), (k - 1.2) / 0.5, 20)
        paste_anim(img, L["cta"], (k - 2.0) / 0.5, 30)
        if L.get("shared") is not None: paste_anim(img, L["shared"], (k - 2.3) / 0.5, 20)
        paste_anim(img, L["foot"], (k - 2.6) / 0.6, 0)
        flash(img, math.exp(-k * 12) if k < 0.6 else 0)
    out = img.convert("RGB")
    if t > DUR - 0.5:
        out = Image.blend(out, Image.new("RGB", (W, H), DARK), (t - (DUR - 0.5)) / 0.5)
    return out

def logo_fade(p):
    lg = R.logo_w.copy(); a = lg.split()[3].point(lambda v: int(v * p)); lg.putalpha(a)
    return lg, (W - lg.width) // 2, int(780 + (1 - p) * 40)

if __name__ == "__main__":
    mode = sys.argv[2] if len(sys.argv) > 2 else "render"
    if mode == "stills":
        ts = [0.2, 1.0, 3.3, 5.5, 7.4, 8.5, 12.2, 13.5, 15.5, 17.5, 18.8, 19.0, 20.0, 21.0, 21.9, 23.0, 26.0, 29.0]
        ims = [make_frame(int(tt * FPS)).resize((360, 640)) for tt in ts]
        cols = 6; rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (360 * cols, 640 * rows))
        for n, im in enumerate(ims): sh.paste(im, ((n % cols) * 360, (n // cols) * 640))
        sh.save(SP + "stills30.png"); print("saved")
    else:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-i", SP + "music30/hype_30s.mp3", "-t", str(DUR), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", SP + "Vivix_VO2_Reel_30s.mp4"], stdin=subprocess.PIPE)
        for n in range(NF):
            p.stdin.write(make_frame(n).tobytes())
        p.stdin.close(); p.wait(); print("ok")
