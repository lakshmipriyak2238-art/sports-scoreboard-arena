/**
 * SPORTS SCOREBOARD ARENA - TACTICAL SCORER CONSOLE ENGINE
 * Handles instant referee scoring commands, commentary notes, undo, and audio clicks.
 */

class ScorekeeperTerminal {
  constructor(matchId, sport) {
    this.matchId = matchId;
    this.sport = sport;
    this.isSubmitting = false;
  }

  async sendAction(actionType, extraData = {}) {
    if (this.isSubmitting) return;
    this.isSubmitting = true;
    ArenaAudio.click();

    const payload = {
      action: actionType,
      commentary: extraData.commentary || document.getElementById('scorer-custom-note')?.value || '',
      player_name: extraData.player_name || document.getElementById('scorer-player-name')?.value || '',
      team_id: extraData.team_id || null
    };

    try {
      const res = await fetch(`/api/matches/${this.matchId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const result = await res.json();
      if (result.success) {
        if (actionType.includes('GOAL') || actionType.includes('SIX') || actionType.includes('POINT')) {
          ArenaAudio.cheerScore();
        } else if (actionType === 'END_MATCH' || actionType === 'START_MATCH') {
          ArenaAudio.whistle();
        }

        this.updateScorerDisplay(result.match, result.latest_event);
        ArenaToast.show(result.latest_event?.description || 'Action recorded successfully!', 'success');

        // Clear custom note input
        const noteInput = document.getElementById('scorer-custom-note');
        if (noteInput && !extraData.keepNote) noteInput.value = '';
      } else {
        ArenaToast.show(result.error || 'Failed to submit action', 'danger');
      }
    } catch (err) {
      console.error(err);
      ArenaToast.show('Network error recording score action.', 'danger');
    } finally {
      this.isSubmitting = false;
    }
  }

  updateScorerDisplay(match, latestEvent) {
    // 1. Update big scores
    const el1 = document.getElementById('scorer-score-t1');
    const el2 = document.getElementById('scorer-score-t2');
    if (el1) el1.textContent = match.score_team1;
    if (el2) el2.textContent = match.score_team2;

    const elClock = document.getElementById('scorer-clock-text');
    if (elClock) elClock.textContent = `${match.current_period} • ${match.match_clock}`;

    // 2. Prepend event to mini side-feed
    if (latestEvent) {
      const feed = document.getElementById('scorer-history-list');
      if (feed) {
        const item = document.createElement('div');
        item.className = 'history-item-mini';
        item.innerHTML = `
          <div class="history-item-time">${latestEvent.minute_or_over || 'Just now'} • ${latestEvent.event_type}</div>
          <div style="color:#fff; margin-top:2px;">${latestEvent.description}</div>
        `;
        feed.insertBefore(item, feed.firstChild);
      }
    }
  }

  async undoLast() {
    ArenaAudio.click();
    try {
      const res = await fetch(`/api/matches/${this.matchId}/undo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await res.json();
      if (result.success) {
        ArenaToast.show('Last action reverted. Refreshing match...', 'warning');
        setTimeout(() => window.location.reload(), 600);
      } else {
        ArenaToast.show(result.message || 'No actions to undo.', 'warning');
      }
    } catch (err) {
      ArenaToast.show('Error undoing action.', 'danger');
    }
  }
}
