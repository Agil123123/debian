# Development

- **source code** is available using [Git][1]:

        $ git clone https://salsa.debian.org/qa/debsources.git

  or $ git clone git@salsa.debian.org:qa/debsources.git

  and browsable [on the Web][2].

- please report **bugs** to the [Debian Bug Tracking System][6] (short URL:
  <http://deb.li/debsrcbugs>), against the `qa.debian.org` pseudo-package,
  using a subject line that begins with "debsources:".

  If you use the standard Debian `reportbug` tool, please use the command line:

        $ reportbug -P "User: qa.debian.org@packages.debian.org" -P "Usertags: debsources" qa.debian.org

  (`bin/debsources-reportbug` in the Debsources' Git repo is a convenience
  script that does the above for you)

- for discussions about Debsources please **contact** the
  [debian-qa-debsources mailing list][4] or the `#debian-debsources` IRC channel on [OFTC][5]

- opportunities for new contributors (AKA **easy hacks**) are [available][7] as
  well (short URL: <http://deb.li/debsrceasy>)

[1]: http://git-scm.com/
[2]: https://salsa.debian.org/qa/debsources
[4]: https://lists.alioth.debian.org/mailman/listinfo/qa-debsources/
[5]: http://www.oftc.net/
[6]: https://bugs.debian.org/cgi-bin/pkgreport.cgi?pkg=qa.debian.org;tag=debsources
[7]: https://bugs.debian.org/cgi-bin/pkgreport.cgi?package=qa.debian.org;include=subject:debsources;tag=newcomer

To get started with Debsources development, have a look at the [HACKING](HACKING.md) file.

# Dependencies

## Webapp

Debian packages:

- apache2
- diffstat
- libapache2-mod-fcgid (for FastCGI deployment)
- libapache2-mod-wsgi (for WSGI deployment)
- libjs-highlight.js
- libjs-jquery
- python-debian
- python-flask
- python-flaskext.wtf
- python-magic
- tango-icon-theme

## Infrastructure

(work in progress, likely incomplete)

Debian packages:

- debmirror
- dpkg-dev
- exuberant-ctags
- postgresql >= 9.1
- python-apt
- python-matplotlib
- python-psycopg2
- python-sqlalchemy
- sloccount

## Other

To re-generate the documentation:

- graphviz
- postgresql-autodoc
