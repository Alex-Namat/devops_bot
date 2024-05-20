CREATE DATABASE DB_DATABASE;
CREATE USER DB_USER WITH PASSWORD 'DB_PASSWORD';
CREATE USER DB_REPL_USER WITH REPLICATION ENCRYPTED PASSWORD 'DB_REPL_PASSWORD';

\c db_devops;
CREATE TABLE emails (
	id SERIAL PRIMARY KEY,
	email VARCHAR(255)
);
CREATE TABLE phones (
	id SERIAL PRIMARY KEY,
	phone VARCHAR(255)
);

GRANT SELECT, INSERT ON emails TO DB_USER;
GRANT ALL ON SEQUENCE emails_id_seq TO DB_USER;

GRANT SELECT, INSERT ON phones TO DB_USER;
GRANT ALL ON SEQUENCE phones_id_seq TO DB_USER;

ALTER SYSTEM SET logging_collector = on;
ALTER SYSTEM SET log_replication_commands = on;
GRANT EXECUTE ON FUNCTION pg_catalog.pg_current_logfile() TO DB_USER;
GRANT EXECUTE ON FUNCTION pg_catalog.pg_read_file(text) TO DB_USER;

CREATE TABLE hba ( lines text ); 
COPY hba FROM 'PG_DATA/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication DB_REPL_USER DB_REPL_HOST/24 scram-sha-256');
INSERT INTO hba (lines) VALUES ('host all all BOT_HOST/32 password');
COPY hba TO 'PG_DATA/pg_hba.conf';

ALTER SYSTEM SET listen_addresses = '*';
ALTER SYSTEM SET hba_file = 'PG_DATA/pg_hba.conf';
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /oracle/pg_data/archive/%f';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET wal_log_hints = on;

INSERT INTO emails (email) VALUES ('first@email.devops');
INSERT INTO emails (email) VALUES ('second@email.devops');
INSERT INTO phones (phone) VALUES ('89161234567');
INSERT INTO phones (phone) VALUES ('89162345678');

SELECT pg_reload_conf();