from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Fixed before any 2025 archive query. These are *source probes*, not draws
# for historical strategy evaluation or substitutes for pinned market days.
CASH_EXPIRY_PROBE_TARGETS = (
    ("2025-09-12", "BTC-USDT-250926"),
    ("2025-09-19", "BTC-USDT-250926"),
    ("2025-12-12", "BTC-USDT-251226"),
    ("2025-12-19", "BTC-USDT-251226"),
)


@dataclass(frozen=True, slots=True)
class CashExpiryProbeResult:
    market_date: str
    expected_future_id: str
    status: str
    reason: str
    raw_archive_sha256: str | None

    def to_payload(self) -> dict[str, str | None]:
        return {
            "market_date": self.market_date,
            "expected_future_id": self.expected_future_id,
            "status": self.status,
            "reason": self.reason,
            "raw_archive_sha256": self.raw_archive_sha256,
        }


def evaluate_cash_expiry_probe(
    report: dict[str, Any],
    *,
    market_date: str,
    expected_future_id: str,
) -> CashExpiryProbeResult:
    if report.get("market_date") != market_date:
        raise ValueError("Cash source probe report date differs from frozen target")
    status = report.get("status")
    if status == "no_unique_future_chain_archive":
        return CashExpiryProbeResult(
            market_date,
            expected_future_id,
            "unavailable",
            "no_unique_future_chain_archive",
            None,
        )
    if status not in {"future_discovered", "multiple_future_contracts"}:
        return CashExpiryProbeResult(
            market_date, expected_future_id, "error", "unsupported_discovery_status", None
        )

    catalog = report.get("catalog")
    if not isinstance(catalog, dict):
        raise ValueError("Cash source probe requires catalog identity")
    raw_sha = catalog.get("raw_sha256")
    if not isinstance(raw_sha, str) or len(raw_sha) != 64:
        raise ValueError("Cash probe requires a 64-char archive SHA-256")
    try:
        int(raw_sha, 16)
    except ValueError as error:
        raise ValueError("Cash probe archive SHA-256 must be hex") from error

    members = catalog.get("archive_members")
    if not isinstance(members, list) or not members:
        raise ValueError("Cash source probe requires archive member identities")
    prefix = f"{expected_future_id}-L2orderbook-"
    matches = [
        member for member in members
        if isinstance(member, str)
        and member.rsplit("/", 1)[-1].startswith(prefix)
        and member.endswith(f"-{market_date}.data")
    ]
    future_ids = (
        [report.get("future", {}).get("instrument_id")]
        if status == "future_discovered"
        else [
            item.get("instrument_id")
            for item in report.get("future_candidates", [])
            if isinstance(item, dict)
        ]
    )
    if future_ids.count(expected_future_id) != 1 or len(matches) != 1:
        return CashExpiryProbeResult(
            market_date,
            expected_future_id,
            "unavailable",
            "expected_expiry_future_not_uniquely_in_archive",
            raw_sha,
        )
    return CashExpiryProbeResult(
        market_date, expected_future_id,
        "identity_verified", "archive_member_only_not_exit_or_pnl_evidence", raw_sha
    )


def cash_expiry_probe_summary(
    observations: list[CashExpiryProbeResult],
) -> dict[str, Any]:
    seen: set[tuple[str, str]] = set()
    for result in observations:
        key = result.market_date, result.expected_future_id
        if key in seen:
            raise ValueError("duplicate Cash source-probe target")
        seen.add(key)
    expected = set(CASH_EXPIRY_PROBE_TARGETS)
    if seen != expected:
        raise ValueError("Cash source probe must cover every frozen target exactly")
    verified = sum(item.status == "identity_verified" for item in observations)
    return {
        "schema_version": 1,
        "evidence_type": "cash_quarterly_expiry_source_readiness",
        "probe_target_count": len(observations),
        "archive_identity_verified_count": verified,
        "missing_or_error_count": len(observations) - verified,
        "target_coverage_complete": verified == len(observations),
        "acquisition_ready": False,
        "additional_requirements": [
            "spot_entry_and_pre_expiry_exit_source_integrity",
            "contract_semantics_and_holding_period_validation",
            "frozen_provenance_compatible_acquisition_plan",
            "human_promotion_review",
        ],
        "note": (
            "A verified futures chain-member identity alone never proves "
            "trade/exit data completeness, profitability or sample readiness."
        ),
        "observations": [item.to_payload() for item in observations],
    }
