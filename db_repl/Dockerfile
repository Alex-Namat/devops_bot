FROM postgres:15.7-alpine

RUN rm -rf /var/lib/postgresql/data/* 
RUN echo "db_host:5432:*:db_repl_user:db_repl_password" > /var/lib/postgresql/.pgpass
RUN chown postgres:postgres /var/lib/postgresql/.pgpass 
RUN chmod 0600 /var/lib/postgresql/.pgpass
