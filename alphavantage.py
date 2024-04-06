import csv
import requests
import json
import os
import math

from enum import Enum
import time

class StatusResults(Enum):
    Default = -1
    FreshlyCollected = 0
    AlreadyCollected = 1
    MinLimit = 100
    DayLimit = 102

class StatusSaving(Enum):
    CreatedFile = 0
    FileExists = 1
    EmptyFile = 2

class CompanyEarnings:

    def __init__(self, company_symbol):
        self._company_symbol = company_symbol
        self._key_file = os.path.abspath(f"{__file__}/../../../.key")
        self._key = None
        with open(self._key_file) as f:
            self._key = f.read()

        self._url = "https://www.alphavantage.co/query"
        self._params = {
            "function": "EARNINGS",
            "symbol": self._company_symbol,
            "apikey": self._key,
            "datatype": "json"
        }
        self._response = None

    def _get_earnings(self):
        if self._response is None:
            self._response = requests.get(url=self._url, params=self._params).json()
            if dict(self._response).get("Note"):
                print(self._response)
                self._response = None
                return StatusResults.MinLimit
            elif dict(self._response).get("symbol") == self._company_symbol.upper() or len(dict(self._response)) == 0:
                return StatusResults.FreshlyCollected
        else:
            print(f"collected earnings already: {self._company_symbol}: {self._response}")
            return StatusResults.AlreadyCollected

    def save_results(self):
        file_path = os.path.abspath(f"{__file__}/../../../earnings_data/{self._company_symbol}.json")
        if not os.path.exists(file_path):
            sleep_counter = 0
            status = StatusResults.Default
            while status not in [StatusResults.FreshlyCollected, StatusResults.AlreadyCollected] and sleep_counter<2:
                status = self._get_earnings()
                if status == StatusResults.MinLimit:
                    print("triggering sleep")
                    time.sleep(60)
                    sleep_counter+=1
            # if sleep counter happens twice, it means we waited for atleast 1 min
            # but still failed to fetch due to api limit
            # so it must have hit day limit so inform that we need to wait for next day
            if sleep_counter<2:
                with open(file_path, "w") as outfile:
                    json.dump(self._response, outfile, indent=4)
                if len(dict(self._response)) == 0:
                    return StatusSaving.EmptyFile
                return StatusSaving.CreatedFile
            else:
                return StatusResults.DayLimit
        else:
            return StatusSaving.FileExists



class Fetch:

    def __init__(self):
        self._company_symbols_file = os.path.abspath(f"{__file__}/../../company_names.txt")
        with open(self._company_symbols_file) as f:
            self._company_symbols = f.read().split("\n")

    def start(self, limit=-1):
        companies_created = 0
        companies_skipped = 0
        no_data_companies = 0
        start_time = time.time()
        for company_symbol in self._company_symbols:
            ce = CompanyEarnings(company_symbol)
            status = ce.save_results()
            if status == StatusResults.DayLimit:
                print("done for the day")
                break
            elif status == StatusSaving.CreatedFile:
                companies_created+=1
            elif status == StatusSaving.FileExists:
                companies_skipped+=1
            elif status == StatusSaving.EmptyFile:
                no_data_companies+=1

            if limit > 0 and companies_created>=limit:
                break
            end_time = time.time()
            if end_time-start_time>60:
                print(
                    f"{end_time-start_time}: "
                    f"last status: {status}, "
                    f"companies_created: {companies_created}, "
                    f"companies_skipped: {companies_skipped}, "
                    f"no_data_companies: {no_data_companies}, "
                    f"limit used: {limit}"
                )
                start_time = end_time

        print(
            f"last status: {status}, "
            f"companies_created: {companies_created}, "
            f"companies_skipped: {companies_skipped}, "
            f"no_data_companies: {no_data_companies}, "
            f"limit used: {limit}"
        )


if __name__ == "__main__":
    fetch = Fetch()
    fetch.start()