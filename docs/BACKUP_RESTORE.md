# Smart Mailbox - Backup & Restore Guide

## Overview

Smart Mailbox stores data in:
- **PostgreSQL** - User accounts, emails, drafts, settings
- **Redis** - Session cache, job queue (ephemeral)
- **Ollama** - LLM models (can be re-downloaded)

---

## Quick Backup

```bash
# Full backup (database + configs)
./scripts/backup.sh

# Or manually:
docker exec smartmailbox-db pg_dump -U smartmailbox smartmailbox > backup_$(date +%Y%m%d).sql
```

---

## Detailed Backup Procedures

### 1. Database Backup

```bash
# Create backup directory
mkdir -p backups

# Backup with timestamp
docker exec smartmailbox-db pg_dump -U smartmailbox smartmailbox \
    > backups/db_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec smartmailbox-db pg_dump -U smartmailbox smartmailbox | gzip \
    > backups/db_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 2. Redis Backup (Optional)

```bash
# Trigger RDB snapshot
docker exec smartmailbox-redis redis-cli BGSAVE

# Copy snapshot
docker cp smartmailbox-redis:/data/dump.rdb backups/redis_$(date +%Y%m%d).rdb
```

### 3. Configuration Backup

```bash
# Backup environment and configs
cp .env backups/env_$(date +%Y%m%d).bak
cp docker-compose.prod.yml backups/
```

### 4. Full Volume Backup

```bash
# Stop services (for consistent backup)
docker-compose -f docker-compose.prod.yml stop

# Backup volumes
docker run --rm -v smartmailbox_postgres_data:/data -v $(pwd)/backups:/backup \
    alpine tar czf /backup/postgres_vol_$(date +%Y%m%d).tar.gz /data

docker run --rm -v smartmailbox_redis_data:/data -v $(pwd)/backups:/backup \
    alpine tar czf /backup/redis_vol_$(date +%Y%m%d).tar.gz /data

# Restart services
docker-compose -f docker-compose.prod.yml start
```

---

## Restore Procedures

### 1. Database Restore

```bash
# Stop API and worker
docker-compose -f docker-compose.prod.yml stop api worker

# Restore from SQL file
docker exec -i smartmailbox-db psql -U smartmailbox smartmailbox < backups/db_20260111.sql

# Or from compressed
gunzip -c backups/db_20260111.sql.gz | docker exec -i smartmailbox-db psql -U smartmailbox smartmailbox

# Restart services
docker-compose -f docker-compose.prod.yml start
```

### 2. Volume Restore

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restore postgres volume
docker run --rm -v smartmailbox_postgres_data:/data -v $(pwd)/backups:/backup \
    alpine sh -c "rm -rf /data/* && tar xzf /backup/postgres_vol_20260111.tar.gz -C /"

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Fresh Install + Restore

```bash
# Start fresh database
docker-compose -f docker-compose.prod.yml up -d db

# Wait for DB to be ready
sleep 10

# Restore backup
docker exec -i smartmailbox-db psql -U smartmailbox smartmailbox < backups/db_20260111.sql

# Start remaining services
docker-compose -f docker-compose.prod.yml up -d
```

---

## Automated Backups

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/smartmailbox/scripts/backup.sh >> /var/log/smartmailbox-backup.log 2>&1

# Weekly full backup at Sunday 3 AM
0 3 * * 0 /path/to/smartmailbox/scripts/full-backup.sh >> /var/log/smartmailbox-backup.log 2>&1
```

### Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup
docker exec smartmailbox-db pg_dump -U smartmailbox smartmailbox | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Cleanup old backups
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: db_$DATE.sql.gz"
```

---

## Disaster Recovery

### Complete System Recovery

1. Deploy fresh infrastructure
2. Restore database from backup
3. Configure `.env` with same secrets
4. Start services
5. Verify health: `curl http://localhost:8000/health/`

### Data Verification

```bash
# Check restored data
docker exec -it smartmailbox-db psql -U smartmailbox -c "SELECT COUNT(*) FROM users;"
docker exec -it smartmailbox-db psql -U smartmailbox -c "SELECT COUNT(*) FROM emails;"
```

---

## Best Practices

1. **Test restores regularly** - Verify backups are working
2. **Encrypt backups** - Use GPG for sensitive data
3. **Off-site storage** - Keep copies in separate location
4. **Monitor backup jobs** - Alert on failures
5. **Document recovery time** - Know your RTO/RPO
