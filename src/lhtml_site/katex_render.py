"""The formulas rendered at build time by the KaTeX of the theme.

A core stage, after LHTML, for the pages that write mathematics (`page.math`):
the formulas of the generated HTML become KaTeX HTML + MathML, as rehype-katex
renders them, and the page loads katex.min.css only (its fonts come through
@font-face, when a formula uses them). No KaTeX JavaScript on the page, no
flash of the TeX source, and the layout report and the PDF export have no
script to wait for.

The formulas are found as KaTeX auto-render finds them in the browser: in the
text of the page (not in its tags or attributes), between the delimiters
`$$ $$`, `\\( \\)` and `\\[ \\]` (those source_scan.has_math detects), the
closing one outside braces, and never inside pre, code, script, style,
textarea, noscript, option, the head, or an element of class `katex` or
`nohighlight`.

KaTeX runs in QuickJS (the package `quickjs`, extra lhtml-site[math]): the
script of the theme, theme/libs/katex/katex.min.js, unchanged, so that the
HTML always matches the katex.min.css of the theme. The configuration says

    katex:
      render: build          # or browser: auto-render on the page, as before
      macros: {'\\RR': '\\mathbb{R}'}

Without QuickJS (or with a theme that ships no KaTeX) the pages render their
formulas in the browser, as with `render: browser`: the template loads the
script when `page.math_render` is not 'build'. Each formula rendered is kept
in .verification/katex.json, by its TeX, display mode, options and the hash
of the KaTeX script.
"""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re

from lhtml_site import filesystem
from lhtml_site.doctor import installation

SCRIPT = Path('libs/katex/katex.min.js')        # in the theme
CACHE = Path('.verification/katex.json')        # next to the configuration
RENDERS = ('build', 'browser')

# The delimiters of auto-render that the generator detects (source_scan.has_math),
# in the order auto-render tries them: (left, right, display)
DELIMITERS = (('$$', '$$', True), ('\\(', '\\)', False), ('\\[', '\\]', True))
IGNORED_TAGS = frozenset(('head', 'title', 'script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'))
IGNORED_CLASSES = frozenset(('katex', 'nohighlight'))
VOID_TAGS = frozenset(('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
                       'param', 'source', 'track', 'wbr'))
ERROR_TITLE = re.compile(r'class="katex-error" title="([^"]*)"')


def check_config(value):
    """The configuration key `katex:` checked: {render, macros}. Returns the
    error message, None when it is valid."""
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        return "'katex' must be a mapping (render:, macros:)"
    unknown = sorted(set(value) - {'render', 'macros'})
    if unknown:
        return f"'katex': unknown key '{unknown[0]}' (render:, macros:)"
    if value.get('render', 'build') not in RENDERS:
        return f"'katex': render must be 'build' or 'browser'; got {value['render']!r}"
    macros = value.get('macros', {})
    if not isinstance(macros, dict) or any(not isinstance(k, str) or not k.startswith('\\')
                                           or not isinstance(v, str) for k, v in macros.items()):
        return "'katex': macros must map a command ('\\\\RR') to its TeX ('\\\\mathbb{R}')"
    return None


def options(meta):
    """The options of KaTeX the configuration gives, the same at build and in the browser."""
    return {'throwOnError': False, 'macros': dict((meta.get('katex') or {}).get('macros') or {})}


def install_command():
    if installation() == 'pipx':
        return 'pipx inject lhtml-site quickjs'
    return 'pip install "lhtml-site[math]"'


def mode(meta):
    """'build' when the formulas are rendered at build time, else 'browser',
    and why: (mode, reason or None)."""
    if (meta.get('katex') or {}).get('render', 'build') == 'browser':
        return 'browser', None
    if not (Path(meta['theme']) / SCRIPT).is_file():
        return 'browser', f'the theme has no {SCRIPT.as_posix()}'
    if importlib.util.find_spec('quickjs') is None:
        return 'browser', f'QuickJS is not installed: {install_command()}'
    return 'build', None


def prepare(meta, log):
    """Say to the templates how each page renders its formulas
    (`page.math_render`, `page.katex_options`), before Jinja."""
    entries = [entry for entry in meta.get('built') or [] if entry.get('math')]
    render, reason = mode(meta)
    meta['math_render'] = render
    if entries and reason:
        log.info(f'Formulas rendered in the browser: {reason}')
    browser_options = json.dumps(options(meta))
    for entry in entries:
        entry['math_render'] = render
        entry['katex_options'] = browser_options


def find_formulas(text):
    """The formulas of a text of the page as auto-render finds them:
    [(start, end, tex, display)], `start:end` the formula with its delimiters."""
    found, position = [], 0
    while True:
        starts = [(text.find(left, position), left, right, display) for left, right, display in DELIMITERS]
        starts = [s for s in starts if s[0] >= 0]
        if not starts:
            return found
        start, left, right, display = min(starts, key=lambda s: s[0])
        end = end_of_math(text, right, start + len(left))
        if end < 0:
            return found
        found.append((start, end + len(right), text[start + len(left):end], display))
        position = end + len(right)


def end_of_math(text, right, index):
    """Where `right` closes the formula that starts at `index`, outside braces
    and not escaped by a backslash (auto-render's findEndOfMath); -1 if nowhere."""
    level = 0
    while index < len(text):
        character = text[index]
        if level <= 0 and text.startswith(right, index):
            return index
        if character == '\\':
            index += 1
        elif character == '{':
            level += 1
        elif character == '}':
            level -= 1
        index += 1
    return -1


class TextSpans(HTMLParser):
    """The spans of the HTML of a page that are text where formulas are
    rendered: [(start, end)] offsets into the HTML, entities left as written."""

    def __init__(self, html):
        super().__init__(convert_charrefs=False)
        self.line_starts = [0]
        for line in html.splitlines(keepends=True):
            self.line_starts.append(self.line_starts[-1] + len(line))
        self.events = []        # (offset, text: whether it is text where formulas render)
        self.stack = []         # (tag, ignored)
        self.feed(html)
        self.close()
        self.events.append((len(html), False))

    def where(self):
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def ignored(self):
        return bool(self.stack) and self.stack[-1][1]

    def event(self, text):
        self.events.append((self.where(), text and not self.ignored()))

    def handle_starttag(self, tag, attrs):
        self.event(False)
        if tag in VOID_TAGS:
            return
        classes = set(next((value or '' for name, value in attrs if name == 'class'), '').split())
        self.stack.append((tag, self.ignored() or tag in IGNORED_TAGS or bool(classes & IGNORED_CLASSES)))

    def handle_startendtag(self, tag, attrs):
        self.event(False)

    def handle_endtag(self, tag):
        self.event(False)
        if any(open_tag == tag for open_tag, _ in self.stack):
            while self.stack.pop()[0] != tag:
                pass

    def handle_data(self, data):
        self.event(True)

    handle_entityref = handle_charref = handle_data

    def handle_comment(self, data):
        self.event(False)

    handle_decl = handle_pi = unknown_decl = handle_comment

    def spans(self):
        """The runs of text, merged across entities."""
        runs = []
        for (start, text), (end, _) in zip(self.events, self.events[1:]):
            if not text or start == end:
                continue
            if runs and runs[-1][1] == start:
                runs[-1] = (runs[-1][0], end)
            else:
                runs.append((start, end))
        return runs


class Renderer:
    """KaTeX in QuickJS, started at the first formula that is not in the cache."""

    def __init__(self, script, katex_options, cache_path):
        self.script = Path(script)
        self.options = katex_options
        self.version = hashlib.sha256(self.script.read_bytes()).hexdigest()[:16]
        self.cache_path = Path(cache_path)
        self.context = None
        self.used, self.made = {}, 0
        try:
            with open(self.cache_path, encoding='utf-8') as fid:
                self.cache = json.load(fid)
            if not isinstance(self.cache, dict):
                self.cache = {}
        except (OSError, ValueError):
            self.cache = {}

    def key(self, tex, display):
        data = json.dumps([tex, display, self.options, self.version], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def render(self, tex, display):
        key = self.key(tex, display)
        html = self.cache.get(key)
        if html is None:
            if self.context is None:
                import quickjs
                self.context = quickjs.Context()
                self.context.eval(self.script.read_text(encoding='utf-8'))
            settings = json.dumps({**self.options, 'displayMode': display})
            html = self.context.eval(f'katex.renderToString({json.dumps(tex)}, {settings})')
            self.made += 1
        self.used[key] = html
        return html

    def save(self, keep_all=False):
        """Write the cache: the formulas of this build (and the previous ones, `keep_all`: --only)."""
        cache = {**self.cache, **self.used} if keep_all else self.used
        if cache == self.cache:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix('.tmp')
        with open(temporary, 'w', encoding='utf-8', newline='\n') as fid:
            json.dump(cache, fid, ensure_ascii=False, indent=0, sort_keys=True)
        os.replace(temporary, self.cache_path)


def render_page(html, renderer):
    """The HTML of a page with its formulas rendered, and the errors of
    KaTeX: (html, [(tex, message)])."""
    parts, errors, position = [], [], 0
    for start, end in TextSpans(html).spans():
        text = html[start:end]
        for begin, finish, tex, display in find_formulas(text):
            source = unescape(tex)
            rendered = renderer.render(source, display)
            error = ERROR_TITLE.search(rendered)
            if error:
                errors.append((source, unescape(error.group(1))))
            parts += [html[position:start + begin], rendered]
            position = start + finish
    parts.append(html[position:])
    return ''.join(parts), errors


def line_of(tex, page):
    """The line of the source of `page` where `tex` is written (with its
    delimiters first: `\\frac{1}` is also the start of `\\frac{1}{2}`), None if not found."""
    try:
        text = Path(page['src']).read_text(encoding='utf-8')
    except (OSError, KeyError, TypeError):
        return None
    for left, right, _ in DELIMITERS + (('', '', None),):
        index = text.find(left + tex + right)
        if index >= 0:
            return text.count('\n', 0, index) + 1
    return None


def run(meta, log, failed=()):
    """Render the formulas of the pages built with `page.math_render` 'build'
    (not those that failed: `failed`, their site_html)."""
    if meta.get('math_render') != 'build':
        return
    entries = [entry for entry in meta.get('built') or []
               if entry.get('math_render') == 'build'
               and entry['dir'] + entry['filename'] not in failed]
    if not entries:
        return
    renderer = Renderer(Path(meta['theme']) / SCRIPT, options(meta), Path(meta['config_directory']) / CACHE)
    for entry in entries:
        path = Path(meta['site_directory']) / (entry['dir'] + entry['filename'])
        if not path.is_file():
            continue
        html = path.read_text(encoding='utf-8')
        try:
            output, errors = render_page(html, renderer)
        except Exception as exc:        # QuickJS that does not run KaTeX: the formulas stay as TeX
            log.warning(f'KaTeX: {type(exc).__name__}: {exc}', filesystem.shown(entry.get('src') or path))
            continue
        for tex, message in errors:
            line = line_of(tex, entry)
            place = filesystem.shown(entry.get('src') or path) + (f':{line}' if line else '')
            log.warning(f'KaTeX: {message}', place)
        if output != html:
            filesystem.write_file(path, output)
    renderer.save(keep_all=bool(meta.get('only')))
    log.detail(f'Formulas: {len(renderer.used)} rendered at build ({renderer.made} by KaTeX, '
               f'the others from the cache)')
