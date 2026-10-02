"""Declared material completeness never promotes market/provider qualification."""

from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.market_data.action_coverage import (
    ActionCoverageRequest,
    ActionFileArtifact,
    ActionMaterialBundle,
    audit_action_materials,
)

NOW = datetime(2026, 10, 2, 20, tzinfo=UTC)
DAY = date(2026, 10, 1)
ID = uuid4()


def request() -> ActionCoverageRequest:
    return ActionCoverageRequest(
        instrument_id=ID, window_start=NOW-timedelta(days=1), window_end=NOW,
        cutoff=NOW, first_session=DAY, last_session=DAY, sessions=(DAY,),
        calendar_uri="https://example.org/fixture-calendar", calendar_hash="a"*64,
    )


def bundle() -> ActionMaterialBundle:
    content = b"fixture explicit no update"
    return ActionMaterialBundle(
        instrument_id=ID, source_product="nasdaq.daily_list", specification_version="fixture-v1",
        files=tuple(ActionFileArtifact(
            kind=kind, session=DAY-timedelta(days=1) if kind == "baseline" else DAY,
            raw_content=content, content_hash=sha256(content).hexdigest(),
            observed_at=NOW, revisions_closed_through=NOW, records_complete=True,
            records_understood=True, revision_chain_closed=True, explicit_no_update=True,
        ) for kind in ("baseline", "equity", "dividends", "next_day")),
    )


def test_complete_declared_material_is_never_provider_qualified() -> None:
    result = audit_action_materials(request(), bundle())
    assert result.material_checks_passed
    assert not result.provider_qualified and not result.historical_pit_qualified
    assert ActionMaterialBundle.model_validate_json(bundle().model_dump_json()) == bundle()


@pytest.mark.parametrize("change", [
    {"content_hash": "b"*64}, {"observed_at": NOW+timedelta(seconds=1)},
    {"revisions_closed_through": NOW-timedelta(seconds=1)},
    {"records_complete": False}, {"records_understood": False},
    {"revision_chain_closed": False}, {"explicit_no_update": False},
    {"has_data_rows": True}, {"session": DAY+timedelta(days=1)},
])
def test_bad_artifact_fails_with_inspectable_gaps(change: dict[str, object]) -> None:
    data = bundle()
    data = data.model_copy(update={
        "files": (*data.files[:-1], data.files[-1].model_copy(update=change)),
    })
    result = audit_action_materials(request(), data)
    assert not result.material_checks_passed
    assert result.gaps and not result.provider_qualified


@pytest.mark.parametrize("change", ["missing", "duplicate", "baseline", "identity"])
def test_missing_duplicate_baseline_or_foreign_subject_are_rejected(change: str) -> None:
    data = bundle()
    changes = {
        "missing": {"files": data.files[:-1]},
        "duplicate": {"files": (*data.files, data.files[-1])},
        "baseline": {"files": data.files[1:]},
        "identity": {"instrument_id": uuid4()},
    }
    result = audit_action_materials(request(), data.model_copy(update=changes[change]))
    assert not result.material_checks_passed


def test_unordered_calendar_and_naive_cutoff_are_invalid() -> None:
    data = request().model_dump()
    for changes in ({"sessions": (DAY, DAY)}, {"cutoff": NOW.replace(tzinfo=None)}):
        with pytest.raises(ValidationError):
            ActionCoverageRequest.model_validate({**data, **changes})
