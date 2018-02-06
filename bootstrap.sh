#!/bin/bash

function log {
    echo "$(date "+%Y-%m-%d %T") - $*"
}

function wait_for_webserver {
    until $(curl --output /dev/null --silent --head --fail http://localhost:$1/$2); do 
        log ...
        sleep 1
    done
}

function check_exit_code {
	if [ $? -eq 0 ]; then
        log "Success"
    else
    	log ERROR: Exit code $?
    fi
}

log Starting Elasticsearch...
elasticsearch/bin/elasticsearch -E http.host=0.0.0.0 -q &

log Starting Kibana...
kibana/bin/kibana -H 0.0.0.0 -Q &

log Checking Kibana status...
wait_for_webserver 5601 api/saved_objects/index-pattern
log Kibana is up

log Checking Elasticsearch status...
wait_for_webserver 9200
log Elasticsearch is up

log Pushing index to Kibana...
curl -sS -f -XPOST -H "Content-Type: application/json" -H "kbn-xsrf: anything" \
  "http://localhost:5601/api/saved_objects/index-pattern/jacko-*" \
  -d"{\"attributes\":{\"title\":\"jacko-*\",\"timeFieldName\":\"timestamp\"}}"
check_exit_code

log Pushing template to Elasticsearch...
curl -sS -f -XPUT 'localhost:9200/_template/jacko?pretty' -H 'Content-Type: application/json' -d @/home/jacko/jacko.template.json
check_exit_code

log Done.

trap : TERM INT; while sleep 3600; do :; done & wait