"""Forward evaluation is scheduled only with an explicit horizon policy."""

import pytest
from pydantic import ValidationError

from backend.app.config import Settings
from backend.app.jobs.celery_app import create_celery


def test_forward_evaluation_schedule_defaults_off() -> None:
    settings = Settings(_env_file=None, forward_evaluation_enabled=False)
    assert "evaluate-due-forward-forecasts" not in create_celery(settings).conf.beat_schedule


def test_forward_evaluation_schedule_requires_horizon_mapping() -> None:
    with pytest.raises(ValidationError, match="positive horizon mappings"):
        Settings(_env_file=None, forward_evaluation_enabled=True)
    settings = Settings(
        _env_file=None,
        forward_evaluation_enabled=True,
        forward_evaluation_interval_seconds=300,
        forward_evaluation_horizon_days={"5d": 5},
    )
    schedule = create_celery(settings).conf.beat_schedule
    assert schedule["evaluate-due-forward-forecasts"]["task"] == "evaluation.run_due"
    assert schedule["evaluate-due-forward-forecasts"]["schedule"] == 300
