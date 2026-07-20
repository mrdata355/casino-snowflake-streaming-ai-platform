from __future__ import annotations

import argparse
import json
from pathlib import Path

from local_demo.generator import generate_slot_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic slot events")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=355)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(
            json.dumps(event.to_dict(), sort_keys=True) + "\n"
            for event in generate_slot_events(args.count, args.seed)
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.count} base events plus the deterministic duplicate to {args.out}")


if __name__ == "__main__":
    main()
