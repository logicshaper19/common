# Railway Migration Plan

## Overview
This document outlines the plan to migrate from local PostgreSQL and Redis to Railway's managed infrastructure services.

## Current Setup
- **Backend**: FastAPI with SQLAlchemy ORM
- **Database**: Local PostgreSQL
- **Cache**: Local Redis
- **Frontend**: React with TypeScript
- **Authentication**: JWT tokens
- **Real-time**: WebSocket connections

## Migration Benefits
- **Managed Infrastructure**: No more local service management
- **Scalability**: Easy horizontal scaling
- **Reliability**: Built-in backups and monitoring
- **Cost-Effective**: Pay-as-you-go pricing
- **Deployment**: Simple git-based deployments

## Migration Steps

### Phase 1: Railway Setup
1. **Create Railway Account**
   - Sign up at [railway.app](https://railway.app)
   - Connect GitHub repository

2. **Create Railway Project**
   - New project from GitHub repo
   - Add PostgreSQL service
   - Add Redis service

### Phase 2: Database Migration
1. **Export Local Data**
   ```bash
   pg_dump -h localhost -U postgres -d your_database > backup.sql
   ```

2. **Update Environment Variables**
   ```bash
   # Railway PostgreSQL
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway
   
   # Railway Redis
   REDIS_URL=redis://default:[PASSWORD]@[HOST]:[PORT]
   ```

3. **Import Data to Railway**
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

### Phase 3: Application Configuration
1. **Update Connection Strings**
   - Modify `app/core/config.py`
   - Update Redis connection in `app/core/redis.py`

2. **Environment Variables**
   ```bash
   # Railway will provide these automatically
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   ```

### Phase 4: Deployment
1. **Railway Deployment**
   - Automatic deployment on git push
   - Environment variables from Railway dashboard

2. **Frontend Updates**
   - Update API endpoints to Railway URL
   - Update WebSocket connections

## Configuration Changes

### Database Configuration
```python
# app/core/config.py
class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
```

### Redis Configuration
```python
# app/core/redis.py
redis_client = redis.from_url(settings.redis_url)
```

## Testing Checklist
- [ ] Database connectivity
- [ ] Redis caching
- [ ] Authentication flow
- [ ] WebSocket connections
- [ ] API endpoints
- [ ] Frontend-backend communication

## Rollback Plan
- Keep local services running during migration
- Use feature flags to switch between local/railway
- Database backup before migration

## Timeline
- **Phase 1**: 1-2 hours (Railway setup)
- **Phase 2**: 2-3 hours (Database migration)
- **Phase 3**: 1-2 hours (Configuration)
- **Phase 4**: 1 hour (Deployment)
- **Total**: 5-8 hours

## Cost Estimation
- **PostgreSQL**: ~$5-10/month
- **Redis**: ~$5-10/month
- **Application**: ~$5-20/month
- **Total**: ~$15-40/month

## Notes
- Railway provides automatic SSL certificates
- Built-in monitoring and logging
- Easy scaling with Railway's dashboard
- No need for Docker configuration (Railway handles it)

## Next Steps
1. Create Railway account and project
2. Set up PostgreSQL and Redis services
3. Export and import database
4. Update application configuration
5. Deploy and test

---
*Created: 2025-01-24*
*Status: Planning Phase*
