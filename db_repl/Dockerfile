FROM postgres:alpine

ARG REPL_USER

RUN echo "#!/bin/bash" > /usr/local/bin/init.sh &&\
    echo "rm -rf /var/lib/postgresql/data/*" >> /usr/local/bin/init.sh &&\
    echo "until pg_basebackup -h db -U ${REPL_USER} -D /var/lib/postgresql/data -P" >> /usr/local/bin/init.sh &&\
    echo "do" >> /usr/local/bin/init.sh && \
    echo "  echo 'Replica not ready, trying again...'" >> /usr/local/bin/init.sh &&\
    echo "  sleep 1" >> /usr/local/bin/init.sh &&\
    echo "done" >> /usr/local/bin/init.sh &&\
    echo "echo 'Backup done, starting replica...'" >> /usr/local/bin/init.sh &&\
    echo "chown -R postgres:postgres /var/lib/postgresql/data" >> /usr/local/bin/init.sh &&\
    echo "chmod 0700 /var/lib/postgresql/data" >> /usr/local/bin/init.sh &&\
    echo "su - postgres -c 'postgres -D /var/lib/postgresql/data'" >> /usr/local/bin/init.sh &&\
    chmod +x /usr/local/bin/init.sh

CMD ["/usr/local/bin/init.sh"]