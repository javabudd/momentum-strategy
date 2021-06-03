import _thread
import json
import math
import time
from typing import Optional

import pandas as pd
from cement.core.log import LogInterface
from pyEX import PyEXception

import jtrader.core.utils as utils
from jtrader import __STOCK_CSVS__
from jtrader.core.iex import IEX
from jtrader.core.validator import __VALIDATION_MAP__


class Scanner(IEX):
    def __init__(self, is_sandbox: bool, logger: LogInterface, stocks: Optional[str], indicators: Optional[list]):
        super().__init__(is_sandbox, logger)

        if stocks is None:
            self.stock_list = __STOCK_CSVS__['all']
        else:
            if stocks not in __STOCK_CSVS__:
                raise RuntimeError

            self.stock_list = __STOCK_CSVS__[stocks]

        self.indicators = []
        if indicators is None:
            self.indicators = __VALIDATION_MAP__['all']
        else:
            for indicator in indicators:
                if indicator[0] in __VALIDATION_MAP__:
                    self.indicators.append(__VALIDATION_MAP__[indicator[0]])
            if len(self.indicators) == 0:
                raise RuntimeError

    def run(self):
        num_lines = len(open(self.stock_list).readlines())
        chunk_size = math.floor(num_lines / 10)
        if self.is_sandbox:
            chunk_size = math.floor(num_lines / 4)

        stocks = pd.read_csv(self.stock_list, chunksize=chunk_size)

        while True:
            i = 1
            for chunk in enumerate(stocks):
                _thread.start_new_thread(self.loop, (f"Thread-{i}", chunk))
                i += 1

            self.logger.info('Processing finished, sleeping for an hour...')
            time.sleep(3600)

    def loop(self, thread_name, chunk):
        sleep = .2

        if self.is_sandbox:
            sleep = 2

        for ticker in chunk[1]['Ticker']:
            self.logger.info(f"({thread_name}) Processing ticker: {ticker}")
            for indicator_class in self.indicators:
                indicator = indicator_class(ticker, self.iex_client)
                passed_validators = {}
                try:
                    is_valid = indicator.validate()

                    if is_valid is False:
                        continue

                    chain = indicator.get_validation_chain()
                    has_valid_chain = True
                    if len(chain) > 0:
                        passed_validators[indicator.get_name()] = []
                        chain_index = 0
                        for validator_chain in chain:
                            validator_chain = validator_chain(ticker, self.iex_client)
                            if validator_chain.validate() is False:
                                has_valid_chain = False
                                break  # break out of validation chain

                            passed_validators[indicator.get_name()] \
                                .append(validator_chain.get_name() + f"({validator_chain.get_time_range()})")
                            chain_index += 1
                        if has_valid_chain is False:
                            continue  # continue to the next validator in list
                    else:
                        passed_validators = [indicator.get_name()]

                except PyEXception as e:
                    self.logger.error(e.args[0] + ' ' + e.args[1])

                    break

                if len(passed_validators) > 0:
                    message = {
                        "ticker": ticker,
                        "signal_type": "bullish",
                        "indicators_triggered": passed_validators
                    }

                    message_string = json.dumps(message)

                    self.logger.info(message_string)
                    utils.send_slack_message('```' + message_string + '```')

            time.sleep(sleep)
