# Jacko

Jacko (pronounced JAH-ko) is an analysis and visualization tool for the behaviour and performance of Hadoop clusters. It collects data about jobs running on the cluster and indexes it to Elasticsearch, where it can be queried or visualized in Kibana.

It currently supports reading jobs from [MapReduce History Server](https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-hs/HistoryServerRest.html) with plans to support other APIs, e.g.  [Spark History Server](https://spark.apache.org/docs/latest/monitoring.html).

### Bootstrap

#### Using Docker

- Build the image:
```sh
docker build -t jacko .
```

- Start the container in detached mode:
```sh
docker run -d -p 5601:5601 -p 9200:9200 --name jacko1 jacko
```

- Run Jacko to index the jobs from your History Server to Elasticsearch:
```sh
docker exec -i -t jacko1 python jacko/Jacko.py --history_server historyserverhost --elasticsearch localhost
```

- Go to Kibana ([http://localhost:5601/app/kibana](http://localhost:5601/app/kibana)) and start exploring.

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

### More info:

https://www.outbrain.com/techblog/2018/03/meet-jacko-bringing-hadoop-resource-utilization-view/

### Todos

 - Tests
 - Documentation
 - Get job counters and configuration from the History Server
 - Support [Spark History Server](https://spark.apache.org/docs/latest/monitoring.html)
 - Report live job status using the [ApplicationMaster API](https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapredAppMasterRest.html)

License
----

[Apache License 2.0](LICENSE)
