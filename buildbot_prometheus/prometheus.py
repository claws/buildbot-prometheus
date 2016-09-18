'''
This reporter exposes Buildbot metrics to Prometheus.

A configuration block such as the following example should be added to
the Prometheus configuration file to instruct it to scrape the buildbot
metrics exporter.

.. code-block:: yaml

    scrape_configs:
      - job_name:       'buildbot'
        target_groups:
          - targets: ['localhost:9101']

Prometheus will then automatically associate a ``job`` label of
``buildbot`` with metrics from this exporter. Prometheus will also
automatically associate an ``instance`` label (e.g. 'localhost:9101')
too.

All metrics exposed are prefixed with the ``buildbot_`` string as a namespace
strategy to isolate them from other Prometheus exporters. This also makes them
easier to find in metrics consumer and visualisation tools such as Grafana.

All duration metrics use seconds as the unit of measure.
'''

from twisted.internet import defer, reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.resource import Resource

from buildbot.util import service
from buildbot.process.results import (
    CANCELLED, EXCEPTION, FAILURE, RETRY, SKIPPED, SUCCESS, WARNINGS)

from prometheus_client import Counter, Gauge
from prometheus_client import CollectorRegistry
from prometheus_client.twisted import MetricsResource


BuildStatusMap = {SUCCESS: 'success',
                  WARNINGS: 'success',
                  FAILURE: 'failure',
                  SKIPPED: 'success',
                  EXCEPTION: 'error',
                  RETRY: 'pending',
                  CANCELLED: 'error'}


def resolve_build_status(state):
    return BuildStatusMap.get(state, 'error')


class Prometheus(service.BuildbotService):
    '''
    This service exposes buildbot metrics to Prometheus.

    Metrics state is initialised at service start and is (mostly) retained
    through a reconfiguration. Instance attributes holding a Prometheus
    metrics item are prefixed with a symbol indicating the kind of metric
    they are. For example:

    - Counters: c_<attr_label>
    - Gauges: g_<attr_label>
    - Histogram: h_<attr_label>
    - Summary: s_<attr_label>

    '''

    name = "Prometheus"

    def __init__(self, port=9101, **kwargs):
        service.BuildbotService.__init__(self, **kwargs)
        log.msg("initialising Prometheus")
        self.port = port
        self.server = None
        self.consumers = []
        self.registry = None
        self.create_metrics()

    @defer.inlineCallbacks
    def reconfigService(self, builders=None, **kwargs):
        '''
        Accumulated metrics are maintained through a reconfigure.
        '''
        log.msg("Reconfiguring Prometheus reporter")
        yield service.BuildbotService.reconfigService(self)
        self.registerConsumers()

    @defer.inlineCallbacks
    def startService(self):
        log.msg("starting Prometheus reporter")
        yield service.BuildbotService.startService(self)
        root = Resource()
        root.putChild(b'metrics', MetricsResource(registry=self.registry))
        self.server = reactor.listenTCP(self.port, Site(root))
        log.msg("Prometheus service starting on {}".format(self.server.port))

    @defer.inlineCallbacks
    def stopService(self):
        log.msg("stopping Prometheus reporter")
        yield self.server.stopListening()
        yield service.BuildbotService.stopService(self)
        self.removeConsumers()

    def create_metrics(self):
        '''
        Create the Prometheus metrics that will be exposed.
        '''
        log.msg("creating Prometheus metrics")
        self.registry = CollectorRegistry()

        # build metrics
        builds_labels = ['builder_id', 'worker_id']
        self.c_builds_success = Counter(
            'buildbot_builds_success',
            'Number of builds reporting success',
            builds_labels,
            registry=self.registry)
        self.c_builds_failure = Counter(
            'buildbot_builds_failure',
            'Number of builds reporting failure',
            builds_labels,
            registry=self.registry)
        self.c_builds_error = Counter(
            'buildbot_builds_error',
            'Number of builds reporting error',
            builds_labels,
            registry=self.registry)
        self.g_builds_duration = Gauge(
            'buildbot_builds_duration_seconds',
            'Number of seconds spent performing builds',
            builds_labels,
            registry=self.registry)

        # builders metrics
        builders_labels = ['builder_id', 'builder_name']
        self.g_builders_running_total = Gauge(
            'buildbot_builders_running_total',
            'Total number of builders running',
            registry=self.registry)
        self.g_builders_running = Gauge(
            'buildbot_builders_running',
            'Number of builders running',
            builders_labels,
            registry=self.registry)

        # buildsets metrics
        buildsets_labels = ['buildset_id']
        self.c_buildsets_success = Counter(
            'buildbot_buildsets_success',
            'Number of buildsets reporting success',
            buildsets_labels,
            registry=self.registry)
        self.c_buildsets_failure = Counter(
            'buildbot_buildsets_failure',
            'Number of buildsets reporting failure',
            buildsets_labels,
            registry=self.registry)
        self.c_buildsets_error = Counter(
            'buildbot_buildsets_error',
            'Number of buildsets reporting error',
            buildsets_labels,
            registry=self.registry)
        self.g_buildsets_duration = Gauge(
            'buildbot_buildsets_duration_seconds',
            'Number of seconds spent performing buildsets',
            buildsets_labels,
            registry=self.registry)

        # build requests metrics
        build_requests_labels = ['builder_id']
        self.g_build_requests_duration = Gauge(
            'buildbot_build_requests_duration_seconds',
            'Number of seconds spent performing build requests',
            build_requests_labels,
            registry=self.registry)
        self.c_build_requests_success = Counter(
            'buildbot_build_requests_success',
            'Number of build requests reporting success',
            build_requests_labels,
            registry=self.registry)
        self.c_build_requests_failure = Counter(
            'buildbot_build_requests_failure',
            'Number of build requests reporting failure',
            build_requests_labels,
            registry=self.registry)
        self.c_build_requests_error = Counter(
            'buildbot_build_requests_error',
            'Number of build requests reporting error',
            build_requests_labels,
            registry=self.registry)

        # steps metrics
        steps_labels = ['step_number', 'step_name', 'builder_id', 'worker_id']
        self.g_steps_duration = Gauge(
            'buildbot_steps_duration_seconds',
            'Number of seconds spent performing build steps',
            steps_labels,
            registry=self.registry)
        self.c_steps_success = Counter(
            'buildbot_steps_success',
            'Number of steps reporting success',
            steps_labels,
            registry=self.registry)
        self.c_steps_failure = Counter(
            'buildbot_steps_failure',
            'Number of steps reporting failure',
            steps_labels,
            registry=self.registry)
        self.c_steps_error = Counter(
            'buildbot_steps_error',
            'Number of steps reporting error',
            steps_labels,
            registry=self.registry)

        # workers metrics
        workers_labels = ['worker_id', 'worker_name']
        self.g_workers_running_total = Gauge(
            'buildbot_workers_running_total',
            'Total number of workers running',
            registry=self.registry)
        self.g_workers_running = Gauge(
            'buildbot_workers_running',
            'Number of workers running',
            workers_labels,
            registry=self.registry)

    @defer.inlineCallbacks
    def registerConsumers(self):
        self.removeConsumers()
        startConsuming = self.master.mq.startConsuming

        handlers = (
            (('builds', None, None), self.buildsConsumer),
            (('builders', None, None), self.buildersConsumer),
            (('buildsets', None, None), self.buildSetsConsumer),
            (('buildrequests', None, None), self.buildRequestsConsumer),
            (('steps', None, None), self.stepsConsumer),
            (('workers', None, None), self.workersConsumer),
        )
        for routingKey, handler in handlers:
            consumer = yield startConsuming(handler, routingKey)
            self.consumers.append(consumer)

    @defer.inlineCallbacks
    def removeConsumers(self):
        for consumer in self.consumers:
            yield consumer.stopConsuming()
        self.consumers = []

    @defer.inlineCallbacks
    def buildsConsumer(self, key, msg):
        '''
        '''
        action = key[2]
        labels = dict(builder_id=msg['builderid'],
                      worker_id=msg['workerid'])
        build_info = yield self.master.data.get(("builds", msg['buildid']))
        log.msg("buildSetsConsumer: build_info:{}".format(build_info))

        if action == 'finished':

            assert msg['complete']
            build_started = msg['started_at']
            build_finished = msg['complete_at']
            build_duration = build_finished - build_started
            duration_seconds = build_duration.total_seconds()
            self.g_builds_duration.labels(labels).set(duration_seconds)

            build_status = resolve_build_status(msg['results'])
            if build_status == 'success':
                self.c_builds_success.labels(labels).inc()
            elif build_status == 'failure':
                self.c_builds_failure.labels(labels).inc()
            elif build_status == 'error':
                self.c_builds_error.labels(labels).inc()

    def buildersConsumer(self, key, msg):
        '''
        The Buildmaster runs a collection of Builders, each of which handles a
        single type of build (e.g. full versus quick), on one or more workers.
        Builders serve as a kind of queue for a particular type of build. Each
        Builder gets a separate column in the waterfall display. In general,
        each Builder runs independently.

        Each builder is a long-lived object which controls a sequence of Builds.
        Each Builder is created when the config file is first parsed, and lives
        forever (or rather until it is removed from the config file). It mediates
        the connections to the workers that do all the work, and is responsible
        for creating the Build objects - Builds.

        This method is responsible for updating builder related metrics. There
        are two builder metrics ``buildbot_builders_running_total`` and
        ``buildbot_builders_running``.

        ``buildbot_builders_running_total`` is a gauge metric used to track the
        total number of running builders. As builders start the metric is
        increased and as they stop the metric is decreased. No extra labels are
        used with this metric.

        ``buildbot_builders_running`` is a gauge metric used to track the
        running state of individual workers by making use of Prometheus multi
        dimensional labels. As builders start, an instance of this metric is
        created by passing ``builder_id`` and ``builder_name`` labels and then
        incremented. When the worker disconnects the same gauge metric is
        decreased. This means that a gauge value of 1 indicates started while
        a gauge value of 0 indicates stopped.
        '''
        action = key[2]
        labels = dict(builder_id=msg['builderid'],
                      builder_name=msg['name'])

        if action == 'started':
            self.g_builders_running_total.inc()
            self.g_builders_running.labels(labels).inc()
        elif action == 'stopped':
            self.g_builders_running_total.dec()
            self.g_builders_running.labels(labels).dec()

    # @defer.inlineCallbacks
    def buildSetsConsumer(self, key, msg):
        '''
        A BuildSet is the name given to a set of Builds that all compile/test
        the same version of the tree on multiple Builders. In general, all these
        component Builds will perform the same sequence of Steps, using the same
        source code, but on different platforms or against a different set of
        libraries.

        Each scheduler creates and submits BuildSet objects to the BuildMaster.
        The buildmaster is responsible for turning the BuildSet into a set of
        BuildRequest objects and queueing them on the appropriate Builders.

        This method is responsible for updating build set related metrics.
        There are four build set metrics:

        - buildbot_buildsets_duration_seconds,
        - buildbot_buildsets_success,
        - buildbot_buildsets_failure,
        - buildbot_buildsets_error

        buildbot_buildsets_duration_seconds is a gauge metric used to
        track the duration of individual build sets by making use of
        Prometheus multi dimensional labels. As build sets complete, an
        instance of this metric is created by passing buildset_id labels and
        then setting the value. This allows visualisation tools to query and
        filter metrics for specific builder combinations.

        Similarly, the other counter metrics record success, failure and
        error states for each build set.

        '''
        action = key[2]
        # TODO: substitute bsid for something more useful. bsid is just
        # a number that increments. A better choice would be something
        # like the repo, project, etc
        labels = dict(buildset_id=msg['bsid'])

        # buildset_info = yield self.master.data.get(("buildsets", msg['bsid']))

        if action == 'complete':

            assert msg['complete']
            buildset_started = msg['submitted_at']
            buildset_finished = msg['complete_at']
            buildset_duration = buildset_finished - buildset_started
            duration_seconds = buildset_duration.total_seconds()
            self.g_buildsets_duration.labels(labels).set(duration_seconds)

            bs_success = resolve_build_status(msg['results'])
            if bs_success == 'success':
                self.c_buildsets_success.labels(labels).inc()
            elif bs_success == 'failure':
                self.c_buildsets_failure.labels(labels).inc()
            elif bs_success == 'error':
                self.c_buildsets_error.labels(labels).inc()

    def buildRequestsConsumer(self, key, msg):
        '''
        A BuildRequest is a request to build a specific set of source code
        on a single Builder. Each Builder runs the BuildRequest as soon as
        it can (i.e. when an associated worker becomes free).

        This method is responsible for updating build request related metrics.
        There are four nuild request metrics:

        - buildbot_build_requests_duration_seconds
        - buildbot_build_requests_success
        - buildbot_build_requests_failure
        - buildbot_build_requests_error

        buildbot_build_requests_duration_seconds is a gauge metric used to
        track the duration of individual build requests by making use of
        Prometheus multi dimensional labels. As build requests complete, an
        instance of this metric is created by passing builder_id labels and
        then setting the value. This allows visualisation tools to query and
        filter metrics for specific builder combinations.

        Similarly, the other counter metrics record success, failure and
        error states for each build request.
        '''
        action = key[2]
        labels = dict(builder_id=msg['builderid'])

        if action == 'complete':
            assert msg['complete']
            br_started = msg['submitted_at']
            br_finished = msg['complete_at']
            br_duration = br_finished - br_started
            duration_seconds = br_duration.total_seconds()
            self.g_build_requests_duration.labels(labels).set(duration_seconds)

            br_success = resolve_build_status(msg['results'])
            if br_success == 'success':
                self.c_build_requests_success.labels(labels).inc()
            elif br_success == 'failure':
                self.c_build_requests_failure.labels(labels).inc()
            elif br_success == 'error':
                self.c_build_requests_error.labels(labels).inc()

    @defer.inlineCallbacks
    def stepsConsumer(self, key, msg):
        '''
        This method is responsible for updating step related metrics. There
        are four steps metrics:

        - buildbot_steps_duration_seconds,
        - buildbot_steps_success
        - buildbot_steps_failure
        - buildbot_steps_error

        buildbot_steps_duration_seconds is a gauge metric used to track
        the duration of individual steps by making use of Prometheus multi
        dimensional labels. As steps complete, an instance of this metric is
        created by passing step_number, step_name, builder_id and worker_id
        labels and then setting the value. This allows visualisation tools
        to query and filter metrics for specific step, builder and worker
        combinations.

        Similarly, the other counter metrics record success, failure and
        error states for each step.
        '''
        action = key[2]

        build_info = yield self.master.data.get(("builds", msg['buildid']))

        labels = dict(step_number=msg['number'],
                      step_name=msg['name'],
                      builder_id=build_info['builderid'],
                      worker_id=build_info['workerid'])

        if action == 'finished':
            assert msg['complete']
            step_started = msg['started_at']
            step_finished = msg['complete_at']
            step_duration = step_finished - step_started
            duration_seconds = step_duration.total_seconds()
            self.g_steps_duration.labels(labels).set(duration_seconds)

            step_success = resolve_build_status(msg['results'])
            if step_success == 'success':
                self.c_steps_success.labels(labels).inc()
            elif step_success == 'failure':
                self.c_steps_failure.labels(labels).inc()
            elif step_success == 'error':
                self.c_steps_error.labels(labels).inc()

    def workersConsumer(self, key, msg):
        '''
        This method is responsible for updating worker related metrics. There
        are two worker metrics ``buildbot_workers_running_total`` and
        ``buildbot_workers_running``.

        ``buildbot_workers_running_total`` is a gauge metric used to track the
        total number of running workers. As workers connect the metric is
        increased and as they disconnect the metric is decreased. No extra
        labels are used with this metric.

        ``buildbot_workers_running`` is a gauge metric used to track the
        running state of individual workers by making use of Prometheus multi
        dimensional labels. As workers connect, an instance of this metric is
        created by passing ``worker_id`` and ``worker_name`` labels and then
        incremented. When the worker disconnects the same gauge metric is
        decreased. This means that a gauge value of 1 indicates connected while
        a gauge value of 0 indicates disconnected.
        '''
        action = key[2]

        labels = dict(worker_id=msg['workerid'],
                      worker_name=msg['name'])

        if action == 'connected':
            self.g_workers_running_total.inc()
            self.g_workers_running.labels(labels).inc()
        elif action == 'disconnected':
            self.g_workers_running_total.dec()
            self.g_workers_running.labels(labels).dec()
