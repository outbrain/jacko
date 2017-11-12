import logging
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch import helpers


class ElasticsearchReporter(object):
    """
    Reporter for elasticsearch
    """

    def __init__(self, es_host, es_index, es_type):
        """
        :param es_host: Elasticsearch host
        :param es_index: Elasticsearch index
        :param es_type: Elasticsearch type
        """
        self.logger = logging.getLogger(__name__)
        self.es = Elasticsearch(hosts=[es_host])
        self.logger.debug("Connected to Elasticsearch host %s", es_host)
        self.es_index = es_index
        self.es_type = es_type

    def report(self, jobs):
        """
        Index jobs to Elasticsearch

        :param jobs: List of jobs
        """
        actions = ({
            "_index": "%s-%s" % (self.es_index, datetime.fromtimestamp(job["finishTime"] / 1000).strftime("%Y-%m-%d")),
            "_type": self.es_type,
            "_id": job["id"],
            "_source": job,
        } for job in jobs)

        helpers.bulk(client=self.es, actions=actions)

    def get_latest_finish_time(self, cluster_name):
        """
        Get latest finish time for a cluster from Elasticsearch

        :param cluster_name: Name of cluster
        :return: latest finish time for the cluster
        """
        agg_name = 'maxFinishTime'
        query = {
            '_source': False, 'query': {'bool': {'must': [
                {'match': {'_type': self.es_type}},
                {'match': {'cluster': cluster_name}}
            ]}},
            'aggs': {agg_name: {'max': {'field': 'finishTime'}}}, 'size': 0}
        search_results = self.es.search(index=self.es_index, body=query,
                                        filter_path=["aggregations.%s.value" % agg_name])
        agg_value = search_results["aggregations"][agg_name]["value"]
        max_finish_time = "%d" % (0 if agg_value is None else agg_value)
        self.logger.debug("Got max finish time %s for cluster %s", max_finish_time, cluster_name)
        return max_finish_time
