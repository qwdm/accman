DROP DATABASE IF EXISTS accman_test;

CREATE DATABASE accman_test;

\c accman_test

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50),
    password_hash CHAR(32),
    is_external_account BOOLEAN,
    expires INTEGER -- just ts, for simplicity
);

CREATE TABLE policy (
    length INTEGER,
    numbers BOOLEAN,
    uppercase_letters BOOLEAN,
    lowercase_letters BOOLEAN,
    special_symbols BOOLEAN
);

CREATE INDEX accounts_login_idx ON accounts (login);

INSERT INTO accounts (login, password_hash, is_external_account, expires)
VALUES (
    'root',
    '63a9f0ea7bb98050796b649e85481845', -- md5('root')
    false,
    2000000000
);

INSERT INTO policy (length, numbers, uppercase_letters, lowercase_letters, special_symbols)
VALUES (0, false, false, false, false);
