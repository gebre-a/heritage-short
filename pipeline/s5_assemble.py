"""Stage 5: Ken Burns / Wan segments -> concat + burned subtitles + end card -> duck + loudnorm -> 2 exports."""
import pathlib, textwrap, time
from PIL import Image, ImageDraw, ImageFont
from common import load_storyboard, h, file_hash, cached, mark, log_call, LEAD, TAIL, END_S, FPS
from media import run, probe, add_durations, narration_track

ASPECTS = {"vertical": (1080, 1920), "horizontal": (1920, 1080)}
SUB_STYLE = {"vertical": (14, 40), "horizontal": (12, 15)}   # (FontSize, MarginV) in libass 288-high units
MUSIC_GAIN = 0.35        # tune by ear
OUT = pathlib.Path("outputs"); TMP = OUT / "tmp"; FIN = OUT / "final"
TMP.mkdir(parents=True, exist_ok=True); FIN.mkdir(parents=True, exist_ok=True)

sb = load_storyboard()
shots = add_durations(sb["shots"])
total = round(sum(s["_dur"] for s in shots) + END_S, 2)
print(f"film length: {total}s", "" if 60 <= total <= 90 else "  <-- WARNING: outside 60-90 s, edit narration/shots")


def kb_filter(kind, W, H, n):
    pre = f"scale={2*W}:{2*H}:force_original_aspect_ratio=increase,crop={2*W}:{2*H},"
    if kind == "zoom_out":
        z = f"z='if(eq(on,0),1.2,max(zoom-{0.2/n:.6f},1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    elif kind == "pan_right":
        z = f"z=1.15:x='(iw-iw/zoom)*on/{n}':y='ih/2-(ih/zoom/2)'"
    elif kind == "pan_left":
        z = f"z=1.15:x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-(ih/zoom/2)'"
    else:  # zoom_in
        z = f"z='min(zoom+{0.2/n:.6f},1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    return pre + f"zoompan={z}:d={n}:s={W}x{H}:fps={FPS},format=yuv420p"


def segment(s, name, W, H):
    clip = OUT / "shots" / f"{s['id']}.mp4"
    img = OUT / "keyframes" / f"{s['id']}.jpg"
    use_clip = clip.exists()
    src = clip if use_clip else img
    D = s["_dur"]; n = int(D * FPS)
    p = TMP / f"{s['id']}_{name}.mp4"
    key = h(src.name, file_hash(src), s["kb"], D, W, H, use_clip)
    if cached(p, key):
        print("CACHED", s["id"], name); return p
    print("REGEN ", s["id"], name, "(wan clip)" if use_clip else "(ken-burns)")
    t0 = time.time()
    if use_clip:
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration={D},trim=duration={D},setpts=PTS-STARTPTS,format=yuv420p")
        run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-an", "-c:v", "libx264", "-crf", "18", p])
    else:
        run(["ffmpeg", "-y", "-i", src, "-vf", kb_filter(s["kb"], W, H, n), "-frames:v", n,
             "-an", "-c:v", "libx264", "-crf", "18", p])
    mark(p, key)
    log_call("assemble_segment", "ffmpeg", {"aspect": name, "mode": "wan" if use_clip else "kb"}, s["seed"], time.time() - t0, note=s["id"])
    return p


def font(size):
    for f in ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try: return ImageFont.truetype(f, size)
        except OSError: pass
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()


def end_card(name, W, H):
    p = TMP / f"end_{name}.png"
    im = Image.new("RGB", (W, H), (10, 10, 10)); d = ImageDraw.Draw(im)
    lines = [("Made with AI", W // 11, 0.40),
             ("Images: FLUX.1 schnell  |  Voice: Gemini TTS", W // 30, 0.52),
             ("Music: ACE-Step 1.5  |  Motion: Wan 2.2 / FFmpeg", W // 30, 0.57)]
    for text, size, y in lines:
        f = font(size); w = d.textlength(text, font=f)
        d.text(((W - w) / 2, H * y), text, fill=(240, 240, 240), font=f)
    im.save(p); return p


def make_srt():
    def ts(x): return f"{int(x//3600):02}:{int(x%3600//60):02}:{int(x%60):02},{int(x%1*1000):03}"
    out, idx, t = [], 1, 0.0
    for s in shots:
        start, end = t + LEAD, t + s["_dur"] - TAIL
        lines = textwrap.wrap(s["subtitle_en"], 40)
        cues = ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]   # max 2 lines per cue
        weights = [len(c) for c in cues]; tot = sum(weights); cs = start
        for c, w in zip(cues, weights):
            ce = cs + (end - start) * w / tot
            out.append(f"{idx}\n{ts(cs)} --> {ts(ce)}\n{c}\n"); idx += 1; cs = ce
        t += s["_dur"]
    p = TMP / "subs.srt"; p.write_text("\n".join(out), encoding="utf-8"); return p


narr = narration_track(shots, TMP / "narration_all.wav", TMP)
subs = make_srt()
music = OUT / "music" / "score_48k.wav"
if not music.exists():
    raise SystemExit("run stage 4 first (outputs/music/score_48k.wav missing)")

for name, (W, H) in ASPECTS.items():
    t0 = time.time()
    segs = [segment(s, name, W, H) for s in shots]
    endv = TMP / f"end_{name}.mp4"
    run(["ffmpeg", "-y", "-loop", "1", "-i", end_card(name, W, H), "-t", END_S, "-r", FPS,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", endv])
    lst = TMP / f"vlist_{name}.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segs + [endv]))
    fs, mv = SUB_STYLE[name]
    vid = TMP / f"video_{name}.mp4"      # concat + burn subtitles in one pass
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
         f"subtitles={subs.as_posix()}:force_style='FontSize={fs},Outline=2,MarginV={mv}'",
         "-r", FPS, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", vid])
    fc = (f"[1:a]apad=whole_dur={total},asplit=2[vsc][vmix];"
          f"[2:a]volume={MUSIC_GAIN},afade=t=out:st={total-2.5}:d=2.5[m];"
          f"[m][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[duck];"
          f"[vmix][duck]amix=inputs=2:duration=first:normalize=0[mix];"
          f"[mix]loudnorm=I=-14:TP=-1:LRA=11[a]")
    final = FIN / f"film_{name}.mp4"
    run(["ffmpeg", "-y", "-i", vid, "-i", narr, "-stream_loop", "-1", "-i", music,
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", total,
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
    log_call("assemble_final", "ffmpeg", {"aspect": name, "duration": total}, None, time.time() - t0)
    print("wrote", final)