# Test runner

## Run tests locally

Debsources test suite is managed with [Nose](https://nose.readthedocs.org/). To run the
test suite execute the following from Debsources top-level dir:

```shell
nosetests3 -v debsources/tests/
```

Check [Nose documentation](https://nose.readthedocs.org/en/latest/) for more advanced
options, including how to only run specific tests, based on attributes.

## Run tests in docker

You can run debsources test suite in a docker container using the following commands
(containers must be running):

```shell
cd contrib/docker
docker compose build
docker compose up -d db
docker compose run app /opt/run-tests
```

## Test attributes

To get a list of available test attributes you might try something like:

```shell
rgrep -h @attr debsources/tests/ | tr -d '[:blank:]' | sort -u
```

# Test Postgres DB

To be able to run the tests tagged with attribute 'postgres' you need to have a local
PostgreSQL installation with the ability for the user running the tests to create (and
destroy) a database called 'debsources-test'. On that database you should have enough
privileges to create/drop tables, and perform select/insert/delete queries.

If needed, you can change the name of the test database by changing TEST_DB_NAME in the
tesdata.py module.

# Test data

Large test data for Debsources, including a sample mirror and reference database, are
kept in a separate Git repository to avoid cluttering and making too heavy Debsources
development repository. The test data repository is registered as a submodule under the
`testdata/` directory.

Upon first clone of Debsources repository you might initialize and clone the testdata
submodule by executing:

```
git submodule update --init
```

On successful execution the above will populate `testdata/`.

For more information check
[Git submodule documentation](http://git-scm.com/docs/git-submodule).

## Maintaining testdata reference DB

When the DB structure changes, or when new packages are added to the test data, the
reference DBs contained---in DB dump form---under testdata/ will need to be updated to
avoid test failures. Here is the recommended procedures to do that:

1. start with _clean slate_: clean your DB (e.g., `dropdb debsources`) and your local
   sources directory (e.g., `rm -rf /srv/debsources/sources`). Then re-inizialize an
   empty DB (e.g.,
   `createdb debsources; bin/debsources-dbadmin --createdb postgres:///debsources`)

2. do a _full update run_ using a version of the code base that is trusted enough to
   create the new reference version of the DB to be used for tests (e.g.,
   `bin/debsources-update -vv`)

3. ```shell
   cd testdata/
   make distclean # this will remove old DB dumps.
   make dump # this will create fresh DB dumps based on the current status of the DB just
             # filled by the updater
   ```

4. Now do `git diff` (in testdata/) to ensure that the new state of the reference DB is
   sane. Note: one of the two dump is in Postgres (binary) custom form, so is not
   inspectable; but the other one is in textual (SQL) form, so te diff will be
   meaningful. Ideally, the diff should only contain new data added (e.g., new tables,
   new rows in old tables, etc.) and possibly changes in non-deterministic datas (e.g.,
   timestamps). All other kind of changes should be considered suspicious.

5. If everything is fine:

   ```shell
   git add db/ # this is under testdata/
   git commit
   git push
   cd ..
   git add testdata # this is in the main debsources repo
   git commit
   git push
   ```
