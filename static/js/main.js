/**
 * SPORTS SCOREBOARD ARENA - GLOBAL CLIENT SCRIPTS
 * Includes Web Audio API synthesizers for stadium sounds, toasts, and UI interactions
 */

// Web Audio API Stadium FX Synthesizer
const ArenaAudio = {
  ctx: null,
  init() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
  },
  whistle() {
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(2400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1800, this.ctx.currentTime + 0.25);
      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.25);
    } catch (e) {
      console.warn("Audio FX not supported or blocked by user gesture:", e);
    }
  },
  cheerScore() {
    this.init();
    if (!this.ctx) return;
    try {
      // Fanfare triad chord
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime + (i * 0.06));
        gain.gain.setValueAtTime(0.08, this.ctx.currentTime + (i * 0.06));
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.6);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(this.ctx.currentTime + (i * 0.06));
        osc.stop(this.ctx.currentTime + 0.6);
      });
    } catch (e) {
      console.warn(e);
    }
  },
  click() {
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.05);
    } catch (e) {}
  }
};

// Global Toast Notifications
const ArenaToast = {
  container: null,
  ensureContainer() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'arena-toast-container';
      this.container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'success') {
    this.ensureContainer();
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
      pointer-events: auto;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      font-size: 0.9rem;
      min-width: 280px;
      margin: 0;
    `;
    toast.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span>${type === 'success' ? '⚡' : '⚠️'}</span>
        <span>${message}</span>
      </div>
    `;
    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 400);
    }, 3500);
  }
};

// Enable audio on first user click anywhere
document.addEventListener('click', () => {
  ArenaAudio.init();
}, { once: true });
