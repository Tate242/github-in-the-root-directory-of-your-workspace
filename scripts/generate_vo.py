"""Generate voiceover lines via FAL TTS (Kokoro).

Usage: python scripts/generate_vo.py manifests/part-1-vo.json

Reads FAL_KEY from .env. Idempotent: skips files that already exist.
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
        sys.exit("Usage: generate_vo.py <manifest.json>")

    manifest = json.loads(Path(sys.argv[1]).read_text())
    voice = manifest.get("voice", "am_michael")
    out_root = Path(manifest["output_dir"])
    failures = []

    for item in manifest["items"]:
        out_path = out_root / item["file"]
        if out_path.exists():
            print(f"SKIP (exists): {out_path}")
            continue
        print(f"Voicing {out_path} ...")
        try:
            result = fal_client.subscribe(
                "fal-ai/kokoro/american-english",
                arguments={"prompt": item["text"], "voice": voice},
            )
            url = result["audio"]["url"]
            out_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, out_path)
            print("  saved.")
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failures.append(item["file"])

    print("\nVO complete." if not failures else f"\nFailures: {failures}")


if __name__ == "__main__":
    main()
