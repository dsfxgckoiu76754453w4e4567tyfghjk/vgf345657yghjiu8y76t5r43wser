# MODULE 02: DATABASE SCHEMA
[◀️ Back to Index](./00-INDEX.md) | [Previous](./01-ARCHITECTURE-OVERVIEW.md) | [Next: Authentication ▶️](./03-AUTHENTICATION.md)

---

## 📋 TABLE OF CONTENTS
1. [Schema Overview](#schema-overview)
2. [Authentication & User Tables](#authentication--user-tables)
3. [Admin System Tables](#admin-system-tables)
4. [Chat & Conversation Tables](#chat--conversation-tables)
5. [Knowledge Base & RAG Tables](#knowledge-base--rag-tables)
6. [Marja Official Sources (NEW)](#marja-official-sources-new)
7. [Rejal & Hadith Chain Tables](#rejal--hadith-chain-tables)
8. [Ticket & Support Tables](#ticket--support-tables)
9. [Leaderboard Tables](#leaderboard-tables)
10. [External API Tables](#external-api-tables)
11. [System & Monitoring Tables](#system--monitoring-tables)
12. [Qdrant Collections](#qdrant-collections)

---

## COMPLETE DATABASE SCHEMA

### Architecture Philosophy

The database schema is designed with the following principles:

1. **Separation of Concerns**: Clear distinction between user data, content, analytics, and system operations
2. **Audit Trail**: Comprehensive logging of all actions for compliance and debugging
3. **Flexibility**: JSONB fields for extensibility without schema changes
4. **Performance**: Strategic indexing and partitioning where needed
5. **Hybrid Storage**: PostgreSQL for relational data, Qdrant for vectors, Redis for cache
6. **Token Tracking**: Detailed breakdown of token usage at every stage

### Database Schema (PostgreSQL 15+)

```sql
-- ================================================================
-- AUTHENTICATION & USER MANAGEMENT
-- ================================================================

-- Main users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Authentication fields (email/password OR Google OAuth)
    email VARCHAR(255) UNIQUE,  -- NOT NULL removed for truly anonymous users
    password_hash VARCHAR(255),  -- bcrypt/argon2 hashed password
    google_id VARCHAR(255) UNIQUE,  -- Google OAuth identifier
    
    -- Profile information
    full_name VARCHAR(255),
    profile_picture_url VARCHAR(500),  -- URL if from Google OAuth
    profile_picture_uploaded BOOLEAN DEFAULT FALSE,  -- TRUE if user uploaded custom image
    
    -- Religious preferences
    marja_preference VARCHAR(100),  -- User's selected Marja (e.g., 'Sistani', 'Khamenei')
    preferred_language VARCHAR(10) DEFAULT 'fa',  -- 'fa' (Persian), 'ar' (Arabic), 'en', 'ur'
    
    -- Account status
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    account_type VARCHAR(20) DEFAULT 'free',  -- 'anonymous', 'free', 'premium', 'unlimited', 'test'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT check_auth_method CHECK (
        (email IS NOT NULL AND password_hash IS NOT NULL) OR 
        (google_id IS NOT NULL) OR
        (account_type = 'anonymous' AND email IS NULL AND google_id IS NULL)
    )
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_account_type ON users(account_type);

-- OTP (One-Time Password) verification codes
CREATE TABLE otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,  -- 6-digit code
    purpose VARCHAR(50) NOT NULL,  -- 'email_verification', 'password_reset' ONLY
    
    -- Status tracking
    is_used BOOLEAN DEFAULT FALSE,
    attempts_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE,
    
    -- Link to user (nullable for new registrations)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    CONSTRAINT check_otp_purpose CHECK (purpose IN ('email_verification', 'password_reset'))
);

CREATE INDEX idx_otp_email_purpose ON otp_codes(email, purpose);
CREATE INDEX idx_otp_expires_at ON otp_codes(expires_at);

-- User sessions (for JWT or refresh tokens)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session identification
    session_token VARCHAR(500) UNIQUE NOT NULL,  -- JWT or random token
    refresh_token VARCHAR(500) UNIQUE,
    
    -- Session metadata
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,  -- {device_type, os, browser}
    
    -- Session lifecycle
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);

-- Account linking for cross-platform authentication (Email <-> Google OAuth)
-- Allows users who signed up with one method to log in with another using same email
CREATE TABLE linked_auth_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Provider details
    provider_type VARCHAR(50) NOT NULL,  -- 'email', 'google', 'apple', 'github', etc.
    provider_user_id VARCHAR(255),  -- Provider-specific user ID (e.g., Google ID)
    provider_email VARCHAR(255),  -- Email from provider

    -- Link status
    is_primary BOOLEAN DEFAULT FALSE,  -- The original sign-up method
    is_verified BOOLEAN DEFAULT FALSE,

    -- Metadata
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(user_id, provider_type)
);

CREATE INDEX idx_linked_providers_user_id ON linked_auth_providers(user_id);
CREATE INDEX idx_linked_providers_type ON linked_auth_providers(provider_type);
CREATE INDEX idx_linked_providers_email ON linked_auth_providers(provider_email);

-- User settings and preferences
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- UI preferences
    theme VARCHAR(20) DEFAULT 'light',  -- 'light', 'dark', 'auto'
    font_size VARCHAR(20) DEFAULT 'medium',  -- 'small', 'medium', 'large'
    
    -- Chat preferences
    default_chat_mode VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'fast', 'scholarly', 'deep_search', 'filtered'
    auto_play_quranic_audio BOOLEAN DEFAULT FALSE,
    
    -- Notification settings
    email_notifications_enabled BOOLEAN DEFAULT TRUE,
    push_notifications_enabled BOOLEAN DEFAULT FALSE,
    
    -- Privacy settings
    allow_data_for_training BOOLEAN DEFAULT TRUE,
    show_in_leaderboard BOOLEAN DEFAULT FALSE,
    
    -- Rate limiting tier (managed by system)
    rate_limit_tier VARCHAR(50) DEFAULT 'free',
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- ADMIN & SYSTEM USERS
-- ================================================================

CREATE TABLE system_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Admin role and permissions
    role VARCHAR(50) NOT NULL,  -- 'super_admin', 'content_admin', 'support_admin', 'scholar_reviewer'
    permissions JSONB NOT NULL DEFAULT '[]',  -- ['manage_users', 'manage_content', 'view_analytics', 'view_feedbacks', 'approve_chunks', 'answer_tickets', 'review_quality']
    
    -- Specific capabilities per role
    can_access_dashboard BOOLEAN DEFAULT TRUE,
    can_modify_content BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE,
    can_view_sensitive_data BOOLEAN DEFAULT FALSE,
    can_approve_chunking BOOLEAN DEFAULT FALSE,  -- For content quality control
    can_answer_tickets BOOLEAN DEFAULT FALSE,  -- For support team
    can_review_responses BOOLEAN DEFAULT FALSE,  -- For scholar reviewers
    
    -- Admin status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    assigned_by UUID REFERENCES system_admins(id),  -- Who granted admin access
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,  -- Reason for admin access
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_admin_role CHECK (role IN ('super_admin', 'content_admin', 'support_admin', 'scholar_reviewer'))
);

CREATE INDEX idx_admins_user_id ON system_admins(user_id);
CREATE INDEX idx_admins_role ON system_admins(role);

-- Admin task assignments and tracking
CREATE TABLE admin_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES system_admins(id) ON DELETE CASCADE,
    
    -- Task details
    task_type VARCHAR(50) NOT NULL,  -- 'chunk_review', 'ticket_response', 'content_upload', 'quality_review'
    task_description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'cancelled'
    
    -- Timestamps
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,
    
    -- Related entities
    related_document_id UUID,  -- If task is about a document
    related_ticket_id UUID,  -- If task is about a ticket
    related_chunk_id UUID,  -- If task is about chunk approval
    
    -- Performance tracking
    completion_time_minutes INTEGER,  -- Calculated on completion
    quality_score DECIMAL(3, 2)  -- 0.00 to 1.00, evaluated by super_admin
);

CREATE INDEX idx_admin_tasks_admin_id ON admin_tasks(admin_id);
CREATE INDEX idx_admin_tasks_status ON admin_tasks(status);
CREATE INDEX idx_admin_tasks_assigned_at ON admin_tasks(assigned_at);

-- ================================================================
-- CHAT MANAGEMENT
-- ================================================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- Nullable for truly anonymous chats
    
    -- Conversation metadata
    title VARCHAR(200),  -- Auto-generated, but user can edit
    is_title_auto_generated BOOLEAN DEFAULT TRUE,
    mode VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'fast', 'scholarly', 'deep_search', 'filtered'
    
    -- Privacy settings
    is_anonymous BOOLEAN DEFAULT FALSE,  -- Anonymous chat for logged-in users
    is_truly_anonymous BOOLEAN DEFAULT FALSE,  -- Completely anonymous (no user_id)
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_anonymous_logic CHECK (
        (is_truly_anonymous = TRUE AND user_id IS NULL) OR
        (is_truly_anonymous = FALSE)
    )
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_mode ON conversations(mode);
CREATE INDEX idx_conversations_is_anonymous ON conversations(is_anonymous);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message identification
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    
    -- LLM processing details (only for assistant messages)
    llm_provider VARCHAR(50),  -- 'openai', 'anthropic', 'google', 'cohere', 'openrouter', NULL for user messages
    llm_model VARCHAR(100),    -- 'gpt-4', 'claude-3-sonnet', 'gemini-1.5-pro', NULL for user messages
    llm_purpose VARCHAR(50),  -- 'text_generation', 'classification', 'tool_selection', 'reranking', 'guardrail_check'
    
    -- Detailed Token tracking (CRITICAL FEATURE)
    -- Input token breakdown
    input_tokens_total INTEGER,
    input_tokens_user_prompt INTEGER,
    input_tokens_system_prompt INTEGER,
    input_tokens_rag_context INTEGER,
    input_tokens_web_search_results INTEGER,
    input_tokens_tool_outputs INTEGER,
    input_tokens_memory_context INTEGER,  -- mem0 injected context
    input_tokens_other INTEGER,
    
    -- Output tokens (only for assistant messages)
    output_tokens_generated INTEGER,
    output_tokens_citations INTEGER,
    output_tokens_suggestions INTEGER,
    
    -- Total tokens
    total_tokens_used INTEGER,
    estimated_cost_usd DECIMAL(10, 6),  -- Cost in USD
    
    -- Response quality metadata
    response_quality_score DECIMAL(3, 2),  -- 0.00 to 1.00 (from hallucination detection, etc.)
    has_citations BOOLEAN DEFAULT FALSE,
    citation_count INTEGER DEFAULT 0,
    
    -- Processing metadata (flexible, provider-specific)
    llm_metadata JSONB,  -- Different structure per provider: {finish_reason, temperature, etc.}
    processing_metadata JSONB,  -- {retrieval_time_ms, total_time_ms, cache_hit, etc.}
    
    -- Message status
    is_edited BOOLEAN DEFAULT FALSE,
    generation_stopped_by_user BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_llm_provider ON messages(llm_provider);
CREATE INDEX idx_messages_llm_purpose ON messages(llm_purpose);

-- Message edit history (simplified - no edit_reason, no edited_by)
CREATE TABLE message_edit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Edit details
    previous_content TEXT NOT NULL,
    new_content TEXT NOT NULL,
    
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_message_edits_message_id ON message_edit_history(message_id);

-- User feedback on messages
CREATE TABLE message_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Feedback type
    feedback_type VARCHAR(20) NOT NULL,  -- 'like', 'dislike', 'stop_generation'
    
    -- Detailed feedback (for dislikes)
    dislike_reason VARCHAR(50),  -- 'inaccurate', 'poor_citation', 'not_relevant', 'incomplete', 'inappropriate', 'other'
    feedback_text TEXT,  -- High character limit for detailed feedback (5000 chars)
    
    -- Context
    was_helpful BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_feedback_text_length CHECK (LENGTH(feedback_text) <= 5000)
);

CREATE INDEX idx_feedback_message_id ON message_feedback(message_id);
CREATE INDEX idx_feedback_type ON message_feedback(feedback_type);
CREATE INDEX idx_feedback_created_at ON message_feedback(created_at);

-- A/B testing responses (toggle-able feature)
CREATE TABLE ab_test_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Test enabled flag (system-wide control)
    is_enabled BOOLEAN DEFAULT FALSE,
    
    -- Two variants
    variant_a_content TEXT NOT NULL,
    variant_a_model VARCHAR(100) NOT NULL,
    variant_a_metadata JSONB,
    
    variant_b_content TEXT NOT NULL,
    variant_b_model VARCHAR(100) NOT NULL,
    variant_b_metadata JSONB,
    
    -- User selection
    user_selected_variant VARCHAR(1),  -- 'A', 'B', or NULL if no selection
    selection_time_seconds INTEGER,  -- How long user took to decide
    
    -- Test metadata
    test_purpose VARCHAR(100),  -- 'model_comparison', 'prompt_testing', etc.
    scheduled_during_off_peak BOOLEAN DEFAULT TRUE,  -- Recommendation to run during off-peak
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    selected_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ab_tests_message_id ON ab_test_responses(message_id);
CREATE INDEX idx_ab_tests_is_enabled ON ab_test_responses(is_enabled);

-- ================================================================
-- KNOWLEDGE BASE & RAG ARCHITECTURE
-- ================================================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Document identification
    title VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255),
    document_type VARCHAR(50) NOT NULL,  -- 'hadith', 'quran', 'tafsir', 'fiqh', 'book', 'article', 'fatwa', 'doubts_response', 'rejal', 'other'
    
    -- Source information
    source_reference VARCHAR(500),  -- Book name, hadith collection, article URL, etc.
    author VARCHAR(255),
    publisher VARCHAR(255),
    publication_date DATE,
    language VARCHAR(10) DEFAULT 'fa',  -- 'fa' (Persian), 'ar' (Arabic), 'en', 'ur'
    
    -- Religious context (NOT all documents need this)
    fiqh_category VARCHAR(100),  -- NULL if not Ahkam-related (e.g., 'prayer', 'fasting', 'zakat')
    
    -- Document classification
    primary_category VARCHAR(100) NOT NULL,  -- 'aqidah', 'fiqh', 'akhlaq', 'tafsir', 'history', 'doubts', 'rejal', 'general'
    secondary_categories JSONB DEFAULT '[]',  -- Multiple categories possible
    tags JSONB DEFAULT '[]',  -- Flexible tagging
    
    -- File type classification (for pre-processing optimization)
    file_type_category VARCHAR(50),  -- 'clean_text', 'ocr_required', 'asr_required', 'structured', 'other'
    requires_ocr BOOLEAN DEFAULT FALSE,  -- TRUE for PDFs, images that need OCR
    requires_asr BOOLEAN DEFAULT FALSE,  -- TRUE for Audios, Voices that need ASR
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed', 'awaiting_chunk_approval'
    chunk_count INTEGER DEFAULT 0,
    total_characters INTEGER,
    
    -- Chunking configuration
    chunking_mode VARCHAR(20) DEFAULT 'auto',  -- 'auto', 'manual'
    chunking_method VARCHAR(50),  -- 'semantic', 'fixed_size', 'paragraph', 'custom'
    chunk_size INTEGER DEFAULT 768,  -- Optimized for Persian/Arabic (larger than English)
    chunk_overlap INTEGER DEFAULT 150,  -- Optimized overlap for Persian/Arabic
    
    -- Quality and verification
    is_verified BOOLEAN DEFAULT FALSE,  -- Verified by scholar/admin
    verification_notes TEXT,
    quality_score DECIMAL(3, 2),  -- 0.00 to 1.00
    
    -- Chunking approval (NEW FEATURE)
    requires_chunk_approval BOOLEAN DEFAULT TRUE,  -- Can be turned off for automatic processing
    chunk_approval_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'needs_revision'
    chunk_approved_by UUID REFERENCES system_admins(id),
    chunk_approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    retrieval_count INTEGER DEFAULT 0,  -- How many times chunks were retrieved
    citation_count INTEGER DEFAULT 0,   -- How many times cited in responses
    
    -- Metadata (flexible field for additional info)
    additional_metadata JSONB DEFAULT '{}',
    
    -- Admin tracking
    uploaded_by UUID REFERENCES system_admins(id),
    verified_by UUID REFERENCES system_admins(id),
    
    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_category ON documents(primary_category);
CREATE INDEX idx_documents_language ON documents(language);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX idx_documents_chunk_approval_status ON documents(chunk_approval_status);
CREATE INDEX idx_documents_file_type_category ON documents(file_type_category);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Chunk content
    chunk_text TEXT NOT NULL,  -- Actual text content
    chunk_index INTEGER NOT NULL,  -- Position in document (0-based)
    
    -- Chunk metadata
    char_count INTEGER NOT NULL,
    word_count INTEGER,
    token_count_estimated INTEGER,  -- Estimated tokens (for cost calculation)
    
    -- Context preservation
    previous_chunk_id UUID REFERENCES document_chunks(id),  -- Link to previous chunk for context
    next_chunk_id UUID REFERENCES document_chunks(id),      -- Link to next chunk
    
    -- Chunking strategy info
    chunking_method VARCHAR(50),  -- 'semantic', 'fixed_size', 'paragraph', 'custom'
    overlap_with_previous INTEGER DEFAULT 0,  -- Characters of overlap
    
    -- Flexible metadata (for chunk-specific info)
    chunk_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_index ON document_chunks(chunk_index);

-- Dynamic vector DB abstraction (to support future migration from Qdrant)
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    -- Embedding identification
    embedding_model VARCHAR(100) NOT NULL,  -- 'gemini-text-embedding-004', 'cohere-embed-v3'
    embedding_model_version VARCHAR(50),
    vector_dimension INTEGER NOT NULL,
    
    -- Vector DB integration (DYNAMIC - not tied to Qdrant only)
    vector_db_type VARCHAR(50) NOT NULL DEFAULT 'qdrant',  -- 'qdrant', 'elasticsearch', 'milvus', etc.
    vector_db_collection_name VARCHAR(100) NOT NULL,
    vector_db_point_id UUID NOT NULL,  -- ID in the vector DB
    vector_db_metadata JSONB,  -- DB-specific metadata
    
    -- Embedding metadata
    embedding_generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding_cost_usd DECIMAL(10, 8),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,  -- FALSE if superseded by new embedding
    
    UNIQUE(chunk_id, embedding_model, vector_db_collection_name)
);

CREATE INDEX idx_embeddings_chunk_id ON document_embeddings(chunk_id);
CREATE INDEX idx_embeddings_model ON document_embeddings(embedding_model);
CREATE INDEX idx_embeddings_vector_db_point ON document_embeddings(vector_db_point_id);
CREATE INDEX idx_embeddings_vector_db_type ON document_embeddings(vector_db_type);

-- Citations (tracks which documents were used in which responses)
CREATE TABLE message_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    -- Citation details
    relevance_score DECIMAL(5, 4) NOT NULL,  -- 0.0000 to 1.0000 (from reranker)
    citation_text TEXT,  -- Excerpt shown to user
    citation_order INTEGER,  -- Order of citation in response (1, 2, 3...)
    
    -- CLARIFICATION: This field tracks whether the citation was actually shown to the user
    -- (Some retrieved chunks might not make it to the final response due to context limits)
    is_displayed BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_citations_message_id ON message_citations(message_id);
CREATE INDEX idx_citations_document_id ON message_citations(document_id);
CREATE INDEX idx_citations_chunk_id ON message_citations(chunk_id);

-- ================================================================
-- MARJA OFFICIAL WEBSITES & AHKAM SOURCES
-- ================================================================
-- CRITICAL: For Ahkam (religious rulings), we DO NOT use RAG retrieval.
-- Instead, we fetch directly from official Marja websites with maximum citations.
-- This table allows admins to configure and manage these official sources.

CREATE TABLE marja_official_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Marja identification
    marja_name VARCHAR(255) NOT NULL,  -- 'Sistani', 'Khamenei', 'Makarem Shirazi', etc.
    marja_name_arabic VARCHAR(255),
    marja_name_persian VARCHAR(255),
    marja_name_english VARCHAR(255),

    -- Official website information
    official_website_url VARCHAR(500) NOT NULL,
    website_language VARCHAR(10),  -- 'fa', 'ar', 'en', 'ur'
    website_type VARCHAR(50),  -- 'primary', 'secondary', 'mobile', 'api'

    -- API or Scraping configuration
    has_official_api BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(500),
    api_key_required BOOLEAN DEFAULT FALSE,
    api_documentation_url VARCHAR(500),

    -- Web scraping configuration (if no API available)
    scraping_enabled BOOLEAN DEFAULT TRUE,
    scraping_config JSONB,  -- {selectors, url_patterns, rate_limits, etc.}

    -- Fatwa/Ahkam specific URLs
    ahkam_section_url VARCHAR(500),  -- Direct link to Ahkam/Fatwa section
    search_url VARCHAR(500),  -- Search endpoint URL
    search_method VARCHAR(10) DEFAULT 'GET',  -- 'GET', 'POST'
    search_parameters JSONB,  -- {query_param: 'q', filters: {...}}

    -- Content structure
    response_format VARCHAR(50),  -- 'html', 'json', 'xml', 'text'
    content_selectors JSONB,  -- {title: '.fatwa-title', content: '.fatwa-body', ...}

    -- Reliability & Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,  -- Verified by scholar/admin
    last_verified_at TIMESTAMP WITH TIME ZONE,
    last_successful_fetch_at TIMESTAMP WITH TIME ZONE,

    -- Rate limiting (respect website policies)
    requests_per_minute INTEGER DEFAULT 10,
    requests_per_hour INTEGER DEFAULT 100,

    -- Caching policy
    cache_duration_hours INTEGER DEFAULT 24,  -- How long to cache responses

    -- Contact information
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),

    -- Metadata
    notes TEXT,
    additional_metadata JSONB DEFAULT '{}',

    -- Admin tracking
    added_by UUID REFERENCES system_admins(id),
    verified_by UUID REFERENCES system_admins(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_marja_sources_name ON marja_official_sources(marja_name);
CREATE INDEX idx_marja_sources_active ON marja_official_sources(is_active);
CREATE INDEX idx_marja_sources_language ON marja_official_sources(website_language);

-- Tracking Ahkam fetches from official sources
CREATE TABLE ahkam_fetch_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marja_source_id UUID NOT NULL REFERENCES marja_official_sources(id) ON DELETE CASCADE,

    -- Request details
    question_text TEXT NOT NULL,
    question_category VARCHAR(100),  -- 'prayer', 'fasting', 'zakat', etc.

    -- Response details
    fetch_status VARCHAR(50),  -- 'success', 'failed', 'no_result', 'rate_limited'
    response_found BOOLEAN DEFAULT FALSE,
    response_text TEXT,
    response_url VARCHAR(500),  -- Direct link to the ruling on official website

    -- Citation information
    citation_title VARCHAR(500),
    citation_reference VARCHAR(500),  -- Book/section reference if available

    -- Performance
    fetch_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,

    -- Quality
    confidence_score DECIMAL(3, 2),  -- How confident are we in this result

    -- Error handling
    error_message TEXT,

    -- Timestamps
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ahkam_fetch_source ON ahkam_fetch_log(marja_source_id);
CREATE INDEX idx_ahkam_fetch_status ON ahkam_fetch_log(fetch_status);
CREATE INDEX idx_ahkam_fetch_date ON ahkam_fetch_log(fetched_at);

-- ================================================================
-- REJAL & HADITH CHAIN VALIDATION (NEW FEATURE)
-- ================================================================

-- Rejal: Narrator/transmitter information for hadith authentication
CREATE TABLE rejal_persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Person identification
    name_arabic VARCHAR(255) NOT NULL,
    name_persian VARCHAR(255),
    name_english VARCHAR(255),
    kunyah VARCHAR(100),  -- Abu/Umm name
    laqab VARCHAR(100),  -- Descriptive title
    
    -- Biographical info
    birth_year INTEGER,
    death_year INTEGER,
    birth_place VARCHAR(255),
    lived_in JSONB DEFAULT '[]',  -- List of places lived
    
    -- Reliability rating (by Shia scholars)
    reliability_rating VARCHAR(50),  -- 'thiqah' (reliable), 'da`if' (weak), 'matruk' (abandoned), etc.
    reliability_score DECIMAL(3, 2),  -- 0.00 to 1.00 (calculated from multiple sources)
    reliability_sources JSONB DEFAULT '[]',  -- References to Rejal books
    
    -- Additional metadata
    teachers JSONB DEFAULT '[]',  -- List of teacher IDs
    students JSONB DEFAULT '[]',  -- List of student IDs
    biographical_notes TEXT,
    additional_metadata JSONB DEFAULT '{}',
    
    -- Admin tracking
    added_by UUID REFERENCES system_admins(id),
    verified_by UUID REFERENCES system_admins(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rejal_name_arabic ON rejal_persons(name_arabic);
CREATE INDEX idx_rejal_reliability_rating ON rejal_persons(reliability_rating);
CREATE INDEX idx_rejal_reliability_score ON rejal_persons(reliability_score);

-- Hadith narration chains (Sanad/Isnad)
CREATE TABLE hadith_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Related hadith text (stored in documents table)
    hadith_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    hadith_text TEXT NOT NULL,
    
    -- Chain metadata
    chain_type VARCHAR(50),  -- 'full_chain', 'broken_chain', 'suspended', 'mursal'
    source_book VARCHAR(255),  -- Original hadith collection
    hadith_number VARCHAR(50),  -- Number in the collection
    
    -- Chain quality assessment
    overall_reliability VARCHAR(50),  -- 'sahih', 'hasan', 'da`if', 'mawdu`'
    reliability_score DECIMAL(3, 2),  -- 0.00 to 1.00 (calculated from narrator chain)
    
    -- Visualization data (for graph display)
    chain_graph_data JSONB,  -- {nodes: [...], edges: [...]} for frontend visualization
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hadith_chains_document_id ON hadith_chains(hadith_document_id);
CREATE INDEX idx_hadith_chains_reliability ON hadith_chains(overall_reliability);
CREATE INDEX idx_hadith_chains_score ON hadith_chains(reliability_score);

-- Individual narrators in a specific chain
CREATE TABLE chain_narrators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id UUID NOT NULL REFERENCES hadith_chains(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES rejal_persons(id) ON DELETE CASCADE,
    
    -- Position in chain
    position INTEGER NOT NULL,  -- 1 = first narrator (closest to Prophet/Imam), higher = later
    
    -- Relationship to next narrator
    transmission_method VARCHAR(100),  -- 'heard from', 'was told by', 'on authority of'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(chain_id, position)
);

CREATE INDEX idx_chain_narrators_chain_id ON chain_narrators(chain_id);
CREATE INDEX idx_chain_narrators_person_id ON chain_narrators(person_id);
CREATE INDEX idx_chain_narrators_position ON chain_narrators(position);

-- ================================================================
-- TICKET SUPPORT SYSTEM (NEW FEATURE)
-- ================================================================

CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(50) UNIQUE NOT NULL,  -- User-facing ticket ID (e.g., "TICKET-2024-001234")
    
    -- User information
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL if ticket from anonymous user
    user_email VARCHAR(255),  -- In case anonymous user provides email
    user_name VARCHAR(255),
    
    -- Ticket details
    subject VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),  -- 'bug_report', 'feature_request', 'content_issue', 'technical_issue', 'general_inquiry'
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    
    -- Status
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'in_progress', 'waiting_user', 'resolved', 'closed'
    
    -- Assignment
    assigned_to UUID REFERENCES system_admins(id),  -- Support admin who will handle it
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Resolution
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES system_admins(id),
    
    -- Performance tracking
    first_response_time_minutes INTEGER,  -- Time from creation to first admin response
    resolution_time_minutes INTEGER,  -- Time from creation to resolution
    
    -- Related entities
    related_conversation_id UUID REFERENCES conversations(id),
    related_message_id UUID REFERENCES messages(id),
    related_document_id UUID REFERENCES documents(id),
    
    -- Attachments
    attachments JSONB DEFAULT '[]',  -- [{filename, url, size}]
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_assigned_to ON support_tickets(assigned_to);
CREATE INDEX idx_tickets_created_at ON support_tickets(created_at);
CREATE INDEX idx_tickets_ticket_number ON support_tickets(ticket_number);

-- Ticket messages/responses (conversation thread)
CREATE TABLE ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    
    -- Message details
    sender_type VARCHAR(20) NOT NULL,  -- 'user', 'admin', 'system'
    sender_id UUID,  -- user_id or admin_id
    message_text TEXT NOT NULL,
    
    -- Attachments
    attachments JSONB DEFAULT '[]',
    
    -- Internal notes (only visible to admins)
    is_internal_note BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX idx_ticket_messages_created_at ON ticket_messages(created_at);

-- ================================================================
-- LEADERBOARDS (NEW FEATURE)
-- ================================================================

-- Admin performance leaderboard
CREATE TABLE admin_leaderboard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES system_admins(id) ON DELETE CASCADE,
    
    -- Time period for this leaderboard entry
    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Performance metrics
    tasks_completed INTEGER DEFAULT 0,
    tasks_pending INTEGER DEFAULT 0,
    average_task_completion_time_minutes INTEGER,
    average_quality_score DECIMAL(3, 2),  -- From super_admin evaluations
    
    tickets_resolved INTEGER DEFAULT 0,
    average_ticket_response_time_minutes INTEGER,
    average_ticket_resolution_time_minutes INTEGER,
    
    documents_processed INTEGER DEFAULT 0,
    chunks_approved INTEGER DEFAULT 0,
    chunks_rejected INTEGER DEFAULT 0,
    
    responses_reviewed INTEGER DEFAULT 0,  -- For scholar reviewers
    
    -- Ranking
    rank INTEGER,
    points INTEGER DEFAULT 0,  -- Gamification points
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(admin_id, period_type, period_start)
);

CREATE INDEX idx_admin_leaderboard_admin_id ON admin_leaderboard(admin_id);
CREATE INDEX idx_admin_leaderboard_period ON admin_leaderboard(period_type, period_start);
CREATE INDEX idx_admin_leaderboard_rank ON admin_leaderboard(rank);

-- User feedback quality leaderboard
CREATE TABLE user_feedback_leaderboard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Time period
    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Feedback metrics
    total_feedbacks_given INTEGER DEFAULT 0,
    helpful_feedbacks INTEGER DEFAULT 0,  -- Marked as helpful by admins/LLM judge
    detailed_feedbacks INTEGER DEFAULT 0,  -- Feedbacks with text > 100 chars
    
    -- Quality assessment
    feedback_quality_score DECIMAL(3, 2),  -- 0.00 to 1.00 (evaluated by LLM as judge or admin)
    feedback_usefulness_score DECIMAL(3, 2),  -- How useful was the feedback for improvements
    
    -- Ranking
    rank INTEGER,
    points INTEGER DEFAULT 0,
    
    -- User opt-in
    show_in_public_leaderboard BOOLEAN DEFAULT FALSE,  -- Controlled by user in settings
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, period_type, period_start)
);

CREATE INDEX idx_user_feedback_leaderboard_user_id ON user_feedback_leaderboard(user_id);
CREATE INDEX idx_user_feedback_leaderboard_period ON user_feedback_leaderboard(period_type, period_start);
CREATE INDEX idx_user_feedback_leaderboard_rank ON user_feedback_leaderboard(rank);
CREATE INDEX idx_user_feedback_leaderboard_public ON user_feedback_leaderboard(show_in_public_leaderboard);

-- ================================================================
-- SYSTEM OPERATIONS & MONITORING
-- ================================================================

-- General API request tracking (ALL endpoints, not just LLM)
CREATE TABLE api_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request identification
    request_id VARCHAR(100) UNIQUE NOT NULL,  -- Unique per request for tracing
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    
    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    request_path TEXT,
    request_body_size INTEGER,  -- In bytes
    
    -- Response details
    status_code INTEGER,
    response_time_ms INTEGER,
    response_body_size INTEGER,  -- In bytes
    
    -- Resource usage (if applicable)
    total_tokens_used INTEGER DEFAULT 0,
    estimated_cost_usd DECIMAL(10, 6),
    
    -- Client information
    ip_address INET,
    user_agent TEXT,
    
    -- Environment
    environment VARCHAR(20),  -- 'dev', 'test', 'prod'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_requests_user_id ON api_requests(user_id);
CREATE INDEX idx_api_requests_created_at ON api_requests(created_at);
CREATE INDEX idx_api_requests_endpoint ON api_requests(endpoint);
CREATE INDEX idx_api_requests_environment ON api_requests(environment);

-- Rate limiting tracking
CREATE TABLE rate_limit_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Rate limit window
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    window_duration_minutes INTEGER NOT NULL,  -- 1440 for daily
    
    -- Usage within window
    request_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    
    -- Limit enforcement
    limit_exceeded BOOLEAN DEFAULT FALSE,
    limit_exceeded_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, window_start, window_duration_minutes)
);

CREATE INDEX idx_rate_limits_user_window ON rate_limit_tracking(user_id, window_start);

-- LLM API calls (detailed tracking with provider and purpose)
CREATE TABLE llm_api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,  -- Links to api_requests
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- LLM details
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'google', 'cohere', 'openrouter'
    model VARCHAR(100) NOT NULL,
    llm_purpose VARCHAR(50) NOT NULL,  -- 'text_generation', 'classification', 'tool_selection', 'reranking', 'guardrail_check', 'summarization'
    
    -- Token usage (detailed breakdown)
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    
    -- Token breakdown (if available from provider)
    cached_tokens INTEGER,  -- Tokens served from cache
    reasoning_tokens INTEGER,  -- For models with explicit reasoning
    
    -- Cost tracking
    cost_usd DECIMAL(10, 8) NOT NULL,
    
    -- Performance
    latency_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    cache_type VARCHAR(50),  -- 'response', 'prompt', NULL
    
    -- Request metadata
    temperature DECIMAL(3, 2),
    max_tokens INTEGER,
    top_p DECIMAL(3, 2),
    additional_params JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_calls_request_id ON llm_api_calls(request_id);
CREATE INDEX idx_llm_calls_provider ON llm_api_calls(provider);
CREATE INDEX idx_llm_calls_model ON llm_api_calls(model);
CREATE INDEX idx_llm_calls_purpose ON llm_api_calls(llm_purpose);
CREATE INDEX idx_llm_calls_created_at ON llm_api_calls(created_at);

-- Tool executions (unified table for all tools)
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,  -- Links to api_requests
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Tool identification
    tool_name VARCHAR(100) NOT NULL,  -- 'web_search', 'ahkam_lookup', 'datetime_calculator', 'math_calculator', 'comparison_tool', 'rejal_lookup'
    tool_category VARCHAR(50),  -- 'search', 'calculation', 'data_retrieval', 'analysis', 'validation'
    
    -- Tool execution
    input_parameters JSONB NOT NULL,
    output_result JSONB,
    execution_status VARCHAR(50),  -- 'success', 'failed', 'timeout', 'cached'
    
    -- Performance
    execution_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    
    -- For web search specific tracking (UPDATED: supports multiple queries)
    search_queries JSONB,  -- Array of queries if web_search generated multiple
    search_results_count INTEGER,  -- Total number of results returned
    
    -- Cost (if applicable)
    cost_usd DECIMAL(10, 6),
    
    -- Error handling
    error_message TEXT,
    error_traceback TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tool_executions_request_id ON tool_executions(request_id);
CREATE INDEX idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX idx_tool_executions_created_at ON tool_executions(created_at);
CREATE INDEX idx_tool_executions_was_cached ON tool_executions(was_cached);

-- Guardrail checks (NeMo Guardrails)
CREATE TABLE guardrail_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Check details
    check_type VARCHAR(50) NOT NULL,  -- 'input', 'output'
    validator_name VARCHAR(100) NOT NULL,  -- Name of the rail (e.g., 'ToxicLanguage', 'IslamicContentAppropriate')
    
    -- Result
    passed BOOLEAN NOT NULL,
    confidence_score DECIMAL(5, 4),
    
    -- Details
    check_details JSONB,  -- Specific findings from validator
    action_taken VARCHAR(50),  -- 'allow', 'block', 'flag', 'modify'
    
    -- Performance
    check_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_guardrail_checks_request_id ON guardrail_checks(request_id);
CREATE INDEX idx_guardrail_checks_passed ON guardrail_checks(passed);
CREATE INDEX idx_guardrail_checks_type ON guardrail_checks(check_type);

-- ================================================================
-- ADMIN DASHBOARD & DATA MANAGEMENT
-- ================================================================

CREATE TABLE data_feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Feed identification
    feed_name VARCHAR(255) NOT NULL,
    feed_type VARCHAR(50) NOT NULL,  -- 'rss', 'api', 'file_upload', 'manual', 'web_scrape_url'
    
    -- Source information
    source_reference VARCHAR(500),  -- URL for web scraping, file path, or description
    source_credentials JSONB,  -- Encrypted API keys, auth tokens (if needed)
    
    -- Web scraping (admins just provide URL, system handles scraping)
    scraping_config JSONB,  -- {selectors, depth, follow_links, etc.}
    
    -- Processing configuration
    processing_schedule VARCHAR(100),  -- Cron expression: '0 */6 * * *' or 'manual'
    auto_process BOOLEAN DEFAULT FALSE,
    require_approval BOOLEAN DEFAULT TRUE,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'paused', 'failed', 'disabled'
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50),  -- 'success', 'failed', 'partial'
    last_sync_message TEXT,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    total_documents_processed INTEGER DEFAULT 0,
    total_chunks_created INTEGER DEFAULT 0,
    total_sync_attempts INTEGER DEFAULT 0,
    successful_syncs INTEGER DEFAULT 0,
    failed_syncs INTEGER DEFAULT 0,
    
    -- Configuration
    feed_config JSONB DEFAULT '{}',  -- Feed-specific settings
    
    -- Admin tracking
    created_by UUID REFERENCES system_admins(id),
    updated_by UUID REFERENCES system_admins(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_feeds_type ON data_feeds(feed_type);
CREATE INDEX idx_data_feeds_status ON data_feeds(status);
CREATE INDEX idx_data_feeds_next_sync ON data_feeds(next_sync_at);

-- Data feed execution log
CREATE TABLE data_feed_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID NOT NULL REFERENCES data_feeds(id) ON DELETE CASCADE,
    
    -- Execution details
    execution_status VARCHAR(50) NOT NULL,  -- 'running', 'completed', 'failed'
    documents_processed INTEGER DEFAULT 0,
    documents_created INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Logs
    execution_log TEXT,
    error_message TEXT,
    
    triggered_by VARCHAR(50),  -- 'schedule', 'manual', 'api'
    triggered_by_admin UUID REFERENCES system_admins(id)
);

CREATE INDEX idx_feed_executions_feed_id ON data_feed_executions(feed_id);
CREATE INDEX idx_feed_executions_started_at ON data_feed_executions(started_at);

-- ================================================================
-- EXTERNAL API (FOR THIRD-PARTY COMPANIES)
-- ================================================================

CREATE TABLE external_api_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Client identification
    client_name VARCHAR(255) NOT NULL,
    client_company VARCHAR(255),
    client_email VARCHAR(255) NOT NULL,
    client_contact_person VARCHAR(255),
    client_phone VARCHAR(50),

    -- API credentials
    api_key VARCHAR(255) UNIQUE NOT NULL,  -- Hashed API key
    api_secret VARCHAR(255),  -- Hashed secret for additional security

    -- Access control & Status (SUPER-ADMIN MANAGEMENT)
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'suspended', 'banned', 'pending_approval', 'expired'
    is_active BOOLEAN DEFAULT TRUE,  -- Quick toggle
    allowed_endpoints JSONB DEFAULT '[]',  -- List of endpoints they can access
    blocked_endpoints JSONB DEFAULT '[]',  -- Explicitly blocked endpoints

    -- Rate limiting configuration (GRANULAR CONTROL)
    rate_limit_tier VARCHAR(50) DEFAULT 'basic',  -- 'basic', 'standard', 'premium', 'enterprise', 'custom'

    -- Custom rate limits (if tier = 'custom')
    custom_requests_per_minute INTEGER,
    custom_requests_per_hour INTEGER,
    custom_requests_per_day INTEGER,
    custom_requests_per_month INTEGER,
    custom_tokens_per_request INTEGER,
    custom_concurrent_requests INTEGER DEFAULT 5,

    -- Usage limits & tracking
    monthly_request_limit INTEGER,
    monthly_token_limit INTEGER,
    daily_request_limit INTEGER,
    daily_token_limit INTEGER,

    current_month_requests INTEGER DEFAULT 0,
    current_month_tokens INTEGER DEFAULT 0,
    current_day_requests INTEGER DEFAULT 0,
    current_day_tokens INTEGER DEFAULT 0,

    -- Cost tracking
    cost_per_token DECIMAL(10, 8),  -- Custom pricing
    current_month_cost_usd DECIMAL(10, 4) DEFAULT 0,
    total_cost_usd DECIMAL(12, 4) DEFAULT 0,

    -- IP & Security
    allowed_ips JSONB DEFAULT '[]',  -- Whitelist of allowed IP addresses
    blocked_ips JSONB DEFAULT '[]',  -- Blacklist of blocked IPs
    require_ip_whitelist BOOLEAN DEFAULT FALSE,

    -- Billing
    billing_email VARCHAR(255),
    plan_type VARCHAR(50),  -- 'free', 'pay_as_you_go', 'subscription', 'enterprise'
    payment_status VARCHAR(50) DEFAULT 'current',  -- 'current', 'overdue', 'suspended'

    -- Moderation & Control (SUPER-ADMIN ACTIONS)
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    banned_at TIMESTAMP WITH TIME ZONE,
    banned_by UUID REFERENCES system_admins(id),

    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason TEXT,
    suspension_start TIMESTAMP WITH TIME ZONE,
    suspension_end TIMESTAMP WITH TIME ZONE,  -- NULL for indefinite
    suspended_by UUID REFERENCES system_admins(id),

    -- Permissions & Features
    permissions JSONB DEFAULT '{}',  -- {allow_web_search: true, allow_tool_calls: false, ...}
    enabled_features JSONB DEFAULT '[]',  -- ['chat', 'embeddings', 'search']

    -- Alerts & Monitoring
    alert_on_high_usage BOOLEAN DEFAULT TRUE,
    alert_threshold_percentage INTEGER DEFAULT 80,  -- Alert at 80% of limit
    admin_notes TEXT,  -- Super-admin internal notes

    -- Audit trail
    created_by UUID REFERENCES system_admins(id),  -- Which admin created this client
    last_modified_by UUID REFERENCES system_admins(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_reset_at TIMESTAMP WITH TIME ZONE  -- Last time usage counters were reset
);

CREATE INDEX idx_external_clients_api_key ON external_api_clients(api_key);
CREATE INDEX idx_external_clients_is_active ON external_api_clients(is_active);
CREATE INDEX idx_external_clients_status ON external_api_clients(status);
CREATE INDEX idx_external_clients_is_banned ON external_api_clients(is_banned);
CREATE INDEX idx_external_clients_is_suspended ON external_api_clients(is_suspended);
CREATE INDEX idx_external_clients_company ON external_api_clients(client_company);

-- External API usage tracking
CREATE TABLE external_api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES external_api_clients(id) ON DELETE CASCADE,
    
    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    
    -- Response
    status_code INTEGER,
    response_time_ms INTEGER,
    
    -- Resource usage
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6),
    
    -- Client info
    ip_address INET,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_external_api_usage_client_id ON external_api_usage(client_id);
CREATE INDEX idx_external_api_usage_created_at ON external_api_usage(created_at);

-- ================================================================
-- AUDIT LOGS
-- ================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Actor (who did the action)
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL for system actions
    actor_type VARCHAR(50) DEFAULT 'user',  -- 'user', 'admin', 'system', 'api', 'external_client'
    actor_ip_address INET,
    
    -- Action details
    action VARCHAR(100) NOT NULL,  -- 'create', 'update', 'delete', 'login', 'logout', 'export', 'approve', etc.
    action_category VARCHAR(50),  -- 'auth', 'content', 'user_management', 'system', 'ticket', 'admin'
    
    -- Resource affected (polymorphic)
    resource_type VARCHAR(50) NOT NULL,  -- 'user', 'document', 'conversation', 'data_feed', 'admin', 'settings', 'ticket'
    resource_id UUID NOT NULL,  -- ID of the affected resource
    
    -- Change details
    previous_state JSONB,  -- State before action (for updates)
    new_state JSONB,       -- State after action
    changes JSONB,         -- Specific fields changed
    
    -- Context
    description TEXT,  -- Human-readable description
    metadata JSONB DEFAULT '{}',  -- Additional context
    
    -- Request tracking
    request_id VARCHAR(100),  -- Link to api_requests if applicable
    
    -- Environment
    environment VARCHAR(20),  -- 'dev', 'test', 'prod'
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action_category ON audit_logs(action_category);
CREATE INDEX idx_audit_logs_environment ON audit_logs(environment);

-- ================================================================
-- CACHE ANALYTICS (for performance optimization)
-- ================================================================

CREATE TABLE cache_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Cache identification
    cache_type VARCHAR(50) NOT NULL,  -- 'response', 'embedding', 'retrieval', 'tool', 'guardrail'
    cache_key_hash VARCHAR(64) NOT NULL,  -- SHA-256 of cache key (for privacy)
    
    -- Hit/Miss tracking
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    eviction_count INTEGER DEFAULT 0,
    
    -- Performance impact
    avg_latency_ms_on_miss INTEGER,
    avg_latency_ms_on_hit INTEGER,
    total_cost_saved_usd DECIMAL(10, 6) DEFAULT 0,
    
    -- Time tracking
    first_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Window for aggregation
    date_bucket DATE DEFAULT CURRENT_DATE,
    
    -- Environment
    environment VARCHAR(20),  -- 'dev', 'test', 'prod'
    
    UNIQUE(cache_type, cache_key_hash, date_bucket, environment)
);

CREATE INDEX idx_cache_analytics_type ON cache_analytics(cache_type);
CREATE INDEX idx_cache_analytics_date ON cache_analytics(date_bucket);
CREATE INDEX idx_cache_analytics_environment ON cache_analytics(environment);

-- ================================================================
-- BACKUP TRACKING (HuggingFace Integration)
-- ================================================================

CREATE TABLE backup_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Backup details
    backup_type VARCHAR(50) NOT NULL,  -- 'full', 'incremental', 'embeddings_only', 'documents_only'
    backup_destination VARCHAR(100) NOT NULL,  -- 'huggingface', 'local', 's3'
    
    -- HuggingFace specific
    hf_repository VARCHAR(255),  -- HuggingFace repo name (private)
    hf_commit_hash VARCHAR(100),
    
    -- Backup contents
    tables_backed_up JSONB,  -- List of table names
    total_rows INTEGER,
    total_size_mb DECIMAL(10, 2),
    
    -- Status
    status VARCHAR(50),  -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

CREATE INDEX idx_backup_logs_started_at ON backup_logs(started_at);
CREATE INDEX idx_backup_logs_status ON backup_logs(status);
CREATE INDEX idx_backup_logs_backup_type ON backup_logs(backup_type);
```

### Qdrant Collections (Vector DB Schema)

```python
# Collection configuration for dynamic vector DB abstraction
collections_config = {
    "shia_knowledge_gemini": {
        "vectors": {
            "size": 3072,
            "distance": "Cosine"
        },
        "quantization": {
            "binary": {
                "enabled": True,
                "always_ram": False  # Use for 40x performance boost
            }
        },
        "payload_schema": {
            "document_id": "keyword",
            "chunk_id": "keyword",
            "source_type": "keyword",  # hadith, quran, fiqh, tafsir, rejal, etc.
            "language": "keyword",  # fa, ar, en, ur
            "author": "text",
            "title": "text",
            "content": "text",  # Actual chunk text for re-ranking
            "metadata": "json"
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 200,
            "full_scan_threshold": 10000
        }
    },
    
    "shia_knowledge_cohere": {
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "quantization": {
            "binary": {
                "enabled": True,
                "always_ram": False
            }
        },
        "payload_schema": {
            # Same as above
        }
    },
    
    "conversation_memory_mem0": {
        "vectors": {
            "size": "MAKE IT FLEXIBLE TO CAN WORK WITH DIFFERENT EMBEDDINGS", 
            "distance": "Cosine"
        },
        "payload_schema": {
            "conversation_id": "keyword",
            "user_id": "keyword",
            "summary": "text",
            "key_points": "json",
            "facts": "json",  # mem0 extracted facts
            "timestamp": "integer"
        }
    },
    
    "rejal_persons_embeddings": {
        "vectors": {
            "size": "MAKE IT FLEXIBLE TO CAN WORK WITH DIFFERENT EMBEDDINGS",
            "distance": "Cosine"
        },
        "payload_schema": {
            "person_id": "keyword",
            "name_arabic": "text",
            "name_persian": "text",
            "biographical_notes": "text",
            "reliability_rating": "keyword",
            "reliability_score": "float"
        }
    }
}
```

---



---

## 🔗 Related Modules
- **Referenced by:** ALL modules use this schema
- **Authentication:** [03-AUTHENTICATION.md](./03-AUTHENTICATION.md)
- **Admin System:** [05-ADMIN-SYSTEM.md](./05-ADMIN-SYSTEM.md)
- **Tools:** [06-TOOLS-AHKAM.md](./06-TOOLS-AHKAM.md), [07-TOOLS-HADITH.md](./07-TOOLS-HADITH.md)
- **RAG Pipeline:** [09-RAG-PIPELINE-CHONKIE.md](./09-RAG-PIPELINE-CHONKIE.md)

---

[◀️ Back to Index](./00-INDEX.md) | [Previous](./01-ARCHITECTURE-OVERVIEW.md) | [Next: Authentication ▶️](./03-AUTHENTICATION.md)
