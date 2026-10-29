"use strict";
// 404.html (template/404.html): the page of the menu closest to the URL that was asked for,
// and the search box of the page, which searches with the one of the top bar (site.js).
// Runs after menu.js, whose `toc` lists the pages of the site.

(function () {
  const root = document.body.dataset.root || '/';
  const base = new URL(root, location.href).pathname;

  // the words of a path: 02_guides/01_write/index.html -> guides write
  const words = (path) => path.toLowerCase()
    .replace(/(^|\/)index\.html?$/, '').replace(/\.html?$/, '')
    .split('/').map(part => part.replace(/^\d+[_-]/, '')).join(' ')
    .split(/[^a-z0-9]+/).filter(Boolean);

  // 1 for the same text, 0 for nothing in common (edit distance)
  function similarity(a, b) {
    if (!a.length || !b.length) return 0;
    let row = Array.from({length: b.length + 1}, (_, j) => j);
    for (let i = 1; i <= a.length; i++) {
      const next = [i];
      for (let j = 1; j <= b.length; j++)
        next[j] = Math.min(row[j] + 1, next[j - 1] + 1, row[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      row = next;
    }
    return 1 - row[b.length] / Math.max(a.length, b.length);
  }

  let asked = location.pathname;
  try { asked = decodeURIComponent(asked); } catch (_) { /* kept as it is */ }
  if (asked.startsWith(base)) asked = asked.slice(base.length);
  const askedWords = words(asked);
  const askedText = askedWords.join(' ');
  const askedLast = words(asked.split('/').filter(Boolean).pop() || '').join(' ');

  // the closest page: by its whole path, its last directory, or its title
  const pages = typeof toc === 'undefined' ? [] : toc;
  let best = null, score = 0;
  for (const entry of pages) {
    const path = words(entry.path);
    const s = Math.max(similarity(askedText, path.join(' ')),
                       similarity(askedLast, path.slice(-1).join(' ')),
                       similarity(askedLast, words(entry.title || '').join(' ')));
    if (s > score) { best = entry; score = s; }
  }
  const suggestion = document.querySelector('.not-found-suggestion');
  if (best && score >= 0.6 && suggestion) {
    const a = suggestion.querySelector('a');
    a.href = root + best.path.split('/').map(encodeURIComponent).join('/');
    a.textContent = best.title;
    suggestion.hidden = false;
  }

  // the search box of the page: the words of the URL, searched with the top bar
  const query = document.querySelector('#not-found-query');
  const search = document.querySelector('#search');
  if (query && search) {
    query.value = askedWords.join(' ');
    query.addEventListener('input', () => {
      search.value = query.value;
      search.dispatchEvent(new Event('input'));
    });
    query.closest('form').addEventListener('submit', () => { search.value = query.value; search.focus(); });
  }
})();
