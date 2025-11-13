-- ============================================================================
-- Database Initialization Script
-- ============================================================================
--
-- Creates 3 SEPARATE databases for complete environment isolation:
--   - shia_chatbot_dev   (DEV environment)
--   - shia_chatbot_stage (STAGE environment)
--   - shia_chatbot_prod  (PROD environment)
--
-- This ensures EnvironmentPromotionMixin provides TRUE data isolation.
-- No risk of DEV tests corrupting PROD data.
-- ============================================================================

-- Create DEV database
CREATE DATABASE shia_chatbot_dev
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE shia_chatbot_dev IS 'Development environment database';

-- Create STAGE database
CREATE DATABASE shia_chatbot_stage
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE shia_chatbot_stage IS 'Staging environment database for test users';

-- Create PROD database
CREATE DATABASE shia_chatbot_prod
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE shia_chatbot_prod IS 'Production environment database';

-- Grant all privileges to postgres user on all databases
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_stage TO postgres;
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_prod TO postgres;
