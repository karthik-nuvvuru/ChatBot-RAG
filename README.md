# =============================================================================
# README - NelloreRuchullu (Conversation AI Platform)
# =============================================================================

# Conversation AI Platform

A production-ready conversational AI backend with memory, vector search, real-time streaming, and enterprise-grade infrastructure.

## Features

- **Multi-LLM Support**: Switch between EURI API (development) and Azure OpenAI (production) via environment variable
- **Session Management**: Create, manage, and archive conversation sessions
- **Message Storage**: Store messages with threading support
- **Vector Memory**: Store and search conversation memories using embeddings
- **Redis Caching**: Fast session context and message caching
- **WebSocket Support**: Real-time chat with typing indicators and progress streaming
- **Background Jobs**: Celery tasks for session archival and cleanup
- **File Attachments**: Local or Azure Blob storage support
- **REST API**: Full API with authentication and rate limiting

## Quick Start

### Using Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your API keys
# - Set EURI_API_KEY for development
# - Or set AZURE_OPENAI_* for production

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Local Development

```bash
# Install dependencies
poetry install

# Copy and edit environment
cp .env.example .env

# Start PostgreSQL and Redis (using Docker)
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Start the API
poetry run uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
poetry run celery -A app.celery_app worker --loglevel=info
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `dev` | Environment (dev/prod) |
| `LLM_PROVIDER` | `euri` | LLM provider (euri/azure) |
| `EURI_API_KEY` | - | EURI API key |
| `EURI_BASE_URL` | `https://api.euri.ai/v1` | EURI API URL |
| `EURI_MODEL` | `claude-sonnet-4-20250514` | EURI model name |
| `AZURE_OPENAI_ENDPOINT` | - | Azure OpenAI endpoint |
| `AZURE_OPENAI_KEY` | - | Azure API key |
| `AZURE_DEPLOYMENT_NAME` | `gpt-4o` | Azure deployment name |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Database connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |

### Switching LLM Providers

**Development (EURI):**
```bash
LLM_PROVIDER=euri
EURI_API_KEY=your-key
```

**Production (Azure):**
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_KEY=your-key
AZURE_DEPLOYMENT_NAME=gpt-4o
```

## API Endpoints

### Sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}` - Get session
- `PATCH /api/v1/sessions/{id}` - Update session
- `DELETE /api/v1/sessions/{id}` - Archive session
- `POST /api/v1/sessions/{id}/fork` - Fork session

### Messages
- `POST /api/v1/sessions/{id}/messages` - Add message
- `GET /api/v1/sessions/{id}/messages` - List messages
- `GET /api/v1/messages/{id}/thread` - Get message thread
- `POST /api/v1/chat` - Send message and get AI response
- `POST /api/v1/chat/stream` - Stream AI response

### WebSocket
- `ws://localhost:8000/api/v1/chat/sessions/{id}/ws?token=<jwt>`

## Architecture

```
app/
├── core/           # Configuration, security, logging, rate limiting
├── db/             # Database session and base
├── integrations/llm/  # LLM provider abstraction
├── chat/
│   ├── routers/    # API endpoints
│   ├── websocket/  # WebSocket handlers
│   └── *.py        # Services (session, message, memory, etc.)
├── celery_app/     # Celery configuration and tasks
└── main.py         # FastAPI entry point
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/chat/test_session_manager.py -v
```

## License

MIT