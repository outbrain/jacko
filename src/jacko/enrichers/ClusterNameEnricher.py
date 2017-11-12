from Enricher import Enricher


class ClusterNameEnricher(Enricher):
    def __init__(self, cluster_name):
        super(ClusterNameEnricher, self).__init__()
        self.cluster_name = cluster_name

    def enrich(self, obj):
        obj["cluster"] = self.cluster_name


Enricher.register(ClusterNameEnricher)
