"""Generate one image via FAL (flux) from a prompt.

Usage: python scripts/generate_image.py "<prompt>" <output_path> [--fast]

Reads FAL_KEY from .env. Never hardcode the key.
"""
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import fal_client  # noqa: E402  (after dotenv so FAL_KEY is available)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("Usage: generate_image.py <prompt> <output_path> [--fast]")

    prompt, out_path = sys.argv[1], Path(sys.argv[2])
    fast = "--fast" in sys.argv
    model = "fal-ai/flux/schnell" if fast else "fal-ai/flux/dev"

    print(f"Generating with {model} -> {out_path}")
    result = fal_client.subscribe(
        model,
        arguments={
            "prompt": prompt,
            "image_size": "portrait_16_9",  # vertical 9:16
            "num_images": 1,
        },
    )
    url = result["images"][0]["url"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out_path)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
