import numpy as np

from jtrader.core.validator.validator import Validator


class MACDValidator(Validator):
    """
    Moving average convergence divergence (MACD) is a trend-following momentum indicator that shows the relationship
    between two moving averages of a security’s price. The MACD is calculated by subtracting the 26-period exponential
    moving average (EMA) from the 12-period EMA. The result of that calculation is the MACD line. A nine-day EMA of
    the MACD called the "signal line," is then plotted on top of the MACD line, which can function as a trigger for
    buy and sell signals. Traders may buy the security when the MACD crosses above its signal line and sell—or
    short—the security when the MACD crosses below the signal line. Moving average convergence divergence (MACD)
    indicators can be interpreted in several ways, but the more common methods are crossovers, divergences, and rapid
    rises/falls.

    Buy signals:
    A bullish divergence appears when the MACD forms two rising lows that correspond with two falling lows on the price.
    This is a valid bullish signal when the long-term trend is still positive.

    Sell signals:
    When the MACD forms a series of two falling highs that correspond with two rising highs on the price, a bearish
    divergence has been formed. A bearish divergence that appears during a long-term bearish trend is considered
    confirmation that the trend is likely to continue.
    """

    @staticmethod
    def get_name():
        return 'MACD'

    def validate(self):
        if self.is_bullish:
            data = self.iex_client.stocks.technicals(self.ticker, 'macd', range=self.time_range)

            if 'chart' not in data:
                return False

            chart = data['chart']

            if not chart or len(chart) == 1:
                return False

            average_close = np.mean(list(map(lambda x: x['close'] is not None, chart)))

            return average_close <= 30

        return False

    def get_validation_chain(self):
        return []
