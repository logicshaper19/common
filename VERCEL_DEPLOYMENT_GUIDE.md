# Vercel Deployment Guide

## 🚀 Complete Setup for Vercel Deployment

### Prerequisites
1. **Upstash Redis Account**: Sign up at [upstash.com](https://upstash.com)
2. **PostgreSQL Database**: Use Vercel Postgres, Supabase, or Railway
3. **Vercel Account**: Connect your GitHub repository

---

## 📋 Step-by-Step Deployment

### 1. **Set Up Upstash Redis**

1. Go to [upstash.com](https://upstash.com)
2. Sign up with GitHub (easiest for Vercel integration)
3. Create a new Redis database:
   - Select region closest to your users
   - Choose appropriate plan
4. Copy the Redis URL and REST credentials

### 2. **Set Up PostgreSQL Database**

**Option A: Neon (Recommended for Vercel)**
1. Go to [neon.tech](https://neon.tech)
2. Sign up with GitHub (easiest for Vercel integration)
3. Create a new project:
   - Choose a region close to your users
   - Select PostgreSQL version (latest recommended)
4. Get connection details:
   - Copy the connection string from the "Connect" modal
   - Enable connection pooling (recommended for Vercel)
   - Note the password (you'll need it for environment variables)

**Option B: Vercel Postgres**
1. In Vercel dashboard, go to Storage
2. Create a new Postgres database
3. Copy the connection string

**Option C: Supabase**
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Get the connection string from Settings > Database

**Option D: Railway**
1. Go to [railway.app](https://railway.app)
2. Create a new PostgreSQL service
3. Copy the connection string

### 3. **Configure Vercel Environment Variables**

In your Vercel project dashboard, add these environment variables:

#### **Database Configuration**
```bash
DATABASE_URL=postgresql://username:password@host:port/database
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
```

#### **Redis Configuration**
```bash
REDIS_URL=redis://:password@region-redis.upstash.io:port
UPSTASH_REDIS_REST_URL=https://region-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
```

#### **JWT Configuration**
```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-here-make-it-long-and-random
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### **Application Configuration**
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=Common Supply Chain Platform
APP_VERSION=1.0.0
```

#### **CORS Configuration**
```bash
ALLOWED_ORIGINS=https://your-domain.vercel.app,https://your-frontend.vercel.app
```

#### **Frontend Configuration**
```bash
REACT_APP_API_URL=https://your-backend.vercel.app/api
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
CI=false
```

### 4. **Vercel Project Settings**

#### **Backend Project (API)**
- **Framework Preset**: `Other`
- **Root Directory**: Leave blank (use root)
- **Build Command**: `pip install -r requirements.txt`
- **Output Directory**: Leave blank
- **Install Command**: `pip install -r requirements.txt`

#### **Frontend Project**
- **Framework Preset**: `Create React App`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `frontend/build`
- **Install Command**: `npm install`

### 5. **Database Migration**

After deployment, run database migrations:

```bash
# Connect to your deployed backend
vercel env pull .env.production

# Run migrations
python -m alembic upgrade head
```

### 6. **Test Deployment**

1. **Health Check**: Visit `https://your-backend.vercel.app/health`
2. **API Docs**: Visit `https://your-backend.vercel.app/docs`
3. **Frontend**: Visit `https://your-frontend.vercel.app`

---

## 🔧 Troubleshooting

### Common Issues

#### **Redis Connection Failed**
- Check Redis URL format
- Verify Upstash credentials
- Ensure Redis database is active

#### **Database Connection Failed**
- Verify DATABASE_URL format
- Check database credentials
- Ensure database is accessible from Vercel

#### **Build Failures**
- Check environment variables
- Verify all dependencies in requirements.txt
- Check build logs in Vercel dashboard

#### **CORS Issues**
- Update ALLOWED_ORIGINS with your frontend URL
- Check CORS middleware configuration

### **Environment Variable Checklist**

✅ `DATABASE_URL` - PostgreSQL connection string  
✅ `REDIS_URL` - Upstash Redis connection string  
✅ `JWT_SECRET_KEY` - Long, random secret key  
✅ `ENVIRONMENT=production`  
✅ `REACT_APP_API_URL` - Backend API URL  
✅ `ALLOWED_ORIGINS` - Frontend domain(s)  

---

## 📊 Monitoring

### **Vercel Analytics**
- Enable Vercel Analytics in project settings
- Monitor performance and errors

### **Upstash Monitoring**
- Check Redis metrics in Upstash dashboard
- Monitor connection count and memory usage

### **Database Monitoring**
- Monitor connection pool usage
- Check query performance
- Set up alerts for connection limits

---

## 🚀 Production Checklist

- [ ] All environment variables configured
- [ ] Database migrations completed
- [ ] Redis connection working
- [ ] Frontend connecting to backend
- [ ] CORS properly configured
- [ ] SSL certificates working
- [ ] Error monitoring set up
- [ ] Performance monitoring enabled
- [ ] Backup strategy in place

---

## 📞 Support

If you encounter issues:
1. Check Vercel deployment logs
2. Verify environment variables
3. Test database connectivity
4. Check Redis connection
5. Review CORS configuration

For additional help, check the application logs in Vercel dashboard.
