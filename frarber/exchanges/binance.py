from ccxt.pro import binance, binancecoinm, binanceusdm


class Binance(binance):
    def describe(self):
        return self.deep_extend(
            super().describe(),
            {
                "options": {
                    "brokerId": None,
                    "broker": None,
                },
            },
        )


class BinanceCoinM(binancecoinm):
    def describe(self):
        return self.deep_extend(
            super().describe(),
            {
                "options": {
                    "brokerId": None,
                    "broker": None,
                },
            },
        )


class BinanceUSDM(binanceusdm):
    def describe(self):
        return self.deep_extend(
            super().describe(),
            {
                "options": {
                    "brokerId": None,
                    "broker": None,
                },
            },
        )
