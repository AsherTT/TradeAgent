"""Statistically honest descriptive evaluation over frozen forward outcomes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import log, sqrt
from uuid import UUID

from pydantic import Field, model_validator

from backend.app.contracts.base import ContractModel, utc_now
from backend.app.contracts.evaluation import EvaluationMaturity, StatisticalStatus
from backend.app.contracts.thesis import ForecastRecord, OutcomeRecord


class ForecastEvaluationPolicy(ContractModel):
    """Thresholds are configured per horizon, universe and outcome definition."""

    min_early_sample: int = Field(ge=1)
    horizon_days: int = Field(ge=1)
    min_mature_sample: int = Field(ge=2)
    min_bucket_usable: int = Field(ge=1)
    min_outcome_coverage: float = Field(ge=0, le=1)
    confidence_z: float = Field(default=1.959963984540054, gt=0)

    @model_validator(mode="after")
    def ordered_thresholds(self) -> ForecastEvaluationPolicy:
        if self.min_mature_sample <= self.min_early_sample:
            raise ValueError("mature sample threshold must exceed early threshold")
        return self


class CalibrationBucket(ContractModel):
    probability_low: float
    probability_high: float
    sample_count: int = Field(ge=0)
    mean_predicted_probability: float | None = None
    observed_frequency: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    mfe_mean: float | None = None
    mae_mean: float | None = None
    mean_excess_return: float | None = None
    statistical_status: StatisticalStatus


class ForecastEvaluationReport(ContractModel):
    forecast_count: int = Field(ge=0)
    eligible_forecast_count: int = Field(ge=0)
    sample_count: int = Field(ge=0)
    outcome_coverage: float = Field(ge=0, le=1)
    evaluation_maturity: EvaluationMaturity
    directional_accuracy: float | None = None
    brier_score: float | None = None
    log_loss: float | None = None
    calibration_error: float | None = None
    calibration_curve: tuple[CalibrationBucket, ...]
    invalidation_precision: float | None = None
    invalidation_recall: float | None = None
    buckets: tuple[CalibrationBucket, ...]
    exploratory: bool


def _wilson_interval(successes: int, total: int, z: float) -> tuple[float, float]:
    if total == 0:
        raise ValueError("Wilson interval requires a nonempty sample")
    p = successes / total
    z2 = z * z
    denominator = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denominator
    radius = z * sqrt((p * (1 - p) + z2 / (4 * total)) / total) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def evaluate_forecasts(
    forecasts: tuple[ForecastRecord, ...],
    outcomes: tuple[OutcomeRecord, ...],
    *,
    policy: ForecastEvaluationPolicy,
    as_of: datetime | None = None,
) -> ForecastEvaluationReport:
    """Report one comparable cohort; callers choose horizon/universe/outcome scope."""

    cutoff = as_of or utc_now()
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("evaluation as_of must be timezone-aware")
    cutoff = cutoff.astimezone(UTC)
    forecast_by_id: dict[UUID, ForecastRecord] = {}
    for forecast in forecasts:
        if forecast.forecast_id in forecast_by_id:
            raise ValueError("duplicate forecast identifier")
        if forecasts and forecast.horizon != forecasts[0].horizon:
            raise ValueError("evaluation cohort must use one horizon")
        forecast_by_id[forecast.forecast_id] = forecast
    outcome_by_id: dict[UUID, OutcomeRecord] = {}
    for outcome in outcomes:
        if outcome.forecast_id not in forecast_by_id:
            raise ValueError("outcome has no forecast in cohort")
        if outcome.forecast_id in outcome_by_id:
            raise ValueError("duplicate outcome for forecast")
        if outcome.evaluated_at <= forecast_by_id[outcome.forecast_id].created_at:
            raise ValueError("outcome cannot precede frozen forecast")
        if outcome.evaluated_at < (
            forecast_by_id[outcome.forecast_id].created_at
            + timedelta(days=policy.horizon_days)
        ):
            raise ValueError("outcome precedes configured forecast horizon")
        if outcome.evaluated_at > cutoff:
            raise ValueError("outcome is not yet available at evaluation time")
        outcome_by_id[outcome.forecast_id] = outcome
    n = len(outcome_by_id)
    forecast_count = len(forecasts)
    eligible_count = sum(
        forecast.created_at + timedelta(days=policy.horizon_days) <= cutoff
        for forecast in forecasts
    )
    if n > eligible_count:
        raise ValueError("outcomes exceed eligible matured forecasts")
    coverage = n / eligible_count if eligible_count else 0.0
    if n == 0:
        maturity = (
            EvaluationMaturity.ACCUMULATING if forecast_count else EvaluationMaturity.COLD_START
        )
    elif n >= policy.min_mature_sample and coverage >= policy.min_outcome_coverage:
        maturity = EvaluationMaturity.MATURE
    elif n >= policy.min_early_sample:
        maturity = EvaluationMaturity.EARLY_SAMPLE
    else:
        maturity = EvaluationMaturity.ACCUMULATING

    pairs = tuple(
        (forecast_by_id[identifier], outcome)
        for identifier, outcome in outcome_by_id.items()
    )
    buckets: list[CalibrationBucket] = []
    for index in range(10):
        lower = index / 10
        upper = (index + 1) / 10
        selected = tuple(
            (forecast, outcome)
            for forecast, outcome in pairs
            if lower <= forecast.probability < upper
            or (index == 9 and forecast.probability == 1)
        )
        count = len(selected)
        if count:
            successes = sum(outcome.direction_correct for _, outcome in selected)
            ci_low, ci_high = _wilson_interval(successes, count, policy.confidence_z)
            bucket_status = (
                StatisticalStatus.INSUFFICIENT_SAMPLE
                if count < policy.min_bucket_usable
                else StatisticalStatus.USABLE
                if maturity is EvaluationMaturity.MATURE and count >= policy.min_bucket_usable
                else StatisticalStatus.EARLY_ESTIMATE
            )
            buckets.append(CalibrationBucket(
                probability_low=lower,
                probability_high=upper,
                sample_count=count,
                mean_predicted_probability=sum(f.probability for f, _ in selected) / count,
                observed_frequency=successes / count,
                confidence_interval_low=ci_low,
                confidence_interval_high=ci_high,
                mfe_mean=sum(o.mfe for _, o in selected) / count,
                mae_mean=sum(o.mae for _, o in selected) / count,
                mean_excess_return=sum(o.excess_return for _, o in selected) / count,
                statistical_status=bucket_status,
            ))
        else:
            buckets.append(CalibrationBucket(
                probability_low=lower,
                probability_high=upper,
                sample_count=0,
                statistical_status=StatisticalStatus.INSUFFICIENT_SAMPLE,
            ))
    brier = (
        sum((f.probability - float(o.direction_correct)) ** 2 for f, o in pairs) / n
        if n else None
    )
    log_loss = (
        -sum(
            float(o.direction_correct) * log(max(1e-15, f.probability))
            + (1 - float(o.direction_correct)) * log(max(1e-15, 1 - f.probability))
            for f, o in pairs
        ) / n
        if n else None
    )
    calibration_error = (
        sum(
            bucket.sample_count
            * abs(bucket.mean_predicted_probability - bucket.observed_frequency)
            for bucket in buckets
            if bucket.sample_count
            and bucket.mean_predicted_probability is not None
            and bucket.observed_frequency is not None
        ) / n
        if n else None
    )
    labeled = tuple(o for _, o in pairs if o.invalidation_alert is not None)
    true_positive = sum(o.invalidation_alert is True and o.invalidation_hit for o in labeled)
    predicted_positive = sum(o.invalidation_alert is True for o in labeled)
    actual_positive = sum(o.invalidation_hit for o in labeled)
    return ForecastEvaluationReport(
        forecast_count=forecast_count,
        eligible_forecast_count=eligible_count,
        sample_count=n,
        outcome_coverage=coverage,
        evaluation_maturity=maturity,
        directional_accuracy=sum(o.direction_correct for _, o in pairs) / n if n else None,
        brier_score=brier,
        log_loss=log_loss,
        calibration_error=calibration_error,
        calibration_curve=tuple(buckets),
        invalidation_precision=(
            true_positive / predicted_positive if predicted_positive else None
        ),
        invalidation_recall=(true_positive / actual_positive if actual_positive else None),
        buckets=tuple(buckets),
        exploratory=maturity is not EvaluationMaturity.MATURE,
    )
