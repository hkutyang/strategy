#!/usr/bin/env python3

# AUTHOR <Chenyang LI>
# EMAIL <chenyangli@ece.utoronto.ca> / <sjtulichenyang@126.com>

import datetime
import numpy


def time_start_from1900(time_string):
    time_obj = datetime.datetime.strptime(time_string, "%Y-%m-%d")
    reference_date = datetime.datetime(1900, 1, 1)
    time_delta = time_obj - reference_date
    time_int = time_delta.days

    return time_int


def read_file(path):
    """
    since the data is small, list is used for include info,
    pandas used applied when data set is large.

    """
    data = open(path)
    data.readline()  # skip first row
    tmp_ticker, tmp_date_log, tmp_last_price, tmp_volume = [], [], [], []
    for line in data:
        s_ticker, s_date, s_last, s_volume = line.split(",")

        tmp_ticker.append(s_ticker)
        tmp_date_log.append(time_start_from1900(s_date))
        tmp_last_price.append(float(s_last))
        tmp_volume.append(int(s_volume))

    return tmp_ticker, tmp_date_log, tmp_last_price, tmp_volume


def find_static(strategy, stock_alias, rf=0, date_frozen=10):
    """
    approx: the deviation is fixed along all stock period

    """
    indexing = numpy.where(strategy.ticker_array == stock_alias)
    by_date = strategy.date_array[indexing]
    sort_bydate = numpy.argsort(by_date)

    date_sort_by_date = by_date[sort_bydate]
    price_single_stock_bydate = strategy.price_array[indexing][sort_bydate]

    return_date_frozon, tmp_price = [], price_single_stock_bydate[0]
    for i in range(0, len(price_single_stock_bydate), date_frozen):
        return_date_frozon.append((price_single_stock_bydate[i] - tmp_price) / tmp_price)
        tmp_price = price_single_stock_bydate[i]

    return_date_frozon = numpy.array(return_date_frozon)

    average = numpy.average(return_date_frozon)
    deviation = numpy.std(return_date_frozon)
    rf = rf
    sharp_ratio = (average - rf) / deviation
    optimal_leverge = (average - rf) / (deviation * deviation)

    return optimal_leverge, date_sort_by_date, price_single_stock_bydate


def find_dynamic(strategy, stock_alias, rf=0, trading_period=10):
    """
    please be reminded, all list of date based optimal_leverge is calculated.
    further improvement can be done by calculate trade_date-based optimal_leverge.

    """
    indexing = numpy.where(strategy.ticker_array == stock_alias)
    by_date = strategy.date_array[indexing]
    sort_bydate = numpy.argsort(by_date)

    date_sort_by_date = by_date[sort_bydate]
    price_single_stock_bydate = strategy.price_array[indexing][sort_bydate]

    optimal_leverge = [0] * trading_period  # initial optimal_leverge since it will not be used for trading

    for i in range(trading_period, len(price_single_stock_bydate)):
        stepsize = min(int(i / trading_period), trading_period)
        price_to_use = price_single_stock_bydate[:i][::stepsize]

        return_date_frozon, tmp_price = [], price_to_use[0]

        for i in range(1, len(price_to_use)):
            return_date_frozon.append((price_to_use[i] - tmp_price) / tmp_price)
            tmp_price = price_to_use[i]

        return_date_frozon = numpy.array(return_date_frozon)

        average = numpy.average(return_date_frozon)
        deviation = numpy.std(return_date_frozon)
        rf = rf
        # sharp_ratio = (average - rf) / deviation
        optimal_leverge.append((average - rf) / (deviation * deviation))

    assert len(optimal_leverge) == len(date_sort_by_date)
    optimal_leverge = numpy.array(optimal_leverge)
    return optimal_leverge, date_sort_by_date, price_single_stock_bydate


def put_in_pocket(strategy, date):
    """what to buy"""
    stock_list, optimal_lev_single, price_single = [], [], []
    for i in range(len(strategy.tick_dict)):

        if (date not in strategy.date_sort_by_date_list[i] or
                date + strategy.trading_period not in strategy.date_sort_by_date_list[i]):
            pass

        else:
            if strategy.mode == "dynamic":
                tmp_optimal_leverge_list = (
                    strategy.optimal_leverge_list)[i][numpy.where(strategy.date_sort_by_date_list[i] == date)]
            else:
                tmp_optimal_leverge_list = strategy.optimal_leverge_list[i]

            if tmp_optimal_leverge_list <= 2:  # f_i threshold
                pass

            else:
                stock_list.append(i)
                optimal_lev_single.append(tmp_optimal_leverge_list)
                price_single.append(strategy.price_single_stock_bydate_list[i]
                                    [numpy.where(strategy.date_sort_by_date_list[i] == date)])
    return stock_list, optimal_lev_single, price_single


def obtain_price(strategy, date):
    """calculate price"""

    price_dict = dict()

    for i in range(len(strategy.tick_dict)):

        if date in strategy.date_sort_by_date_list[i]:
            price_dict[i] = strategy.price_single_stock_bydate_list[i][
                numpy.where(strategy.date_sort_by_date_list[i] == date)]
    return price_dict


class Strategy:

    def __init__(self, path, mode="static", trading_period=10, cash_tot=1000000):

        self.mode = mode

        self.trading_period = trading_period
        self.cash_tot = cash_tot

        ticker, date_log, last_price, volume = read_file(path)
        date_since_day1 = numpy.array(date_log) - min(date_log) + 1
        tmp_list = list(set(date_since_day1))
        tmp_list.sort()

        date_dict = dict()
        for i, j in zip(tmp_list, range(len(tmp_list))):
            date_dict[i] = j

        continue_date_since_day1 = [date_dict[i] for i in date_since_day1]

        self.tick_dict, self.tick_dict_back = dict(), dict()
        for i, j in zip(set(ticker), range(len(set(ticker)))):
            self.tick_dict[i] = j
            self.tick_dict_back[j] = i

        ticker_with_alias = [self.tick_dict[i] for i in ticker]

        assert (len(ticker_with_alias) == len(continue_date_since_day1) == len(last_price) == len(volume))

        self.ticker_array = numpy.array(ticker_with_alias, dtype=int)
        self.date_array = numpy.array(continue_date_since_day1, dtype=int)
        self.volume_array = numpy.array(volume, dtype=int)
        self.price_array = numpy.array(last_price)

    def find_optimal_leverge_list(self):
        optimal_leverge_list, date_sort_by_date_list, price_single_stock_bydate_list = [], [], []

        for i in range(len(self.tick_dict)):
            if self.mode == "static":
                tmp_list = find_static(self, i, rf=0, date_frozen=self.trading_period)
            elif self.mode == "dynamic":
                tmp_list = find_dynamic(self, i, rf=0, trading_period=self.trading_period)

            optimal_leverge_list.append(tmp_list[0])
            date_sort_by_date_list.append(tmp_list[1])
            price_single_stock_bydate_list.append(tmp_list[2])

        return optimal_leverge_list, date_sort_by_date_list, price_single_stock_bydate_list

    def run(self):

        (self.optimal_leverge_list, self.date_sort_by_date_list,
         self.price_single_stock_bydate_list) = self.find_optimal_leverge_list()

        if self.mode == "static":
            start_time = 0
        else:
            start_time = self.trading_period

        for trading_day in range(0, max(self.date_array), self.trading_period):

            if trading_day <= start_time:
                in_pocket = dict()
                buy_info = put_in_pocket(self, trading_day)
                tot_opti_lev = sum(buy_info[1])
                for tmp_index in range(len(buy_info[0])):
                    in_pocket[buy_info[0][tmp_index]] = (self.cash_tot * buy_info[1][tmp_index] /
                                                         tot_opti_lev) / buy_info[2][tmp_index]

            else:
                # print(f'''cash_total at day {trading_day} is {self.cash_tot:.2f}''')
                price_dict = obtain_price(self, trading_day)
                kk = sum([in_pocket[j] * price_dict[j] for j in in_pocket])[0]
                # print(kk)
                self.cash_tot = kk
                if trading_day >= max(self.date_array) - self.trading_period:
                    pass

                else:
                    in_pocket = dict()
                    buy_info = put_in_pocket(self, trading_day)
                    tot_opti_lev = sum(buy_info[1])

                    for tmp_index in range(len(buy_info[0])):
                        in_pocket[buy_info[0][tmp_index]] = (self.cash_tot * buy_info[1][tmp_index] /
                                                             tot_opti_lev) / buy_info[2][tmp_index]

        print(f'''The final cash amount from {self.mode} mode is {self.cash_tot:.2f}''')


if __name__ == "__main__":
    cash_tot, trading_period = 1000000, 5
    # STATIC MODE
    K = Strategy(path='data.csv', mode="static", cash_tot=cash_tot, trading_period=trading_period)
    K.run()

    # DYNAMIC MODE
    K = Strategy(path='data.csv', mode="dynamic", cash_tot=cash_tot,
                 trading_period=trading_period)
    K.run()