# The docs theme

A documentation site: a top bar with the search box, a side menu by section and group, an
"On this page" column, a breadcrumb, previous / next links, light and dark modes, a drawer
menu on phones (below 860 px, its entries large enough for a finger), "On this page" as a
bar at the top of the content where the column is hidden (below 1180 px), and figures that
open full size.

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
- The menu and the previous / next links are written in each page by the build
  (`template/nav.html`): they work without JavaScript and for the crawlers. `js/menu.js` keeps
  the open / closed state the reader leaves to the sections and groups, and scrolls the menu to
  the current page. A build with `--only` warns when the menu changed (a title, a section): the
  pages it does not generate keep the previous one until the next full build.
- The breadcrumb above the title: the section links to its index page (`section_index`, else
  `<section>/index.html`), and is plain text when the section has none.
- The h2 of a page, and any element with an `id` and a `data-toc` attribute (its label), are
  listed in "On this page".
- Headings get readable ids, unique in their page: `## When something goes wrong` ->
  `#when-something-goes-wrong` (see "Heading ids" below).
- A figure that opens full size on click:
  `<figure class="figure"><a class="figure-zoom" href="a.svg"><img src="a.svg" alt="..."></a><figcaption>...</figcaption></figure>`.
  The width of the image can be set by the CSS variable `--fig-w` (style attribute).
- Formulas: `\(...\)`, `\[...\]` and `$$...$$`, rendered by KaTeX. Only the pages that write
  one outside code load KaTeX; a page whose formulas come from an included template or a
  macro says `math: true`, and `math: false` keeps KaTeX off a page. With `quickjs`
  installed (`lhtml-site[math]`) the build renders the formulas: the page loads
  `katex.min.css` only (its fonts when a formula uses them), not the about 280 KB of
  scripts, and shows no TeX source while it loads. Otherwise, or with
  `katex: {render: browser}` in `configure.yaml`, KaTeX renders them in the browser
  (`page.math_render` says which, for a template). Macros for both:
  `katex: {macros: {'\RR': '\mathbb{R}'}}` (README of lhtml-site, "Formulas").

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
    lang: en                         # <html lang>, and the language of the texts of the theme (en, fr)
    strings:                         # any text of the theme, over those of `lang` (template/strings.html)
      copy: Copy code
    storage: docs                    # prefix of the localStorage keys <storage>-theme, <storage>-menu-open
    section_index:                   # breadcrumb: the section and group link to these pages
      How-to: how-to/index.html      # (group anchor: the id of the group's heading there, its slug)
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

## Languages

`lang` names the language of the site: the `lang` attribute of the pages, and the texts the
theme writes itself (buttons, labels, the 404 page, "On this page", previous / next...). The
theme has them in English (`en`, the default, also for a language it does not know) and
French (`fr`; `fr-CA` reads `fr`). `strings` replaces any of them, key by key; the keys are
those of `template/strings.html`. The older settings `search_placeholder`, `repo_label`,
`menu.home_label` and `menu.index_label` keep the last word on their text.

```yaml
keywords:
  docs:
    lang: fr                         # the texts of the theme in French
    strings:
      search_placeholder: Rechercher dans la doc
      repository: Le dépôt
```

Keys: `skip_to_content`, `open_menu`, `search_placeholder`, `search_label`, `repository`,
`toggle_theme`, `menu_label`, `breadcrumb`, `pager_label`, `previous`, `next`, `home`,
`overview`, `on_this_page`, `link_to_section`, `copy`, `copied`, `figure_full_size`,
`open_image`, `close`, `no_result`, `search_unavailable`, `page_not_found`, `not_found_text`,
`did_you_mean`, `sections`. The scripts find theirs in `window.docsTheme.strings`.

## Heading ids

The theme asks the build for readable ids (`theme.yaml`, `heading_ids: scheme: slug`;
`lhtml_site/headings.py`, `slug`): the text of the heading in lower case, the accents of
Latin letters removed (`œ` -> `oe`), apostrophes dropped, the words of letters and digits
joined by `-`, nothing else kept, never truncated. A repeated heading gets `-2`, `-3`... in its
page; an id the author wrote (`=(#mine) Title`, `## Title {: #mine}`) is kept, and no
generated id takes it, nor one of the ids of the theme (`content`, `toc`, `sidebar`...).

| Heading | Id |
| --- | --- |
| `Only LHTML?` | `only-lhtml` |
| `When something goes wrong` | `when-something-goes-wrong` |
| `Vue d'ensemble` | `vue-densemble` |
| `std::vector, exemples` | `std-vector-exemples` |

The other themes keep the ids of the sites already published (`only_lhtml?_l2`).

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
  `window.docsTheme = {root, storage, strings, $, $$}`: the path to the root of the site, the
  prefix of the localStorage keys, the texts of the scripts of the theme, and two query helpers.
- **A link to the other language** of the site, added to `.topbar-actions` with the classes
  `icon-btn lang-switch`, stays in the top bar on phones (the repository link leaves).

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

`template/base.html`, `template/nav.html` (the menu and previous / next),
`template/strings.html` (the texts, by language), `css/docs.css`, `js/menu.js` (the state of
the menu), `js/site.js` (everything else), `template/404.html` and `js/not_found.js` (the 404 page), `css/font.css` with `fonts/source_code_pro` (the monospace font; the text
uses the system font) and `libs/katex`.
