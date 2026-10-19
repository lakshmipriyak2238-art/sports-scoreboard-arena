/**
 * SPORTS SCOREBOARD ARENA - INTERACTIVE TOURNAMENT BRACKET ENGINE
 * Connects progression pathways, highlights winners on hover, and launches match center.
 */

document.addEventListener('DOMContentLoaded', () => {
  const matchNodes = document.querySelectorAll('.bracket-match-node');
  
  matchNodes.forEach(node => {
    // Click navigates to match center
    node.addEventListener('click', () => {
      const matchId = node.getAttribute('data-match-id');
      if (matchId) {
        window.location.href = `/matches/${matchId}`;
      }
    });

    // Hover effect highlights matching team in other rounds
    const teamSlots = node.querySelectorAll('.bracket-team-slot');
    teamSlots.forEach(slot => {
      const teamId = slot.getAttribute('data-team-id');
      if (!teamId) return;

      slot.addEventListener('mouseenter', () => {
        document.querySelectorAll(`.bracket-team-slot[data-team-id="${teamId}"]`).forEach(el => {
          el.style.boxShadow = '0 0 12px var(--accent-lime)';
          el.style.borderColor = 'var(--accent-lime)';
        });
      });

      slot.addEventListener('mouseleave', () => {
        document.querySelectorAll(`.bracket-team-slot[data-team-id="${teamId}"]`).forEach(el => {
          el.style.boxShadow = '';
          el.style.borderColor = '';
        });
      });
    });
  });
});
