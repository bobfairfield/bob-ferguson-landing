import sys, subprocess
from PIL import Image
sys.argv = [sys.argv[0]]
import reel30 as M
from reel import text_layer
FH = 1350
M.L["erases"] = text_layer(["ERASES"], 385, 130, "Black", (255, 196, 214), track=8)
M.L["cell"] = text_layer(["OF CELLULAR AGING^"], 1648, 62, "Bold", (255, 255, 255), track=3)
POST = Image.open("fb/Vivix_FB_Post_1080x1350.png").convert("RGB")
def y0_for(t):
    if t < M.S2: return 170
    if t < M.D1: return 285
    if t < M.S4: return 140
    if t < M.S5: return 250
    if t < M.S6: return 365
    if t < M.D2: return 270
    return 570
def frame(i):
    t = i / M.FPS
    if t < M.S1: return POST
    img = M.make_frame(i)
    y0 = y0_for(t)
    return img.crop((0, y0, M.W, y0 + FH))
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stills": pass
    mode = __import__("os").environ.get("MODE", "render")
    if mode == "stills":
        ts = [0.2, 2.0, 5.5, 8.5, 12.5, 14.5, 17.5, 20.5, 23.5, 27.0]
        ims = [frame(int(tt * M.FPS)).resize((360, 450)) for tt in ts]
        sh = Image.new("RGB", (360 * 5, 450 * 2))
        for n, im in enumerate(ims): sh.paste(im, ((n % 5) * 360, (n // 5) * 450))
        sh.save("feed_stills.png"); print("saved")
    else:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{M.W}x{FH}", "-r", str(M.FPS), "-i", "-",
                              "-i", M.SP + "music30/hype_30s.mp3", "-t", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "fb/Vivix_FB_Feed_Video_4x5.mp4"], stdin=subprocess.PIPE)
        for n in range(M.NF): p.stdin.write(frame(n).tobytes())
        p.stdin.close(); p.wait(); print("ok")
