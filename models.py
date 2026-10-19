import sqlite3
import json
import os
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users / Organizers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'organizer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tournaments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sport TEXT NOT NULL,
        format TEXT NOT NULL DEFAULT 'league',
        status TEXT NOT NULL DEFAULT 'UPCOMING',
        description TEXT,
        venue TEXT,
        start_date TEXT,
        end_date TEXT,
        organizer_id INTEGER,
        rules_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')

    # Teams
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER,
        name TEXT NOT NULL,
        short_name TEXT NOT NULL,
        color TEXT DEFAULT '#00FF87',
        logo_url TEXT,
        captain TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
    )
    ''')

    # Players
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER,
        name TEXT NOT NULL,
        jersey_number INTEGER,
        role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
    )
    ''')

    # Matches
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER,
        team1_id INTEGER,
        team2_id INTEGER,
        sport TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'UPCOMING',
        round_name TEXT,
        scheduled_at TEXT,
        venue TEXT,
        current_period TEXT,
        match_clock TEXT,
        winner_team_id INTEGER,
        score_team1 INTEGER DEFAULT 0,
        score_team2 INTEGER DEFAULT 0,
        sport_state_json TEXT,
        bracket_round INTEGER DEFAULT 0,
        bracket_match_index INTEGER DEFAULT 0,
        next_match_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
        FOREIGN KEY (team1_id) REFERENCES teams(id) ON DELETE SET NULL,
        FOREIGN KEY (team2_id) REFERENCES teams(id) ON DELETE SET NULL,
        FOREIGN KEY (winner_team_id) REFERENCES teams(id) ON DELETE SET NULL
    )
    ''')

    # Match Events (Timeline, commentary & scoring logs)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER NOT NULL,
        minute_or_over TEXT,
        event_type TEXT NOT NULL,
        team_id INTEGER,
        player_name TEXT,
        description TEXT NOT NULL,
        score_snapshot TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
        FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
    )
    ''')

    # Standings / Points Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS standings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        played INTEGER DEFAULT 0,
        won INTEGER DEFAULT 0,
        drawn INTEGER DEFAULT 0,
        lost INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0,
        score_for REAL DEFAULT 0,
        score_against REAL DEFAULT 0,
        net_run_rate_or_diff REAL DEFAULT 0.0,
        FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
        FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
        UNIQUE(tournament_id, team_id)
    )
    ''')

    conn.commit()
    conn.close()

def parse_sport_state(match_row):
    """Safely parse the sport state JSON for a match."""
    state_str = match_row['sport_state_json'] if match_row and 'sport_state_json' in match_row.keys() else None
    if not state_str:
        return {}
    try:
        return json.loads(state_str)
    except Exception:
        return {}
