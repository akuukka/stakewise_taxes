#!/usr/bin/env python3
"""
polkadot_reward_income.py.

Compute taxable income from Polkadot staking rewards income (Ledger Live .csv).
"""

import sys
import re
import sqlite3
import time
import datetime
from pycoingecko import CoinGeckoAPI  # pip3 install pycoingecko
from requests.exceptions import HTTPError

CURRENCY = "eur"


def get_price(cg, db_con, day, month, year):
    date = "%d-%d-%d" % (day, month, year)
    unix_time = int(time.mktime(datetime.datetime.strptime(date, "%d-%m-%Y").timetuple()))

    # Check if we can fetch price from cache
    cmd = "SELECT Price FROM DotPrice WHERE Timestamp=%d" % (unix_time,)
    cursor = db_con.execute(cmd)
    rows = cursor.fetchall()
    if rows:
        from_cache = rows[0][0]
        return from_cache
    try:
        data = cg.get_coin_history_by_id(id='polkadot',
                                         date=date,
                                         localization='false')
    except HTTPError:
        # Probably too many requests
        return None
    price = float(data["market_data"]["current_price"][CURRENCY])
    cmd = "REPLACE INTO DotPrice(Timestamp, Price) VALUES (%d,%f);" % (unix_time,
                                                                       price)
    db_con.execute(cmd)
    db_con.commit()
    return price


def get_db():
    """Return database connection object."""
    db_con = sqlite3.connect(".pricedata_%s.db" % (CURRENCY,))
    db_con.execute("""CREATE TABLE IF NOT EXISTS DotPrice(
Timestamp INT PRIMARY KEY NOT NULL,
Price FLOAT NOT NULL);
""")
    return db_con


def get_rewards(filename):
    """Parse the given file."""
    rewards = {}
    db_con = get_db()
    cg = CoinGeckoAPI()
    with open(filename) as file:
        lines = [line.rstrip() for line in file.readlines()[1:]]
        for line in lines:
            line = line.split(',')
            if not line[2] == "REWARD_PAYOUT":
                continue
            if not line[1] == "DOT":
                continue
            pattern = '^([0-9]+)-([0-9]+)-([0-9]+)'
            result = re.search(pattern, line[0])
            year = int(result.group(1))
            month = int(result.group(2))
            day = int(result.group(3))
            dot = float(line[3])
            if dot < 0.000001:
                continue
            price = None
            while not price:
                price = get_price(cg, db_con, day, month, year)
                if not price:
                    print("Was unable to retrieve price. Trying again...")
                    time.sleep(1)
            usd = price * dot
            cur = CURRENCY.upper()
            print("%f DOT (%f %s) received on %d/%d/%d" % (dot,
                                                           usd,
                                                           cur,
                                                           month,
                                                           day,
                                                           year))
            if year not in rewards:
                rewards[year] = usd
            else:
                rewards[year] += usd
    return rewards


def main():
    """Read .csv and compute total income."""
    if len(sys.argv) < 2:
        print("Please specify input csv file")
        return 1
    file_name = sys.argv[1]
    rewards = get_rewards(file_name)
    for year, rewards in rewards.items():
        print("%d: %f %s" % (year, rewards, CURRENCY.upper()))
    return 0


if __name__ == "__main__":
    ret = main()
    exit(ret)
