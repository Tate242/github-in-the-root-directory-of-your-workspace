"""Animate keyframes into video clips via FAL image-to-video (Kling).

Usage: python scripts/generate_video.py manifests/part-1-video.json [--only <substr>]

Reads FAL_KEY from .env. Idempotent: skips clips that already exist.
Each item uploads its keyframe as the start frame and animates per the prompt.
"""
import json
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import fal_client  # noqa: E402  (after dotenv so FAL_KEY is available)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: generate_video.py <manifest.json> [--only <substr>]")

    manifest = json.loads(Path(sys.argv[1]).read_text())
    model = manifest.get("model", "fal-ai/kling-video/v1.6/standard/image-to-video")
    out_root = Path(manifest["output_dir"])
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    failures = []

    for item in manifest["items"]:
        out_path = out_root / item["file"]
        if only and only not in item["file"]:
            continue
        if out_path.exists():
            print(f"SKIP (exists): {out_path}")
            continue
        print(f"Animating {out_path} ...")
        try:
            image_url = fal_client.upload_file(out_root / item["keyframe"])
            result = fal_client.subscribe(
                model,
                arguments={
                    "prompt": item["prompt"],
                    "image_url": image_url,
                    "duration": "5",
                },
            )
            url = result["video"]["url"]
            out_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, out_path)
            print("  saved.")
        except Exception as exc:  # keep going; report at end
            print(f"  FAILED: {exc}")
            failures.append(item["file"])

    print("\nAll clips complete." if not failures else f"\nFailures: {failures}")


if __name__ == "__main__":
    main()
