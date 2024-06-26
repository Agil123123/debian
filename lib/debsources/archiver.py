# Copyright (C) 2014-2021  The Debsources developers
# <qa-debsources@lists.alioth.debian.org>.
# See the AUTHORS file at the top-level directory of this distribution and at
# https://salsa.debian.org/qa/debsources/blob/master/AUTHORS
#
# This file is part of Debsources. Debsources is free software: you can
# redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.  For more information
# see the COPYING file at the top-level directory of this distribution and at
# https://salsa.debian.org/qa/debsources/blob/master/COPYING

"""handle the archive of sticky suites"""


import logging

from sqlalchemy import sql

from debsources import db_storage, statistics, updater
from debsources.debmirror import SourcePackage
from debsources.models import Package, Suite


def list_suites(conf, session, archive):
    """return a mapping from suite names to a dict `{'archive': bool, 'db':
    bool}`. The first field tells whether a suite is available via the local
    mirror archive; the second whether it is available in Debsources DB.

    """
    suites = {}  # suite name -> {'archive': bool, 'db': bool}

    def ensure_suite(suite):
        if suite not in suites:
            suites[suite] = {"archive": False, "db": False}

    for suite in archive.ls_suites():
        ensure_suite(suite)
        suites[suite]["archive"] = True

    for suite in statistics.sticky_suites(session):
        ensure_suite(suite)
        suites[suite]["db"] = True

    return suites


def _add_stats_for(conf, session, suite):
    status = updater.UpdateStatus()
    if updater.STAGE_STATS in conf["stages"]:
        updater.update_statistics(status, conf, session, [suite])
    if updater.STAGE_CACHE in conf["stages"]:
        updater.update_metadata(status, conf, session)
    if updater.STAGE_CHARTS in conf["stages"]:
        updater.update_charts(status, conf, session, [suite])


def _remove_stats_for(conf, session, suite):
    status = updater.UpdateStatus()
    if updater.STAGE_STATS in conf["stages"]:
        updater.update_statistics(status, conf, session, [suite])
        # remove newly orphan keys from stats.data
        stats_file = conf["cache_dir"] / "stats.data"
        stats = statistics.load_metadata_cache(stats_file)
        stats = {
            k: v for k, v in stats.items() if not k.startswith("debian_" + suite + ".")
        }
        statistics.save_metadata_cache(stats, stats_file)
    if updater.STAGE_CACHE in conf["stages"]:
        updater.update_metadata(status, conf, session)
    if updater.STAGE_CHARTS in conf["stages"]:
        updater.update_charts(status, conf, session)


def add_suite(conf, session, suite, archive):
    logging.info("add sticky suite %s to the archive..." % suite)

    db_suite = db_storage.lookup_db_suite(session, suite, sticky=True)
    if not db_suite:
        if updater.STAGE_EXTRACT in conf["stages"]:
            updater._add_suite(conf, session, suite, sticky=True)
    else:
        logging.warn("sticky suite %s already exist, looking for new packages" % suite)

    if updater.STAGE_EXTRACT in conf["stages"]:
        for pkg in archive.ls(suite):
            db_package = db_storage.lookup_package(
                session, pkg["package"], pkg["version"]
            )
            if db_package:  # avoid GC upon removal from a non-sticky suite
                if not db_package.sticky and not conf["dry_run"]:
                    logging.debug("setting sticky bit on %s" % pkg)
                    db_package.sticky = True
            else:
                if not conf["single_transaction"]:
                    with session.begin():
                        updater._add_package(pkg, conf, session, sticky=True)
                else:
                    updater._add_package(pkg, conf, session, sticky=True)
        session.flush()  # to fill Package.id-s

    if updater.STAGE_SUITES in conf["stages"]:
        suitemap_q = sql.insert(Suite.__table__)
        suitemaps = []
        for pkg, version in archive.suites[suite]:
            db_package = db_storage.lookup_package(session, pkg, version)
            if not db_package:
                logging.warn(
                    "package %s/%s not found in sticky suite"
                    " %s, skipping" % (pkg, version, suite)
                )
                continue
            if not db_storage.lookup_suitemapping(session, db_package, suite):
                suitemaps.append({"package_id": db_package.id, "suite": suite})
        if suitemaps and not conf["dry_run"]:
            session.execute(suitemap_q, suitemaps)

    _add_stats_for(conf, session, suite)

    logging.info("sticky suite %s added to the archive." % suite)


def remove_suite(conf, session, suite):
    logging.info("remove sticky suite %s from the archive..." % suite)

    db_suite = db_storage.lookup_db_suite(session, suite, sticky=True)
    if not db_suite:
        logging.error("sticky suite %s does not exist in DB, abort." % suite)
        return
    sticky_suites = statistics.sticky_suites(session)

    if updater.STAGE_GC in conf["stages"]:
        for package in (
            session.query(Package)
            .join(Suite, Suite.package_id == Package.id)
            .filter(Suite.suite == suite)
            .filter(Package.sticky)
        ):
            pkg = SourcePackage.from_db_model(package)

            other_suites = (
                session.query(Suite.suite.distinct())
                .filter(Suite.package_id == package.id)
                .filter(Suite.suite != suite)
            )
            other_suites = [row[0] for row in other_suites]

            if not other_suites:
                if not conf["single_transaction"]:
                    with session.begin():
                        updater._rm_package(pkg, conf, session, db_package=package)
                else:
                    updater._rm_package(pkg, conf, session, db_package=package)
            else:
                other_sticky_suites = [s for s in other_suites if s in sticky_suites]
                if not other_sticky_suites and not conf["dry_run"]:
                    # package is only listed in "live" suites, drop sticky flag
                    logging.debug("clearing sticky bit on %s" % pkg)
                    package.sticky = False

            suitemap = db_storage.lookup_suitemapping(session, package, suite)
            if suitemap and not conf["dry_run"]:
                session.delete(suitemap)

        if not conf["dry_run"]:
            session.delete(db_suite)

    _remove_stats_for(conf, session, suite)

    logging.info("sticky suite %s removed from the archive." % suite)
