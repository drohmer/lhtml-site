# The docs theme

A documentation site: a top bar with the search box, a side menu by section and group, an
"On this page" column, a breadcrumb, previous / next links, light and dark modes, a drawer
menu on phones (below 860 px) and figures that open full size.

```sh
lhtml-site init my-docs --theme docs    # a project with a few pages to start from
```

## Pages

Each page names its place in the menu in its front matter:

```yaml
---
title: Draw a mesh
section: How-to          # the section of the menu
group: Shapes            # optional: a group inside the section
description: One line.   # optional: <meta name="description">
wide: true               # optional: a wider column (--wide-w), for tables
math: true               # optional: load KaTeX (default: when the page writes formulas)
---
```

- The menu lists the sections in the order of the setting `menu.sections`, then the others in
  the order of their first page. Inside a section, the pages keep the order of the site
  (the deck, or the order of the paths). The pages of a group must be contiguous.
- A page with no section is listed at the top of the menu; the first page of the site is
  labelled "Home".
- The page `<dir>/index.html` of a section is its index page: the title of the section in the
  menu links to it, and the menu lists it first, as "Overview". Without a deck, name the
  section directories so that they sort in order (`01_start`, `02_guides`): the
  `index.md.j2` of a directory comes before its pages.
- The h2 of a page, and any element with an `id` and a `data-toc` attribute (its label), are
  listed in "On this page".
- A figure that opens full size on click:
  `<figure class="figure"><a class="figure-zoom" href="a.svg"><img src="a.svg" alt="..."></a><figcaption>...</figcaption></figure>`.
  The width of the image can be set by the CSS variable `--fig-w` (style attribute).
- Formulas: `\(...\)`, `\[...\]` and `$$...$$`, rendered by KaTeX. Only the pages that write
  one outside code load KaTeX (about 280 KB); a page whose formulas come from an included
  template or a macro says `math: true`, and `math: false` keeps KaTeX off a page.

## Settings

All optional, under the `docs` keyword of `configure.yaml`:

```yaml
keywords:
  docs:
    name: CGP                        # top bar (default 'Docs')
    sub: docs                        # smaller, after the name
    title: CGP docs                  # after the page title in the browser tab (not on the first page)
    logo: assets/logo.svg            # an image, relative to the root of the site
    logo_svg: '<svg ...>...</svg>'   # or inline SVG markup (it can use currentColor: the accent color)
    repo_url: https://github.com/me/project   # a repository link (GitHub icon) in the top bar
    repo_label: The project on GitHub
    footer: Built with lhtml-site.   # no footer without it
    search_placeholder: Search the docs
    lang: en
    storage: docs                    # prefix of the localStorage keys <storage>-theme, <storage>-menu-open
    section_index:                   # breadcrumb: the section and group link to these pages
      How-to: how-to/index.html      # (group anchor: the group name in lower case, with hyphens)
    css: [theme/css/extra.css]       # stylesheets loaded after the docs.css of the theme
    js: [theme/js/extra.js]          # scripts run after the site.js of the theme
    menu:
      sections: [Get started, How-to, Reference]   # order of the sections
      home_label: Home
      index_label: Overview
      section:
        Reference:
          open: false                # starts closed, unless the current page is in it
          groups: closed             # its groups start closed (lighter style); default open
          group_link_class: mono     # an extra class on the links of its groups
          plain_groups: [Other]      # groups whose links do not get that class
```

## The 404 page

With `base_url` in `configure.yaml` (where the site is served: `/`, `/my-project/` for a GitHub
project page, or a whole URL such as `https://example.org/docs/`), the build writes `404.html`
at the root of the site:

```yaml
base_url: /cgp-doc/
```

- A server shows it at the URL that was asked for, at any depth (`/cgp-doc/a/b/c/`): its links
  start from `base_url` (`/cgp-doc/theme/css/docs.css`) instead of being relative. The other
  pages keep their relative links. Without `base_url`, no `404.html` is written.
- It holds a message, a search box, the sections of the menu and, when one is close enough,
  the page of the menu that looks like the URL asked for ("Did you mean ...?", `js/not_found.js`).
- A page `404.md.j2` (or `404.html.j2`) at the top of the sources replaces that content; it is
  rendered the same way, so write its links with `{{ pathToRoot }}`.
- It is not in the menu, the order of the pages, previous / next or the search index
  (`data-pagefind-ignore`), and has `<meta name="robots" content="noindex">`. A template sees
  it as `page.not_found`.
- GitHub Pages and Netlify serve `404.html` by themselves; for nginx:
  `error_page 404 /cgp-doc/404.html;`, for Apache: `ErrorDocument 404 /cgp-doc/404.html`.

## An overlay

A project restyles or extends the theme without copying it: copy the bundled theme into a
directory of the project, add its own files over it, and point `theme:` at that directory.
For example `renderers/lhtml/build.py` of the CGP documentation copies
`lhtml_site/themes/docs`, then its own `css/cgp.css` and `js/cgp.js`, and the settings load
them (`css:`, `js:`).

- **Styles**: every color and size of `css/docs.css` is a variable on `:root`
  (`--accent`, `--bg`, `--text`, `--content-w`, `--wide-w`, `--sidebar-w`,
  `--figure-card`...), with a dark variant on `:root[data-theme="dark"]`. An overlay
  stylesheet overrides the variables first, then adds its own rules.
- **Scripts**: the scripts of `js:` run after `site.js` (all are deferred, in order) and find
  `window.docsTheme = {root, storage, $, $$}`: the path to the root of the site, the prefix of
  the localStorage keys, and two query helpers.

## Search

The search box uses [Pagefind](https://pagefind.app). Its index is built after the site:

```sh
lhtml-site
python -m pip install 'pagefind[extended]'
python -m pagefind --site .site
```

The theme marks the article as the indexed content (`data-pagefind-body`) and its section as
a filter (`data-pagefind-meta`); the breadcrumb, the pager and the footer are not indexed.
The search works when the site is served over http, not from a file opened on the disk.
`/` and Ctrl+K (Cmd+K) go to the search box, the arrows and Enter choose a result.

## Files

`template/base.html`, `css/docs.css`, `js/menu.js` (menu and previous / next), `js/site.js`
(everything else), `template/404.html` and `js/not_found.js` (the 404 page), `css/font.css` with `fonts/source_code_pro` (the monospace font; the text
uses the system font) and `libs/katex`.
