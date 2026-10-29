"""Burn per-shot captions into the final cut (libass subtitles).

Usage: python scripts/burn_captions.py

Reads dialogue from manifests/part-1-vo.json and shot timing from
assemble_part1.SHOTS so captions always match the assembled timeline.
Output: generated-assets/part-1/part-1-final-captioned.mp4
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from assemble_part1 import ROOT, SHOTS  # noqa: E402

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,2,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_time(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:05.2f}"


def main() -> None:
    vo = json.loads(Path("manifests/part-1-vo.json").read_text())
    total = 42.8  # assembled duration (ffprobe-verified)

    events = []
    for (name, start, dur), item in zip(SHOTS, vo["items"]):
        end = min(start + dur, total)
        text = item["text"].replace("...", "\\N\\N")  # pause = line-breath
        events.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}"
        )

    ass_path = ROOT / "captions.ass"
    ass_path.write_text(ASS_HEADER + "\n".join(events) + "\n")

    out = ROOT / "part-1-final-captioned.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(ROOT / "part-1-final.mp4"),
            "-vf", f"ass={ass_path}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", str(out),
        ],
        check=True,
    )
    print(f"Captioned cut: {out}")


if __name__ == "__main__":
    main()
