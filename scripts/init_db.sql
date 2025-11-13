-- ============================================================================
-- Database Initialization Script
-- ============================================================================
--
-- Creates 4 SEPARATE databases for complete environment isolation:
--   - shia_chatbot_local (YOUR personal development, not deployed)
--   - shia_chatbot_dev   (DEV environment for frontend/QA team)
--   - shia_chatbot_stage (STAGE environment for beta testing)
--   - shia_chatbot_prod  (PROD environment for real users)
--
-- This ensures EnvironmentPromotionMixin provides TRUE data isolation.
-- No risk of your dev work affecting team's DEV, or DEV tests corrupting PROD.
-- ============================================================================

-- Create LOCAL database (YOUR personal development)
CREATE DATABASE shia_chatbot_local
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE shia_chatbot_local IS 'Personal development database (not deployed)';

-- Create DEV database (team access: frontend + QA)
CREATE DATABASE shia_chatbot_dev
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE shia_chatbot_dev IS 'Development environment database for frontend/QA team';

-- Create STAGE database (beta testing)
CREATE DATABASE shia_chatbot_stage
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE shia_chatbot_stage IS 'Staging environment database for test users';

-- Create PROD database (production)
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
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_local TO postgres;
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_stage TO postgres;
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot_prod TO postgres;
