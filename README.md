# Smart Mailbox

A secure, intelligent mailbox application featuring:
- Thin React UI + Google SSO
- Secure FastAPI backend
- Async workers via queue
- On-prem LLM for compliant AI replies

## Architecture

- **Frontend**: React (apps/web)
- **Backend**: FastAPI (apps/api)
- **Workers**: Python/Celery/Arq (apps/workers)
- **Infrastructure**: Docker Compose, Nginx (infra/)

## Getting Started

1. Copy `.env.example` to `.env`
2. Run `make up`
