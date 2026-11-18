-- Automatically initialize the dedicated automated test database alongside the main database.
SELECT 'CREATE DATABASE nexora_test_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nexora_test_db')\gexec
