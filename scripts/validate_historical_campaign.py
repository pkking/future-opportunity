from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from future_opportunity.backtest.campaign import (
    load_historical_campaign_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-items", type=int, default=31)
    args = parser.parse_args()

    campaign = load_historical_campaign_manifest(
        args.manifest,
        max_items=args.max_items,
    )
    payload = {
        "schema_version": campaign.schema_version,
        "campaign_id": campaign.campaign_id,
        "items": [
            {
                "source_workflow_run": item.source_workflow_run,
                "compact_artifact_name": item.compact_artifact_name,
            }
            for item in campaign.items
        ],
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as output:
            output.write(f"campaign_id={campaign.campaign_id}\n")
            output.write(f"item_count={len(campaign.items)}\n")


if __name__ == "__main__":
    main()
