#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import click

from flaskick.app import app, db
from flaskick.models import import_matches_from_path
from flaskick.views import index
from flaskick.api import api

import datetime
from flaskick.kicker_scraper import download_and_parse_date, download_and_parse_url, extract_kicker_day
import time
import yaml
import os


@click.group()
def cli():
    pass


@cli.command()
def test():
    pass


# GAMES_YAML_PATH = '/home/dm/code/kicker-scraper/data'


@cli.command("import")
@click.argument("data-path")
def import_matches_cli(data_path):
    db.create_all()
    import_matches_from_path(data_path)

@cli.command()
def reset():
    db.drop_all()
    db.create_all()


@cli.command()
def serve():
    db.create_all()
    app.run()


@cli.command()
def dbg():
    with open('/tmp/kicker.htm', 'r') as infile:
        html = infile.read()
    data = extract_kicker_day(html)
    print(data)


@cli.command()
@click.argument('date')
@click.argument('outdir')
def scrape(date, outdir):
    year, month, day = map(int, date.split('-'))
    data = download_and_parse_date(datetime.date(year, month, day))
    while True:
        next_url = 'http://www.kicker.cool' + data['next_day_url']
        fname = os.path.join(outdir, data['date'].strftime('%Y%m%d.yaml'))
        if os.path.isfile(fname):
            break
        with open(fname, 'w') as outfile:
            yaml.safe_dump(data, outfile)
        time.sleep(2)
        data = download_and_parse_url(next_url)
        if data['date'] > datetime.date.today():
            break



if __name__ == '__main__':
    cli()
