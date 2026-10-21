# ⚡ Sports Scoreboard Arena

> A premium, modern sports-technology web application built for competitive vibe-coding with real-time multi-sport live scoring, tournament management, interactive knockout brackets, and organizer consoles.

![Theme](https://img.shields.io/badge/Theme-Dark%20Navy%20%26%20Electric%20Lime-00FF87?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-Flask%20%7C%20SQLite%20%7C%20Vanilla%20JS-38BDF8?style=for-the-badge)
![Sports](https://img.shields.io/badge/Sports-Cricket%20%7C%20Football%20%7C%20Basketball%20%7C%20Badminton%20%7C%20Volleyball-FACC15?style=for-the-badge)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-sports--scoreboard--arena.onrender.com-00FF87?style=for-the-badge&logo=render)](https://sports-scoreboard-arena.onrender.com/)

🔗 **Live Website**: [https://sports-scoreboard-arena.onrender.com/](https://sports-scoreboard-arena.onrender.com/)

---

## 🌟 Key Features

### 1. 🏟️ Multi-Sport Real-Time Scoring
- **Cricket**: Runs, wickets, overs, balls, current run rate (CRR), batsman strike tracking, bowler figures, and interactive ball-by-ball tracker strip (`[ 4, 1, 6, W, 2, 1 ]`).
- **Football (Soccer)**: Goal counters, 1st & 2nd halves, injury time, possession split meter (`58% vs 42%`), shots on target, disciplinary yellow/red cards.
- **Basketball**: Quarter-by-quarter breakdown (`Q1`, `Q2`, `Q3`, `Q4`, `Total`), 1-point free throws, 2-point field goals, 3-pointers, fouls, and timeouts.
- **Badminton**: Best-of-3 sets tracker, real-time rally points, server indicator, and deuce detection.
- **Volleyball**: Best-of-5 sets matrix, current set points, timeouts counter, and rotation point tracking.

### 2. 🏆 Championship Tournament System
- **Formats Supported**:
  - **Round-Robin League**: Full points table with Played, Won, Drawn, Lost, Points, and Net Run Rate / Goal Difference.
  - **Knockout Bracket Tree**: Interactive visual tournament bracket (Quarter-Finals ➔ Semi-Finals ➔ Grand Final ➔ Champion Crown).
- **Squad Registration**: Add teams with short codes (`CSK`, `MCI`, `LAL`), custom accent colors, and captain rosters.
- **Fixture Scheduler**: Schedule matches with custom dates, venues, and rounds.

### 3. 🎮 Referee & Scorer Tactile Terminal
- Touch-friendly, high-contrast tactical buttons with neon feedback.
- Sound effects via Web Audio API (crowd fanfares, referee whistles, score clicks).
- Instant Undo Last Action capability.
- Real-time event log with custom commentary notes.

### 4. 🎨 Design Aesthetics
- **Dark Navy Broadcast Theme**: `#070B14` & `#0D1527` glassmorphism backdrop.
- **Electric Lime Accents**: `#00FF87` with neon glow reflections.
- **Live Match Ticker**: Smooth continuous scrolling marquee at the top of every page.
- **Google Typography**: `Outfit` for UI headings, `Inter` for readability, and `Teko` / `Space Grotesk` for dynamic scoreboard numerals.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure Python 3.10+ is installed on your machine.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python app.py
```
Visit `http://localhost:5000` in your web browser.

---

## 🔑 Demo Organizer Credentials

Use the pre-seeded organizer account to manage tournaments and operate live scorekeeper consoles:
- **Username**: `admin`
- **Password**: `admin123`
*(A 1-click "Fill Demo" button is also provided directly on the login screen for effortless testing)*

---

## 📁 Project Architecture
```
SportsScoreBoardArena/
├── app.py                 # Main Flask application & REST APIs
├── config.py              # Configuration & sport definitions
├── models.py              # SQLite relational schema & helpers
├── seed_data.py           # Pre-seeded realistic tournaments & matches
├── requirements.txt       # Dependencies (Flask, Werkzeug)
├── arena.db               # SQLite database
├── static/
│   ├── css/
│   │   ├── style.css      # Core design system & theme
│   │   ├── scoreboard.css # Sport HUDs, possession, ball strip
│   │   ├── bracket.css    # Interactive tournament tree styling
│   │   └── scorekeeper.css# Tactical scorer terminal layout
│   └── js/
│       ├── main.js        # Global scripts, Web Audio synthesizers, toasts
│       ├── live_match.js  # 3.5s auto-polling & score animations
│       ├── scorekeeper.js # Scorer action dispatching & undo
│       └── bracket.js     # Bracket progression highlighting
└── templates/
    ├── base.html          # Base layout with navbar, ticker, and footer
    ├── index.html         # Live Arena Hub & featured match hero
    ├── tournaments.html   # Tournaments directory & filter
    ├── tournament_detail.html # Tournament Hub (Overview, Fixtures, Standings, Bracket, Squads)
    ├── tournament_create.html # Host a tournament form
    ├── tournament_manage.html # Register teams & schedule fixtures
    ├── match_detail.html  # Immersive full-screen broadcast center
    ├── scorekeeper.html   # Referee live scoring terminal
    ├── leaderboards.html  # Multi-sport leaderboards matrix
    ├── login.html         # Organizer login
    └── register.html      # Organizer sign-up
```
