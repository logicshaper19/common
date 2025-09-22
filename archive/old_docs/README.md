# Common Supply Chain Platform

A comprehensive supply chain transparency and traceability platform built with FastAPI and React.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis (optional)

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL database
python setup_postgres_local.py

# Start the API server
export DATABASE_URL="postgresql://common_user:common_password@localhost:5432/common_db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Test Credentials
- **Email**: `admin@testmanufacturer.com`
- **Password**: `TestPass123!`

## 📁 Project Structure

```
├── app/                    # Backend FastAPI application
│   ├── api/               # API endpoints
│   ├── core/              # Core functionality (auth, database, etc.)
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── tests/             # Unit tests
├── frontend/              # React frontend application
├── docs/                  # Documentation
├── archive/               # Archived files
│   ├── test_scripts/      # Old test scripts
│   ├── old_docs/          # Old documentation
│   └── setup_scripts/     # Setup scripts
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

### Run Unit Tests
```bash
pytest app/tests/
```

### Test Supply Chain Flow
```bash
python test_supply_chain_direct.py
```

## 🔧 Development

### Database Management
- **Setup**: `python setup_postgres_local.py`
- **Reset**: `python reset_test_data.py`
- **Schema**: See `app/models/` for database models

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Database Schema](docs/database.md)
- [Frontend Guide](docs/frontend.md)
- [Deployment Guide](docs/deployment.md)

## 🐛 Troubleshooting

### Common Issues
1. **Port already in use**: Kill existing processes or use different ports
2. **Database connection**: Ensure PostgreSQL is running and credentials are correct
3. **CORS errors**: Check frontend/backend port configuration

### Getting Help
- Check the logs in the terminal output
- Review the API documentation at `/docs`
- Check the archive folder for old troubleshooting guides

## 📄 License

[Add your license here]