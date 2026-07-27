'use strict';

/* ─── Toast ───────────────────────────────────────────────────── */
const rack = document.getElementById('toast-rack');

function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `
    <svg class="toast-icon" viewBox="0 0 20 20" fill="currentColor">
      ${type === 'success'
        ? '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>'
        : '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>'}
    </svg>
    <span class="toast-msg">${msg}</span>`;
  rack.appendChild(el);
  setTimeout(() => {
    el.classList.add('removing');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, 3500);
}

// Convert server-rendered flash messages to toasts
document.querySelectorAll('.flash').forEach(f => {
  const type = f.classList.contains('flash-error') ? 'error' : 'success';
  toast(f.textContent.trim(), type);
  f.remove();
});


/* ─── Avatar colours ──────────────────────────────────────────── */
const AVATAR_PALETTES = [
  ['#4a6cf7','#7b5ef8'], ['#06b6d4','#3b82f6'], ['#10b981','#06b6d4'],
  ['#f59e0b','#ef4444'], ['#ec4899','#8b5cf6'], ['#6366f1','#3b82f6'],
  ['#14b8a6','#6366f1'], ['#f43f5e','#f59e0b'],
];
document.querySelectorAll('.card-avatar').forEach(el => {
  const letter = el.dataset.letter || 'A';
  const idx = (letter.charCodeAt(0) - 65) % AVATAR_PALETTES.length;
  const [c1, c2] = AVATAR_PALETTES[Math.abs(idx)];
  el.style.background = `linear-gradient(135deg, ${c1}, ${c2})`;
});


/* ─── Dashboard: staggered card animation ─────────────────────── */
document.querySelectorAll('.vault-card').forEach((card, i) => {
  card.style.animationDelay = `${i * 0.05}s`;
});


/* ─── CSRF helper ─────────────────────────────────────────────── */
function csrfToken() {
  const el = document.querySelector('meta[name="csrf-token"]') ||
             document.querySelector('[name=csrf_token]');
  return el ? (el.content || el.value) : '';
}


/* ─── Reveal / hide secret ────────────────────────────────────── */
document.querySelectorAll('[data-reveal]').forEach(btn => {
  btn.addEventListener('click', async () => {
    const id = btn.dataset.reveal;
    const display = document.getElementById(`sec-${id}`);
    const notesEl = document.getElementById(`notes-${id}`);
    const icon    = btn.querySelector('svg');

    if (btn.dataset.state === 'visible') {
      display.textContent = '••••••••••••';
      display.classList.remove('visible');
      btn.dataset.state = '';
      btn.title = 'Reveal';
      if (notesEl) notesEl.style.display = 'none';
      return;
    }

    btn.disabled = true;
    const resp = await fetch(`/vault/${id}/reveal`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
      credentials: 'same-origin',
    });
    btn.disabled = false;

    if (!resp.ok) { toast('Session expired — please log in again.', 'error'); return; }
    const data = await resp.json();

    display.textContent = data.secret;
    display.classList.add('visible');
    btn.dataset.state = 'visible';
    btn.title = 'Hide';

    if (data.notes && notesEl) {
      notesEl.textContent = data.notes;
      notesEl.style.display = 'block';
    }
  });
});


/* ─── Copy to clipboard ───────────────────────────────────────── */
document.querySelectorAll('[data-copy]').forEach(btn => {
  btn.addEventListener('click', async () => {
    const id = btn.dataset.copy;
    const display = document.getElementById(`sec-${id}`);

    let value = display.dataset.state === 'visible' ? display.textContent : null;
    if (!value) {
      const resp = await fetch(`/vault/${id}/reveal`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() },
        credentials: 'same-origin',
      });
      if (!resp.ok) { toast('Session expired.', 'error'); return; }
      value = (await resp.json()).secret;
    }

    await navigator.clipboard.writeText(value);
    btn.classList.add('ripple');
    btn.addEventListener('animationend', () => btn.classList.remove('ripple'), { once: true });
    toast('Copied to clipboard');
  });
});


/* ─── Entry form: toggle secret visibility ────────────────────── */
const toggleBtn   = document.getElementById('toggle-secret');
const secretField = document.getElementById('secret-field');
if (toggleBtn && secretField) {
  toggleBtn.addEventListener('click', () => {
    const hidden = secretField.type === 'password';
    secretField.type = hidden ? 'text' : 'password';
    toggleBtn.textContent = hidden ? 'Hide' : 'Show';
  });
}


/* ─── Password generator ──────────────────────────────────────── */
const genBtn = document.getElementById('gen-pass');
if (genBtn && secretField) {
  genBtn.addEventListener('click', () => {
    const upper  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lower  = 'abcdefghijklmnopqrstuvwxyz';
    const digits = '0123456789';
    const syms   = '!@#$%^&*()-_=+';
    const pool   = upper + lower + digits + syms;
    const arr    = new Uint8Array(20);
    crypto.getRandomValues(arr);
    let pw = '';
    // Guarantee at least one from each category
    pw += upper[arr[0] % upper.length];
    pw += lower[arr[1] % lower.length];
    pw += digits[arr[2] % digits.length];
    pw += syms[arr[3] % syms.length];
    for (let i = 4; i < 20; i++) pw += pool[arr[i] % pool.length];
    // Shuffle
    secretField.value = pw.split('').sort(() => crypto.getRandomValues(new Uint8Array(1))[0] - 128).join('');
    secretField.type  = 'text';
    if (toggleBtn) toggleBtn.textContent = 'Hide';
    meterCheck();
  });
}


/* ─── Password strength meter ─────────────────────────────────── */
const pwField  = document.getElementById('pw-meter-field');
const bar      = document.getElementById('strength-bar');
const barLabel = document.getElementById('strength-label');

function meterCheck() {
  const field = pwField || secretField;
  if (!field || !bar) return;
  const v = field.value;
  let score = 0;
  if (v.length >= 10) score++;
  if (v.length >= 14) score++;
  if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
  if (/\d/.test(v)) score++;
  if (/[^A-Za-z0-9]/.test(v)) score++;

  const levels = [
    { label: '',          color: 'transparent', w: '0%'   },
    { label: 'Very weak', color: '#ef4444',     w: '20%'  },
    { label: 'Weak',      color: '#f97316',     w: '40%'  },
    { label: 'Fair',      color: '#f59e0b',     w: '60%'  },
    { label: 'Good',      color: '#22c55e',     w: '80%'  },
    { label: 'Strong',    color: '#10b981',     w: '100%' },
  ];
  const lvl = levels[Math.min(score, 5)];
  bar.style.width     = lvl.w;
  bar.style.background = lvl.color;
  if (barLabel) { barLabel.textContent = lvl.label; barLabel.style.color = lvl.color; }
}

if (pwField) pwField.addEventListener('input', meterCheck);
if (secretField && bar) secretField.addEventListener('input', meterCheck);


/* ─── Live client-side search (instant filter) ────────────────── */
const searchInput = document.getElementById('live-search');
if (searchInput) {
  const cards = [...document.querySelectorAll('.vault-card')];
  const empty = document.getElementById('empty-state');

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const text = card.dataset.search || '';
      const show = !q || text.includes(q);
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (empty) empty.style.display = visible === 0 ? 'flex' : 'none';
  });
}


/* ─── Favorite toggle ─────────────────────────────────────────── */
document.querySelectorAll('.btn-fav').forEach(btn => {
  btn.addEventListener('click', async () => {
    const entryId = btn.dataset.id;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    const res = await fetch(`/vault/${entryId}/favorite`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
    });
    if (res.ok) {
      const { is_favorite } = await res.json();
      btn.classList.toggle('active', is_favorite);
      btn.title = is_favorite ? 'Remove from favorites' : 'Add to favorites';
      toast(is_favorite ? 'Added to favorites' : 'Removed from favorites');
    }
  });
});


/* ─── Auto-logout on inactivity (15 min) ─────────────────────── */
(function () {
  const TIMEOUT_MS = 15 * 60 * 1000;
  let timer;
  const reset = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const form = document.getElementById('auto-logout-form');
      if (form) { toast('Session expired — logging out…', 'error'); setTimeout(() => form.submit(), 1200); }
    }, TIMEOUT_MS);
  };
  ['mousemove', 'keydown', 'pointerdown', 'touchstart'].forEach(e => document.addEventListener(e, reset, { passive: true }));
  reset();
})();


/* ─── Password generator via server API ───────────────────────── */
const genBtnApi = document.getElementById('gen-pass-api');
if (genBtnApi && secretField) {
  genBtnApi.addEventListener('click', async () => {
    const res = await fetch('/vault/generate-password?length=20');
    if (res.ok) {
      const { password } = await res.json();
      secretField.value = password;
      secretField.type  = 'text';
      if (toggleBtn) toggleBtn.textContent = 'Hide';
      meterCheck();
      toast('Strong password generated');
    }
  });
}
