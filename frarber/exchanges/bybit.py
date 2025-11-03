from ccxt.pro import bybit


class Bybit(bybit):
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
