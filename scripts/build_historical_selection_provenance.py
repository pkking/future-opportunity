from __future__ import annotations

import argparse
import json
from pathlib import Path

from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    selection_provenance_from_sampling_evidence,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sampling_evidence", type=Path)
    parser.add_argument("--source-workflow-run", required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads(args.sampling_evidence.read_text())
    provenance = selection_provenance_from_sampling_evidence(
        raw,
        source_workflow_run=args.source_workflow_run,
        artifact_name=args.artifact_name,
        artifact_id=args.artifact_id,
        artifact_digest=args.artifact_digest,
    )
    payload = historical_selection_provenance_payload(provenance)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
