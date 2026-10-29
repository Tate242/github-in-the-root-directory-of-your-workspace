"""Generate a full deck of images via FAL from a manifest JSON.

Usage: python scripts/generate_deck.py manifests/part-1.json [--fast]

Reads FAL_KEY from .env. Idempotent: skips files that already exist,
so re-runs only generate missing items. Never hardcode the key.
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
        sys.exit("Usage: generate_deck.py <manifest.json> [--fast]")

    manifest = json.loads(Path(sys.argv[1]).read_text())
    model = "fal-ai/flux/schnell" if "--fast" in sys.argv else "fal-ai/flux/dev"
    out_root = Path(manifest["output_dir"])
    failures = []

    for item in manifest["items"]:
        out_path = out_root / item["file"]
        if out_path.exists():
            print(f"SKIP (exists): {out_path}")
            continue
        print(f"Generating {out_path} ...")
        try:
            result = fal_client.subscribe(
                model,
                arguments={
                    "prompt": item["prompt"],
                    "image_size": "portrait_16_9",  # vertical 9:16
                    "num_images": 1,
                },
            )
            url = result["images"][0]["url"]
            out_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, out_path)
            print("  saved.")
        except Exception as exc:  # keep going; report at end
            print(f"  FAILED: {exc}")
            failures.append(item["file"])

    print("\nDeck complete." if not failures else f"\nFailures: {failures}")


if __name__ == "__main__":
    main()
