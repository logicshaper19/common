# 🚀 Streaming Chat Assistant with Rich Content

## Overview

This implementation provides a comprehensive streaming chat assistant for the Common palm oil supply chain platform with rich visualizations including charts, tables, graphs, and interactive content.

## 🎯 Features

### Core Functionality
- **Real-time streaming responses** with Server-Sent Events (SSE)
- **Rich content types**: text, charts, tables, graphs, metric cards, alerts
- **Context-aware responses** based on user's company type and role
- **Progressive disclosure** - content streams in as it's generated
- **Interactive elements** - sortable tables, clickable charts, exportable data

### Content Types Supported
- 📊 **Charts**: Line charts, donut charts, bar charts, gauge charts
- 📋 **Tables**: Sortable, filterable, paginated data tables with actions
- 🕸️ **Graphs**: Supply chain network visualizations, flow diagrams
- 📈 **Metric Cards**: KPI displays with trends and icons
- 🚨 **Alerts**: Error, warning, info, and success notifications
- 📍 **Maps**: Supply chain location visualizations (extensible)

### Supply Chain Specific Features
- **Inventory Analysis**: Real-time inventory tracking with visualizations
- **Transparency Metrics**: EUDR compliance, RSPO certification tracking
- **Yield Performance**: OER (Oil Extraction Rate) trends and benchmarks
- **Supplier Networks**: Interactive supply chain relationship mapping
- **Compliance Status**: Regulatory compliance dashboards
- **Processing Efficiency**: Mill performance and transformation metrics

## 🏗️ Architecture

### Backend Components

#### 1. Streaming Assistant Core (`app/core/streaming_assistant.py`)
```python
class SupplyChainStreamingAssistant:
    async def stream_response(user_message, user_context) -> AsyncGenerator[StreamingResponse, None]
    async def analyze_content_requirements(message, context) -> List[str]
    async def stream_inventory_content(user_context) -> AsyncGenerator[StreamingResponse, None]
    async def stream_transparency_content(user_context) -> AsyncGenerator[StreamingResponse, None]
    # ... more content streamers
```

#### 2. API Endpoints (`app/api/streaming_assistant.py`)
- `POST /api/v1/assistant/stream-chat` - Main streaming endpoint
- `POST /api/v1/assistant/stream-chat-sync` - Synchronous collection endpoint
- `GET /api/v1/assistant/stream-chat/health` - Health check
- `GET /api/v1/assistant/stream-chat/features` - Available features
- `GET /api/v1/assistant/stream-chat/test` - Test endpoint

#### 3. Response Types
```python
class ResponseType(Enum):
    TEXT = "text"
    CHART = "chart"
    TABLE = "table"
    GRAPH = "graph"
    METRIC_CARD = "metric_card"
    MAP = "map"
    ALERT = "alert"
    PROGRESS = "progress"
    COMPLETE = "complete"
```

### Frontend Components

#### 1. Main Chat Component (`frontend/src/components/StreamingChatAssistant.jsx`)
- Real-time message streaming with SSE
- Rich content rendering
- Connection status monitoring
- Input suggestions and auto-complete
- Responsive design for mobile/desktop

#### 2. Chart Components (`frontend/src/components/Charts/index.js`)
- **LineChart**: Time series data with benchmarks
- **DonutChart**: Proportional data visualization
- **BarChart**: Comparative data display
- **GaugeChart**: Performance metrics with ranges
- **DataTable**: Sortable, filterable, paginated tables
- **MetricCards**: KPI displays with trends
- **NetworkGraph**: Supply chain relationship mapping

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- FastAPI server running
- React frontend setup

### Backend Setup

1. **Install Dependencies**
```bash
pip install fastapi uvicorn aiohttp
pip install chart.js react-chartjs-2  # For frontend
```

2. **Add to Main App**
```python
# In your main FastAPI app
from app.api.streaming_assistant import router as streaming_router
app.include_router(streaming_router)
```

3. **Environment Variables**
```bash
# Add to your .env file
V2_DASHBOARD_BRAND=true
V2_DASHBOARD_PROCESSOR=true
V2_DASHBOARD_ORIGINATOR=true
V2_NOTIFICATION_CENTER=true
TRANSPARENCY_DEGRADATION_FACTOR=0.95
TRANSPARENCY_CALCULATION_TIMEOUT=30
```

### Frontend Setup

1. **Install Chart Dependencies**
```bash
npm install chart.js react-chartjs-2
```

2. **Import Components**
```jsx
import StreamingChatAssistant from './components/StreamingChatAssistant';
import './components/Charts/Charts.css';
```

3. **Use in Your App**
```jsx
function App() {
  return (
    <div className="App">
      <StreamingChatAssistant />
    </div>
  );
}
```

## 📊 Usage Examples

### Basic Streaming Chat
```javascript
const response = await fetch('/api/v1/assistant/stream-chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    message: "Show me my current inventory",
    include_visualizations: true,
    max_response_time: 30
  })
});

const reader = response.body.getReader();
// Process streaming responses...
```

### Content Type Examples

#### Inventory Analysis
```javascript
// User asks: "Show me my current inventory"
// Response includes:
// 1. Metric cards with total batches, available quantity, product types
// 2. Donut chart showing inventory by product type
// 3. Data table with batch details, sortable and filterable
```

#### Transparency Metrics
```javascript
// User asks: "What's our transparency score?"
// Response includes:
// 1. Gauge chart showing overall transparency percentage
// 2. Supply chain flow graph with traceability mapping
// 3. EUDR compliance table with risk levels
```

#### Yield Performance
```javascript
// User asks: "Show yield performance"
// Response includes:
// 1. Line chart showing OER trends over time
// 2. Bar chart comparing mill efficiency
// 3. Performance comparison table
```

## 🧪 Testing

### Run Test Suite
```bash
python test_streaming_assistant.py
```

### Test Individual Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/assistant/stream-chat/health

# Features
curl http://localhost:8000/api/v1/assistant/stream-chat/features

# Test streaming
curl -X POST http://localhost:8000/api/v1/assistant/stream-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me my inventory", "include_visualizations": true}'
```

### Frontend Testing
```bash
# Start React development server
npm start

# Navigate to the streaming chat component
# Test various queries and visualizations
```

## 🔧 Configuration

### Backend Configuration
```python
# In streaming_assistant.py
class SupplyChainStreamingAssistant:
    def __init__(self):
        # Configure based on your environment
        self.max_response_time = 30
        self.enable_visualizations = True
        self.chart_options = {
            "responsive": True,
            "maintainAspectRatio": False
        }
```

### Frontend Configuration
```javascript
// In StreamingChatAssistant.jsx
const config = {
  maxResponseTime: 30,
  enableVisualizations: true,
  autoScroll: true,
  showSuggestions: true,
  connectionRetryAttempts: 3
};
```

## 📈 Performance Considerations

### Backend Optimization
- **Parallel data fetching** for context building
- **Streaming responses** to reduce perceived latency
- **Caching** for frequently accessed data
- **Connection pooling** for database queries

### Frontend Optimization
- **Lazy loading** of chart components
- **Virtual scrolling** for large tables
- **Debounced search** for table filtering
- **Memoized components** to prevent unnecessary re-renders

### Memory Management
- **Streaming responses** prevent large payloads
- **Component cleanup** on unmount
- **Chart instance disposal** to prevent memory leaks

## 🔒 Security Considerations

### Authentication
- **JWT token validation** for all requests
- **User context isolation** - users only see their company data
- **Role-based access** to different content types

### Data Privacy
- **No sensitive data** in streaming responses
- **Sanitized content** before sending to frontend
- **Audit logging** for compliance tracking

## 🚀 Deployment

### Production Setup
```bash
# Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
npm run build
# Serve static files with nginx or similar
```

### Docker Deployment
```dockerfile
# Add to your existing Dockerfile
COPY frontend/build /app/static
COPY app/core/streaming_assistant.py /app/app/core/
COPY app/api/streaming_assistant.py /app/app/api/
```

## 🔮 Future Enhancements

### Planned Features
- **Voice input/output** for hands-free operation
- **Mobile app integration** with push notifications
- **Advanced analytics** with machine learning insights
- **Multi-language support** for global operations
- **Real-time collaboration** for team discussions

### Extensibility
- **Plugin system** for custom content types
- **Custom chart types** for specific use cases
- **Integration APIs** for third-party tools
- **Webhook support** for external notifications

## 📚 API Reference

### Streaming Endpoint
```http
POST /api/v1/assistant/stream-chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "Show me my inventory",
  "include_visualizations": true,
  "max_response_time": 30,
  "chat_history": ""
}
```

### Response Format
```json
{
  "type": "chart",
  "content": {
    "chart_type": "line",
    "title": "OER Trend",
    "data": [...],
    "options": {...}
  },
  "metadata": {
    "status": "generating",
    "progress": 75
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This implementation is part of the Common platform and follows the same licensing terms.

---

**Built with ❤️ for the Common palm oil supply chain platform**
