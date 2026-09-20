"""Prepared image-input demo. Default prints the request shape, makes no API call."""

import argparse
import base64
import json
from pathlib import Path

from carrito.model import native_call
from carrito.store import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
parser.add_argument("--image", type=Path, default=ROOT / "data/demo/product-card.png")
args = parser.parse_args()
encoded = base64.b64encode(args.image.read_bytes()).decode()
messages = [
    {
        "role": "developer",
        "content": (
            "Describe only visible evidence. "
            "Do not infer stock, warranty or battery life from a picture."
        ),
    },
    {
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": "¿Qué sabemos de este producto y qué habría que consultar?",
            },
            {"type": "input_image", "image_url": "data:image/png;base64," + encoded},
        ],
    },
]
if args.mode == "live":
    print(json.dumps(native_call(messages), ensure_ascii=False, indent=2))
else:
    # Do not print the large base64 payload; show the shape students need to inspect.
    messages[1]["content"][1]["image_url"] = "data:image/png;base64,<local image bytes>"
    print(
        json.dumps(
            {
                "mode": "fixture",
                "api_called": False,
                "messages": messages,
                "observation": (
                    "The card shows P001 and 69,90 EUR. It does not prove stock or battery life."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
