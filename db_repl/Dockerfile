FROM postgres:15.7-alpine

RUN rm -rf /var/lib/postgresql/data/* 

RUN \
    echo "#! /bin/bash \\n\
    spawn pg_basebackup -R -h $DB_HOST -U $DB_REPL_USER -D /var/lib/postgresql/data --slot=replication_slot \\n\
    expect "Password: " \\n\
    send "$DB_REPL_PASSWORD" \\n" > script.sh

RUN chmod +x script.sh


