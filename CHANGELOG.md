# Changelog

All notable changes to lhtml-site (`lhtml-site` on PyPI) are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed
- The site holds no file of the generator any more, which the server served
  to anyone: the Jinja templates of the theme (`theme/template/`, and the
  templates its `theme.yaml` names), its `theme.yaml` and `design.yaml`
  are read in the theme and not copied; the record of the pages that
  `--only` completes is kept in `.verification/structure.json` (next to the
  dependency store, with the site it describes, written once that site is
  published), not in `structure/` of the site; `sitemap/`, a redirection per
  page, empty pages for a search engine, is written no more. The next build,
  full or `--only`, writes a site without them. `--only` completes only the
  site its record describes: another site, a site missing a page or holding
  one the record does not list (a page put back by hand), is built whole.

### Added
- `publish_sitemap: true` and `publish_structure: true` in the
  configuration write `sitemap/` (its redirections marked `noindex`) and
  `structure/structure.{json,yaml}` into the site again, for the links and
  the custom themes or plugins that read them there.
- The `slides` theme: a horizontal swipe goes to the next slide (to the
  left) or the previous one (to the right), on a phone, a tablet or a touch
  screen. A pinch, a vertical scroll, a page zoomed in, and a swipe on a
  video, a form, the menu or a block that scrolls sideways (code) are left
  to the browser.
- The `docs` theme, for a documentation site: a top bar with the search box
  (Pagefind, `/` and Ctrl/Cmd+K, keyboard navigation of the results), a side
  menu by the `section` and `group` of the pages (collapsible, its state kept
  by the browser, scrolled to the current page), "On this page", a
  breadcrumb, previous / next, light and dark modes, a drawer menu on
  phones and figures that open full size. Its settings are the `docs` key
  of `keywords:` (name, logo, repository link, footer, order of the sections,
  sections and groups closed at first...); an overlay adds its own
  stylesheets and scripts (`css:`, `js:`, `window.docsTheme`). See
  `themes/docs/README.md`.
- `lhtml-site init --theme docs`: a documentation site to start from, three
  sections in Markdown pages.
- A `404.html` for the `docs` theme, when the configuration sets the new key
  `base_url` (`/`, `/docs/` or a full URL): served at any depth, its links
  are absolute; a message, the search box, the sections and the page of the
  menu closest to the address asked. `src/404.md.j2` replaces its content.
  It is out of the menu, of previous / next and of the search, and not
  indexed (`noindex`). A theme names the template of this content in
  `theme.yaml`, with the new key `not_found:`.
- The formulas are rendered at build time when `quickjs` is installed (the
  extra `lhtml-site[math]`): the KaTeX of the theme runs in QuickJS, and the
  page gets the HTML and MathML of each formula and `katex.min.css`, without
  any KaTeX script. Without `quickjs`, the browser renders them as before,
  and the build says so in one line. A formula KaTeX cannot read is shown in
  red and is a warning at its line (an error with `--strict`). The formulas
  rendered are kept in `.verification/katex.json`. `lhtml-site doctor` lists
  the feature.
- The configuration key `katex`: `render: build` (default) or `browser`, and
  `macros`, used at build and in the browser.
- The `docs` theme on phones and tablets: "On this page" is a bar at the top
  of the content where the right column is hidden (below 1180 px), sticky
  under the top bar; it names the section being read, and a link closes it.
  The entries of the drawer menu are about 40 px high (below 860 px).

### Changed
- The themes load KaTeX only on the pages that write formulas (`\(`, `\[`,
  `$$`, outside code, comments and Jinja). The page setting `math: true` or
  `math: false` decides instead. Templates read `page.math`,
  `page.math_render` (`build` or `browser`) and `page.katex_options`.
- KaTeX 0.16.47 in the four themes (it was 0.12.0).
- `lhtml-site init` accepts a starter written in Markdown, and names its top
  page.

### Fixed
- The transcoded videos: only the variants of the videos of the pages built
  are copied into the site, not the whole `cache_video_directory`. The cache
  of a page removed was published with the site. A full build now names the
  directories of the cache that belong to no video of the site, and removes
  nothing (`--only` builds some pages, and says nothing of the others).

## [1.0.0] - 2026-10-19

The first release on PyPI. The generator was named `static_website_lhtml`,
and projects used it as a copy or a submodule; it is now a package with a
command, `lhtml-site`, built on LHTML 3 (`lhtml-markup` on PyPI).

### Added
- `pipx install lhtml-site` (or `pip install lhtml-site` in a virtual
  environment) installs the command `lhtml-site`; `lhtml-site --version`
  says its version and the LHTML it runs.
- `lhtml-site init [DIR] [--theme slides|slides-pdf|webpage-frame]` creates
  a project: a `configure.yaml` and pages to start from in `src/` (four
  slides, or two web pages). Over a directory that already has its pages in
  `src/`, it writes only `configure.yaml`.
- `lhtml-site doctor` says, for each optional feature (PDF export, layout
  report, videos, SASS, figures, code snippets, tidy), what it finds and the
  command that installs what is missing for the way lhtml-site is
  installed (`pipx inject` after pipx).
- `lhtml-site --serve --watch` builds, serves the site on localhost and
  rebuilds it on save.
- A page says what it is in its front matter (the YAML at its top), and may
  be written in Markdown (`index.md.j2`) as well as in LHTML
  (`index.html.j2`).
- Projects of several decks, each built to several targets (the slides in
  the browser, a PDF), the layout report (`--layout`), the lint of the
  values written by hand (`--lint`).
- The PDF export runs Chromium through Playwright for Python, with the extra
  `lhtml-site[pdf]` (playwright, pypdf) and
  `python -m playwright install --only-shell chromium`: no Node.js, poppler
  nor ImageMagick. One browser for the deck, a few slides at a time, each
  printed once ready (fonts, math, images, a frame of each video) instead of
  after a fixed 4 s; the images are screenshots at 3840 px, the merge is
  pypdf. The outputs keep their names and layout. `lhtml-site doctor`
  reports it.
- A progress bar while the PDF is made, on a terminal only (a log gets
  nothing). Without Playwright, the build says what to install, the command
  for the way lhtml-site is installed.
- The layout report (`--layout`, `--render`) runs in the same Chromium,
  through Playwright for Python (`lhtml_site/layout/measure.py`; what runs
  inside the page is `lhtml_site/layout/page.js`). Its reports are those of
  the Node version: same blocks, problems and usual values of the deck
  measured in the same browser. The pages of an existing report are measured
  again once (the measuring code changed). On a deck of 35 slides, the
  report takes 7.9 s instead of 9.5 s.
- A slide is printed once the promises a page or a demo (in an iframe too)
  registered with `window.__lhtmlReady` are settled, as the layout report
  already waited for them; the whole preparation of a slide is bounded (60
  s), so a promise that never settles fails the slide instead of blocking
  the export. After pipx, the commands to install are the same in the
  README, in `lhtml-site doctor` and in the errors:
  `pipx inject lhtml-site pypdf`, `pipx inject --include-apps lhtml-site
  playwright`, then `playwright install --only-shell chromium`.

### Changed
- Requires LHTML 3 (`lhtml-markup>=3.0`), which reads no file: the
  generator reads the sources, and `include::` is written with Jinja
  (`{% include %}`). Coming from LHTML 2: the
  [migration of LHTML](https://github.com/drohmer/lhtml/blob/main/docs/migration.md).
- The README leads to a first talk in a few commands, opened from the disk
  (`lhtml-site`, then `.site/index.html`; `--watch` to rebuild on save, and
  `init` says the same); the reference moves to
  [docs/reference.md](https://github.com/drohmer/lhtml-site/blob/main/src/lhtml_site/docs/reference.md),
  with the details of the PDF export.
- The package holds the themes, plugins and starters but not the demo
  course, and the themes ship their fonts as WOFF2 only: the wheel is about
  8 MB.
- The id of a heading is the one of the generator copied into projects
  since April 2026 (` -,.:()` become `_`, then `__` becomes `_`), so links
  into the sites it built keep working; a site built by an older copy
  changes the id of its headings with these characters (`Part - One`:
  `part___one` before, `part__one` now). A repeated heading gets distinct
  ids (`_id2`, `_id3`...) and characters unsafe in a URL are removed.
- The "Page content" column of the theme webpage-frame is read in the page
  (its level-2 headings with an id), not fetched from a JSON file: it is
  shown when the site is opened from disk (`file://`), where it was empty,
  and lists the headings as the page shows them (`== One **bold**` is
  "One bold", it was "One \*\*bold\*\*").
- A heading whose text comes from Jinja gets its id from its text as
  rendered, unique in its page: each occurrence of a page reused with
  `params` has the id of its own title (`interpolation_de_key_l1`; it was
  `_parties[current__1]_id2_l1`, the same source for all of them), and
  each heading of a `{% for %}` loop has its own. The ids of the headings
  written as text do not change: links into published sites keep working.

### Removed
- Node.js is no longer used: the Node PDF export of `static_website_lhtml`
  (puppeteer, poppler, ImageMagick, `LHTML_PDF_ENGINE`), the Node scripts of
  the layout report, `package.json`. `lhtml-site doctor` no longer looks for
  Node, puppeteer or a Chrome of its own.
- The site no longer holds `<page>.title_id.json`, `title_id.json` nor
  `structure/title_id.json` (144 files, 592 KB on a deck of 78 slides).
  The record of the headings that `--only` needs is build state, in
  `.verification/headings.json`; the `structure/title_id.json` of a site
  built by an older copy is read once in its place.

### Fixed
- The slides no longer write their menu in the console of the browser.

[1.0.0]: https://github.com/drohmer/lhtml-site/releases/tag/v1.0.0
