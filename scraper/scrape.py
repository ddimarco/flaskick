#!/bin/env python3

from bs4 import BeautifulSoup
import yaml
import urllib.request
import time
import datetime
import os

def create_filename(year, month, day):
    return 'data/df-kicker-%s_%s_%s.yaml' % (year, month, day)

def extract_kicker_day(html_doc, url):
    soup = BeautifulSoup(html_doc, 'html.parser')

    date = soup.find('div', class_='current').text

    match_elems = soup.find_all('li', class_='m-match')

    def extract_team_members(mmatch_team):
        return [member['title'] for member in mmatch_team.find_all('span', class_='m-match--team--member')]

    next_day_div = soup.find('div', class_='next')
    next_day_url = next_day_div.find('a', class_='m-link')['href']

    print('next day: %s' % next_day_url)
    match_dicts = []
    for match in match_elems:
        # match id
        match_id = match['data-id']

        # teams
        teams = match.find_all('a', class_='m-match--team')
        assert(len(teams) == 2)

        # kicker.cool team id
        team1_id = teams[0]['href']
        team2_id = teams[1]['href']

        print("%s (%s) vs %s (%s)" % \
              (extract_team_members(teams[0]), team1_id, \
               extract_team_members(teams[1]), team2_id))

        winner_team = None
        loser_team = None
        winner_idx = -1
        if 'as-winner' in teams[0]['class']:
            winner_team = teams[0]
            loser_team = teams[1]
            winner_idx = 0
        if 'as-winner' in teams[1]['class']:
            winner_team = teams[1]
            loser_team = teams[0]
            winner_idx = 1
        # assert(winner_team is not None)
        # assert(loser_team is not None)
        # print('winners were: %s' % extract_team_members(winner_team))

        crawling = 'as-crawling' in match['class']
        if crawling:
            print('with crawling!')

        # score
        score_elem = match.find('div', class_='m-match--score')
        difference_elem = score_elem.find('div', class_='m-match--score--difference')
        score = difference_elem.previousSibling.strip()
        print('score: %s' % score)

        # difference
        difference = difference_elem.text.strip()
        print('diff: %s' % difference)

        match_dict = {
            'match_id': match_id,
            'team1': extract_team_members(teams[0]),
            'team2': extract_team_members(teams[1]),
            'winner_team_idx': winner_idx,
            'crawling': crawling,
            'score': score,
            'difference': int(difference),
        }
        match_dicts.append(match_dict)

        print('---')

    return {
        'date': date,
        'url': url,
        'next_day_url': next_day_url,
        'matches': match_dicts
    }

def ymd_date_to_url(year, month, day):
    return 'https://kicker.cool/deepfield/matches?date=%s-%s-%s' % (year, month, day)

def next_url_from_dict(day_dict):
    next_day_url = day_dict['next_day_url']
    next_day_string = next_day_url.split('=')[1]
    [year, month, day] = next_day_string.split('-')
    return (year, month, day)


# earliest entry: https://kicker.cool/deepfield/matches?date=2015-09-02
(year, month, day) = ('2015', '09', '02')

#(end_year, end_month, end_day) = ('2016', '03', '20')
today = datetime.date.today()
(end_year, end_month, end_day) = ('%04d' % today.year, '%02d' % today.month, '%02d' % today.day)

dled = 0
while year != end_year or month != end_month or day != end_day:
    # file already there?
    filename = create_filename(year, month, day)
    if os.path.isfile(filename):
        print('entry "%s" already scraped, skipping...' % filename)
        day_dict = None
        with open(filename, 'r') as infile:
            day_dict = yaml.load(infile)
        (year, month, day) = next_url_from_dict(day_dict)
        continue

    # download site
    url = ymd_date_to_url(year, month, day)
    print('downloading site from %s' % url)
    with urllib.request.urlopen(url) as response:
       html = response.read()

    day_dict = extract_kicker_day(html, url)
    [day, month, year] = day_dict['date'].split('.')
    filename = create_filename(year, month, day)
    with open(filename, 'w') as outfile:
        #json.dump(match_dicts, outfile, sort_keys=True, indent=2, ensure_ascii=False)
        yaml.dump(day_dict, outfile)
    dled += 1

    (year, month, day) = next_url_from_dict(day_dict)
    time.sleep(2)
