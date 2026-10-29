"""KaTeX on the pages that need it only: page.math (lhtml_site/pages.py, source_scan.has_math).

The themes load katex.min.css, katex.min.js and auto-render.min.js when the page writes
mathematics outside code (\\( \\), \\[ \\], $$ $$), or when its settings say `math: true`;
`math: false` drops them from a page that writes some.
"""
import subprocess
import sys
from pathlib import Path

import jinja2
import pytest
import yaml

from lhtml_site import source_scan
from lhtml_site.pages import Page, Source

REPO = Path(__file__).resolve().parents[1]
GENERATE = [sys.executable, str(REPO / 'generate.py')]


@pytest.mark.parametrize('text, markup, expected', [
    (r'A formula \(e^{i\pi} + 1 = 0\).', 'lhtml', True),
    (r'\[ f(x) = x^2 \]', 'markdown', True),
    ('$$\nx^2\n$$\n', 'markdown', True),
    ('Display $$x^2$$ inline.', 'lhtml', True),
    ('No mathematics here.', 'lhtml', False),
    ('It costs 5$ and 6$, or $5 and $6.', 'markdown', False),          # a single $ is no delimiter
    ('A price $x$ is not KaTeX for the themes.', 'markdown', False),
    ('```\n\\(x\\) $$y$$\n```\n', 'markdown', False),                    # fenced code
    ('code::[latex]\n\\(x\\) $$y$$\ncode::[-]\n', 'lhtml', False),       # LHTML code block
    ('Write `\\(x\\)` or `$$y$$`.', 'markdown', False),                  # inline code
    ('<!-- \\(x\\) $$y$$ -->', 'lhtml', False),                          # comment
    ('{{ "$$y$$" }}', 'lhtml', False),                                   # Jinja
    ('$$ $$', 'markdown', False),                                        # empty
    ('---\ntitle: "$$x$$"\n---\n# Page\n', 'markdown', False),           # front matter
])
def test_has_math(text, markup, expected):
    assert source_scan.has_math(source_scan.Scan(text, markup)) is expected


def page_of(tmp_path, text, name='index.md.j2', config=None):
    (tmp_path / name).write_text(text, encoding='utf-8')
    return Page(Source(None, tmp_path), '', name, config=config or {})


@pytest.mark.parametrize('text, config, expected', [
    (r'# A \(x\)', {}, True),
    ('# A', {}, False),
    ('---\nmath: true\n---\n# A', {}, True),                  # math from an include or a macro
    ('---\nmath: false\n---\n# A \\(x\\)', {}, False),
    ('# A', {'math': True}, True),                           # config.yaml of the directory
    ('---\nmath: false\n---\n# A', {'math': True}, False),   # the page has the last word
])
def test_the_setting_overrides_the_detection(tmp_path, text, config, expected):
    assert page_of(tmp_path, text, config=config).math is expected


KATEX = ['katex.min.css', 'katex.min.js', 'auto-render.min.js']


def katex_files(html):
    return [name for name in KATEX if name in html]


@pytest.mark.parametrize('name', ['webpage-frame', 'slides', 'slides-pdf', 'docs'])
def test_each_template_loads_katex_when_page_math_is_true(name):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(REPO / 'src/lhtml_site/themes' / name / 'template'))
    template = env.get_template('base.html')
    assert katex_files(template.render(page={'math': True}, pathToRoot='', pageID=1)) == KATEX
    assert katex_files(template.render(page={'math': False}, pathToRoot='', pageID=1)) == []


def init(directory, theme):
    subprocess.run(GENERATE + ['init', str(directory), '--theme', theme], check=True, capture_output=True)


def build(project):
    result = subprocess.run(GENERATE + ['--strict'], cwd=project, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return project / '.site'


def with_front_matter(path, settings):
    """Give the page at `path` the front matter `settings`, merged with its own."""
    text = path.read_text(encoding='utf-8')
    head = {}
    if text.startswith('---\n'):
        end = text.index('\n---', 4)
        head, text = yaml.safe_load(text[4:end]) or {}, text[end + 4:].lstrip('\n')
    path.write_text('---\n' + yaml.safe_dump({**head, **settings}) + '---\n' + text, encoding='utf-8')


# (theme, the source of a page of its starter with mathematics)
STARTERS = [
    ('webpage-frame', '02_writing/index.html.j2'),
    ('slides', '02_text/index.html.j2'),
    ('docs', '01_start/02_first-page/index.md.j2'),
]


@pytest.mark.parametrize('theme, with_math', STARTERS, ids=[s[0] for s in STARTERS])
def test_the_built_pages_load_katex_when_they_have_mathematics(tmp_path, theme, with_math):
    project = tmp_path / 'p'
    init(project, theme)
    sources = project / 'src'
    plain = sources / '09_plain' / ('index.md.j2' if with_math.endswith('.md.j2') else 'index.html.j2')
    plain.parent.mkdir()
    plain.write_text('# Plain\n\nNo formula: 5$ and 6$.\n' if plain.suffixes[0] == '.md'
                     else '= Plain\n\nNo formula: 5$ and 6$.\n', encoding='utf-8')
    pages = {'math': (sources / with_math, with_math[:-len('.j2')].replace('.md', '.html')),
             'plain': (plain, '09_plain/index.html')}

    def katex_of(site):
        return {key: katex_files((site / html).read_text(encoding='utf-8')) for key, (_, html) in pages.items()}

    site = build(project)
    assert katex_of(site) == {'math': KATEX, 'plain': []}
    assert (site / 'theme/libs/katex/katex.min.js').is_file()        # still copied with the theme

    # the front matter overrides the detection, both ways
    with_front_matter(pages['math'][0], {'math': False})
    with_front_matter(pages['plain'][0], {'math': True})
    assert katex_of(build(project)) == {'math': [], 'plain': KATEX}
