from __future__ import annotations

import inspect
import pytest

from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_json,
    sample_historical_market_days,
)


def test_sampling_golden_vector_is_reproducible_and_spans_window() -> None:
    request = HistoricalSamplingRequest(
        strategy="funding-carry",
        start_date="2026-01-01",
        end_date="2026-01-31",
        sample_size=5,
        seed="stage2-baseline-v1",
    )

    result = sample_historical_market_days(request)

    assert result.population_size == 31
    assert result.selected_dates == (
        "2026-01-01",
        "2026-01-08",
        "2026-01-13",
        "2026-01-22",
        "2026-01-29",
    )
    assert [item.sha256 for item in result.strata] == [
        "f4bf2e23e50f0ff64d56783b6fb8078cd6389d3370482d47b29435ff656033d2",
        "2ba942785a74a4cfa6dc28345b28c2b1e1431e6f97d54f7c60a221374dc80d6d",
        "59c3279e5095ce76aaca1d43d3a8029fe5db6a5ecf25747e3708020c8a1cd576",
        "dff7deb3f74a7cbdb791a117fb7aaebcd1c0881b39cc6ab52895e77b71b1c079",
        "85413829400e9f1b7f2aaad7470dbf125b805a9852249a3e8ffcbdbbce12cf61",
    ]
    assert [(item.population_start_index, item.population_end_index_exclusive) for item in result.strata] == [
        (0, 6),
        (6, 12),
        (12, 18),
        (18, 24),
        (24, 31),
    ]


def test_same_request_is_byte_for_byte_deterministic() -> None:
    request = HistoricalSamplingRequest(
        strategy="cash-and-carry",
        start_date="2026-04-01",
        end_date="2026-06-30",
        sample_size=30,
        seed="stage2-wave-a",
    )

    first = historical_sampling_json(sample_historical_market_days(request))
    second = historical_sampling_json(sample_historical_market_days(request))

    assert first == second


def test_strategy_and_seed_are_hash_domain_separators() -> None:
    funding = sample_historical_market_days(
        HistoricalSamplingRequest(
            strategy="funding-carry",
            start_date="2026-01-01",
            end_date="2026-03-31",
            sample_size=10,
            seed="same-seed",
        )
    )
    cash = sample_historical_market_days(
        HistoricalSamplingRequest(
            strategy="cash-and-carry",
            start_date="2026-01-01",
            end_date="2026-03-31",
            sample_size=10,
            seed="same-seed",
        )
    )
    other_seed = sample_historical_market_days(
        HistoricalSamplingRequest(
            strategy="funding-carry",
            start_date="2026-01-01",
            end_date="2026-03-31",
            sample_size=10,
            seed="different-seed",
        )
    )

    assert [item.sha256 for item in funding.strata] != [
        item.sha256 for item in cash.strata
    ]
    assert [item.sha256 for item in funding.strata] != [
        item.sha256 for item in other_seed.strata
    ]


def test_full_population_request_selects_every_calendar_day_once() -> None:
    request = HistoricalSamplingRequest(
        strategy="funding-carry",
        start_date="2026-02-01",
        end_date="2026-02-05",
        sample_size=99,
        seed="full-population",
    )

    result = sample_historical_market_days(request)

    assert result.population_size == 5
    assert result.selected_count == 5
    assert result.selected_dates == (
        "2026-02-01",
        "2026-02-02",
        "2026-02-03",
        "2026-02-04",
        "2026-02-05",
    )
    assert all(item.width == 1 for item in result.strata)
    assert all(item.offset == 0 for item in result.strata)


def test_sampling_rejects_invalid_request_boundaries() -> None:
    with pytest.raises(ValueError, match="sample_size must be positive"):
        HistoricalSamplingRequest(
            strategy="funding-carry",
            start_date="2026-01-01",
            end_date="2026-01-31",
            sample_size=0,
            seed="x",
        )

    with pytest.raises(ValueError, match="end_date must not be before"):
        HistoricalSamplingRequest(
            strategy="funding-carry",
            start_date="2026-02-01",
            end_date="2026-01-31",
            sample_size=1,
            seed="x",
        )

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        HistoricalSamplingRequest(
            strategy="funding-carry",
            start_date="2026/01/01",
            end_date="2026-01-31",
            sample_size=1,
            seed="x",
        )

    with pytest.raises(ValueError, match="unsupported"):
        HistoricalSamplingRequest(
            strategy="other",
            start_date="2026-01-01",
            end_date="2026-01-31",
            sample_size=1,
            seed="x",
        )

    with pytest.raises(ValueError, match="seed is required"):
        HistoricalSamplingRequest(
            strategy="funding-carry",
            start_date="2026-01-01",
            end_date="2026-01-31",
            sample_size=1,
            seed="",
        )


def test_sampler_contract_has_no_market_or_profitability_inputs() -> None:
    parameters = tuple(inspect.signature(sample_historical_market_days).parameters)
    request_fields = tuple(HistoricalSamplingRequest.__dataclass_fields__)

    assert parameters == ("request",)
    assert request_fields == (
        "strategy",
        "start_date",
        "end_date",
        "sample_size",
        "seed",
        "policy_version",
    )
    assert not {
        "return",
        "profit",
        "funding_rate",
        "basis",
        "volatility",
        "qualification",
    }.intersection(request_fields)


def test_each_selection_is_inside_its_nonoverlapping_stratum() -> None:
    request = HistoricalSamplingRequest(
        strategy="cash-and-carry",
        start_date="2026-01-01",
        end_date="2026-12-31",
        sample_size=30,
        seed="annual-sample-v1",
    )
    result = sample_historical_market_days(request)

    previous_end = 0
    for item in result.strata:
        assert item.population_start_index == previous_end
        assert (
            item.population_start_index
            <= item.selected_population_index
            < item.population_end_index_exclusive
        )
        previous_end = item.population_end_index_exclusive

    assert previous_end == result.population_size
