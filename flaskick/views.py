from flask import render_template

from app import app, db
from models import Match, MatchStatsKickerCool, MatchDay, Player, PlayerStatKickerCool, Team, TeamStatKickerCool

import datetime

def get_players_for_ranking():
    # latest_matchday = datetime.date.today() - datetime.timedelta(days=14)
    players = db.session.query(Player).join(PlayerStatKickerCool, Player.id == PlayerStatKickerCool.player_id).order_by(PlayerStatKickerCool.points.desc()).all()
    # TODO: put in single query
    for p in players:
        s = PlayerStatKickerCool.query.filter(PlayerStatKickerCool.player == p).first()
        p.points = s.points
    # TODO: should put this as a SQL query
    # players = filter(lambda p: p.stat.last_match.matchday.date >= latest_matchday, players)
    return players

@app.route('/')
def index():
    start_idx = 0
    page_size = 10
    matchdays = MatchDay.query.order_by(
        MatchDay.date.desc())[start_idx:start_idx + page_size]
    for md in matchdays:
        for m in md.matches:
            m.points = MatchStatsKickerCool.query.filter(MatchStatsKickerCool.match_id == m.id).first().points
    return render_template(
        'index.html',
        matchdays=filter(lambda md: len(md.matches) > 0, matchdays),
        players=get_players_for_ranking()
    )

@app.route('/players')
def player_list():
    allplayers = Player.query.join(PlayerStatKickerCool, Player.id == PlayerStatKickerCool.player_id).order_by(PlayerStatKickerCool.points.desc()).all()
    pstats = []
    for p in allplayers:
        teams = db.session.query(Team.id).filter(
            db.or_(Team.player1 == p, Team.player2 == p)).subquery()
        won_matches = Match.query.filter(Match.team1_id.in_(teams)).all()
        lost_matches = Match.query.filter(Match.team2_id.in_(teams)).all()
        matches_played = len(won_matches) + len(lost_matches)
        win_quota = float(len(won_matches)) / float(matches_played)
        pstat = {
            'matches_played': matches_played,
            'win_quota': win_quota * 100.,
        }
        pstats.append(pstat)

    return render_template('player-list.html', players=get_players_for_ranking(),
                           allplayers=zip(allplayers, pstats))

@app.route('/teams')
def team_list():
    all_teams = Team.query.join(TeamStatKickerCool, Team.id == TeamStatKickerCool.team_id).order_by(TeamStatKickerCool.points.desc()).all()
    # TODO: also show single player "teams"?
    all_teams = filter(lambda t: t.player2 is not None, all_teams)
    stats = []
    for team in all_teams:
        won_matches = Match.query.filter(Match.team1 == team).all()
        lost_matches = Match.query.filter(Match.team2 == team).all()
        matches_played = len(won_matches) + len(lost_matches)
        win_quota = float(len(won_matches)) / float(matches_played)
        stats.append({
            'matches_played': matches_played,
            'win_quota': win_quota * 100.,
            'points': TeamStatKickerCool.query.filter(TeamStatKickerCool.team_id == team.id).first().points,
        })
    return render_template('team-list.html',  players=get_players_for_ranking(),
                           allteams=zip(all_teams, stats))

@app.route('/player/<int:pid>')
def player(pid):
    player = Player.query.get(pid)
    teams = db.session.query(Team.id).filter(
        db.or_(Team.player1_id == pid, Team.player2_id == pid)).subquery()

    all_teams = Team.query.filter(Team.id.in_(teams)).all()

    # team 1 is always the winning one
    won_matches = Match.query.filter(Match.team1_id.in_(teams)).all()
    lost_matches = Match.query.filter(Match.team2_id.in_(teams)).all()
    matches_played = len(won_matches) + len(lost_matches)

    made_crawl = Match.query.filter(Match.team1_id.in_(teams),
                                    Match.crawling).all()
    did_crawl = Match.query.filter(Match.team2_id.in_(teams),
                                   Match.crawling).all()

    points_sum = player.stat.points
    avg_points = float(points_sum - 1200) / float(matches_played)

    all_matches = Match.query.filter(
        db.or_(Match.team1_id.in_(teams), Match.team2_id.in_(teams))).join(
            MatchDay, Match.matchday).order_by(MatchDay.date).all()
    first_matchday = all_matches[0].matchday.date

    won_ids = [m.id for m in won_matches]
    lost_ids = [m.id for m in lost_matches]
    points_hist = []
    points = 1200
    matchdays = []
    lowest = (points, first_matchday)
    highest = (points, first_matchday)
    for m in all_matches:
        if m.id in won_ids:
            points += m.points
        elif m.id in lost_ids:
            points -= m.points
        else:
            raise RuntimeError('ERROR! you messed up!')
        points_hist.append(points)
        matchdays.append(m.matchday.date.isoformat())

        if points < lowest[0]:
            lowest = (points, m.matchday.date)
        if points > highest[0]:
            highest = (points, m.matchday.date)

    return render_template(
        'player.html',
        player=player,
        # players=get_players_for_ranking(),
        teams=all_teams,
        avg_points=avg_points,
        matches_played=matches_played,
        made_crawl=made_crawl,
        did_crawl=did_crawl,
        first_matchday=first_matchday,
        lowest_points=lowest,
        highest_points=highest,
    )
