"""The docs theme (lhtml_site/themes/docs) and its starter (lhtml-site init --theme docs).

The build tests run everywhere; the ones that run the menu in Chromium are opt-in, as the
other browser tests (LHTML_BROWSER_TEST=1).
"""
import functools
import html
import http.server
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

import pytest
import yaml

from lhtml_site import theme

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / 'src/lhtml_site/themes/docs'
GENERATE = [sys.executable, str(REPO / 'generate.py')]
SETTINGS = {
    'name': 'Proj', 'sub': 'docs', 'title': 'Proj docs', 'storage': 'proj',
    'repo_url': 'https://example.org/proj', 'repo_label': 'Proj repository',
    'footer': 'Proj footer text.',
    'section_index': {'Guides': '02_guides/index.html'},
    'css': ['theme/css/extra.css'], 'js': ['theme/js/extra.js'],
    'menu': {'sections': ['Reference', 'Get started', 'Guides'],
             'section': {'Reference': {'open': False, 'groups': 'closed',
                                       'group_link_class': 'mono', 'plain_groups': ['Other']}}},
}


def build(project, docs=None):
    """Build the project; with `docs`, its configure.yaml gets these settings first."""
    if docs is not None:
        config = project / 'configure.yaml'
        data = yaml.safe_load(config.read_text(encoding='utf-8'))
        data['keywords'] = {'docs': docs}
        config.write_text(yaml.safe_dump(data), encoding='utf-8')
    result = subprocess.run(GENERATE + ['--strict'], cwd=project, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return project / '.site'


def toc_of(site):
    text = (site / 'theme/js/menu.js').read_text(encoding='utf-8')
    return json.loads(re.search(r'const toc = (\[.*?\]);', text, re.S).group(1))


@pytest.fixture(scope='module')
def starter(tmp_path_factory):
    """The starter, as `lhtml-site init --theme docs` writes it, plus a section with groups
    in the Reference (for the settings of a section)."""
    project = tmp_path_factory.mktemp('docs') / 'my-docs'
    subprocess.run(GENERATE + ['init', str(project), '--theme', 'docs'], check=True, capture_output=True)
    for name, group in (('02_vec', 'Types'), ('03_other', 'Other')):
        page = project / 'src/03_reference' / name
        page.mkdir()
        (page / 'index.md.j2').write_text(
            f'---\ntitle: {name}\nsection: Reference\ngroup: {group}\n---\n\n# {name}\n', encoding='utf-8')
    return project


def test_the_manifest_validates():
    manifest = theme.read(DOCS)
    assert manifest['toc'] == {'file': 'js/menu.js', 'keys': ['section', 'group']}
    assert manifest['layout']['root'] == '#content article'
    assert theme.validate(yaml.safe_load(theme.path(DOCS).read_text()), theme.path(DOCS))


def test_the_starter_builds_with_its_sections_in_order(starter):
    site = build(starter)
    toc = toc_of(site)
    assert toc[0]['path'] == 'index.html' and 'section' not in toc[0]
    assert [e.get('section') for e in toc[1:]] == ['Get started'] * 3 + ['Guides'] * 3 + ['Reference'] * 3
    assert toc[1]['path'] == '01_start/index.html'           # the index of a section comes first
    assert [e.get('group') for e in toc if e.get('section') == 'Guides'] == ['Writing', 'Writing', 'Publishing']
    page = (site / '02_guides/02_figures/index.html').read_text(encoding='utf-8')
    assert 'class="figure-zoom"' in page and 'data-pagefind-body' in page
    assert '<nav class="breadcrumb"' in page and '<li aria-current="page">Figures</li>' in page
    assert (site / 'theme/fonts/source_code_pro').is_dir() and (site / 'theme/libs/katex/katex.min.js').is_file()


def test_defaults_without_settings(starter):
    site = build(starter)
    page = (site / '01_start/01_install/index.html').read_text(encoding='utf-8')
    assert '<html lang="en">' in page and '>Skip to content</a>' in page
    assert 'placeholder="Search the docs"' in page and '<span class="pager-label">Previous</span>' in page
    assert json.loads(re.search(r'<script id="docs-strings" type="application/json">(.*?)</script>',
                                page).group(1))['copy'] == 'Copy'
    assert '<span class="brand-name">Docs</span>' in page
    assert '<title>Install</title>' in page                     # no suffix without docs.title
    assert 'icon-btn" href=' not in page and '<footer' not in page
    assert "localStorage.getItem('docs-theme')" in page and 'data-storage="docs"' in page
    assert re.search(r'<script id="docs-menu-config" type="application/json">\{\}</script>', page)


def test_the_settings_reach_the_pages(starter):
    site = build(starter, SETTINGS)
    page = (site / '02_guides/01_write/index.html').read_text(encoding='utf-8')
    assert '<span class="brand-name">Proj</span><span class="brand-sub">docs</span>' in page
    assert '<title>Write a page - Proj docs</title>' in page
    assert 'href="https://example.org/proj" aria-label="Proj repository"' in page
    assert 'Proj footer text.' in page
    assert "localStorage.getItem('proj-theme')" in page
    # the breadcrumb links the section and the group to the index of the section
    assert '<a href="../../02_guides/index.html">Guides</a>' in page
    assert '<a href="../../02_guides/index.html#writing">Writing</a>' in page
    # the overlay files, after those of the theme
    css = page.index('theme/css/docs.css'), page.index('theme/css/extra.css')
    js = page.index('theme/js/site.js'), page.index('theme/js/extra.js')
    assert css[0] < css[1] and js[0] < js[1]
    menu = json.loads(re.search(r'<script id="docs-menu-config" type="application/json">(.*?)</script>',
                                page, re.S).group(1))
    assert menu == SETTINGS['menu']
    build(starter, {})                                          # back to the defaults


def nav_of(page):
    return re.search(r'<nav id="toc" class="nav">(.*?)</nav>', page, re.S).group(1)


def pager_of(page):
    """[previous title, next title] of the pager written in the page (None: no link)."""
    pager = re.search(r'<nav class="pager"[^>]*>(.*?)</nav>', page, re.S).group(1)
    found = dict(re.findall(r'<a class="pager-link (prev|next)" href="[^"]*"><span class="pager-label">[^<]*</span>'
                            r'<span class="pager-title">([^<]*)</span></a>', pager))
    return [html.unescape(found[r]) if r in found else None for r in ('prev', 'next')]


def test_the_menu_and_the_pager_are_written_in_the_pages(starter):
    """The menu and previous / next are in the HTML, without JavaScript: the same menu as
    js/menu.js built in the browser (open / closed parts, groups, labels, current page)."""
    site = build(starter, SETTINGS)
    toc = toc_of(site)
    for k, entry in enumerate(toc):
        page = (site / entry['path']).read_text(encoding='utf-8')
        root = '../' * entry['path'].count('/')
        active = re.findall(r'<a href="([^"]+)" class="nav-link active[^"]*" aria-current="page">', nav_of(page))
        assert active == [root + entry['path']], (entry, active)
        assert pager_of(page) == [toc[k - 1]['title'] if k > 0 else None,
                                  toc[k + 1]['title'] if k + 1 < len(toc) else None]
    nav = nav_of((site / 'index.html').read_text(encoding='utf-8'))
    # the sections in the order of the settings, Reference closed (open: false)
    assert re.findall(r'<details class="nav-section" data-key="([^"]+)"( open)?>', nav) == [
        ('Reference', ''), ('Get started', ' open'), ('Guides', ' open')]
    assert re.findall(r'<details class="nav-group" data-key="([^"]+)"( open)?>', nav) == [
        ('Reference/Types', ''), ('Reference/Other', '')]                    # groups: closed
    assert re.findall(r'<details class="nav-subgroup" data-key="([^"]+)" open>', nav) == [
        'Guides/Writing', 'Guides/Publishing']
    assert re.findall(r'class="nav-link mono">([^<]*)<', nav) == ['02_vec']   # not Other, not ungrouped
    assert '<a href="01_start/index.html" class="nav-link">Overview</a>' in nav
    assert '<summary class="nav-section-title"><a href="01_start/index.html">Get started</a></summary>' in nav
    assert '<summary class="nav-section-title"><span>Guides</span></summary>' in nav     # no index page
    # a page of the closed section opens it, and its group
    nav = nav_of((site / '03_reference/02_vec/index.html').read_text(encoding='utf-8'))
    assert '<details class="nav-section" data-key="Reference" open>' in nav
    assert '<details class="nav-group" data-key="Reference/Types" open>' in nav
    assert '<details class="nav-group" data-key="Reference/Other">' in nav
    # menu.js builds no menu: it keeps the state of the parts
    menu = (site / 'theme/js/menu.js').read_text(encoding='utf-8')
    assert 'createElement' not in menu and "dataset.key" in menu
    build(starter, {})


def test_a_partial_build_says_when_the_menu_of_the_other_pages_is_out_of_date(tmp_path):
    project = tmp_path / 'my-docs'
    subprocess.run(GENERATE + ['init', str(project), '--theme', 'docs'], check=True, capture_output=True)
    build(project)
    run = lambda: subprocess.run(GENERATE + ['--only', '01_start/01_install'], cwd=project,
                                 capture_output=True, text=True)
    result = run()
    assert result.returncode == 0 and 'the menu changed' not in result.stdout + result.stderr
    page = project / 'src/01_start/01_install/index.md.j2'
    page.write_text(page.read_text(encoding='utf-8').replace('title: Install', 'title: Set up'), encoding='utf-8')
    result = run()
    assert result.returncode == 0 and 'the menu changed' in result.stdout + result.stderr
    assert '>Set up</a>' in (project / '.site/01_start/01_install/index.html').read_text(encoding='utf-8')


def test_the_breadcrumb_links_the_section_to_its_index_page(starter):
    site = build(starter)
    install = (site / '01_start/01_install/index.html').read_text(encoding='utf-8')
    assert '<li class="bc-section"><a href="../../01_start/index.html">Get started</a></li>' in install
    # the index page itself, and a section with no index page: text
    index = (site / '01_start/index.html').read_text(encoding='utf-8')
    assert '<li class="bc-section"><span>Get started</span></li>' in index
    write = (site / '02_guides/01_write/index.html').read_text(encoding='utf-8')
    assert '<li class="bc-section"><span>Guides</span></li>' in write
    css = (DOCS / 'css/docs.css').read_text(encoding='utf-8')
    assert '.breadcrumb li.bc-section a { color: var(--accent-text); }' in css


def test_the_texts_in_the_language_of_the_site(starter):
    """lang: fr: the texts of the theme in French; strings: and the older settings replace
    one of them."""
    site = build(starter, {'lang': 'fr', 'strings': {'copy': 'Copier le code', 'next': 'Après'},
                           'search_placeholder': 'Chercher', 'menu': {'home_label': 'Départ'}})
    page = (site / '01_start/01_install/index.html').read_text(encoding='utf-8')
    assert '<html lang="fr">' in page and '>Aller au contenu</a>' in page
    assert 'aria-label="Ouvrir le menu"' in page and 'aria-label="Menu de la documentation"' in page
    assert 'placeholder="Chercher"' in page and 'aria-label="Rechercher dans la documentation"' in page
    assert '<span class="pager-label">Précédent</span>' in page and '<span class="pager-label">Après</span>' in page
    assert 'class="nav-link">Départ</a>' in page and 'Vue d&#39;ensemble</a>' in page
    assert 'aria-label="Fil d&#39;Ariane"' in page
    strings = json.loads(re.search(r'<script id="docs-strings" type="application/json">(.*?)</script>',
                                   page).group(1))
    assert strings['copy'] == 'Copier le code' and strings['on_this_page'] == 'Sur cette page'
    for english in ('Skip to content', 'Previous', 'Search the docs', 'Toggle dark mode'):
        assert english not in page, english
    # the scripts read their texts there, with the English ones as a fallback
    script = (site / 'theme/js/site.js').read_text(encoding='utf-8')
    assert "text('copy', 'Copy')" in script and "text('on_this_page', 'On this page')" in script
    build(starter, {})


def test_the_language_switch_stays_on_phones():
    """Below 480 px the repository link leaves the top bar, not a link to the other language
    (icon-btn lang-switch, added by an overlay)."""
    css = (DOCS / 'css/docs.css').read_text(encoding='utf-8')
    assert '.topbar-actions .icon-btn[href]:not(.lang-switch) { display: none; }' in css


def test_readable_heading_ids(tmp_path):
    """The docs theme asks for slugs (theme.yaml, heading_ids): complete, unique in the page,
    never an id of the theme, an id written by the author kept; LHTML pages as Markdown ones."""
    project = tmp_path / 'my-docs'
    subprocess.run(GENERATE + ['init', str(project), '--theme', 'docs'], check=True, capture_output=True)
    page = project / 'src/01_start/01_install/index.md.j2'
    page.write_text(page.read_text(encoding='utf-8') + '\n## When something goes wrong\n\n## Step\n\n## Step\n\n'
                    '## Content\n\n## Only LHTML?\n\n## {{ "Rendered" }} by Jinja\n\n## mine\n\n## Mine {: #mine}\n',
                    encoding='utf-8')
    lhtml = project / 'src/01_start/03_lhtml/index.html.j2'
    lhtml.parent.mkdir()
    lhtml.write_text('---\ntitle: LHTML page\nsection: Get started\n---\n= LHTML page\n\n== Café crème\n\n'
                     '==(#kept) Written\n', encoding='utf-8')
    site = build(project)
    ids = re.findall(r'<h2[^>]* id="([^"]+)"', (site / '01_start/01_install/index.html').read_text(encoding='utf-8'))
    for expected in ('when-something-goes-wrong', 'step', 'step-2', 'content-2', 'only-lhtml',
                     'rendered-by-jinja', 'mine-2', 'mine'):
        assert expected in ids, (expected, ids)
    assert not any(re.search(r'_l\d$|_id\d', i) for i in ids), ids
    ids = re.findall(r'<h2[^>]* id="([^"]+)"', (site / '01_start/03_lhtml/index.html').read_text(encoding='utf-8'))
    assert ids == ['cafe-creme', 'kept']


def test_a_heading_search_does_not_take_the_id_of_the_search_box(tmp_path):
    """A heading "Search" with the id `search` (here given, a slug in a page that
    includes a README): the search box has another one, so that `#search` leads to
    the heading and the ids of the page stay unique."""
    project = tmp_path / 'my-docs'
    subprocess.run(GENERATE + ['init', str(project), '--theme', 'docs'], check=True, capture_output=True)
    page = project / 'src/01_start/01_install/index.md.j2'
    page.write_text(page.read_text(encoding='utf-8') + '\n## Search {: #search}\n\nThe search box.\n', encoding='utf-8')
    html = (build(project) / '01_start/01_install/index.html').read_text(encoding='utf-8')
    ids = re.findall(r'\sid="([^"]+)"', html)
    assert ids.count('search') == 1 and len(ids) == len(set(ids))
    assert re.search(r'<h2[^>]* id="search"', html)
    assert '<input id="site-search" type="search"' in html


# ---- in Chromium ---------------------------------------------------------------------

browser_test = pytest.mark.skipif(os.environ.get('LHTML_BROWSER_TEST') != '1',
                                  reason='Set LHTML_BROWSER_TEST=1 for Chromium')


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def served(starter):
    """(base URL, page) of the built starter served over http, in Chromium."""
    playwright = pytest.importorskip('playwright.sync_api')
    servers = []

    def serve(docs):
        site = build(starter, docs)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(site)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f'http://127.0.0.1:{server.server_address[1]}/', toc_of(site)

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        yield serve, page
        browser.close()
    for server in servers:
        server.shutdown()
    build(starter, {})
    assert errors == []


@browser_test
def test_every_page_has_the_menu_and_the_pager_in_the_order_of_the_site(served):
    serve, page = served
    base, toc = serve({})
    for k, entry in enumerate(toc):
        page.goto(base + entry['path'])
        active = page.eval_on_selector_all('#toc a.active', 'els => els.map(a => a.href)')
        assert active == [base + entry['path']], (entry, active)
        pager = page.evaluate("() => ['prev', 'next'].map(r => { const a = document.querySelector('.pager a.' + r);"
                              " return a ? a.querySelector('.pager-title').textContent : null; })")
        assert pager == [toc[k - 1]['title'] if k > 0 else None,
                         toc[k + 1]['title'] if k + 1 < len(toc) else None]
    # defaults: sections in the order of their first page, all open, the index as Overview
    page.goto(base + 'index.html')
    sections = page.eval_on_selector_all('#toc > details.nav-section', 'els => els.map(d => [d.querySelector("summary").textContent, d.open])')
    assert sections == [['Get started', True], ['Guides', True], ['Reference', True]]
    assert page.text_content('#toc details.nav-section .nav-children a') == 'Overview'


@browser_test
def test_the_menu_settings_are_honored(served):
    serve, page = served
    base, toc = serve(SETTINGS)
    page.goto(base + 'index.html')
    sections = page.eval_on_selector_all('#toc > details.nav-section', 'els => els.map(d => [d.querySelector("summary").textContent, d.open])')
    assert sections == [['Reference', False], ['Get started', True], ['Guides', True]]
    groups = page.eval_on_selector_all('#toc details.nav-group', 'els => els.map(d => [d.querySelector("summary").textContent, d.open])')
    assert groups == [['Types', False], ['Other', False]]                  # closed groups
    assert page.eval_on_selector_all('#toc details.nav-subgroup', 'els => els.length') == 2   # Guides: open
    mono = page.eval_on_selector_all('#toc a.mono', 'els => els.map(a => a.textContent)')
    assert mono == ['02_vec']                                              # not 'Other', not ungrouped
    # a page of the closed section opens it, and its group
    page.goto(base + '03_reference/02_vec/index.html')
    assert page.eval_on_selector('#toc > details.nav-section', 'd => d.open')
    assert page.eval_on_selector('#toc details.nav-group', 'd => d.open')


@browser_test
def test_a_collapsed_section_stays_collapsed_after_a_reload(served):
    serve, page = served
    base, toc = serve({})
    page.goto(base + 'index.html')
    guides = '#toc > details.nav-section:nth-of-type(2)'
    assert page.eval_on_selector(guides, 'd => d.open')
    # the title of a section with no index page is text: a click toggles the section
    page.click(guides + ' > summary')
    assert not page.eval_on_selector(guides, 'd => d.open')
    page.reload()
    assert not page.eval_on_selector(guides, 'd => d.open')
    assert page.evaluate("() => JSON.parse(localStorage.getItem('docs-menu-open'))")['Guides'] is False


@browser_test
def test_the_language_switch_fits_the_top_bar_of_a_phone(served):
    serve, page = served
    base, toc = serve(SETTINGS)
    page.set_viewport_size({'width': 390, 'height': 700})
    page.goto(base + '01_start/01_install/index.html')
    page.evaluate("() => { const a = document.createElement('a'); a.className = 'icon-btn lang-switch';"
                  " a.href = '#'; a.textContent = 'FR'; document.querySelector('.topbar-actions').prepend(a); }")
    assert page.is_visible('.lang-switch') and page.is_visible('.theme-toggle')
    assert not page.is_visible('.topbar-actions a.icon-btn:not(.lang-switch)')         # the repository
    assert page.eval_on_selector('.theme-toggle', 'b => b.getBoundingClientRect().right') <= 390
    assert page.evaluate('() => document.documentElement.scrollWidth') <= 390


@browser_test
def test_on_this_page_on_a_phone(served):
    """Below 1180 px the right column is hidden: "On this page" is a bar at the top of the
    content, its links those of the column; a link closes it and leaves its heading in view."""
    serve, page = served
    base, toc = serve({})
    page.set_viewport_size({'width': 390, 'height': 700})
    page.goto(base + '01_start/02_first-page/index.html')
    bar = '.mobile-toc'
    assert page.is_visible(bar + ' summary')
    column = page.eval_on_selector_all('#title_id a', 'els => els.map(a => a.getAttribute("href"))')
    links = page.eval_on_selector_all(bar + ' nav a', 'els => els.map(a => a.getAttribute("href"))')
    assert links == column and len(links) >= 2
    page.click(bar + ' summary')
    page.click(f'{bar} nav a[href="{links[-1]}"]')
    assert not page.eval_on_selector(bar, 'd => d.open')
    page.wait_for_timeout(300)
    heading_top = page.evaluate('id => document.getElementById(id).getBoundingClientRect().top', links[-1][1:])
    assert heading_top >= page.eval_on_selector(bar, 'd => d.getBoundingClientRect().bottom')
    # on a wide screen, the column only
    page.set_viewport_size({'width': 1400, 'height': 900})
    assert not page.is_visible(bar)
