# Jacko

Jacko (pronounced JAH-ko) is a set of Kibana dashboards and visualizations to monitor and analyze [YARN](https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/YARN.html) jobs.

The Jacko.py script reads jobs info from the [MapReduce History Server](https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-hs/HistoryServerRest.html) and indexes it in Elasticsearch.

#### Bootstrap

- Create the Elasticsearch index template:

```sh
curl -XPUT 'elasticsearchhost:9200/_template/jacko?pretty' -H 'Content-Type: application/json' -d @jacko.template.json
```

- Create a Kibana index pattern for "jacko-*":

```sh
curl -f -XPOST -H "Content-Type: application/json" -H "kbn-xsrf: anything" \
     "http://kibanahost:5601/api/saved_objects/index-pattern/jacko-*" \
     -d"{\"attributes\":{\"title\":\"jacko-*\",\"timeFieldName\":\"timestamp\"}}"
```

- Import the Kibana visualizations, then the dashboard
- Install Python dependencies:

```sh
pip install -r requirements.txt
```

- Run Jacko.py with "--time 0" to index all the data from the History Server

### Jacko.py Usage

Fetch jobs from the History Server to Elasticsearch:

```sh
$ Jacko.py --history_server historyserverhost --elasticsearch elasticsearchhost
```

##### Multiple Clusters
You can provide multiple history_server arguments and include cluster ids:
```sh
$ Jacko.py --history_server historyserverhost,my_cluster --history_server anotherhistoryserverhost,my_other_cluster --elasticsearch elasticsearchhost
```

##### More Options
- *--index*: Elasticsearch index, default is "jacko"
- *--type*: Elasticsearch type, default is "history_server"
- *--time*: Get jobs with finish time beginning with this time in ms since epoch, default: 10 minutes ago. Alternatively, you can use *--get_latest_finish_time* to use the latest finish time available for this index, type and cluster in Elasticsearch
- *--max_pool_size*: Max pool size to get jobs concurrently, default is 16
- *--abort_on_error*: Abort on any error during fetching of jobs from any cluster
- *--log_level*: Logging level, default is INFO

### Todos

 - Tests
 - Documentation
 - Get job counters and configuration from the History Server
 - Support [Spark History Server](https://spark.apache.org/docs/latest/monitoring.html)
 - Report live job status using the [ApplicationMaster API](https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapredAppMasterRest.html)

License
----

[Apache License 2.0](LICENSE)
