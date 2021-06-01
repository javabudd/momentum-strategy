from typing import Optional

from pyEX.client import Client


class APOValidator:
    """
    The Absolute Price Oscillator displays the difference between two exponential moving averages of a security's price
    and is expressed as an absolute value.

    APO crossing above zero is considered bullish , while crossing below zero is bearish . A positive indicator value
    indicates an upward movement, while negative readings signal a downward trend. Divergences form when a new high or
    low in price is not confirmed by the Absolute Price Oscillator (APO).

    Buy signals:

    A bullish divergence forms when the price makes a lower low, but the APO forms a higher low. This indicates less
    downward momentum that could foreshadow a bullish reversal.

    Sell signals:

    A bearish divergence forms when the price makes a higher high, but the APO forms a lower high. This shows less
    upward momentum that could foreshadow a bearish reversal.
    """

    def __init__(self, ticker: str, iex_client: Client, is_bullish: Optional[bool] = True):
        self.iex_client = iex_client
        self.ticker = ticker
        self.is_bullish = is_bullish

    @staticmethod
    def get_name():
        return 'Absolute Price Oscillator'

    def validate(self):
        time_range = '5d'
        historical_data = self.iex_client.stocks.chart(self.ticker, timeframe=time_range)
        quote_data = self.iex_client.stocks.quote(self.ticker)

        if self.is_bullish:
            return self.signals_bullish(historical_data, quote_data, time_range)
        else:
            return self.signals_bearish()

    def signals_bullish(self, historical_data, quote_data, time_range):
        if not historical_data:
            return False

        lowest_low_historical = min(historical_data, key=lambda x: x["low"])

        if lowest_low_historical['low'] is None or quote_data['low'] is None:
            return False

        if quote_data['low'] < lowest_low_historical['low']:
            data = self.iex_client.stocks.technicals(self.ticker, 'apo', range=time_range)
            for required in ['indicator', 'chart']:
                if required not in data:
                    return False

            indicator_data = data['indicator']

            try:
                short_period = indicator_data[0][0]
            except IndexError:
                short_period = None

            try:
                long_period = indicator_data[0][1]
            except IndexError:
                return False

            if short_period is not None and short_period > 0 and long_period <= 0:
                apo_chart = data['chart']

                if not apo_chart:
                    return False

                highest_apo_low = max(apo_chart[:-1], key=lambda x: x["low"])
                latest_apo_low = apo_chart[-1]

                if latest_apo_low['low'] > highest_apo_low['low']:
                    return True

        return False

    # nothing yet
    def signals_bearish(self):
        return False
