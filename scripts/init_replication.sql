-- Initialize replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';

-- Grant necessary privileges
GRANT CONNECT ON DATABASE shia_chatbot TO replicator;
