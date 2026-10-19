import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sports-scoreboard-arena-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'arena.db')
    SPORTS = {
        'cricket': {
            'name': 'Cricket',
            'icon': '🏏',
            'color': '#00FF87',
            'scoring_units': 'Runs / Wickets',
            'periods': ['1st Innings', '2nd Innings', 'Super Over']
        },
        'football': {
            'name': 'Football',
            'icon': '⚽',
            'color': '#38BDF8',
            'scoring_units': 'Goals',
            'periods': ['1st Half', 'Half Time', '2nd Half', 'Extra Time', 'Penalties']
        },
        'basketball': {
            'name': 'Basketball',
            'icon': '🏀',
            'color': '#FB923C',
            'scoring_units': 'Points',
            'periods': ['Q1', 'Q2', 'Q3', 'Q4', 'Overtime']
        },
        'badminton': {
            'name': 'Badminton',
            'icon': '🏸',
            'color': '#A855F7',
            'scoring_units': 'Sets & Points',
            'periods': ['Set 1', 'Set 2', 'Set 3']
        },
        'volleyball': {
            'name': 'Volleyball',
            'icon': '🏐',
            'color': '#F43F5E',
            'scoring_units': 'Sets & Points',
            'periods': ['Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']
        }
    }
