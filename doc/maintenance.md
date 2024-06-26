# Recreate the DB

To recreate the DB using the current state of Debsources file storage as
reference:

1. reset the current DB by either emptying all tables or simply recreating the
   DB, e.g. with:

   $ bin/debsources-dbadmin --dropdb --createdb postgresql:///debsources

2. refill DB backend(s), skipping filesystem:

   $ bin/debsources-update --backend db --backend hooks --backend hooks.db

# Add/remove plugins

To add a plugin:

1. add the (Python) plugin under `debsources/plugins/hook_NAME.py`

2. trigger the `add-package` event:

   $ bin/debsources-update -vvv --backend hooks.fs --backend hooks.db \
    --trigger add-package/NAME

3. add the hook to the `hooks` configuration entry in config(.local).ini

To remove a hook follow the reverse process, but trigger the `rm-package` event
instead.

To rerun a plugin (e.g. if you change its logic), you can follow the above
recipes and do a full rm+add cycle.
