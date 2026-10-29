"use strict";
// The side menu, grouped by the `section` (and `group`) of each page, and previous / next.
// lhtml-site writes the table of contents in place of the placeholder below
// (theme.yaml: toc: file: js/menu.js, keys: [section, group]).
// Settings: the `menu` of the `docs` keyword, written by the template in
// <script id="docs-menu-config">:
//   sections:    [names]  order of the sections (others follow, in order of first appearance)
//   home_label:  label of the first page when it has no section (default 'Home')
//   index_label: label of the index page of a section, <section>/index.html (default 'Overview')
//   section: {<name>: {open: false,            the section starts closed (unless the page is in it)
//                      groups: closed,         its groups start closed, in the lighter style
//                      group_link_class: mono, extra class of the links of its groups
//                      plain_groups: [names]}} groups whose links do not get that class

const toc = {{TOC}};

(function () {
  let cfg = {};
  try { cfg = JSON.parse(document.querySelector('#docs-menu-config').textContent) || {}; } catch (_) { cfg = {}; }
  const SECTIONS = cfg.sections || [];
  const nav = document.querySelector('#toc');
  const current = parseInt(document.querySelector('#current-page-id').textContent, 10);
  const root = document.body.dataset.root || '';
  const url = (p) => root + p.split('/').map(encodeURIComponent).join('/');

  function link(entry, k, label) {
    const a = document.createElement('a');
    a.href = url(entry.path);
    a.textContent = label || entry.title;
    a.className = 'nav-link';
    if (k === current) { a.classList.add('active'); a.setAttribute('aria-current', 'page'); }
    return a;
  }

  // Home: the pages without section
  toc.forEach((e, k) => { if (!e.section) nav.appendChild(link(e, k, k === 0 ? (cfg.home_label || 'Home') : e.title)); });

  // Open / closed state of the collapsible parts of the menu, kept by the browser
  //  (key: "section" or "section/group"; may be unavailable, e.g. private window)
  const STORE = (document.body.dataset.storage || 'docs') + '-menu-open';
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(STORE) || '{}') || {}; } catch (_) { saved = {}; }
  function collapsible(cls, key, label, href, openByDefault) {
    const det = document.createElement('details');
    det.className = cls;
    det.open = key in saved ? saved[key] : openByDefault;
    const sum = document.createElement('summary');
    sum.className = cls + '-title';
    const t = document.createElement(href ? 'a' : 'span');
    t.textContent = label;
    if (href) t.href = href;     // the title links to the index page; the arrow toggles
    sum.appendChild(t);
    det.appendChild(sum);
    // the entries of the part, after a vertical line showing the level (as in Starlight)
    det.body = document.createElement('div');
    det.body.className = 'nav-children';
    det.appendChild(det.body);
    det.addEventListener('toggle', () => {
      saved[key] = det.open;
      try { localStorage.setItem(STORE, JSON.stringify(saved)); } catch (_) { /* not stored */ }
    });
    return det;
  }

  const order = SECTIONS.concat(toc.map(e => e.section).filter(s => s && !SECTIONS.includes(s)));
  const seen = new Set();
  for (const section of order) {
    if (seen.has(section)) continue;
    seen.add(section);
    const pages = toc.map((e, k) => [e, k]).filter(([e]) => e.section === section);
    if (!pages.length) continue;
    const opt = (cfg.section || {})[section] || {};
    // the index page of the section (how-to/index.html): the section title links to it, and
    // it is the first entry of the section, labelled Overview
    const isIndex = (e) => /^[^/]+\/index\.html$/.test(e.path);
    const index = pages.find(([e]) => isIndex(e));
    const here = pages.some(([, k]) => k === current);
    // every section can be collapsed; a section with open: false starts closed unless the
    // current page is in it
    const box = collapsible('nav-section', section, section, index ? url(index[0].path) : null, opt.open !== false || here);
    if (here) box.open = true;
    // groups: open by default (nav-subgroup); with groups: closed, closed except the one of
    // the current page, in the lighter style (nav-group)
    const closedGroups = opt.groups === 'closed';
    let group = null, groupBox = box;
    for (const [e, k] of pages) {
      if (e.group && e.group !== group) {
        group = e.group;
        groupBox = closedGroups
          ? collapsible('nav-group', section + '/' + group, group, null, false)
          : collapsible('nav-subgroup', section + '/' + group, group, null, true);
        box.body.appendChild(groupBox);
      }
      const a = link(e, k, isIndex(e) ? (cfg.index_label || 'Overview') : null);
      if (opt.group_link_class && e.group && !(opt.plain_groups || []).includes(e.group)) a.classList.add(opt.group_link_class);
      if (k === current && groupBox.tagName === 'DETAILS') groupBox.open = true;
      groupBox.body.appendChild(a);
    }
    nav.appendChild(box);
  }
  // Scroll the menu (not the page) so that the current page is in view, centered
  const active = nav.querySelector('.active');
  const scroller = document.querySelector('#sidebar');
  if (active && scroller) {
    const center = () => {
      const r = active.getBoundingClientRect(), s = scroller.getBoundingClientRect();
      if (r.top < s.top + 40 || r.bottom > s.bottom - 40)
        scroller.scrollTop += r.top - s.top - (s.height - r.height) / 2;
    };
    center();
    // mobile: the menu is a drawer, laid out only when it opens
    const btn = document.querySelector('.nav-toggle');
    if (btn) btn.addEventListener('click', () => requestAnimationFrame(center));
  }

  // Previous / next, in the order of the site
  const pager = document.querySelector('.pager');
  if (pager) {
    const make = (k, cls, label) => {
      if (k < 0 || k >= toc.length) return;
      const a = document.createElement('a');
      a.className = 'pager-link ' + cls;
      a.href = url(toc[k].path);
      a.innerHTML = '<span class="pager-label"></span><span class="pager-title"></span>';
      a.querySelector('.pager-label').textContent = label;
      a.querySelector('.pager-title').textContent = toc[k].title;
      pager.appendChild(a);
    };
    make(current - 1, 'prev', 'Previous');
    make(current + 1, 'next', 'Next');
  }
})();
