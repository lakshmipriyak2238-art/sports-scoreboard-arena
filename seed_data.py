import json
from werkzeug.security import generate_password_hash
from models import get_db, init_db

def seed_database():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM tournaments")
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        return

    print("Seeding Sports Scoreboard Arena with realistic demo data...")

    # 1. Organizer User
    password_hash = generate_password_hash("admin123")
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
        ("admin", password_hash, "Chief Arena Director", "organizer")
    )
    admin_id = cursor.lastrowid

    # ---------------------------------------------------------
    # 1. CRICKET TOURNAMENT: Apex Premier T20
    # ---------------------------------------------------------
    cursor.execute('''
    INSERT INTO tournaments (name, sport, format, status, description, venue, start_date, end_date, organizer_id, rules_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Apex Premier T20 Championship",
        "cricket",
        "league",
        "ONGOING",
        "The most electrifying franchise T20 cricket tournament featuring elite international stars and high-octane batting.",
        "National Sports Complex & Oval Arena",
        "2026-10-15",
        "2026-11-05",
        admin_id,
        json.dumps({"overs": 20, "powerplay_overs": 6, "balls_per_over": 6})
    ))
    cricket_tourn_id = cursor.lastrowid

    # Cricket Teams
    cricket_teams_data = [
        ("Mumbai Thunderbolts", "MTB", "#00FF87", "Rohit Verma"),
        ("Bangalore Blasters", "BGB", "#EF4444", "Virat Kohli"),
        ("Chennai Super Kings", "CSK", "#FACC15", "MS Dhoni"),
        ("Kolkata Knights", "KKR", "#A855F7", "Shreyas Iyer"),
        ("Delhi Dynamos", "DLD", "#38BDF8", "Rishabh Pant"),
        ("Punjab Strikers", "PBS", "#F97316", "KL Rahul")
    ]
    cricket_team_ids = []
    for name, short, col, capt in cricket_teams_data:
        cursor.execute(
            "INSERT INTO teams (tournament_id, name, short_name, color, captain) VALUES (?, ?, ?, ?, ?)",
            (cricket_tourn_id, name, short, col, capt)
        )
        t_id = cursor.lastrowid
        cricket_team_ids.append(t_id)

        # Standings entry
        cursor.execute(
            "INSERT INTO standings (tournament_id, team_id, played, won, drawn, lost, points, score_for, score_against, net_run_rate_or_diff) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cricket_tourn_id, t_id, 0, 0, 0, 0, 0, 0, 0, 0.0)
        )

    # Initial standings for cricket
    standings_cricket = [
        (cricket_team_ids[0], 4, 3, 0, 1, 6, 680, 620, +0.852),
        (cricket_team_ids[1], 4, 3, 0, 1, 6, 710, 690, +0.410),
        (cricket_team_ids[2], 4, 2, 0, 2, 4, 640, 630, +0.125),
        (cricket_team_ids[3], 4, 2, 0, 2, 4, 615, 625, -0.180),
        (cricket_team_ids[4], 4, 1, 0, 3, 2, 590, 635, -0.540),
        (cricket_team_ids[5], 4, 1, 0, 3, 2, 580, 650, -0.680),
    ]
    for tid, p, w, d, l, pts, sf, sa, nrr in standings_cricket:
        cursor.execute(
            "UPDATE standings SET played=?, won=?, drawn=?, lost=?, points=?, score_for=?, score_against=?, net_run_rate_or_diff=? WHERE tournament_id=? AND team_id=?",
            (p, w, d, l, pts, sf, sa, nrr, cricket_tourn_id, tid)
        )

    # Live Cricket Match: Mumbai Thunderbolts vs Bangalore Blasters
    cricket_state = {
        "innings": 2,
        "team1_name": "Bangalore Blasters",
        "team2_name": "Mumbai Thunderbolts",
        "target": 192,
        "team1_score": {"runs": 191, "wickets": 6, "overs": 20, "balls": 0},
        "team2_score": {"runs": 178, "wickets": 4, "overs": 18, "balls": 2},
        "current_batting_team_id": cricket_team_ids[0],  # Mumbai
        "batsman1": {"name": "Rohit Verma", "runs": 74, "balls": 42, "fours": 7, "sixes": 4, "on_strike": True},
        "batsman2": {"name": "Aryan Sharma", "runs": 28, "balls": 14, "fours": 2, "sixes": 2, "on_strike": False},
        "bowler": {"name": "Naveen Malik", "overs": 3.2, "maidens": 0, "runs": 32, "wickets": 2},
        "recent_balls": ["4", "1", "6", "W", "2", "1", "4", "6", "1"]
    }

    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, sport_state_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        cricket_tourn_id,
        cricket_team_ids[1], # Team 1: Bangalore
        cricket_team_ids[0], # Team 2: Mumbai
        "cricket",
        "LIVE",
        "Match 14 (League Phase)",
        "2026-10-17 19:30",
        "Oval Arena Stadium, Floodlights",
        "2nd Innings",
        "18.2 Overs",
        191,
        178,
        json.dumps(cricket_state)
    ))
    live_cricket_match_id = cursor.lastrowid

    # Cricket Match Events
    cricket_events = [
        ("18.2 ov", "SIX", cricket_team_ids[0], "Rohit Verma", "MASSIVE HIT! Rohit Verma steps down the track and hammers it deep over long-on for a towering 98m six!", "178/4"),
        ("18.1 ov", "FOUR", cricket_team_ids[0], "Rohit Verma", "GLORIOUS COVER DRIVE! Finding the gap with surgical precision through extra cover for boundary.", "172/4"),
        ("17.6 ov", "SINGLE", cricket_team_ids[0], "Aryan Sharma", "Pushed softly toward deep mid-wicket to retain strike for the next over.", "168/4"),
        ("17.4 ov", "WICKET", cricket_team_ids[1], "Naveen Malik", "WICKET! Clean bowled! Hardik gets yorked right on the off-stump base. Big breakthrough for Bangalore!", "165/4"),
        ("16.5 ov", "FOUR", cricket_team_ids[0], "Aryan Sharma", "Upper cut over backward point! Clever batting using the pace of the bowler.", "158/3"),
        ("15.1 ov", "FIFTY", cricket_team_ids[0], "Rohit Verma", "Captain's knock! Rohit Verma raises his bat for a sensational 50 off 32 balls under immense pressure.", "142/3")
    ]
    for mover, etype, tid, ply, desc, snap in cricket_events:
        cursor.execute(
            "INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (live_cricket_match_id, mover, etype, tid, ply, desc, snap)
        )

    # ---------------------------------------------------------
    # 2. FOOTBALL TOURNAMENT: Champions Arena Cup (Knockout)
    # ---------------------------------------------------------
    cursor.execute('''
    INSERT INTO tournaments (name, sport, format, status, description, venue, start_date, end_date, organizer_id, rules_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Champions Arena Football Cup",
        "football",
        "knockout",
        "ONGOING",
        "High-stakes elite football knockout tournament bringing together the top 8 metropolitan clubs.",
        "Metropolis Grand Stadium",
        "2026-10-12",
        "2026-10-24",
        admin_id,
        json.dumps({"half_duration_mins": 45, "extra_time": True, "penalties": True})
    ))
    football_tourn_id = cursor.lastrowid

    # 8 Teams for Knockout Bracket
    football_teams = [
        ("Madrid Strikers", "MDR", "#00FF87", "Carlos Alvarez"),
        ("London Royals", "LON", "#38BDF8", "Marcus Davies"),
        ("Paris Vanguard", "PAR", "#EC4899", "Kylian Mbappé"),
        ("Munich Titans", "MUN", "#EF4444", "Thomas Muller"),
        ("Milan Knights", "MIL", "#F59E0B", "Rafael Leão"),
        ("Barcelona Blau", "FCB", "#8B5CF6", "Pedri"),
        ("Amsterdam Ajaxians", "AJX", "#10B981", "Steven Berghuis"),
        ("Lisbon Eagles", "SLB", "#F43F5E", "Angel Di Maria")
    ]
    fb_team_ids = []
    for name, short, col, capt in football_teams:
        cursor.execute(
            "INSERT INTO teams (tournament_id, name, short_name, color, captain) VALUES (?, ?, ?, ?, ?)",
            (football_tourn_id, name, short, col, capt)
        )
        fb_team_ids.append(cursor.lastrowid)

    # Football Knockout Tree:
    # Round 1 (Quarter Finals): 4 matches
    # Round 2 (Semi Finals): 2 matches
    # Round 3 (Final): 1 match

    # Semi Final 1 (Winner QF1 vs Winner QF2) -> created as placeholder / upcoming
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, bracket_round, bracket_match_index)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (football_tourn_id, None, None, "football", "UPCOMING", "Semi-Final 1", "2026-10-21 20:00", "Metropolis Grand Arena", "Scheduled", "00:00", 0, 0, 2, 1))
    sf1_id = cursor.lastrowid

    # Semi Final 2 (Winner QF3 vs Winner QF4)
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, bracket_round, bracket_match_index)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (football_tourn_id, fb_team_ids[4], fb_team_ids[6], "football", "UPCOMING", "Semi-Final 2", "2026-10-22 20:00", "Metropolis Grand Arena", "Scheduled", "00:00", 0, 0, 2, 2))
    sf2_id = cursor.lastrowid

    # Final
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, bracket_round, bracket_match_index)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (football_tourn_id, None, None, "football", "UPCOMING", "Grand Championship Final", "2026-10-24 21:00", "Metropolis Grand Arena", "Scheduled", "00:00", 0, 0, 3, 1))
    final_id = cursor.lastrowid

    # Update SF next_match_id
    cursor.execute("UPDATE matches SET next_match_id=? WHERE id IN (?, ?)", (final_id, sf1_id, sf2_id))

    # QF 1: LIVE MATCH (Madrid Strikers vs London Royals) -> Winner to SF1
    football_state = {
        "possession_team1": 58,
        "possession_team2": 42,
        "shots_team1": 11,
        "shots_team2": 7,
        "shots_on_target_t1": 6,
        "shots_on_target_t2": 3,
        "corners_t1": 5,
        "corners_t2": 2,
        "fouls_t1": 8,
        "fouls_t2": 11,
        "cards_yellow_t1": 1,
        "cards_yellow_t2": 2,
        "cards_red_t1": 0,
        "cards_red_t2": 0
    }
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, sport_state_json, bracket_round, bracket_match_index, next_match_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        football_tourn_id,
        fb_team_ids[0], # Madrid Strikers
        fb_team_ids[1], # London Royals
        "football",
        "LIVE",
        "Quarter-Final 1",
        "2026-10-17 21:00",
        "Pitch 1, Metropolis Grand",
        "2nd Half",
        "76'",
        2,
        1,
        json.dumps(football_state),
        1,
        1,
        sf1_id
    ))
    live_football_match_id = cursor.lastrowid

    football_events = [
        ("72'", "GOAL", fb_team_ids[0], "Lucas Silva", "GOAAAL! Sensational thunderbolt strike from 25 yards out into the top right corner! The arena erupts!", "2 - 1"),
        ("64'", "YELLOW_CARD", fb_team_ids[1], "Declan Rice", "Tactical foul breaking a dangerous counter attack in the midfield.", "1 - 1"),
        ("53'", "GOAL", fb_team_ids[1], "Marcus Davies", "EQUALIZER! Davies taps in a low driven cross from close range after a lightning wing break.", "1 - 1"),
        ("38'", "YELLOW_CARD", fb_team_ids[0], "Sergio Ramos", "Aggressive aerial challenge on the edge of the penalty box.", "1 - 0"),
        ("24'", "GOAL", fb_team_ids[0], "Carlos Alvarez", "GOAL! Header off an inch-perfect in-swinging corner kick!", "1 - 0")
    ]
    for mover, etype, tid, ply, desc, snap in football_events:
        cursor.execute(
            "INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (live_football_match_id, mover, etype, tid, ply, desc, snap)
        )

    # QF 2: Completed: Paris Vanguard (3) vs Munich Titans (2) -> Paris to SF1
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, winner_team_id, bracket_round, bracket_match_index, next_match_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (football_tourn_id, fb_team_ids[2], fb_team_ids[3], "football", "COMPLETED", "Quarter-Final 2", "2026-10-16 19:00", "Pitch 2", "Full Time", "90+4'", 3, 2, fb_team_ids[2], 1, 2, sf1_id))

    # QF 3: Completed: Milan Knights (2) vs Barcelona Blau (1) -> Milan to SF2
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, winner_team_id, bracket_round, bracket_match_index, next_match_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (football_tourn_id, fb_team_ids[4], fb_team_ids[5], "football", "COMPLETED", "Quarter-Final 3", "2026-10-16 21:00", "Pitch 1", "Full Time", "90'", 2, 1, fb_team_ids[4], 1, 3, sf2_id))

    # QF 4: Completed: Amsterdam (2) vs Lisbon (0) -> Amsterdam to SF2
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, winner_team_id, bracket_round, bracket_match_index, next_match_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (football_tourn_id, fb_team_ids[6], fb_team_ids[7], "football", "COMPLETED", "Quarter-Final 4", "2026-10-17 18:00", "Pitch 2", "Full Time", "90+2'", 2, 0, fb_team_ids[6], 1, 4, sf2_id))

    # ---------------------------------------------------------
    # 3. BASKETBALL TOURNAMENT: Metro Pro Hoops
    # ---------------------------------------------------------
    cursor.execute('''
    INSERT INTO tournaments (name, sport, format, status, description, venue, start_date, end_date, organizer_id, rules_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Metro Pro Hoops Showdown",
        "basketball",
        "league",
        "ONGOING",
        "Fast-paced court action featuring clutch three-pointers, buzzer beaters, and dynamic fastbreaks.",
        "Skyline Dome Indoor Court",
        "2026-10-10",
        "2026-11-02",
        admin_id,
        json.dumps({"quarter_minutes": 12, "quarters": 4, "foul_limit": 5})
    ))
    basket_tourn_id = cursor.lastrowid

    bball_teams = [
        ("Brooklyn Vipers", "BKN", "#00FF87", "Jason Tatum"),
        ("Chicago Cyclones", "CHI", "#FB923C", "Zach LaVine"),
        ("Golden Gate Warriors", "GSW", "#FACC15", "Stephen Curry"),
        ("Miami Solar", "MIA", "#F43F5E", "Jimmy Butler")
    ]
    bb_team_ids = []
    for name, short, col, capt in bball_teams:
        cursor.execute(
            "INSERT INTO teams (tournament_id, name, short_name, color, captain) VALUES (?, ?, ?, ?, ?)",
            (basket_tourn_id, name, short, col, capt)
        )
        t_id = cursor.lastrowid
        bb_team_ids.append(t_id)
        cursor.execute(
            "INSERT INTO standings (tournament_id, team_id, played, won, drawn, lost, points, score_for, score_against, net_run_rate_or_diff) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (basket_tourn_id, t_id, 3, 2, 0, 1, 4, 310, 295, 15.0)
        )

    # Live Basketball Match: Brooklyn Vipers vs Chicago Cyclones
    bball_state = {
        "quarter": "Q4",
        "team1_q1": 24, "team1_q2": 26, "team1_q3": 22, "team1_q4": 21,
        "team2_q1": 22, "team2_q2": 21, "team2_q3": 25, "team2_q4": 20,
        "fouls_team1": 3, "fouls_team2": 4,
        "timeouts_team1": 2, "timeouts_team2": 1,
        "top_scorer_team1": {"name": "Jason Tatum", "points": 34, "rebounds": 8, "assists": 6},
        "top_scorer_team2": {"name": "Zach LaVine", "points": 29, "rebounds": 4, "assists": 7}
    }
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, sport_state_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        basket_tourn_id,
        bb_team_ids[0],
        bb_team_ids[1],
        "basketball",
        "LIVE",
        "Regular Season Round 5",
        "2026-10-17 20:00",
        "Skyline Dome - Court A",
        "Q4",
        "02:44",
        93,
        88,
        json.dumps(bball_state)
    ))
    live_bball_match_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (live_bball_match_id, "Q4 02:44", "POINT_3", bb_team_ids[0], "Jason Tatum", "STEP-BACK THREE! Pure splash from beyond the arc over a contested hand!", "93 - 88")
    )
    cursor.execute(
        "INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (live_bball_match_id, "Q4 03:10", "DUNK", bb_team_ids[1], "Zach LaVine", "MONSTER SLAM! LaVine glides through the lane and rattles the rim!", "90 - 88")
    )

    # ---------------------------------------------------------
    # 4. BADMINTON TOURNAMENT: National Shuttle Masters
    # ---------------------------------------------------------
    cursor.execute('''
    INSERT INTO tournaments (name, sport, format, status, description, venue, start_date, end_date, organizer_id, rules_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "National Shuttle Masters 2026",
        "badminton",
        "knockout",
        "ONGOING",
        "High-velocity shuttle smashers competing in premier 3-set badminton battles.",
        "Emerald Badminton Pavilion",
        "2026-10-14",
        "2026-10-20",
        admin_id,
        json.dumps({"max_sets": 3, "points_per_set": 21, "deuce_cap": 30})
    ))
    badm_tourn_id = cursor.lastrowid

    badm_teams = [
        ("Vikram Sen", "SEN", "#00FF87", "Vikram Sen"),
        ("Tatsuya Kato", "KAT", "#A855F7", "Tatsuya Kato"),
        ("Anders Antonsen", "ANT", "#38BDF8", "Anders Antonsen"),
        ("Lee Zii Jia", "LZJ", "#FACC15", "Lee Zii Jia")
    ]
    badm_team_ids = []
    for name, short, col, capt in badm_teams:
        cursor.execute(
            "INSERT INTO teams (tournament_id, name, short_name, color, captain) VALUES (?, ?, ?, ?, ?)",
            (badm_tourn_id, name, short, col, capt)
        )
        badm_team_ids.append(cursor.lastrowid)

    # Live Badminton Match: Vikram Sen vs Tatsuya Kato (Decider 3rd set!)
    badminton_state = {
        "current_set": 3,
        "sets_won_team1": 1,
        "sets_won_team2": 1,
        "set1_score": "21 - 18",
        "set2_score": "19 - 21",
        "set3_score": "18 - 16",
        "server_team_id": badm_team_ids[0],
        "is_game_point": False,
        "rally_count": 24
    }
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, sport_state_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        badm_tourn_id,
        badm_team_ids[0],
        badm_team_ids[1],
        "badminton",
        "LIVE",
        "Semi-Final Decider",
        "2026-10-17 19:00",
        "Emerald Court 1",
        "Set 3",
        "Rally 34",
        1,
        1,
        json.dumps(badminton_state)
    ))
    live_badm_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (live_badm_id, "Set 3", "POINT", badm_team_ids[0], "Vikram Sen", "STEEP CROSS-COURT SMASH! 398 km/h smash cleanly hits the tramline!", "18 - 16 (Set 3)")
    )

    # ---------------------------------------------------------
    # 5. VOLLEYBALL TOURNAMENT: Pro Spike League
    # ---------------------------------------------------------
    cursor.execute('''
    INSERT INTO tournaments (name, sport, format, status, description, venue, start_date, end_date, organizer_id, rules_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Pro Spike Super Volleyball Cup",
        "volleyball",
        "league",
        "ONGOING",
        "Thunderous jump serves, impenetrable triple blocks, and athletic dives in 5-set volleyball combat.",
        "Pacific Arena Indoor Hall",
        "2026-10-08",
        "2026-10-28",
        admin_id,
        json.dumps({"max_sets": 5, "set_points": 25, "final_set_points": 15})
    ))
    vb_tourn_id = cursor.lastrowid

    vb_teams = [
        ("Tokyo Hawks", "TKH", "#00FF87", "Yuki Ishikawa"),
        ("Berlin Titans", "BER", "#F43F5E", "Georg Grozer"),
        ("Sampaio Spikers", "SAM", "#FACC15", "Bruno Rezende"),
        ("Trentino Volley", "TRN", "#38BDF8", "Alessandro Michieletto")
    ]
    vb_team_ids = []
    for name, short, col, capt in vb_teams:
        cursor.execute(
            "INSERT INTO teams (tournament_id, name, short_name, color, captain) VALUES (?, ?, ?, ?, ?)",
            (vb_tourn_id, name, short, col, capt)
        )
        t_id = cursor.lastrowid
        vb_team_ids.append(t_id)
        cursor.execute(
            "INSERT INTO standings (tournament_id, team_id, played, won, drawn, lost, points, score_for, score_against, net_run_rate_or_diff) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (vb_tourn_id, t_id, 2, 1, 0, 1, 3, 5, 4, 1.0)
        )

    # Live Volleyball Match: Tokyo Hawks vs Berlin Titans
    vb_state = {
        "current_set": 4,
        "sets_won_team1": 2,
        "sets_won_team2": 1,
        "set1_score": "25 - 22",
        "set2_score": "22 - 25",
        "set3_score": "25 - 20",
        "set4_score": "21 - 19",
        "current_set_pts_t1": 21,
        "current_set_pts_t2": 19,
        "serving_team_id": vb_team_ids[0],
        "timeouts_left_t1": 1,
        "timeouts_left_t2": 0
    }
    cursor.execute('''
    INSERT INTO matches (tournament_id, team1_id, team2_id, sport, status, round_name, scheduled_at, venue, current_period, match_clock, score_team1, score_team2, sport_state_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        vb_tourn_id,
        vb_team_ids[0],
        vb_team_ids[1],
        "volleyball",
        "LIVE",
        "League Matchday 4",
        "2026-10-17 18:30",
        "Pacific Arena Court 2",
        "Set 4",
        "Set 4 (21-19)",
        2,
        1,
        json.dumps(vb_state)
    ))
    live_vb_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO match_events (match_id, minute_or_over, event_type, team_id, player_name, description, score_snapshot) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (live_vb_id, "Set 4", "ACE", vb_team_ids[0], "Yuki Ishikawa", "SERVICE ACE! Wicked jump float drops right on the backline corner!", "Set 4: 21 - 19")
    )

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
