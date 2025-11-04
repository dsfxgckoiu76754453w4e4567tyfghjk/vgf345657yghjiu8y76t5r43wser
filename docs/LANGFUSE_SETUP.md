# Langfuse Setup Guide

Langfuse provides LLM observability and tracing for your application. You can use it in two modes:

1. **Langfuse Cloud** (Recommended) - Managed service, no infrastructure needed
2. **Self-hosted** - Run on your own infrastructure

## Option 1: Langfuse Cloud (RECOMMENDED) ✅

### Why Cloud?
- ✅ **Zero infrastructure** - No Docker containers, no resource usage
- ✅ **Free tier** - 50,000 observations/month
- ✅ **No maintenance** - Automatic updates and scaling
- ✅ **Production-ready** - High availability, backups, monitoring
- ✅ **Fast setup** - 5 minutes to get started

### Setup Steps

1. **Sign up** at [https://cloud.langfuse.com](https://cloud.langfuse.com)

2. **Create a project** and get your API keys:
   - Go to `Project Settings` → `API Keys`
   - Copy your `Public Key` and `Secret Key`

3. **Update your `.env` file**:
   ```bash
   LANGFUSE_ENABLED=true
   LANGFUSE_PUBLIC_KEY=pk-lf-...  # Your public key
   LANGFUSE_SECRET_KEY=sk-lf-...  # Your secret key
   LANGFUSE_HOST=https://cloud.langfuse.com  # EU region
   # LANGFUSE_HOST=https://us.cloud.langfuse.com  # US region
   ```

4. **Done!** Your application will now send traces to Langfuse Cloud.

### Regions Available
- 🇪🇺 **EU**: `https://cloud.langfuse.com`
- 🇺🇸 **US**: `https://us.cloud.langfuse.com`

---

## Option 2: Self-hosted Langfuse

### ⚠️ Important Considerations

**Self-hosting Langfuse v3 requires:**
- PostgreSQL (transactional data)
- ClickHouse (OLAP database for traces)
- Redis (caching and queueing)
- MinIO/S3 (blob storage for events and media)

**Resource Requirements:**
- Minimum: 4GB RAM, 2 CPU cores
- Production: 8GB+ RAM, 4+ CPU cores
- Storage: 20GB+ for databases

**Not recommended for production servers** running other critical services due to resource consumption.

### Setup Steps (Advanced Users)

1. **Uncomment services in `docker-compose.yml`**:

```yaml
services:
  # ... existing services ...

  # ClickHouse (Required for Langfuse v3)
  clickhouse:
    image: docker.io/clickhouse/clickhouse-server:latest
    restart: always
    user: "101:101"
    environment:
      CLICKHOUSE_DB: default
      CLICKHOUSE_USER: clickhouse
      CLICKHOUSE_PASSWORD: changeme-secure-password
    volumes:
      - langfuse_clickhouse_data:/var/lib/clickhouse
      - langfuse_clickhouse_logs:/var/log/clickhouse-server
    ports:
      - "127.0.0.1:8124:8123"  # HTTP port (avoid conflict with other services)
      - "127.0.0.1:9001:9000"  # Native port
    healthcheck:
      test: wget --no-verbose --tries=1 --spider http://localhost:8123/ping || exit 1
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - chatbot-network

  # MinIO (S3-compatible storage - Required for Langfuse v3)
  minio:
    image: docker.io/minio/minio:latest
    restart: always
    entrypoint: sh
    command: -c 'mkdir -p /data/langfuse && minio server --address ":9000" --console-address ":9001" /data'
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: changeme-secure-password
    ports:
      - "9092:9000"  # API port (avoid conflict with other services)
      - "127.0.0.1:9093:9001"  # Console port
    volumes:
      - langfuse_minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 1s
      timeout: 5s
      retries: 5
    networks:
      - chatbot-network

  # Langfuse Web
  langfuse:
    image: langfuse/langfuse:3
    restart: always
    container_name: shia-chatbot-langfuse
    ports:
      - "3001:3000"  # Using 3001 externally (3000 is used by Grafana)
    environment:
      # Database
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/langfuse

      # Security (CHANGE THESE!)
      - NEXTAUTH_SECRET=changeme-secure-secret
      - SALT=changeme-secure-salt
      - ENCRYPTION_KEY=0000000000000000000000000000000000000000000000000000000000000000  # Generate: openssl rand -hex 32

      # URLs
      - NEXTAUTH_URL=http://localhost:3001

      # ClickHouse (Required for v3)
      - CLICKHOUSE_MIGRATION_URL=clickhouse://clickhouse:9000
      - CLICKHOUSE_URL=http://clickhouse:8123
      - CLICKHOUSE_USER=clickhouse
      - CLICKHOUSE_PASSWORD=changeme-secure-password
      - CLICKHOUSE_CLUSTER_ENABLED=false

      # S3/MinIO Storage (Required for v3)
      - LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse
      - LANGFUSE_S3_EVENT_UPLOAD_REGION=auto
      - LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=minio
      - LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=changeme-secure-password
      - LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://minio:9000
      - LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
      - LANGFUSE_S3_EVENT_UPLOAD_PREFIX=events/

      # Redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_AUTH=changeme-redis-password

      # Optional
      - TELEMETRY_ENABLED=true
      - LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=false

    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - chatbot-network

# Add volumes
volumes:
  langfuse_clickhouse_data:
    driver: local
  langfuse_clickhouse_logs:
    driver: local
  langfuse_minio_data:
    driver: local
```

2. **Update your `.env` file**:
   ```bash
   LANGFUSE_ENABLED=true
   LANGFUSE_PUBLIC_KEY=  # Create in Langfuse UI after first login
   LANGFUSE_SECRET_KEY=  # Create in Langfuse UI after first login
   LANGFUSE_HOST=http://localhost:3001
   ```

3. **Start services**:
   ```bash
   make docker-up
   ```

4. **Access Langfuse UI**:
   - URL: http://localhost:3001
   - Create your first user account
   - Generate API keys in Project Settings

### Monitoring Resource Usage

```bash
# Check container resource usage
docker stats shia-chatbot-langfuse shia-chatbot-clickhouse shia-chatbot-minio

# Check disk usage
docker system df
```

---

## Switching Between Cloud and Self-hosted

### From Self-hosted to Cloud:

1. Comment out Langfuse services in `docker-compose.yml`
2. Update `.env`:
   ```bash
   LANGFUSE_HOST=https://cloud.langfuse.com
   LANGFUSE_PUBLIC_KEY=pk-lf-...  # Your Cloud keys
   LANGFUSE_SECRET_KEY=sk-lf-...
   ```
3. Restart your application

### From Cloud to Self-hosted:

1. Uncomment services in `docker-compose.yml`
2. Run `make docker-up`
3. Update `.env`:
   ```bash
   LANGFUSE_HOST=http://localhost:3001
   LANGFUSE_PUBLIC_KEY=  # Your self-hosted keys
   LANGFUSE_SECRET_KEY=
   ```
4. Restart your application

---

## Integration with Your Application

Your application already has Langfuse integrated via LangChain. Example usage:

```python
from langfuse.langchain import CallbackHandler

# Initialize Langfuse handler
langfuse_handler = CallbackHandler()

# Use with LangGraph
graph.stream(
    {"messages": [HumanMessage(content="Hello")]},
    config={"callbacks": [langfuse_handler]}
)
```

All LangChain/LangGraph calls will be automatically traced!

---

## Troubleshooting

### Langfuse Cloud Not Connecting

```bash
# Check if API keys are correct
curl -X POST https://cloud.langfuse.com/api/public/traces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SECRET_KEY"
```

### Self-hosted Langfuse Not Starting

1. **Check logs**:
   ```bash
   docker logs shia-chatbot-langfuse
   docker logs shia-chatbot-clickhouse
   docker logs shia-chatbot-minio
   ```

2. **Verify all services are healthy**:
   ```bash
   docker ps | grep shia-chatbot
   ```

3. **Common issues**:
   - ClickHouse not starting → Check disk space
   - MinIO not accessible → Check port conflicts
   - Connection refused → Verify network connectivity

---

## Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [Self-hosting Guide](https://langfuse.com/self-hosting)
- [LangGraph Integration](https://langfuse.com/docs/integrations/langgraph)

---

## Recommendation

**For your production environment**: Use **Langfuse Cloud**
- No additional infrastructure burden
- Free tier covers most use cases
- Easy to switch to self-hosted later if needed
- Production-ready with backups and monitoring
