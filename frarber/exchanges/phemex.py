from ccxt.pro import phemex


class Phemex(phemex):
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
