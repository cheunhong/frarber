import asyncio
import json
import time
from typing import Any, cast
from urllib import error, request

from ccxt.base.exchange import Exchange
from loguru import logger
from pydantic import BaseModel, Field

from frarber.enums.exchange_type import ExchangeType
from frarber.enums.threshold_direction import ThresholdDirection


class EquityAlertPayload(BaseModel):
    """Payload structure used when sending webhook alerts."""

    exchange: str = Field(..., description="Exchange identifier issuing the alert")
    currency: str = Field(..., description="Currency the equity is measured in")
    equity: float = Field(..., description="Current account equity")
    threshold: float = Field(..., description="Configured threshold")
    direction: ThresholdDirection = Field(
        ..., description="Alert triggers when equity crosses this direction"
    )
    crossed_at: float = Field(..., description="Unix timestamp when crossing detected")


async def monitor_equity_threshold(
    exchange: Exchange,
    exchange_type: ExchangeType,
    threshold: float,
    direction: ThresholdDirection,
    webhook_url: str,
    currency: str,
    check_interval: float,
    trigger_once: bool,
    balance_type: str | None = None,
) -> None:
    """Monitor futures account equity and fire a webhook when it crosses the threshold."""

    params: dict[str, Any] = {}
    if balance_type:
        params["type"] = balance_type

    previous_condition: bool | None = None

    while True:
        try:
            balance = await exchange.fetch_balance(params)
            equity = _extract_equity(balance=balance, currency=currency)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error(f"Failed to fetch balance from {exchange_type.value}: {exc}")
            await asyncio.sleep(check_interval)
            continue

        condition_met = _is_threshold_crossed(
            equity=equity, threshold=threshold, direction=direction
        )

        logger.debug(
            f"Equity check | exchange={exchange_type.value} currency={currency} "
            f"equity={equity:.6f} threshold={threshold:.6f} direction={direction.value}"
        )

        if condition_met and previous_condition is not True:
            await _send_webhook_alert(
                webhook_url=webhook_url,
                payload=EquityAlertPayload(
                    exchange=exchange_type.value,
                    currency=currency,
                    equity=equity,
                    threshold=threshold,
                    direction=direction,
                    crossed_at=time.time(),
                ),
            )
            logger.info(
                f"Equity threshold crossed | exchange={exchange_type.value} "
                f"currency={currency} equity={equity:.6f} threshold={threshold:.6f} "
                f"direction={direction.value}"
            )
            if trigger_once:
                break

        previous_condition = condition_met
        await asyncio.sleep(check_interval)


async def _send_webhook_alert(webhook_url: str, payload: EquityAlertPayload) -> None:
    """Send the webhook alert using a background thread to avoid blocking the loop."""

    body = json.dumps(payload.model_dump()).encode("utf-8")

    def _post() -> None:
        req = request.Request(
            webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10.0) as response:
            response.read()

    try:
        await asyncio.to_thread(_post)
    except error.HTTPError as http_err:  # pragma: no cover - network dependent
        logger.error(
            "Webhook responded with HTTP %s when posting equity alert to %s",
            http_err.code,
            webhook_url,
        )
    except error.URLError as url_err:  # pragma: no cover - network dependent
        logger.error(
            "Failed to reach webhook endpoint %s: %s", webhook_url, url_err.reason
        )


def _extract_equity(balance: dict[str, Any], currency: str) -> float:
    """Extract the futures equity for the requested currency from the balance payload."""

    normalized_currency = currency.upper()

    totals_raw = balance.get("total")
    totals = cast(dict[str, Any], totals_raw) if isinstance(totals_raw, dict) else {}
    equity_value = totals.get(normalized_currency)
    parsed_equity = _try_parse_float(equity_value)
    if parsed_equity is not None:
        return parsed_equity

    info_raw = balance.get("info")
    info = cast(dict[str, Any], info_raw) if isinstance(info_raw, dict) else {}
    candidate_keys = (
        "equity",
        "totalEquity",
        "walletBalance",
        "accountEquity",
        "marginBalance",
        "totalWalletBalance",
    )

    for key in candidate_keys:
        raw_value = info.get(key)
        if isinstance(raw_value, dict):
            nested = cast(dict[str, Any], raw_value)
            parsed_equity = _try_parse_float(nested.get(normalized_currency))
        else:
            parsed_equity = _try_parse_float(raw_value)
        if parsed_equity is not None:
            return parsed_equity

    raise ValueError(
        f"Unable to extract equity for {normalized_currency} from balance payload"
    )


def _try_parse_float(value: Any) -> float | None:
    """Attempt to coerce the provided value into a float."""

    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value:
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _is_threshold_crossed(
    equity: float, threshold: float, direction: ThresholdDirection
) -> bool:
    """Return True when the equity crosses the configured threshold in the direction."""

    if direction == ThresholdDirection.ABOVE:
        return equity >= threshold
    return equity <= threshold
