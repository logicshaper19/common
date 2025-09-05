# Common Supply Chain Platform - Backend API

A FastAPI-based backend for supply chain transparency platform with unified Purchase Order system.

## Features

- **Unified Purchase Order System**: Single source of truth for supply chain transactions
- **Dual Confirmation Model**: Different interfaces for processors vs originators
- **Transparency Calculations**: Real-time supply chain visibility scoring
- **Viral Onboarding**: Cascade supplier invitation system
- **Business Relationship Management**: Sophisticated data sharing controls
- **Background Processing**: Async transparency calculations with Celery
- **Comprehensive Audit**: Full transaction history and event logging

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with JSONB support
- **Cache/Queue**: Redis for caching and background jobs
- **Background Jobs**: Celery for async processing
- **Authentication**: JWT tokens with secure password hashing
- **Email**: Resend.com API for notifications
- **Deployment**: Docker containers

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd common-backend
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Install dependencies (for local development)**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Checks

- **Basic Health**: `GET /health/`
- **Readiness**: `GET /health/ready`
- **Liveness**: `GET /health/live`

## Testing

Run tests with pytest:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

## Project Structure

```
app/
├── api/                 # API endpoints
├── core/               # Core configuration and utilities
├── models/             # Database models
├── services/           # Business logic services
├── utils/              # Utility functions
└── tests/              # Test modules
```

## Development

### Code Quality

- **Formatting**: Black
- **Import Sorting**: isort
- **Type Checking**: mypy
- **Testing**: pytest with coverage

### Database Migrations

Database schema is managed through SQLAlchemy models. For production, consider using Alembic for migrations.

## Deployment

The application is containerized and can be deployed using:

- Docker Compose (development)
- Kubernetes (production)
- Railway/Render (cloud platforms)

## Contributing

1. Follow the implementation plan in `.kiro/specs/common-backend-mvp/tasks.md`
2. Write tests for new features
3. Maintain code coverage above 80%
4. Follow the existing code style and patterns

## License

[License information]
