from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest

from app.core.config import Settings
from app.core.report_state import ReportState
from app.integrations.mercadopago_api_client import (
    MercadoPagoApiClient,
    MercadoPagoApiClientError,
)
from app.schemas.transaction import BalanceStatus


def test_fetch_balance_generates_downloads_and_persists_release_report(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(202, json={"message": "processing"})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 123,
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                    }
                ],
            )
        return httpx.Response(
            200,
            text=(
                "DATE;amount;BALANCE_AMOUNT\n"
                "2026-06-01;10;1000.50\n"
                "2026-06-02;20;1020.75\n"
                ";;0.00\n"
            ),
        )

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        report_state=ReportState(tmp_path / "reports.json"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert balance.source == "mercadopago"
    assert str(balance.amount) == "1020.75"
    assert [request.method for request in requests] == ["GET", "GET"]
    assert requests[0].headers["Authorization"] == "Bearer test-token"
    assert ReportState(tmp_path / "reports.json").is_downloaded("123")


def test_fetch_balance_downloads_enabled_release_report_from_list(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(202, json={"message": "processing"})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 61743707,
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name": "reserve-release-67076163-manual-2026-06-09-004618.csv",
                        "status": "enabled",
                        "currency_id": "ARS",
                    }
                ],
            )
        return httpx.Response(
            200,
            text="DATE;BALANCE_AMOUNT\n2026-06-02;1500.25\n",
        )

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        report_state=ReportState(tmp_path / "reports.json"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert balance.currency == "ARS"
    assert str(balance.amount) == "1500.25"
    assert ReportState(tmp_path / "reports.json").is_downloaded("61743707")


def test_fetch_balance_backfills_latest_report_when_state_has_no_balance(
    tmp_path: Path,
) -> None:
    state = ReportState(tmp_path / "reports.json")
    state.mark_downloaded("61743707")
    downloaded_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(202, json={"id": "generation-request-999"})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 61743707,
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name": "already-downloaded.csv",
                        "status": "enabled",
                        "currency_id": "ARS",
                    },
                    {
                        "id": 61743683,
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name": "new-report.csv",
                        "status": "enabled",
                        "currency_id": "ARS",
                    },
                ],
            )
        downloaded_urls.append(str(request.url))
        return httpx.Response(200, text="DATE;BALANCE_AMOUNT\n2026-06-02;1500.25\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        report_state=state,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert str(balance.amount) == "1500.25"
    assert downloaded_urls == ["https://api.example.com/release_report/already-downloaded.csv"]
    assert state.is_downloaded("61743707")
    assert not state.is_downloaded("61743683")


def test_fetch_balance_polls_until_release_report_is_processed(tmp_path: Path) -> None:
    list_calls = 0
    sleeps: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal list_calls
        if request.method == "POST":
            return httpx.Response(202, json={})
        if str(request.url).endswith("/list"):
            list_calls += 1
            status = "processing" if list_calls == 1 else "processed"
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 123,
                        "status": status,
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                    }
                ],
            )
        return httpx.Response(
            200,
            text="DATE;BALANCE_AMOUNT\n2026-06-02;1020.75\n",
        )

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path, MERCADOPAGO_REPORT_WAIT_SECONDS=30),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=sleeps.append,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert str(balance.amount) == "1020.75"
    assert list_calls == 2
    assert sleeps == [30]


def test_fetch_balance_persists_report_id_from_list_not_generation_request(
    tmp_path: Path,
) -> None:
    state = ReportState(tmp_path / "reports.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(202, json={"id": "generation-request-999"})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "report-123",
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                    }
                ],
            )
        return httpx.Response(200, text="DATE;BALANCE_AMOUNT\n2026-06-02;1020.75\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        report_state=state,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert state.is_downloaded("report-123")
    assert not state.is_downloaded("generation-request-999")


def test_fetch_balance_generates_new_report_when_latest_cached_report_was_downloaded(
    tmp_path: Path,
) -> None:
    state = ReportState(tmp_path / "reports.json")
    state.mark_downloaded("123", balance_amount=Decimal("1020.75"), balance_currency="ARS")
    list_calls = 0
    downloaded_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal list_calls
        if request.method == "POST":
            return httpx.Response(202, json={"id": "generation-request-999"})
        if str(request.url).endswith("/list"):
            list_calls += 1
            report_id = 123 if list_calls == 1 else 124
            file_name = "old-report.csv" if list_calls == 1 else "new-report.csv"
            return httpx.Response(
                200,
                json=[
                    {
                        "id": report_id,
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": file_name,
                        "currency_id": "ARS",
                    }
                ],
            )
        downloaded_urls.append(str(request.url))
        return httpx.Response(200, text="DATE;BALANCE_AMOUNT\n2026-06-02;2040.75\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        report_state=state,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert str(balance.amount) == "2040.75"
    assert balance.failure_reason is None
    assert downloaded_urls == ["https://api.example.com/release_report/new-report.csv"]
    assert state.is_downloaded("124")


def test_fetch_balance_reuses_cached_balance_when_new_report_is_not_ready(tmp_path: Path) -> None:
    state = ReportState(tmp_path / "reports.json")
    state.mark_downloaded("123", balance_amount=Decimal("1020.75"), balance_currency="ARS")
    downloads: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(202, json={"id": "generation-request-999"})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 123,
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                        "currency_id": "ARS",
                    }
                ],
            )
        downloads.append(str(request.url))
        return httpx.Response(200, text="DATE;BALANCE_AMOUNT\n2026-06-02;2040.75\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path, MERCADOPAGO_REPORT_MAX_ATTEMPTS=2),
        report_state=state,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert str(balance.amount) == "1020.75"
    assert downloads == []


def test_fetch_balance_backfills_cache_for_old_downloaded_report_state(tmp_path: Path) -> None:
    state = ReportState(tmp_path / "reports.json")
    state.mark_downloaded("123")

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 123,
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                        "currency_id": "ARS",
                    }
                ],
            )
        return httpx.Response(200, text="DATE;BALANCE_AMOUNT\n2026-06-02;1020.75\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        report_state=state,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert balance.status == BalanceStatus.SUCCESS
    assert str(balance.amount) == "1020.75"
    assert state.snapshot().last_balance_amount is not None
    assert str(state.snapshot().last_balance_amount) == "1020.75"


def test_fetch_balance_fails_when_report_is_not_ready_after_max_attempts(tmp_path: Path) -> None:
    list_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal list_calls
        if request.method == "POST":
            return httpx.Response(202, json={})
        list_calls += 1
        return httpx.Response(
            200,
            json=[
                {
                    "id": 123,
                    "status": "processing",
                    "begin_date": "2026-06-01T00:00:00Z",
                    "end_date": "2026-06-02T00:00:00Z",
                    "file_name_report": "release-report.csv",
                }
            ],
        )

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path, MERCADOPAGO_REPORT_MAX_ATTEMPTS=5),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    with pytest.raises(MercadoPagoApiClientError, match="aun no esta listo") as exc_info:
        client.fetch_balance()

    assert exc_info.value.reason == "report_not_ready"
    assert list_calls == 6


def test_fetch_balance_requires_balance_amount_column(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(202, json={})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 123,
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                    }
                ],
            )
        return httpx.Response(200, text="date,amount\n2026-06-01,10\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    with pytest.raises(MercadoPagoApiClientError, match="BALANCE_AMOUNT") as exc_info:
        client.fetch_balance()

    assert exc_info.value.reason == "balance_amount_not_found"


@pytest.mark.parametrize(
    ("raw_amount", "expected_amount"),
    [
        ("1.020,75", "1020.75"),
        ("1,020.75", "1020.75"),
        ("1.020.750", "1020750"),
        ("$ 1.020,75", "1020.75"),
    ],
)
def test_fetch_balance_accepts_localized_balance_amounts(
    tmp_path: Path,
    raw_amount: str,
    expected_amount: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(202, json={})
        if str(request.url).endswith("/list"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 123,
                        "status": "processed",
                        "begin_date": "2026-06-01T00:00:00Z",
                        "end_date": "2026-06-02T00:00:00Z",
                        "file_name_report": "release-report.csv",
                    }
                ],
            )
        return httpx.Response(200, text=f"DATE;BALANCE_AMOUNT\n2026-06-02;{raw_amount}\n")

    client = MercadoPagoApiClient(
        settings=_settings(tmp_path),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleeper=lambda _: None,
        clock=_fixed_clock,
    )

    balance = client.fetch_balance()

    assert str(balance.amount) == expected_amount


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "MERCADOPAGO_ENABLED": True,
        "MERCADOPAGO_ACCESS_TOKEN": "test-token",
        "MERCADOPAGO_RELEASE_REPORT_URL": "https://api.example.com/release_report",
        "MERCADOPAGO_RELEASE_REPORT_LIST_URL": "https://api.example.com/release_report/list",
        "MERCADOPAGO_RELEASE_REPORT_DOWNLOAD_URL": "https://api.example.com/release_report",
        "MERCADOPAGO_REPORT_WAIT_SECONDS": 0,
        "MERCADOPAGO_REPORT_STATE_FILE": tmp_path / "reports.json",
    }
    values.update(overrides)
    return Settings(
        **values,
    )


def _fixed_clock() -> datetime:
    return datetime(2026, 6, 2, tzinfo=timezone.utc)
