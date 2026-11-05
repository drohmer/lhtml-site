# lhtml-site: advanced

For the authors of themes and plugins, and for the layout report: what a theme declares about the
build, the stages of the build, plugins, the layout report, and the migration from
static_website_lhtml. The everyday reference (command, configuration, decks, design) is
[lhtml-site: reference](reference.md).

## Theme: what it declares about the build

A theme answers questions the build used to answer for it: which template a
page is wrapped in, which block it fills, and what the measurement must take
as the content of a page. It says so in `theme.yaml`, next to its
`design.yaml`:

```yaml
template: 'theme/template/base.html'   # the page is wrapped in it
content_block: 'content'               # the Jinja block it fills
toc:                                   # the theme has a menu
  file: 'js/menu.js'                   # the theme file that receives the table of contents
  keys: [section, group]               # extra page settings the menu carries
layout:                                # what the layout analysis reads
  root: 'body'                         # CSS selector of the content
  exclude: 'nav, footer'               # children of the root that are not content
  width: 1920                          # size of a page, in CSS pixels
  height: 1080
export: pdf                            # the site is rendered to a PDF, not published
not_found: 'theme/template/404.html'   # the content of 404.html (with base_url)
heading_ids:                           # the ids the build gives to the headings
  scheme: slug                         # legacy (the default) or slug
  reserved: [content, toc]             # ids of the theme's own elements, that no heading takes
```

| Key | Default | Effect |
|-----|---------|--------|
| <a id="theme-template"></a>`template` | `theme/template/base.html` | The template a page is wrapped in, as `theme/` followed by its path in the theme |
| <a id="theme-content_block"></a>`content_block` | `content` | The Jinja block of that template the page fills |
| <a id="theme-toc"></a>`toc` | none: no menu | The theme has a menu: `file`, the theme file that receives the table of contents; `keys`, the page settings the menu carries beyond those every theme displays (the `docs` theme: `section`, `group`) |
| <a id="theme-layout"></a>`layout` | `root: body`, `exclude: nav, footer` | What the layout report reads: only `root`, `exclude`, `width`, `height` and `reserved` |
| <a id="theme-export"></a>`export` | none | `pdf`: the site is rendered to `<deck>.pdf` and `images/`, and not published ([PDF export](reference.md#pdf-export)) |
| <a id="theme-not_found"></a>`not_found` | none | The template of the content of `404.html`, written with `base_url` (see below) |
| <a id="theme-heading_ids"></a>`heading_ids` | `scheme: legacy` | `scheme`: `legacy` or `slug`; `reserved`: the ids of the theme's own elements, that no generated id takes ([Heading ids](reference.md#heading-ids)) |

`not_found:` names the template of the content of `404.html`, as `theme/`
followed by its path in the theme:
the build writes that page at the root of the site when the configuration
sets `base_url` (see [Configuration](reference.md#configuration)), out of the menu, of
previous / next and of the search index; a page `src/404.md.j2` (or
`.html.j2`) of the project replaces the content of the theme. The `docs`
theme declares one.

Everything is optional and a theme with no `theme.yaml` builds as before.
The order is **engine, then theme, then project**: the defaults above are
the engine's fallback, a theme replaces what it declares, and the `layout:`
key of a project replaces both - the project keeps the last word because it
is the one that knows it added a banner to its pages. A theme with no `toc:`
has no menu, and the build writes none.

A theme may declare only `root`, `exclude`, `width`, `height` and
`reserved` under `layout:`; the other options (thresholds, output
directory, jobs) belong to a project. An unknown key is refused by name,
and `--check-config` prints the manifest the build will use.

The four themes shipped declare theirs. `webpage-frame` holds its content
in `#main-content-centered`: a project using it used to have to write that
selector in its own configuration, and a project that did not had its whole
page measured as a single block - the example site went from 3 blocks over
3 pages to 145 when its theme started saying so.

## Pipeline

The generator runs the following stages:

1. **Data preparation** — Find the `.html.j2` and `.md.j2` templates, select and order them (deck), copy the sources and theme to the site (or, with `--only`, the templates and assets of its pages; the theme without its templates and declarations, read in the theme), extract the titles and the structure of the site (`sitemap/` and `structure/` in the site with `publish_sitemap` / `publish_structure`), write the design (`design.css` in the site, `design.md` in `.structure/`)
2. **Pre-process plugins** — Plugin hooks before Jinja2 rendering
3. **Jinja2 rendering** — Render the templates with their variables (see [Template variables](reference.md#template-variables))
4. **Mid-process plugins** — Plugin hooks between Jinja2 and LHTML
5. **LHTML conversion** — Convert LHTML markup to HTML, with optional tidy (a Markdown page is converted in step 3), then **Formulas** — render the formulas of the pages that have some with the KaTeX of the theme, when they are rendered at build (see [Formulas](reference.md#formulas))
6. **SASS compilation** — Compile `.sass` files to `.css` (if libsass installed)
7. **Post-process plugins** — Plugin hooks after all conversions

## Plugins

A plugin (an extension of the project, `plugin:` of the configuration) is a
Python file that transforms the pages: it receives content and returns
content, and the build reads and writes the files - in the site, never in
the sources (`lhtml_site/extensions.py`).

```python
def prepare(context):                  # once per build, before the pages
    ...

def pre_process(text, context):        # the template of a page, before Jinja
    return text

def mid_process(html, context):        # the page as Jinja wrote it, before LHTML
    return html

def post_process(html, context):       # the page once converted, before the menu
    return html
```

`context.options` is `plugin_arg` of the configuration, `context.config_directory`
the directory its paths are relative to, `context.page` the page (`title`,
`dir`, `filename`, `src` and its settings; `None` in `prepare`), and
`context.warning(message)` reports a warning at the page. An exception fails
the page, named with the plugin; the other pages are built and the build
fails at the end. A module is loaded once per build, so it keeps a state
from `prepare` to the pages, but not from a build to the next (`--watch`).

This is a discipline, not a sandbox: a plugin is Python and can still reach
the file system. It no longer has to, and the plugins of the generator do
not. The hooks of static_website_lhtml, `pre_process(meta)` and the like, are refused
with the form to write.

A plugin is called for the pages generated by this build (all of them, or those of `--only`); a page that failed before a stage is not given to it. The keys written by the generator (`dir`, `filename`, `template`, `level`, `src`, `source`, `occurrence`, `path`, `title_id`) cannot be set in a `config.yaml` nor in the deck.

### Built-in plugins

| Plugin | Hook | Description |
|--------|------|-------------|
| `pre_include.py` | pre | Writes the files of `plugin_arg: pre_include:` at the top of each page (shared Jinja macros) |
| `code_include.py` | mid | `includeadv::{...}`: code of a Git repository (`plugin_arg: includeadv:`), a whole file or the lines found in it |

Guide: [The code of the course](https://scholartools.fr/lhtml/03_recipes/01_course-website/#code-of-the-course).

The page placed in the template of its theme, the heading ids, the menu,
the index of a site that has none and the transcoded videos used to be
plugins; they are stages of the build (`lhtml_site/wrap.py`, `lhtml_site/headings.py`,
`lhtml_site/menu.py`, `lhtml_site/index_page.py`, `lhtml_site/video_cache.py`). A configuration
that still lists one of them is refused by name.

## Layout report (LLM-assisted slide layout)

`--layout` measures the layout of every generated page in headless Chromium
and writes a text report that an LLM (or any script) can read to find and fix
layout problems. It runs the Chromium of Playwright for Python, as the PDF
export does (the extra `lhtml-site[pdf]`, then
`python -m playwright install --only-shell chromium`; see
[PDF export](../../../README.md#pdf-export) in the installation).

**What happens when it cannot run.** The analysis never takes the build with
it: a missing browser, a page it cannot measure, a measurement that crashes
are reported (`Layout report not produced ...`), the site is built and
published, and the report of the previous build is left whole - what the
measurement cannot replace, it does not destroy. What it is *asked* to do is
another matter: an output directory that would overlap the sources, the
theme or the site, and an option of the wrong shape (`jobs`,
`design_rules`), stop the build with the name of the key, before anything is
written.

```bash
lhtml-site --layout          # full generation + layout report
lhtml-site --only 03_squelette/04_ik --layout   # after editing a slide
```

The measure shows its progress (pages measured, time left). With `--only`,
only those pages are measured, and the summary keeps the other pages of the
previous report. Without it, a page is measured again only when something
it shows changed: its report is kept when its HTML and every file it loaded
(styles, images, fonts, videos) are those it was measured with, with the
same options of the measure, the same Chrome and the same measuring script;
its analysis is made again. On a deck of 78 slides: 6 s when nothing
changed, 9 s after editing one slide, 26 s for all of it. Delete `.layout/`
to measure everything again. Output in `.layout/` (next to the configuration file). Each page has a unique `pages/<relative HTML path>/` directory, for example `pages/chapter/a.html/layout.json`. The output path remains configurable and is checked before deletion: it cannot overlap sources, theme, site or cache, or contain the configuration, generator or plugin files. Paths through symbolic links are checked too.

Files:

- `summary.md`: the usual values of the deck (its style, see below), then all
  pages sorted by number of problems and warnings, with their number `n` in
  the deck and links to the page reports
- `contact_NN.png` (and `.html`): thumbnails of all pages in deck order, 16
  per sheet, with badges `P` (problems), `W` (warnings), `D` (differences
  with the deck): the whole deck at a glance
- `deck.json`: the usual values of the deck, for scripts
- `changes.md`: what changed since the previous report (see below)
- `summary.md` links to `.structure/design.md` of the project: the macros and
  tokens of the design (when the theme or the configuration defines one), to
  use instead of inline styles
- `pages/<relative HTML path>/layout.md`: one row per top-level block (number, kind, position and
  size of what is actually drawn, margins, CSS position, font size, signature),
  then the problems, warnings, differences with the deck, density and the
  vertical gaps between blocks. Each finding ends with where its blocks are
  written: `[line 62]` for the line of the block in the page,
  `[parts/bloc.j2:3]` for a block written in a template the page includes,
  `[near line 62]` for the line of what surrounds it (an element inside a
  marked block), `[no source marker]` for a block nothing names (one a
  script writes); the table writes them `62`, `~62` and `-`
- `pages/<relative HTML path>/layout.json`: the same data, for scripts.
  `analysis.findings` is what was found, one shape for every check:
  `{key, code, severity, blocks, subject, detail, text, data}` - `code` is
  what the report prints (`HIDDEN TEXT`), `severity` is `problem`,
  `warning`, `deviation` or `note`, `blocks` the numbers the finding is
  about, `text` the line of the report, `data` the row the check produced
  (its measured values). Read it instead of parsing `layout.md`
- `pages/<relative HTML path>/render.png`: the real render
- with `images: true` only (they take a third of the time of the measure):
  `pages/<relative HTML path>/overlay.png`, the real render with the outlined
  ink of each block and its number; `blocks.png`, the ink of each block as
  solid rectangles, content hidden; `internal-overlay.png`, the render with
  the inner blocks outlined (columns, paragraphs, list items, figures,
  captions, formulas). `layout.md` gives the same blocks, as text

Coordinates are CSS pixels, origin at the top-left corner of the page
(1920×1080 for slides); the usable area is the inside of the slide frame.
Detected problems:

- `HIDDEN TEXT`: text covered by another block drawn on top of it (checked in
  the browser, along each line of text: an opaque image pixel or a background
  of another block is visible on top of the text)
- `COLLISION`: the drawn content of two blocks overlaps (text on text, text
  on the drawn part of an image, images, backgrounds)
- `OUT OF AREA`: block beyond the usable area. A block laid over the page
  rather than placed in the content is compared with the whole page
  instead - one marked as an intentional overlay (class `overlay`), or one
  fixed to the viewport (`position: fixed`: a timer, a page number, a
  source line in the margin). A full-bleed figure covers the slide on
  purpose and a fixed note sits in the margin on purpose; either one is
  still reported when it spills past the page itself
- `CLIPPED`: content cut by `overflow`
- `UPSCALED IMAGE`: bitmap or video drawn more than 1.25× its native size,
  hence blurry (vector images such as SVG are ignored)
- `RESERVED AREA`: **text** written over an area of the theme (the
  navigation: the elements of `exclude`), reported once per block and per
  element, whatever the number of parts that element is drawn in. A figure
  or a background passing under the navigation is not reported: the theme
  draws its navigation over the content, which is what a full-bleed slide
  is for
- `COLLAPSED FIGURE`: an image or a video drawn (almost) without width or
  height, e.g. in a flex box without a height: invisible
- `SVG OVERFLOW`: an SVG figure draws beyond its viewBox (by more than the
  threshold, at its displayed size): what is beyond is cut. For an SVG image,
  its pixels drawn outside the viewBox are measured on a copy of its file (an
  SVG without viewBox needs its width and height in px); for an inline SVG,
  the boxes of its elements beyond its own box (unless its overflow is visible).
- `INTERNAL COLLISION`, `INTERNAL CLIPPED`: the same checks between the inner
  blocks of a block (two items of a list, a formula and its text...); at most
  400 inner blocks per page.
- `COLUMN OVERFLOW`: content wider than its column (`.col`, `.column`).

Warnings:

- `TIGHT`: the line box of a text overlaps another text or an image by less
  than 0.4× the font size: the glyphs usually do not touch, but the spacing
  is tight. Text on the background of another block is not an overlap (only
  hidden text matters there).
- `NEAR-ALIGNED`: an edge or the center of a block is 3 to 12 px away from
  that of another block, of the usable area, or of a column of the deck:
  align it exactly, or move it clearly. Only edges whose position is
  meaningful are compared: edges of images filling their box and of
  backgrounds/borders, the aligned side of text (left, right or center,
  from `text-align`); tops and bottoms only between blocks side by side.
  A block laid over the page (the same overlay as `OUT OF AREA`) takes no
  part on either side: it is positioned against the page, not in the grid
  of the content.
- `DENSE` (more than `max_words` words of text) and `SMALL FONT` (text
  smaller than `min_font` px, only when `design_rules.enabled` is false), on
  slides only.
- `WRAPPED`: a title on several lines, or a list item (paragraph, credit or
  reference) whose second line holds only a few words.
- `SHORT WRAPPED`: a list item (paragraph, credit or reference) on several
  lines that would fit on one line of the slide: its width on one line is at
  most the width from its left edge to the right of the usable area. The
  report gives that width, the width available and the difference: give the
  element that width (another layout, a wider column) or shorten the text.
- `ROW`: figures side by side whose tops (or bottoms) differ by 3 to 40 px.
- `SMALL IN ITS BOX` / `CROPPED`: a figure drawn on less than 75 % of its
  box, or cut, by `object-fit` (e.g. in `media::`: use `media::(.fill)` or
  another arrangement).
- `SVG LABEL`: a text of an SVG figure drawn across one of its lines (a line,
  path, circle... with a stroke), without a halo that keeps it readable
  (`paint-order="stroke" stroke="white"`).
- `DESIGN`: checks by role. Text smaller than the minimum of its role (body,
  caption, reference, code), title not larger than the body or on more than 2
  lines, caption larger than the body or far from its figure, tiny figure. The
  role comes from the element: `.credit`, `.legende`, `figcaption` are
  captions, `.source`, `.reference` references; `data-lhtml-role` sets it
  (`decorative` exempts an ornament). Inside a block laid over the page (the
  same overlay as `OUT OF AREA`) the role is not guessed: it is `decorative`,
  so a timer, a page number or a watermark is not judged as content. Write
  `data-lhtml-role` on it to have it judged. These checks replace `SMALL FONT`
  unless `design_rules.enabled` is false.
- `CANVAS OVERLAP`: text over a canvas or an animated demo. The box of a
  canvas does not say which pixels are drawn: look at the render.
- `INTERNAL TIGHT`: `TIGHT` between inner blocks.

A formula is one box for `WRAPPED` and `SHORT WRAPPED`: its sums, indices and fractions are not
lines of text.

Each page report also gives its density: words (math and code excluded),
formulas, lines of code, list items, lines of text, smallest font size, the
parts of the area covered by text and images, and the largest free area.

Renders are reproducible: videos are measured at their first frame, animated
GIFs at their first image, CSS animations stopped. A page whose media could
not be measured says so (`Report validity`, and `render_health` in
`layout.json`): a video measured before it loaded has the default box of the
browser, not the one of the slide, so the checks of that page are computed
on a rectangle it never shows. `changes.md` lists what
changed since the previous report for the pages measured again: the problems
that appeared or were solved, the counts of warnings and of values written
by hand, the blocks moved or resized (matched by their signature), added or
removed.

Differences with the deck: the usual values of the deck are measured over
all its pages (`summary.md`, `deck.json`): page title variants (heading tag
and font size used on at least 3 pages) with their position (left edge or
center, top or middle: whichever varies least), columns (left edges of
in-flow blocks shared by at least a quarter of the pages), body font size
and the text sizes used on several pages, gap below the title, words per
page and occupancy. A page is compared with them: `TITLE POSITION`,
`TITLE VARIANT` (title of an unusual kind or size), `TITLE GAP`, `TEXT FONT`
(text in a size used nowhere else). These are not errors, but breaks of
consistency to check.

Only what is actually drawn counts (the *ink* of a block): text lines, images
reduced to their drawn shape (16 px cells; uniform or transparent background
removed), backgrounds and borders. Each block is described by a list of typed
ink rectangles (`"ink"` in `layout.json`), so invisible full-width boxes and
the empty corners of an irregular block do not create collisions. Empty
blocks (`::nl`, `div[height:...]`) are `spacer`s and are ignored.

An overlap can be intentional (zoom inset over an image, annotation placed on
a figure): add the class `overlay` to one of the blocks, e.g.
`::(.overlay)[position:fixed; ...]`. The overlap is then listed as
`INTENTIONAL OVERLAP` in the `Notes` section instead of the problems
(hidden text is still reported). `Notes` also lists `BACKGROUND OVERLAP`: a
block over the part of an image that is only its background (uniform or
transparent), not visible, but the box of the image is reserved there.

A block is a top-level element of the page: title, paragraph or bare text,
list, code block, image, video, math, or a `div::` / `::[...]` with all its
content. An element placed out of the flow (`position: fixed` or `absolute`)
inside a block is measured as a block of its own (`in #n` in the table), so
that it collides with the text of its block. Each block gives the line of the
source where it starts (column `line`, from the source map below), and its
signature (tag, inline style, beginning of the text, image names).

**Source map.** In the builds for development (`--layout`, `--serve`,
`--watch`), the blocks of the pages carry `data-lhtml-src="<file>:<line>"`:
the line of the template where they start. The blocks are the children of
the content root the theme declares (`layout: root:` of its `theme.yaml`),
or of the wrapper of the theme that holds all the content. The generator marks the
lines of the templates with invisible characters before Jinja and LHTML, then
moves them to the attribute (`lhtml_site/source_map.py`); the lines inside a zone
that LHTML keeps as it is (code block, multi-line Jinja or HTML tag, math)
and inside the Jinja blocks whose content is a value (`{% set x %}`,
`{% markdown %}`, `{% filter %}`) are not marked. A block written on one line
in HTML or by a macro (`{{ box() }}`) gets its own line. Without the
attributes, the HTML is the same as in a normal build.

**Validity of the reports.** Each build records the files that each page
depends on (template, includes, configuration, design, theme, plugins, its
assets, the files its scripts request) with their SHA-256, in
`.verification/builds.json`. `--only` then also rebuilds and measures the pages
whose dependencies changed. A change of what all pages share (theme,
configuration, design, plugins, the generator itself) rebuilds and measures
all of them, once. A report kept from a previous build gives its validity in
`layout.md` (`current`, `stale` or `unknown` for a remote file). One build at a
time writes the report: a second one waits for the first (at most 10 min).

**Pages that load asynchronously.** The measure waits for the load of the
page and of its local frames, for the fonts and the images, then for a short
network idle and a settling delay. A page or a demo that prepares itself
asynchronously can say when it is ready: the measure then waits for its
promises (a rejected promise, or more than 15 s, fails the measure of the
page), and skips the delays when every frame of the page does so and none
plays a video or a sound. The slides theme loads
`themes/slides/js/readiness.js`; a demo in an iframe loads it too, from
`theme/js/readiness.js` of the site:

```js
window.__lhtmlReady.optIn();
window.__lhtmlReady.waitUntil(loadAndPrepareTheDemo());   // a promise
```

Typical loop with an LLM (e.g. Claude Code): "read `.layout/summary.md` and
the contact sheets, fix the collisions and overflows by editing the sources
(positions, widths, font sizes), run `lhtml-site --only <slide> --layout` and
check the new report" (the procedure: [agents.md](agents.md)).

Options (`configure.yaml`):

```yaml
layout:
    # these four describe the theme and are declared in its theme.yaml
    # (see Theme); set them here only to override what the theme says
    root: 'body'                # content root
    exclude: 'nav, footer'      # children of the root that are not content
    width: 1920                 # viewport size
    height: 1080
    images: render              # render.png and the contact sheets; true: also overlay.png, blocks.png,
                                # internal-overlay.png; false: no image (the fastest)
    threshold: 4                # minimal overlap / overflow reported (px)
    output: '.layout/'
    max_words: 80               # DENSE above this number of words per slide
    min_font: 20                # SMALL FONT below this font size (px), when design_rules is disabled
    contact_columns: 4          # thumbnails per row and rows per contact sheet
    contact_rows: 4
    jobs: auto                  # pages measured at the same time (a window each); auto: half of the processors, at most 6
    design_rules:               # DESIGN checks (defaults at 1920 px, scaled with the width)
      enabled: true
      roles:
        body: {min_font: 20}
        caption: {min_font: 12, max_body_ratio: 1.05, max_figure_gap: 64}
        title: {min_font: 32, min_body_ratio: 1.25, max_lines: 2}
        figure: {min_extent: 32}
      layouts:                  # per layout (exact name, e.g. side-s)
        section:
          title: {min_body_ratio: 1.5}
```

A check set to `null` is disabled; an unknown key or an invalid limit of
`design_rules` is an error of the configuration. Another unknown key of
`layout:` is ignored, with a warning.

## Migrating from static_website_lhtml

lhtml-site 1.0, the first version as a package and built on LHTML 3, breaks
with the old generator, static_website_lhtml: an old form is refused by name, with the change to
make, rather than accepted with a warning.

- `lhtml-site init DIR` copies a few pages to start from into `DIR/src/` (four slides with
  `--theme slides` or `slides-pdf`, two pages with `webpage-frame`, three
  sections with `docs`), instead of the course example
  into `DIR/example/`. The course example, with its videos, is no longer in the package: it is in
  `src/lhtml_site/example/` of a checkout (see [From a checkout](../../../README.md#from-a-checkout)).
- The default `source_directory` is still `src_site/`, the directory of the old projects; `init`
  writes `source_directory: 'src/'` (see [Configuration](reference.md#configuration)).
- The themes ship their fonts as WOFF2 only (`fonts/*/WOFF2/TTF/`), which every current browser
  and the Chrome of the PDF export read: a theme of your own that copied `css/font.css` and named
  the OTF, TTF or WOFF files of the generator names the WOFF2 ones.
- The generator is a package, `lhtml-site` (`pip install`, command `lhtml-site`): its code is in `src/lhtml_site/` (the package `lib` is now `lhtml_site`: a plugin or a script that imported `from lib.structure import ...` imports `from lhtml_site.structure import ...`), with its `themes/`, `plugins/` and `configure_example.yaml` (the course example stays in the checkout, `src/lhtml_site/example/`, and is not installed). `python generate.py` in a checkout still runs it, and the paths `<checkout>/themes/...` and `<checkout>/plugins/...` of a configuration still find these files. A configuration that names a theme of the generator can name it alone (`theme: slides`), which works from a checkout and from an installation. `configure_example.yaml` is no longer at the root: `lhtml-site init` sets up a project (see [Getting started](../../../README.md#getting-started-your-first-slides)).
- `configure_default.yaml` is now `configure_example.yaml`.
- Replace `plugin_post` with `plugin` (all the hooks of a plugin run). `include_head` is gone (it was read nowhere).
- `.site/` is the output default; an explicit `site_directory` still takes precedence.
- `level_print` is gone: the build prints no indented log (`-v` shows its stages).
- A plugin is a transformation, `pre_process(text, context) -> text` (and `prepare`, `mid_process`, `post_process`, see [Plugins](#plugins)): it no longer receives `meta`, reads or writes the files of the site, nor uses the log. `pre_process(meta)` is refused with the form to write.
- LHTML is now installed with pip (`lhtml-markup`, see [`requirements.txt`](../../../requirements.txt)) instead of the `lib/lhtml` submodule.
- `theme_templates/` was renamed `themes/` and `src_site_example/` was renamed `example/`: update the configuration, e.g. `theme: 'static_website_lhtml/themes/webpage-frame/'`.
- Light mode (`-l`) was removed: it copied the whole previous site and was not faster than a full build. Use `--only <page>` to regenerate some pages.
- Deck parameters of a page are read as `params.<name>` (not as top-level variables).
- `auto_wrap.py` (or `auto-wrap.py`), `redirection_first_page.py` and `cache_video.py` are no longer plugins either: remove them from `plugin:`, which is then usually empty. The transcoded videos are asked for by setting `cache_video_directory:` (the plugin used to fall back to a default directory and say so); without it, nothing is transcoded.
- The menu of the theme and the heading ids are no longer plugins: remove `plugins/menu.py` and `plugins/title_submenu.py` from `plugin:`. The build runs them itself, and the theme declares whether it has a menu (`toc:` in its `theme.yaml`). The extra page settings the menu carried move from `plugin_arg: menu: keys:` to `toc: keys:` of the theme. Both old spellings are refused by name.
- The layout report is no longer a plugin: remove `plugins/layout_report.py` from `plugin:` and run the build with `--layout`. Its options move from `plugin_arg: layout_report:` to the configuration key `layout:`. Both old spellings are refused by name, with the change to make; `--check-config` reports them without building anything.
- `generate_pdf.py` is no longer a plugin: the PDF is a target, `targets: pdf: {theme: slides-pdf}` (the theme declares `export: pdf`), named after its deck. A script that looped over the chapters with a temporary configuration per chapter and per theme is replaced by `decks: directories` and `targets:` (see [Decks and targets](reference.md#decks-and-targets)).
- LHTML 3.0 reads no file: `include::` is refused, with the file it named. Include with Jinja instead, `{% include "part.html" %}` (the path is relative to the sources). A poster is no longer looked for next to a video: write it, `video::clip.mp4{poster="clip.jpg"}`. `wrap-auto` and `directory_include` are no longer passed to LHTML: the theme wraps the page. LHTML 3 also refuses `::name[-]` and `::[-]` (close with `::`), `::#` comments (write `{# ... #}`) and `verbatim::` (write `code::[text]`); `$...$` is text (write `\(...\)`), and a tag inside inline code is literal. The YAML front matter of a page is read by the generator, which removes it before LHTML.
- For plugins: the directories of `meta` (`source_directory`, `site_directory`, `theme`, `config_directory`, `lib_directory`, `cache_video_directory`) are `pathlib.Path`: join with `/` (`meta['site_directory'] / page_path(entry)`), not `+`. The place of a page in the site stays a string with `/` (`entry['dir']`, `page_path(entry)` of `lhtml_site.structure`).
- Heading anchors keep the scheme of the generator copied into projects since April 2026 (` -,.:()` become `_`, then `__` becomes `_`): a site built by an older copy changes the id of its headings with these characters (`Part - One`: `part___one` before, `part__one` now). Identical headings, or a heading that starts like another one (`= Installation` / `== Installation sous Windows`), get distinct ids, and characters such as `<`, `>`, `"` are removed from ids. See [Heading ids](reference.md#heading-ids).
