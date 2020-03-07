#!/usr/bin/env python3

from datetime import datetime
import urllib.request as request
import urllib.error as error
from http import cookiejar
from bs4 import BeautifulSoup
import pandas as pd
from tabulate import tabulate


def semester():
    year = datetime.now().strftime('%Y')
    month = int(datetime.now().strftime('%m'))
    if 2 <= month < 9:
        semester = year + "S"
    else:
        semester = year + "W"
    return semester


def scrape(url):
    if url is None:
        return None
    try:
        req = request.Request(url)
        cj = cookiejar.FileCookieJar(filename="./cookies.txt")
        cp = request.HTTPCookieProcessor(cookiejar=cj)
        opener = request.build_opener()
        content = opener.open(req).read()
    except error.URLError as e:
        print('Webscraper Error:', e.reason)
        content = None
    return content


if __name__ == '__main__':
    # input the name of the course
    kbz = "basketball"
    # form the correct url to query desired output
    url = "https://usionline.uni-graz.at/usiweb/myusi.kurse?suche_in=go&sem_id_in={s1}&sp_id_in=&kursbez_in={s2}&\
kursleiter_in=&kursnr_in=&wt_in=&uhrzeit_von_in=&uhrzeit_bis_in=&suche_kursstaette_id_in=".format(s1=semester(), s2=kbz)
    content = scrape(url)
    soup = BeautifulSoup(content, "lxml")
    table = soup.find_all('table', {"id": "kursangebot"})
    df = pd.read_html(str(table))[0]
    # drop everything but the first four columns
    df.drop(df.columns[4:], axis=1, inplace=True)
    # drop every third row
    df.drop(df.index[2::3], inplace=True)
    print(tabulate(df, headers='keys', tablefmt='psql'))