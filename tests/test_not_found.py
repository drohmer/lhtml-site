"""404.html of the docs theme (lhtml_site/not_found.py, theme.yaml: not_found, configuration: base_url).

The build tests run everywhere; the one that serves the site and opens a URL that leads
nowhere in Chromium is opt-in, as the other browser tests (LHTML_BROWSER_TEST=1).
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
from urllib.parse import unquote, urlsplit

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
GENERATE = [sys.executable, str(REPO / 'generate.py')]


def configure(project, **options):
    config = project / 'configure.yaml'
    data = yaml.safe_load(config.read_text(encoding='utf-8'))
    data.pop('base_url', None)
    data.update(options)
    config.write_text(yaml.safe_dump(data), encoding='utf-8')


def build(project, **options):
    configure(project, **options)
    result = subprocess.run(GENERATE + ['--strict'], cwd=project, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return project / '.site'


def toc_of(site):
    text = (site / 'theme/js/menu.js').read_text(encoding='utf-8')
    return json.loads(re.search(r'const toc = (\[.*?\]);', text, re.S).group(1))


def links(html):
    """The href and src of a page."""
    return re.findall(r'(?:href|src)="([^"]*)"', html)


@pytest.fixture
def project(tmp_path):
    directory = tmp_path / 'my-docs'
    subprocess.run(GENERATE + ['init', str(directory), '--theme', 'docs'], check=True, capture_output=True)
    return directory


def test_no_404_without_base_url(project):
    site = build(project)
    assert not (site / '404.html').exists()


def test_the_404_page_links_from_the_base_url(project):
    site = build(project, base_url='/docs/')
    html = (site / '404.html').read_text(encoding='utf-8')
    own = [url for url in links(html) if not url.startswith(('http', '#', 'mailto:')) and url]
    assert own and all(url.startswith('/docs/') for url in own), own
    assert '/docs/theme/css/docs.css' in own and '/docs/theme/js/menu.js' in own
    assert '/docs/theme/js/not_found.js' in own
    assert 'data-root="/docs/"' in html
    assert '<meta name="robots" content="noindex">' in html
    assert 'data-pagefind-ignore="all"' in html and 'data-pagefind-body' not in html
    assert 'class="pager"' not in html and 'class="breadcrumb"' not in html
    assert '<title>Page not found</title>' in html
    assert 'katex' not in html
    # the default content: the message, the search box, the sections (their index page first)
    assert '<h1>Page not found</h1>' in html and 'id="not-found-query"' in html
    assert re.findall(r'<li><a href="([^"]*)">([^<]*)</a></li>', html) == [
        ('/docs/index.html', 'Home'), ('/docs/01_start/index.html', 'Get started'),
        ('/docs/02_guides/01_write/index.html', 'Guides'), ('/docs/03_reference/01_settings/index.html', 'Reference')]
    # out of the menu, the order of the pages and structure/
    assert all(entry['path'] != '404.html' for entry in toc_of(site))
    structure = json.loads((site / 'structure/structure.json').read_text(encoding='utf-8'))
    assert all(entry['filename'] != '404.html' or entry['dir'] for entry in structure)
    # the other pages keep their relative links
    page = (site / '01_start/01_install/index.html').read_text(encoding='utf-8')
    assert 'href="../../theme/css/docs.css"' in page and 'data-root="../../"' in page
    assert 'noindex' not in page and 'data-pagefind-body' in page and 'class="pager"' in page


def test_a_full_url_as_base(project):
    site = build(project, base_url='https://example.org/proj/')
    assert 'href="https://example.org/proj/theme/css/docs.css"' in (site / '404.html').read_text(encoding='utf-8')


def test_a_page_of_the_project_replaces_the_content_of_the_theme(project):
    (project / 'src/404.md.j2').write_text(
        '---\ntitle: Lost\n---\n\n# Lost in {{ docs.name if docs is defined else "the docs" }}\n\n'
        'Back to [the start]({{ pathToRoot }}01_start/index.html). Euler: \\(e^{i\\pi} = -1\\).\n',
        encoding='utf-8')
    site = build(project, base_url='/')
    html = (site / '404.html').read_text(encoding='utf-8')
    assert '<title>Lost</title>' in html
    assert '<h1>Lost in the docs</h1>' in html and 'href="/01_start/index.html"' in html
    assert 'Page not found' not in html and 'not_found.js' not in html
    assert 'href="/theme/libs/katex/katex.min.css"' in html          # its formula loads KaTeX
    assert all(entry['path'] != '404.html' for entry in toc_of(site))  # still no page of the menu
    # without base_url, it is a page as any other (as before)
    site = build(project)
    assert any(entry['path'] == '404.html' for entry in toc_of(site))


def test_a_page_of_the_project_in_lhtml(project):
    (project / 'src/404.html.j2').write_text('= Nothing here\n\nSee link::{{ pathToRoot }}index.html[the home page].\n',
                                             encoding='utf-8')
    site = build(project, base_url='/docs/')
    html = (site / '404.html').read_text(encoding='utf-8')
    assert re.search(r'<h1[^>]*>Nothing here</h1>', html), html
    assert 'href="/docs/index.html"' in html and 'the home page' in html


# ---- in Chromium ---------------------------------------------------------------------

browser_test = pytest.mark.skipif(os.environ.get('LHTML_BROWSER_TEST') != '1',
                                  reason='Set LHTML_BROWSER_TEST=1 for Chromium')


class Server(http.server.SimpleHTTPRequestHandler):
    """The site under /docs/, and 404.html (status 404) for a URL that leads nowhere,
    as GitHub Pages or a web server configured for it serve it."""
    def log_message(self, *args):
        pass

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        local = Path(self.directory) / path[len('/docs/'):] if path.startswith('/docs/') else None
        if local is not None and local.is_dir():
            local = local / 'index.html'
        if local is not None and local.is_file():
            self.path = '/' + local.relative_to(self.directory).as_posix()
            return super().send_head()
        body = (Path(self.directory) / '404.html').read_bytes()
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return None


@browser_test
def test_the_404_page_works_at_any_depth(project):
    playwright = pytest.importorskip('playwright.sync_api')
    site = build(project, base_url='/docs/')
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Server, directory=str(site)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}/docs/'
    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            errors, failed = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('requestfailed', lambda r: failed.append(r.url))
            page.on('response', lambda r: r.status >= 400 and r.request.resource_type != 'document'
                    and failed.append(r.url))
            for url in (base + 'a/b/c/', base + 'nothing.html', base + 'x/y/z/w/index.html'):
                response = page.goto(url)
                assert response.status == 404
                # its stylesheets and scripts are loaded: the theme styles it, the menu is built
                assert page.evaluate("() => getComputedStyle(document.querySelector('.topbar')).position") \
                    in ('sticky', 'fixed')
                assert page.eval_on_selector_all('#toc a.nav-link', 'els => els.length') == len(toc_of(site))
                hrefs = page.eval_on_selector_all('#toc a.nav-link', 'els => els.map(a => a.href)')
                assert all(h.startswith(base) for h in hrefs), hrefs
                assert page.eval_on_selector_all('.pager a', 'els => els.length') == 0
                assert page.is_hidden('.not-found-suggestion')
            assert failed == [] and errors == []
            # the closest page of the menu to the URL asked for
            page.goto(base + 'guides/figure/')
            assert page.is_visible('.not-found-suggestion')
            assert page.text_content('.not-found-suggestion a') == 'Figures'
            assert page.get_attribute('.not-found-suggestion a', 'href') == '/docs/02_guides/02_figures/index.html'
            assert page.input_value('#not-found-query') == 'guides figure'
            page.click('.not-found-suggestion a')
            page.wait_for_url(base + '02_guides/02_figures/index.html')
            assert errors == []
            browser.close()
    finally:
        server.shutdown()
