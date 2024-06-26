# copyright.debian.net Specification - Version 0.3

The goal is to develop a web application that allow to browse, search, and
publish on the web license and copyright information, as contained in Debian's
`debian/copyright` files.

As a first step, we aim to support only machine-readable `debian/copyright`
files, as described in the relevant [standard][1].

[1]: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/

## Functional requirements

- **location**: the web app will be located at <http://copyright.debian.net>

- it should allow **browsing/searching** through packages/versions as currently
  possible using <http://sources.debian.net>: the user should be able to browse
  by package prefix, or search packages by name

- once a fully-specified package/version is reached in the navigation, the web
  app should return the content of the corresponding **debian/copyright** file:

  - if the file does /not/ conform to the machine-readable format, then only a
    textual dump of the content of the file will be shown (this is the
    least-interesting/useful case)

  - if the file does conform to the machine-readable format, then a proper
    **rendering of the copyright file** will be given, exploiting the (parsable)
    file-structure as much as possible, e.g.:

    - folding license paragraphs
    - adding hyperlinks to the relevant files within <sources.debian.net>

  - adding hyperlinks to the authoritative license URLs, etc.

- when visiting a specific `debian/copyright` file, it should be possible to
  convert it to [**SPDX**][2], offering the ability to download the generated
  XML file

  [2]: https://spdx.org/

- in addition to package-based navigation, the web app will allow to **search
  by file** the set of available debian/copyright files. In the beginning (due
  to the lack of other file-based searches in Debsources), file-based search
  will be limited to SHA256-based search, as currently available for Debsources
  at <http://sources.debian.net/advancedsearch/>.

  It should be possible to search <http://copyright.debian.net> providing a
  SHA256 of some file. In response to such a query the web app should:

  1. search all packages containing files with the given SHA256
  2. parse all the corresponding `debian/copyright` files, as long as they are
     machine readable
  3. return the corresponding copyright and license information; only for that
     file (according to the semantics of "Files:" globs in the corresponding
     `debian/copyright` files).

  Note that there might be inconsistencies in the obtained results: one
  package could claim that a given file is, say, licensed under the GPL3 and
  copyright Joe R. Developer, while another that the very same file is
  licensed under LGPL2 and copyright John Doe. Such inconsistencies should
  _not_ be hidden to the user, but rather shown and highlighted (e.g., with
  presentations like "according to package1/version2 license is...,
  copyright is; ... according to package3/version4 ....").

- extending on the above search-by-file feature, it should be possible to
  request the generation of a **Bill of Material (BoM)**. The query API should
  be extended to allow submitting _a list of SHA256_ files as a single
  request. For long lists, the submission of a compressed version of such a
  list should be supported, for efficiency reasons. The web app should return a
  BoM, consisting of a list of license/copyright statements that match those
  hashes. In case of inconsistencies (as discussed above), they should be
  included in the BoM as well, unless the request specifies a
  best-/first-/random-match policy. It should be possible to request the BoM in
  various formats, including:

  - a simple, human readable, text format (e.g. JSON, as already supported by
    Debsources API calls)
  - [SPDX][2]

  Ideally, a compatible **client-side scanner** tool will be available, to scan
  a given software project available locally, contact copyright.d.n, and return
  a BoM. (Writing the scanner is outside the scope of the present
  specification.)

- **statistics**: we should collect/publish statistics about licenses, in the
  same spirit of the current <http://sources.debian.net/stats/> page

## Non-functional requirements

- the web app will be a **front-end only**. Its back-end will be the same of
  Debsources. In particular, the web app will use the same database and the
  same ORM abstractions on top of it. No specific updated will be deployed
  either. The app will use (read-only) the data maintained up-to-date by
  Debsources.

- **deployment modularity**: the web app should be deployable both on the
  separate <http://copyright.debian.net> website and within Debsources, e.g.,
  starting from a URL like <http://sources.debian.net/copyright/>. To this end,
  the core functionalities will be included in a Flask blueprint and the
  blueprints (copyright & sources) will share the navigation code.

- **debian/copyright rendering module**: the rendering of a machine-readable
  `debian/copyright` should be a separate "debian/copyright renderer"
  component, reusable in a form of a python module. The module should consume
  a Copyright object from python-debian and export it in a jinja template.
  It should be extensible and generic enough to enable other output formats
  such as HTML and anticipate other uses besides Debsources i.e integrate
  it upstream.

- **infobox copyright link**: from <http://sources.debian.net> it should be
  possible, after reaching a fully determined package/version, to follow a link
  "copyright" from the package infobox; that link will lead to the appropriate
  `debian/copyright` rendering page under
  <http://sources.debian.net/copyright/...> (or, equivalently, under
  <http://copyright.debian.net/...>)

- **sources of copyright & license information**: for the time being,
  machine-readable `debian/copyright` files are the only source of
  copyright/license information that we can exploit. In the future we might
  have more, e.g., we might run tools like [FOSSology][3] or [Ninka][4] to
  obtain other statements about license/copyright, potentially different from
  what is contained in `debian/copyright` files. We should take into account
  the possibility of other data providers showing up in the future, and not
  assume that only one data provider will always exist.

  [3]: http://www.fossology.org/projects/fossology
  [4]: http://ninka.turingmachine.org/

- **on-the-fly vs batch parsing of debian/copyright:** for the time being, we
  can parse on the fly `debian/copyright` files when the web app needs
  them. But that is sub-optimal, slow, and potentially dangerous (especially
  when the user asks for the copyright of a file whose SHA256 is very popular:
  in that case we have to parse many `debian/copyright` files, potentially
  leading to DoS scenarios). As soon as the celery migration is completed,
  a plugin should be developped to parse copyright information at update time.
  The result of the plugin will be storing into the DB (in a new table)
  copyright/license statements; the web app will simply have to read those data.
  We should keep in mind this extension, to ease future migrations.

- **debian/copyright parser**: to parse machine-readable `debian/copyright`
  files, we will use the `debian.copyright` module shipped by the
  [python-debian][5]. An example of how to use the module is available at
  <file:///usr/share/doc/python-debian/examples/copyright/check_parse_and_dump.py.gz>

  [5]: https://tracker.debian.org/pkg/python-debian

<!-- Local Variables: -->
<!-- mode: markdown -->
<!-- End: -->
