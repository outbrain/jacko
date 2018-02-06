#!/usr/bin/env python2.7

import argparse
import importlib
import logging
import platform
import sys
import time

from prometheus_client import CollectorRegistry, Counter, Summary, pushadd_to_gateway

from ElasticsearchReporter import ElasticsearchReporter
from HistoryServerClient import HistoryServerClient
from enrichers.ClusterNameEnricher import ClusterNameEnricher
from enrichers.Enricher import Enricher
from scrapers.HistoryServerScraper import HistoryServerScraper

HOST = platform.uname()[1]


def setup_logging(log_level):
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    logging_formatter = logging.Formatter('%(asctime)-15s %(name)-12s %(levelname)s %(message)s')
    handler.setFormatter(logging_formatter)
    logger.addHandler(handler)
    level = logging.getLevelName(log_level)
    logger.setLevel(level)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    return logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Read jobs data from History Server and index it to Elasticsearch')
    parser.add_argument('-time', '--time', type=int, dest='start_time', default=int(round((time.time() - 600) * 1000)),
                        help='Get jobs with finish time beginning with this time in ms since epoch, default: 10 minutes ago')
    parser.add_argument('-g', '--get_latest_finish_time', dest='get_latest_finish_time', action='store_true',
                        default=False,
                        help='Get jobs from latest finish time from elastic search, default is false. Overrides -time')
    parser.add_argument('-es', '--elasticsearch', dest='es_host', default=None, required=True,
                        help='Elasticsearch host')
    parser.add_argument('-i', '--index', dest='es_index', default="jacko",
                        help='Elasticsearch index prefix, default is "jacko"')
    parser.add_argument('-t', '--type', dest='es_type', default="history_server",
                        help='Elasticsearch type, default is "history_server"')
    parser.add_argument('-hs', '--history_server', dest='history_servers', action='append', required=True,
                        help='History Server host and an optional cluster name, e.g. "localhost,MyLocalYarn"')
    parser.add_argument('-p', '--prometheus_pushgateway', dest='prometheus_pushgateways', action='append',
                        required=False, help='Prometheus Pushgateway host')
    parser.add_argument('-m', '--max_pool_size', type=int, dest='max_pool_size', default=16,
                        help='Max pool size to get jobs concurrently, default 16')
    parser.add_argument('-en', '--enricher', dest='enrichers', action='append',
                        help='Enricher module and an optional class name, e.g. "MyEnricher,MyEnricherClass"')
    parser.add_argument('-a', '--abort_on_error', dest='abort_on_error', action='store_true', default=False,
                        help='Abort on error in any cluster, default is false')
    parser.add_argument('-s', '--skip_indexing', dest='skip_indexing', action='store_true', default=False,
                        help='Skip indexing to Elasticsearch, default is false')
    parser.add_argument('-l', '--log_level', dest='log_level', default="INFO",
                        help='Logging level, default is INFO')
    return parser.parse_args()


def parse_history_server_scrapers(args, es_reporter=None):
    """
    :param args: arguments object containing history_servers, start_time and max_pool_size attributes
    :param es_reporter: ElasticsearchReporter object used to query max finish time
    :return: list of name and scraper tuples
    """
    scrapers = []
    for idx, arg in enumerate(args.history_servers):
        if ',' in arg:
            host, name = arg.split(",", 1)
        else:
            host = arg
            name = "cluster%d" % (idx + 1)
        port = HistoryServerClient.DEFAULT_PORT
        if host.find(":") > 0:
            (host, port) = host.split(':')
        start_time = es_reporter.get_latest_finish_time(
            cluster_name=name) if args.get_latest_finish_time else args.start_time
        history_server_client = HistoryServerClient(host=host, port=port, start_time=start_time)
        history_server_scraper = HistoryServerScraper(history_server_client=history_server_client,
                                                      max_pool_size=args.max_pool_size)
        scrapers.append((name, history_server_scraper))
    return scrapers


def parse_enrichers(args):
    """
    :param args: arguments object that might contain an enrichers attribute
    :return: list of enrichers or an empty list if no enricher attribute was found
    """
    enrichers = []
    if args.enrichers:
        for arg in args.enrichers:
            if ',' in arg:
                module_name, class_name = arg.split(",", 1)
            else:
                module_name = class_name = arg
            enricher_module = importlib.import_module(".%s" % module_name, package='enrichers')
            enricher_class = getattr(enricher_module, class_name)
            assert issubclass(enricher_class, Enricher), "%s.%s is not an Enricher" % (module_name, class_name)
            enrichers.append(enricher_class())
    return enrichers


def main():
    args = parse_args()
    logger = setup_logging(args.log_level)
    metrics_registry = CollectorRegistry()
    logger.info("Jacko started")

    es_reporter = ElasticsearchReporter(es_host=args.es_host, es_index=args.es_index, es_type=args.es_type)

    scrapers = parse_history_server_scrapers(args=args, es_reporter=es_reporter)
    logger.debug("Initialized %d scrapers", len(scrapers))

    external_enrichers = parse_enrichers(args)

    all_jobs = []
    jobs_counter = Counter('jobs_scraped', 'Number of jobs scraped', labelnames=['instance', 'cluster_name'],
                           registry=metrics_registry)
    scrape_errors_counter = Counter('scrape_errors', 'Number of errors during scrape',
                                    labelnames=['instance', 'cluster_name', 'exception_type'],
                                    registry=metrics_registry)
    scrape_time = Summary('scrape_time', 'Time to scrape all jobs', labelnames=['instance', 'cluster_name'],
                          registry=metrics_registry)
    for (cluster_name, scraper) in scrapers:
        try:
            with scrape_time.labels(HOST, cluster_name).time():
                jobs = scraper.scrape()
            jobs_counter.labels(HOST, cluster_name).inc(len(jobs))
            scraper_enrichers = [ClusterNameEnricher(cluster_name)]
            enrichers = scraper_enrichers + external_enrichers
            for job in jobs:
                for enricher_class in enrichers:
                    enricher_class.enrich(job)
            all_jobs.extend(jobs)
        except Exception as e:
            logger.exception("Exception encountered while processing cluster %s", cluster_name)
            scrape_errors_counter.labels(HOST, cluster_name, type(e).__name__).inc()
            if args.abort_on_error:
                return "Exception encountered while processing cluster %s, aborting." % cluster_name
    jobs_count = len(all_jobs)
    logger.info("Scraped %d jobs", jobs_count)

    if jobs_count > 0:
        if not args.skip_indexing:
            logger.info("Indexing to Elasticsearch, host %s index %s type %s",
                        es_reporter.es_host, es_reporter.es_index, es_reporter.es_type)
            indexed_jobs_counter = Counter('docs_indexed', 'Number of jobs indexed',
                                           labelnames=['instance', 'elasticsearch_host'],
                                           registry=metrics_registry)
            index_time = Summary('index_time', 'Time to index all jobs', labelnames=['instance', 'elasticsearch_host'],
                                 registry=metrics_registry)
            with index_time.labels(HOST, es_reporter.es_host).time():
                es_reporter.report(all_jobs)
            logger.info("%d jobs indexed in Elasticsearch", jobs_count)
            indexed_jobs_counter.labels(HOST, es_reporter.es_host).inc(jobs_count)
        else:
            logger.info("Skipping indexing to Elasticsearch")

    if args.prometheus_pushgateways:
        Counter('jacko_runs', 'Number of Jacko runs', ['instance'], registry=metrics_registry).labels(HOST).inc()
        for gateway in args.prometheus_pushgateways:
            try:
                pushadd_to_gateway(gateway=gateway, job='jacko', registry=metrics_registry, timeout=5)
            except Exception as e:
                logger.exception('Error pushing metrics to %s' % gateway)

    logger.info("Jacko finished")


if __name__ == '__main__':
    sys.exit(main())
