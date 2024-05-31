import argparse
import datetime
import mnb
import PyPDF2
import re
import time


def parse_pdf():
    tax = []
    div = []

    with open(args.input[0], "rb") as f:
        reader = PyPDF2.PdfReader(f)

        for i in range(args.pages[0], args.pages[-1]):
            page = reader.pages[i]

            text = page.extract_text()
            # regex has to match the following:
            # 2023-09-11 IBM(US4592001014) Cash Dividend USD 1.66 per Share - US Tax -2.99
            #
            # 2023-01-16CAH(US14149Y1082) Cash Dividend USD 0.4957 per Share - US
            # Tax-0.60
            #
            # ENB(CA29250N1050) Cash Dividend USD 0.65161 per Share - CA Tax -2.25
            match = re.findall(rf"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+).+(?:US|CA)\n* *Tax *(?P<taxv>-*\d+\.\d+)",
                               text)
            if not match and args.verbose:
                print(f"tax regex error on page {i}")
            tax += match

            # # regex has to match the following:
            # 2023-03-15ED(US2091151041) Cash Dividend USD 0.81 per Share (Ordinary Dividend)
            #  0.88 per Share (Ordinary Dividend)
            #
            # 2022-05-13MMP(US5590801065) Cash Dividend USD 1.0375 per Share (Limited Partnership)9.34
            #
            # 2023-08-31ETD(US2976021046) Cash Dividend USD 0.50 per Share (Bonus Dividend)24.00
            match = re.findall(
                rf"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+).+\n*\((?:Ordinary|Limited|Bonus)\n* *(?:Dividend|Partnership)\)(?P<divv>-*\d+\.\d+)",
                text)
            if not match and args.verbose:
                print(f"div regex error on page {i}")
            div += match
    return tax, div


def filter_by_year(input_list):
    filtered_list = [x for x in input_list if int(x[0]) == args.year[0]]
    return filtered_list


def calc_totals(raw_data):
    totals = {"usd": 0.0, "huf": 0.0}

    for t in raw_data:
        year = int(t[0])
        month = int(t[1])
        day = int(t[2])
        usdv = float(t[3])
        totals["usd"] += usdv
        exchange_rate = []
        while not exchange_rate:
            exchange_rate = client.get_exchange_rates(datetime.date(year, month, day), datetime.date(year, month, day),
                                                      ["USD"])
            if not exchange_rate:
                if args.verbose:
                    print(f"exchange rate error - {year}-{month}-{day}, trying again with - {year}-{month}-{day + 1}")
                day += 1
        exchange_rate = client.get_exchange_rates(datetime.date(year, month, day), datetime.date(year, month, day),
                                                  ["USD"])
        uds2huf_rate = exchange_rate[0].rates[0].rate
        totals["huf"] += usdv * uds2huf_rate
        time.sleep(0.1)
    return totals


if __name__ == "__main__":
    client = mnb.Mnb()

    parser = argparse.ArgumentParser(description="IBKR tax and dividend helper")
    parser.add_argument("-i", "--input", type=str, nargs=1, required=True, help="input statement (.pdf)")
    parser.add_argument("-p", "--pages", type=int, nargs="+", required=True,
                        help="start and end pages of tax and dividend info")
    parser.add_argument("-y", "--year", type=int, nargs=1, required=True, help="year filter")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    args = parser.parse_args()

    print("Parsing pdf...")
    tax, div = parse_pdf()
    tax = filter_by_year(tax)
    div = filter_by_year(div)

    print("Calculating tax totals...")
    totals_tax = calc_totals(tax)
    print(f"tax [USD]: {totals_tax['usd']}")
    print(f"tax [HUF]: {totals_tax['huf']}")
    print(f"# of tax transactions: {len(tax)}")

    print("Calculating div totals...")
    totals_div = calc_totals(div)
    print(f"div [USD]: {totals_div['usd']}")
    print(f"div [HUF]: {totals_div['huf']}")
    print(f"# of div transactions: {len(div)}")
