"""Assemble Part 1: video clips + voiceover + score -> final 45s vertical mp4.

Usage: python scripts/assemble_part1.py

Requires ffmpeg on PATH. Reads clips/VO/score from generated-assets/part-1/.
Timing follows the approved shot table (part-1-the-fallen-star.md).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path("generated-assets/part-1")
NORM = ROOT / "clips-norm"
OUT = ROOT / "part-1-final.mp4"

# (clip, start_s, duration_s) — from the shot table
SHOTS = [
    ("s1-aerial-starfall", 0, 3),
    ("s2-ceremony-standup", 3, 5),
    ("s3-guard-charge", 8, 5),
    ("s4-zilex-closeup", 13, 5),
    ("s5-parents-dragged", 18, 5),
    ("s6-chase", 23, 5),
    ("s7-crater-stone", 28, 4),
    ("s8-hand-stone", 32, 3),
    ("s9-alia-throne", 35, 5),
    ("s10-direct-address", 40, 5),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd)[:120])
    subprocess.run(cmd, check=True)


def main() -> None:
    for name, _, _ in SHOTS:
        for candidate in [ROOT / "shots" / f"{name}.mp4"]:
            if not candidate.exists():
                sys.exit(f"Missing clip: {candidate}")
    for name, _, _ in SHOTS:
        if not (ROOT / "vo" / f"{name.split('-')[0]}.wav").exists():
            sys.exit(f"Missing VO: {name.split('-')[0]}.wav")
    if not (ROOT / "music" / "score.wav").exists():
        sys.exit("Missing score.wav")

    # 1) Normalize each clip: trim to shot duration, scale/crop to 1080x1920, no audio
    NORM.mkdir(parents=True, exist_ok=True)
    for name, _, dur in SHOTS:
        run([
            "ffmpeg", "-y", "-i", str(ROOT / "shots" / f"{name}.mp4"),
            "-t", str(dur),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-an", "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264",
            str(NORM / f"{name}.mp4"),
        ])

    # 2) Concat the video track (uniform codec params -> stream copy)
    concat_list = NORM / "list.txt"
    concat_list.write_text("".join(f"file '{name}.mp4'\n" for name, _, _ in SHOTS))
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy", str(ROOT / "video-track.mp4"),
    ])

    # 3) Build the VO track: each line delayed to its shot start, then mixed
    vo_inputs, delays = [], []
    for i, (name, start, _) in enumerate(SHOTS):
        vo_inputs += ["-i", str(ROOT / "vo" / f"{name.split('-')[0]}.wav")]
        delays.append(f"[{i}:a]adelay={start * 1000}|{start * 1000}[v{i}]")
    mix_in = "".join(f"[v{i}]" for i in range(len(SHOTS)))
    run([
        "ffmpeg", "-y", *vo_inputs,
        "-filter_complex", ";".join(delays) + f";{mix_in}amix=inputs={len(SHOTS)}:normalize=0[vo]",
        "-map", "[vo]", "-t", "45", str(ROOT / "vo-track.m4a"),
    ])

    # 4) Final mux: video + VO over a ducked score
    run([
        "ffmpeg", "-y",
        "-i", str(ROOT / "video-track.mp4"),
        "-i", str(ROOT / "vo-track.m4a"),
        "-i", str(ROOT / "music" / "score.wav"),
        "-filter_complex",
        "[2:a]atrim=0:45,volume=0.18[m];[1:a]volume=1.0[v];[v][m]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(OUT),
    ])
    print(f"\nFinal cut: {OUT}")


if __name__ == "__main__":
    main()
