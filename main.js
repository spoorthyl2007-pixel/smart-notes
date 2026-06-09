/* ════════════════════════════════════════════════════════════
   SMART NOTES — main.js
   ════════════════════════════════════════════════════════════ */

/* ── Auto-dismiss flash messages ─────────────────────────────── */
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s ease';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 450);
  }, 4200);
});

/* ── Flash close button ──────────────────────────────────────── */
document.querySelectorAll('.flash-close').forEach(btn => {
  btn.addEventListener('click', () => {
    const flash = btn.closest('.flash');
    if (flash) flash.remove();
  });
});

/* ── Password visibility toggle ─────────────────────────────── */
function togglePassword(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  const isHidden = field.type === 'password';
  field.type = isHidden ? 'text' : 'password';
  // Swap icon on the button that triggered it (optional enhancement)
  const btn = field.parentElement.querySelector('.pw-toggle');
  if (btn) btn.textContent = isHidden ? '🙈' : '👁';
}

/* ── Password strength meter (signup page) ───────────────────── */
(function initStrength() {
  const pw  = document.getElementById('password');
  const bar = document.getElementById('strengthBar');
  if (!pw || !bar) return;

  pw.addEventListener('input', () => {
    const v = pw.value;
    let score = 0;
    if (v.length >= 6)              score++;
    if (v.length >= 10)             score++;
    if (/[A-Z]/.test(v))            score++;
    if (/[0-9]/.test(v))            score++;
    if (/[^A-Za-z0-9]/.test(v))     score++;

    const palette = ['', '#dc2626', '#f97316', '#eab308', '#22c55e', '#16a34a'];
    const widths  = ['0%', '20%', '40%', '60%', '80%', '100%'];
    bar.style.width      = widths[score]  || '0%';
    bar.style.background = palette[score] || 'transparent';
  });
})();

/* ── Confirm delete ──────────────────────────────────────────── */
function confirmDelete() {
  return confirm('Delete this note permanently? This cannot be undone.');
}

/* ── Toggle pin via AJAX ─────────────────────────────────────── */
function togglePin(noteId, btn) {
  fetch(`/notes/${noteId}/pin`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      const card = btn.closest('.note-card');
      if (!card) return;

      if (data.pinned) {
        card.classList.add('pinned');
        btn.title = 'Unpin';
        if (!card.querySelector('.pin-badge')) {
          const badge = document.createElement('span');
          badge.className = 'pin-badge';
          badge.textContent = '📌';
          card.querySelector('.note-card-top').appendChild(badge);
        }
      } else {
        card.classList.remove('pinned');
        btn.title = 'Pin';
        const badge = card.querySelector('.pin-badge');
        if (badge) badge.remove();
      }
    })
    .catch(() => alert('Could not update pin status. Please try again.'));
}

/* ── Textarea character counter ──────────────────────────────── */
(function initCharCounter() {
  const ta   = document.getElementById('content');
  const info = document.getElementById('charInfo');
  if (!ta || !info) return;

  const update = () => {
    const len = ta.value.length;
    info.textContent = `${len.toLocaleString()} character${len !== 1 ? 's' : ''}`;
  };
  ta.addEventListener('input', update);
  update();
})();

/* ── Toolbar helpers (note form) ─────────────────────────────── */
function wrapText(before, after) {
  const ta = document.getElementById('content');
  if (!ta) return;
  const start    = ta.selectionStart;
  const end      = ta.selectionEnd;
  const selected = ta.value.substring(start, end) || 'text';
  ta.value = ta.value.substring(0, start) + before + selected + after + ta.value.substring(end);
  ta.selectionStart = start + before.length;
  ta.selectionEnd   = start + before.length + selected.length;
  ta.focus();
  ta.dispatchEvent(new Event('input'));
}

function insertBullet() {
  const ta = document.getElementById('content');
  if (!ta) return;
  const pos    = ta.selectionStart;
  const before = ta.value.substring(0, pos);
  const after  = ta.value.substring(pos);
  const nl     = (before.length && !before.endsWith('\n')) ? '\n' : '';
  ta.value = before + nl + '• ' + after;
  const cursor = pos + nl.length + 2;
  ta.selectionStart = ta.selectionEnd = cursor;
  ta.focus();
  ta.dispatchEvent(new Event('input'));
}

/* ── Live search autocomplete (dashboard) ─────────────────────── */
(function initAutocomplete() {
  const input = document.getElementById('searchInput');
  const list  = document.getElementById('autocompleteList');
  if (!input || !list) return;

  let timer;

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { closeList(); return; }

    timer = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(items => {
          list.innerHTML = '';
          if (!items.length) { closeList(); return; }
          items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.title;
            li.addEventListener('mousedown', (e) => {
              e.preventDefault(); // prevent blur before click
              window.location.href = `/notes/${item.id}/view`;
            });
            list.appendChild(li);
          });
          list.classList.add('open');
        })
        .catch(() => closeList());
    }, 280);
  });

  input.addEventListener('blur', () => setTimeout(closeList, 200));

  function closeList() {
    list.innerHTML = '';
    list.classList.remove('open');
  }
})();
