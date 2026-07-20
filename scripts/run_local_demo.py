from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from local_demo.pipeline import run_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the credential-free casino platform demo")
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--seed", type=int, default=int(os.getenv("DEMO_RANDOM_SEED", "355")))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.getenv("DEMO_OUTPUT_DIR", "build/demo")),
    )
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output_dir, count=args.count, seed=args.seed), indent=2))


if __name__ == "__main__":
    main()
