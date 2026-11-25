"""FFmpeg helpers."""
import pathlib, subprocess
from common import LEAD, TAIL


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("command failed:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-2000:])
    return r.stdout


def probe(path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", path]).strip())


def add_durations(shots):
    """Shot length = narration length + lead + tail. Narration drives the timing."""
    for s in shots:
        s["_narr"] = pathlib.Path("outputs/narration") / f"{s['id']}.wav"
        s["_dur"] = round(probe(s["_narr"]) + LEAD + TAIL, 2)
    return shots


def narration_track(shots, out_path, tmp_dir):
    """One stereo 48 kHz file; each line is delayed by LEAD and padded to its shot length."""
    tmp_dir = pathlib.Path(tmp_dir)
    parts = []
    for s in shots:
        p = tmp_dir / f"n_{s['id']}.wav"
        run(["ffmpeg", "-y", "-i", s["_narr"], "-af",
             f"adelay={int(LEAD*1000)}:all=1,apad=whole_dur={s['_dur']}",
             "-ar", "48000", "-ac", "2", "-t", s["_dur"], p])
        parts.append(p)
    lst = tmp_dir / "narr_list.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out_path])
    return out_path