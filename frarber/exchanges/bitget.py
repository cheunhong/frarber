from ccxt.pro import bitget


class Bitget(bitget):
    def describe(self):
        return self.deep_extend(
            super().describe(),
            {
                "options": {
                    "brokerId": None,
                    "broker": "a",
                },
            },
        )
