# Smart Mailbox - Architecture Diagram

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Browser["🌐 Web Browser"]
    end

    subgraph "Frontend (React)"
        WebApp["📱 React Web App<br/>Port 3000"]
        AuthProvider["🔐 AuthProvider"]
        Dashboard["📊 Dashboard"]
        Inbox["📥 Inbox"]
        Mailboxes["📬 Mailbox Manager"]
    end

    subgraph "API Gateway"
        Nginx["🔀 Nginx<br/>Port 80"]
    end

    subgraph "Backend (FastAPI)"
        API["⚡ FastAPI Server<br/>Port 8000"]
        AuthRoutes["🔑 Auth Routes"]
        EmailRoutes["📧 Email Routes"]
        MailboxRoutes["📮 Mailbox Routes"]
        GmailService["📨 Gmail Service"]
    end

    subgraph "Background Workers"
        Worker["⚙️ Celery Workers"]
        EmailSync["🔄 Email Sync"]
        AIProcessor["🤖 AI Processor"]
    end

    subgraph "Data Layer"
        PostgreSQL["🐘 PostgreSQL<br/>Port 5432"]
        Redis["🔴 Redis<br/>Port 6379"]
    end

    subgraph "External Services"
        GoogleOAuth["🔒 Google OAuth"]
        GmailAPI["📬 Gmail API"]
        LLM["🧠 LLM API"]
    end

    Browser --> WebApp
    WebApp --> Nginx
    Nginx --> API
    
    WebApp --> AuthProvider
    AuthProvider --> Dashboard
    AuthProvider --> Inbox
    AuthProvider --> Mailboxes
    
    API --> AuthRoutes
    API --> EmailRoutes
    API --> MailboxRoutes
    API --> GmailService
    
    AuthRoutes --> GoogleOAuth
    GmailService --> GmailAPI
    
    API --> PostgreSQL
    API --> Redis
    Worker --> Redis
    Worker --> PostgreSQL
    
    Worker --> EmailSync
    Worker --> AIProcessor
    AIProcessor --> LLM
```

---

## Component Details

### Frontend (React + TypeScript)
| Component | Description |
|-----------|-------------|
| `AuthProvider` | Manages user authentication state and Google OAuth |
| `Dashboard` | Main dashboard with email statistics |
| `InboxList` | Email inbox with search, filter, and bulk actions |
| `MailboxForm` | Connect external mailboxes via IMAP/SMTP |
| `Layout` | App shell with navigation and theme toggle |

### Backend (FastAPI + Python)
| Route | Endpoint | Description |
|-------|----------|-------------|
| Auth | `/auth/google/oauth` | Google OAuth login with Gmail scopes |
| Emails | `/emails` | Email CRUD operations |
| Mailboxes | `/mailboxes` | Mailbox connection management |
| Gmail | `/gmail/inbox` | Direct Gmail API access |
| Jobs | `/jobs` | Background job monitoring |

### Data Models
```mermaid
erDiagram
    USER ||--o{ MAILBOX : has
    USER ||--o{ EMAIL : receives
    MAILBOX ||--o{ EMAIL : contains
    
    USER {
        int id PK
        string email
        string full_name
        string google_access_token
        string google_refresh_token
        boolean is_active
        string role
    }
    
    MAILBOX {
        int id PK
        int user_id FK
        string email_address
        string provider
        string imap_host
        string smtp_host
    }
    
    EMAIL {
        int id PK
        int mailbox_id FK
        string subject
        string sender
        text body
        boolean is_read
        datetime received_at
    }
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Material UI, React Router |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 15 |
| **Cache/Queue** | Redis |
| **Workers** | Celery |
| **Auth** | Google OAuth 2.0, JWT |
| **Email** | Gmail API, IMAP/SMTP |
| **AI** | LLM Integration for drafts |
| **Container** | Docker, Docker Compose |
| **Proxy** | Nginx |

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Google

    User->>Frontend: Click "Sign in with Google"
    Frontend->>Google: OAuth Request (email, profile, gmail.readonly)
    Google->>User: Consent Screen
    User->>Google: Grant Permission
    Google->>Frontend: Access Token
    Frontend->>Backend: POST /auth/google/oauth
    Backend->>Google: Verify Token + Get User Info
    Google->>Backend: User Data
    Backend->>Backend: Create/Update User + Store Token
    Backend->>Frontend: JWT Session Cookie
    Frontend->>User: Redirect to Dashboard
```

---

## Deployment Architecture

```mermaid
graph LR
    subgraph "Docker Compose"
        nginx[Nginx :80]
        web[Web App :3000]
        api[API :8000]
        worker[Worker]
        db[(PostgreSQL :5432)]
        redis[(Redis :6379)]
    end

    nginx --> web
    nginx --> api
    api --> db
    api --> redis
    worker --> db
    worker --> redis
```

---

*Developed by [ThinkHive Labs](https://www.thinkhivelabs.com)*
