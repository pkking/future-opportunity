from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx


BASE_URL = "https://www.okx.com"
CATALOG_PATH = "/api/v5/public/market-data-history"
INSTRUMENTS_PATH = "/api/v5/public/instruments"
DATE_MS = 1790812800000  # 2026-10-01T00:00:00Z
MAX_DOWNLOAD_MB = float(os.getenv("MAX_ARCHIVE_MB", "64"))
OUTPUT = Path(
    os.getenv(
        "HISTORICAL_PROBE_DIR",
        "artifacts/historical-probe",
    )
)
CANDIDATES = ("OKB-USDT", "USDC-USDT", "BTC-USDT", "ETH-USDT")


def get_json(
    client: httpx.Client,
    path: str,
    params: dict[str, str],
) -> dict[str, Any]:
    response = client.get(f"{BASE_URL}{path}", params=params)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "0":
        raise RuntimeError(
            f"OKX error {payload.get('code')}: {payload.get('msg')}"
        )
    return payload


def catalog(
    client: httpx.Client,
    *,
    instrument_type: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    selector = (
        "instIdList" if instrument_type == "SPOT" else "instFamilyList"
    )
    params = {
        "module": "4",
        "instType": instrument_type,
        selector: ",".join(CANDIDATES),
        "dateAggrType": "daily",
        "begin": str(DATE_MS),
        "end": str(DATE_MS),
    }
    return params, get_json(client, CATALOG_PATH, params)


def archive_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for group in payload.get("data", []):
        for detail in group.get("details", []):
            for file in detail.get("groupDetails", []):
                result.append(
                    {
                        "instId": detail.get("instId", ""),
                        "instFamily": detail.get("instFamily", ""),
                        "instType": detail.get("instType", ""),
                        "dateRangeStart": detail.get("dateRangeStart", ""),
                        "dateRangeEnd": detail.get("dateRangeEnd", ""),
                        **file,
                    }
                )
    return sorted(
        result,
        key=lambda item: float(item.get("sizeMB") or "inf"),
    )


def select_small_archive(
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in candidates
            if item.get("url")
            and float(item.get("sizeMB") or "inf") <= MAX_DOWNLOAD_MB
        ),
        None,
    )


def download(
    client: httpx.Client,
    item: dict[str, Any],
    destination: Path,
) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    hard_limit = int((MAX_DOWNLOAD_MB + 4) * 1024 * 1024)

    with client.stream("GET", str(item["url"])) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > hard_limit:
                    raise RuntimeError(
                        "archive exceeded the configured probe size limit"
                    )
                digest.update(chunk)
                output.write(chunk)

    return digest.hexdigest(), total


def inspect_zip(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if not members:
            raise RuntimeError("archive contains no files")

        first = members[0]
        with archive.open(first) as source:
            sample = source.read(128 * 1024)

    text = sample.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()[:30]
    return {
        "members": [
            {
                "filename": item.filename,
                "compressed_size": item.compress_size,
                "uncompressed_size": item.file_size,
            }
            for item in members[:20]
        ],
        "sample_member": first.filename,
        "first_lines": lines,
    }


def instrument_metadata(
    client: httpx.Client,
    item: dict[str, Any],
) -> list[dict[str, Any]]:
    instrument_type = str(item["instType"])
    params = {"instType": instrument_type}

    if instrument_type == "SPOT":
        instrument_id = str(item["instId"])
        params["instId"] = instrument_id
    else:
        params["instFamily"] = str(item["instFamily"])

    payload = get_json(client, INSTRUMENTS_PATH, params)
    keys = (
        "instId",
        "instFamily",
        "instType",
        "ctVal",
        "ctMult",
        "ctValCcy",
        "settleCcy",
        "listTime",
        "expTime",
        "state",
    )
    return [
        {key: row.get(key, "") for key in keys}
        for row in payload.get("data", [])
    ]


def probe(instrument_type: str) -> dict[str, Any]:
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        params, payload = catalog(
            client,
            instrument_type=instrument_type,
        )
        candidates = archive_candidates(payload)
        selected = select_small_archive(candidates)

        result: dict[str, Any] = {
            "source": f"{BASE_URL}{CATALOG_PATH}",
            "query": params,
            "max_download_mb": MAX_DOWNLOAD_MB,
            "catalog_candidates": candidates,
            "status": "catalog_only",
        }

        if selected is None:
            result["reason"] = "no_archive_within_probe_size_limit"
            return result

        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / str(selected["filename"])
            sha256, size = download(client, selected, archive_path)
            result.update(
                {
                    "status": "schema_sampled",
                    "selected": selected,
                    "raw_sha256": sha256,
                    "downloaded_bytes": size,
                    "zip": inspect_zip(archive_path),
                    "instrument_metadata": instrument_metadata(
                        client,
                        selected,
                    ),
                }
            )
        return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "probe_date": "2026-10-01",
        "module": "4",
        "source_timezone": "UTC",
        "results": {},
    }
    failures: list[str] = []

    for instrument_type in ("SPOT", "SWAP"):
        try:
            result = probe(instrument_type)
        except Exception as error:
            result = {
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
            }
            failures.append(instrument_type)

        summary["results"][instrument_type] = result
        (OUTPUT / f"{instrument_type.lower()}-probe.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )

    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    if failures:
        raise SystemExit(
            "historical schema probe failed for: " + ", ".join(failures)
        )


if __name__ == "__main__":
    main()
