FROM postgres:15.7-alpine

RUN \
     mkdir -p /oracle/pg_data/archive/ &&\
     chmod -R 777 /oracle/pg_data/archive

COPY init.sql /docker-entrypoint-initdb.d/

