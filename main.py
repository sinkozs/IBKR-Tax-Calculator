import argparse
import datetime
import mnb
import PyPDF2
import re
import time

client = mnb.Mnb()

parser = argparse.ArgumentParser(description="IBKR tax and dividend helper")
parser.add_argument("statement", type=str)
parser.add_argument("start_page", type=int)
parser.add_argument("end_page", type=int)
parser.add_argument("year", type=int)
args = parser.parse_args()

with open(args.statement, 'rb') as f:
    reader = PyPDF2.PdfReader(f)

    tax_sum_usd = 0.0
    tax_sum_huf = 0.0
    tax_len = 0
    tax = []
    div_sum_usd = 0.0
    div_sum_huf = 0.0
    div_len = 0
    div = []
    for i in range(args.start_page, args.end_page):

        page = reader.pages[i]

        text = page.extract_text()
        tax_match = re.findall(rf'(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+).+(?:US|CA)\n* *Tax *(?P<taxv>-*\d+\.\d+)', text)
        if not tax_match:
            print(f"tax regex error on page {i}")
        tax += tax_match

        div_match = re.findall(rf'(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+).+\n*\((?:Ordinary|Limited|Bonus)\n* *(?:Dividend|Partnership)\)(?P<divv>-*\d+\.\d+)', text)
        if not div_match:
            print(f"div regex error on page {i}")
        div += div_match

    for t in tax:
        if int(t[0]) == args.year:
            tax_len += 1
            year = int(t[0])
            month = int(t[1])
            day = int(t[2])
            usdv = float(t[3])
            tax_sum_usd += usdv
            exchange_rate = client.get_exchange_rates(datetime.date(year, month, day), datetime.date(year, month, day), ["USD"])
            if not exchange_rate:
                print(f"exchange rate error - {year}-{month}-{day}, trying again with - {year}-{month}-{day+1}")
                day += 1
            exchange_rate = client.get_exchange_rates(datetime.date(year, month, day), datetime.date(year, month, day), ["USD"])
            uds2huf_rate = exchange_rate[0].rates[0].rate
            tax_sum_huf += usdv * uds2huf_rate
        time.sleep(0.1)

    print(f"tax [USD]: {tax_sum_usd}")
    print(f"tax [HUF]: {tax_sum_huf}")
    print(f"tax transactions: {tax_len}")

    for d in div:
        if int(d[0]) == args.year:
            div_len += 1
            year = int(d[0])
            month = int(d[1])
            day = int(d[2])
            usdv = float(d[3])
            div_sum_usd += usdv
            exchange_rate = client.get_exchange_rates(datetime.date(year, month, day), datetime.date(year, month, day), ["USD"])
            if not exchange_rate:
                print(f"exchange rate error - {year}-{month}-{day}, trying again with - {year}-{month}-{day+1}")
                day += 1
            exchange_rate = client.get_exchange_rates(datetime.date(year, month, day), datetime.date(year, month, day), ["USD"])
            uds2huf_rate = exchange_rate[0].rates[0].rate
            div_sum_huf += usdv * uds2huf_rate
        time.sleep(0.1)

    print(f"div [USD]: {div_sum_usd}")
    print(f"div [HUF]: {div_sum_huf}")
    print(f"div transactions: {div_len}")