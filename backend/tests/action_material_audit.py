"""Offline CLI: --request REQUEST.json --bundle BUNDLE.json (base64 artifact bytes)."""

import argparse
from pathlib import Path

from backend.app.market_data.action_coverage import (
    ActionCoverageRequest,
    ActionMaterialBundle,
    audit_action_materials,
)


def bounded_read(path: Path) -> bytes:
    with path.open("rb") as source:
        payload = source.read(15_000_001)
    if len(payload) > 15_000_000:
        raise ValueError("action audit input exceeds file limit")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    request = ActionCoverageRequest.model_validate_json(bounded_read(args.request))
    bundle = ActionMaterialBundle.model_validate_json(bounded_read(args.bundle))
    print(audit_action_materials(request, bundle).model_dump_json())
