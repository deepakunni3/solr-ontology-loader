FROM openjdk:8-jre
MAINTAINER  Deepak Unni "deepak.unni3@gmail.com"

# Install pre-requisites
RUN apt-get update && \
  apt-get -y install vim lsof htop wget python3 python3-pip git-core

# Set environment variables
ENV SOLR_USER="solr" \
    SOLR_UID="89830" \
    SOLR_GROUP="solr" \
    SOLR_GID="89830" \
    SOLR_VERSION="4.10.4"

ENV SOLR_DISTRIBUTION="solr-${SOLR_VERSION}"
ENV SOLR_DOWNLOAD_URL=https://archive.apache.org/dist/lucene/solr/${SOLR_VERSION}/${SOLR_DISTRIBUTION}.tgz

# Set user and group
RUN groupadd -r --gid $SOLR_GID $SOLR_GROUP && \
  useradd -r --uid $SOLR_UID --gid $SOLR_GID $SOLR_USER

RUN echo "${SOLR_VERSION} ${SOLR_DISTRIBUTION} ${SOLR_DOWNLOAD_URL}"

# Download Solr
RUN mkdir /opt/solr && \
  cd /opt/solr && \
  wget ${SOLR_DOWNLOAD_URL} && \
  tar -xvzf ${SOLR_DISTRIBUTION}.tgz

RUN chown -R $SOLR_USER:$SOLR_GROUP /opt/solr

# Download owltools
RUN wget http://build.berkeleybop.org/userContent/owltools/owltools -O /usr/bin/owltools && \
  chmod 700 /usr/bin/owltools

# Clone solr-ontology-loader
RUN git clone https://github.com/deepakunni3/solr-ontology-loader.git /opt/solr/solr-ontology-loader
RUN cd /opt/solr/solr-ontology-loader && \
 pip3 install -r requirements.txt

# Download necessary ontologies
RUN wget http://purl.obolibrary.org/obo/uberon/basic.obo -O /opt/solr/solr-ontology-loader/uberon.obo

# Configure Solr
RUN set -e; \
  mkdir /opt/solr/${SOLR_DISTRIBUTION}/example/solr/ontology-core && \
  mkdir /opt/solr/${SOLR_DISTRIBUTION}/example/solr/ontology-core/conf && \
  cp /opt/solr/${SOLR_DISTRIBUTION}/example/solr/collection1/conf/solrconfig.xml /opt/solr/${SOLR_DISTRIBUTION}/example/solr/ontology-core/conf && \
  cp /opt/solr/${SOLR_DISTRIBUTION}/example/solr/collection1/conf/elevate.xml /opt/solr/${SOLR_DISTRIBUTION}/example/solr/ontology-core/conf && \
  cp /opt/solr/solr-ontology-loader/schema/ontology-core-schema.xml /opt/solr/${SOLR_DISTRIBUTION}/example/solr/ontology-core/conf/schema.xml

RUN echo '<?xml version="1.0" encoding="UTF-8" ?><solr persistent="true"><cores hostContext="${hostContext:solr}" defaultCoreName="ontology-core" host="${host:}" hostPort="${jetty.port:8983}" zkClientTimeout="${zkClientTimeout:15000}" adminPath="/admin/cores"><core loadOnStartup="true" transient="false" name="ontology-core" collection="ontology-core" instanceDir="ontology-core/"/></cores></solr>' > /opt/solr/${SOLR_DISTRIBUTION}/example/solr/solr.xml

EXPOSE 8983
WORKDIR /opt/solr

ENTRYPOINT cd /opt/solr/${SOLR_DISTRIBUTION}/example && \
  (nohup java -jar start.jar &) && \
  python3 /opt/solr/solr-ontology-loader/solr_ontology_loader.py --solr_url http://localhost:8983/solr/ontology-core --ontology /opt/solr/solr-ontology-loader/uberon.obo && \
  /bin/bash
