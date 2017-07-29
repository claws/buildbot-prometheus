Buildbot Prometheus Exporter
============================

``buildbot-prometheus`` is a Python package providing a Prometheus metrics
exporter for a buildbot master. The package should work on Python 2 and
Python 3.


Installation
------------

.. code-block:: console

    $ pip install buildbot_prometheus

The ``setup.py`` file includes an *entry_points* directive that configures
it as a Buildbot *reporters* plugin which simplifies its use in the Buildbot
configuration file.

To use the Prometheus reporter plugin add the following to your buildbot
``master.cfg`` file and (re)start the master.

.. code-block:: python

    c['services'].append(reporters.Prometheus(port=9101))

The buildbot master should now be exposing metrics to Prometheus. You can
check the metrics service using the simple command line tool *curl*:

.. code-block:: console

    $ curl -s localhost:9100/metrics | grep -v "#" | sort
    buildbot_build_requests_duration_seconds{builder_id="1"} 2.0
    buildbot_build_requests_success{builder_id="1"} 1.0
    buildbot_builders_running_total 1.0
    buildbot_builders_running{builder_id="1",builder_name="runtests"} 1.0
    buildbot_builds_duration_seconds{builder_id="1",worker_id="2"} 2.571184
    buildbot_builds_success{builder_id="1",worker_id="2"} 1.0
    buildbot_buildsets_duration_seconds{buildset_id="8"} 2.0
    buildbot_buildsets_success{buildset_id="8"} 1.0
    buildbot_steps_duration_seconds{builder_id="1",step_name="git",step_number="0",worker_id="2"} 1.742647
    buildbot_steps_duration_seconds{builder_id="1",step_name="shell",step_number="1",worker_id="2"} 0.334757
    buildbot_steps_success{builder_id="1",step_name="git",step_number="0",worker_id="2"} 1.0
    buildbot_steps_success{builder_id="1",step_name="shell",step_number="1",worker_id="2"} 1.0
    buildbot_workers_running_total 1.0
    buildbot_workers_running{worker_id="2",worker_name="worker1"} 1.0

A configuration block such as the following example should be added to
the Prometheus configuration file to instruct it to scrape the buildbot
metrics exporter.

.. code-block:: yaml

    scrape_configs:
      - job_name: 'buildbot'
        target_groups:
          - targets: ['localhost:9101']

Prometheus will then automatically associate a ``job`` label of ``buildbot``
with metrics from this exporter. Prometheus will also automatically associate
an ``instance`` label (e.g. 'localhost:9101') too.

All metrics exposed by this exporter are prefixed with the ``buildbot_``
string as a namespace strategy to isolate them from other Prometheus exporters.
This makes them easier to find in metrics consumer and visualisation tools
such as Grafana.

All duration metrics use seconds as the unit of measure.
