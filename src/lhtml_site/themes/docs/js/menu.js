"use strict";
// The side menu: the build writes it in each page, with previous / next (template/nav.html);
// this script keeps the open / closed state the reader leaves to its sections and groups, and
// scrolls the menu to the current page.
// lhtml-site writes the table of contents in place of the placeholder below
// (theme.yaml: toc: file: js/menu.js, keys: [section, group]): the pages of the site, for
// the 404 page (js/not_found.js) and the scripts of an overlay.

const toc = {{TOC}};

(function () {
  const nav = document.querySelector('#toc');
  if (!nav) return;

  // Open / closed state of the collapsible parts of the menu, kept by the browser
  //  (key: "section" or "section/group", data-key; may be unavailable, e.g. private window).
  //  The parts holding the current page stay open.
  const STORE = (document.body.dataset.storage || 'docs') + '-menu-open';
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(STORE) || '{}') || {}; } catch (_) { saved = {}; }
  const parts = nav.querySelectorAll('details[data-key]');
  const store = () => {
    parts.forEach(det => { saved[det.dataset.key] = det.open; });
    try { localStorage.setItem(STORE, JSON.stringify(saved)); } catch (_) { /* not stored */ }
  };
  parts.forEach(det => {
    const key = det.dataset.key;
    if (key in saved) det.open = !!saved[key];
    if (det.querySelector('.nav-link.active')) det.open = true;
    det.addEventListener('toggle', store);
  });
  // the toggle event comes after the click: a page left at once keeps the state too
  window.addEventListener('pagehide', store);

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
})();
