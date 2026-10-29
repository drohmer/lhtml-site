"""The docs theme (lhtml_site/themes/docs) and its starter (lhtml-site init --theme docs).

The build tests run everywhere; the ones that run the menu in Chromium are opt-in, as the
other browser tests (LHTML_BROWSER_TEST=1).
"""
import functools
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
