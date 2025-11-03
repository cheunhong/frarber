import hashlib
import json
import time

from ccxt.base.decimal_to_precision import TRUNCATE
from ccxt.base.errors import BadRequest, InvalidOrder
from ccxt.base.types import Entry
from ccxt.pro import mexc


class Mexc(mexc):
    contract_private_post_order_submit = contractPrivatePostOrderSubmit = Entry(
        "order/create", ["futures", "private"], "POST", {"cost": 2}
    )
    contract_private_post_order_cancel = contractPrivatePostOrderCancel = Entry(
        "order/cancel", ["futures", "private"], "POST", {"cost": 2}
    )
    userToken: str | None = None

    def describe(self):
        return self.deep_extend(
            super().describe(),
            {
                "urls": {
                    "api": {
                        "futures": {
                            "public": "https://futures.mexc.com/api/v1",
                            "private": "https://futures.mexc.com/api/v1/private",
                        },
                    }
                },
                "options": {
                    "brokerId": None,
                    "broker": None,
                    "unavailableContracts": {
                        "BTC/USDT:USDT": False,
                        "LTC/USDT:USDT": False,
                        "ETH/USDT:USDT": False,
                    },
                },
            },
        )

    def sign(
        self, path, api="public", method="GET", params={}, headers=None, body=None
    ):
        section = self.safe_string(api, 0)
        access = self.safe_string(api, 1)
        path, params = self.resolve_path(path, params)

        if section in ("futures", "spot4"):
            url = (
                self.urls["api"][section][access]
                + "/"
                + self.implode_params(path, params)
            )
            if self.userToken is None:
                raise Exception("Missing user token")
            params = self.omit(params, self.extract_params(path))
            timestamp = str(int(time.time() * 1000))
            concat = f"{self.userToken}{timestamp}"
            partial_hash = hashlib.md5(concat.encode("utf-8")).hexdigest()[7:]
            body = self.json(params)
            sign_param = f"{timestamp}{body}{partial_hash}"
            signature = hashlib.md5(sign_param.encode("utf-8")).hexdigest()
            headers = {
                "x-mxc-nonce": timestamp,
                "x-mxc-sign": signature,
                "authorization": self.userToken,
                "user-agent": "MEXC/7 CFNetwork/1474 Darwin/23.0.0",
                "content-type": "application/json",
                "origin": "https://futures.mexc.com",
                "referer": "https://futures.mexc.com/exchange",
            }
            if section == "spot4":
                headers["origin"] = "https://www.mexc.com"
                headers["referer"] = "https://www.mexc.com/exchange"
            return {"url": url, "method": method, "body": body, "headers": headers}
        return super().sign(path, api, method, params, headers, body)

    def prepare_request_headers(self, headers=None):
        headers = super().prepare_request_headers(headers)
        # Private endpoints dont require the following headers
        if "x-mxc-sign" in headers:
            del headers["User-Agent"]
            del headers["Accept-Encoding"]
        return headers

    def parse_trade(self, trade, market=None):
        trade = super().parse_trade(trade, market)
        if market is not None:
            if market.get("contractSize") is not None:
                trade["amount"] = trade["amount"] * market["contractSize"]
        return trade

    def swap_amount_to_precision(self, symbol, amount):
        market = self.market(symbol)
        result = self.decimal_to_precision(
            amount,
            TRUNCATE,
            market["contractSize"],
            self.precisionMode,
            self.paddingMode,
        )
        if result == "0":
            raise InvalidOrder(
                self.id
                + " amount of "
                + market["symbol"]
                + " must be greater than minimum amount precision of "
                + self.number_to_string(market["contractSize"])
            )
        return result

    async def create_swap_order(
        self, market, type, side, amount, price=None, marginMode=None, params={}
    ):
        await self.load_markets()
        amount = (
            float(
                self.decimal_to_precision(
                    amount,
                    TRUNCATE,
                    market["contractSize"],
                    self.precisionMode,
                    self.paddingMode,
                )
            )
            / market["contractSize"]
        )
        if amount < 1:
            raise InvalidOrder(
                self.id
                + " amount of "
                + market["symbol"]
                + " must be greater than minimum amount precision of "
                + self.number_to_string(market["contractSize"])
            )

        response = await super().create_swap_order(
            market, type, side, amount, price, marginMode, params
        )
        info = json.loads(response["id"].replace("'", '"'))
        response["id"] = self.safe_string(info, "orderId")
        response["timestamp"] = ts = self.safe_integer(info, "ts")
        response["datetime"] = self.iso8601(ts)
        return response
