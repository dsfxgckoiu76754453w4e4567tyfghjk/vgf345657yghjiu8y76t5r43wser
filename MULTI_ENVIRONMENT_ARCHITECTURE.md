# 🏗️ Multi-Environment Architecture Recommendations

**Complete Environment Isolation & Cross-Environment Access Control**

**Date:** 2025-11-06
**Status:** Architecture Recommendations
**Version:** 1.0.0

---

## 📋 Requirements Analysis

### Current Situation

You have **3 completely separate environments** with different purposes and users:

```
┌─────────────────────────────────────────────────────────────────┐
│  Environment 1: DEV                                             │
│  • Purpose: Development and testing                             │
│  • Users: Developers                                            │
│  • Data: Development/test data                                  │
│  • Documents: Test documents for RAG                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Environment 2: STAGE                                           │
│  • Purpose: Pre-production testing                              │
│  • Users: Test team (end users actively testing)               │
│  • Data: Test data (realistic but not production)              │
│  • Documents: Test documents for RAG                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Environment 3: PROD                                            │
│  • Purpose: Production                                          │
│  • Users: Real end users                                        │
│  • Data: Real production data                                   │
│  • Documents: Real documents for RAG                            │
└─────────────────────────────────────────────────────────────────┘
```

### Key Requirements

**1. Complete Separation:**
- ✅ Separate users in each environment
- ✅ Separate databases in each environment
- ✅ Separate documents/RAG data in each environment
- ✅ A user with prod access should NOT automatically have dev access
- ✅ A user with dev access should NOT automatically have prod access

**2. Cross-Environment Access Control:**
- ✅ Some users need access to multiple environments
- ✅ Developers need special access to stage/prod for debugging
- ✅ Access should be controlled and audited

**3. Developer Testing in Non-Dev Environments:**
- ✅ Developers need test accounts in stage/prod
- ✅ Used for debugging reported issues
- ✅ Used for verification and testing
- ✅ Should be clearly marked as developer testing activity

---

## 🎯 Solution Architecture

### Recommended Approach: Multi-Environment with Cross-Environment Identity

I recommend **Option 3: Federated Identity with Environment-Specific Databases** (detailed below).

---

## 💡 Solution Options Analysis

### Option 1: Completely Separate Systems (Maximum Isolation)

**Architecture:**
```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   dev.wisqu.com     │  │  stage.wisqu.com    │  │   wisqu.com        │
│                     │  │                     │  │                     │
│  • Separate App     │  │  • Separate App     │  │  • Separate App     │
│  • Separate DB      │  │  • Separate DB      │  │  • Separate DB      │
│  • Separate Users   │  │  • Separate Users   │  │  • Separate Users   │
│  • Separate Qdrant  │  │  • Separate Qdrant  │  │  • Separate Qdrant  │
│  • Separate Redis   │  │  • Separate Redis   │  │  • Separate Redis   │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘

      NO CONNECTION          NO CONNECTION          NO CONNECTION
```

**User Management:**
- Each environment has completely separate user tables
- `dev-user@example.com` in dev is different from `dev-user@example.com` in prod
- No shared authentication
- No cross-environment access

**Pros:**
- ✅ Maximum security and isolation
- ✅ Simple to implement (just 3 separate deployments)
- ✅ No risk of cross-environment data leakage
- ✅ Clear separation of concerns
- ✅ Easy to understand

**Cons:**
- ❌ No cross-environment access for developers
- ❌ Developers need separate accounts in each environment
- ❌ Hard to track "same user" across environments
- ❌ No centralized user management
- ❌ Triple maintenance burden

**When to Use:**
- High security requirements
- Completely independent teams per environment
- No need for cross-environment access

---

### Option 2: Shared Authentication + Environment-Specific Data (Hybrid)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                  CENTRAL AUTHENTICATION SERVICE                  │
│  • Single User Table                                            │
│  • Single Login Flow                                            │
│  • Environment Access Control (which envs user can access)     │
└─────────────────────────────────────────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ↓                    ↓                    ↓
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  DEV ENV    │      │ STAGE ENV   │      │  PROD ENV   │
│             │      │             │      │             │
│ • Separate  │      │ • Separate  │      │ • Separate  │
│   DB        │      │   DB        │      │   DB        │
│ • Separate  │      │ • Separate  │      │ • Separate  │
│   Qdrant    │      │   Qdrant    │      │   Qdrant    │
│ • Separate  │      │ • Separate  │      │ • Separate  │
│   Data      │      │   Data      │      │   Data      │
└─────────────┘      └─────────────┘      └─────────────┘
```

**User Model:**
```python
class User(Base):
    id: UUID
    email: str
    password_hash: str
    full_name: str

    # Environment access control
    can_access_dev: bool = False
    can_access_stage: bool = False
    can_access_prod: bool = False

    # Roles per environment
    dev_role: Optional[str] = None      # user, admin, developer
    stage_role: Optional[str] = None    # user, admin, tester
    prod_role: Optional[str] = None     # user, admin
```

**JWT Token:**
```json
{
  "user_id": "uuid",
  "email": "dev@example.com",
  "environment": "prod",  // Current environment
  "can_access": ["dev", "stage", "prod"],
  "role_in_current_env": "developer"
}
```

**Pros:**
- ✅ Single login for all environments
- ✅ Centralized user management
- ✅ Easy cross-environment access control
- ✅ Can track same user across environments
- ✅ Flexible permissions per environment

**Cons:**
- ❌ Shared authentication = potential attack vector
- ❌ If auth service goes down, all environments affected
- ❌ More complex to implement
- ❌ Need careful security for cross-environment access

**When to Use:**
- Medium-to-large teams
- Developers need access to multiple environments
- Want centralized user management

---

### Option 3: Federated Identity with Environment-Specific Databases (RECOMMENDED)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│               IDENTITY PROVIDER (Internal or External)           │
│  • User Registry (email, name, id)                             │
│  • Environment Access Matrix                                    │
│  • OAuth2 / OIDC                                                │
└─────────────────────────────────────────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ↓                    ↓                    ↓
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  DEV APP         │ │  STAGE APP       │ │  PROD APP        │
│                  │ │                  │ │                  │
│ Local User Table │ │ Local User Table │ │ Local User Table │
│ • Synced from IDP│ │ • Synced from IDP│ │ • Synced from IDP│
│ • Env-specific   │ │ • Env-specific   │ │ • Env-specific   │
│   data           │ │   data           │ │   data           │
│                  │ │                  │ │                  │
│ Separate DB      │ │ Separate DB      │ │ Separate DB      │
│ Separate Qdrant  │ │ Separate Qdrant  │ │ Separate Qdrant  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

**How It Works:**

1. **Identity Provider (IDP):**
   - Central place for user identities
   - Stores which environments each user can access
   - Handles authentication
   - Can be custom-built or use existing (Keycloak, Auth0, etc.)

2. **Environment-Specific Apps:**
   - Each environment is a separate deployment
   - Each has its own database, Qdrant, Redis
   - Each syncs user identities from IDP on first login
   - Each maintains environment-specific user data

3. **User Login Flow:**
   ```
   User → IDP Login → Check Environment Access → Redirect to Environment
   ```

4. **Cross-Environment Access:**
   ```
   Developer logs in to IDP
   → IDP shows: "You have access to: dev, stage, prod"
   → Developer selects "prod"
   → Redirected to prod.wisqu.com with access token
   ```

**Pros:**
- ✅ Strong separation between environments
- ✅ Centralized identity management
- ✅ Easy to add/remove environment access
- ✅ Single login experience
- ✅ Each environment can fail independently
- ✅ Scalable and professional
- ✅ Industry standard approach

**Cons:**
- ❌ More complex initial setup
- ❌ Need IDP infrastructure
- ❌ Slightly more expensive (IDP hosting)

**When to Use:**
- Professional/production systems
- Multiple environments with different access needs
- Want best practice architecture
- **RECOMMENDED for your use case**

---

### Option 4: Single App with Multi-Tenancy (Environment as Tenant)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                     SINGLE APPLICATION                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  DEV TENANT  │  │ STAGE TENANT │  │  PROD TENANT │         │
│  │              │  │              │  │              │         │
│  │  • Schema    │  │  • Schema    │  │  • Schema    │         │
│  │    "dev"     │  │    "stage"   │  │    "prod"    │         │
│  │  • Qdrant    │  │  • Qdrant    │  │  • Qdrant    │         │
│  │    Collection│  │    Collection│  │    Collection│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│            SINGLE DATABASE (with tenant isolation)              │
└─────────────────────────────────────────────────────────────────┘
```

**User Model:**
```python
class User(Base):
    id: UUID
    email: str
    password_hash: str

    # Tenant memberships
    tenants: List[str] = ["dev", "stage"]  # Which envs user can access
    current_tenant: str = "dev"  # Which env user is currently in
```

**Every Query:**
```python
# Always filter by tenant
users = await db.execute(
    select(User).where(User.tenant_id == current_tenant)
)

documents = qdrant.search(
    collection_name=f"documents_{current_tenant}",
    query=query
)
```

**Pros:**
- ✅ Single application to maintain
- ✅ Easy to add new environments
- ✅ Shared code between environments
- ✅ Lower infrastructure cost

**Cons:**
- ❌ Risk of tenant isolation bugs (DANGEROUS!)
- ❌ One bug affects all environments
- ❌ Not true separation
- ❌ Performance impact (complex queries)
- ❌ Not recommended for prod isolation

**When to Use:**
- SaaS applications with many tenants
- NOT recommended for dev/stage/prod separation

---

## 🏆 RECOMMENDED: Option 3 - Federated Identity

Based on your requirements, **Option 3 (Federated Identity)** is the best choice.

---

## 📐 Detailed Implementation Plan

### Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                    CENTRAL IDENTITY SERVICE                        │
│                    (auth.wisqu.com)                                │
│                                                                    │
│  Users Table:                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ id: UUID                                                   │   │
│  │ email: string                                              │   │
│  │ password_hash: string                                      │   │
│  │ full_name: string                                          │   │
│  │ is_active: boolean                                         │   │
│  │                                                            │   │
│  │ Environment Access:                                        │   │
│  │ • environment_access: ["dev", "stage", "prod"]            │   │
│  │                                                            │   │
│  │ Roles per Environment:                                     │   │
│  │ • dev_role: "developer" | "admin" | null                  │   │
│  │ • stage_role: "tester" | "developer" | "admin" | null     │   │
│  │ • prod_role: "user" | "developer" | "admin" | null        │   │
│  │                                                            │   │
│  │ Developer Testing:                                         │   │
│  │ • can_create_test_accounts: boolean                       │   │
│  │ • test_access_reason_required: boolean                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ↓             ↓             ↓
     ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
     │  DEV APP        │ │  STAGE APP      │ │  PROD APP       │
     │  dev.wisqu.com  │ │ stage.wisqu.com │ │  wisqu.com      │
     │                 │ │                 │ │                 │
     │ Local Users:    │ │ Local Users:    │ │ Local Users:    │
     │ • id (from IDP) │ │ • id (from IDP) │ │ • id (from IDP) │
     │ • email         │ │ • email         │ │ • email         │
     │ • role          │ │ • role          │ │ • role          │
     │ • env_data      │ │ • env_data      │ │ • env_data      │
     │                 │ │                 │ │                 │
     │ Env-specific:   │ │ Env-specific:   │ │ Env-specific:   │
     │ • Conversations │ │ • Conversations │ │ • Conversations │
     │ • API calls     │ │ • API calls     │ │ • API calls     │
     │ • Settings      │ │ • Settings      │ │ • Settings      │
     │                 │ │                 │ │                 │
     │ Separate DB     │ │ Separate DB     │ │ Separate DB     │
     │ Separate Qdrant │ │ Separate Qdrant │ │ Separate Qdrant │
     │ Separate Redis  │ │ Separate Redis  │ │ Separate Redis  │
     └─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🔐 Implementation: Phase 1 - Central Identity Service

### Step 1.1: Create Identity Service Database

```python
# identity_service/models/user.py

from sqlalchemy import Column, String, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import uuid4

class CentralUser(Base):
    """Central user identity - shared across all environments."""
    __tablename__ = "central_users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)

    # Environment access control
    environment_access = Column(ARRAY(String), default=[])
    # Example: ["dev", "stage", "prod"]

    # Role in each environment
    dev_role = Column(String(50), nullable=True)
    # Options: "developer", "admin", null

    stage_role = Column(String(50), nullable=True)
    # Options: "tester", "developer", "admin", null

    prod_role = Column(String(50), nullable=True)
    # Options: "user", "developer", "admin", null

    # Developer testing privileges
    can_create_test_accounts = Column(Boolean, default=False)
    # True for developers who need test access

    test_access_audit = Column(Boolean, default=False)
    # If true, all test access is logged and audited

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EnvironmentAccess(Base):
    """Audit log for cross-environment access."""
    __tablename__ = "environment_access_log"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    environment = Column(String(50), nullable=False)  # dev, stage, prod
    access_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    reason = Column(String(500), nullable=True)
    # For developer access: "Debugging issue #123"
```

### Step 1.2: Identity Service API Endpoints

```python
# identity_service/api/auth.py

@router.post("/login")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Central login - returns available environments.
    """
    # Authenticate user
    user = await authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Return access token with environment list
    return LoginResponse(
        access_token=create_jwt(user.id, user.email),
        available_environments=user.environment_access,
        roles={
            "dev": user.dev_role,
            "stage": user.stage_role,
            "prod": user.prod_role,
        }
    )


@router.post("/environment-token")
async def get_environment_token(
    request: EnvironmentTokenRequest,
    current_user: CentralUser = Depends(get_current_user)
) -> EnvironmentTokenResponse:
    """
    Get access token for specific environment.

    Request:
    {
      "environment": "prod",
      "reason": "Debugging issue #123" (optional)
    }
    """
    env = request.environment

    # Check if user has access to this environment
    if env not in current_user.environment_access:
        raise HTTPException(
            status_code=403,
            detail=f"You don't have access to {env} environment"
        )

    # Get role for this environment
    role = getattr(current_user, f"{env}_role")

    # Log environment access (audit trail)
    await log_environment_access(
        user_id=current_user.id,
        environment=env,
        reason=request.reason
    )

    # Create environment-specific JWT
    env_token = create_environment_jwt(
        user_id=current_user.id,
        email=current_user.email,
        environment=env,
        role=role,
        can_create_test_accounts=current_user.can_create_test_accounts
    )

    return EnvironmentTokenResponse(
        token=env_token,
        environment=env,
        role=role,
        redirect_url=f"https://{get_env_domain(env)}/auth/callback"
    )
```

---

## 🔐 Implementation: Phase 2 - Environment-Specific Apps

### Step 2.1: Environment User Model

```python
# app/models/user.py (in dev/stage/prod apps)

class User(Base):
    """Environment-specific user data."""
    __tablename__ = "users"

    # Synced from Identity Service
    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # Same UUID as central_users.id

    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))

    # Environment-specific data
    role = Column(String(50), nullable=False)
    # "developer", "tester", "user", "admin"

    account_type = Column(String(50), default="free")
    # "free", "premium", "unlimited", "developer_test"

    is_test_account = Column(Boolean, default=False)
    # True if this is a developer test account in stage/prod

    created_by_developer = Column(PG_UUID(as_uuid=True), nullable=True)
    # If test account, which developer created it

    test_expires_at = Column(DateTime(timezone=True), nullable=True)
    # When this test account expires

    # Environment-specific activity
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)

    # Relationships to environment-specific data
    # conversations, documents, api_calls, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Step 2.2: Environment Authentication Middleware

```python
# app/middleware/auth.py

@app.middleware("http")
async def environment_auth_middleware(request: Request, call_next):
    """
    Verify environment-specific JWT tokens.
    """
    # Get token from header
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token:
        return await call_next(request)

    try:
        # Decode JWT
        payload = decode_jwt(token)

        # CRITICAL: Verify environment matches
        token_env = payload.get("environment")
        current_env = os.getenv("ENVIRONMENT")  # dev, stage, prod

        if token_env != current_env:
            raise HTTPException(
                status_code=403,
                detail=f"Token is for {token_env}, but this is {current_env}"
            )

        # Get or create user in this environment
        user = await get_or_create_environment_user(
            user_id=payload["user_id"],
            email=payload["email"],
            role=payload["role"],
            db=request.state.db
        )

        request.state.user = user
        request.state.environment = current_env

    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    response = await call_next(request)
    return response


async def get_or_create_environment_user(
    user_id: UUID,
    email: str,
    role: str,
    db: AsyncSession
) -> User:
    """
    Get or create user in this environment.
    First login syncs from Identity Service.
    """
    user = await db.get(User, user_id)

    if not user:
        # First time this user logs into this environment
        user = User(
            id=user_id,
            email=email,
            role=role,
            account_type="free" if role == "user" else "unlimited"
        )
        db.add(user)
        await db.commit()

        logger.info(f"Created new user in {os.getenv('ENVIRONMENT')}: {email}")

    return user
```

---

## 🔐 Implementation: Phase 3 - Developer Test Accounts

### Step 3.1: Test Account Creation (Stage/Prod)

```python
# app/api/v1/developer.py

@router.post("/test-accounts")
async def create_developer_test_account(
    request: CreateTestAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    environment: str = Depends(get_environment)
) -> TestAccountResponse:
    """
    Create a test account in stage/prod for debugging.

    Only available to developers with can_create_test_accounts=True

    Request:
    {
      "reason": "Debugging issue #123 - user can't login",
      "expires_in_hours": 24
    }
    """
    # Check if user has permission
    if not current_user.can_create_test_accounts:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create test accounts"
        )

    # Don't allow in dev (not needed)
    if environment == "dev":
        raise HTTPException(
            status_code=400,
            detail="Test accounts not needed in dev environment"
        )

    # Create test user
    test_email = f"dev-test-{uuid4().hex[:8]}@test.wisqu.com"
    test_password = generate_secure_password()

    test_user = User(
        id=uuid4(),
        email=test_email,
        password_hash=hash_password(test_password),
        full_name=f"Developer Test Account ({current_user.full_name})",
        role="user",
        account_type="developer_test",
        is_test_account=True,
        created_by_developer=current_user.id,
        test_expires_at=datetime.now() + timedelta(hours=request.expires_in_hours),
        is_email_verified=True,
        is_active=True
    )

    db.add(test_user)
    await db.commit()

    # Log test account creation (audit trail)
    await log_developer_action(
        developer_id=current_user.id,
        action="create_test_account",
        environment=environment,
        details={
            "test_user_id": str(test_user.id),
            "test_user_email": test_email,
            "reason": request.reason,
            "expires_at": test_user.test_expires_at.isoformat()
        }
    )

    logger.warning(
        f"Developer test account created",
        environment=environment,
        developer=current_user.email,
        test_account=test_email,
        reason=request.reason
    )

    return TestAccountResponse(
        id=test_user.id,
        email=test_email,
        password=test_password,  # Return password for developer to use
        expires_at=test_user.test_expires_at,
        environment=environment,
        created_by=current_user.email,
        reason=request.reason,
        warning="This account will be automatically deleted after expiration"
    )


@router.get("/test-accounts")
async def list_my_test_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    environment: str = Depends(get_environment)
) -> List[TestAccountInfo]:
    """
    List test accounts created by current developer.
    """
    if not current_user.can_create_test_accounts:
        raise HTTPException(status_code=403, detail="Not authorized")

    test_accounts = await db.execute(
        select(User).where(
            User.is_test_account == True,
            User.created_by_developer == current_user.id
        )
    )

    return [
        TestAccountInfo(
            id=account.id,
            email=account.email,
            created_at=account.created_at,
            expires_at=account.test_expires_at,
            is_expired=account.test_expires_at < datetime.now()
        )
        for account in test_accounts.scalars()
    ]


@router.delete("/test-accounts/{account_id}")
async def delete_test_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Delete a test account (only your own).
    """
    if not current_user.can_create_test_accounts:
        raise HTTPException(status_code=403, detail="Not authorized")

    test_account = await db.get(User, account_id)

    if not test_account or not test_account.is_test_account:
        raise HTTPException(status_code=404, detail="Test account not found")

    if test_account.created_by_developer != current_user.id:
        raise HTTPException(status_code=403, detail="Not your test account")

    await db.delete(test_account)
    await db.commit()

    return {"message": "Test account deleted"}
```

### Step 3.2: Statistics Filtering

```python
# app/services/stats.py

async def get_production_statistics(
    db: AsyncSession,
    environment: str
) -> dict:
    """
    Get statistics excluding developer test accounts.
    """
    # Exclude test accounts from statistics
    total_users = await db.scalar(
        select(func.count(User.id)).where(
            User.is_test_account == False  # ← Exclude test accounts
        )
    )

    active_users = await db.scalar(
        select(func.count(User.id)).where(
            User.is_test_account == False,
            User.is_active == True
        )
    )

    # Separate statistics for test accounts
    test_account_count = await db.scalar(
        select(func.count(User.id)).where(
            User.is_test_account == True
        )
    )

    return {
        "environment": environment,
        "production_users": {
            "total": total_users,
            "active": active_users
        },
        "developer_test_accounts": {
            "total": test_account_count,
            "warning": "These are excluded from production statistics"
        }
    }
```

---

## 🔐 Implementation: Phase 4 - Complete Separation

### Step 4.1: Environment Configuration

```bash
# .env.dev
ENVIRONMENT=dev
DATABASE_URL=postgresql://localhost:5432/wisqu_dev
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents_dev
REDIS_URL=redis://localhost:6379/0
IDENTITY_SERVICE_URL=https://auth.wisqu.com

# .env.stage
ENVIRONMENT=stage
DATABASE_URL=postgresql://stage-db:5432/wisqu_stage
QDRANT_URL=https://stage-qdrant.wisqu.com
QDRANT_COLLECTION=documents_stage
REDIS_URL=redis://stage-redis:6379/0
IDENTITY_SERVICE_URL=https://auth.wisqu.com

# .env.prod
ENVIRONMENT=prod
DATABASE_URL=postgresql://prod-db:5432/wisqu_prod
QDRANT_URL=https://qdrant.wisqu.com
QDRANT_COLLECTION=documents_prod
REDIS_URL=redis://prod-redis:6379/0
IDENTITY_SERVICE_URL=https://auth.wisqu.com
```

### Step 4.2: Qdrant Collection Isolation

```python
# app/services/rag.py

class RAGService:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT")
        self.collection_name = f"documents_{self.environment}"

    async def search_documents(self, query: str, user_id: UUID):
        """
        Search documents in environment-specific collection.
        """
        # Each environment has completely separate collection
        results = await self.qdrant.search(
            collection_name=self.collection_name,  # documents_dev, documents_stage, documents_prod
            query=query,
            limit=10,
            filter={
                "must": [
                    {"key": "environment", "match": {"value": self.environment}},
                    # Additional filters based on user access
                ]
            }
        )

        logger.info(
            "Document search",
            environment=self.environment,
            user_id=str(user_id),
            results=len(results)
        )

        return results
```

---

## 🚀 User Flows

### Flow 1: Normal User (Prod Only)

```
1. User visits wisqu.com
2. Clicks "Login"
3. Redirected to auth.wisqu.com
4. Enters credentials
5. Identity Service checks: user.environment_access = ["prod"]
6. Redirected back to wisqu.com with prod token
7. User can only access prod environment
```

### Flow 2: Tester (Stage Only)

```
1. Tester visits stage.wisqu.com
2. Clicks "Login"
3. Redirected to auth.wisqu.com
4. Enters credentials
5. Identity Service checks: user.environment_access = ["stage"]
6. Redirected back to stage.wisqu.com with stage token
7. Tester can only access stage environment
8. Tests with realistic but non-production data
```

### Flow 3: Developer (All Environments)

```
1. Developer visits auth.wisqu.com
2. Enters credentials
3. Identity Service shows:
   "You have access to:
    • Dev (developer role)
    • Stage (developer role)
    • Prod (developer role)"
4. Developer selects "Stage" with reason: "Debugging issue #123"
5. Redirected to stage.wisqu.com with stage token
6. Can create test account if needed
7. Can switch to other environments anytime
```

### Flow 4: Developer Creates Test Account in Prod

```
1. Developer logged into prod with developer role
2. Navigates to /developer/test-accounts
3. Clicks "Create Test Account"
4. Enters reason: "Testing reported login issue from user@example.com"
5. Sets expiration: 24 hours
6. System creates:
   Email: dev-test-a1b2c3d4@test.wisqu.com
   Password: <auto-generated>
   Marked as: is_test_account=True
   Created by: <developer_id>
7. Developer uses this account to replicate issue
8. Account automatically deleted after 24 hours
9. All actions logged for audit
```

---

## 📊 Access Control Matrix

| User Type | Dev Access | Stage Access | Prod Access | Can Create Test Accounts |
|-----------|------------|--------------|-------------|--------------------------|
| End User | ❌ No | ❌ No | ✅ Yes (user role) | ❌ No |
| Tester | ❌ No | ✅ Yes (tester role) | ❌ No | ❌ No |
| Developer | ✅ Yes (developer role) | ✅ Yes (developer role) | ✅ Yes (developer role) | ✅ Yes (stage/prod) |
| Admin | ✅ Yes (admin role) | ✅ Yes (admin role) | ✅ Yes (admin role) | ✅ Yes (all envs) |
| Super Admin | ✅ Yes (superadmin) | ✅ Yes (superadmin) | ✅ Yes (superadmin) | ✅ Yes (all envs) |

---

## 🔒 Security Considerations

### 1. Environment Token Validation

```python
def validate_environment_token(token: str, required_environment: str):
    """
    Ensure token is for the correct environment.
    """
    payload = decode_jwt(token)

    if payload.get("environment") != required_environment:
        raise SecurityError(
            f"Token mismatch: expected {required_environment}, got {payload.get('environment')}"
        )

    return payload
```

### 2. Test Account Safeguards

```python
# Prevent test accounts from critical actions
@require_non_test_account
async def process_payment(user: User, amount: Decimal):
    """Test accounts can't make real payments."""
    if user.is_test_account:
        raise HTTPException(
            status_code=403,
            detail="Test accounts cannot perform this action"
        )
```

### 3. Audit Logging

```python
class DeveloperAction(Base):
    """Audit log for all developer actions in stage/prod."""
    __tablename__ = "developer_actions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    developer_id = Column(PG_UUID(as_uuid=True), nullable=False)
    environment = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    # "create_test_account", "delete_test_account", "access_user_data", etc.

    reason = Column(String(500))
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 📋 Implementation Checklist

### Phase 1: Central Identity Service (Week 1-2)
- [ ] Create identity service database
- [ ] Implement CentralUser model
- [ ] Create login endpoint
- [ ] Create environment token endpoint
- [ ] Add environment access control
- [ ] Add audit logging
- [ ] Test authentication flow

### Phase 2: Environment Separation (Week 2-3)
- [ ] Deploy 3 separate apps (dev/stage/prod)
- [ ] Configure separate databases
- [ ] Configure separate Qdrant collections
- [ ] Configure separate Redis instances
- [ ] Implement environment JWT validation
- [ ] Test environment isolation

### Phase 3: Cross-Environment Access (Week 3-4)
- [ ] Implement environment switcher UI
- [ ] Add developer dashboard
- [ ] Test developer access to multiple environments
- [ ] Verify audit logging works
- [ ] Test token expiration and refresh

### Phase 4: Developer Test Accounts (Week 4-5)
- [ ] Add is_test_account field to User model
- [ ] Create test account creation endpoint
- [ ] Implement test account expiration
- [ ] Add statistics filtering
- [ ] Create cleanup job for expired test accounts
- [ ] Test end-to-end developer testing flow

### Phase 5: Documentation & Training (Week 5)
- [ ] Document architecture
- [ ] Create developer guide
- [ ] Create tester guide
- [ ] Train team on new system
- [ ] Monitor usage for 2 weeks

---

## 🎯 Benefits

### Complete Isolation
- ✅ Separate users in each environment
- ✅ Separate databases (no shared data)
- ✅ Separate document collections
- ✅ User in prod ≠ user in dev

### Controlled Cross-Environment Access
- ✅ Developers can access multiple environments
- ✅ All access logged and audited
- ✅ Reason required for prod access
- ✅ Can revoke access per environment

### Developer Testing Support
- ✅ Create test accounts in stage/prod
- ✅ Test accounts clearly marked
- ✅ Automatic expiration and cleanup
- ✅ Statistics exclude test accounts
- ✅ Full audit trail

### Security
- ✅ Single sign-on experience
- ✅ Environment token validation
- ✅ Audit logging for all actions
- ✅ Test accounts can't perform critical actions

---

## 💰 Cost Estimate

### Infrastructure
- **Identity Service**: $20-50/month (small server)
- **Dev Environment**: $50-100/month
- **Stage Environment**: $100-200/month
- **Prod Environment**: $200-500/month (based on load)

**Total**: ~$370-850/month

### Development Time
- **Phase 1**: 1-2 weeks
- **Phase 2**: 1-2 weeks
- **Phase 3**: 1-2 weeks
- **Phase 4**: 1-2 weeks
- **Phase 5**: 1 week

**Total**: 5-9 weeks (1-2 developers)

---

## 🚀 Quick Start (Simplified Version)

If full federated identity is too complex initially, start with **Option 2 (Shared Auth)** as a stepping stone:

1. **Week 1**: Add environment_access field to existing User model
2. **Week 2**: Deploy 3 separate apps with separate databases
3. **Week 3**: Add environment validation to JWT
4. **Week 4**: Add developer test account feature
5. **Later**: Migrate to full federated identity

---

## 📞 Questions to Answer Before Implementation

1. **Identity Provider:**
   - Build custom or use existing (Keycloak, Auth0)?
   - Recommendation: Start custom, migrate to managed later

2. **Environment Domains:**
   - dev.wisqu.com, stage.wisqu.com, wisqu.com?
   - Or: wisqu.dev, wisqu.staging, wisqu.com?

3. **Developer Access:**
   - Should developers need approval for prod access?
   - Should prod access be temporary (e.g., 24 hours)?

4. **Test Account Limits:**
   - Max test accounts per developer?
   - Max test account lifetime?
   - Recommended: 5 accounts, 7 days max

5. **Audit Requirements:**
   - Who should be notified of prod access?
   - How long to keep audit logs?
   - Recommended: 1 year minimum

---

## 🎯 Recommendation Summary

**For your specific requirements, I recommend:**

1. **Start with Shared Authentication (Option 2)** for faster implementation
2. **Separate databases, Qdrant, Redis** for each environment
3. **Add developer test account feature** from day one
4. **Implement audit logging** for all cross-environment access
5. **Plan migration to Federated Identity (Option 3)** within 6-12 months

This gives you:
- ✅ Complete data separation
- ✅ Controlled cross-environment access
- ✅ Developer testing capabilities
- ✅ Faster time to market
- ✅ Clear migration path to best practice architecture

---

**Ready to implement when you approve the approach! 🚀**

---

## ✅ IMPLEMENTATION STATUS

**Status:** ✅ **IMPLEMENTED** (Phases 1 & 2 Complete)
**Implementation Date:** 2025-11-07
**Version:** 2.0.0

The multi-environment architecture with data promotion pipeline has been successfully implemented following the recommendations above. See the implementation details below.

---

# 📦 IMPLEMENTATION DOCUMENTATION

## Phase 1: Core Environment Infrastructure ✅ COMPLETED

### 1.1 Environment Mixins (`src/app/models/mixins.py`)

Created comprehensive mixin system for environment awareness:

#### `EnvironmentPromotionMixin`
Automatically adds environment tracking, test data detection, and promotion support to any model:

```python
from app.models.mixins import EnvironmentPromotionMixin

class MyModel(Base, EnvironmentPromotionMixin):
    __tablename__ = "my_table"
    # ... your fields

    # Automatically gets:
    # - environment (dev/stage/prod)
    # - is_test_data, test_data_reason
    # - is_promotable, promotion_status
    # - source_id, source_environment
    # - promoted_at, promoted_by_user_id
    # - Helper methods: approve_for_promotion(), mark_as_test_data(), etc.
```

**Key Fields:**
- `environment`: Current environment (dev, stage, prod)
- `is_test_data`: Auto-detected or manually marked test data
- `test_data_reason`: Why marked as test data (e.g., "matches pattern: John Doe")
- `is_promotable`: Can this item be promoted?
- `promotion_status`: draft, approved, promoted, deprecated
- `source_id`: ID in source environment (for linking promoted items)
- `source_environment`: Where this was promoted from

**Helper Properties:**
- `is_production`: Check if this is production data
- `is_development`: Check if this is development data
- `is_staging`: Check if this is staging data
- `can_be_promoted`: Check if ready for promotion
- `is_promoted_item`: Check if this was promoted from another environment

#### `TimestampMixin`
- `created_at`: Auto-set on creation
- `updated_at`: Auto-updated on modification

#### `SoftDeleteMixin`
- `deleted_at`: Soft delete timestamp
- `is_deleted`: Soft delete flag
- Helper methods: `soft_delete()`, `restore()`, `is_active`

### 1.2 Test Data Detection (`src/app/utils/test_data_detector.py`)

Automatic test data detection with 40+ patterns:

```python
from app.utils.test_data_detector import TestDataDetector

# Check if text is test data
is_test, reason = TestDataDetector.is_test_data("John Doe")
# Returns: (True, "Matches test pattern: john\\s*doe")

# Check entire model instance
is_test, reason = TestDataDetector.check_model(user_instance)

# Scan and mark test data in database
stats = await TestDataDetector.scan_and_mark_test_data(
    db, User, "dev", batch_size=100
)
```

**Built-in Patterns:**
- Generic keywords: test, demo, dummy, sample, example
- Test names: John Doe, Jane Doe, test user
- Persian patterns: تست, آزمایش, نمونه
- Email patterns: test@test.com, *@test.*
- Sequential: test1, test2, user123
- Lorem ipsum, placeholder text

**Custom Patterns:**
```python
# Add organization-specific patterns
TestDataDetector.add_custom_pattern(r"company-test-\\d+")
```

### 1.3 Environment Tracking Models (`src/app/models/environment.py`)

#### `EnvironmentPromotion`
Audit log for all environment promotions:

```python
promotion = EnvironmentPromotion(
    promotion_type="stored_files",
    source_environment="dev",
    target_environment="stage",
    items_promoted={
        "promoted_ids": ["uuid1", "uuid2"],
        "total_count": 2
    },
    status="success",  # pending, in_progress, success, failed, rolled_back
    success_count=2,
    error_count=0,
    promoted_by_user_id=developer_id,
    reason="Deploy approved RAG documents",
    rollback_data={
        "created_item_ids": ["new_uuid1", "new_uuid2"]
    }
)
```

**Key Features:**
- Full audit trail of promotions
- Success/error tracking
- Rollback support with rollback data
- Duration tracking
- Detailed error logging

#### `EnvironmentAccessLog`
Tracks cross-environment access:

```python
access_log = EnvironmentAccessLog(
    user_id=developer_id,
    environment="prod",
    access_type="data_access",  # login, test_account_create, api_call
    reason="Debugging reported issue #123",
    ip_address="192.168.1.1",
    metadata={"ticket_id": "123"}
)
```

#### `DeveloperAction`
Tracks privileged developer actions in stage/prod:

```python
action = DeveloperAction(
    developer_id=developer_id,
    environment="prod",
    action="create_test_account",
    reason="Testing authentication flow for bug #456",
    details={"test_user_email": "test@test.com"},
    success=True
)
```

### 1.4 Environment Configuration (`src/app/core/config.py`)

Added environment-specific settings with auto-configuration:

```python
class Settings(BaseSettings):
    # Environment tracking
    environment: str = "dev"  # dev, test, stage, prod

    # Retention policies (auto-configured based on environment)
    environment_data_retention_days: int = 30  # dev: 30, stage: 90, prod: 365
    environment_auto_cleanup_enabled: bool = True  # disabled in prod

    # Promotion settings
    promotion_enabled: bool = True
    promotion_allowed_paths: str = "dev->stage,stage->prod,dev->prod"

    # Helper methods
    def get_bucket_name(self, base_bucket: str) -> str:
        """Get environment-prefixed bucket name."""
        return f"{self.environment}-{base_bucket}"
        # wisqu-images → dev-wisqu-images (in dev)

    def get_collection_name(self, base_collection: str) -> str:
        """Get environment-specific Qdrant collection name."""
        return f"{base_collection}_{self.environment}"
        # islamic_knowledge → islamic_knowledge_dev

    @property
    def is_production(self) -> bool:
        return self.environment == "prod"
```

**Auto-Configuration:**
- Retention policies adjust based on environment
- Cleanup enabled in dev/stage, disabled in prod
- Test accounts allowed but audited in prod

### 1.5 Environment-Aware MinIO Storage (`src/app/services/minio_storage_service.py`)

MinIO service automatically prefixes buckets by environment:

```python
# Upload file
result = await minio_service.upload_file(
    bucket="wisqu-images",
    file_data=image_bytes,
    filename="profile.jpg"
)
# Actual bucket: dev-wisqu-images (in dev environment)
# Adds environment metadata tag

# Download file (environment handled automatically)
file_data = await minio_service.download_file(
    bucket="wisqu-images",
    object_name="profile.jpg"
)
```

**Environment Isolation:**
- All buckets auto-prefixed: `{env}-{bucket_name}`
- Environment metadata added to all uploads
- Separate buckets per environment prevent data mixing

---

## Phase 2: Promotion System & Tools ✅ COMPLETED

### 2.1 Updated Models

**StoredFile** and **UserStorageQuota** now include:
- ✅ EnvironmentPromotionMixin
- ✅ TimestampMixin
- ✅ SoftDeleteMixin
- ✅ Full environment awareness

### 2.2 Environment-Scoped Repository (`src/app/repositories/base.py`)

Base repository with automatic environment filtering:

```python
from app.repositories.base import EnvironmentAwareRepository

class UserRepository(EnvironmentAwareRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(
            db,
            User,
            auto_exclude_test_data=True  # Exclude test data in prod
        )

# Usage
repo = UserRepository(db)

# Automatically scoped to current environment
users = await repo.get_all()  # Only current environment's users

# Automatically excludes test data in production
user = await repo.get_by_id(user_id)  # Excludes test data if in prod

# Get promotable items
promotable = await repo.get_promotable_items()  # Only approved, non-test items

# Approve for promotion
await repo.approve_for_promotion(item_id)

# Mark as test data
await repo.mark_as_test_data(item_id, reason="Contains placeholder text")

# Cross-environment access (admin only)
item = await repo.get_by_id_any_environment(item_id, "prod")
```

**Features:**
- Automatic environment filtering
- Test data exclusion (configurable)
- Promotion helpers
- Cross-environment queries for admin/debugging

### 2.3 Promotion Service (`src/app/services/promotion_service.py`)

Comprehensive promotion service for moving data between environments:

```python
from app.services.promotion_service import EnvironmentPromotionService

service = EnvironmentPromotionService(db, minio_service)

# Preview what will be promoted
preview = await service.preview_promotion(
    model_class=StoredFile,
    source_env="dev",
    target_env="stage",
    item_ids=None  # None = all approved items
)
print(f"Will promote {preview.total_count} items")
print(f"Total size: {preview.total_size_bytes} bytes")
print(f"Errors: {preview.errors}")

# Execute promotion
result = await service.execute_promotion(
    model_class=StoredFile,
    source_env="dev",
    target_env="stage",
    promoted_by_user_id=developer_id,
    reason="Deploy approved RAG documents",
    item_ids=None  # None = all approved items
)
print(f"Promoted {result.success_count} items")
print(f"Errors: {result.error_count}")

# Rollback if needed
await service.rollback_promotion(
    promotion_id=result.promotion_id,
    rolled_back_by_user_id=admin_id
)
```

**Features:**
- Preview before execution
- Validation of promotion paths
- Automatic file copying (MinIO)
- Vector copying support (Qdrant) - placeholder for Phase 3
- Full audit logging
- Rollback support
- Error tracking per item

**Promotion Flow:**
1. Validate promotion path (dev→stage allowed?)
2. Query approved, non-test items
3. Copy each item to target environment
4. Copy associated files (MinIO)
5. Update source items as "promoted"
6. Create promotion audit record
7. Store rollback data

### 2.4 Promotion CLI Tool (`scripts/promote.py`)

Command-line tool for managing promotions:

```bash
# Preview promotion
python scripts/promote.py preview stored_files dev stage

# Execute promotion
python scripts/promote.py execute stored_files dev stage \
    --user-id 12345678-1234-1234-1234-123456789abc \
    --reason "Deploy approved RAG documents"

# Promote specific items only
python scripts/promote.py execute stored_files dev stage \
    --user-id 12345678-1234-1234-1234-123456789abc \
    --item-ids uuid1 uuid2 uuid3

# Rollback promotion
python scripts/promote.py rollback 87654321-4321-4321-4321-cba987654321 \
    --user-id 12345678-1234-1234-1234-123456789abc

# Scan for test data
python scripts/promote.py scan-test-data dev stored_files

# Approve item for promotion
python scripts/promote.py approve stored_files 11111111-2222-3333-4444-555555555555
```

**Features:**
- Interactive preview with counts and sizes
- Validation before execution
- Detailed error reporting
- Color-coded output (✅ ❌ ⚠️)

### 2.5 Environment Cleanup Job (`scripts/cleanup_environments.py`)

Scheduled job for managing environment data lifecycle:

```bash
# Dry run (preview what will be deleted)
python scripts/cleanup_environments.py --dry-run

# Execute cleanup
python scripts/cleanup_environments.py

# Cleanup specific environment
python scripts/cleanup_environments.py --environment dev

# Cleanup specific model
python scripts/cleanup_environments.py --model stored_files

# Delete only test data (7+ days old)
python scripts/cleanup_environments.py --test-data-only

# Schedule with cron (daily at 2 AM)
0 2 * * * cd /path/to/app && python scripts/cleanup_environments.py
```

**Features:**
- Respects retention policies per environment
- Never auto-deletes production data
- Skips promoted items
- Dry-run mode for safety
- Detailed statistics
- Test data only mode

**Retention Policies:**
- Dev: 30 days (auto-cleanup enabled)
- Stage: 90 days (auto-cleanup enabled)
- Prod: 365 days (auto-cleanup DISABLED, manual only)

### 2.6 Database Migration (`alembic/versions/20251107_1400_add_environment_promotion_support.py`)

Comprehensive migration that:
- ✅ Adds EnvironmentPromotionMixin fields to stored_files
- ✅ Adds EnvironmentPromotionMixin fields to user_storage_quotas
- ✅ Creates environment_promotions table
- ✅ Creates environment_access_logs table
- ✅ Creates developer_actions table
- ✅ Creates all necessary indexes
- ✅ Sets default environment to 'prod' for existing data

**Migration Commands:**
```bash
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

---

## 🎯 Usage Examples

### Example 1: Create and Promote RAG Document

```python
# 1. Create document in dev environment
# (environment auto-set to 'dev' from settings)
file = StoredFile(
    filename="islamic_knowledge.pdf",
    bucket="wisqu-documents",
    purpose="rag_corpus",
    # ... other fields
)
db.add(file)
await db.commit()

# 2. Test data auto-detection runs
# (if filename contains test patterns, auto-marks as test data)

# 3. Approve for promotion
file.approve_for_promotion()
# Sets: is_promotable=True, promotion_status='approved'
await db.commit()

# 4. Preview promotion
preview = await promotion_service.preview_promotion(
    StoredFile, "dev", "stage"
)
print(f"Will promote {preview.total_count} documents")

# 5. Execute promotion
result = await promotion_service.execute_promotion(
    StoredFile, "dev", "stage",
    promoted_by_user_id=developer_id,
    reason="Deploy approved knowledge base"
)
print(f"Promoted {result.success_count} documents")

# 6. Document now exists in both dev and stage
# - Dev: original (marked as promoted)
# - Stage: new copy (linked via source_id)
```

### Example 2: Scan and Clean Test Data

```python
# Scan dev environment for test data
stats = await TestDataDetector.scan_and_mark_test_data(
    db, StoredFile, "dev"
)
print(f"Marked {stats['marked_as_test']} items as test data")

# Clean up old test data (7+ days old)
# Using cleanup script
subprocess.run([
    "python", "scripts/cleanup_environments.py",
    "--environment", "dev",
    "--test-data-only"
])
```

### Example 3: Cross-Environment Repository Usage

```python
from app.repositories.base import EnvironmentAwareRepository

# Create environment-aware repository
repo = EnvironmentAwareRepository(db, StoredFile)

# Get all files in current environment (excludes test data in prod)
files = await repo.get_all(limit=100)

# Get promotable items
promotable = await repo.get_promotable_items()

# Approve item for promotion
await repo.approve_for_promotion(file_id)

# Mark as test data
await repo.mark_as_test_data(
    file_id,
    reason="Developer test file"
)

# Admin: access item from different environment
prod_file = await repo.get_by_id_any_environment(
    file_id,
    "prod"
)
```

---

## 🔒 Security Considerations

### 1. Automatic Test Data Exclusion
- Production queries automatically exclude test data
- Configurable via `auto_exclude_test_data` parameter
- 40+ built-in patterns for test data detection

### 2. Promotion Validation
- Validates promotion paths (dev→stage allowed, stage→dev blocked)
- Checks promotion_enabled setting
- Verifies items are approved and not test data

### 3. Audit Logging
- All promotions logged in environment_promotions table
- Cross-environment access logged in environment_access_logs
- Developer actions logged in developer_actions table

### 4. Rollback Support
- Rollback data stored for all promotions
- Can reverse promotions if issues detected
- Tracks who performed rollback

### 5. Environment Isolation
- MinIO: Separate buckets per environment
- Qdrant: Separate collections per environment (Phase 3)
- Redis: Separate DB numbers per environment (Phase 3)

---

## 📊 Monitoring and Metrics

### Promotion Metrics
Query `environment_promotions` table for:
- Success rate by environment path
- Average promotion duration
- Most promoted models
- Error rates

```sql
SELECT
    promotion_type,
    source_environment,
    target_environment,
    COUNT(*) as total_promotions,
    SUM(success_count) as total_items_promoted,
    SUM(error_count) as total_errors,
    AVG(duration_seconds) as avg_duration
FROM environment_promotions
WHERE status = 'success'
GROUP BY promotion_type, source_environment, target_environment;
```

### Test Data Detection
```sql
SELECT
    environment,
    COUNT(*) as total_test_items,
    test_data_reason,
    COUNT(*) as count
FROM stored_files
WHERE is_test_data = true
GROUP BY environment, test_data_reason
ORDER BY count DESC;
```

### Environment Distribution
```sql
SELECT
    environment,
    promotion_status,
    COUNT(*) as count,
    SUM(file_size_bytes) as total_bytes
FROM stored_files
WHERE is_deleted = false
GROUP BY environment, promotion_status;
```

---

## 🚀 Next Steps (Phase 3)

### Planned Enhancements:

1. **Qdrant Environment Isolation**
   - Environment-specific collections
   - Vector copying during promotion
   - Collection naming: `{collection}_{environment}`

2. **Redis Environment Isolation**
   - Environment-specific DB numbers
   - Cache isolation per environment
   - DB mapping: dev=0-2, stage=6-8, prod=9-11

3. **Langfuse Environment Projects**
   - Separate projects per environment
   - Environment tagging in traces
   - Cross-environment LLM cost tracking

4. **API Endpoints**
   - REST API for promotion management
   - Web UI for promotion review
   - Real-time promotion status

5. **Additional Model Updates**
   - User model with EnvironmentPromotionMixin
   - Conversation model
   - Message model
   - RAG document models

6. **Enhanced Test Data Detection**
   - ML-based test data detection
   - Learn from manual markings
   - Organization-specific pattern learning

7. **Automated Promotion Pipelines**
   - CI/CD integration
   - Automatic promotion after tests pass
   - Scheduled promotions (e.g., weekly stage→prod)

---

**Generated by:** Claude Code
**Date:** 2025-11-07
**Version:** 2.0.0
**Status:** ✅ **IMPLEMENTED** - Phases 1 & 2 Complete
