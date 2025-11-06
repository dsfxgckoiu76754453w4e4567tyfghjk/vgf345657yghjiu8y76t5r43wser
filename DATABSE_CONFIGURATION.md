# Database Configuration Guide

## Overview

The application now uses **individual database parameters** instead of a single `DATABASE_URL` for better security, flexibility, and configuration management.

## Configuration Parameters

Set these environment variables in your `.env` file:

```bash
# Database Parameters
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=shia_chatbot
DATABASE_DRIVER=postgresql+asyncpg
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

## Benefits

### 1. **No Environment Variable Override Issues**
- Individual parameters cannot be overridden by shell environment variables
- The database URL is **computed** from parameters, not stored
- Eliminates port mismatch issues (e.g., 5432 vs 5433)

### 2. **Better Security**
- Password can be sourced from secure vaults (e.g., HashiCorp Vault, AWS Secrets Manager)
- Each parameter can have different access controls
- Easier to rotate credentials without changing URL format

### 3. **Easier Configuration Management**
- Override only specific parameters (e.g., just the port or host)
- Clearer configuration for different environments
- Better support for Docker/Kubernetes ConfigMaps and Secrets

### 4. **Flexible Connection Building**
- Programmatically construct URLs for different databases
- Example: Connect to `postgres` database for admin operations

## Usage in Code

### Standard Connection
```python
from app.core.config import settings

# Get the database URL (automatically constructed)
url = settings.database_url
# postgresql+asyncpg://postgres:postgres@localhost:5433/shia_chatbot
```

### Alternative Database Connection
```python
from app.core.config import settings

# Connect to a different database (e.g., for admin operations)
postgres_url = settings.get_database_url("postgres")
# postgresql+asyncpg://postgres:postgres@localhost:5433/postgres
```

### Access Individual Parameters
```python
from app.core.config import settings

print(f"Host: {settings.database_host}")
print(f"Port: {settings.database_port}")
print(f"Database: {settings.database_name}")
```

## Migration from DATABASE_URL

### Old Configuration (`.env`)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/shia_chatbot
```

### New Configuration (`.env`)
```bash
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=shia_chatbot
DATABASE_DRIVER=postgresql+asyncpg
```

### Important Notes

1. **Do NOT set `DATABASE_URL` environment variable** - It will be ignored
2. All existing code continues to work (uses `settings.database_url`)
3. Alembic migrations automatically use the new configuration
4. No changes needed in SQLAlchemy models or queries

## Production Best Practices

### 1. Secure Password Management
```bash
# Use environment-specific secrets
DATABASE_PASSWORD=${DB_PASSWORD_FROM_VAULT}
```

### 2. Connection Pooling
```bash
# Adjust based on your workload
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### 3. SSL Configuration
```python
# For production, add SSL parameters to the URL in config.py
def get_database_url(self, database_name: str | None = None) -> str:
    url = f"{self.database_driver}://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{db_name}"
    if self.environment == "prod":
        url += "?ssl=require"
    return url
```

## Docker/Kubernetes Example

### Docker Compose
```yaml
services:
  app:
    environment:
      DATABASE_HOST: postgres-service
      DATABASE_PORT: 5432
      DATABASE_USER: ${DB_USER}
      DATABASE_PASSWORD: ${DB_PASSWORD}
      DATABASE_NAME: shia_chatbot
```

### Kubernetes ConfigMap + Secret
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-config
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "shia_chatbot"
  DATABASE_DRIVER: "postgresql+asyncpg"
---
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  DATABASE_USER: "postgres"
  DATABASE_PASSWORD: "secure-password-here"
```

## Troubleshooting

### Issue: "Database connection failed"
```bash
# Verify individual parameters
poetry run python3 -c "from app.core.config import settings; print(settings.database_url)"
```

### Issue: "Wrong port being used"
```bash
# Check for environment variable override
env | grep DATABASE
# Unset any DATABASE_URL variable
unset DATABASE_URL
```

### Issue: "Alembic migrations fail"
```bash
# Alembic now uses settings.database_url automatically
# Check alembic/env.py for config.set_main_option() call
```

## Files Changed

1. **src/app/core/config.py**
   - Removed `database_url` field
   - Added `database_url` as computed property
   - Added `get_database_url()` method

2. **src/app/core/startup.py**
   - Updated to use `get_database_url("postgres")`

3. **alembic/env.py**
   - Added `config.set_main_option("sqlalchemy.url", settings.database_url)`

4. **.env and .env.example**
   - Replaced `DATABASE_URL` with individual parameters
