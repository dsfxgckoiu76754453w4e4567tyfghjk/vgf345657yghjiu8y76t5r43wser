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

**Generated by:** Claude Code
**Date:** 2025-11-06
**Version:** 1.0.0
**Status:** Architecture Recommendations - Ready for Review
