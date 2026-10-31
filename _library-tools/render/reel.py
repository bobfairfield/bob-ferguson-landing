import os
import numpy as np, subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

M = os.path.join(os.environ.get("BFL_ASSETS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")), "deck", "x", "ppt", "media") + "/"
OUT = sys.argv[1]
W, H, FPS, DUR = 1080, 1920, 30, 15.0
NF = int(FPS * DUR)
BEAT = 60 / 128
DROP = 7.5
MAROON = (84, 14, 42)
ROSE = (255, 196, 214)

def font(w, s): return ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)

def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def ease_back(x):
    x = min(1, max(0, x)); c1 = 1.4; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def clamp(x): return min(1, max(0, x))

def load(n, h=None):
    im = Image.open(M + n).convert("RGB")
    return im

cells = load("image6.jpg")
cells = cells.resize((int(cells.width * 2300 / cells.height), 2300), Image.LANCZOS)
hero = load("image14.jpg")
hero = hero.resize((int(hero.width * 2300 / hero.height), 2300), Image.LANCZOS)
iv = load("image26.jpg")
iv = iv.resize((int(iv.width * 2300 / iv.height), 2300), Image.LANCZOS)
logo = Image.open(M + "image18.png").convert("RGBA")
# recolor logo to white
a = logo.split()[3]
logo_w = Image.merge("RGBA", (Image.new("L", logo.size, 255),) * 3 + (a,))
logo_w = logo_w.resize((820, int(820 * logo.height / logo.width)), Image.LANCZOS)

def cover(im, zoom=1.0, cx=0.5, cy=0.5, shift=(0, 0)):
    """crop-to-fill W x H with zoom, center in fractions"""
    sc = max(W / im.width, H / im.height) * zoom
    cw, ch = W / sc, H / sc
    x0 = cx * im.width - cw / 2 + shift[0]; y0 = cy * im.height - ch / 2 + shift[1]
    x0 = min(max(0, x0), im.width - cw); y0 = min(max(0, y0), im.height - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

# vignette / gradients
yy, xx = np.mgrid[0:H, 0:W]
vig = np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2, 0, 1)
vig = (vig * 0.55)[..., None]
grad_top = np.clip(1 - yy / (H * 0.45), 0, 1)[..., None] * 0.55
grad_bot = np.clip((yy - H * 0.55) / (H * 0.45), 0, 1)[..., None] * 0.65

def darken(arr, amt=1.0, top=False, bot=False):
    k = vig * amt
    if top: k = k + grad_top
    if bot: k = k + grad_bot
    k = np.clip(k, 0, 0.92)
    tint = np.array([40, 4, 20], dtype=np.float32)
    return arr * (1 - k) + tint * k

def text_layer(lines, y, size, wgt="ExtraBold", color=(255, 255, 255), spacing=1.08, track=0, align="center", shadow=True):
    """returns RGBA layer (full-frame) and total height. lines: list of strings"""
    f = font(wgt, size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    yc = y
    for ln in lines:
        if track:
            wtot = sum(d.textlength(c, font=f) + track for c in ln) - track
        else:
            wtot = d.textlength(ln, font=f)
        x = (W - wtot) / 2
        if shadow:
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
            if track:
                xx_ = x
                for c in ln:
                    sd.text((xx_, yc + 6), c, font=f, fill=(20, 0, 10, 150)); xx_ += d.textlength(c, font=f) + track
            else:
                sd.text((x, yc + 6), ln, font=f, fill=(20, 0, 10, 150))
            sh = sh.filter(ImageFilter.GaussianBlur(10))
            layer.alpha_composite(sh)
            d = ImageDraw.Draw(layer)
        if track:
            xx_ = x
            for c in ln:
                d.text((xx_, yc), c, font=f, fill=color + (255,)); xx_ += d.textlength(c, font=f) + track
        else:
            d.text((x, yc), ln, font=f, fill=color + (255,))
        yc += size * spacing
    return layer

def paste_anim(base, layer, p, rise=60, scale0=1.0):
    """p: progress 0..1. fade + rise"""
    if p <= 0: return base
    e = ease_out(p)
    al = layer.copy()
    a = al.split()[3].point(lambda v: int(v * e))
    al.putalpha(a)
    dy = int((1 - e) * rise)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if scale0 != 1.0:
        s = scale0 + (1 - scale0) * ease_back(p)
        nw, nh = int(W * s), int(H * s)
        al = al.resize((nw, nh), Image.BILINEAR)
        out.alpha_composite(al, ((W - nw) // 2, (H - nh) // 2 + dy)) if nw <= W else out.paste(al.crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H)), (0, dy))
    else:
        out.alpha_composite(al, (0, dy))
    base.alpha_composite(out)
    return base


def build_thumb():
    bg = cover(hero, 1.0, 0.5, 0.62)
    arr = np.asarray(bg, dtype=np.float32)
    # bloom: blur bright areas and add back
    bright = np.clip(arr - 110, 0, 255)
    bl = np.asarray(Image.fromarray(bright.astype(np.uint8)).filter(ImageFilter.GaussianBlur(40)), dtype=np.float32)
    arr = arr * 1.05 + bl * 0.8
    arr = darken(arr, 1.5, top=True, bot=True)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # rose light streak behind headline
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, 80, W + 200, 760], fill=(255, 60, 110, 120))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    img.alpha_composite(text_layer(["SHOWN TO INCREASE"], 130, 66, "Bold", ROSE, track=4))
    vl = L["vo2"]
    sc = vl.resize((int(W * 0.74), int(H * 0.74)), Image.LANCZOS)
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tmp.paste(sc, ((W - sc.width) // 2, -300), sc)
    img.alpha_composite(tmp)
    # bottom banner
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.rectangle([0, 1470, W, 1790], fill=(40, 4, 20, 190))
    bd.rectangle([0, 1470, W, 1476], fill=ROSE + (255,))
    img.alpha_composite(band)
    img.alpha_composite(text_layer(["WITHOUT", "EXERCISE."], 1490, 140, "Black", (255, 255, 255), spacing=0.98))
    return img.convert("RGB")


def pulse(t):
    if t < 1.9: return 0.0
    ph = ((t - 1.9) % BEAT)
    return math.exp(-ph * 9)

# pre-build text layers
L = {}
L["the_only"] = text_layer(["THE ONLY"], 640, 150, "Black", ROSE, track=6)
L["longevity"] = text_layer(["LONGEVITY", "SUPPLEMENT"], 870, 138, "Black", (255, 255, 255), spacing=1.02)
L["shown"] = text_layer(["SHOWN TO INCREASE"], 520, 74, "Bold", ROSE, track=4)

# VO2 MAX layer, built manually with subscript
def vo2_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    fb = font("Black", 330); fs = font("Black", 150)
    wvo = d.textlength("VO", font=fb); w2 = d.textlength("2", font=fs)
    tot = wvo + w2 + 8
    x = (W - tot) / 2; y = 640
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.text((x, y + 8), "VO", font=fb, fill=(20, 0, 10, 160)); sd.text((x + wvo + 8, y + 250), "2", font=fs, fill=(20, 0, 10, 160))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(layer)
    d.text((x, y), "VO", font=fb, fill=(255, 255, 255, 255)); d.text((x + wvo + 8, y + 250), "2", font=fs, fill=(255, 255, 255, 255))
    ymax = y + 400
    wm = d.textlength("MAX", font=fb)
    d.text(((W - wm) / 2, ymax - 40), "MAX", font=fb, fill=(255, 196, 214, 255))
    return layer
L["vo2"] = vo2_layer()
THUMB = build_thumb()
L["without"] = text_layer(["WITHOUT", "EXERCISE."], 200, 150, "Black", (255, 255, 255), spacing=1.0)
L["brand_sub"] = text_layer(["NAD+ BOOSTER"], 1040, 54, "Bold", ROSE, track=14)
L["shaklee"] = text_layer(["SHAKLEE  ·  LIVE AGE FREE™"], 1700, 36, "SemiBold", (255, 255, 255), track=8, shadow=False)

def make_frame(i):
    t = i / FPS
    if t < 0.5:
        return THUMB
    pl = pulse(t)
    if t < 3.7:
        # Scene A: cells
        k = t / 3.7
        bg = cover(cells, 1.15 + 0.12 * k + 0.012 * pl, 0.45 + 0.1 * k, 0.5)
        arr = darken(np.asarray(bg, dtype=np.float32), 1.0, top=True, bot=True)
    elif t < DROP:
        k = (t - 3.7) / (DROP - 3.7)
        bg = cover(cells, 1.35 + 0.25 * k + 0.012 * pl, 0.6, 0.5)
        arr = np.asarray(bg, dtype=np.float32)
        # deepen maroon as tension builds
        arr = arr * (1 - 0.55) + np.array(MAROON, dtype=np.float32) * 0.55
        arr = darken(arr, 1.1, top=True, bot=True)
    else:
        k = (t - DROP) / (DROP)
        s_in = 1.0 + 0.22 * math.exp(-(t - DROP) * 7)
        shake = math.exp(-(t - DROP) * 14) * 14
        sx = math.sin(t * 90) * shake; sy = math.cos(t * 77) * shake
        bg = cover(hero, s_in * (1.0 + 0.07 * (t - DROP) / (DUR - DROP) + 0.010 * pl), 0.5, 0.58, (sx, sy))
        arr = darken(np.asarray(bg, dtype=np.float32), 0.7, top=(t < 12.0), bot=True)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

    if t < 3.7:
        paste_anim(img, L["the_only"], (t - 0.45) / 0.5, 50)
        paste_anim(img, L["longevity"], (t - 0.95) / 0.55, 70)
        # accent line
        wl = int(520 * ease_out((t - 1.4) / 0.7))
        if wl > 0:
            ImageDraw.Draw(img).rectangle([(W - wl) // 2, 822, (W + wl) // 2, 828], fill=ROSE + (255,))
        if t > 3.35:  # fade out
            f = 1 - (t - 3.35) / 0.35
            ov = Image.new("RGBA", (W, H), MAROON + (int((1 - f) * 90),)); img.alpha_composite(ov)
    elif t < DROP:
        k = t - 3.7
        paste_anim(img, L["shown"], k / 0.4, 40)
        paste_anim(img, L["vo2"], (k - 0.2) / 0.5, 0, scale0=0.72)
        # tension flash flicker near drop
        if t > DROP - 0.25:
            ov = Image.new("RGBA", (W, H), (255, 255, 255, int(60 * (t - (DROP - 0.25)) / 0.25))); img.alpha_composite(ov)
    else:
        k = t - DROP
        # impact flash
        fl = math.exp(-k * 12)
        if k < 0.6:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 235, 242, int(255 * fl))))
        wp = (k - 0.05) / 0.45
        if t < 10.9: paste_anim(img, L["without"], wp, 0, scale0=1.35)
        elif t < 11.4:
            lay = L["without"].copy(); lay.putalpha(lay.split()[3].point(lambda v: int(v * (1 - (t - 10.9) / 0.5)))); img.alpha_composite(lay)
        if t >= 10.9:
            p = (t - 10.9) / 0.7
            # darken the whole frame, bring in logo
            img.alpha_composite(Image.new("RGBA", (W, H), (40, 4, 20, int(205 * ease_out(p)))))
            lg = logo_w.copy(); al = lg.split()[3].point(lambda v: int(v * ease_out(p))); lg.putalpha(al)
            img.alpha_composite(lg, ((W - lg.width) // 2, int(820 + (1 - ease_out(p)) * 40)))
            paste_anim(img, L["brand_sub"], (t - 11.4) / 0.5, 30)
            paste_anim(img, L["shaklee"], (t - 12.0) / 0.5, 20)
            # "without exercise" fades up out
            if t > 11.2:
                pass
    # fade in/out
    out = img.convert("RGB")
    if t < 0.2:
        out = Image.blend(Image.new("RGB", (W, H), (30, 0, 14)), out, t / 0.2)
    if t > DUR - 0.4:
        out = Image.blend(out, Image.new("RGB", (W, H), (30, 0, 14)), (t - (DUR - 0.4)) / 0.4)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "thumb":
        THUMB.save(f"{OUT}/Vivix_VO2_Thumbnail.png")
    elif len(sys.argv) > 2 and sys.argv[2] == "stills":
        for tt in [0.5, 1.8, 3.0, 5.0, 7.0, 7.65, 9.0, 11.0, 13.0, 14.8]:
            make_frame(int(tt * FPS)).resize((540, 960)).save(f"{OUT}/still_{tt:05.2f}.png")
    else:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-i", f"{OUT}/music/5_fast_hype.mp3", "-t", str(DUR), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{OUT}/Vivix_VO2_Reel.mp4"], stdin=subprocess.PIPE)
        for i in range(NF):
            p.stdin.write(make_frame(i).tobytes())
        p.stdin.close(); p.wait()
        print("ok")
