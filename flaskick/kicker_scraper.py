#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

import requests
import datetime

 # r = requests.get('https://ungif.apps.railslabs.com/ungif?url=http://freestockgallery.de/hintergrund/rote-backsteinwand-939.thumb_large.jpg&size=80x80', stream=True)
 # if r.status_code == 200:
 #     with open('/tmp/img.jpg', 'wb') as f:
 #         r.raw.decode_content = True
 #         shutil.copyfileobj(r.raw,f)

def download_and_parse_date(date):
    url = ymd_date_to_url(date.year, date.month, date.day)
    return download_and_parse_url(url)


def download_and_parse_url(url):
    print('downloading site from %s' % url)
    # with urllib.request.urlopen(url) as response:
    #     html = response.read()
    #     return extract_kicker_day(html)
    r = requests.get(url)
    return extract_kicker_day(r.text)


def ymd_date_to_url(year, month, day, league='deepfield'):
    return 'https://kicker.cool/{}/matches?date={:04d}-{:02d}-{:02d}'.format(
        league, year, month, day)


def extract_kicker_day(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    date_str = soup.find('div', class_='current').text
    day, month, year = map(int, date_str.split('.'))
    date = datetime.date(year=year, month=month, day=day)

    match_elems = soup.find_all('li', class_='m-match')

    def extract_team_members(mmatch_team):
        return [
            member['title']
            for member in mmatch_team.find_all(
                'span', class_='m-match--team--member')
        ]

    next_day_div = soup.find('div', class_='next')
    next_day_url = next_day_div.find('a', class_='m-link')['href']

    avatars = {}
    match_dicts = []
    for match in match_elems:
        match_id = match['data-id']
        teams = match.find_all('a', class_='m-match--team')
        assert (len(teams) == 2)
        for team in teams:
            for member in team.find_all('span', class_='m-match--team--member'):
                name = member['title']
                img = member.find('img', class_='m-user-image')
                if img and (name not in avatars):
                    avatars[name] = img['src']
        # kicker.cool team id
        # team1_id = teams[0]['href']
        # team2_id = teams[1]['href']
        # print("%s (%s) vs %s (%s)" % \
        #       (extract_team_members(teams[0]), team1_id, \
        #        extract_team_members(teams[1]), team2_id))
        winner_idx = -1
        if 'as-winner' in teams[0]['class']:
            winner_idx = 0
        if 'as-winner' in teams[1]['class']:
            winner_idx = 1
        crawling = 'as-crawling' in match['class']
        score_elem = match.find('div', class_='m-match--score')
        difference_elem = score_elem.find(
            'div', class_='m-match--score--difference')
        score = difference_elem.previousSibling.strip()
        difference = difference_elem.text.strip()
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
    # make sure we have the games in the right order (assuming ids are ascending)
    match_dicts.sort(key=lambda d: d['match_id'])
    return {'date': date, 'next_day_url': next_day_url, 'matches': match_dicts, 'avatars': avatars}

def main():
    with open('/tmp/kicker.html', 'r') as infile:
        html_doc = infile.read()

    day = extract_kicker_day(html_doc)
    print(day)


if __name__ == '__main__':
    main()
