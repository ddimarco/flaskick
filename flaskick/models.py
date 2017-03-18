# -*- coding: utf-8 -*-
import datetime
import os

import yaml

from flaskick.app import db


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    stat_id = db.Column(
        db.Integer, db.ForeignKey('player_stat.id'), nullable=False)
    stat = db.relationship('PlayerStat', back_populates='player')

    def __repr__(self):
        return '<Player %s>' % self.name

    @property
    def to_json(self):
        return {
            'type': 'player',
            'id': self.id,
            'attributes': {
                'name': self.name,
                'points': self.stat.points
            },
            'relationships': {
                'statistics': {
                    'data': {
                        'id': self.id,
                        'type': 'statistic'
                    }
                }
            }
        }


class PlayerStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.relationship('Player', uselist=False, back_populates='stat')
    points = db.Column(db.Integer, nullable=False)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player1 = db.relationship('Player', uselist=False, primaryjoin='Team.player1_id == Player.id')
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    player2 = db.relationship('Player', uselist=False, primaryjoin='Team.player2_id == Player.id')
    stat_id = db.Column(
        db.Integer, db.ForeignKey('team_stat.id'), nullable=False)
    stat = db.relationship('TeamStat', back_populates='team')

    def __repr__(self):
        return '<Team %i, Players %s>' % (self.id,
                                          [self.player1, self.player2]
                                          if self.player2 else [self.player1])

    @property
    def to_json(self):
        return {
            'type': 'team',
            'id': self.id,
            # 'player1': self.player1,
            # 'player2': self.player2
            'attributes': {
                'points': self.stat.points
            },
            'relationships': {
                'player1': {
                    'data': {
                        'id': self.player1.id,
                        'type': 'player'
                    }
                },
                'player2': {
                    'data': {
                        'id': self.player2.id,
                        'type': 'player'
                    }
                },
                'statistics': {
                    'data': {
                        'id': self.id,
                        'type': 'teamstatistic'
                    }
                }
            }
        }


class TeamStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team = db.relationship('Team', uselist=False, back_populates='stat')
    points = db.Column(db.Integer, nullable=False)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # team1 = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team1 = db.relationship('Team', uselist=False, primaryjoin='Match.team1_id == Team.id')
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team2 = db.relationship('Team', uselist=False, primaryjoin='Match.team2_id == Team.id')
    goals_team1 = db.Column(db.Integer, nullable=False, autoincrement=False)
    goals_team2 = db.Column(db.Integer, nullable=False, autoincrement=False)
    points = db.Column(db.Integer, nullable=False, autoincrement=False)
    crawling = db.Column(db.Boolean, nullable=False)
    matchday_id = db.Column(db.Integer, db.ForeignKey('matchday.id'))
    matchday = db.relationship('MatchDay', backref='matches')

    @property
    def to_json(self):
        return {
            'type': 'match',
            'id': self.id,
            'attributes': {
                'goals1': self.goals_team1,
                'goals2': self.goals_team2,
                'points': self.points,
                'crawling': self.crawling,
            },
            'relationships': {
                'team1': {
                    'data': {
                        'id': self.team1,
                        'type': 'team'
                    }
                },
                'team2': {
                    'data': {
                        'id': self.team2,
                        'type': 'team'
                    }
                }
            },
            'matchday_id': self.matchday_id
        }


class MatchDay(db.Model):
    __tablename__ = 'matchday'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)

    @property
    def to_json(self):
        return {
            'type': 'matchday',
            'id': self.id,
            'attributes': {
                'date': self.date.isoformat()
            },
            'relationships': {
                'matches': {
                    'data': [m.to_json for m in self.matches]
                }
            }
        }


def playerids2team(ids):
    assert (len(ids) <= 2)
    assert (len(ids) > 0)
    p1 = ids[0]
    if len(ids) == 1:
        return Team.query.filter(Team.player1_id == p1,
                                 Team.player2_id.is_(None)).first()
    p2 = ids[1]
    return Team.query.filter(
        db.or_(
            db.and_(Team.player1_id == p1, Team.player2_id == p2),
            db.and_(Team.player1_id == p2, Team.player2_id == p1))).first()


def playername2player(player_name):
    player_qry = Player.query.filter(Player.name == player_name).first()
    assert (player_qry)
    return player_qry


def add_team(t1, pointsdiff):
    if len(t1) == 1:
        p1 = t1[0]
        t_qry = Team.query.filter(Team.player1 == p1,
                                  Team.player2_id.is_(None)).first()
        if not t_qry:
            print('adding single player team: %s' % t1)
            team = Team()
            team.player1 = t1[0]
            db.session.add(team)
            tm_stat = TeamStat(team=team, points=1200 + pointsdiff)
            db.session.add(tm_stat)
        else:
            print('single player team found: %s' % t_qry)
            t_qry.stat.points += pointsdiff
    elif len(t1) == 2:
        p1 = t1[0]#.id
        p2 = t1[1]#.id
        t_qry = Team.query.filter(
            db.or_(
                db.and_(Team.player1 == p1, Team.player2 == p2),
                db.and_(Team.player1 == p2, Team.player2 == p1))).first()
        if not t_qry:
            # print('adding team: %s' % t1)
            team = Team()
            team.player1 = t1[0]#.id
            team.player2 = t1[1]#.id
            db.session.add(team)
            tm_stat = TeamStat(team=team, points=1200 + pointsdiff)
            db.session.add(tm_stat)
        else:
            # print ('team found: %s' % t_qry)
            t_qry.stat.points += pointsdiff


def import_matches(path):
    matchdays_all = {}
    for fn in os.listdir(path):
        with open('%s/%s' % (path, fn), 'r') as infile:
            day = yaml.load(infile)
        matchdays_all[day['date']] = day
    # create db data
    # players
    for day, md in matchdays_all.items():
        for m in md['matches']:
            for p in m['team1'] + m['team2']:
                win = p in m['team1']
                pointsdiff = m['difference'] if win else -m['difference']
                player_qry = Player.query.filter(Player.name == p).first()
                if not player_qry:
                    plr = Player(name=p)
                    db.session.add(plr)
                    plr_stats = PlayerStat(
                        player=plr, points=1200 + pointsdiff)
                    db.session.add(plr_stats)
                else:
                    # just update the points
                    player_qry.stat.points += pointsdiff
    # teams
    for day, md in matchdays_all.items():
        for m in md['matches']:
            t1 = [playername2player(p) for p in m['team1']]
            add_team(t1, m['difference'])
            t2 = [playername2player(p) for p in m['team2']]
            add_team(t2, -m['difference'])
    # matchdays & matches
    for day, md in matchdays_all.items():
        [day, month, year] = md['date'].split('.')
        date = datetime.date(int(year), int(month), int(day))
        md_qry = MatchDay.query.filter(MatchDay.date == date).first()
        if not md_qry:
            print('adding matchday: %s' % md)
            matchday = MatchDay(date=date)
            for m in md['matches']:
                t1 = playerids2team(
                    [playername2player(p).id for p in m['team1']])
                t2 = playerids2team(
                    [playername2player(p).id for p in m['team2']])
                [goals_t1, goals_t2] = map(int, m['score'].split(':'))
                match = Match(
                    crawling=m['crawling'],
                    team1=t1,
                    team2=t2,
                    goals_team1=goals_t1,
                    goals_team2=goals_t2,
                    points=m['difference'])
                matchday.matches.append(match)
            db.session.add(matchday)
    db.session.commit()
