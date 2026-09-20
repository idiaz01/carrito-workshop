"""S3: uv run --extra langchain python examples/langchain_comparison.py."""

import argparse
import json

from carrito.langchain_demo import run_comparison


def main():
    parser = argparse.ArgumentParser(description="Same Carrito catalog through LangChain")
    parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    args = parser.parse_args()
    print(json.dumps(run_comparison(live=args.mode == "live"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
