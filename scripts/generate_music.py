"""Generate the background score via FAL (Stable Audio).

Usage: python scripts/generate_music.py

Reads FAL_KEY from .env. Skips if the track already exists.
"""
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import fal_client  # noqa: E402  (after dotenv so FAL_KEY is available)

PROMPT = (
    "dark epic cinematic tension score, deep pulsing drone, sparse heavy hits, "
    "mysterious sci-fi fantasy atmosphere, slow build, no vocals, no melody hooks"
)
OUT = Path("generated-assets/part-1/music/score.wav")


def main() -> None:
    if OUT.exists():
        print(f"SKIP (exists): {OUT}")
        return
    print(f"Composing {OUT} ...")
    try:
        result = fal_client.subscribe(
            "fal-ai/stable-audio-25/text-to-audio",
            arguments={"prompt": PROMPT, "seconds_total": 45},
        )
        audio = result.get("audio_file") or result.get("audio")
        url = audio["url"]
        OUT.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, OUT)
        print("  saved.")
    except Exception as exc:
        sys.exit(f"FAILED: {exc}")


if __name__ == "__main__":
    main()
