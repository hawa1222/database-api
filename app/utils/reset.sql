DROP TABLE IF EXISTS testdb.users;

DROP USER IF EXISTS testing @localhost;

DROP DATABASE IF EXISTS testdb;
DROP DATABASE IF EXISTS testdb2;

DELETE FROM api_testing_db.api_users WHERE username != 'hw_master';
