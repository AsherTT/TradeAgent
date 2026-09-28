"""Forward evaluation keeps small samples descriptive and shows bucket uncertainty."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.contracts.evaluation import EvaluationMaturity, StatisticalStatus
from backend.app.contracts.thesis import Direction, ForecastRecord, OutcomeRecord
from backend.app.evaluation import ForecastEvaluationPolicy, evaluate_forecasts

NOW = datetime(2026, 9, 28, tzinfo=UTC)
POLICY = ForecastEvaluationPolicy(
    min_early_sample=2,
    min_mature_sample=4,
    min_bucket_usable=3,
    min_outcome_coverage=0.8,
)


def _forecast(probability: float) -> ForecastRecord:
    return ForecastRecord(
        research_run_id=uuid4(),
        instrument_id=uuid4(),
        created_at=NOW,
        analysis_timestamp=NOW,
        horizon="3-5 days",
        direction=Direction.BULLISH,
        probability=probability,
        thesis_id=uuid4(),
        thesis_version=1,
        model_execution_ids=(uuid4(),),
        evidence_ids=(uuid4(),),
    )


def _outcome(forecast: ForecastRecord, correct: bool) -> OutcomeRecord:
    actual = 0.1 if correct else -0.1
    return OutcomeRecord(
        forecast_id=forecast.forecast_id,
        actual_return=actual,
        benchmark_return=0,
        excess_return=actual,
        direction_correct=correct,
        mfe=0.2,
        mae=-0.2,
        invalidation_hit=False,
        evaluated_at=NOW + timedelta(days=6),
    )


def test_evaluation_cold_start_and_accumulation() -> None:
    empty = evaluate_forecasts((), (), policy=POLICY)
    assert empty.evaluation_maturity is EvaluationMaturity.COLD_START
    assert all(bucket.sample_count == 0 for bucket in empty.buckets)
    forecast = _forecast(0.75)
    accumulating = evaluate_forecasts((forecast,), (), policy=POLICY)
    assert accumulating.evaluation_maturity is EvaluationMaturity.ACCUMULATING
    assert accumulating.brier_score is None


def test_calibration_bucket_reports_n_wilson_interval_and_maturity() -> None:
    forecasts = tuple(_forecast(probability) for probability in (0.71, 0.74, 0.76, 0.78))
    outcomes = tuple(_outcome(f, correct) for f, correct in zip(
        forecasts, (True, True, False, True), strict=True
    ))
    report = evaluate_forecasts(forecasts, outcomes, policy=POLICY)
    assert report.evaluation_maturity is EvaluationMaturity.MATURE
    assert report.exploratory is False
    bucket = report.buckets[7]
    assert bucket.sample_count == 4
    assert bucket.mean_predicted_probability == pytest.approx(0.7475)
    assert bucket.observed_frequency == 0.75
    assert bucket.confidence_interval_low is not None
    assert bucket.confidence_interval_high is not None
    assert bucket.confidence_interval_low < 0.75 < bucket.confidence_interval_high
    assert bucket.statistical_status is StatisticalStatus.USABLE
    assert report.brier_score == pytest.approx(
        sum((f.probability - float(o.direction_correct)) ** 2
            for f, o in zip(forecasts, outcomes, strict=True)) / 4
    )


def test_small_bucket_stays_insufficient_even_with_mature_cohort() -> None:
    forecasts = tuple(_forecast(p) for p in (0.75, 0.85, 0.86, 0.87))
    outcomes = tuple(_outcome(f, True) for f in forecasts)
    report = evaluate_forecasts(forecasts, outcomes, policy=POLICY)
    assert report.evaluation_maturity is EvaluationMaturity.MATURE
    assert report.buckets[7].sample_count == 1
    assert report.buckets[7].statistical_status is StatisticalStatus.INSUFFICIENT_SAMPLE


def test_unmatched_or_duplicate_outcomes_are_rejected() -> None:
    forecast = _forecast(0.75)
    outcome = _outcome(forecast, True)
    with pytest.raises(ValueError, match="duplicate outcome"):
        evaluate_forecasts((forecast,), (outcome, outcome), policy=POLICY)
    with pytest.raises(ValueError, match="no forecast"):
        evaluate_forecasts((), (outcome,), policy=POLICY)
