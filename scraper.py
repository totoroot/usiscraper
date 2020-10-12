#!/usr/bin/env python3

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
import os
from dotenv import load_dotenv
import time
from datetime import timezone
from influxdb import InfluxDBClient


def init_influx():
    """Initialize InfluxDB client and create database if it does not exist yet."""
    # load environment variables from .env file
    load_dotenv()

    # InfluxDB settings
    DB_ADDRESS = os.environ.get('INFLUXDB_ADDRESS')
    DB_PORT = int(os.environ.get('INFLUXDB_PORT'))
    DB_USER = os.environ.get('INFLUXDB_USER')
    DB_PASSWORD = os.environ.get('INFLUXDB_PASSWORD')
    DB_DATABASE = os.environ.get('INFLUXDB_DATABASE')

    # create InfluxDB client
    cl = InfluxDBClient(
        DB_ADDRESS, DB_PORT, DB_USER, DB_PASSWORD, None)

    databases = cl.get_list_database()
    if len(list(filter(lambda x: x['name'] == DB_DATABASE, databases))) == 0:
        cl.create_database(
            DB_DATABASE)
    else:
        cl.switch_database(DB_DATABASE)
    return(cl)


def semester():
    """Form semester string."""
    year = datetime.now().strftime('%Y')
    month = int(datetime.now().strftime('%m'))
    if 2 <= month < 9:
        semester = year + "S"
    else:
        semester = year + "W"
    return semester


def load_cfg(file):
    """Load and parse config."""
    # load yaml config file safely
    try:
        cfg = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)
    # get current semester if no entry in config
    if cfg['semester'] is None:
        cfg['semester'] = semester()
    # replace None values with empty strings and whitespace by '+'
    for key in cfg:
        if cfg[key] is None:
            cfg[key] = ''
        elif ' ' in str(cfg[key]):
            cfg[key] = cfg[key].replace(' ', '+')
    return cfg


def form_url(cfg):
    """Form correct url to query desired output."""
    url = "https://usionline.uni-graz.at/usiweb/myusi.kurse?suche_in=go&\
sem_id_in={0}&\
sp_id_in={1}&\
kursbez_in={2}&\
kursleiter_in={3}&\
kursnr_in={4}&\
wt_in={5}&\
uhrzeit_von_in={6}&\
uhrzeit_bis_in={7}&\
suche_kursstaette_id_in={8}".format(cfg['semester'],cfg['discipline'],cfg['course'],cfg['instructor'],
cfg['id'],cfg['weekday'],cfg['after'],cfg['until'],cfg['location'])
    return url


def scrape(url):
    """Scrape USI webpage for HTML content."""
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
    """Extract dataframe from HTML content."""
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
    df.columns = ['id', 'course', 'time', 'location', 'rate_a', 'rate_b', 'rate_c', 'instructor', 'num_free', 'text_free']
    # reset row indices
    df.reset_index(drop=True, inplace=True)
    return df


def report_free(df, file):
    """Report vacancies and write to specified file."""
    # remove all fully booked courses and populate dictionary with vacancies
    free = {}
    index = 0
    for value in df.iloc[:,0]:
        if 'AUSG' not in str(value):
            num_free = str(df.iloc[index, 8])
            free[value] = int(re.search(r'\d+', num_free).group())
        index += 1
        # write to file
    if file.name.split(".")[-1] == 'json':
        json.dump(free, file)
    elif file.name.split(".")[-1] == 'yml' or file.name.split(".")[-1] == 'yaml':
        yaml.dump(free, file)
    else:
        sys.exit('Error: YAML or JSON output supported only.')


def report_influx(cl, df, ts):
    """Report vacancies to InfluxDB."""
    # remove "AUSG" from course ID and populate dictionary with all courses and open spots
    free = {}
    index = 0
    for value in df.iloc[:,0]:
        if 'AUSG' in str(value):
            value = str(value).replace('AUSG', '')
        num_free = str(df.iloc[index, 8])
        free[value] = int(re.search(r'\d+', num_free).group())
        index += 1
    # translate vacancies to InfluxDB line protocol with UTC timestamp
    free_influx = []
    for key, value in free.items():
        free_influx.append(
            {
                'measurement': "free",
                'tags': {
                    'course': str(key)
                },
                'time': ts,
                'fields': {
                    'value': int(value)
                }
            }
        )
    # write to database
    cl.write_points(free_influx)


def main():
    """Main"""
    # get path of python script
    abs_file_path = os.path.abspath(__file__)
    path, filename = os.path.split(abs_file_path)
    # parse arguments
    parser = argparse.ArgumentParser(description='USI Graz Webscraper')
    parser.add_argument('-d', '--debug', action='store_true', help='print tabulated results and exit')
    parser.add_argument('-i', '--influx', action='store_true', help='write free spaces to InfluxDB specified in .env')
    parser.add_argument('--input', nargs='?', type=argparse.FileType('r'), default=str(os.path.join(path, 'config.yml')), help='YAML or JSON config input file')
    parser.add_argument('--output', nargs='?', type=argparse.FileType('w'), default=str(os.path.join(path, 'free.json')), help='YAML or JSON report output file')
    args = parser.parse_args()
    # load config file
    cfg = load_cfg(args.input)
    # get USI URL to query
    url = form_url(cfg)
    # query URL, scrape and format as table
    print('{} - Starting to scrape...'.format(datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')))
    content = scrape(url)
    soup = BeautifulSoup(content, "lxml")
    table = soup.find('table', {"id": "kursangebot"})
    # format dataframe due to poor html implementation of USI website
    dataframe = format(table)
    # print as formatted dataframe tabulated for debugging purposes or send to InfluxDB and export file
    if args.debug:
        # print table to STDOUT
        print(tabulate(dataframe, headers='keys', tablefmt='psql'))
    if args.influx:
        # send data to InfluxDB
        client = init_influx()
        timestamp = datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        report_influx(client, dataframe, timestamp)
    # write vacancies to file
    report_free(dataframe, args.output)
    print('{} - Done!'.format(timestamp))


if __name__ == '__main__':
    main()
