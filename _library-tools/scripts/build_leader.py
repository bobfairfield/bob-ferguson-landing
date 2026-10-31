"""Render one leader's personalized Series videos and place them.

Usage: python build_leader.py <slug> [<leader_repo_dir>] [<series_id>]
Videos go into <leader_repo_dir>/library-videos/<series_id>/ when the leader has a
video_base, otherwise into <repo root>/library/<slug>/<series_id>/.
"""
import os, sys, json, subprocess, tempfile

TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
ASSETS = os.path.join(TOOLS, "assets")
os.environ["BFL_ASSETS"] = ASSETS
sys.path.insert(0, os.path.join(TOOLS, "render"))
os.chdir(ASSETS)  # feed.py opens fb/... relative to here

slug = sys.argv[1]
leader_dir = sys.argv[2] if len(sys.argv) > 2 else None
series_id = sys.argv[3] if len(sys.argv) > 3 else "series-01"
people = json.load(open(os.path.join(TOOLS, "participants.json")))
p = next(x for x in people if x["slug"] == slug)

import reel30 as M
import feed as F
FPS, SPLIT, NF = M.FPS, int(M.D2 * M.FPS), M.NF
fmts = {"reel": (M.make_frame, "1080x1920"), "feed": (F.frame, "1080x1350")}
M.set_participant(p["onscreen_url"], p["display_name"])

if p.get("video_base"):
    if not leader_dir:
        sys.exit("leader repo dir required for this leader")
    dest = os.path.join(leader_dir, "library-videos", series_id)
else:
    dest = os.path.join(ROOT, "library", slug, series_id)
os.makedirs(dest, exist_ok=True)

tmp = tempfile.mkdtemp()
for k, (fn, size) in fmts.items():
    pb = os.path.join(tmp, f"partB_{k}.mp4")
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", size, "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "30", "-an", pb], stdin=subprocess.PIPE)
    for i in range(SPLIT, NF):
        pr.stdin.write(fn(i).tobytes())
    pr.stdin.close(); pr.wait()
    lst = os.path.join(tmp, f"{k}.txt")
    open(lst, "w").write(f"file '{os.path.join(ASSETS, f'partA_{k}.mp4')}'\nfile '{pb}'\n")
    joined = os.path.join(tmp, f"{k}_joined.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(ASSETS, "music30/hype_30s.mp3"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "30", "-movflags", "+faststart", joined], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(dest, f"{k}.mp4")], check=True)
    print("wrote", os.path.join(dest, f"{k}.mp4"))
