"""Generate a full deck of images via FAL from a manifest JSON.

Usage: python scripts/generate_deck.py manifests/part-1.json [--fast] [--refs-only] [--force]

Reads FAL_KEY from .env. Idempotent: skips files that already exist,
so re-runs only generate missing items. Never hardcode the key.

Items with a "reference" field (path relative to output_dir, e.g. a
character lock) are generated via FLUX Redux with that image uploaded
as the character reference, keeping characters on-model across scenes.
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
        sys.exit("Usage: generate_deck.py <manifest.json> [--fast] [--refs-only] [--force]")

    manifest = json.loads(Path(sys.argv[1]).read_text())
    model = "fal-ai/flux/schnell" if "--fast" in sys.argv else "fal-ai/flux/dev"
    refs_only = "--refs-only" in sys.argv
    force = "--force" in sys.argv
    out_root = Path(manifest["output_dir"])
    failures = []
    uploads = {}  # local reference path -> uploaded FAL URL

    for item in manifest["items"]:
        reference = item.get("reference")
        if refs_only and not reference:
            continue
        out_path = out_root / item["file"]
        if out_path.exists() and not force:
            print(f"SKIP (exists): {out_path}")
            continue
        try:
            arguments = {
                "prompt": item["prompt"],
                "image_size": "portrait_16_9",  # vertical 9:16
                "num_images": 1,
            }
            endpoint = model
            if reference:
                ref_path = out_root / reference
                if ref_path not in uploads:
                    print(f"Uploading reference: {ref_path}")
                    uploads[ref_path] = fal_client.upload_file(ref_path)
                if item.get("mode") == "pulid":
                    # PuLID: face-identity lock (strongest consistency for faces)
                    arguments["reference_image_url"] = uploads[ref_path]
                    endpoint = "fal-ai/flux-pulid"
                else:
                    # Redux: style/content guide (fine for helmed figures, objects)
                    arguments["image_url"] = uploads[ref_path]
                    endpoint = "fal-ai/flux/dev/redux"
            print(f"Generating {out_path} via {endpoint} ...")
            result = fal_client.subscribe(endpoint, arguments=arguments)
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
