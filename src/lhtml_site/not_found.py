"""404.html: the page a server shows for a URL that leads nowhere.

A core stage, for a theme that declares the content of the page in its
manifest (lhtml_site/theme.py) and a site that says where it is served
(the configuration key `base_url`):

    not_found: 'theme/template/404.html'

The server shows 404.html at the URL that was asked for, at any depth
(/a/b/c/): the relative links of the other pages (pathToRoot) would lead
nowhere from there, so this page is rendered with pathToRoot = base_url,
its links starting at the root of the server.

The page is not one of the pages of the site: not in the menu, the order
of the pages, previous / next, structure/ or the search index. The theme
knows it by `page.not_found` (it writes <meta name="robots" content="noindex">
and leaves it out of the search). Its content is the template of the theme,
or the page 404.md.j2 (404.html.j2 in LHTML) at the top of the sources,
which takes its place; the theme's template finds the pages of the menu in
`site_pages`.
"""
import json

import lhtml

from lhtml_site import filesystem, front_matter, menu
from lhtml_site.pages import markup
from lhtml_site.source_scan import Scan, has_math, leading_settings
from lhtml_site.theme import of as theme_manifest

FILE = '404.html'
PAGE_TEMPLATES = ('404.md.j2', '404.html.j2')       # the page of the project that replaces the theme's
TITLE = 'Page not found'

WRAPPER = '''{{% set pageTitle = {title} %}}
{{% set tocTitle = {title} %}}
{settings}
{{% extends "{template}" %}}

{{% block {block} %}}
{content}
{{% endblock %}}
'''


def enabled(meta):
    """Whether the build writes 404.html: its theme has one, and it knows the base URL."""
    return bool(meta.get('base_url')) and bool(theme_manifest(meta).get('not_found'))


def is_page(page):
    """Whether a page of the sources is the 404 page of the project (not a page of the site)."""
    return page.source.name is None and page.directory == '' and page.template in PAGE_TEMPLATES


def project_page(meta):
    """The source of the 404 page of the project, or None."""
    for name in PAGE_TEMPLATES:
        path = meta['source_directory'] / name
        if path.is_file():
            return path
    return None


def run(meta, env):
    """Write 404.html into the site; `env`: the Jinja environment of the
    pages (lhtml_site/generate.py). Does nothing unless `enabled`."""
    if not enabled(meta):
        return None
    manifest = theme_manifest(meta)
    source = project_page(meta)
    settings, kind, content = {}, None, f'{{% include "{manifest["not_found"]}" %}}'
    leading = ''
    if source is not None:
        kind = markup(source.name)
        text, settings = front_matter.split(filesystem.read_text(source))
        leading = leading_settings(text)
        content = text[len(leading):]
        if kind == 'markdown':
            content = f'{{% filter markdown_page %}}\n{content}\n{{% endfilter %}}'
    title = str(settings.get('title') or TITLE)
    math = settings.get('math')
    page = {**settings, 'title': title, 'not_found': True,
            'math': bool(math) if math is not None else bool(source and has_math(Scan(text, kind)))}
    wrapper = WRAPPER.format(title=json.dumps(title, ensure_ascii=False), settings=leading, content=content,
                             template=manifest['template'], block=manifest['content_block'])
    base = meta['base_url']
    html = env.from_string(wrapper).render({
        **meta['keywords'], 'params': {}, 'page': page, 'pathToRoot': base, 'pageID': -1,
        'site_pages': menu.table_of_contents(meta, manifest)})
    if kind == 'lhtml':
        document = lhtml.parse(html, macros=meta.get('macros'), warn=False)
        html = lhtml.render(document, line_breaks=meta.get('line_breaks', False))
        for problem in document.problems:
            meta['log'].warning(f'{filesystem.shown(source)}: {problem}')
    path = meta['site_directory'] / FILE
    filesystem.write_file(path, html)
    return path
