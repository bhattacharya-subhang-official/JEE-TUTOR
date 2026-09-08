/* mini markdown renderer with LaTeX (KaTeX) support */
(function () {
  const MATH_TOKEN = '\u0001MATH';

  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
  }

  /* Extract math spans before markdown so * _ etc. inside math survive. */
  function extractMath(src) {
    const store = [];
    const keep = (m) => { store.push(m); return MATH_TOKEN + (store.length - 1) + '\u0001'; };
    let s = src;
    s = s.replace(/```[\s\S]*?```|`[^`\n]+`/g, (m) => keep(m));          // code first
    s = s.replace(/\$\$([\s\S]+?)\$\$/g, (m) => keep(m));
    s = s.replace(/\\\[([\s\S]+?)\\\]/g, (m) => keep(m));
    s = s.replace(/\\\(([\s\S]+?)\\\)/g, (m) => keep(m));
    s = s.replace(/\$([^\$\n]+?)\$/g, (m) => keep(m));
    return [s, store];
  }

  function inlineMd(s) {
    s = escHtml(s);
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[\s(])\*([^*\n]+)\*/g, '$1<em>$2</em>');
    s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>');
    s = s.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return s;
  }

  function blockMd(src) {
    const lines = src.split('\n');
    let html = '', i = 0;
    let listType = null;

    const closeList = () => { if (listType) { html += listType === 'ol' ? '</ol>' : '</ul>'; listType = null; } };

    while (i < lines.length) {
      const line = lines[i];

      if (/^\s*$/.test(line)) { closeList(); i++; continue; }
      if (/^ {0,3}(---+|\*\*\*+|___+)\s*$/.test(line)) { closeList(); html += '<hr>'; i++; continue; }
      const h = line.match(/^(#{1,4})\s+(.*)$/);
      if (h) { closeList(); const l = h[1].length; html += `<h${l}>${inlineMd(h[2])}</h${l}>`; i++; continue; }
      if (/^ {0,3}>\s?/.test(line)) {
        closeList();
        const buf = [];
        while (i < lines.length && /^ {0,3}>\s?/.test(lines[i])) { buf.push(lines[i].replace(/^ {0,3}>\s?/, '')); i++; }
        html += `<blockquote>${inlineMd(buf.join(' '))}</blockquote>`; continue;
      }
      // table: | a | b |  /  |---|---|
      if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
        closeList();
        const parseRow = (l) => l.trim().replace(/^\||\|$/g, '').split('|').map((c) => inlineMd(c.trim()));
        const head = parseRow(line); i += 2;
        let rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { rows.push(parseRow(lines[i])); i++; }
        html += '<table><thead><tr>' + head.map((c) => `<th>${c}</th>`).join('') + '</tr></thead><tbody>' +
                rows.map((r) => '<tr>' + r.map((c) => `<td>${c}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
        continue;
      }
      if (/^\s*[-*+]\s+/.test(line)) {
        if (listType !== 'ul') { closeList(); html += '<ul>'; listType = 'ul'; }
        html += `<li>${inlineMd(line.replace(/^\s*[-*+]\s+/, ''))}</li>`; i++; continue;
      }
      if (/^\s*\d+[.)]\s+/.test(line)) {
        if (listType !== 'ol') { closeList(); html += '<ol>'; listType = 'ol'; }
        html += `<li>${inlineMd(line.replace(/^\s*\d+[.)]\s+/, ''))}</li>`; i++; continue;
      }
      closeList();
      const buf = [line]; i++;
      while (i < lines.length && !/^\s*$/.test(lines[i]) && !/^(#{1,4}\s| {0,3}>|\s*[-*+]\s|\s*\d+[.)]\s|\s*\|)/.test(lines[i])) {
        buf.push(lines[i]); i++;
      }
      html += `<p>${inlineMd(buf.join('\n')).replace(/\n/g, '<br>')}</p>`;
    }
    closeList();
    return html;
  }

  function restoreCode(html, store) {
    html = html.replace(/\u0001MATH(\d+)\u0001/g, (_, n) => store[+n]);
    return html;
  }

  function renderMarkdown(raw) {
    const [md, store] = extractMath(raw || '');
    let html = blockMd(md);
    html = restoreCode(html, store);
    // fenced code blocks & inline code (stored raw, escaped)
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
      `<pre><code class="lang-${escHtml(lang)}">${escHtml(code.replace(/\n$/, ''))}</code></pre>`);
    return html;
  }

  /* KaTeX typeset an element (falls back silently if katex missing). */
  function typesetMath(el) {
    if (!el || typeof renderMathInElement !== 'function') return;
    try {
      renderMathInElement(el, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false },
          { left: '$', right: '$', display: false },
        ],
        throwOnError: false,
        ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
      });
    } catch (e) { /* ignore */ }
  }

  function renderMarkdownMath(raw) {
    const wrap = document.createElement('div');
    wrap.className = 'md';
    wrap.innerHTML = renderMarkdown(raw);
    typesetMath(wrap);
    return wrap;
  }

  window.MD = { renderMarkdown, renderMarkdownMath, typesetMath, escHtml };
})();
