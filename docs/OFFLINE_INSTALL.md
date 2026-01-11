# Smart Mailbox - Offline Installation Guide

This guide covers deploying Smart Mailbox in air-gapped or limited-connectivity environments.

## Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended for LLM)
- 50GB disk space

---

## Step 1: Prepare Images on Internet-Connected Machine

### 1.1 Export Docker Images

```bash
# Pull all required images
docker pull python:3.11-slim
docker pull node:20-alpine
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull nginx:alpine
docker pull ollama/ollama:latest

# Save images to tar files
docker save -o smartmailbox-images.tar \
    python:3.11-slim \
    node:20-alpine \
    postgres:16-alpine \
    redis:7-alpine \
    nginx:alpine \
    ollama/ollama:latest
```

### 1.2 Build Application Images

```bash
# Clone repository
git clone https://github.com/your-org/smartmailbox.git
cd smartmailbox

# Build API image
docker build -t smartmailbox-api:latest ./apps/api

# Build Web image
docker build -t smartmailbox-web:latest ./apps/web

# Save application images
docker save -o smartmailbox-app-images.tar \
    smartmailbox-api:latest \
    smartmailbox-web:latest
```

### 1.3 Download LLM Model

```bash
# Run Ollama temporarily to pull model
docker run -d --name ollama-temp ollama/ollama

# Pull your preferred model
docker exec ollama-temp ollama pull llama3.2

# Copy model data
docker cp ollama-temp:/root/.ollama ./ollama-data

# Cleanup
docker stop ollama-temp && docker rm ollama-temp

# Create tarball
tar -czvf ollama-models.tar.gz ollama-data/
```

### 1.4 Package Everything

```bash
# Create offline package
mkdir smartmailbox-offline
cp smartmailbox-images.tar smartmailbox-offline/
cp smartmailbox-app-images.tar smartmailbox-offline/
cp ollama-models.tar.gz smartmailbox-offline/
cp -r smartmailbox/ smartmailbox-offline/source/

tar -czvf smartmailbox-offline-package.tar.gz smartmailbox-offline/
```

---

## Step 2: Transfer to Air-Gapped Machine

Transfer `smartmailbox-offline-package.tar.gz` via:
- USB drive
- Secure file transfer
- Optical media

---

## Step 3: Install on Air-Gapped Machine

### 3.1 Extract Package

```bash
tar -xzvf smartmailbox-offline-package.tar.gz
cd smartmailbox-offline
```

### 3.2 Load Docker Images

```bash
# Load base images
docker load -i smartmailbox-images.tar

# Load application images
docker load -i smartmailbox-app-images.tar
```

### 3.3 Restore LLM Models

```bash
# Extract model data
tar -xzvf ollama-models.tar.gz

# Create volume and copy data
docker volume create ollama_data
docker run --rm -v ollama_data:/dest -v $(pwd)/ollama-data:/src alpine \
    sh -c "cp -r /src/* /dest/"
```

### 3.4 Configure Environment

```bash
cd source

# Copy and edit environment file
cp .env.production.example .env

# Generate secrets
# On a machine with OpenSSL:
# openssl rand -hex 32  # for SECRET_KEY
# openssl rand -hex 32  # for ENCRYPTION_KEY

# Edit .env with your values
nano .env
```

### 3.5 Start Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Verify health
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health/
```

---

## Step 4: Verify Installation

```bash
# Check all services are healthy
docker-compose -f docker-compose.prod.yml ps

# Test API
curl http://localhost:8000/health/

# Test web UI
curl http://localhost:3000/
```

---

## Updating in Offline Environment

1. On internet-connected machine, rebuild images with new code
2. Export new images: `docker save -o update.tar smartmailbox-api:latest smartmailbox-web:latest`
3. Transfer to air-gapped machine
4. Load images: `docker load -i update.tar`
5. Restart services: `docker-compose -f docker-compose.prod.yml up -d`

---

## Troubleshooting

### Images not loading
```bash
# Check Docker daemon is running
sudo systemctl status docker

# Verify tar file integrity
tar -tzvf smartmailbox-images.tar
```

### Database connection failed
```bash
# Check container logs
docker logs smartmailbox-db

# Verify network
docker network ls
```

### LLM not responding
```bash
# Check Ollama logs
docker logs smartmailbox-ollama

# Verify model is loaded
docker exec smartmailbox-ollama ollama list
```

---

## Security Considerations

- Generate unique secrets for each deployment
- Regularly backup database volumes
- Monitor container logs for anomalies
- Keep image tarballs in secure storage
