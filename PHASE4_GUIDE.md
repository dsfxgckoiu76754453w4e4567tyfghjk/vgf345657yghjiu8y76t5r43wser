# Phase 4: Admin Dashboard & Support System - Implementation Guide

**Status**: ✅ COMPLETED

**Lines of Code**: ~4,100

## Overview

Phase 4 implements administrative features, support ticketing system, and user leaderboards. This phase enables:

1. **Admin Dashboard**: Super-admin API key management, user management, content moderation
2. **Support System**: Ticket creation, responses, assignment, status tracking
3. **Leaderboards**: User contribution tracking and ranking
4. **Email Notifications**: Automated email notifications for tickets and moderation

## Critical Design Principles

### 1. Super-Admin API Keys

**CRITICAL**: API keys provide programmatic access to admin functions.

**Security Features**:
- Generated once and never shown again
- Hashed storage (NOT plain text)
- Expiration support
- Permission-based access control
- Activity logging

```python
# API key is returned ONLY during creation
{
    "api_key": "sk_a1b2c3d4...",  # SAVE THIS NOW!
    "warning": "SAVE THIS KEY NOW - It will not be shown again!"
}
```

### 2. Support Ticket System

**CRITICAL**: Users can create support tickets and track responses.

**Workflow**:
1. User creates ticket → Status: "open"
2. Admin assigns ticket → Status: "in_progress"
3. Admin/User add responses → Conversation thread
4. Admin resolves ticket → Status: "resolved"
5. Ticket closed → Status: "closed"

### 3. Leaderboard Scoring System

**Scoring**:
- Document upload: 10 points (high value contribution)
- Conversation: 2 points (moderate engagement)
- Message: 1 point (basic activity)

**Why this weighting?**
- Uploading quality documents is the most valuable contribution
- Starting conversations shows engagement
- Messages are basic activity

### 4. Email Notifications

**CRITICAL**: Users receive email notifications for:
- Ticket created/responded/resolved
- Document approved/rejected
- Account banned/unbanned

## Implemented Services

### 1. Admin Service

**File**: `src/app/services/admin_service.py` (~600 lines)

**Features**:

#### API Key Management
```python
async def create_api_key(
    self,
    admin_user_id: UUID,
    key_name: str,
    permissions: list[str],
    expires_in_days: Optional[int] = None,
) -> dict:
    """Create secure API key with permissions."""
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    # Return key ONLY once
    return {"api_key": api_key, "warning": "SAVE THIS KEY NOW!"}
```

#### User Management
```python
# Ban user (temporary or permanent)
await admin_service.ban_user(
    admin_user_id=admin_id,
    user_id=user_id,
    reason="Violation of community guidelines",
    ban_duration_days=7  # None = permanent
)

# Change user role
await admin_service.change_user_role(
    admin_user_id=admin_id,
    user_id=user_id,
    new_role="moderator"  # user, moderator, admin, super_admin
)
```

#### Content Moderation
```python
# Get pending content
pending = await admin_service.get_pending_content(admin_user_id=admin_id)

# Moderate content
await admin_service.moderate_content(
    admin_user_id=admin_id,
    content_id=document_id,
    content_type="document",
    action="approve",  # or "reject"
    reason="Content meets quality standards"
)
```

#### System Statistics
```python
stats = await admin_service.get_system_statistics(admin_user_id=admin_id)

# Returns:
{
    "users": {
        "total": 1500,
        "verified": 1200,
        "banned": 10,
        "unverified": 300
    },
    "content": {
        "total_documents": 500,
        "pending_moderation": 25
    },
    "chat": {
        "total_conversations": 10000
    }
}
```

### 2. Support Ticket Service

**File**: `src/app/services/support_service.py` (~500 lines)

**Features**:

#### Ticket Creation
```python
ticket = await support_service.create_ticket(
    user_id=user_id,
    subject="Unable to upload documents",
    description="I'm getting an error when...",
    category="technical",  # technical, content, account, billing, other
    priority="medium"  # low, medium, high, urgent
)
```

#### Ticket Responses
```python
# User adds response
response = await support_service.add_response(
    ticket_id=ticket_id,
    responder_user_id=user_id,
    message="Here are more details...",
    is_staff_response=False
)

# Admin adds response
response = await support_service.add_response(
    ticket_id=ticket_id,
    responder_user_id=admin_id,
    message="Thank you for reporting. We're investigating...",
    is_staff_response=True
)
```

#### Ticket Management
```python
# Assign to admin
await support_service.assign_ticket(
    admin_user_id=admin_id,
    ticket_id=ticket_id,
    assign_to_admin_id=specific_admin_id
)

# Update status
await support_service.update_ticket_status(
    ticket_id=ticket_id,
    new_status="resolved",
    resolution="Issue fixed. Document upload feature is working."
)
```

#### Ticket Statistics
```python
stats = await support_service.get_ticket_statistics()

# Returns:
{
    "total": 250,
    "by_status": {
        "open": 15,
        "in_progress": 30,
        "resolved": 180,
        "closed": 25
    },
    "resolution_rate": 0.82  # 82% resolved/closed
}
```

### 3. Leaderboard Service

**File**: `src/app/services/leaderboard_service.py` (~400 lines)

**Features**:

#### Document Upload Leaderboard
```python
leaderboard = await leaderboard_service.get_document_upload_leaderboard(
    timeframe="month",  # all_time, month, week
    limit=10
)

# Returns:
[
    {
        "rank": 1,
        "user_id": "...",
        "display_name": "Ahmed Ali",
        "upload_count": 45
    },
    ...
]
```

#### Chat Activity Leaderboard
```python
leaderboard = await leaderboard_service.get_chat_activity_leaderboard(
    timeframe="week",
    limit=10
)

# Returns users ranked by message count
```

#### Overall Leaderboard (Combined Metrics)
```python
leaderboard = await leaderboard_service.get_overall_leaderboard(
    timeframe="all_time",
    limit=10
)

# Returns:
[
    {
        "rank": 1,
        "user_id": "...",
        "display_name": "Ahmed Ali",
        "total_score": 520,  # 45 docs * 10 + 30 convs * 2 + 100 msgs * 1
        "breakdown": {
            "document_uploads": 45,
            "conversations": 30,
            "messages": 100
        }
    },
    ...
]
```

#### User Statistics
```python
stats = await leaderboard_service.get_user_statistics(user_id=user_id)

# Returns:
{
    "user_id": "...",
    "display_name": "Ahmed Ali",
    "statistics": {
        "document_uploads": 45,
        "conversations": 30,
        "messages": 100,
        "overall_score": 520
    },
    "rank": 3,  # Global rank
    "member_since": "2025-01-15T10:30:00Z"
}
```

### 4. Email Notification Service

**File**: `src/app/services/email_service.py` (~400 lines)

**Features**:

#### Support Ticket Notifications
```python
email_service = EmailService()

# Ticket created
await email_service.send_ticket_created_notification(
    to_email="user@example.com",
    ticket_id="123e4567...",
    subject="Unable to upload documents"
)

# Ticket response
await email_service.send_ticket_response_notification(
    to_email="user@example.com",
    ticket_id="123e4567...",
    subject="Unable to upload documents",
    response_preview="Thank you for reporting. We are investigating..."
)

# Ticket resolved
await email_service.send_ticket_resolved_notification(
    to_email="user@example.com",
    ticket_id="123e4567...",
    subject="Unable to upload documents",
    resolution="Issue fixed. Document upload feature is working."
)
```

#### Document Moderation Notifications
```python
# Document approved
await email_service.send_document_approved_notification(
    to_email="user@example.com",
    document_id="123e4567...",
    document_title="Tafsir of Surah Al-Fatiha"
)

# Document rejected
await email_service.send_document_rejected_notification(
    to_email="user@example.com",
    document_id="123e4567...",
    document_title="Document Title",
    reason="Content does not meet quality standards"
)
```

#### Account Notifications
```python
# Account banned
await email_service.send_account_ban_notification(
    to_email="user@example.com",
    ban_reason="Violation of community guidelines",
    ban_duration="7 days"  # None for permanent
)

# Account unbanned
await email_service.send_account_unban_notification(
    to_email="user@example.com"
)
```

**Email Configuration**:
```python
# In .env file
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@example.com
FROM_NAME=Shia Islamic Chatbot
```

## API Endpoints

### Admin Endpoints

**Base Path**: `/api/v1/admin`

#### API Key Management

**POST /admin/api-keys** - Create API key
```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "Production Admin Key",
    "permissions": ["user:read", "user:write", "content:moderate"],
    "expires_in_days": 90
  }'
```

**GET /admin/api-keys** - List API keys
```bash
curl -X GET http://localhost:8000/api/v1/admin/api-keys?include_expired=false
```

**POST /admin/api-keys/{api_key_id}/revoke** - Revoke API key
```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys/123e4567.../revoke
```

#### User Management

**GET /admin/users** - List users
```bash
curl -X GET "http://localhost:8000/api/v1/admin/users?page=1&page_size=50&search_query=ahmed&role_filter=user"
```

**POST /admin/users/{user_id}/ban** - Ban user
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/123e4567.../ban \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Violation of community guidelines - spam content",
    "ban_duration_days": 7
  }'
```

**POST /admin/users/{user_id}/unban** - Unban user
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/123e4567.../unban
```

**POST /admin/users/{user_id}/role** - Change user role
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/123e4567.../role \
  -H "Content-Type: application/json" \
  -d '{
    "new_role": "moderator"
  }'
```

#### Content Moderation

**GET /admin/content/pending** - Get pending content
```bash
curl -X GET "http://localhost:8000/api/v1/admin/content/pending?limit=20"
```

**POST /admin/content/{content_type}/{content_id}/moderate** - Moderate content
```bash
curl -X POST http://localhost:8000/api/v1/admin/content/document/123e4567.../moderate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve"
  }'
```

#### System Statistics

**GET /admin/statistics** - Get system statistics
```bash
curl -X GET http://localhost:8000/api/v1/admin/statistics
```

### Support Ticket Endpoints

**Base Path**: `/api/v1/support`

#### Ticket Creation and Listing

**POST /support/tickets** - Create ticket
```bash
curl -X POST http://localhost:8000/api/v1/support/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Unable to upload documents",
    "description": "I'm getting an error when trying to upload PDF documents...",
    "category": "technical",
    "priority": "medium"
  }'
```

**GET /support/tickets/my** - List my tickets
```bash
curl -X GET "http://localhost:8000/api/v1/support/tickets/my?status_filter=open&page=1"
```

**GET /support/tickets/all** - List all tickets (admin)
```bash
curl -X GET "http://localhost:8000/api/v1/support/tickets/all?status_filter=open&assigned_to_me=true&page=1"
```

#### Ticket Details and Responses

**GET /support/tickets/{ticket_id}** - Get ticket details
```bash
curl -X GET http://localhost:8000/api/v1/support/tickets/123e4567...
```

**POST /support/tickets/{ticket_id}/responses** - Add response
```bash
curl -X POST "http://localhost:8000/api/v1/support/tickets/123e4567.../responses?is_staff=true" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Thank you for reporting. We are investigating this issue."
  }'
```

#### Ticket Management (Admin)

**POST /support/tickets/{ticket_id}/assign** - Assign ticket
```bash
curl -X POST http://localhost:8000/api/v1/support/tickets/123e4567.../assign \
  -H "Content-Type: application/json" \
  -d '{
    "assign_to_admin_id": "789e0123..."
  }'
```

**PUT /support/tickets/{ticket_id}/status** - Update status
```bash
curl -X PUT http://localhost:8000/api/v1/support/tickets/123e4567.../status \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "resolved",
    "resolution": "Issue fixed. Document upload feature is working correctly."
  }'
```

**GET /support/statistics** - Get ticket statistics
```bash
curl -X GET http://localhost:8000/api/v1/support/statistics
```

### Leaderboard Endpoints

**Base Path**: `/api/v1/leaderboard`

**GET /leaderboard/documents** - Document upload leaderboard
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboard/documents?timeframe=month&limit=10"
```

**GET /leaderboard/chat** - Chat activity leaderboard
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboard/chat?timeframe=week&limit=10"
```

**GET /leaderboard/conversations** - Conversation leaderboard
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboard/conversations?timeframe=all_time&limit=10"
```

**GET /leaderboard/overall** - Overall leaderboard
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboard/overall?timeframe=month&limit=10"
```

**GET /leaderboard/users/{user_id}/statistics** - User statistics
```bash
curl -X GET http://localhost:8000/api/v1/leaderboard/users/123e4567.../statistics
```

**GET /leaderboard/me/statistics** - My statistics
```bash
curl -X GET http://localhost:8000/api/v1/leaderboard/me/statistics
```

## Database Models

### Support Ticket Model

**File**: `src/app/models/support_ticket.py`

```python
class SupportTicket(Base):
    """User support tickets."""

    id: UUID
    user_id: UUID
    subject: str
    description: str
    category: str  # technical, content, account, billing, other
    priority: str  # low, medium, high, urgent
    status: str  # open, in_progress, resolved, closed
    assigned_to_admin_id: Optional[UUID]
    resolution: Optional[str]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    responses: list["SupportTicketResponse"]
```

### Support Ticket Response Model

```python
class SupportTicketResponse(Base):
    """Responses to support tickets."""

    id: UUID
    ticket_id: UUID
    responder_user_id: UUID
    message: str
    is_staff_response: bool  # True if from admin/staff
    created_at: datetime
```

## Testing Phase 4

### 1. Test Admin Service

```python
import asyncio
from app.services.admin_service import AdminService

async def test_admin():
    # Create API key
    api_key = await admin_service.create_api_key(
        admin_user_id=admin_id,
        key_name="Test Key",
        permissions=["user:read"],
        expires_in_days=30
    )
    print(f"API Key (SAVE THIS): {api_key['api_key']}")

    # Ban user
    result = await admin_service.ban_user(
        admin_user_id=admin_id,
        user_id=user_id,
        reason="Test ban",
        ban_duration_days=7
    )
    print(f"User banned: {result}")

    # Get statistics
    stats = await admin_service.get_system_statistics(admin_user_id=admin_id)
    print(f"Total users: {stats['users']['total']}")
```

### 2. Test Support Service

```python
from app.services.support_service import SupportService

async def test_support():
    # Create ticket
    ticket = await support_service.create_ticket(
        user_id=user_id,
        subject="Test Issue",
        description="This is a test support ticket",
        category="technical",
        priority="medium"
    )
    print(f"Ticket created: {ticket['ticket_id']}")

    # Add response
    response = await support_service.add_response(
        ticket_id=ticket["ticket_id"],
        responder_user_id=admin_id,
        message="We are looking into this",
        is_staff_response=True
    )
    print(f"Response added: {response['response_id']}")

    # Resolve ticket
    result = await support_service.update_ticket_status(
        ticket_id=ticket["ticket_id"],
        new_status="resolved",
        resolution="Issue resolved"
    )
    print(f"Ticket resolved: {result}")
```

### 3. Test Leaderboard Service

```python
from app.services.leaderboard_service import LeaderboardService

async def test_leaderboard():
    # Get overall leaderboard
    leaderboard = await leaderboard_service.get_overall_leaderboard(
        timeframe="month",
        limit=10
    )
    for entry in leaderboard:
        print(f"Rank {entry['rank']}: {entry['display_name']} - {entry['total_score']} points")

    # Get user statistics
    stats = await leaderboard_service.get_user_statistics(user_id=user_id)
    print(f"User rank: {stats['rank']}")
    print(f"Overall score: {stats['statistics']['overall_score']}")
```

### 4. Test Email Service

```python
from app.services.email_service import EmailService

async def test_email():
    email_service = EmailService()

    # Send ticket created notification
    sent = await email_service.send_ticket_created_notification(
        to_email="user@example.com",
        ticket_id="123e4567...",
        subject="Unable to upload documents"
    )
    print(f"Email sent: {sent}")
```

## Critical Notes

### 1. API Key Security

- **NEVER** store API keys in plain text
- Use proper hashing (bcrypt, argon2)
- Rotate keys regularly
- Implement rate limiting
- Log all API key usage

### 2. Support Ticket Privacy

- Users can only view their own tickets
- Admins can view all tickets
- Implement proper permission checks
- Audit all ticket access

### 3. Email Notifications

- Configure SMTP settings properly
- Handle email failures gracefully
- Don't send sensitive information
- Provide unsubscribe options
- Rate limit email sending

### 4. Leaderboard Performance

- Cache leaderboard results (15 minutes)
- Use database indexes on user_id, created_at
- Limit query complexity
- Consider background jobs for updates

## Next Steps (Phase 5)

After Phase 4 completion, Phase 5 will implement:

1. **External API Client System**
   - API key authentication for external apps
   - Rate limiting
   - Usage tracking

2. **ASR (Automatic Speech Recognition)**
   - Google Speech-to-Text integration
   - OpenAI Whisper integration
   - Multi-language support

3. **Langfuse Observability**
   - Trace all LLM calls
   - Monitor token usage
   - Track latency and errors

## File Structure - Phase 4

```
src/app/
├── models/
│   └── support_ticket.py         # Support ticket models
├── services/
│   ├── admin_service.py          # Admin operations (~600 lines)
│   ├── support_service.py        # Support tickets (~500 lines)
│   ├── leaderboard_service.py    # Leaderboards (~400 lines)
│   └── email_service.py          # Email notifications (~400 lines)
├── schemas/
│   └── admin.py                  # Pydantic schemas (~400 lines)
└── api/v1/
    ├── admin.py                  # Admin endpoints (~400 lines)
    ├── support.py                # Support endpoints (~400 lines)
    ├── leaderboard.py            # Leaderboard endpoints (~300 lines)
    └── __init__.py               # Router updates

PHASE4_GUIDE.md                   # This file
```

## Summary

Phase 4 successfully implements:

✅ Admin service with API keys, user management, content moderation
✅ Support ticket system with full lifecycle tracking
✅ Leaderboard system with multiple ranking criteria
✅ Email notification service for all key events
✅ Complete API endpoints with validation
✅ Comprehensive error handling
✅ Detailed documentation and examples

**Total Implementation**: ~4,100 lines of production-ready code

**Ready for**: Phase 5 - External API Integration & Observability
