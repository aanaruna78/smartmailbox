# Smart Mailbox - Operations Runbooks

Quick reference for common operational tasks and incident response.

---

## Table of Contents
- [Service Management](#service-management)
- [Incident Response](#incident-response)
- [Performance Issues](#performance-issues)
- [Database Operations](#database-operations)
- [LLM Issues](#llm-issues)

---

## Service Management

### Start All Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop All Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Single Service
```bash
docker-compose -f docker-compose.prod.yml restart api
# Options: api, worker, web, db, redis, ollama
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Single service (last 100 lines)
docker logs --tail 100 -f smartmailbox-api
```

### Check Health
```bash
curl http://localhost:8000/health/
```

---

## Incident Response

### API Not Responding

1. **Check container status**
   ```bash
   docker ps | grep smartmailbox-api
   ```

2. **Check logs for errors**
   ```bash
   docker logs --tail 200 smartmailbox-api
   ```

3. **Verify database connection**
   ```bash
   docker exec smartmailbox-api python -c "from app.db.session import SessionLocal; db = SessionLocal(); print('OK')"
   ```

4. **Restart API**
   ```bash
   docker-compose -f docker-compose.prod.yml restart api
   ```

### Worker Not Processing Jobs

1. **Check pending jobs count**
   ```bash
   curl http://localhost:8000/health/worker
   ```

2. **Check worker logs**
   ```bash
   docker logs --tail 200 smartmailbox-worker
   ```

3. **Restart worker**
   ```bash
   docker-compose -f docker-compose.prod.yml restart worker
   ```

4. **Clear stuck jobs (if needed)**
   ```bash
   docker exec -it smartmailbox-db psql -U smartmailbox -c \
     "UPDATE jobs SET status='pending', attempts=0 WHERE status='processing' AND started_at < NOW() - INTERVAL '1 hour';"
   ```

### Database Connection Issues

1. **Check DB container**
   ```bash
   docker ps | grep smartmailbox-db
   docker logs --tail 50 smartmailbox-db
   ```

2. **Test connection**
   ```bash
   docker exec smartmailbox-db pg_isready -U smartmailbox
   ```

3. **Check disk space**
   ```bash
   docker exec smartmailbox-db df -h /var/lib/postgresql/data
   ```

4. **Restart database (last resort)**
   ```bash
   docker-compose -f docker-compose.prod.yml restart db
   ```

---

## Performance Issues

### High Memory Usage

1. **Check container stats**
   ```bash
   docker stats --no-stream
   ```

2. **Identify memory hogs**
   ```bash
   docker top smartmailbox-api
   ```

3. **Clear Redis cache**
   ```bash
   docker exec smartmailbox-redis redis-cli FLUSHDB
   ```

### Slow API Responses

1. **Check metrics**
   ```bash
   curl http://localhost:8000/metrics/performance
   ```

2. **Check database slow queries**
   ```bash
   docker exec -it smartmailbox-db psql -U smartmailbox -c \
     "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

3. **Scale workers** (if job backlog)
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --scale worker=2
   ```

### Job Queue Backlog

1. **Check queue depth**
   ```bash
   curl http://localhost:8000/health/worker
   ```

2. **View pending jobs**
   ```bash
   docker exec -it smartmailbox-db psql -U smartmailbox -c \
     "SELECT type, COUNT(*) FROM jobs WHERE status='pending' GROUP BY type;"
   ```

3. **Scale workers temporarily**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --scale worker=3
   ```

---

## Database Operations

### Check Table Sizes
```bash
docker exec -it smartmailbox-db psql -U smartmailbox -c \
  "SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass)) 
   FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(tablename::regclass) DESC;"
```

### Vacuum Database
```bash
docker exec smartmailbox-db psql -U smartmailbox -c "VACUUM ANALYZE;"
```

### Reset Auto-increment
```bash
docker exec -it smartmailbox-db psql -U smartmailbox -c \
  "SELECT setval(pg_get_serial_sequence('jobs', 'id'), COALESCE(MAX(id), 1)) FROM jobs;"
```

---

## LLM Issues

### Ollama Not Responding

1. **Check container**
   ```bash
   docker ps | grep ollama
   docker logs --tail 50 smartmailbox-ollama
   ```

2. **Test LLM connection**
   ```bash
   curl http://localhost:11434/api/version
   ```

3. **List available models**
   ```bash
   docker exec smartmailbox-ollama ollama list
   ```

4. **Restart Ollama**
   ```bash
   docker-compose -f docker-compose.prod.yml restart ollama
   ```

### Model Not Loaded

```bash
# Pull model
docker exec smartmailbox-ollama ollama pull llama3.2

# Verify
docker exec smartmailbox-ollama ollama list
```

---

## Escalation

If issues persist after following runbooks:

1. Collect logs: `docker-compose -f docker-compose.prod.yml logs > logs_$(date +%Y%m%d).txt`
2. Export health status: `curl http://localhost:8000/health/ > health.json`
3. Document timeline and actions taken
4. Escalate to development team
