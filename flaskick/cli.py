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

import trueskill


@click.group()
def cli():
    pass


@cli.command()
def test():
    pass

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
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=5000)
def serve(host, port):
    db.create_all()
    app.run(host=host, port=port)


@cli.command()
def dbg():
    with open('/tmp/kicker.htm', 'r') as infile:
        html = infile.read()
    data = extract_kicker_day(html)
    print(data)

@cli.command()
def ts():
    from flaskick.models import Match, MatchDay, Player, PlayerStat, Team, TeamStat
    matches = Match.query.join(MatchDay, Match.matchday).order_by(MatchDay.date)
    ratings = {p.id: trueskill.Rating() for p in Player.query}

    def _team_ratings(team):
        rat = [ratings[team.player1_id]]
        if team.player2:
            rat.append(ratings[team.player2_id])
        return rat
    for m in matches:
        won_team, lost_team = m.team1, m.team2
        t1_ratings = _team_ratings(won_team)
        t2_ratings = _team_ratings(lost_team)
        q = trueskill.quality([t1_ratings, t2_ratings])
        new_ratings_won, new_ratings_lost = trueskill.rate([t1_ratings, t2_ratings])
        ratings[won_team.player1_id] = new_ratings_won[0]
        if won_team.player2:
            ratings[won_team.player2_id] = new_ratings_won[1]
        ratings[lost_team.player1_id] = new_ratings_lost[0]
        if lost_team.player2:
            ratings[lost_team.player2_id] = new_ratings_lost[1]

    playerids = sorted(ratings.keys(), key=lambda pid: trueskill.expose(ratings[pid]))
    # for player_id, rating in ratings.iteritems():
    for player_id in playerids:
        rating = ratings[player_id]
        player = Player.query.filter(Player.id == player_id).first()
        print ("{}: {} {}".format(player.name.encode('utf-8'), rating,
                                  trueskill.expose(rating)))


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
