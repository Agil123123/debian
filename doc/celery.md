# Research

## Persistence

With the AQMP backend, tasks are persistent by default (messages are
saved both in-memory and on disk).

http://celery.readthedocs.org/en/latest/internals/reference/celery.backends.amqp.html#celery.backends.amqp.AMQPBackend.Exchange.delivery_mode

By default, if a worker crashes mid-execution, the task will not be
run again. It is possible to enable 'late acks', meaning tasks will be
aknowledged only after a successful execution. Tasks need to be
idempotent for that to work correctly.

- http://celery.readthedocs.org/en/latest/faq.html#faq-acks-late-vs-retry

- http://celery.readthedocs.org/en/latest/configuration.html#celery-acks-late

## Transactional tasks

Celery does not support transactional task queues.

Several libraries try to add the feature:

pyramid_transactional_celery

```

 -> https://pypi.python.org/pypi/pyramid_transactional_celery

Developed for use with pyramid, but does not depend on pyramid.

Uses Zope's transaction library:
https://pypi.python.org/pypi/transaction

Available in debian: python-transaction, depends on
python-zope.interface.

django-transaction-barrier
~~~~~~~~~~~~~~~~~~~~~~~~~~

-> https://libraries.io/pypi/django-transaction-barrier

For django.


Unit tests
----------

For unit testing, tasks can easily be made synchronous.

-> CELERY_ALWAYS_EAGER = True

Workflow
--------


Celery has several ways to define workflows:
http://celery.readthedocs.org/en/latest/userguide/canvas.html


Hooks
~~~~~

Hooks can be run as chord[1], i.e. a group of tasks run in parallel,
with a callback that will be executed once all of the tasks have
completed.

By default on celery 3.1+, if one of the tasks fail, the callback will
not be executed[2] (this behavior can be disabled, or enabled on
celery 3.0).

This mean tasks running the hooks can send the results of the plugins
to a callback which will insert those results into the database.

This solution allows:

 - running the hooks on machines that don't have access to the
   database

 - not importing a package if one of the hooks failed

However, it increases the network overhead. In particular, the ctags
plugin can generate large sets of data (e.g. ~250MB for
chromium-browser, or 100M gziped).

One possible workaround is to pass the data as a local file when the
callback runs on the same machine.

It is possible to run a task on a given worker using
`celery.utils.worker_direct` [3][4]. The current worker of a task can
be retrieved from the task's context[5]: self.request.hostname.

Example:

    @app.task(bind=True)
    def task_A(self):
        worker = worker_direct(self.request.hostname)
        task_B.apply_async((a, b), queue=worker.name)

[1] http://celery.readthedocs.org/en/latest/userguide/canvas.html#chords
[2] http://celery.readthedocs.org/en/latest/userguide/canvas.html#error-handling
[3] http://docs.celeryproject.org/en/latest/configuration.html#celery-worker-direct
[4] http://docs.celeryproject.org/en/latest/internals/reference/celery.utils.html#celery.utils.worker_direct
[5] http://celery.readthedocs.org/en/latest/userguide/tasks.html#context



Data locality
-------------

Resources dependencies
~~~~~~~~~~~~~~~~~~~~~~

The graph of tasks also contains blue nodes, representing resources:

 - mirror

 - database: connection to postgresql

 - extracted sources: the sources extracted by the extract_new stage

When a node does not have edges, it means the resource is needed by
all tasks in the cluster.

Running tasks near the resources
```

The simplest way to run tasks on machine with access to the needed
resources is to create several queues, one for each resource:

- mirror

- database

For example, several workers can listen to the 'mirror' queue, and all
tasks routed to that queue will run only on those workers.

The "extracted sources" resource can't be managed with a single queue:
the sources can be extracted by workers on different machines, and
thus there is no single repository of sources. In this case, we can
dynamically find workers running on the same machine as the
"add_package" task, and direct the hooks tasks on those workers.

# Implementation details

## sqlalchemy session

The session is setup in the DBTask class, which will be used as the
base class for all celery tasks that need to access the database. That
class will be instantiated only once per process (worker) [1].

Tasks that need access to the DB need to be defined this way:

    @app.task(base=DBTask, bind=True)
    do_something_with_db(self, conf, arg):
        self.conf = conf
        thing = self.session.query(Thing).first()

In unit tests, we must close the session of all task classes, for example:

    from debsources.updater.celery import app
    def testSomething(self):
        extract_new(self.conf, self.mirror)

        # retrieve the task from the registry
        # (extract_new does not have session and engine attributes,
        # since it is not based on DBTask

        add_package = app.tasks[
            'debsources.new_updater.tasks.add_package'
        ]
        add_package.session.close()
        add_package.engine.dispose()

[1] http://celery.readthedocs.org/en/latest/userguide/tasks.html#instantiation

## plugin tasks

Celery has a way to define tasks that don't depend on a celery
application: use the `celery.shared_task decorator` instead of
`app.task` decorator[1].

However, in the current implementation the plugins use the DBTask from
celery.py for defining tasks, because those tasks need to access the
database.

The celery worker won't automatically find the tasks, so we can use
the `celeryd_init` signal[2] to import the plugins when the worker is
started.

    @celeryd_init.connect
    def configure_workers(sender=None, conf=None, **kwargs):
        debsources_conf = mainlib.load_conf(mainlib.guess_conffile())
        debsources_conf['observers'], debsources_conf['file_exts'] = \
            mainlib.load_hooks(debsources_conf)

[1] http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-the-shared-task-decorator
[2] http://celery.readthedocs.org/en/latest/userguide/signals.html#celeryd-init

# Celery configuration

## Result backend

To use chords, we need to keep a result backend for keeping the results
of tasks and passing them to other tasks. Result backends are disabled by default, and several choices are available[1]:

- sqlalchemy
- memcached
- redis
- rabbitmq
- ...

[1]
http://celery.readthedocs.org/en/latest/configuration.html#task-result-backend-settings

# Dependencies

- python-celery
- rabbitmq

# Running

## Worker

    bin/debsources-async-celery worker

## Updater

    bin/debsources-async-update
