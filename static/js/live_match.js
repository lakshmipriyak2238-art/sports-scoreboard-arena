/**
 * SPORTS SCOREBOARD ARENA - LIVE MATCH REAL-TIME CENTER
 * Polls match state periodically, updates scorecards smoothly, and animates timeline events.
 */

class LiveMatchEngine {
  constructor(matchId, sport, status) {
    this.matchId = matchId;
    this.sport = sport;
    this.status = status;
    this.pollInterval = null;
    this.lastScoreT1 = null;
    this.lastScoreT2 = null;
    this.knownEventIds = new Set();
  }

  start() {
    if (this.status !== 'LIVE') return;
    // Initial known event IDs from DOM
    document.querySelectorAll('[data-event-id]').forEach(el => {
      this.knownEventIds.add(el.getAttribute('data-event-id'));
    });

    // Start polling every 3.5 seconds
    this.pollInterval = setInterval(() => this.poll(), 3500);
  }

  stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  async poll() {
    try {
      const res = await fetch(`/api/matches/${this.matchId}`);
      if (!res.ok) return;
      const data = await res.json();
      this.renderUpdate(data);
    } catch (err) {
      console.warn("Match polling failed:", err);
    }
  }

  renderUpdate(data) {
    const match = data.match;
    const events = data.events || [];
    const state = match.sport_state || {};

    // 1. Check Score Bumps
    const elScore1 = document.getElementById('live-score-team1');
    const elScore2 = document.getElementById('live-score-team2');

    if (elScore1 && this.lastScoreT1 !== null && match.score_team1 !== this.lastScoreT1) {
      elScore1.textContent = match.score_team1;
      elScore1.classList.remove('digit-bump');
      void elScore1.offsetWidth; // trigger reflow
      elScore1.classList.add('digit-bump');
      ArenaAudio.cheerScore();
    } else if (elScore1) {
      elScore1.textContent = match.score_team1;
    }

    if (elScore2 && this.lastScoreT2 !== null && match.score_team2 !== this.lastScoreT2) {
      elScore2.textContent = match.score_team2;
      elScore2.classList.remove('digit-bump');
      void elScore2.offsetWidth;
      elScore2.classList.add('digit-bump');
      ArenaAudio.cheerScore();
    } else if (elScore2) {
      elScore2.textContent = match.score_team2;
    }

    this.lastScoreT1 = match.score_team1;
    this.lastScoreT2 = match.score_team2;

    // 2. Update Clock / Period
    const elClock = document.getElementById('live-match-clock');
    if (elClock) elClock.textContent = match.match_clock;
    const elPeriod = document.getElementById('live-match-period');
    if (elPeriod) elPeriod.textContent = match.current_period;

    // 3. Sport Specific Updates
    if (this.sport === 'cricket') {
      this.updateCricket(state);
    } else if (this.sport === 'football') {
      this.updateFootball(state);
    } else if (this.sport === 'basketball') {
      this.updateBasketball(state);
    } else if (this.sport === 'badminton' || this.sport === 'volleyball') {
      this.updateSets(state);
    }

    // 4. Update Commentary Events Timeline
    this.updateTimeline(events);
  }

  updateCricket(state) {
    const b1 = state.batsman1;
    const b2 = state.batsman2;
    const bowler = state.bowler;
    const balls = state.recent_balls || [];

    if (b1) {
      const elB1Name = document.getElementById('cricket-b1-name');
      const elB1Score = document.getElementById('cricket-b1-score');
      if (elB1Name) elB1Name.innerHTML = `${b1.name} ${b1.on_strike ? '<span class="strike-star">*</span>' : ''}`;
      if (elB1Score) elB1Score.textContent = `${b1.runs} (${b1.balls}b, ${b1.fours}x4, ${b1.sixes}x6)`;
    }

    if (b2) {
      const elB2Name = document.getElementById('cricket-b2-name');
      const elB2Score = document.getElementById('cricket-b2-score');
      if (elB2Name) elB2Name.innerHTML = `${b2.name} ${b2.on_strike ? '<span class="strike-star">*</span>' : ''}`;
      if (elB2Score) elB2Score.textContent = `${b2.runs} (${b2.balls}b, ${b2.fours}x4, ${b2.sixes}x6)`;
    }

    if (bowler) {
      const elBowlerName = document.getElementById('cricket-bowler-name');
      const elBowlerFigs = document.getElementById('cricket-bowler-figs');
      if (elBowlerName) elBowlerName.textContent = bowler.name;
      if (elBowlerFigs) elBowlerFigs.textContent = `${bowler.overs} ov, ${bowler.maidens} m, ${bowler.runs} r, ${bowler.wickets} w`;
    }

    // Balls strip
    const elStrip = document.getElementById('cricket-balls-strip');
    if (elStrip && balls.length > 0) {
      elStrip.innerHTML = balls.map(b => {
        let cls = 'ball-pill';
        if (b === '6') cls += ' six';
        else if (b === '4') cls += ' four';
        else if (b === 'W') cls += ' wicket';
        else if (b === 'Wd' || b === 'Nb') cls += ' extra';
        return `<span class="${cls}">${b}</span>`;
      }).join('');
    }
  }

  updateFootball(state) {
    const p1 = state.possession_team1 || 50;
    const p2 = state.possession_team2 || 50;
    const fill1 = document.getElementById('football-possession-t1');
    const fill2 = document.getElementById('football-possession-t2');
    const lbl1 = document.getElementById('football-possession-lbl1');
    const lbl2 = document.getElementById('football-possession-lbl2');

    if (fill1 && fill2) {
      fill1.style.width = `${p1}%`;
      fill2.style.width = `${p2}%`;
      if (lbl1) lbl1.textContent = `${p1}%`;
      if (lbl2) lbl2.textContent = `${p2}%`;
    }
  }

  updateBasketball(state) {
    ['q1', 'q2', 'q3', 'q4'].forEach(q => {
      const el1 = document.getElementById(`bball-t1-${q}`);
      const el2 = document.getElementById(`bball-t2-${q}`);
      if (el1 && state[`team1_${q}`] !== undefined) el1.textContent = state[`team1_${q}`];
      if (el2 && state[`team2_${q}`] !== undefined) el2.textContent = state[`team2_${q}`];
    });
  }

  updateSets(state) {
    ['set1', 'set2', 'set3', 'set4', 'set5'].forEach(s => {
      const el = document.getElementById(`${s}-score-val`);
      if (el && state[`${s}_score`]) {
        el.textContent = state[`${s}_score`];
      }
    });
  }

  updateTimeline(events) {
    const container = document.getElementById('commentary-timeline-list');
    if (!container) return;

    events.forEach(ev => {
      const strId = String(ev.id);
      if (!this.knownEventIds.has(strId)) {
        this.knownEventIds.add(strId);
        
        // Build new timeline item
        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.setAttribute('data-event-id', strId);

        let icon = '⚡';
        let highlight = '';
        if (ev.event_type.includes('GOAL') || ev.event_type.includes('SIX') || ev.event_type.includes('POINT_3') || ev.event_type.includes('DUNK')) {
          icon = '🔥';
          highlight = 'highlight';
        } else if (ev.event_type.includes('WICKET') || ev.event_type.includes('RED')) {
          icon = '🔴';
        } else if (ev.event_type.includes('YELLOW') || ev.event_type.includes('FOUL')) {
          icon = '🟨';
        }

        item.innerHTML = `
          <div class="timeline-dot ${highlight}">${icon}</div>
          <div class="timeline-content">
            <div class="timeline-meta">
              <span class="timeline-time">${ev.minute_or_over || 'Live'}</span>
              <span class="badge badge-sport">${ev.event_type}</span>
            </div>
            <div class="timeline-desc">${ev.description}</div>
            ${ev.score_snapshot ? `<div style="font-size:0.78rem; color:var(--text-muted); margin-top:4px;">Score: ${ev.score_snapshot}</div>` : ''}
          </div>
        `;

        container.insertBefore(item, container.firstChild);
      }
    });
  }
}
