# lhtml-site: reference

The reference of lhtml-site for everyday use: the command, the configuration, decks and targets,
the template variables, the heading ids, the design, formulas, the PDF export and the error
messages. To start, see [Getting started](../../../README.md#getting-started-your-first-slides);
to install, [Installation](../../../README.md#installation). Theme declarations, plugins, the
stages of the build, the layout report and the migration from static_website_lhtml are in
[lhtml-site: advanced](advanced.md).

## CLI options

```
lhtml-site [-h] [-d | --no-debug] [-v] [--strict] [-c] [-i INPUT_CONFIG] [--only POINTER]
           [--target NAME] [--lint] [--check-config] [--layout] [--render FILE] [--deck FILE]
           [--scaffold] [--serve] [--watch] [--port PORT] [-V]
lhtml-site init [DIR] [--theme NAME]
lhtml-site doctor
```

`lhtml-site` builds the project of the current directory (its `configure.yaml`), or the one of
`-i`. `lhtml-site --help` prints the same list.

| Flag | Argument | Default | Effect | See |
|------|----------|---------|--------|-----|
| <a id="opt-input_config"></a>`-i`, `--input_config` | FILE | `configure.yaml` | The configuration file of the project; relative paths in it are read from its directory | [Configuration](#configuration) |
| <a id="opt-verbose"></a>`-v`, `--verbose` | | off | Display the stages of the build, their time, and what they did | [Error reporting](#error-reporting) |
| <a id="opt-debug"></a>`-d`, `--debug` | | `debug:` of the configuration (false) | Display debug information (tracebacks) and keep temporary files (the staging directory of a failed build) | [Error reporting](#error-reporting) |
| <a id="opt-no-debug"></a>`--no-debug` | | | Turn off a `debug: true` of the configuration | |
| <a id="opt-strict"></a>`--strict` | | off | A warning fails the build (exit code 1), as an error does | [Error reporting](#error-reporting) |
| <a id="opt-clean"></a>`-c`, `--clean` | | | Remove the site directory of the configuration, and exit: nothing is built, and the sources and the theme need not exist | [Configuration](#configuration) |
| <a id="opt-check-config"></a>`--check-config` | | | Validate the configuration, the paths, the plugin files, the deck and the design, and print the resolved settings (one YAML document per build); nothing is built nor removed, and it wins over `--clean` | [Configuration](#configuration) |
| <a id="opt-only"></a>`--only` | POINTER | all the pages | Generate only these pages (deck pointers: directory, file, glob, `name:path`) in the existing site; a full build when the pages of the site changed. Repeatable | [Generating some pages](#generating-some-pages---only) |
| <a id="opt-target"></a>`--target` | NAME | all the targets | Build only these targets of the configuration. Repeatable, or `html,pdf` | [Decks and targets](#decks-and-targets) |
| <a id="opt-lint"></a>`--lint` | | | List the values written by hand in the pages (positions, spacers, font sizes), with the layout or macro of the design that replaces them; no generation (with `--only`: some pages) | [Design](#design-tokens-macros-and-layouts) |
| <a id="opt-layout"></a>`--layout` | | | Build, then write a layout report of each page in `.layout/` (needs Playwright: `lhtml-site doctor`) | [Layout report](advanced.md#layout-report-llm-assisted-slide-layout) |
| <a id="opt-render"></a>`--render` | FILE | | Render a file as PNG as the slides draw it (an SVG or image at its size, at most the slide; an HTML page at the size of the slide) in `<layout output>/render/` (`.layout/render/`; a file outside the project goes to `_outside/`); no build. Repeatable; used alone | [Layout report](advanced.md#layout-report-llm-assisted-slide-layout) |
| <a id="opt-deck"></a>`--deck` | FILE | `deck:` of the configuration | A deck file (order of the slides) replacing the deck of the configuration; relative to the current directory, else to the configuration file | [Deck](#deck-order-of-the-slides) |
| <a id="opt-scaffold"></a>`--scaffold` | | | Create the source of the deck slides that do not exist yet (entries with a `title`) | [Deck](#deck-order-of-the-slides) |
| <a id="opt-serve"></a>`--serve` | | | Build, then serve the site on `http://127.0.0.1:<port>/` (localhost only), with the comments on the render | [Local preview](#local-preview) |
| <a id="opt-watch"></a>`--watch` | | | Rebuild after each edit of the sources, theme, plugins or configuration | [Local preview](#local-preview) |
| <a id="opt-port"></a>`--port` | PORT | `8000` | The port of `--serve`; `0` selects a free one | [Local preview](#local-preview) |
| <a id="opt-version"></a>`-V`, `--version` | | | Print the version of lhtml-site and of the LHTML it runs | |
| <a id="opt-help"></a>`-h`, `--help` | | | Print the options | |

`--serve` and `--watch` do not go with `--clean` or `--check-config`, nor `--only` with
`--clean` or `--check-config`, nor `--lint` with `--clean`, `--check-config`, `--serve` or
`--watch`; `--render` is used alone.

| Command | Argument | Default | Effect | See |
|---------|----------|---------|--------|-----|
| <a id="cmd-init"></a>`lhtml-site init` | DIR, `--theme NAME` | the current directory, `webpage-frame` | Write `configure.yaml` in DIR (created if needed): its pages are those of `src/` if it has one, else pages to start from are copied into `src/` (four slides for `slides` and `slides-pdf`, two pages for `webpage-frame`, three sections for `docs`). NAME is one of `webpage-frame`, `docs`, `slides`, `slides-pdf` | [Themes](#themes), [Getting started](../../../README.md#getting-started-your-first-slides) |
| <a id="cmd-doctor"></a>`lhtml-site doctor` | | | Say what each optional feature (PDF export, layout report, formulas rendered at build, videos, SASS, figures in code, code of other repositories, tidy) finds and lacks, with the command that installs it; changes nothing | [Optional features](../../../README.md#optional-features) |

## Local preview

```bash
lhtml-site --serve --watch
```

The server binds only to localhost. Open the printed URL, and refresh the browser after a rebuild (the server asks the browser to check every file again, `Cache-Control: no-cache`: a page rebuilt after an edit of the deck never runs with the previous menu, which gives the previous and next pages). `--serve` can be used alone; `--watch` can rebuild without an HTTP server. Stop with Ctrl+C. The watcher polls inputs and waits for saves to settle. It watches the source, theme, YAML configuration, deck and design files (with the files they `extends`), configured plugin files and `pre_include` files. It does not follow directory symlinks or watch remote repositories. With `--only`, each edit regenerates only those pages. Changes to assets and configuration are included. Invalid edits leave the previous site available, and a later edit retries the build.

**Comments on the render.** With `--serve`, the pages have a button 💬 (or
the key `c`): click a block, write a comment, save. The comments are kept next
to the configuration in `.feedback/comments.md` (and `comments.jsonl`), with
the page and the file and line of the block (source map), for an agent or the
author to treat; open comments are shown on the pages as numbered pins (click:
read, "Done"; setting `"status": "done"` in `comments.jsonl` by hand works
too, `comments.md` is written again when a page loads its comments; a hand
edit that misses fields is still read). Only the script of the
pages of this server can read and write them: the requests must name the
server (`127.0.0.1` or `localhost` and its port: a page of another site
reaching it by DNS rebinding is refused), and the writes need a custom header
and JSON.

Builds run in a hidden temporary sibling directory. Only a successful build replaces the output; failures preserve the previous site. With `--debug`, failed staging directories are kept and their location is reported. Publication uses a backup/rename with rollback on failure; there is a brief directory swap, not an atomic filesystem exchange. Plugin side effects outside the site directory (reports, PDF, caches or custom actions) are not covered by the site transaction. PDF-only exports can remove their staged HTML on success; an existing published site is retained (with `--only`, the build is made in the site itself, which is kept).

### Generating some pages (`--only`)

```bash
lhtml-site --only 03_squelette/04_ik --layout   # one slide, and its layout report
lhtml-site --only 02_rotations --only inf585:04_interpolation_position/content/07_hermite
```

`--only` takes pointers written as in a deck (directory, file, glob,
`name:path`; all the occurrences of a repeated slide) and generates only
these pages, in the site itself: their template, the files of their
directory (assets), the menu and the structure of the site; the
other pages are those of the previous build. Their numbering, their links
(`pathTo_*`) and the ids of the titles are those of a full build. A page that
fails keeps its previous version (put back at the end of the build, as it
was), and the build reports the failure. When there is no previous build (its
record, `.verification/structure.json`, or its site missing), or when
the pages of the site changed (deck, new, renamed or removed page), a full
build is done instead; with `--layout`, it still measures only the pages
named (and those without a report, or whose report was made from another
source), the other pages keep their report (also when only their deck entry
changed: `layout`, `params`; `--layout` measures all of them). Edits of the theme or of files outside the page
directories (shared images, sources included from elsewhere are read from the
sources) need a full build.

## Configuration

```yaml
source_directory: 'src/'               # Source content directory
site_directory: '.site/'               # Output directory
theme: 'webpage-frame'                 # A theme of the generator, or a theme directory
plugin: []                             # Extensions, in order (none by default)
```

`lhtml-site init` writes a `configure.yaml` that explains each of the usual
options, ready to uncomment (the file is
[`src/lhtml_site/configure_example.yaml`](../configure_example.yaml)).

> **Note: `source_directory`.** `lhtml-site init` writes `source_directory: 'src/'`, and every
> tutorial uses `src/`. A configuration **without** the key reads its pages from `src_site/`, the
> default of the generator: write the key.

### Configuration keys

All the keys are optional. An unknown key is ignored with a warning (and a spelling
suggestion); the authoritative list and defaults are `Config` in
[`lhtml_site/configuration.py`](../configuration.py).

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| <a id="key-source_directory"></a>`source_directory` | path | `src_site/` (see the note above) | The pages: `.html.j2` (LHTML) and `.md.j2` ([Markdown](#markdown-pages)) templates, with their assets |
| <a id="key-site_directory"></a>`site_directory` | path | `.site/` | The site, replaced at each build that succeeds; it must not overlap the sources nor the theme (see below) |
| <a id="key-theme"></a>`theme` | name or path | `webpage-frame` | A theme of the generator, named alone (`webpage-frame`, `docs`, `slides`, `slides-pdf`), or the directory of a theme, relative to the configuration file. Not with `targets`. See [Themes](#themes) |
| <a id="key-plugin"></a>`plugin` | list of paths (or one path) | `[]` | The extensions of the project, in order; everything a bundled theme needs is a stage of the build. See [Plugins](advanced.md#plugins) |
| <a id="key-plugin_arg"></a>`plugin_arg` | mapping | `{}` | The options of the plugins, by name (`context.options` of a plugin) |
| <a id="key-keywords"></a>`keywords` | mapping | `{}` | Extra Jinja2 variables of every page (`params`, `page`, `credit`, `credits` are reserved). Some are settings of the theme: `docs:` ([the docs theme](../themes/docs/README.md#settings)), `css`, `cssAbs`, `js`, `jsAbs` ([stylesheets and scripts](#stylesheets-and-scripts-of-the-pages)) |
| <a id="key-debug"></a>`debug` | boolean | `false` | Verbose logging and retained intermediate files; overridden by `--debug` / `--no-debug` |
| <a id="key-title_id"></a>`title_id` | boolean | `true` | Give the headings ids, a stage of the build; `false` for a project that writes its own. See [Heading ids](#heading-ids) |
| <a id="key-use_tidy"></a>`use_tidy` | boolean | `false` | Clean the HTML of the pages with tidy (the library `libtidy`) |
| <a id="key-line-breaks"></a>`line-breaks` | boolean | `false` | The line breaks of the sources are rendered as `<br>` (LHTML's option; `line_breaks` is read too) |
| <a id="key-public_page_keys"></a>`public_page_keys` | list of strings | `[]` | The page settings (of a `config.yaml`, a front matter or a deck entry) kept in the record of the pages, beyond the ones the themes display: for a custom theme or plugin that reads `structure/` of the site (`publish_structure: true`). `src`, the path of a source on your machine, is refused. See [The site is published](#the-site-is-published-the-documents-of-a-project-are-not) |
| <a id="key-publish_sitemap"></a>`publish_sitemap` | boolean | `false` | Write `sitemap/` into the site: a redirection per page, named after its title id, marked `noindex` |
| <a id="key-publish_structure"></a>`publish_structure` | boolean | `false` | Write the pages of the site into `structure/structure.{json,yaml}` of the site, for a custom theme or plugin that reads them there (the build keeps its own record in `.verification/structure.json`) |
| <a id="key-deck"></a>`deck` | path, list or mapping | none: the order of the files | The order of the pages: the path of a deck file, or the deck itself. See [Deck](#deck-order-of-the-slides) |
| <a id="key-decks"></a>`decks` | `directories` | none: the sources are one deck | Each directory of the sources is a deck, built as a site of its own. See [Decks and targets](#decks-and-targets) |
| <a id="key-targets"></a>`targets` | mapping `{name: {theme: ...}}` | none: one build, with `theme` | Each deck is built once per target, with its theme (instead of `theme`, which is then refused). See [Decks and targets](#decks-and-targets) |
| <a id="key-design"></a>`design` | mapping or path | none: the theme's `design.yaml` | Tokens, macros and layouts over those of the theme (a mapping, or the path of a YAML file). See [Design](#design-tokens-macros-and-layouts) |
| <a id="key-katex"></a>`katex` | mapping `{render, macros}` | `render: build` when `quickjs` is installed, else in the browser | Formulas: `render: build` or `browser`; `macros`, a mapping `'\RR': '\mathbb{R}'` given to KaTeX at build and in the browser. See [Formulas](#formulas) |
| <a id="key-cache_video_directory"></a>`cache_video_directory` | path | none: nothing is transcoded | The directory of the transcoded videos; setting it is what asks for them. See [Videos](#videos) |
| <a id="key-chrome"></a>`chrome` | path | none: the Chromium of Playwright | The Chrome executable run by the PDF export, the layout report and `--render`; a macOS `.app` bundle is accepted |
| <a id="key-base_url"></a>`base_url` | string | none: no `404.html` | The path of the site on its server, starting and ending with `/` (`/`, `/docs/`), or a full URL ending with `/`. Set, a theme that declares `not_found:` gets a `404.html` at the root of the site, with absolute links built from it (it is served at any depth); the other pages keep their relative links. See [the 404 page](../themes/docs/README.md#the-404-page) |
| <a id="key-layout"></a>`layout` | mapping | `{}` | Options of the layout report (`--layout`): content root, viewport, thresholds, output directory, design rules. Unrelated to the `layout` of a page, which chooses its arrangement. See [Layout report](advanced.md#layout-report-llm-assisted-slide-layout) |

### How the configuration is read

Configuration precedence is **built-in defaults → the selected YAML file → explicit CLI options**. Only one YAML file is loaded: `configure_example.yaml` is a commented example, not a second layer of defaults.

Relative paths are resolved from the YAML file's directory, independent of the shell's working directory. Absolute paths and `~` are supported. If omitted, `site_directory` defaults to `.site/`, `source_directory` to `src_site/` (see the note above), and `theme` to the generator's bundled `webpage-frame` theme. The default `plugin` list is empty: everything a bundled theme needs is a stage of the build - the page placed in the template of its theme, the heading ids, the menu, the index of a site that has none. A project lists only its own extensions, and the theme declares whether it has a menu (see [Theme: what it declares](advanced.md#theme-what-it-declares-about-the-build)). An explicitly configured relative theme path is relative to the YAML file.

Configuration values are type-checked before generating or cleaning. Runtime fields such as `log`, `args`, and `plugin_paths` cannot be supplied in YAML. A plugin reads its options in `plugin_arg`.

The output directory must not overlap the source or theme directory, even via symbolic links. It must not contain the configuration file, generator installation, or configured video cache. These checks apply to both generation and `--clean`. Cleaning does not require the source/theme to still exist and does not remove Python caches from the working directory.

Page-level `config.yaml` files may be empty or contain only comments. Their metadata must otherwise be a mapping. Template discovery has no default depth limit, skips directory symlink cycles and never enters the site (reached through a link). The generator never writes through a link into the sources or the theme: a symbolic link to a directory is copied into the site as a directory (a linked library of videos is thus copied into each build), and a link to a file is kept only if it is relative and leads to a file of the copy, else the file is copied. A link to a directory containing it is kept only if it is relative and stays in the sources; the site itself is never copied.

Check a project without running plugins, generating the site, or deleting outputs:

```bash
lhtml-site -i configure.yaml --check-config
```

This reports the resolved paths, selected plugin files and logging settings. Missing plugins fail validation before the previous site is touched. The check validates plugin file presence, not plugin execution or optional external dependencies. `--check-config` takes precedence if combined with `--clean`.

### The site is published; the documents of a project are not

The site holds the pages, the assets and the theme, without its Jinja templates
(`template/` of the theme: the build reads them in the theme, the server
would serve them as text). The build keeps the pages of the site in
`.verification/structure.json` (`.verification/<deck>/<target>/` in a
project of several), for `--only` and the plugins, with the keys a theme may
display: a `notes:` or a `message:` written by the author stays out of it,
as does the path of the sources. Two files of the generator go into the site
only when the configuration asks for them: `publish_structure: true` writes
that list into `structure/structure.{json,yaml}` of the site (a custom theme
or plugin that reads it there), `publish_sitemap: true` writes `sitemap/`, a
redirection per page named after its title id (`sitemap/introduction.html`,
marked `noindex` for the search engines), a stable address for a link from
elsewhere. The theme's `theme.yaml` and `design.yaml`, and the templates its
`theme.yaml` names elsewhere than `template/`, stay out of the site too. The site of
an earlier version held all of them: the next build, full or `--only`,
writes a site without them. What is written for the author and
their agent goes to `.structure/`, next to the configuration: `agents.md`
(the procedure), `design.md` (the macros and tokens of the design),
`credits.md` (the origin of the pages and the credits of the images) and
`todo.md` (the planned figures and slides).

A custom theme that needs another page setting in the site lists it in `public_page_keys`:

```yaml
publish_structure: true
public_page_keys: [duration, message]    # kept in structure/structure.json, for the theme
```

### Decks and targets

A course is several decks (a chapter each), and each is published twice: as
slides, and as a PDF. The configuration says so, and one command builds
everything:

Guide: [A course of several chapters](https://scholartools.fr/lhtml/03_recipes/03_pdf/#a-course-of-several-chapters).

```yaml
source_directory: src
site_directory: _site
cache_video_directory: cache_video
decks: directories           # src/01_procedural/, src/02_rigid/, ...: a deck each
targets:
  html: {theme: slides}
  pdf: {theme: slides-pdf}
```

```
_site/01_procedural/html/index.html ...     # target html
_site/01_procedural/01_procedural.pdf       # target pdf: its theme declares export: pdf
_site/01_procedural/images/slide_000.jpg ...
```

- A deck is a directory of the sources (those starting with `.` or `_` are
  not); each is built with its own videos, `cache_video/<deck>/`. Without
  `decks`, the sources are one deck.
- A target is a theme, given by its directory or by the name of a theme of
  the generator. Without `targets`, there is one: `theme`, built into the
  site directory itself.
- The site of a deck for a target is `<site>/<deck>/<target>/`. A target
  whose theme declares `export: pdf` is rendered to `<site>/<deck>/<deck>.pdf`
  and `images/`, and its site is not published (see [PDF export](#pdf-export)).
- `--target html` builds only that target (repeatable, or `--target
  html,pdf`); `--only 01_procedural` builds only that deck, and
  `--only 01_procedural/03_noise` pages of it.
- The builds run one after the other; one that fails does not stop the
  next ones, and the command fails if one did.
- Each build keeps its state apart, under `<deck>/<target>/`: the record of
  what its pages depend on (`.verification/`, for `--only`), its layout
  report (`.layout/`), its credits and todo (`.structure/`; the design and
  the guide for agents stay at the top, they are the project's).
- `--check-config` prints one YAML document per build (`build: {deck,
  target}`); `--lint` checks each deck once; `--render` renders once.
- The pages at the top of the sources belong to no deck: the build says so.
  A project with `decks: directories` and no deck directory is an error.
- A target may not be named `images` (the PDF export writes the images of the slides there).

## Deck: order of the slides

Without a deck, the pages are generated in the order of the files (sorted
paths, hence numbered directories such as `02_rotations/04_representations`).
A deck lists the slides with pointers to their sources, so that the order
does not depend on the names of the directories, slides can come from other
projects, and a slide can appear several times:

```yaml
# deck.yaml (configure.yaml: deck: 'deck.yaml')
title: Talk, short version
duration: 60                          # length of the talk (minutes): a warning beyond
sources:                              # other projects (relative to the deck file)
  inf585: ~/teaching/inf585/lecture/inf585_lecture_slides/src
slides:
  - 00_ouverture/00_titre             # one page (its directory)
  - path: 00_ouverture/02_partie      # parameterized slide...
    title: Plan
    params: {current: 0}
  - 01_introduction                   # directory: all its pages, in file order
  - path: 00_ouverture/02_partie      # ...the same slide again, other parameters
    title: Transformations and rotations
    params: {current: 2}
  - 02_rotations/0[5-8]*              # glob on the page paths
  - 02_rotations                      # the rest of the section
  - path: 02_rotations/13_interpolation   # moved after the rest of the section
    title: Interpolation (summary)    # title in the menu
    duration: 1.5                     # minutes: the build log sums them
  - inf585:04_interpolation_position/content/07_hermite   # slide of another project
  - path: 03_squelette/10_bilan       # planned slide, no source yet
    title: Kinematics, summary
    message: IK = optimisation, FK = composition
  - '!*/00_section'                   # excluded, wherever it is listed
```

- A pointer is a path relative to the source directory: the directory of a
  page, a parent directory (all its pages, in file order, including its own
  page if it has one), a page file (`course/intro.html`, or `sec/index.html`
  for the page of a directory that also holds other pages), or a glob.
  Accented names match whatever the form the file system stores (Unicode
  NFC); `name:path` refers to another project only if `name` is one of the
  `sources` (otherwise it is a path). Hidden files and directories at the top
  level of a source (`.name`) are ignored, as they are not copied.
- A pointer that names a page (its directory or its file) takes precedence
  over parent directories and globs: the page is placed there, and skipped by
  the directories and globs.
- `!pattern` excludes the matching pages from the whole deck
  (`!inf585:*/00_title` for another project).
- A slide may be a mapping with `path` and metadata. `title` replaces the
  title in the menu; `duration` (minutes) is summed in the build log (the
  `duration` of the deck itself is the length of the talk: the log gives the
  total against it, and warns beyond);
  `params` (see below); every other key (`message`, `notes`, ...) is a
  setting of the page given to the plugins (`meta['structure']`), like the
  page `config.yaml`, with the template of each page in the site, `template`,
  and its origin: `src`, its source file, `source`, `occurrence`; only the
  keys a theme displays are written down (see
  [The site is published](#the-site-is-published-the-documents-of-a-project-are-not)). The metadata of a
  directory or a glob applies to each of its pages, except `duration`, which
  is the duration of all its pages together.
- Pages that are not in the deck are not generated (they are listed in the
  build log); the files of their directory (assets) are still copied, and
  their templates can still be included (`{% include 'parts/box.html.j2' %}`:
  Jinja reads the includes from the sources of the project, then of the other
  projects, then from the site).
- A pointer that matches no page is an error (with a suggestion), unless the
  slide has a `title`: it is a planned slide, reported in the log.
  `--scaffold` creates its source, `<path>/index.html.j2` (or `<file>.j2` for
  a pointer to a file), with the title and the other metadata as LHTML
  comments. Existing files are never modified; a planned directory is not
  created inside a directory that already holds pages (a pointer to a file,
  `sec/extra.html`, creates that file only).
- A deck that selects no page gives a warning.

**Other projects.** `sources` gives a name to the source directory of another
project (`name: path`); its pages are named `name:path`. They are generated
under `name/` in the site, with the files and asset directories of their
directory and their `config.yaml` (hidden files are not copied, and linked
directories are copied as directories). The name must not be a
directory of the project nor of the generator (`theme`, `structure`,
`sitemap`). The other project is only read: nothing is copied into its
sources or yours. A source must not contain the site. `--watch` also watches the deck file and, in the other
projects, the directories the deck points to. A page of another project is
rendered in this site: Jinja `extends`/`include` resolve from the sources of
the project, then from the root of the other projects, then from this site
(theme).

**Repeated slides and parameters.** Naming the same page explicitly again
creates another occurrence: it is generated next to the first one
(`index-2.html`, `index-3.html`, ..., skipping the names of the pages of
that directory, so that the names are the same in every build), so its relative assets still work, with
its own place in the navigation and its own metadata. The `params` of an
occurrence are given to Jinja as the variable `params` (empty for the other
pages; `params` is thus not a name for `keywords`), e.g. a plan that
highlights the current part:

```
{% set parts = ["Introduction", "Rotations", "Skeleton"] %}
{% set current = params.current | default(0) %}
div::[margin-left:600px;]
{%- for p in parts %}
* {% if loop.index == current %}**{{ p }}**{% else %}muted:: {{ p }} ::{% endif %}
{%- endfor %}
::
```

(The `{%-` remove the line breaks of the loop, which would otherwise split the
LHTML list.) Directories and globs never repeat a page: once a directory
holds several pages, name the file of the repeated one (`00_plan/index.html`);
an entry that places no page gives a warning.

The menu, the previous/next navigation, the redirection to the first page,
the PDF export and the layout report follow the deck. The sitemap ids
(`pathTo_<id>`, `linkTo_<id>`) are given to the pages of the project first,
so adding pages of other projects or repeated slides does not change them.
`--check-config` also reads the deck and the design (sources, macros). Several decks can share
the same sources (`lhtml-site --deck deck_short.yaml`).

## Markdown pages

A page is written in LHTML (`index.html.j2`) or in Markdown (`index.md.j2`):
the file says which, the generator never guesses it. Both give `index.html`,
and both can sit in the same project, the same deck, the same directory -
not as the same page: `index.html.j2` next to `index.md.j2` is refused.

~~~markdown
---
layout: stack
---
# Noise *functions* {: #noise}

Perlin noise \(n(x)\) is smooth: {{ params.detail | default('see below') }}.

```python
def noise(x): ...
```
~~~

- Jinja runs first, as for an LHTML page: the variables, the includes and
  the macros of Jinja work the same way. The theme wraps the page, its
  content converted alone (the Jinja filter `markdown_page`): a Markdown
  page writes no `{% extends %}`, `{% block content %}` or `<html>`, which
  is refused with a message.
- CommonMark, with tables and strikethrough; raw HTML is kept. A fenced code
  block is highlighted as LHTML highlights `code::[python]`.
- The mathematics `\(...\)` and `\[...\]` is kept as written for KaTeX
  (Markdown alone would read `\(` as `(` and `_` as emphasis); see
  [Formulas](#formulas).
- A heading gets an id as in LHTML (`{: #id}` sets it by hand: `{#id}`
  would be a Jinja comment; see [Heading ids](#heading-ids)); the title of the page is its first heading,
  without its marks. Only the `#` headings: an underlined one
  (`Title` / `=====`) gets no id and does not title the page.
- What is LHTML's is not available: the macros of the design (`gap::`),
  `video::` and its transcoded variants (write `<video>` in HTML), the line
  breaks option, the lint of the values written by hand, and the source map
  (a block of a Markdown page names no line in the layout report nor in the
  comments on the render; a problem is still placed at its line).

## Template variables

Each page is rendered by Jinja2 with:

| Variable | Value |
|----------|-------|
| `pathToRoot` | Relative path to the root of the site (`../../`) |
| `pageID` | Number of the page in the site (order of the files or of the deck), from 0 |
| `pathTo_<id>` | Relative link to the page `<id>` of the sitemap (`<id>`: its title in lower case with `_` for spaces, or the value of `{% set title_id = '...' %}`; `_1`, `_2`... for repeated titles) |
| `linkTo_<id>` | `<a href="...">` to that page |
| `params` | Parameters of the occurrence given by the deck (`params.current`), empty otherwise |
| `page` | Metadata of the page: its `config.yaml` and deck entry (`page.notes`, `page.layout`), title, place in the site |
| `layout` | Layout of the page, when the page sets it with `{% set layout = 'side' %}` (the front matter sets `page.layout` instead, see [Design](#design-tokens-macros-and-layouts)) |
| `credit(file)`, `credits` | Credit of a file of the page, credits of all the pages (see [Credits](#credits-origin-of-the-slides-figures-in-code)) |
| `site_pages` | The pages of the menu, in order (`path`, `title` and the page settings the theme lists in `toc: keys:`); `site_pages[pageID]` is this page. Empty for a theme with no menu |
| `page.math` | The page has formulas: detected in its source, or its setting `math: true` / `math: false` (see [Formulas](#formulas)) |
| `page.math_render` | Where its formulas are rendered: `build` (the page needs `katex.min.css` only) or `browser` (it loads the KaTeX scripts too) |
| `page.katex_options` | The options of KaTeX (delimiters, macros), as JSON for auto-render in the browser |
| keys of `keywords` | Values of the configuration (`params`, `page`, `credit`, `credits` are reserved) |

`{% extends %}`, `{% include %}` and `{% import %}` read the templates of the
project (relative to its source directory), then of the other projects of the
deck, then of the theme (`theme/template/base.html` is `template/base.html`
of the theme), then of the site.

### Stylesheets and scripts of the pages

The themes `webpage-frame`, `slides` and `slides-pdf` add to each page the stylesheets and
scripts listed in four `keywords`, after their own:

| Keyword | Each entry is | Written as |
|---------|---------------|------------|
| `cssAbs` | a stylesheet, as a path from the root of the site | `<link rel="stylesheet" href="{{ pathToRoot }}<entry>">` |
| `jsAbs` | a script, as a path from the root of the site | `<script src="{{ pathToRoot }}<entry>" defer>` |
| `css` | a stylesheet, as written (a URL, or a path relative to each page) | `<link rel="stylesheet" href="<entry>">` |
| `js` | a script, as written | `<script src="<entry>" defer>` |

```yaml
keywords:
  cssAbs: [assets/course.css]     # src/assets/course.css, copied to the site as assets/course.css
```

Despite its name, a `cssAbs` entry is not an absolute URL: it is prefixed with the path to the
root of the site, so that the same file is found from a page at any depth. The `docs` theme reads
its own lists instead, `docs: css:` and `docs: js:` (also from the root of the site; see
[the docs theme](../themes/docs/README.md#settings)).

## Heading ids

The build gives an id to each heading that has none (a stage of the build,
`lhtml_site/headings.py`; `title_id: false` turns it off). An id written by hand
(`==(#mine) Title` in LHTML, `## Title {: #mine}` in Markdown) is kept as written: it is the way
to keep an anchor that a link already uses. The theme chooses the scheme, in its `theme.yaml`
(`heading_ids: scheme:`; see [Theme: what it declares](advanced.md#theme-what-it-declares-about-the-build)):

| Scheme | Themes | `= When something goes wrong` | Unique in |
|--------|--------|-------------------------------|-----------|
| `legacy` (the default) | `webpage-frame`, `slides`, `slides-pdf`, a theme that does not say | `when_something_goes__l1` | the site |
| `slug` | `docs` (`heading_ids: scheme: slug`) | `when-something-goes-wrong` | the page |

**The `legacy` scheme** keeps the ids of the sites already published. The id is the text in
lower case, each of ` -,.:()` becomes `_`, then `__` becomes `_`, characters unsafe in a URL
(`<>"&{}%`, a backquote, a tab) are removed, the result is cut at 20 characters, and the level of
the heading follows (`= Simulation - Mass-springs Cloth` gives `simulation__mass_spr_l1`). This is
the scheme of the generator copied into projects since April 2026, so links into the sites it
built keep working; a repeated id gets `_id2`, `_id3`... The ids of the headings written as text
are unique in the site.

**The `slug` scheme** gives readable ids: the text in lower case, the accents of Latin letters
removed (`œ` gives `oe`), apostrophes dropped, the words of letters and digits joined by `-`,
nothing else kept, never truncated (`Vue d'ensemble` gives `vue-densemble`,
`std::vector, exemples` gives `std-vector-exemples`). A repeated heading gets `-2`, `-3`... in
its page. A generated id never takes an id written by the author in the page, nor one of the ids
the theme reserves for its own elements (`heading_ids: reserved:`, for the `docs` theme
`content`, `toc`, `sidebar`...). See also [the docs theme](../themes/docs/README.md#heading-ids).

**Headings from Jinja.** A heading whose text comes from Jinja
(`= {{ parts[params.current - 1] }}`, a heading in a `{% for %}` loop) gets its id from its text
as rendered, with the scheme of the theme, unique in its page: each occurrence of a page reused
with `params` gets the id of its own title (`= Interpolation de keyframes` gives
`interpolation_de_key_l1` in the `legacy` scheme). The ids of the headings written as text do not
depend on these.

**Where they are read.** The theme webpage-frame lists the level-2 headings with an id of the page
in its "Page content" column, read in the page itself (`theme/js/title_id.js`): the column is the
same over http and from a file opened on disk; the `docs` theme lists the h2 in "On this page".
Nothing about the headings is written into the site; the build keeps their record, for `--only`
(the ids of the pages it does not generate), in `.verification/headings.json` next to the
dependency store (`.verification/<deck>/<target>/` in a project of several). Version 1.0 wrote
`<page>.title_id.json`, a copy `title_id.json` and `structure/title_id.json` into the site: a
custom theme that read them reads the headings of the page instead
(`document.querySelectorAll('h2[id]')`).

## Themes

Four built-in themes are available, named alone in the configuration
(`theme: slides`; see [Getting started](../../../README.md#getting-started-your-first-slides) for which to choose):

- **`webpage-frame/`** — Standard website with navigation menu, suitable for documentation and course pages
- **`docs/`** — Documentation site: search (Pagefind), menu by section and group, "On this page", breadcrumb, previous / next, light and dark, a `404.html` with `base_url`; its settings are the `docs` key of `keywords:` (see [the docs theme](../themes/docs/README.md))
- **`slides/`** — Presentation slides for browser display
- **`slides-pdf/`** — Presentation slides optimized for PDF export

Guide: [Themes](https://scholartools.fr/lhtml/04_themes/).

Themes use Jinja2 template inheritance. The base template provides blocks
that content pages can override; which template and which block is what the
theme declares in its `theme.yaml`, with what the layout analysis must take
as the content of a page - see
[Theme: what it declares about the build](advanced.md#theme-what-it-declares-about-the-build).

## Design: tokens, macros and layouts

A theme can describe its design in `design.yaml`: **tokens** (sizes, colors,
spacing), **macros** (LHTML tags such as `gap::`, `aside::`, `box::`) and
**layouts** of the pages. The `slides` and `slides-pdf` themes provide one,
built from the most frequent idioms of 904 existing slides.

Guide: [Themes](https://scholartools.fr/lhtml/04_themes/#change-the-look).

```
= Inverse kinematics

aside::
img::assets/ik.png[width:450px;]
::

* Describe the position of the end effectors
gap::
* Compute the joint angles
gap::l
center::
videoplay::assets/ik.webm[width:750px;]
credit:: MiloScerny Animation ::
::
```

Macros of the slide themes: `gap::` (`gap::s`, `gap::l`, `gap::xl`),
`small::`, `tiny::`, `large::`, `credit::`, `muted::`, `center::`, `aside::`
(figure in the right column, `aside::[top:400px;]`), `cols::` / `col::`
(`.even`, `.spread`, `.middle`; `col::(.fixed)` keeps its width), `box::`
(`.good`, `.bad`, `.warn`, `.key`), `section::`, `demo::url` (iframe),
`placeholder:: text ::` (a planned figure), `intro::` (text above the columns of
`side`), `media::` (the figures of a layout: `.row`, `.even`, `.fill`,
`.top`/`.middle`/`.bottom`, `.auto`, `.here`).
Brackets still work for exceptions; the classes, style and attributes of
the source are added to those of the macro.

**Layouts.** A page chooses a layout in its **front matter**, the YAML at
its very top; the theme then places and sizes its blocks, and `media::`
holds its figures, fitted in the area of the layout: no positions, widths
or spacers to write.

A page setting can be written in three places, from the least specific to
the most: the `config.yaml` of its directory, the front matter of the page
itself, and its deck entry - the deck is where a talk is arranged, so it
has the last word over what a page says about itself. A page may also set
`layout` as a Jinja variable (`{% set layout = 'side' %}` at its top, only
blank lines, comments, other `{% set %}` and `{% import %}` before it; a
page that writes its own `{% extends %}` sets it outside its `{% block %}`),
which the theme reads directly and which therefore wins over all three.

```
---
layout: side
---
= Forward kinematics

* Each joint angle is set by hand
* Rotations are interpolated

media::
img::assets/fk.jpg
credit:: Image: Wikimedia Commons ::
::
```

Layouts of the slide themes (measured on 780 slides, they cover 68 % of
them; the others, text, text and code, columns, stay in the flow with the
macros):

| Layout | Page |
|--------|------|
| `side` (`side-s`, `side-l`) | Text on the left, figures in the right column below the title (36 % of the slides, also code + figure) |
| `stack` | Text, then figures taking the rest of the slide; `media::(.row)` for a row of figures (21 %) |
| `section` | Section or title slide, centered (11 %) |

A layout is a class of `<body>` (`layout-side`, plus `layout-side-s` for a
variant) styled by its `css` in `design.yaml` (`layouts:` with `css` and
`doc`, documented in `.structure/design.md`); the `design` key adds or
removes layouts like macros.

**Lint.** `lhtml-site --lint` lists the values written by hand in the
pages, including those not in the deck, with what replaces them in the
design: positions (`position:fixed`, `top`, `left`), spacers
(`div::[height:25px;]::` → `gap::`), font sizes in percent (→ `small::`,
`tiny::`, `large::`), line heights, offsets in pixels (except the documented
ones of `aside::`), `display:flex` (→ `cols::`), `text-align:center`
(→ `center::`), gray text (→ `muted::`), `display:none` (→ `(.hidden)`), an
`<iframe>` written by hand (→ `demo::`), sizes of figures in a page with a
layout (→ `media::`), and unknown layouts or layouts without `media::`:

```
src/03_squelette/04_ik/index.html.j2:9: spacer: div::[height:25px;]::
    -> gap::
```

**Rules of the project.** The `lint` section of the design adds the rules of
a deck (an author's habits that the design cannot express):

```yaml
design:
  lint:
    small_text: true          # small::/tiny:: on list items: keep the text at its size
    rules:                    # a pattern of the text (code, math and comments are not read)
      part-number:
        pattern: '\bPart \d'
        advice: 'name the topic: the audience does not remember part numbers'
```

`small_text` reports a `small::` or `tiny::` around list items, or opening
a list item; captions, credits and notes may stay small (a list of references
in `tiny::` is reported too: justify it, or write it without a list). The
patterns are searched in the text only: not in code, math, comments, Jinja,
HTML tags nor URLs. They are listed in
`.structure/design.md` and reported as the other values written by hand.

Each build gives their number (the style debt of the deck), and the layout
report lists them per page (column `lint` of `summary.md`). What LHTML does
not read as text is not linted: code and verbatim blocks, inline code, math,
comments (the lint, the source map and the credits read the sources with the
patterns of LHTML itself, `lhtml_site/source_scan.py`). A value that nothing in the
design covers (an annotation drawn over a figure) can stay.

The generator:

1. merges the theme's `design.yaml` with the `design` key of the
   configuration (a value `null` removes a token or a macro),
2. writes `theme/css/design.css`: the tokens as CSS variables
   (`font: {small: 85%}` gives `--font-small`), then the `css` of each macro,
3. writes their reference in `.structure/design.md` of the project (macros,
   layouts, tokens: for authors and LLMs; the layout report links to it),
4. validates the tokens and the macros (with LHTML), and gives the macros to LHTML without their `css`.

A design file may start from another one with `extends` (relative to the
file), then override it key by key; `slides-pdf` reuses the design of
`slides` this way:

```yaml
extends: ../slides/design.yaml
tokens:
  font: {small: 80%}
```

Change the look of a whole deck in `configure.yaml`:

```yaml
design:
  tokens:
    space: {m: 30px}                 # gap::
    aside: {top: 180px, right: 80px} # aside::
    section: {top: 250px}
  macros:
    note:                            # new macro: note:: text ::
      class: note
      css: '.note { color: var(--color-muted); font-style: italic; }'
      doc: 'Side remark. note:: text ::'
    demo: null                       # remove a macro of the theme
```

Macro fields (see [Macros](https://github.com/drohmer/lhtml/blob/main/README.md#macros) in
LHTML): `tag` (default `div`), `class`, `style`, `attrs`, `empty`, `url`, `variant`, `default`,
plus `css` and `doc` used by the generator. The `design` key may also be the path of a YAML file
with the same structure.

## Formulas

The themes render the formulas with KaTeX, on the pages that have some: the
build finds `\(...\)`, `\[...\]` and `$$...$$` in the source of a page,
outside code, comments and Jinja (a single `$...$` is not a delimiter, so a
price stays text). Formulas a page gets from an included template or a macro
are not seen: the page setting `math: true` (or `math: false`) decides
instead. A page with no formula references no KaTeX file. To install the
rendering at build, see [Formulas](../../../README.md#formulas) in the installation.

- **At build** (`katex: render: build`, the default, with `quickjs`
  installed: the extra `lhtml-site[math]`): the stage Formulas runs the
  `libs/katex/katex.min.js` of the theme in QuickJS, so that the HTML always
  matches the CSS of the theme. The page gets the KaTeX HTML and MathML of
  each formula and `katex.min.css`, without any KaTeX script: no TeX source
  shown while the page loads, and nothing for the PDF export or the layout
  report to wait for. A formula
  KaTeX cannot read is shown in red (`katex-error`) and is a warning at its
  line in the source (an error with `--strict`). The formulas rendered are
  kept in `.verification/katex.json`, by TeX, display mode, options and the
  hash of `katex.min.js`: the next build only renders the new ones.
- **In the browser** (`render: browser`, or `quickjs` missing, which the
  build says in one line): the page loads `katex.min.js` and auto-render,
  which also render the `\begin{equation}`-style environments.
- `katex: macros:` (`{'\RR': '\mathbb{R}'}`) is given to KaTeX in both
  cases.

```yaml
katex:
  render: build                        # or browser: always in the browser
  macros: {'\RR': '\mathbb{R}'}       # for KaTeX, at build and in the browser
```

`lhtml-site doctor` says whether `quickjs` is found.

## PDF export

The theme `slides-pdf` (a theme that declares `export: pdf`) writes
`<deck>.pdf` (`slides.pdf` for a project of one deck) and `images/` (an
image of each slide, 3840 px wide) next to the site directory of its
target; the HTML of the slides is only a step towards them, and is not
kept. To have both the slides in the browser and the PDF at each build, declare two
[targets](#decks-and-targets).

Guide: [Your slides as a PDF](https://scholartools.fr/lhtml/03_recipes/03_pdf/).

It runs Chromium through Playwright for Python (the extra
`lhtml-site[pdf]`: playwright, pypdf, and the Chromium of Playwright), as the
layout report and `--render` do: no Node.js. To install it, see
[PDF export](../../../README.md#pdf-export) in the installation (after pipx:
`pipx inject lhtml-site pypdf`, `pipx inject --include-apps lhtml-site playwright`,
`playwright install --only-shell chromium`); `lhtml-site doctor` says what is found.

The export opens one browser
for the deck, prints a few slides at a time, and prints a slide once it is
ready (fonts loaded, math rendered, images decoded, a frame of each video,
the promises a page or a demo, in an iframe too, registered with
`window.__lhtmlReady`) rather than after a fixed delay; a slide that is not
ready within a minute fails the build. A bar shows the progress on a
terminal. The configuration key `chrome` names another Chromium or Chrome
to run instead.

## Videos

Guide: [A talk with videos](https://scholartools.fr/lhtml/03_recipes/02_talk-with-videos/).

A video of a page (`video::`, `videoplay::` of the slides) is shown as written. Setting
`cache_video_directory:` asks for transcoded variants, which every browser reads:

```yaml
cache_video_directory: cache_video
```

The build then makes, with `ffmpeg` and `ffpb` (`lhtml-site doctor`), an H.264 MP4 and a VP9 WebM
of each video (`.mp4`, `.webm`, `.mkv`) of the `assets/` directory of a page, keeps them in the
cache directory, and copies the variants of these videos into the site
(`assets/cache_video_codecs/` of the page); LHTML then writes a `<source>` per variant. Only the
missing variants are made; the rest of the cache is not copied, and a full build names the
directories of the cache that belong to no video, and removes nothing. With
`decks: directories`, each deck has its own cache, `cache_video/<deck>/`. Unset, nothing is
transcoded.

## Credits, origin of the slides, figures in code

**Credits.** A page declares the credits of its images in its `config.yaml`
(or deck entry), and its `origin` (the slide it was copied from):

```yaml
origin: csc_43043/course_slides/src/08_transformations/02_rotation/01_definition
credits:
  assets/euler.jpg:
    author: J. E. Handmann, 1753
    source: Wikimedia Commons
    license: public domain
    url: https://commons.wikimedia.org/wiki/File:...
  assets/plaque.jpg: Brendan Ward, CC0      # a text is the whole credit
```

In the page, `credit:: {{ credit('assets/euler.jpg') }} ::` writes the
caption from it ("J. E. Handmann, 1753, Wikimedia Commons, public domain"; an
error if the file has no credit; shown as written: `__init__` or `a::b` in a
credit is not read as LHTML), and `credits` lists the credits of all the
pages, for a credits slide (`c.text`: shown as written, the fields `c.author`,
`c.source`... as given):

```
= Credits
small::
{%- for c in credits %}
* {{ c.title }}: {{ c.text }}
{%- endfor %}
::
```

Each build writes `.structure/credits.md`: the origin of each page (`origin`,
or its project), the credits, and the images and videos used by the pages
without credit (`img::`, `video::`, `videoplay::`, the macros showing an image
or a video, `src="..."`; to check: your own figures need none). A page whose
`credits` are invalid fails, with the error: a build publishes nothing, and
with `--only` the other pages are generated (the page keeps its previous
version).

**To do.** `placeholder:: video of the walk cycle ::` draws a planned figure;
each build lists the planned figures (with their line) and the planned slides
of the deck in `.structure/todo.md`, and gives their number in the log.

**Figures in code.** A file `<name>.<format>.py` of the sources (`svg`, `png`,
`pdf`, `jpg`), e.g. `assets/curve.svg.py`, is a script that writes the figure
`assets/curve.svg`: it gets the file to write as its argument and runs in its
directory, with the Python of the generator (install what it imports, e.g.
matplotlib). `<name>.svg.tex` is a standalone LaTeX document (TikZ) made into
SVG with `latex` and `dvisvgm`. The page uses the figure as any other
(`img::assets/curve.svg`). Figures are made in the site, never in the
sources, and kept in `.figures/` next to the configuration under the hash of
their script and of the files of its directory: a figure is made again when
its script or one of those files changes (delete `.figures/` after a change
of data read from elsewhere). A figure that fails gives a
warning with the error.

## Writing slides with an AI agent

[`src/lhtml_site/docs/agents.md`](agents.md) is the procedure for an agent (LLM) that
writes or edits slides: plan in the deck, layouts and macros, `--only
--layout`, `--lint`, how to read the report and when to stop. It does not
depend on the agent used. Each build copies it into `.structure/agents.md` of
the project, next to the configuration (not into the site), and the layout
report links to it. In a slide project, one line in
the file that your agent reads (`AGENTS.md`, `CLAUDE.md`, ...) is enough:

```
To write or edit the slides, follow .structure/agents.md of this project.
```

## Error reporting

A problem is one line, `file:line:column: level: message`, the line being
the one of the source of the page (not of the HTML Jinja wrote), as far as
it is known. A build ends with one line: the pages built, the warnings,
the time, and where the site (or the PDF) is. The stages print with `-v`.

```
src/01_intro/03_noise/index.html.j2:12:1: warning: gap::zz: unknown variant, expected one of s, m, l, xl
src/01_intro/04_grid/index.html.j2:7: error: Jinja: 'missing' is undefined
error: deck 01_intro target html: build failed (previous site kept): 1 page(s) failed
deck 02_shapes target html: 12 page(s) built in 1.4s -> _site/02_shapes/html
```

A line written by Jinja itself (an expression, a theme around the page)
names the page alone; in a build for development (`--serve`, `--watch`,
`--layout`) the source map names the file and line of an included template
too. A path is never cut, and colour is used on a terminal only.

Errors are non-fatal — the generator continues processing remaining files (a page whose Jinja2 rendering fails is skipped), then exits with code 1 if any page or plugin failed (missing plugin, exception in a plugin; use `-d` to see the traceback). With `--strict`, a warning fails the build too. Errors of the deck start with `Deck:` and errors of the design with `Design:`.
