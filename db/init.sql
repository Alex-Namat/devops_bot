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