CREATE TABLE emails (
	id SERIAL PRIMARY KEY,
	email VARCHAR(255)
);
CREATE TABLE phones (
	id SERIAL PRIMARY KEY,
	phone VARCHAR(255)
);

INSERT INTO emails (email) VALUES ('first@email.devops');
INSERT INTO emails (email) VALUES ('second@email.devops');
INSERT INTO phones (phone) VALUES ('89161234567');
INSERT INTO phones (phone) VALUES ('89162345678');

\set DB_REPL_USER `echo "${DB_REPL_USER}"`
\set DB_REPL_PASSWORD `echo "${DB_REPL_PASSWORD}"`
CREATE USER :DB_REPL_USER WITH REPLICATION ENCRYPTED PASSWORD :'DB_REPL_PASSWORD';

CREATE TABLE hba ( lines text ); 
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
\set val 'host replication '  :DB_REPL_USER  ' samenet scram-sha-256'
INSERT INTO hba (lines) VALUES (:'val');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';

ALTER SYSTEM SET logging_collector = on;
ALTER SYSTEM SET log_replication_commands = on;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /oracle/pg_data/archive/%f';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET wal_log_hints = on;

SELECT pg_reload_conf();
