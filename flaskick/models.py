# -*- coding: utf-8 -*-
import datetime
import os

import yaml

from flaskick.app import db
from flaskick.avatars import avatar_filename


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    # stat_id = db.Column(
    #     db.Integer, db.ForeignKey('player_stat.id'), nullable=False)
    # stat = db.relationship('PlayerStat', back_populates='player')
    avatar_url = db.Column(db.String, nullable=True)
    # last_match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    # last_match = db.relationship('Match')

    def __repr__(self):
        return '<Player %s>' % self.name

    @property
    def to_json(self):
        return {
            'type': 'player',
            'id': self.id,
            'attributes': {
                'name': self.name,
                # 'points': self.stat.points
            },
            # 'relationships': {
            #     'statistics': {
            #         'data': {
            #             'id': self.id,
            #             'type': 'statistic'
            #         }
            #     }
            # }
        }


class PlayerStatKickerCool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', uselist=False)
    points = db.Column(db.Integer, nullable=False)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(
        db.Integer, db.ForeignKey('player.id'), nullable=False)
    player1 = db.relationship(
        'Player', uselist=False, primaryjoin='Team.player1_id == Player.id')
    player2_id = db.Column(
        db.Integer, db.ForeignKey('player.id'), nullable=True)
    player2 = db.relationship(
        'Player', uselist=False, primaryjoin='Team.player2_id == Player.id')
    # stat_id = db.Column(
    #     db.Integer, db.ForeignKey('team_stat.id'), nullable=False)
    # stat = db.relationship('TeamStat', back_populates='team')

    def __repr__(self):
        return '<Team %i, Players %s>' % (self.id,
                                          [self.player1, self.player2]
                                          if self.player2 else [self.player1])

    @property
    def to_json(self):
        return {
            'type': 'team',
            'id': self.id,
            'attributes': {
                # 'points': self.stat.points
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
                # 'statistics': {
                #     'data': {
                #         'id': self.id,
                #         'type': 'teamstatistic'
                #     }
                # }
            }
        }


class TeamStatKickerCool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team = db.relationship('Team', uselist=False)
    points = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<TeamStatKickerCool(team_id={}, points={})>'.format(self.team_id, self.points)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team1 = db.relationship(
        'Team', uselist=False, primaryjoin='Match.team1_id == Team.id')
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team2 = db.relationship(
        'Team', uselist=False, primaryjoin='Match.team2_id == Team.id')
    goals_team1 = db.Column(db.Integer, nullable=False, autoincrement=False)
    goals_team2 = db.Column(db.Integer, nullable=False, autoincrement=False)
    # points = db.Column(db.Integer, nullable=False, autoincrement=False)
    crawling = db.Column(db.Boolean, nullable=False)
    matchday_id = db.Column(db.Integer, db.ForeignKey('matchday.id'))
    matchday = db.relationship('MatchDay', backref='matches')
    # imported id from kicker.cool
    # kicker_id = db.Column(db.Integer, nullable=True, autoincrement=False)

    @property
    def to_json(self):
        return {
            'type': 'match',
            'id': self.id,
            'attributes': {
                'goals1': self.goals_team1,
                'goals2': self.goals_team2,
                # 'points': self.points,
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

class MatchStatsKickerCool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    match = db.relationship('Match')
    points = db.Column(db.Integer, nullable=False, autoincrement=False)

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


def _get_or_add_player(pname):
    p1 = Player.query.filter(Player.name == pname).first()
    if not p1:
        plr = Player(name=pname)
        db.session.add(plr)
        plr_stats = PlayerStatKickerCool(player=plr, points=1200)
        db.session.add(plr_stats)
        return plr
    return p1


def _get_team(pnames):
    if len(pnames) == 1:
        p1 = _get_or_add_player(pnames[0])
        t_qry = Team.query.filter(Team.player1 == p1,
                                  Team.player2_id.is_(None)).first()
        return t_qry
    else:
        p1 = _get_or_add_player(pnames[0])
        p2 = _get_or_add_player(pnames[1])
        t_qry = Team.query.filter(
            db.or_(
                db.and_(Team.player1 == p1, Team.player2 == p2),
                db.and_(Team.player1 == p2, Team.player2 == p1))).first()
        return t_qry


def _add_team(pnames):
    if len(pnames) == 1:
        p1 = _get_or_add_player(pnames[0])
        t_qry = Team.query.filter(Team.player1 == p1,
                                  Team.player2_id.is_(None)).first()
        if not t_qry:
            team = Team()
            team.player1 = p1
            db.session.add(team)
            tm_stat = TeamStatKickerCool(team=team, points=1200)
            db.session.add(tm_stat)
    elif len(pnames) == 2:
        p1 = _get_or_add_player(pnames[0])
        p2 = _get_or_add_player(pnames[1])
        t_qry = Team.query.filter(
            db.or_(
                db.and_(Team.player1 == p1, Team.player2 == p2),
                db.and_(Team.player1 == p2, Team.player2 == p1))).first()
        if not t_qry:
            # print('adding team: %s' % team)
            team = Team()
            team.player1 = p1
            team.player2 = p2
            db.session.add(team)
            tm_stat = TeamStatKickerCool(team=team, points=1200)
            db.session.add(tm_stat)


def import_dump(data):
    print('importing data from day %s' % data['date'])
    # make sure match order is right
    data['matches'].sort(key=lambda d: d['match_id'])

    # add new players
    # for name, img_link in data['avatars'].iteritems():
    #     player_qry = Player.query.filter(Player.name == name).first()
    #     # if we already have an avatar for this player, remove it
    #     avatar_fname = avatar_filename(name)
    #     if os.path.isfile(avatar_fname):
    #         os.unlink(avatar_fname)
    #     if not player_qry:
    #         plr = Player(name=name, avatar_url=img_link)
    #         db.session.add(plr)
    #         # plr_stats = PlayerStat(player=plr, points=1200)
    #         # db.session.add(plr_stats)

    # add new teams
    for match in data['matches']:
        _add_team(match['team1'])
        _add_team(match['team2'])

    # add matchday
    # date = data['date']
    date = datetime.datetime.strptime(data['date'], '%d.%m.%Y')
    md_qry = MatchDay.query.filter(MatchDay.date == date).first()
    if not md_qry:
        md_qry = MatchDay(date=date)
        db.session.add(md_qry)

    def _update_team_stat_kc(team, point_difference):
        p1 = team.player1
        p1_stats_kc = PlayerStatKickerCool.query.filter(PlayerStatKickerCool.player == p1).first()
        p1_stats_kc.points += point_difference
        p2 = team.player2
        if p2 is not None:
            p2_stats_kc = PlayerStatKickerCool.query.filter(PlayerStatKickerCool.player == p2).first()
            p2_stats_kc.points += point_difference

        team_stat = TeamStatKickerCool.query.filter(TeamStatKickerCool.team_id == team.id).first()
        if team_stat is None:
            print ("no team stat for %s" % team)
            print (TeamStatKickerCool.query.all())
        team_stat.points += point_difference
        # team.player1.stat.points += difference
        # if team.player2:
        #     team.player2.stat.points += difference

    # add matches
    for match in data['matches']:
        # kicker_id = int(match['match_id'])
        # m_qry = Match.query.filter(Match.kicker_id == kicker_id).first()
        # if m_qry:
        #     print "match %s exists! skipping" % m_qry
        #     continue
        winner = _get_team(match['team1'])
        loser = _get_team(match['team2'])
        difference = match['difference']
        _update_team_stat_kc(winner, difference)
        _update_team_stat_kc(loser, -difference)

        [goals_t1, goals_t2] = map(int, match['score'].split(':'))
        match = Match(
            matchday=md_qry,
            team1=winner,
            team2=loser,
            goals_team1=goals_t1,
            goals_team2=goals_t2,
            crawling=match['crawling'],
            # kicker_id=kicker_id,
            # points=difference
        )
        db.session.add(match)
        matchstat_kc = MatchStatsKickerCool(match=match, points=difference)
        db.session.add(matchstat_kc)

        # def _add_match_to_players(team):
        #     team.player1.stat.last_match = match
        #     if team.player2:
        #         team.player2.stat.last_match = match
        # _add_match_to_players(winner)
        # _add_match_to_players(loser)

    db.session.commit()


def import_matches_from_path(path):
    for fn in sorted(os.listdir(path)):
        with open(os.path.join(path, fn), 'r') as infile:
            day = yaml.load(infile)
            import_dump(day)
            # break
