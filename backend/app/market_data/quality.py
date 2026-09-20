"""Fail-closed provider qualification rules."""

from backend.app.contracts.evaluation import DataQualityStatus, ProviderQualityReport
from backend.app.contracts.instrument import CorporateAction
from backend.app.contracts.market import MarketBar


class ProviderQualityError(ValueError):
    """Raised when provider data cannot be used for the requested integrity level."""


_QUALITY_RANK = {
    DataQualityStatus.VERIFIED: 0,
    DataQualityStatus.ACCEPTABLE: 1,
    DataQualityStatus.DEGRADED: 2,
    DataQualityStatus.UNVERIFIED: 3,
    DataQualityStatus.REJECTED: 4,
}


def worse_quality(
    left: DataQualityStatus, right: DataQualityStatus
) -> DataQualityStatus:
    """Return the less trustworthy of two quality assessments."""

    return max((left, right), key=_QUALITY_RANK.__getitem__)


def require_strict_backtest_eligible(report: ProviderQualityReport) -> None:
    eligible = {DataQualityStatus.VERIFIED, DataQualityStatus.ACCEPTABLE}
    if report.quality_status not in eligible:
        raise ProviderQualityError(
            f"provider {report.provider}@{report.provider_version} is not eligible for strict "
            f"backtests: {report.quality_status.value}"
        )
    if report.golden_case_count == 0 or report.passed_case_count != report.golden_case_count:
        raise ProviderQualityError(
            f"provider {report.provider}@{report.provider_version} is not eligible for strict "
            "backtests: golden-case qualification is incomplete"
        )
    if report.coverage < 1 or report.failed_cases:
        raise ProviderQualityError(
            f"provider {report.provider}@{report.provider_version} is not eligible for strict "
            "backtests: qualification coverage is incomplete"
        )


def require_strict_bars_eligible(bars: tuple[MarketBar, ...]) -> None:
    eligible = {DataQualityStatus.VERIFIED, DataQualityStatus.ACCEPTABLE}
    rejected = [bar for bar in bars if bar.data_quality_status not in eligible]
    if rejected:
        raise ProviderQualityError(
            f"{len(rejected)} market bars are not eligible for strict backtests"
        )


def require_report_matches_bars(
    report: ProviderQualityReport, bars: tuple[MarketBar, ...]
) -> None:
    mismatched = [
        bar
        for bar in bars
        if bar.source != report.provider
        or bar.provider_quality_version != report.provider_version
    ]
    if mismatched:
        raise ProviderQualityError(
            f"{len(mismatched)} market bars do not match provider qualification provenance"
        )


def require_report_matches_actions(
    report: ProviderQualityReport, actions: tuple[CorporateAction, ...]
) -> None:
    mismatched = [
        action
        for action in actions
        if action.source != report.provider
        or action.provider_quality_version != report.provider_version
    ]
    if mismatched:
        raise ProviderQualityError(
            f"{len(mismatched)} corporate actions do not match provider qualification provenance"
        )
