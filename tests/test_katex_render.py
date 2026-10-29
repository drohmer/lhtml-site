"""The formulas rendered at build time (lhtml_site/katex_render.py).

A page with formulas ships the KaTeX HTML + MathML and katex.min.css, no KaTeX
script; code is left as written; a formula KaTeX cannot read is shown in red
(katex-error) and makes a warning naming the page; without QuickJS the
browser renders the formulas, as with `katex: {render: browser}`.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import jinja2
import pytest

from lhtml_site import katex_render
from lhtml_site.configuration import ConfigError, load_config

REPO = Path(__file__).resolve().parents[1]
GENERATE = [sys.executable, str(REPO / 'generate.py')]
THEMES = REPO / 'src/lhtml_site/themes'
SCRIPT = THEMES / 'docs' / katex_render.SCRIPT
needs_quickjs = pytest.mark.skipif(importlib.util.find_spec('quickjs') is None,
                                   reason='QuickJS is not installed (lhtml-site[math])')


@pytest.mark.parametrize('text, expected', [
    (r'a \(x\) b', [(2, 7, 'x', False)]),
    (r'\[ y \]', [(0, 7, ' y ', True)]),
    ('$$z$$ and $$w$$', [(0, 5, 'z', True), (10, 15, 'w', True)]),
    (r'\(\text{\)}\)', [(0, 13, r'\text{\)}', False)]),        # the closing one is outside braces
    (r'\(a \) b\)', [(0, 6, 'a ', False)]),
    (r'\(open', []),                                            # never closed: text
    ('5$ and 6$, $x$', []),                                     # a single $ is no delimiter
])
def test_the_formulas_are_found_as_auto_render_finds_them(text, expected):
    assert katex_render.find_formulas(text) == expected


class Fake:
    """A renderer that says what it was asked to render."""

    def render(self, tex, display):
        return f'<span class="katex">{"D" if display else "I"}[{tex}]</span>'


@pytest.mark.parametrize('html, expected', [
    (r'<p>a \(x\) b</p>', '<p>a <span class="katex">I[x]</span> b</p>'),
    (r'<p>\(a &lt; b\)</p>', '<p><span class="katex">I[a < b]</span></p>'),     # the text, decoded
    (r'<p>\(a <em>b</em> c\)</p>', r'<p>\(a <em>b</em> c\)</p>'),               # not across elements
    (r'<pre><code>\(x\)</code></pre>', r'<pre><code>\(x\)</code></pre>'),
    (r'<p><code>$$x$$</code> \(y\)</p>', '<p><code>$$x$$</code> <span class="katex">I[y]</span></p>'),
    (r'<script>let s = "\(x\)";</script>', r'<script>let s = "\(x\)";</script>'),
    (r'<style>p::after { content: "\(x\)" }</style>', r'<style>p::after { content: "\(x\)" }</style>'),
    (r'<textarea>\(x\)</textarea>', r'<textarea>\(x\)</textarea>'),
    (r'<div class="a nohighlight"><p>\(x\)</p></div><p>\(y\)</p>',
     r'<div class="a nohighlight"><p>\(x\)</p></div><p><span class="katex">I[y]</span></p>'),
    (r'<span class="katex">\(x\)</span>', r'<span class="katex">\(x\)</span>'),
    (r'<head><title>\(x\)</title></head><body><img alt="\(x\)" src="a.png">\[y\]</body>',
     r'<head><title>\(x\)</title></head><body><img alt="\(x\)" src="a.png"><span class="katex">D[y]</span></body>'),
    ('<!-- $$x$$ --><p>$$y$$</p>', '<!-- $$x$$ --><p><span class="katex">D[y]</span></p>'),
    ('<p>caf&eacute; $$x$$\nline 2</p><br/>\\(z\\)',
     '<p>caf&eacute; <span class="katex">D[x]</span>\nline 2</p><br/><span class="katex">I[z]</span>'),
])
def test_only_the_text_outside_code_is_rendered(html, expected):
    assert katex_render.render_page(html, Fake())[0] == expected


@needs_quickjs
def test_quickjs_runs_the_katex_of_the_themes(tmp_path):
    renderer = katex_render.Renderer(SCRIPT, {'throwOnError': False, 'macros': {r'\RR': r'\mathbb{R}'}},
                                     tmp_path / 'katex.json')
    html, errors = katex_render.render_page(r'<p>\(x \in \RR\)</p><p>\(\frac{1}\)</p>', renderer)
    assert html.count('class="katex"') == 1 and 'mathbb' in html
    assert '<math xmlns="http://www.w3.org/1998/Math/MathML">' in html
    assert 'class="katex-error"' in html
    assert len(errors) == 1 and errors[0][0] == r'\frac{1}' and 'ParseError' in errors[0][1]


@pytest.mark.parametrize('value, problem', [
    ({}, None),
    ({'render': 'browser', 'macros': {r'\RR': r'\mathbb{R}'}}, None),
    ({'render': 'server'}, "render must be 'build' or 'browser'"),
    ({'renders': 'build'}, "unknown key 'renders'"),
    ({'macros': {'RR': 'x'}}, 'macros must map'),
    ({'macros': [r'\RR']}, 'macros must map'),
    ('build', "'katex' must be a mapping"),
])
def test_the_configuration_is_checked(tmp_path, value, problem):
    config = tmp_path / 'configure.yaml'
    config.write_text(json.dumps({'katex': value}), encoding='utf-8')
    if problem is None:
        assert load_config(config)[0].katex == value
    else:
        with pytest.raises(ConfigError, match=problem.replace('(', r'\(')):
            load_config(config)


@pytest.mark.parametrize('name', ['webpage-frame', 'slides', 'slides-pdf', 'docs'])
def test_each_template_loads_the_css_only_when_the_formulas_are_rendered_at_build(name):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(THEMES / name / 'template'))
    template = env.get_template('base.html')
    built = template.render(page={'math': True, 'math_render': 'build'}, pathToRoot='', pageID=1)
    assert 'katex.min.css' in built and 'katex.min.js' not in built and 'auto-render' not in built
    options = json.dumps({'throwOnError': False, 'macros': {r'\RR': r'\mathbb{R}'}})
    browser = template.render(page={'math': True, 'math_render': 'browser', 'katex_options': options},
                              pathToRoot='', pageID=1)
    assert 'katex.min.js' in browser and 'auto-render.min.js' in browser
    assert '&#34;throwOnError&#34;: false' in browser and '\\\\mathbb{R}' in browser     # escaped in onload=""


PAGE = '''---
title: Formulas
section: Get started
---

# Formulas

Inline \\(a^2 + b^2 = c^2\\) and displayed:

\\[ \\int_0^1 x \\, dx = \\frac{1}{2} \\]

$$\\RR^3$$

Code stays: `\\(x\\)` and

```cpp
// \\(y\\) $$z$$
```
'''
BROKEN = '\nAnd a mistake: \\(\\frac{1}\\)\n'


def docs_project(tmp_path, page=PAGE, config=None):
    project = tmp_path / 'p'
    subprocess.run(GENERATE + ['init', str(project), '--theme', 'docs'], check=True, capture_output=True)
    (project / 'src/01_start/09_formulas').mkdir()
    (project / 'src/01_start/09_formulas/index.md.j2').write_text(page, encoding='utf-8')
    configure = project / 'configure.yaml'
    configure.write_text(configure.read_text(encoding='utf-8')
                         + 'katex:\n  macros: {"\\\\RR": "\\\\mathbb{R}"}\n' + (config or ''), encoding='utf-8')
    return project


def build(project, *options, without_quickjs=False, check=True):
    command = GENERATE + ['-v', *options]
    if without_quickjs:         # QuickJS hidden from the build: importlib.util.find_spec says None
        command = [sys.executable, '-c', 'import runpy, sys; sys.modules["quickjs"] = None; '
                   f'sys.argv = {[str(REPO / "generate.py"), "-v", *options]!r}; '
                   f'runpy.run_path({str(REPO / "generate.py")!r}, run_name="__main__")']
    result = subprocess.run(command, cwd=project, capture_output=True, text=True)
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


def page_html(project):
    return (project / '.site/01_start/09_formulas/index.html').read_text(encoding='utf-8')


@needs_quickjs
def test_a_page_with_formulas_ships_their_html_and_the_css_only(tmp_path):
    project = docs_project(tmp_path)
    result = build(project, '--strict')
    html = page_html(project)
    assert html.count('<span class="katex-display">') == 2 and html.count('<span class="katex">') == 3
    assert 'katex.min.css' in html and 'katex.min.js' not in html and 'auto-render' not in html
    assert 'mathbb' in html                                     # the macro of the configuration
    assert '<code>\\(x\\)</code>' in html                        # code as written
    assert '// \\(y\\) $$z$$' in html
    assert 'katex-error' not in html
    assert 'Formulas: 4 rendered at build (4 by KaTeX' in result.stdout     # 1 in the starter
    # a page without formulas is not touched, and loads nothing of KaTeX
    plain = (project / '.site/index.html')
    assert 'katex' not in plain.read_text(encoding='utf-8') if plain.is_file() else True


@needs_quickjs
def test_an_invalid_formula_is_shown_in_red_and_warned_with_its_page(tmp_path):
    project = docs_project(tmp_path, PAGE + BROKEN)
    result = build(project)
    html = page_html(project)
    assert html.count('class="katex-error"') == 1
    assert html.count('<span class="katex">') == 3              # the others are rendered
    line = (PAGE + BROKEN).splitlines().index('And a mistake: \\(\\frac{1}\\)') + 1
    assert f'src/01_start/09_formulas/index.md.j2:{line}: warning: KaTeX: ParseError' in result.stdout
    strict = build(project, '--strict', check=False)
    assert strict.returncode != 0 and '1 warning(s) with --strict' in strict.stdout + strict.stderr


@needs_quickjs
def test_the_formulas_come_from_the_cache_the_next_time(tmp_path):
    project = docs_project(tmp_path)
    build(project)
    cache_path = project / katex_render.CACHE
    cache = json.loads(cache_path.read_text(encoding='utf-8'))
    assert len(cache) == 4                          # 3 of this page, 1 of the starter
    # the next build asks KaTeX for nothing: what the cache says is what the page gets
    key = next(key for key, html in cache.items() if 'msup' in html)        # a^2 + b^2 = c^2
    cache[key] = '<span class="katex">FROM THE CACHE</span>'
    cache_path.write_text(json.dumps(cache), encoding='utf-8')
    result = build(project)
    assert 'Formulas: 4 rendered at build (0 by KaTeX' in result.stdout
    assert 'FROM THE CACHE' in page_html(project)
    # other options are another key: the formulas are rendered again
    configure = project / 'configure.yaml'
    configure.write_text(configure.read_text(encoding='utf-8').replace('mathbb', 'mathbf'), encoding='utf-8')
    result = build(project)
    assert 'Formulas: 4 rendered at build (4 by KaTeX' in result.stdout
    assert 'FROM THE CACHE' not in page_html(project) and 'mathbf' in page_html(project)
    assert len(json.loads(cache_path.read_text(encoding='utf-8'))) == 4      # the formulas of this build


@pytest.mark.parametrize('how', ['without QuickJS', 'render: browser'])
def test_otherwise_the_browser_renders_the_formulas(tmp_path, how):
    project = docs_project(tmp_path, config='  render: browser\n' if how == 'render: browser' else None)
    result = build(project, '--strict', without_quickjs=how == 'without QuickJS')
    html = page_html(project)
    assert 'class="katex"' not in html and '\\(a^2 + b^2 = c^2\\)' in html
    assert 'katex.min.css' in html and 'katex.min.js' in html and 'auto-render.min.js' in html
    assert '&#34;\\\\RR&#34;: &#34;\\\\mathbb{R}&#34;' in html        # the macros, for auto-render
    info = [line for line in result.stdout.splitlines() if line.startswith('Formulas rendered in the browser')]
    if how == 'without QuickJS':
        assert info == ['Formulas rendered in the browser: QuickJS is not installed: '
                        'pip install "lhtml-site[math]"']
    else:
        assert info == []
    assert not (project / katex_render.CACHE).exists()


def test_without_quickjs_nothing_is_said_on_a_site_without_formulas(tmp_path):
    project = tmp_path / 'p'
    subprocess.run(GENERATE + ['init', str(project), '--theme', 'docs'], check=True, capture_output=True)
    for page in (project / 'src').rglob('*.md.j2'):
        page.write_text(page.read_text(encoding='utf-8').replace('\\(', '(').replace('\\)', ')'),
                        encoding='utf-8')
    result = build(project, without_quickjs=True)
    assert 'Formulas rendered in the browser' not in result.stdout
