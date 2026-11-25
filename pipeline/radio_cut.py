"""Radio cut: narration + (optional) temp music on black. Output: outputs/final/radio_cut.mp4
Put any quiet royalty-free track at outputs/music/temp.mp3 (optional)."""
import pathlib
from common import load_storyboard
from media import add_durations, narration_track, run

sb = load_storyboard()
shots = add_durations(sb["shots"])
tmp = pathlib.Path("outputs/tmp"); tmp.mkdir(parents=True, exist_ok=True)
pathlib.Path("outputs/final").mkdir(parents=True, exist_ok=True)
total = sum(s["_dur"] for s in shots)
narr = narration_track(shots, tmp / "radio_narr.wav", tmp)

temp = next((p for p in [pathlib.Path("outputs/music/temp.mp3"), pathlib.Path("outputs/music/temp.wav")] if p.exists()), None)
cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=24:d={total}", "-i", narr]
if temp:
    cmd += ["-stream_loop", "-1", "-i", temp, "-filter_complex",
            "[2:a]volume=0.15[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]"]
else:
    cmd += ["-map", "0:v", "-map", "1:a"]
cmd += ["-t", total, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "outputs/final/radio_cut.mp4"]
run(cmd)
print(f"radio cut written, {total:.1f}s -> outputs/final/radio_cut.mp4")