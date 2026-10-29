"use strict";
// Behaviour of the pages: theme toggle, mobile menu, "On this page", copy buttons,
// figures opened full size, <details> opened by a link to an element inside, and the
// search (Pagefind, built after the site).
//
// Hook for an overlay: the scripts of the setting docs.js run after this one (all are
// deferred, in order) and find window.docsTheme = {root, storage, $, $$}: the path to the
// root of the site, the prefix of the localStorage keys, and two query helpers.

(function () {
  const root = document.body.dataset.root || '';
  const storage = document.body.dataset.storage || 'docs';
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  window.docsTheme = {root, storage, $, $$};

  // ---- theme ----------------------------------------------------------
  const toggle = $('.theme-toggle');
  if (toggle) toggle.addEventListener('click', () => {
    const t = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem(storage + '-theme', t); } catch (e) {}
  });

  // ---- mobile menu ----------------------------------------------------
  const navBtn = $('.nav-toggle'), backdrop = $('.sidebar-backdrop');
  function setNav(open) {
    document.body.classList.toggle('nav-open', open);
    if (navBtn) navBtn.setAttribute('aria-expanded', String(open));
    if (backdrop) backdrop.hidden = !open;
  }
  if (navBtn) navBtn.addEventListener('click', () => setNav(!document.body.classList.contains('nav-open')));
  if (backdrop) backdrop.addEventListener('click', () => setNav(false));

  // ---- on this page -----------------------------------------------------
  // the h2 of the content, and any element with an id and a data-toc attribute (its label
  // in this list, e.g. "Construct (18)"); an h3 is indented
  const pageToc = $('#title_id');
  const headings = $$('main article h2[id], main article [id][data-toc]');
  if (pageToc && headings.length > 1) {
    const title = document.createElement('div');
    title.className = 'page-toc-title';
    title.textContent = 'On this page';
    pageToc.appendChild(title);
    const links = headings.map(h => {
      const a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.dataset.toc || h.textContent.replace(/\s+/g, ' ').replace(/#$/, '').trim();
      if (h.tagName === 'H3') a.className = 'toc-sub';
      pageToc.appendChild(a);
      return a;
    });
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(entries => {
        entries.forEach(en => {
          if (en.isIntersecting) {
            links.forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + en.target.id));
          }
        });
      }, {rootMargin: '-70px 0px -70% 0px'});
      headings.forEach(h => io.observe(h));
    }
  }
  // anchor link on the headings of the content
  $$('main article h2[id], main article h3[id]').forEach(h => {
    const a = document.createElement('a');
    a.className = 'heading-anchor';
    a.href = '#' + h.id;
    a.setAttribute('aria-label', 'Link to this section');
    a.textContent = '#';
    h.appendChild(a);
  });

  // ---- code: copy button ------------------------------------------------
  $$('main article div.code').forEach(block => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const text = block.querySelector('pre').innerText;
      const done = () => { btn.textContent = 'Copied'; setTimeout(() => btn.textContent = 'Copy', 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => {});
    });
    block.appendChild(btn);
  });

  // ---- figures: open full size on click / tap -------------------------
  // A figure written <figure class="figure"><a class="figure-zoom" href="image"><img ...></a>
  // opens the image at its own size (or larger on a wide screen) in an overlay that scrolls
  // and can be pinch-zoomed: on a phone, the text of a drawing is otherwise unreadable.
  let box = null, lastFocus = null;
  function closeBox() {
    if (!box || box.hidden) return;
    box.hidden = true;
    document.documentElement.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }
  function openBox(href, alt) {
    if (!box) {
      box = document.createElement('div');
      box.className = 'lightbox';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      box.setAttribute('aria-label', 'Figure, full size');
      box.innerHTML = '<div class="lightbox-bar"><a class="lightbox-open" target="_blank" rel="noopener">Open the image</a>'
                    + '<button type="button" class="lightbox-close">Close</button></div><img alt="">';
      box.addEventListener('click', ev => { if (!ev.target.closest('.lightbox-open')) closeBox(); });
      document.body.appendChild(box);
    }
    const img = $('img', box);
    img.style.width = '';
    img.onload = () => {
      const natural = img.naturalWidth || 700, avail = window.innerWidth - 56;
      img.style.width = (natural <= avail ? Math.min(avail, natural * 1.6) : natural) + 'px';
    };
    img.alt = alt || '';
    img.src = href;
    $('.lightbox-open', box).href = href;
    lastFocus = document.activeElement;
    box.hidden = false;
    box.scrollTop = 0; box.scrollLeft = 0;
    document.documentElement.style.overflow = 'hidden';
    $('.lightbox-close', box).focus();
  }
  document.addEventListener('click', ev => {
    const a = ev.target.closest && ev.target.closest('a.figure-zoom');
    if (!a || ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button !== 0) return;
    ev.preventDefault();
    const img = $('img', a);
    openBox(a.href, img && img.alt);
  });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeBox(); });

  // ---- details opened by a link to an element inside ------------------
  function revealHash() {
    if (!location.hash) return;
    let el = null;
    try { el = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) {}
    if (!el) return;
    const det = el.closest('details');
    if (det && !det.open) { det.open = true; el.scrollIntoView(); }
  }
  window.addEventListener('hashchange', revealHash);
  revealHash();

  // ---- search (Pagefind) ----------------------------------------------
  // The index is built after the site: pagefind --site <site directory> (README of the theme).
  const input = $('#search'), panel = $('#search-results');
  // Sub-results come in page order; show the one whose title is the query first.
  const exactFirst = (subs, q) => {
    const k = q.trim().toLowerCase();
    return subs.map((s, i) => [s, i])
      .sort((a, b) => ((a[0].title || '').trim().toLowerCase() !== k) - ((b[0].title || '').trim().toLowerCase() !== k) || a[1] - b[1])
      .map(x => x[0]);
  };
  if (!input || !panel) return;
  let pagefind = null, loading = null, seq = 0, selected = -1;

  function load() {
    if (!loading) {
      const base = new URL(root || './', location.href);
      loading = import(new URL('pagefind/pagefind.js', base).href).then(async pf => {
        await pf.options({baseUrl: base.pathname, excerptLength: 18, ranking: {termSimilarity: 10}});
        pf.init();
        pagefind = pf;
        return pf;
      }).catch(err => {
        panel.innerHTML = '<p class="search-empty">Search is available when the site is served over http (Pagefind index not found).</p>';
        panel.hidden = false;
        throw err;
      });
    }
    return loading;
  }

  function esc(s) { return s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])); }

  async function search(q) {
    const my = ++seq;
    if (!q.trim()) { panel.hidden = true; panel.innerHTML = ''; return; }
    const pf = await load();
    const res = await pf.debouncedSearch(q, {}, 120);
    if (res === null || my !== seq) return;
    const data = await Promise.all(res.results.slice(0, 8).map(r => r.data()));
    if (my !== seq) return;
    if (!data.length) {
      panel.innerHTML = `<p class="search-empty">No result for <strong>${esc(q)}</strong>.</p>`;
    } else {
      panel.innerHTML = data.map(d => {
        const subs = exactFirst((d.sub_results || []).filter(s => s.url !== d.url), q).slice(0, 4);
        const section = d.meta && d.meta.section ? `<span class="sr-section">${esc(d.meta.section)}</span>` : '';
        return `<div class="sr"><a class="sr-page sr-item" href="${d.url}">${section}<span class="sr-title">${esc(d.meta.title || d.url)}</span>` +
               `<span class="sr-excerpt">${d.excerpt}</span></a>` +
               subs.map(s => `<a class="sr-sub sr-item" href="${s.url}"><span class="sr-title">${esc(s.title)}</span>` +
                             `<span class="sr-excerpt">${s.excerpt}</span></a>`).join('') + '</div>';
      }).join('');
    }
    selected = -1;
    panel.hidden = false;
  }

  input.addEventListener('focus', () => { load().catch(() => {}); if (input.value) panel.hidden = false; });
  input.addEventListener('input', () => search(input.value).catch(() => {}));
  input.addEventListener('keydown', ev => {
    const items = $$('.sr-item', panel);
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      ev.preventDefault();
      if (!items.length) return;
      selected = (selected + (ev.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      items.forEach((it, k) => it.classList.toggle('selected', k === selected));
      items[selected].scrollIntoView({block: 'nearest'});
    } else if (ev.key === 'Enter') {
      const it = items[selected >= 0 ? selected : 0];
      if (it) location.href = it.href;
    } else if (ev.key === 'Escape') {
      panel.hidden = true; input.blur();
    }
  });
  document.addEventListener('click', ev => { if (!ev.target.closest('.search')) panel.hidden = true; });
  document.addEventListener('keydown', ev => {
    const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
    if ((ev.key === '/' && !typing) || (ev.key === 'k' && (ev.metaKey || ev.ctrlKey))) {
      ev.preventDefault(); input.focus(); input.select();
    }
  });
})();
