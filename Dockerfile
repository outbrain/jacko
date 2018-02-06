FROM openjdk:jre-alpine

LABEL maintainer="Daniel Avramson<davramson@outbrain.com>"

ENV ES_VERSION=5.6.6 \
    KIBANA_VERSION=5.6.6

RUN apk add --update --quiet --no-progress --no-cache \
		wget \
		bash \
		curl \
		nodejs \
		python \
		py-pip \
 && adduser -D jacko \
 && rm  -rf /tmp/* /var/cache/apk/*

WORKDIR /home/jacko

ADD src/jacko /home/jacko/jacko

ADD bootstrap.sh /home/jacko

ADD elasticsearch /home/jacko

RUN pip install --trusted-host pypi.python.org -r jacko/requirements.txt

USER jacko

RUN wget -q -O - https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VERSION}.tar.gz | tar -zx \
 && mv elasticsearch-${ES_VERSION} elasticsearch \
 && wget -q -O - https://artifacts.elastic.co/downloads/kibana/kibana-${KIBANA_VERSION}-linux-x86_64.tar.gz | tar -zx \
 && mv kibana-${KIBANA_VERSION}-linux-x86_64 kibana \
 && rm -f kibana/node/bin/node kibana/node/bin/npm \
 && ln -s $(which node) kibana/node/bin/node \
 && ln -s $(which npm) kibana/node/bin/npm

CMD bash bootstrap.sh &> /tmp/bootstrap.log

EXPOSE 9200 5601
