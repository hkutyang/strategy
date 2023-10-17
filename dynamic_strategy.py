#!/usr/bin/env python3

# AUTHOR <Chenyang LI>
# EMAIL <chenyangli@ece.utoronto.ca> / <sjtulichenyang@126.com>

import datetime
import numpy


## READING FILES AND TO LIST

def time_start_from1900(time_string):
    """
    """

    time_obj = datetime.datetime.strptime(time_string, "%Y-%m-%d")
    reference_date = datetime.datetime(1900, 1, 1)
    time_delta = time_obj - reference_date
    time_int = time_delta.days

    return time_int


def read_file(path):
    """
    since the data is small, list is used for include info, pandas used applied when data set is large.

    """
    data = open(path)
    data.readline()  # skip first row

    ticker, date_log, last_price, volume = [], [], [], []
    for line in data:
        s_ticker, s_date, s_last, s_volume = line.split(",")

        ticker.append(s_ticker)
        date_log.append(time_start_from1900(s_date))
        last_price.append(float(s_last))
        volume.append(int(s_volume))

    return ticker, date_log, last_price, volume


ticker, date_log, last_price, volume = read_file('data.csv')

date_since_day1 = numpy.array(date_log) - min(date_log) + 1

tmp_list = list(set(date_since_day1))
tmp_list.sort()

date_dict = dict()
for i, j in zip(tmp_list, range(len(tmp_list))):
    date_dict[i] = j

continue_date_since_day1 = [date_dict[i] for i in date_since_day1]

tick_dict, tick_dict_back = dict(), dict()
for i, j in zip(set(ticker), range(len(set(ticker)))):
    tick_dict[i] = j
    tick_dict_back[j] = i

ticker_with_alias = [tick_dict[i] for i in ticker]

assert (len(ticker_with_alias) == len(continue_date_since_day1) == len(last_price) == len(volume))

ticker_array = numpy.array(ticker_with_alias, dtype=int)
date_array = numpy.array(continue_date_since_day1, dtype=int)
volume_array = numpy.array(volume, dtype=int)
price_array = numpy.array(last_price)


## END READING FILES

## START STRATAGY


## FIND STOCK-BASED INFO


def find_dynamic(stock_alias, rf=0, collect_point=10):
    """
    approx: 1. the deviation is fixed along all stock period

    """
    indexing = numpy.where(ticker_array == stock_alias)
    by_date = date_array[indexing]
    sort_bydate = numpy.argsort(by_date)

    date_sort_by_date = by_date[sort_bydate]
    price_single_stock_bydate = price_array[indexing][sort_bydate]

    optimal_leverge = [0] * collect_point  # initial optimal_leverge since it will not be used for trading

    for i in range(collect_point, len(price_single_stock_bydate)):
        stepsize = min(int(i / collect_point), 10)
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


optimal_leverge_list, date_sort_by_date_list, price_single_stock_bydate_list = [], [], []

for i in range(len(tick_dict)):
    tmp_list = find_dynamic(i, rf=0, collect_point=10)
    optimal_leverge_list.append(tmp_list[0])
    date_sort_by_date_list.append(tmp_list[1])
    price_single_stock_bydate_list.append(tmp_list[2])

## END OF FINDING STOCK BASED INFO


## STARTING TRADE

trading_period = 10
starting_time = 10

cash_tot = 1000000


def put_in_pocket(date):
    """what to buy"""
    stock_list, optimal_lev_single, price_single = [], [], []
    for i in range(len(tick_dict)):

        if date not in date_sort_by_date_list[i] or date + trading_period not in date_sort_by_date_list[i]:
            pass

        else:
            if optimal_leverge_list[i][numpy.where(date_sort_by_date_list[i] == date)] <= 0:
                pass
            else:
                stock_list.append(i)
                optimal_lev_single.append(optimal_leverge_list[i][numpy.where(date_sort_by_date_list[i] == date)])
                price_single.append(price_single_stock_bydate_list[i][numpy.where(date_sort_by_date_list[i] == date)])
    return stock_list, optimal_lev_single, price_single


def obtain_price(date):
    """calculate price"""

    price_dict = dict()

    for i in range(len(tick_dict)):

        if date in date_sort_by_date_list[i]:
            price_dict[i] = price_single_stock_bydate_list[i][numpy.where(date_sort_by_date_list[i] == date)]
    return price_dict


for trading_day in range(0, max(date_array), trading_period):

    if trading_day <= starting_time:
        in_pocket = dict()
        buy_info = put_in_pocket(trading_day)
        tot_opti_lev = sum(buy_info[1])
        for tmp_index in range(len(buy_info[0])):
            in_pocket[buy_info[0][tmp_index]] = (cash_tot * buy_info[1][tmp_index] / tot_opti_lev) / buy_info[2][
                tmp_index]

    else:
        print(f'''cash_totol at day {trading_day} is {cash_tot:.2f}''')
        price_dict = obtain_price(trading_day)

        cash_tot = sum([in_pocket[j] * price_dict[j] for j in in_pocket])[0]

        if trading_day >= max(date_array) - trading_period:
            pass

        else:
            in_pocket = dict()
            buy_info = put_in_pocket(trading_day)
            tot_opti_lev = sum(buy_info[1])

            for tmp_index in range(len(buy_info[0])):
                in_pocket[buy_info[0][tmp_index]] = (cash_tot * buy_info[1][tmp_index] / tot_opti_lev) / buy_info[2][
                    tmp_index]

print(f'''the final cash amount is {cash_tot:.2f}''')