import os
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import get_db, init_db, parse_sport_state
from seed_data import seed_database

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is initialized and seeded on startup
with app.app_context():
    init_db()
    seed_database()

# Database connection per request
@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# Context processor for global template variables
@app.context_processor
def inject_global_data():
    return {
        'sports_config': Config.SPORTS,
        'current_year': datetime.now().year,
        'user': {
            'is_authenticated': 'user_id' in session,
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role', 'spectator')
        }
    }

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this organizer area.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        cursor = g.db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password. (Demo: admin / admin123)', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'organizer')

        if not username or not password or not full_name:
            flash('All fields are required.', 'warning')
            return render_template('register.html')

        cursor = g.db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('register.html')

        pw_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, pw_hash, full_name, role)
        )
        g.db.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ==============================================================================
# ARENA HUB & PUBLIC PAGES
# ==============================================================================

@app.route('/')
def index():
    cursor = g.db.cursor()

    # Get active sports filter if specified
    sport_filter = request.args.get('sport', 'all').lower()

    # Fetch live matches
    query_live = '''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color,
           tr.name as tournament_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN tournaments tr ON m.tournament_id = tr.id
    WHERE m.status = 'LIVE'
    '''
    params_live = []
    if sport_filter != 'all':
        query_live += " AND m.sport = ?"
        params_live.append(sport_filter)
    query_live += " ORDER BY m.id DESC"
    cursor.execute(query_live, params_live)
    live_matches = [dict(row) for row in cursor.fetchall()]
    for m in live_matches:
        m['sport_state'] = parse_sport_state(m)

    # Fetch upcoming matches
    query_upcoming = '''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color,
           tr.name as tournament_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN tournaments tr ON m.tournament_id = tr.id
    WHERE m.status = 'UPCOMING'
    '''
    params_up = []
    if sport_filter != 'all':
        query_upcoming += " AND m.sport = ?"
        params_up.append(sport_filter)
    query_upcoming += " ORDER BY m.scheduled_at ASC LIMIT 6"
    cursor.execute(query_upcoming, params_up)
    upcoming_matches = [dict(row) for row in cursor.fetchall()]

    # Fetch recent completed matches
    query_completed = '''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color,
           tr.name as tournament_name,
           w.name as winner_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN tournaments tr ON m.tournament_id = tr.id
    LEFT JOIN teams w ON m.winner_team_id = w.id
    WHERE m.status = 'COMPLETED'
    ORDER BY m.id DESC LIMIT 4
    '''
    cursor.execute(query_completed)
    completed_matches = [dict(row) for row in cursor.fetchall()]

    # Tournaments list
    cursor.execute("SELECT * FROM tournaments ORDER BY id DESC LIMIT 5")
    tournaments = [dict(row) for row in cursor.fetchall()]

    # Global Arena Counts
    cursor.execute("SELECT COUNT(*) as cnt FROM tournaments")
    tourn_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM teams")
    team_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM matches WHERE status = 'LIVE'")
    live_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM matches WHERE status = 'COMPLETED'")
    finished_count = cursor.fetchone()['cnt']

    # Select marquee featured match (first live match or fallback)
    featured_match = live_matches[0] if live_matches else (upcoming_matches[0] if upcoming_matches else None)

    return render_template(
        'index.html',
        live_matches=live_matches,
        upcoming_matches=upcoming_matches,
        completed_matches=completed_matches,
        tournaments=tournaments,
        featured_match=featured_match,
        active_sport=sport_filter,
        stats={
            'tournaments': tourn_count,
            'teams': team_count,
            'live_matches': live_count,
            'finished_matches': finished_count
        }
    )

# ==============================================================================
# TOURNAMENTS
# ==============================================================================

@app.route('/tournaments')
def tournaments_list():
    cursor = g.db.cursor()
    sport = request.args.get('sport', 'all').lower()
    status = request.args.get('status', 'all').upper()

    query = '''
    SELECT t.*, u.full_name as organizer_name,
           (SELECT COUNT(*) FROM teams WHERE tournament_id = t.id) as team_count,
           (SELECT COUNT(*) FROM matches WHERE tournament_id = t.id) as match_count,
           (SELECT COUNT(*) FROM matches WHERE tournament_id = t.id AND status = 'LIVE') as live_matches_count
    FROM tournaments t
    LEFT JOIN users u ON t.organizer_id = u.id
    WHERE 1=1
    '''
    params = []
    if sport != 'all':
        query += " AND t.sport = ?"
        params.append(sport)
    if status != 'all':
        query += " AND t.status = ?"
        params.append(status)
    query += " ORDER BY t.id DESC"

    cursor.execute(query, params)
    tournaments = [dict(row) for row in cursor.fetchall()]

    return render_template('tournaments.html', tournaments=tournaments, selected_sport=sport, selected_status=status)

@app.route('/tournaments/create', methods=['GET', 'POST'])
@login_required
def tournament_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sport = request.form.get('sport', 'cricket').lower()
        t_format = request.form.get('format', 'league')
        venue = request.form.get('venue', '').strip()
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        description = request.form.get('description', '').strip()

        if not name:
            flash('Tournament name is required.', 'danger')
            return render_template('tournament_create.html')

        cursor = g.db.cursor()
        cursor.execute('''
        INSERT INTO tournaments (name, sport, format, status, description, venue, start_date, end_date, organizer_id, rules_json)
        VALUES (?, ?, ?, 'ONGOING', ?, ?, ?, ?, ?, ?)
        ''', (
            name, sport, t_format, description, venue, start_date, end_date,
            session['user_id'], json.dumps({"created_at": datetime.now().isoformat()})
        ))
        g.db.commit()
        new_id = cursor.lastrowid
        flash(f'Tournament "{name}" created successfully! Now add teams and schedule fixtures.', 'success')
        return redirect(url_for('tournament_manage', id=new_id))

    return render_template('tournament_create.html')

@app.route('/tournaments/<int:id>')
def tournament_detail(id):
    cursor = g.db.cursor()
    cursor.execute('''
    SELECT t.*, u.full_name as organizer_name
    FROM tournaments t
    LEFT JOIN users u ON t.organizer_id = u.id
    WHERE t.id = ?
    ''', (id,))
    tournament = cursor.fetchone()
    if not tournament:
        flash('Tournament not found.', 'danger')
        return redirect(url_for('tournaments_list'))
    tournament = dict(tournament)

    # Teams
    cursor.execute("SELECT * FROM teams WHERE tournament_id = ? ORDER BY id ASC", (id,))
    teams = [dict(row) for row in cursor.fetchall()]

    # Matches
    cursor.execute('''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color,
           w.name as winner_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN teams w ON m.winner_team_id = w.id
    WHERE m.tournament_id = ?
    ORDER BY m.id ASC
    ''', (id,))
    matches = [dict(row) for row in cursor.fetchall()]
    for m in matches:
        m['sport_state'] = parse_sport_state(m)

    # Standings
    cursor.execute('''
    SELECT s.*, tm.name as team_name, tm.short_name as team_short, tm.color as team_color
    FROM standings s
    JOIN teams tm ON s.team_id = tm.id
    WHERE s.tournament_id = ?
    ORDER BY s.points DESC, s.net_run_rate_or_diff DESC, s.won DESC
    ''', (id,))
    standings = [dict(row) for row in cursor.fetchall()]

    # Knockout bracket tree if applicable
    bracket_data = []
    if tournament['format'] == 'knockout' or any(m.get('bracket_round') for m in matches):
        rounds = {}
        for m in matches:
            r_num = m['bracket_round'] or 1
            if r_num not in rounds:
                rounds[r_num] = []
            rounds[r_num].append(m)
        bracket_data = sorted([{'round': r, 'matches': sorted(rounds[r], key=lambda x: x['bracket_match_index'] or 0)} for r in rounds], key=lambda x: x['round'])

    return render_template(
        'tournament_detail.html',
        tournament=tournament,
        teams=teams,
        matches=matches,
        standings=standings,
        bracket_data=bracket_data
    )

@app.route('/tournaments/<int:id>/manage')
@login_required
def tournament_manage(id):
    cursor = g.db.cursor()
    cursor.execute("SELECT * FROM tournaments WHERE id = ?", (id,))
    tournament = cursor.fetchone()
    if not tournament:
        flash('Tournament not found.', 'danger')
        return redirect(url_for('tournaments_list'))

    cursor.execute("SELECT * FROM teams WHERE tournament_id = ? ORDER BY id ASC", (id,))
    teams = [dict(row) for row in cursor.fetchall()]

    cursor.execute('''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short,
           t2.name as team2_name, t2.short_name as team2_short
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    WHERE m.tournament_id = ?
    ORDER BY m.id DESC
    ''', (id,))
    matches = [dict(row) for row in cursor.fetchall()]

    return render_template('tournament_manage.html', tournament=dict(tournament), teams=teams, matches=matches)

@app.route('/tournaments/<int:id>/add-team', methods=['POST'])
@login_required
def add_team(id):
    name = request.form.get('name', '').strip()
    short_name = request.form.get('short_name', '').strip().upper()
    color = request.form.get('color', '#00FF87')
    captain = request.form.get('captain', '').strip()

    if not name or not short_name:
        flash('Team name and short code are required.', 'danger')
        return redirect(url_for('tournament_manage', id=id))

    cursor = g.db.cursor()
    cursor.execute(
        "INSERT INTO teams (tournament_id, name, short_name, color, captain) VALUES (?, ?, ?, ?, ?)",
        (id, name, short_name, color, captain)
    )
    new_team_id = cursor.lastrowid

    # Create standings row
    cursor.execute(
        "INSERT INTO standings (tournament_id, team_id, played, won, drawn, lost, points, score_for, score_against, net_run_rate_or_diff) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0.0)",
        (id, new_team_id)
    )
    g.db.commit()

    flash(f'Team "{name}" registered successfully!', 'success')
    return redirect(url_for('tournament_manage', id=id))

@app.route('/tournaments/<int:id>/schedule-match', methods=['POST'])
@login_required
def schedule_match(id):
    team1_id = request.form.get('team1_id')
    team2_id = request.form.get('team2_id')
    round_name = request.form.get('round_name', 'Fixture').strip()
    venue = request.form.get('venue', 'Arena Court').strip()
    scheduled_at = request.form.get('scheduled_at', datetime.now().strftime('%Y-%m-%d %H:%M'))

    if not team1_id or not team2_id or team1_id == team2_id:
        flash('Please select two distinct teams for the match.', 'danger')
        return redirect(url_for('tournament_manage', id=id))

    cursor = g.db.cursor()
    cursor.execute("SELECT sport FROM tournaments WHERE id = ?", (id,))
    tourn = cursor.fetchone()
    sport = tourn['sport'] if tourn else 'cricket'

    # Initialize empty sport state
    state = {}
    if sport == 'cricket':
        state = {
            "innings": 1,
            "target": 0,
            "team1_score": {"runs": 0, "wickets": 0, "overs": 0, "balls": 0},
            "team2_score": {"runs": 0, "wickets": 0, "overs": 0, "balls": 0},
            "current_batting_team_id": int(team1_id),
            "batsman1": {"name": "Batsman 1", "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "on_strike": True},
            "batsman2": {"name": "Batsman 2", "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "on_strike": False},
            "bowler": {"name": "Opening Bowler", "overs": 0, "maidens": 0, "runs": 0, "wickets": 0},
            "recent_balls": []
        }
    elif sport == 'football':
        state = {
            "possession_team1": 50, "possession_team2": 50,
            "shots_team1": 0, "shots_team2": 0,
            "shots_on_target_t1": 0, "shots_on_target_t2": 0,
            "corners_t1": 0, "corners_t2": 0,
            "fouls_t1": 0, "fouls_t2": 0,
            "cards_yellow_t1": 0, "cards_yellow_t2": 0,
            "cards_red_t1": 0, "cards_red_t2": 0
        }
    elif sport == 'basketball':
        state = {
            "quarter": "Q1",
            "team1_q1": 0, "team1_q2": 0, "team1_q3": 0, "team1_q4": 0,
            "team2_q1": 0, "team2_q2": 0, "team2_q3": 0, "team2_q4": 0,
            "fouls_team1": 0, "fouls_team2": 0,
            "timeouts_team1": 4, "timeouts_team2": 4
        }
    elif sport == 'badminton':
        state = {
            "current_set": 1,
            "sets_won_team1": 0, "sets_won_team2": 0,
            "set1_score": "0 - 0", "set2_score": "0 - 0", "set3_score": "0 - 0",
            "server_team_id": int(team1_id)
        }
    elif sport == 'volleyball':
        state = {
            "current_set": 1,
            "sets_won_team1": 0, "sets_won_team2": 0,
            "set1_score": "0 - 0", "set2_score": "0 - 0", "set3_score": "0 - 0", "set4_score": "0 - 0", "set5_score": "0 - 0",
            "current_set_pts_t1": 0, "current_set_pts_t2": 0,
            "serving_team_id": int(team1_id),
            "timeouts_left_t1": 2, "timeouts_left_t2": 2
        }

    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, sport_state_json)
    VALUES (?, ?, ?, ?, 'UPCOMING', ?, ?, ?, 'Scheduled', '00:00', 0, 0, ?)
    ''', (id, team1_id, team2_id, sport, round_name, scheduled_at, venue, json.dumps(state)))
    g.db.commit()

    flash('Match scheduled successfully!', 'success')
    return redirect(url_for('tournament_manage', id=id))

# ==============================================================================
# LIVE MATCH CENTER & COMMENTARY
# ==============================================================================

@app.route('/matches/<int:id>')
def match_detail(id):
    cursor = g.db.cursor()
    cursor.execute('''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color, t1.captain as team1_captain,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color, t2.captain as team2_captain,
           tr.name as tournament_name, tr.sport as tournament_sport,
           w.name as winner_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN tournaments tr ON m.tournament_id = tr.id
    LEFT JOIN teams w ON m.winner_team_id = w.id
    WHERE m.id = ?
    ''', (id,))
    match = cursor.fetchone()
    if not match:
        flash('Match not found.', 'danger')
        return redirect(url_for('index'))
    match = dict(match)
    match['sport_state'] = parse_sport_state(match)

    # Get events / commentary
    cursor.execute('''
    SELECT e.*, tm.name as team_name, tm.short_name as team_short, tm.color as team_color
    FROM match_events e
    LEFT JOIN teams tm ON e.team_id = tm.id
    WHERE e.match_id = ?
    ORDER BY e.id DESC LIMIT 50
    ''', (id,))
    events = [dict(row) for row in cursor.fetchall()]

    return render_template('match_detail.html', match=match, events=events)

# ==============================================================================
# LIVE SCORER CONSOLE (ORGANIZER / REFEREE TERMINAL)
# ==============================================================================

@app.route('/matches/<int:id>/scorekeeper')
@login_required
def scorekeeper(id):
    cursor = g.db.cursor()
    cursor.execute('''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color,
           tr.name as tournament_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN tournaments tr ON m.tournament_id = tr.id
    WHERE m.id = ?
    ''', (id,))
    match = cursor.fetchone()
    if not match:
        flash('Match not found.', 'danger')
        return redirect(url_for('index'))
    match = dict(match)
    match['sport_state'] = parse_sport_state(match)

    cursor.execute("SELECT * FROM match_events WHERE match_id = ? ORDER BY id DESC LIMIT 20", (id,))
    recent_events = [dict(row) for row in cursor.fetchall()]

    return render_template('scorekeeper.html', match=match, events=recent_events)

# ==============================================================================
# REST API ENDPOINTS FOR REAL-TIME POLLING & UPDATES
# ==============================================================================

@app.route('/api/matches/<int:id>')
def api_match_data(id):
    cursor = g.db.cursor()
    cursor.execute('''
    SELECT m.*, 
           t1.name as team1_name, t1.short_name as team1_short, t1.color as team1_color,
           t2.name as team2_name, t2.short_name as team2_short, t2.color as team2_color,
           w.name as winner_name,
           tr.name as tournament_name
    FROM matches m
    LEFT JOIN teams t1 ON m.team1_id = t1.id
    LEFT JOIN teams t2 ON m.team2_id = t2.id
    LEFT JOIN teams w ON m.winner_team_id = w.id
    LEFT JOIN tournaments tr ON m.tournament_id = tr.id
    WHERE m.id = ?
    ''', (id,))
    match = cursor.fetchone()
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    match_dict = dict(match)
    match_dict['sport_state'] = parse_sport_state(match_dict)

    cursor.execute('''
    SELECT e.*, tm.name as team_name, tm.short_name as team_short
    FROM match_events e
    LEFT JOIN teams tm ON e.team_id = tm.id
    WHERE e.match_id = ?
    ORDER BY e.id DESC LIMIT 30
    ''', (id,))
    events = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        'match': match_dict,
        'events': events
    })

@app.route('/api/matches/<int:id>/action', methods=['POST'])
@login_required
def api_match_action(id):
    """
    Tactical scorer action handler. Supports all 5 sports with rich state transitions.
    """
    data = request.get_json() or {}
    action = data.get('action')
    commentary = data.get('commentary', '').strip()
    player_name = data.get('player_name', '').strip()
    selected_team_id = data.get('team_id')

    cursor = g.db.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (id,))
    match = cursor.fetchone()
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    match = dict(match)
    sport = match['sport']
    state = parse_sport_state(match)

    score_team1 = match['score_team1']
    score_team2 = match['score_team2']
    match_clock = match['match_clock'] or '00:00'
    current_period = match['current_period'] or 'LIVE'
    status = match['status']
    event_type = action
    event_desc = commentary

    # 1. Start Match / Change Status
    if action == 'START_MATCH':
        status = 'LIVE'
        event_type = 'STATUS'
        event_desc = 'Match has officially commenced! The crowd is electric.'

    elif action == 'END_MATCH':
        status = 'COMPLETED'
        event_type = 'FULL_TIME'
        # Determine winner
        winner_id = None
        if score_team1 > score_team2:
            winner_id = match['team1_id']
        elif score_team2 > score_team1:
            winner_id = match['team2_id']
        match['winner_team_id'] = winner_id
        cursor.execute("UPDATE matches SET winner_team_id = ? WHERE id = ?", (winner_id, id))
        event_desc = 'Match concluded! Final whistle / final ball has been delivered.'

        # Update standings if league
        update_tournament_standings(match['tournament_id'])

        # Advance knockout bracket if bracket match
        if match.get('next_match_id') and winner_id:
            advance_bracket_winner(match['id'], match['next_match_id'], winner_id)

    # -------------------------------------------------------------
    # CRICKET SCORER LOGIC
    # -------------------------------------------------------------
    elif sport == 'cricket':
        curr_batting_id = state.get('current_batting_team_id', match['team2_id'])
        is_team2_batting = (curr_batting_id == match['team2_id'])
        score_key = 'team2_score' if is_team2_batting else 'team1_score'
        
        curr_score = state.get(score_key, {"runs": 0, "wickets": 0, "overs": 0, "balls": 0})
        b1 = state.get('batsman1', {"name": "Batsman 1", "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "on_strike": True})
        b2 = state.get('batsman2', {"name": "Batsman 2", "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "on_strike": False})
        active_bat = b1 if b1.get('on_strike') else b2
        bowler = state.get('bowler', {"name": "Bowler", "overs": 0, "maidens": 0, "runs": 0, "wickets": 0})
        recent_balls = state.get('recent_balls', [])

        if action in ['CRICKET_0', 'CRICKET_1', 'CRICKET_2', 'CRICKET_3', 'CRICKET_4', 'CRICKET_6']:
            runs = int(action.split('_')[1])
            curr_score['runs'] += runs
            curr_score['balls'] += 1
            active_bat['runs'] += runs
            active_bat['balls'] += 1
            if runs == 4:
                active_bat['fours'] = active_bat.get('fours', 0) + 1
            elif runs == 6:
                active_bat['sixes'] = active_bat.get('sixes', 0) + 1

            bowler['runs'] = bowler.get('runs', 0) + runs
            ball_label = str(runs) if runs > 0 else "•"
            recent_balls.append(ball_label)

            # Rotate strike on odd runs
            if runs in [1, 3]:
                b1['on_strike'] = not b1.get('on_strike', True)
                b2['on_strike'] = not b2.get('on_strike', False)

            if not event_desc:
                if runs == 6:
                    event_desc = f"SIX! {active_bat['name']} launches it into orbit! Massive maximum!"
                elif runs == 4:
                    event_desc = f"FOUR! Superb timing from {active_bat['name']}, piercing the infield gap!"
                elif runs == 0:
                    event_desc = f"Dot ball. Solid defensive stroke from {active_bat['name']}."
                else:
                    event_desc = f"{runs} run{'s' if runs>1 else ''} taken by {active_bat['name']}."

        elif action == 'CRICKET_WIDE':
            curr_score['runs'] += 1
            bowler['runs'] = bowler.get('runs', 0) + 1
            recent_balls.append('Wd')
            event_desc = event_desc or f"Wide ball called by the umpire! +1 extra to the total."

        elif action == 'CRICKET_NO_BALL':
            curr_score['runs'] += 1
            bowler['runs'] = bowler.get('runs', 0) + 1
            recent_balls.append('Nb')
            event_desc = event_desc or f"No Ball! Free hit upcoming on the next legal delivery."

        elif action == 'CRICKET_WICKET':
            curr_score['wickets'] += 1
            curr_score['balls'] += 1
            active_bat['balls'] += 1
            bowler['wickets'] = bowler.get('wickets', 0) + 1
            recent_balls.append('W')
            event_desc = event_desc or f"OUT! Huge wicket! {active_bat['name']} departs ({active_bat['runs']} off {active_bat['balls']}b)."
            # Reset new batsman
            if b1.get('on_strike'):
                b1['name'] = f"New Batsman {curr_score['wickets'] + 2}"
                b1['runs'] = 0
                b1['balls'] = 0
                b1['fours'] = 0
                b1['sixes'] = 0
            else:
                b2['name'] = f"New Batsman {curr_score['wickets'] + 2}"
                b2['runs'] = 0
                b2['balls'] = 0
                b2['fours'] = 0
                b2['sixes'] = 0

        elif action == 'CRICKET_ROTATE_STRIKE':
            b1['on_strike'] = not b1.get('on_strike', True)
            b2['on_strike'] = not b2.get('on_strike', False)
            event_desc = "Strike rotated between batsmen."

        # Check over completion
        if curr_score.get('balls', 0) >= 6:
            curr_score['overs'] += 1
            curr_score['balls'] = 0
            bowler['overs'] = int(bowler.get('overs', 0)) + 1
            # strike rotates at end of over
            b1['on_strike'] = not b1.get('on_strike', True)
            b2['on_strike'] = not b2.get('on_strike', False)
            recent_balls.append('|')

        # Limit recent balls to last 15
        if len(recent_balls) > 15:
            recent_balls = recent_balls[-15:]

        # Sync scores
        if is_team2_batting:
            score_team2 = curr_score['runs']
        else:
            score_team1 = curr_score['runs']

        state[score_key] = curr_score
        state['batsman1'] = b1
        state['batsman2'] = b2
        state['bowler'] = bowler
        state['recent_balls'] = recent_balls
        match_clock = f"{curr_score['overs']}.{curr_score['balls']} ov"

    # -------------------------------------------------------------
    # FOOTBALL SCORER LOGIC
    # -------------------------------------------------------------
    elif sport == 'football':
        if action == 'FOOTBALL_GOAL_T1':
            score_team1 += 1
            state['shots_team1'] = state.get('shots_team1', 0) + 1
            state['shots_on_target_t1'] = state.get('shots_on_target_t1', 0) + 1
            event_desc = event_desc or f"GOAL! {player_name or 'Striker'} fires it into the back of the net!"
            selected_team_id = match['team1_id']

        elif action == 'FOOTBALL_GOAL_T2':
            score_team2 += 1
            state['shots_team2'] = state.get('shots_team2', 0) + 1
            state['shots_on_target_t2'] = state.get('shots_on_target_t2', 0) + 1
            event_desc = event_desc or f"GOAL! {player_name or 'Striker'} finishes with precision!"
            selected_team_id = match['team2_id']

        elif action == 'FOOTBALL_YELLOW_T1':
            state['cards_yellow_t1'] = state.get('cards_yellow_t1', 0) + 1
            event_desc = event_desc or f"Yellow card shown to {player_name or 'defender'} for a rough challenge."
            selected_team_id = match['team1_id']

        elif action == 'FOOTBALL_YELLOW_T2':
            state['cards_yellow_t2'] = state.get('cards_yellow_t2', 0) + 1
            event_desc = event_desc or f"Yellow card shown to {player_name or 'defender'}."
            selected_team_id = match['team2_id']

        elif action == 'FOOTBALL_RED_T1':
            state['cards_red_t1'] = state.get('cards_red_t1', 0) + 1
            event_desc = event_desc or f"RED CARD! {player_name or 'Player'} is sent off! Down to 10 men!"
            selected_team_id = match['team1_id']

        elif action == 'FOOTBALL_RED_T2':
            state['cards_red_t2'] = state.get('cards_red_t2', 0) + 1
            event_desc = event_desc or f"RED CARD! {player_name or 'Player'} sent off!"
            selected_team_id = match['team2_id']

        elif action == 'FOOTBALL_ADVANCE_HALF':
            periods = ['1st Half', 'Half Time', '2nd Half', 'Extra Time', 'Full Time']
            cur_idx = periods.index(current_period) if current_period in periods else 0
            if cur_idx < len(periods) - 1:
                current_period = periods[cur_idx + 1]
                event_desc = f"Match advanced to {current_period}."

    # -------------------------------------------------------------
    # BASKETBALL SCORER LOGIC
    # -------------------------------------------------------------
    elif sport == 'basketball':
        q_key = f"team1_{state.get('quarter', 'Q1').lower()}"
        q_key2 = f"team2_{state.get('quarter', 'Q1').lower()}"

        if action in ['BBALL_1_T1', 'BBALL_2_T1', 'BBALL_3_T1']:
            pts = int(action.split('_')[1])
            score_team1 += pts
            state[q_key] = state.get(q_key, 0) + pts
            event_desc = event_desc or f"+{pts} points scored by {player_name or 'Team 1'}!"
            selected_team_id = match['team1_id']

        elif action in ['BBALL_1_T2', 'BBALL_2_T2', 'BBALL_3_T2']:
            pts = int(action.split('_')[1])
            score_team2 += pts
            state[q_key2] = state.get(q_key2, 0) + pts
            event_desc = event_desc or f"+{pts} points scored by {player_name or 'Team 2'}!"
            selected_team_id = match['team2_id']

        elif action == 'BBALL_FOUL_T1':
            state['fouls_team1'] = state.get('fouls_team1', 0) + 1
            event_desc = event_desc or "Personal foul called on Team 1."

        elif action == 'BBALL_FOUL_T2':
            state['fouls_team2'] = state.get('fouls_team2', 0) + 1
            event_desc = event_desc or "Personal foul called on Team 2."

        elif action == 'BBALL_ADVANCE_Q':
            quarters = ['Q1', 'Q2', 'Q3', 'Q4', 'OT']
            curr_q = state.get('quarter', 'Q1')
            q_idx = quarters.index(curr_q) if curr_q in quarters else 0
            if q_idx < len(quarters) - 1:
                state['quarter'] = quarters[q_idx + 1]
                current_period = state['quarter']
                event_desc = f"End of quarter. Entering {current_period}."

    # -------------------------------------------------------------
    # BADMINTON SCORER LOGIC
    # -------------------------------------------------------------
    elif sport == 'badminton':
        cur_set = state.get('current_set', 1)
        set_key = f"set{cur_set}_score"
        s1, s2 = 0, 0
        if state.get(set_key):
            try:
                parts = state[set_key].split('-')
                s1, s2 = int(parts[0].strip()), int(parts[1].strip())
            except Exception:
                s1, s2 = 0, 0

        if action == 'BADM_POINT_T1':
            s1 += 1
            event_desc = event_desc or f"Point Team 1 ({s1} - {s2})"
            selected_team_id = match['team1_id']
        elif action == 'BADM_POINT_T2':
            s2 += 1
            event_desc = event_desc or f"Point Team 2 ({s1} - {s2})"
            selected_team_id = match['team2_id']

        state[set_key] = f"{s1} - {s2}"

        # Check set win (21 pts, min 2 lead, max 30)
        if (s1 >= 21 or s2 >= 21) and abs(s1 - s2) >= 2 or (s1 == 30 or s2 == 30):
            if s1 > s2:
                state['sets_won_team1'] = state.get('sets_won_team1', 0) + 1
                score_team1 = state['sets_won_team1']
                event_desc = f"SET WON by Team 1! ({s1} - {s2})"
            else:
                state['sets_won_team2'] = state.get('sets_won_team2', 0) + 1
                score_team2 = state['sets_won_team2']
                event_desc = f"SET WON by Team 2! ({s1} - {s2})"

            if cur_set < 3 and state.get('sets_won_team1', 0) < 2 and state.get('sets_won_team2', 0) < 2:
                state['current_set'] = cur_set + 1
                current_period = f"Set {cur_set + 1}"

    # -------------------------------------------------------------
    # VOLLEYBALL SCORER LOGIC
    # -------------------------------------------------------------
    elif sport == 'volleyball':
        cur_set = state.get('current_set', 1)
        s1 = state.get('current_set_pts_t1', 0)
        s2 = state.get('current_set_pts_t2', 0)

        if action == 'VB_POINT_T1':
            s1 += 1
            state['current_set_pts_t1'] = s1
            event_desc = event_desc or f"Point Team 1 ({s1} - {s2})"
            selected_team_id = match['team1_id']
        elif action == 'VB_POINT_T2':
            s2 += 1
            state['current_set_pts_t2'] = s2
            event_desc = event_desc or f"Point Team 2 ({s1} - {s2})"
            selected_team_id = match['team2_id']

        state[f"set{cur_set}_score"] = f"{s1} - {s2}"

        # Check set win (25 pts or 15 in 5th set, lead of 2)
        target_pts = 15 if cur_set == 5 else 25
        if (s1 >= target_pts or s2 >= target_pts) and abs(s1 - s2) >= 2:
            if s1 > s2:
                state['sets_won_team1'] = state.get('sets_won_team1', 0) + 1
                score_team1 = state['sets_won_team1']
            else:
                state['sets_won_team2'] = state.get('sets_won_team2', 0) + 1
                score_team2 = state['sets_won_team2']

            state['current_set_pts_t1'] = 0
            state['current_set_pts_t2'] = 0
            event_desc = f"Set {cur_set} won ({s1} - {s2})!"

            if cur_set < 5 and state.get('sets_won_team1', 0) < 3 and state.get('sets_won_team2', 0) < 3:
                state['current_set'] = cur_set + 1
                current_period = f"Set {cur_set + 1}"

    # General commentary note
    elif action == 'CUSTOM_COMMENTARY':
        event_type = 'COMMENTARY'
        event_desc = commentary or "Match commentary update."

    # Update match in DB
    cursor.execute('''
    UPDATE matches
    SET score_team1 = ?, score_team2 = ?, match_clock = ?, current_period = ?, status = ?, sport_state_json = ?
    WHERE id = ?
    ''', (score_team1, score_team2, match_clock, current_period, status, json.dumps(state), id))

    # Snapshot string
    score_snapshot = f"{score_team1} - {score_team2}"
    if sport == 'cricket':
        batting_score = state.get('team2_score', {}) if state.get('current_batting_team_id') == match['team2_id'] else state.get('team1_score', {})
        score_snapshot = f"{batting_score.get('runs', 0)}/{batting_score.get('wickets', 0)} ({match_clock})"

    # Log event
    cursor.execute('''
    INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (id, match_clock, event_type, selected_team_id, player_name, event_desc, score_snapshot))

    g.db.commit()

    return jsonify({
        'success': True,
        'match': {
            'id': id,
            'score_team1': score_team1,
            'score_team2': score_team2,
            'match_clock': match_clock,
            'current_period': current_period,
            'status': status,
            'sport_state': state
        },
        'latest_event': {
            'minute_or_over': match_clock,
            'event_type': event_type,
            'description': event_desc,
            'score_snapshot': score_snapshot
        }
    })

@app.route('/api/matches/<int:id>/undo', methods=['POST'])
@login_required
def api_match_undo(id):
    cursor = g.db.cursor()
    cursor.execute("SELECT id FROM match_events WHERE match_id = ? ORDER BY id DESC LIMIT 1", (id,))
    last_event = cursor.fetchone()
    if last_event:
        cursor.execute("DELETE FROM match_events WHERE id = ?", (last_event['id'],))
        g.db.commit()
        return jsonify({'success': True, 'message': 'Last event reverted.'})
    return jsonify({'success': False, 'message': 'No events to undo.'})

# Helper functions
def update_tournament_standings(tournament_id):
    """Recalculate league standings after match completion."""
    cursor = g.db.cursor()
    cursor.execute("SELECT * FROM matches WHERE tournament_id = ? AND status = 'COMPLETED'", (tournament_id,))
    completed = cursor.fetchall()
    
    cursor.execute("SELECT id FROM teams WHERE tournament_id = ?", (tournament_id,))
    teams = cursor.fetchall()
    
    stats = {t['id']: {'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'points': 0, 'sf': 0, 'sa': 0} for t in teams}

    for m in completed:
        t1, t2 = m['team1_id'], m['team2_id']
        s1, s2 = m['score_team1'], m['score_team2']
        if t1 in stats:
            stats[t1]['played'] += 1
            stats[t1]['sf'] += s1
            stats[t1]['sa'] += s2
        if t2 in stats:
            stats[t2]['played'] += 1
            stats[t2]['sf'] += s2
            stats[t2]['sa'] += s1

        if s1 > s2:
            if t1 in stats:
                stats[t1]['won'] += 1
                stats[t1]['points'] += 3
            if t2 in stats:
                stats[t2]['lost'] += 1
        elif s2 > s1:
            if t2 in stats:
                stats[t2]['won'] += 1
                stats[t2]['points'] += 3
            if t1 in stats:
                stats[t1]['lost'] += 1
        else:
            if t1 in stats:
                stats[t1]['drawn'] += 1
                stats[t1]['points'] += 1
            if t2 in stats:
                stats[t2]['drawn'] += 1
                stats[t2]['points'] += 1

    for tid, st in stats.items():
        diff = round(float(st['sf'] - st['sa']), 2)
        cursor.execute('''
        INSERT INTO standings (tournament_id, team_id, played, won, drawn, lost, points, score_for, score_against, net_run_rate_or_diff)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(tournament_id, team_id) DO UPDATE SET
            played=excluded.played, won=excluded.won, drawn=excluded.drawn, lost=excluded.lost,
            points=excluded.points, score_for=excluded.score_for, score_against=excluded.score_against,
            net_run_rate_or_diff=excluded.net_run_rate_or_diff
        ''', (tournament_id, tid, st['played'], st['won'], st['drawn'], st['lost'], st['points'], st['sf'], st['sa'], diff))
    
    g.db.commit()

def advance_bracket_winner(match_id, next_match_id, winner_id):
    """Automatically seed the winner into the next bracket node."""
    cursor = g.db.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (next_match_id,))
    next_match = cursor.fetchone()
    if next_match:
        if not next_match['team1_id']:
            cursor.execute("UPDATE matches SET team1_id = ? WHERE id = ?", (winner_id, next_match_id))
        elif not next_match['team2_id']:
            cursor.execute("UPDATE matches SET team2_id = ? WHERE id = ?", (winner_id, next_match_id))
        g.db.commit()

# ==============================================================================
# LEADERBOARDS & STATS
# ==============================================================================

@app.route('/leaderboards')
def leaderboards():
    cursor = g.db.cursor()
    sport = request.args.get('sport', 'all').lower()

    query = '''
    SELECT s.*, tm.name as team_name, tm.short_name as team_short, tm.color as team_color,
           tr.name as tournament_name, tr.sport as tournament_sport
    FROM standings s
    JOIN teams tm ON s.team_id = tm.id
    JOIN tournaments tr ON s.tournament_id = tr.id
    WHERE 1=1
    '''
    params = []
    if sport != 'all':
        query += " AND tr.sport = ?"
        params.append(sport)
    query += " ORDER BY s.points DESC, s.net_run_rate_or_diff DESC, s.won DESC LIMIT 25"

    cursor.execute(query, params)
    standings = [dict(row) for row in cursor.fetchall()]

    return render_template('leaderboards.html', standings=standings, selected_sport=sport)

if __name__ == '__main__':
    # Run dev server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
