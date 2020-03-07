#!/usr/bin/env python3

import sys
import yaml
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

def load_cfg(file):
    # load yaml config file safely
    with open(file, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    # get current semester if no entry in config
    if config['semester'] is None:
        config['semester'] = semester()
    # replace None values with empty strings and whitespace by '+'
    for key in config:
        if config[key] is None:
            config[key] = ''
        elif ' ' in str(config[key]):
            config[key] = config[key].replace(' ', '+')
    return config


def form_url(cfg):
    # form the correct url to query desired output
    url = "https://usionline.uni-graz.at/usiweb/myusi.kurse?suche_in=go&sem_id_in={s1}&\
sp_id_in=&kursbez_in={s2}&\
kursleiter_in={s3}&\
kursnr_in={s4}&\
wt_in={s5}&\
uhrzeit_von_in={s6}&\
uhrzeit_bis_in={s7}&\
suche_kursstaette_id_in={s8}".format(s1=cfg['semester'],s2=cfg['course'],s3=cfg['instructor'],
s4=cfg['id'],s5=cfg['day'],s6=cfg['after'],s7=cfg['until'],s8=cfg['place'])
    return url


def scrape(url):
    if url is None:
        return None
    try:
        req = request.Request(url)
        opener = request.build_opener()
        content = opener.open(req).read()
    except error.URLError as e:
        sys.exit(e)
    return content


def format(table):
    # get dataframe from list
    df = pd.read_html(str(table))[0]
    num_rows, num_cols = df.shape
    print(num_rows, num_cols)
    # drop everything but the first seven columns
    df.drop(df.columns[7:], axis=1, inplace=True)
    for i in range(0, num_rows, 3):
        df.at[i, 'h'] = df.iloc[i+1,1]
        df.at[i, 'i'] = df.iloc[i+1,2]
        df.at[i, 'j'] = df.iloc[i+2,1]
    df = df[::3]
    # rename columns
    df.columns = ['id', 'course', 'time', 'place', 'rate_a', 'rate_b', 'rate_c', 'instructor', 'num_free', 'text_free']
    # reset row indices
    df.reset_index(drop=True, inplace=True)
    return df


if __name__ == '__main__':
    cfg = load_cfg('config.yml')
    url = form_url(cfg)
    content = scrape(url)
    soup = BeautifulSoup(content, "lxml")
    table = soup.find('table', {"id": "kursangebot"})
    dataframe = format(table)
    # print as formatted dataframe tabulated
    print(tabulate(dataframe, headers='keys', tablefmt='psql'))
