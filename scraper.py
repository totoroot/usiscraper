#!./venv/bin/python

import sys
import argparse
import yaml
import json
from datetime import datetime
import urllib.request as request
import urllib.error as error
from bs4 import BeautifulSoup
import pandas as pd
import re
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
    try:
        config = yaml.safe_load(file)
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
    url = "https://usionline.uni-graz.at/usiweb/myusi.kurse?suche_in=go&sem_id_in={0}&\
sp_id_in=&kursbez_in={1}&\
kursleiter_in={2}&\
kursnr_in={3}&\
wt_in={4}&\
uhrzeit_von_in={5}&\
uhrzeit_bis_in={6}&\
suche_kursstaette_id_in={7}".format(cfg['semester'],cfg['course'],cfg['instructor'],
cfg['id'],cfg['day'],cfg['after'],cfg['until'],cfg['place'])
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
    num_rows, _ = df.shape
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


def report_free(df, file):
    free = {}
    index = 0
    for value in df.iloc[:,0]:
        if 'AUSG' not in str(value):
            num_free = str(df.iloc[index, 8])
            free[value] = int(re.search(r'\d+', num_free).group())
        index += 1
    if file.name.split(".")[-1] == 'json':
        json.dump(free, file)
    elif file.name.split(".")[-1] == 'yml' or file.name.split(".")[-1] == 'yaml':
        yaml.dump(free, file)
    else:
        sys.exit('Error: YAML or JSON output supported only.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='USI Graz Webscraper')
    parser.add_argument('-d', '--debug', action='store_true', help='print tabulated results and exit')
    parser.add_argument('--input', nargs='?', type=argparse.FileType('r'), default='config.yml', help='YAML or JSON config input file')
    parser.add_argument('--output', nargs='?', type=argparse.FileType('w'), default='free.json', help='YAML or JSON report output file')
    args = parser.parse_args()

    cfg = load_cfg(args.input)

    url = form_url(cfg)

    content = scrape(url)

    soup = BeautifulSoup(content, "lxml")
    table = soup.find('table', {"id": "kursangebot"})

    # format dataframe due to poor html implementation of USI website
    dataframe = format(table)

    # print as formatted dataframe tabulated for debugging purposes or export file
    if args.debug:
        print(tabulate(dataframe, headers='keys', tablefmt='psql'))
    else :
        report_free(dataframe, args.output)
