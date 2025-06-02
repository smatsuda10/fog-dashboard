"""
Example script that scrapes data from the IEM ASOS download service.

More help on CGI parameters is available at:

    https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?help

Requires: Python 3
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from urllib.request import urlopen

# Number of attempts to download data
MAX_ATTEMPTS = 6
# HTTPS here can be problematic for installs that don't have Lets Encrypt CA
SERVICE = "http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"


def download_data(uri):
    """Fetch the data from the IEM

    The IEM download service has some protections in place to keep the number
    of inbound requests in check.  This function implements an exponential
    backoff to keep individual downloads from erroring.

    Args:
      uri (string): URL to fetch

    Returns:
      string data
    """
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        try:
            data = urlopen(uri, timeout=300).read().decode("utf-8")
            if data is not None and not data.startswith("ERROR"):
                return data
        except Exception as exp:
            print(f"download_data({uri}) failed with {exp}")
            time.sleep(5)
        attempt += 1

    print("Exhausted attempts to download, returning empty data")
    return ""


def main():
    """Our main method"""
    # timestamps in UTC to request data for
    startts = datetime(2023, 8, 1)
    endts = datetime(2024, 9, 1)

    service = SERVICE + "data=all&tz=Etc/UTC&format=comma&latlon=yes&"

    service += startts.strftime("year1=%Y&month1=%m&day1=%d&")
    service += endts.strftime("year2=%Y&month2=%m&day2=%d&")

    stations = ['HAF']
    for station in stations:
        uri = f"{service}&station={station}"
        print(f"Downloading: {station}")
        data = download_data(uri)
        outfn = f"data/{station}_{startts:%Y%m%d%H%M}_{endts:%Y%m%d%H%M}.csv"
        with open(outfn, "w", encoding="ascii") as fh:
            fh.write(data)


if __name__ == "__main__":
    main()