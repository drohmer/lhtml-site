"""Formulas holding `{#` (LaTeX colors) kept from Jinja: lhtml_site/math_raw.py."""
from pathlib import Path
import subprocess
import sys

import yaml

from lhtml_site.math_raw import protect

REPO = Path(__file__).resolve().parents[1]


def test_a_formula_with_a_color_is_kept_from_jinja():
    text = r'a \(\textcolor{#d62728}{x}\) b \[\color{#1f4fd6} y\] c'
    assert protect(text) == (r'a {% raw %}\(\textcolor{#d62728}{x}\){% endraw %} b '
                             r'{% raw %}\[\color{#1f4fd6} y\]{% endraw %} c')


def test_other_formulas_and_jinja_are_left_as_they_are():
    for text in (r'\( n = {{ params.n }} \) and {{ title }}',      # a variable used on purpose
                 r'\( x^2 \) {# a comment #}',
                 'code::[]\n\\(\\textcolor{#ff0000}{x}\\)\ncode::[-]',   # a code block holds no formula
                 r'`\(\textcolor{#ff0000}{x}\)`'):                    # nor inline code
        assert protect(text) == text


def test_a_formula_already_in_a_raw_block_is_left_as_it_is():
    text = '{% raw %}\n\\(\\textcolor{#d62728}{x}\\)\n{%- endraw %} then \\(\\color{#000} y\\)'
    assert protect(text) == ('{% raw %}\n\\(\\textcolor{#d62728}{x}\\)\n{%- endraw %} then '
                             '{% raw %}\\(\\color{#000} y\\){% endraw %}')


def test_a_page_with_colored_formulas_builds(tmp_path):
    """End to end: without the stage, the {# of the first formula opens a Jinja comment that
    swallows the page up to its end (a build error); with it, the formulas reach the page."""
    src = tmp_path / 'src/01_a'
    src.mkdir(parents=True)
    (src / 'index.html.j2').write_text(
        '= Colors\n\n'
        '\\(\\textcolor{#d62728}{a} + \\textcolor{#1f4fd6}{b}\\)\n\n'
        'Page {{ pageID }}\n', encoding='utf-8')
    (tmp_path / 'config.yaml').write_text(yaml.safe_dump({
        'source_directory': 'src', 'site_directory': 'site', 'plugin': [],
        'theme': str(REPO / 'src/lhtml_site/themes/slides')}))
    result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', str(tmp_path / 'config.yaml')],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    html = (tmp_path / 'site/01_a/index.html').read_text(encoding='utf-8')
    assert 'Page 0' in html                        # Jinja still runs on the rest of the page
    assert '{% raw %}' not in html
    assert 'katex' in html or r'\textcolor{#d62728}' in html
    # the source is untouched: the stage writes the copy in the site
    assert '{% raw %}' not in (src / 'index.html.j2').read_text(encoding='utf-8')
