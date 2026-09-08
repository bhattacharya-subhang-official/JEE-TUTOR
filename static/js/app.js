/* ═══════════ JEE Tutor — frontend app ═══════════ */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const state = {
    chats: [], chatId: null, mode: 'numerical', attachments: [],
    streaming: false, abort: null,
  };

  const MODES = {
    numerical: { icon: '🧮', label: 'Numerical', verb: 'Solve',
      desc: 'Step-by-step solutions — SymPy / NumPy / physics & chemistry engines verify every step',
      ph: 'Ask a JEE Advanced problem… paste or attach the question' },
    diagram: { icon: '📐', label: 'Diagram', verb: 'Draw',
      desc: 'Complex labelled SVG diagrams + interactive 3D scenes (rotate & zoom)',
      ph: 'Describe the diagram — e.g. "all forces on a block on a 30° incline with friction"' },
    animation: { icon: '🎬', label: 'Animation', verb: 'Animate',
      desc: 'Animated 2D/3D visualizations (SVG / Canvas / WebGL) that run in the chat',
      ph: 'Describe the animation — e.g. "SHM of a spring–mass system with energy bars"' },
    video: { icon: '🎥', label: 'Manim Video', verb: 'Create video',
      desc: 'Full explainer video rendered by Manim (MP4, downloadable)',
      ph: 'Describe the video — e.g. "explain projectile motion with equations and a graph"' },
  };

  const SUGGESTIONS = {
    numerical: [
      'A projectile is fired at 20 m/s, 30° above horizontal. Find range, max height and time of flight.',
      'Solve x³ − 6x² + 11x − 6 = 0, then plot the cubic.',
      'Find the image distance & magnification for a concave mirror f = −15 cm, u = −25 cm.',
      'pH of 0.05 M H₂SO₄ solution? Verify with the engines.',
      'A body of mass 2 kg on a 37° incline (µ = 0.5): acceleration down the plane?',
    ],
    diagram: [
      'Labelled free-body diagram: block on inclined plane with friction and all force vectors.',
      '3D scene of sp³-hybridised methane with bond angles labelled.',
      'Ray diagram: concave mirror forming a real, inverted image (u = 2f).',
      '3D: electric field lines around a dipole.',
    ],
    animation: [
      'Animate SHM of a spring–mass system with KE/PE energy bars.',
      '3D animation: electron orbiting in a uniform magnetic field (helix).',
      'Animate formation of a standing wave from two opposite waves.',
      'Animate Snell\u2019s law: light bending air→glass with angles shown.',
    ],
    video: [
      'Manim video: projectile motion with trajectory, equations and a worked example.',
      'Manim video: visual intuition for the derivative of sin(x).',
      'Manim video: Bohr model energy levels and transitions with the Rydberg formula.',
      'Manim video: solving a quadratic by completing the square.',
    ],
  };

  /* ═══════════ boot ═══════════ */
  async function init() {
    bindTopbar();
    bindComposer();
    buildModeMenu();
    buildKeypad();
    bindSettings();
    await Promise.all([refreshConfig(), refreshChats()]);
    renderWelcome();
  }

  /* ═══════════ config / status ═══════════ */
  async function refreshConfig() {
    try {
      const cfg = await (await fetch('/api/config')).json();
      const ks = $('keyStatus');
      if (cfg.has_key) { ks.textContent = `● API key set (${cfg.key_masked})`; ks.className = 'key-status ok'; }
      else { ks.textContent = '● No API key — open Settings'; ks.className = 'key-status bad'; }
      $('engineStatus').textContent =
        `Manim ${cfg.manim ? '✓' : '✗'} · LaTeX ${cfg.latex ? '✓' : '✗'} · ${cfg.model.replace('gemini-', 'Gemini ')}`;
      state.cfg = cfg;
    } catch (e) { /* server offline */ }
  }

  /* ═══════════ sidebar ═══════════ */
  async function refreshChats() {
    try { state.chats = await (await fetch('/api/chats')).json(); }
    catch (e) { state.chats = []; }
    renderChatList();
  }

  function renderChatList() {
    const nav = $('chatListNav');
    nav.innerHTML = '';
    state.chats.forEach((c) => {
      const item = document.createElement('div');
      item.className = 'chat-item' + (c.id === state.chatId ? ' active' : '');
      item.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span class="ci-title">${MD.escHtml(c.title)}</span>`;
      const del = document.createElement('button');
      del.className = 'ci-del'; del.title = 'Delete chat'; del.textContent = '🗑';
      del.onclick = async (e) => {
        e.stopPropagation();
        await fetch(`/api/chats/${c.id}`, { method: 'DELETE' });
        if (state.chatId === c.id) { state.chatId = null; renderWelcome(); }
        refreshChats(); toast('Chat deleted');
      };
      item.appendChild(del);
      item.onclick = () => openChat(c.id);
      nav.appendChild(item);
    });
  }

  function setSidebar(open) {
    const app = $('app');
    if (window.innerWidth <= 900) app.classList.toggle('sb-open', open);
    else app.classList.toggle('sb-collapsed', !open);
  }

  async function openChat(id) {
    if (state.streaming) return;
    try {
      const chat = await (await fetch(`/api/chats/${id}`)).json();
      state.chatId = id;
      const col = $('chatColumn');
      col.innerHTML = '';
      (chat.messages || []).forEach((m) => {
        if (m.role === 'user') addUserMessage(m.text, m.attachments || []);
        else addAiMessage(null, { finalText: m.text, media: m.media || [], mode: m.mode || 'numerical' });
      });
      renderChatList();
      setSidebar(false);
      scrollBottom(true);
    } catch (e) { toast('Could not load chat', true); }
  }

  function newChat() {
    if (state.streaming) return;
    state.chatId = null;
    renderChatList();
    renderWelcome();
    setSidebar(false);
  }

  /* ═══════════ welcome ═══════════ */
  function renderWelcome() {
    const col = $('chatColumn');
    col.innerHTML = `
      <div class="welcome">
        <div class="wl-logo">Σ</div>
        <h1>JEE <b>Advanced</b> Solver</h1>
        <p>Numericals solved with live computation engines · labelled diagrams &amp; 3D scenes ·
           animations · Manim videos. Pick a capability and fire away.</p>
        <div class="cap-grid">${Object.entries(MODES).map(([k, m]) => `
          <div class="cap-card" data-mode="${k}">
            <div class="cc-icon">${m.icon}</div><h4>${m.label}</h4><p>${m.desc}</p>
          </div>`).join('')}
        </div>
        <div class="sugg-row" id="suggRow"></div>
      </div>`;
    col.querySelectorAll('.cap-card').forEach((el) => {
      el.onclick = () => { setMode(el.dataset.mode); $('input').focus(); };
    });
    renderSuggestions();
  }

  function renderSuggestions() {
    const row = $('suggRow');
    if (!row) return;
    row.innerHTML = '';
    (SUGGESTIONS[state.mode] || []).forEach((s) => {
      const el = document.createElement('button');
      el.className = 'sugg'; el.textContent = s.length > 76 ? s.slice(0, 76) + '…' : s;
      el.title = s; el.onclick = () => { $('input').value = s; autoGrow($('input')); $('input').focus(); };
      row.appendChild(el);
    });
  }

  /* ═══════════ topbar ═══════════ */
  function bindTopbar() {
    $('menuBtn').onclick = () => setSidebar(true);
    $('collapseBtn').onclick = () => setSidebar(false);
    $('sbScrim').onclick = () => setSidebar(false);
    $('newChatBtn').onclick = newChat;
    $('settingsBtn').onclick = openSettings;
  }

  /* ═══════════ composer ═══════════ */
  function autoGrow(ta) {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 180) + 'px';
  }

  function bindComposer() {
    const input = $('input');
    input.addEventListener('input', () => autoGrow(input));
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    $('sendBtn').onclick = sendMessage;
    $('stopBtn').onclick = () => { if (state.abort) state.abort.abort(); };
    $('attachBtn').onclick = () => $('fileInput').click();
    $('fileInput').addEventListener('change', onFiles);
    $('modeBtn').onclick = (e) => { e.stopPropagation(); togglePop('modeMenu', $('modeBtn')); };
    $('keypadBtn').onclick = (e) => { e.stopPropagation(); togglePop('keypadPop', $('keypadBtn')); };
    document.addEventListener('click', closePops);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { closePops(); $('settingsModal').hidden = true; }
    });
  }

  async function onFiles(e) {
    const files = [...(e.target.files || [])];
    e.target.value = '';
    for (const f of files) {
      if (f.size > 20 * 1024 * 1024) { toast(`${f.name}: too large (max 20 MB)`, true); continue; }
      toast(`Uploading ${f.name}…`);
      try {
        const fd = new FormData();
        fd.append('file', f);
        const meta = await (await fetch('/api/upload', { method: 'POST', body: fd })).json();
        if (meta.id) { state.attachments.push(meta); renderChips(); }
      } catch (err) { toast(`Upload failed: ${f.name}`, true); }
    }
  }

  function renderChips() {
    const row = $('chipsRow');
    row.innerHTML = '';
    state.attachments.forEach((a, i) => {
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.innerHTML = `${a.kind === 'image' && a.url ? `<img src="${a.url}">` : '📄'}
        <span>${MD.escHtml(a.name.length > 28 ? a.name.slice(0, 26) + '…' : a.name)}</span>`;
      const x = document.createElement('button');
      x.className = 'x'; x.textContent = '✕';
      x.onclick = () => { state.attachments.splice(i, 1); renderChips(); };
      chip.appendChild(x);
      row.appendChild(chip);
    });
  }

  /* ═══════════ popovers ═══════════ */
  function togglePop(id, anchor) {
    const pop = $(id);
    const wasOpen = pop.classList.contains('open');
    closePops();
    if (wasOpen) return;
    pop.classList.add('open');
    const r = anchor.getBoundingClientRect();
    pop.style.visibility = 'hidden';
    pop.style.left = '0px'; pop.style.top = '0px';
    requestAnimationFrame(() => {
      const pw = pop.offsetWidth, ph = pop.offsetHeight;
      let x = Math.min(r.left, window.innerWidth - pw - 12);
      let y = r.top - ph - 10;
      if (y < 8) y = r.bottom + 10;
      pop.style.left = Math.max(8, x) + 'px';
      pop.style.top = y + 'px';
      pop.style.visibility = 'visible';
    });
  }
  function closePops(e) {
    document.querySelectorAll('.menu-pop.open').forEach((p) => {
      if (e && p.contains(e.target)) return;
      p.classList.remove('open');
    });
  }

  function buildModeMenu() {
    const menu = $('modeMenu');
    menu.innerHTML = '';
    Object.entries(MODES).forEach(([k, m]) => {
      const item = document.createElement('div');
      item.className = 'menu-item' + (k === state.mode ? ' selected' : '');
      item.dataset.mode = k;
      item.innerHTML = `<div class="mi-icon">${m.icon}</div><div>
        <div class="mi-label">${m.label}</div><div class="mi-desc">${m.desc}</div></div>`;
      item.onclick = () => { setMode(k); closePops(); };
      menu.appendChild(item);
    });
  }

  function setMode(mode) {
    state.mode = mode;
    const m = MODES[mode];
    $('modeBtnLabel').textContent = m.label;
    $('modeBadge').textContent = `${m.icon} ${m.label}`;
    $('input').placeholder = m.ph;
    document.querySelectorAll('#modeMenu .menu-item').forEach((el) =>
      el.classList.toggle('selected', el.dataset.mode === mode));
    renderSuggestions();
  }

  const KP = [
    ['Basic', [
      ['a²', '^2'], ['aⁿ', '^{ }'], ['√', '\\sqrt{ }'], ['ⁿ√', '\\sqrt[n]{ }'],
      ['x⁄y', '\\frac{ }{ }'], ['|x|', '|x|'], ['( )', '()'], ['×', '\\times '],
      ['÷', '\\div '], ['±', '\\pm '], ['°', '°'], ['∞', '\\infty '], ['≈', '\\approx '],
      ['⋅', '\\cdot '],
    ]],
    ['Calculus', [
      ['∫', '\\int '], ['∫ₐᵇ', '\\int_{a}^{b} '], ['∮', '\\oint '], ['∂', '\\partial '],
      ['∇', '\\nabla '], ['Σ', '\\sum_{i=1}^{n} '], ['∏', '\\prod '], ['lim', '\\lim_{x\\to 0} '],
      ['d/dx', '\\frac{d}{dx} '], ['∂/∂x', '\\frac{\\partial}{\\partial x} '], ['∆', '\\Delta '],
    ]],
    ['Greek', [
      ['α', '\\alpha '], ['β', '\\beta '], ['γ', '\\gamma '], ['θ', '\\theta '],
      ['φ', '\\phi '], ['ψ', '\\psi '], ['ω', '\\omega '], ['λ', '\\lambda '],
      ['µ', '\\mu '], ['π', '\\pi '], ['ρ', '\\rho '], ['σ', '\\sigma '],
      ['τ', '\\tau '], ['ε', '\\epsilon '], ['Ω', '\\Omega '], ['Φ', '\\Phi '],
    ]],
    ['Sets & logic', [
      ['→', '\\rightarrow '], ['⇒', '\\Rightarrow '], ['∈', '\\in '], ['∉', '\\notin '],
      ['⊂', '\\subset '], ['∪', '\\cup '], ['∩', '\\cap '], ['∴', '\\therefore '],
      ['≤', '\\leq '], ['≥', '\\geq '], ['≠', '\\neq '], ['∝', '\\propto '],
    ]],
    ['Vectors & chem', [
      ['v⃗', '\\vec{v} '], ['â', '\\hat{a} '], ['a·b', '\\cdot '], ['a×b', '\\times '],
      ['⇌', '\\rightleftharpoons '], ['↑', '↑'], ['↓', '↓'], ['ħ', '\\hbar '],
      ['Ω', '\\Omega '], ['Å', '\\text{Å} '], ['½', '\\frac{1}{2} '], ['µ₀', '\\mu_0 '],
    ]],
  ];

  function buildKeypad() {
    const kp = $('keypadPop');
    kp.innerHTML = '<div class="kp-grid">' + KP.map(([name, keys]) =>
      `<div class="kp-sep">${name}</div>` + keys.map(([lbl, ins]) =>
        `<button class="kp-btn" data-ins="${MD.escHtml(ins)}">${lbl}</button>`).join('')
    ).join('') + '</div>';
    kp.querySelectorAll('.kp-btn').forEach((b) => {
      b.onclick = () => { insertAtCursor($('input'), b.dataset.ins); };
    });
  }

  function insertAtCursor(ta, text) {
    const s = ta.selectionStart || 0, e = ta.selectionEnd || 0;
    ta.value = ta.value.slice(0, s) + text + ta.value.slice(e);
    const pos = s + text.length;
    ta.focus();
    ta.setSelectionRange(pos, pos);
    autoGrow(ta);
  }

  /* ═══════════ send / SSE ═══════════ */
  async function sendMessage() {
    const input = $('input');
    const text = input.value.trim();
    if (!text && !state.attachments.length) return;
    if (state.streaming) return;

    const atts = state.attachments.slice();
    addUserMessage(text, atts.map((a) => ({ name: a.name, kind: a.kind, url: a.url })));
    input.value = ''; autoGrow(input);
    state.attachments = []; renderChips();

    const body = {
      chat_id: state.chatId, mode: state.mode, message: text,
      attachment_ids: atts.map((a) => a.id),
    };
    const m = addAiMessage(null, { streaming: true, mode: state.mode });
    state.streaming = true;
    state.abort = new AbortController();
    setStreamingUI(true);
    scrollBottom(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: state.abort.signal,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf('\n\n')) >= 0) {
          const chunk = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          const line = chunk.split('\n').find((l) => l.startsWith('data: '));
          if (!line) continue;
          let ev; try { ev = JSON.parse(line.slice(6)); } catch (e) { continue; }
          handleEvent(ev, m);
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') finishError(m, e.message || String(e));
      else if (!m.done) finishError(m, '_Generation stopped._');
    } finally {
      state.streaming = false;
      setStreamingUI(false);
      finalize(m);
      if (!state.chatId) refreshChats();
      else refreshChats();
    }
  }

  function setStreamingUI(on) {
    $('sendBtn').style.display = on ? 'none' : 'inline-flex';
    $('stopBtn').style.display = on ? 'inline-flex' : 'none';
  }

  function handleEvent(ev, m) {
    switch (ev.type) {
      case 'chat':
        state.chatId = ev.chat_id;
        refreshChats();
        break;
      case 'status':
        m.statusText.textContent = ev.msg;
        break;
      case 'tool': {
        const chip = document.createElement('span');
        chip.className = 'tool-chip';
        const d = document.createElement('details');
        const sm = document.createElement('summary');
        sm.innerHTML = `<span class="${ev.ok ? 'ok' : 'bad'}">${ev.ok ? '✓' : '✗'}</span> ${MD.escHtml(ev.name)}`;
        const pre = document.createElement('pre');
        let pretty = '';
        try { pretty = JSON.stringify(JSON.parse(ev.result), null, 1); } catch (e) { pretty = ev.result; }
        pre.textContent = JSON.stringify(ev.args, null, 1) + '\n⟶ ' + pretty;
        d.appendChild(sm); d.appendChild(pre); chip.appendChild(d);
        m.toolsRow.appendChild(chip);
        scrollBottom();
        break;
      }
      case 'delta':
        m.text += ev.text;
        scheduleRender(m);
        scrollBottom();
        break;
      case 'media':
        m.media.push(ev.media);
        m.body.appendChild(renderMedia(ev.media));
        scrollBottom();
        break;
      case 'code': {
        const det = document.createElement('details');
        det.className = 'code-block';
        det.innerHTML = `<summary>🐍 Manim source code</summary><pre><code>${MD.escHtml(ev.code)}</code></pre>`;
        m.body.appendChild(det);
        break;
      }
      case 'final':
        m.finalText = ev.text || m.text;
        m.media = (ev.media && ev.media.length) ? ev.media : m.media;
        break;
      case 'error':
        finishError(m, ev.message);
        break;
      case 'done':
        m.done = true;
        break;
    }
  }

  function scheduleRender(m) {
    if (m.renderTimer) return;
    m.renderTimer = setTimeout(() => {
      m.renderTimer = null;
      m.md.innerHTML = MD.renderMarkdown(m.text);
      MD.typesetMath(m.md);
    }, 350);
  }

  /* ═══════════ message DOM ═══════════ */
  function addUserMessage(text, atts) {
    const wrap = document.createElement('div');
    wrap.className = 'msg msg-user';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text || '(attachment)';
    if (atts && atts.length) {
      const thumbs = document.createElement('div');
      thumbs.className = 'att-thumbs';
      atts.forEach((a) => {
        if (a.kind === 'image' && a.url) {
          const img = document.createElement('img');
          img.src = a.url; img.alt = a.name;
          thumbs.appendChild(img);
        } else {
          const c = document.createElement('span');
          c.className = 'att-chip'; c.textContent = '📄 ' + (a.name || 'file');
          thumbs.appendChild(c);
        }
      });
      bubble.appendChild(thumbs);
    }
    wrap.appendChild(bubble);
    $('chatColumn').appendChild(wrap);
    scrollBottom();
    return wrap;
  }

  function addAiMessage(_, opts) {
    opts = opts || {};
    const mode = opts.mode || state.mode;
    const m = { text: '', finalText: opts.finalText || null, media: opts.media || [],
                done: false, errored: false, timer: null };
    const wrap = document.createElement('div');
    wrap.className = 'msg msg-ai';
    wrap.innerHTML = `
      <div class="ai-avatar">Σ</div>
      <div class="ai-body">
        <div class="ai-meta">
          <span class="ai-name">JEE Tutor</span>
          <span class="ai-mode-chip">${MODES[mode].icon} ${MODES[mode].label}</span>
        </div>
        <div class="ai-card">
          <div class="status-line" style="display:none"><span class="spin"></span><span class="status-text"></span></div>
          <div class="tools-row tool-chips"></div>
          <div class="md md-body"></div>
          <div class="media-list"></div>
          <div class="msg-actions">
            <button class="act-btn act-copy">⧉ Copy</button>
            <button class="act-btn act-dl">⬇ Download media</button>
          </div>
        </div>
      </div>`;
    $('chatColumn').appendChild(wrap);
    m.el = wrap;
    m.card = wrap.querySelector('.ai-card');
    m.statusLine = wrap.querySelector('.status-line');
    m.statusText = wrap.querySelector('.status-text');
    m.toolsRow = wrap.querySelector('.tools-row');
    m.md = wrap.querySelector('.md-body');
    m.mediaList = wrap.querySelector('.media-list');
    m.actions = wrap.querySelector('.msg-actions');

    wrap.querySelector('.act-copy').onclick = () => {
      copyText(m.finalText != null ? m.finalText : m.text);
    };
    wrap.querySelector('.act-dl').onclick = () => {
      let n = 0;
      (m.media || []).forEach((med) => { if (med.url) { downloadURL(med.url); n++; } });
      if (!n) toast('No downloadable media on this message');
    };

    if (opts.streaming) {
      m.statusLine.style.display = 'flex';
      m.statusText.textContent = 'Connecting…';
    } else {
      m.done = true;
      m.md.innerHTML = MD.renderMarkdown(m.finalText || '');
      MD.typesetMath(m.md);
      (m.media || []).forEach((med) => m.mediaList.appendChild(renderMedia(med)));
      m.actions.style.opacity = 1;
    }
    return m;
  }

  function finalize(m) {
    if (m.renderTimer) { clearTimeout(m.renderTimer); m.renderTimer = null; }
    if (m.errored && !m.text) { return; }
    const finalText = m.finalText != null ? m.finalText : m.text;
    if (finalText) {
      m.md.innerHTML = MD.renderMarkdown(finalText);
      MD.typesetMath(m.md);
    }
    if (!m.mediaList.children.length && m.media.length) {
      m.media.forEach((med) => m.mediaList.appendChild(renderMedia(med)));
    }
    m.statusLine.style.display = 'none';
    m.actions.style.opacity = 1;
  }

  function finishError(m, msg) {
    m.errored = true;
    m.statusLine.style.display = 'none';
    const box = document.createElement('div');
    box.className = 'md';
    box.innerHTML = `<blockquote style="border-color:var(--red);background:rgba(248,113,113,.08)">
      <strong>⚠️ ${MD.escHtml(String(msg)).slice(0, 800)}</strong></blockquote>`;
    m.md.appendChild(box);
    m.actions.style.opacity = 1;
    toast('Something went wrong — see the message', true);
  }

  /* ═══════════ media rendering ═══════════ */
  function downloadName(url, title) {
    const ext = (url.match(/\.\w{2,4}(?=\?|$)/) || ['.bin'])[0];
    const base = (title || 'media').replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '_').slice(0, 48) || 'media';
    return base + ext;
  }

  function renderMedia(med) {
    const card = document.createElement('div');
    card.className = 'media-card';
    const head = document.createElement('div');
    head.className = 'media-head';
    const icons = { svg: '📐', scene: '🧊', anim: '🎬', video: '🎥', image_svg: '📊', image_png: '📊' };
    head.innerHTML = `<span>${icons[med.kind] || '🖼'}</span>
      <span class="m-title">${MD.escHtml(med.title || 'Media')}</span>`;
    if (med.url) {
      const dl = document.createElement('button');
      dl.className = 'act-btn'; dl.textContent = '⬇ Download';
      dl.onclick = () => downloadURL(med.url, downloadName(med.url, med.title));
      head.appendChild(dl);
    }
    card.appendChild(head);
    const body = document.createElement('div');
    body.className = 'media-body';
    card.appendChild(body);

    switch (med.kind) {
      case 'svg': {
        if (med.svg) {
          body.innerHTML = med.svg;
          const s = body.querySelector('svg');
          if (s) s.classList.add('diagram');
        } else if (med.url) {
          body.innerHTML = `<img src="${med.url}" alt="${MD.escHtml(med.title || '')}">`;
        }
        break;
      }
      case 'scene': {
        const holder = document.createElement('div');
        holder.className = 'scene3d';
        body.appendChild(holder);
        requestAnimationFrame(() => {
          try { window.buildScene(holder, med.scene); }
          catch (e) { holder.textContent = '3D render failed: ' + e.message; }
        });
        break;
      }
      case 'anim': {
        const ifr = document.createElement('iframe');
        ifr.src = med.url;
        ifr.setAttribute('sandbox', 'allow-scripts allow-pointer-lock');
        ifr.loading = 'lazy';
        body.appendChild(ifr);
        break;
      }
      case 'video': {
        const v = document.createElement('video');
        v.src = med.url; v.controls = true; v.preload = 'metadata';
        body.appendChild(v);
        break;
      }
      default: {
        if (med.url) body.innerHTML = `<img src="${med.url}" alt="">`;
      }
    }
    return card;
  }

  /* ═══════════ clipboard / downloads / toast ═══════════ */
  async function copyText(t) {
    if (!t) { toast('Nothing to copy', true); return; }
    try {
      await navigator.clipboard.writeText(t);
      toast('Copied to clipboard ✓');
    } catch (e) {
      const ta = document.createElement('textarea');
      ta.value = t; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); ta.remove();
      toast('Copied ✓');
    }
  }

  function downloadURL(url, name) {
    const a = document.createElement('a');
    a.href = url;
    a.download = name || '';
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  let toastTimer = null;
  function toast(msg, isErr) {
    const t = $('toast');
    t.textContent = msg;
    t.className = 'toast' + (isErr ? ' err' : '');
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 2600);
  }

  /* ═══════════ settings ═══════════ */
  async function openSettings() {
    try {
      const cfg = await (await fetch('/api/config')).json();
      if (cfg.pin_locked) { $('settingsModal').hidden = true; return; }
      $('providerSelect').value = cfg.provider || 'auto';
      $('apiKeyInput').value = '';
      $('apiKeyInput').placeholder = cfg.has_key ? `Current: ${cfg.key_masked} (leave blank to keep)` : 'Paste your Gemini API key';
      $('modelSelect').value = cfg.model;
      $('qualitySelect').value = cfg.quality;
      $('thinkingChk').checked = !!cfg.thinking;
      $('pinInput').value = '';
      $('pinInput').placeholder = cfg.has_pin ? 'PIN is set — type a new one to change' : '4–8 digits (optional)';
      $('pinClear').style.display = cfg.has_pin ? 'grid' : 'none';
      $('pinClear').onclick = () => saveSettings({ app_pin: '' });
    } catch (e) { /* ignore */ }
    $('settingsModal').hidden = false;
  }

  async function saveSettings(extra) {
    const payload = extra || {
      model: $('modelSelect').value,
      quality: $('qualitySelect').value,
      thinking: $('thinkingChk').checked,
      llm_provider: $('providerSelect').value,
    };
    const key = $('apiKeyInput').value.trim();
    if (key) payload.api_key = key;
    const pin = $('pinInput').value.trim();
    if (pin && !extra) payload.app_pin = pin;
    try {
      await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      $('settingsModal').hidden = true;
      toast('Settings saved ✓');
      refreshConfig();
    } catch (e) { toast('Save failed', true); }
  }

  function bindSettings() {
    $('settingsClose').onclick = () => { $('settingsModal').hidden = true; };
    $('settingsModal').addEventListener('click', (e) => {
      if (e.target === $('settingsModal')) $('settingsModal').hidden = true;
    });
    $('keyEye').onclick = () => {
      const inp = $('apiKeyInput');
      inp.type = inp.type === 'password' ? 'text' : 'password';
    };
    $('settingsSave').onclick = saveSettings;
  }

  /* ═══════════ scroll ═══════════ */
  function scrollBottom(force) {
    const sc = $('chatScroll');
    const near = sc.scrollHeight - sc.scrollTop - sc.clientHeight < 260;
    if (near || force) sc.scrollTop = sc.scrollHeight;
  }

  init();
})();
