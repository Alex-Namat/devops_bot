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
CREATE ROLE :DB_REPL_USER WITH REPLICATION ENCRYPTED PASSWORD :'DB_REPL_PASSWORD';
SELECT pg_create_physical_replication_slot('replication_slot');

\set DB_REPL_HOST `echo "${DB_REPL_HOST}"`
CREATE TABLE hba ( lines text ); 
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
\set val 'host replication '  :DB_REPL_USER  ' 0.0.0.0/0 scram-sha-256'
INSERT INTO hba (lines) VALUES (:'val');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf'; 
SELECT pg_reload_conf();