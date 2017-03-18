import math

import dateutil.parser
from flask import request

from flask_restful import Api, Resource, reqparse
from flaskick.app import app, db
from flaskick.models import Match, MatchDay, Player, PlayerStat, Team, TeamStat

api = Api(app)


class MatchDaysResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int)
        parser.add_argument('per_page', type=int)
        args = parser.parse_args()
        print('url: %s' % request.url)
        page_number = args.get('page')
        page_size = args.get('per_page')
        if not page_number:
            page_number = 1
        if not page_size:
            page_size = 7
        start_idx = (page_number - 1) * page_size
        matchdays = MatchDay.query.order_by(
            MatchDay.date.desc())[start_idx:start_idx + page_size]
        total_pages = math.ceil(MatchDay.query.count() / page_size)
        print('total: %s' % total_pages)
        res = {
            'data': [md.to_json for md in matchdays],
            'meta': {
                'total_pages': total_pages,
            },
            'links': {
                'self':
                request.url,
                'first':
                '{baseurl}?page[number]={pn}&page[size]={ps}'.format(
                    baseurl=request.base_url, pn=1, ps=page_size),
                'last':
                '{baseurl}?page[number]={pn}&page[size]={ps}'.format(
                    baseurl=request.base_url, pn=total_pages - 1,
                    ps=page_size),
                'prev':
                '{baseurl}?page[number]={pn}&page[size]={ps}'.format(
                    baseurl=request.base_url,
                    pn=(page_number - 1),
                    ps=page_size),
                'next':
                '{baseurl}?page[number]={pn}&page[size]={ps}'.format(
                    baseurl=request.base_url,
                    pn=(page_number + 1),
                    ps=page_size)
            }
        }
        return res


class MatchDayResource(Resource):
    def get(self, id):
        md = MatchDay.query.get(id)
        return {'data': md.to_json}


class MatchDayByDateResource(Resource):
    def get(self, date_iso):
        date = dateutil.parser.parse(date_iso)
        md = MatchDay.query.filter(MatchDay.date == date.date()).first()
        return {'data': md.to_json}


class MatchesResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('filter[id]')
        args = parser.parse_args()
        filter_ids = []
        if args.get('filter[id]'):
            filter_ids = list(
                map(lambda s: int(s),
                    filter(lambda x: x, args.get('filter[id]').split(','))))
        if len(filter_ids) == 0:
            matches = Match.query.all()
        else:
            matches = Match.query.filter(Match.id.in_(filter_ids)).all()
        print('returning %i matches' % len(matches))
        return {'data': [m.to_json for m in matches]}


class MatchResource(Resource):
    def get(self, id):
        match = Match.query.get(id)
        return {'data': match.to_json}


class TeamsResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('filter[id]')
        args = parser.parse_args()
        filter_ids = []
        if args.get('filter[id]'):
            filter_ids = list(
                map(lambda s: int(s),
                    filter(lambda x: x, args.get('filter[id]').split(','))))
        if len(filter_ids) == 0:
            teams = Team.query.join(
                TeamStat, Team.stat).order_by(TeamStat.points.desc()).all()
        else:
            teams = Team.query.join(TeamStat, Team.stat).filter(
                Team.id.in_(filter_ids)).order_by(TeamStat.points.desc()).all()
        print('returning %i teams' % len(teams))
        return {'data': [t.to_json for t in teams]}


class TeamResource(Resource):
    def get(self, id):
        team = Team.query.get(id)
        return {'data': team.to_json}


class PlayerResource(Resource):
    def get(self, id):
        player = Player.query.get(id)
        return {'data': player.to_json}


class PlayerByNameResource(Resource):
    def get(self, name):
        player = Player.query.filter(Player.name == name).first()
        return {'data': player.to_json}


class PlayersResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('filter[id]')
        args = parser.parse_args()
        filter_ids = []
        if args.get('filter[id]'):
            filter_ids = list(
                map(lambda s: int(s),
                    filter(lambda x: x, args.get('filter[id]').split(','))))
        if len(filter_ids) == 0:
            players = Player.query.join(PlayerStat, Player.stat).order_by(
                PlayerStat.points.desc()).all()
        else:
            players = Player.query.join(PlayerStat, Player.stat).filter(
                Player.id.in_(filter_ids)).order_by(
                    PlayerStat.points.desc()).all()
        print('returning %i players' % len(players))
        return {'data': [p.to_json for p in players]}


class PlayerStatisticsResource(Resource):
    def get(self, id):
        # FIXME: keep this data in db table
        player = Player.query.get(id)
        teams = db.session.query(Team.id).filter(
            db.or_(Team.player1.id == id, Team.player2.id == id)).subquery()
        # team 1 is always the winning one
        won_matches = Match.query.filter(Match.team1.in_(teams)).all()
        lost_matches = Match.query.filter(Match.team2.in_(teams)).all()
        matches_played = len(won_matches) + len(lost_matches)

        made_crawl = Match.query.filter(
            Match.team1.in_(teams), Match.crawling).all()
        did_crawl = Match.query.filter(Match.team2.in_(teams),
                                       Match.crawling).all()

        points_sum = player.stat.points
        avg_points = float(points_sum - 1200) / float(matches_played)

        all_matches = Match.query.filter(
            db.or_(Match.team1.in_(teams), Match.team2.in_(teams))).join(
                MatchDay, Match.matchday).order_by(MatchDay.date).all()

        won_ids = [m.id for m in won_matches]
        lost_ids = [m.id for m in lost_matches]
        points_hist = []
        points = 1200
        matchdays = []
        for m in all_matches:
            if m.id in won_ids:
                points += m.points
            elif m.id in lost_ids:
                points -= m.points
            else:
                raise RuntimeError('ERROR! you messed up!')
            points_hist.append(points)
            matchdays.append(m.matchday.date.isoformat())

        res = {
            'data': {
                'attributes': {
                    'name': player.name,
                    'matchesplayed': len(won_matches) + len(lost_matches),
                    'matcheswon': len(won_matches),
                    'matcheslost': len(lost_matches),
                    'madecrawl': len(made_crawl),
                    'didcrawl': len(did_crawl),
                    'points': points_sum,
                    'avgpoints': avg_points,
                    'pointshist': points_hist,  #[-100:],
                    'matchdays': matchdays  #[-100:]
                },
                'type': 'statistic',
                'id': id
            }
        }
        return res


class TeamStatisticsResource(Resource):
    def get(self, id):
        team = Team.query.get(id)

        won_matches = Match.query.filter(Match.team1 == team.id).all()
        lost_matches = Match.query.filter(Match.team2 == team.id).all()

        made_crawl = Match.query.filter(Match.team1 == team.id,
                                        Match.crawling).all()
        did_crawl = Match.query.filter(Match.team2 == team.id,
                                       Match.crawling).all()

        all_matches = Match.query.filter(
            db.or_(Match.team1 == team.id, Match.team2 == team.id)).join(
                MatchDay, Match.matchday).order_by(MatchDay.date).all()

        won_ids = [m.id for m in won_matches]
        lost_ids = [m.id for m in lost_matches]
        points_hist = []
        points = 1200
        matchdays = []
        for m in all_matches:
            if m.id in won_ids:
                points += m.points
            elif m.id in lost_ids:
                points -= m.points
            else:
                raise RuntimeError('ERROR! you messed up!')
            points_hist.append(points)
            matchdays.append(m.matchday.date.isoformat())

        res = {
            'data': {
                'attributes': {
                    'matchesplayed': len(won_matches) + len(lost_matches),
                    'matcheswon': len(won_matches),
                    'matcheslost': len(lost_matches),
                    'madecrawl': len(made_crawl),
                    'didcrawl': len(did_crawl),
                    'pointshist': points_hist,
                    'matchdays': matchdays
                },
                'type': 'teamstatistic',
                'id': id
            }
        }
        return res


api.add_resource(MatchDaysResource, '/api/matchdays', methods=['GET'])
api.add_resource(MatchDayResource, '/api/matchdays/<int:id>', methods=['GET'])
api.add_resource(
    MatchDayByDateResource,
    '/api/matchday/by-date/<string:date_iso>',
    methods=['GET'])
api.add_resource(MatchesResource, '/api/matches', methods=['GET'])
api.add_resource(MatchResource, '/api/matches/<int:id>', methods=['GET'])
api.add_resource(TeamsResource, '/api/teams', methods=['GET'])
api.add_resource(TeamResource, '/api/teams/<int:id>', methods=['GET'])

api.add_resource(PlayersResource, '/api/players', methods=['GET'])
api.add_resource(PlayerResource, '/api/players/<int:id>', methods=['GET'])
api.add_resource(
    PlayerByNameResource,
    '/api/players/by-name/<string:name>',
    methods=['GET'])

api.add_resource(
    PlayerStatisticsResource, '/api/statistics/<int:id>', methods=['GET'])
api.add_resource(
    TeamStatisticsResource, '/api/teamstatistics/<int:id>', methods=['GET'])
