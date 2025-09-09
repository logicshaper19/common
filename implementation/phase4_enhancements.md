# Phase 4: User Experience Enhancements

## 🎯 Objective
Implement remaining enhancements for better user experience and code organization.

## 📋 Implementation Items

### 1. Recent Improvements Tracking (4 hours)

#### File: `app/api/transparency.py:501`

**Step 1: Add Recent Improvements Endpoint (2 hours)**

```python
@router.get("/v2/companies/{company_id}/recent-improvements")
async def get_recent_improvements(
    company_id: UUID,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent transparency improvements for a company."""
    
    if not await _can_access_company_data(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get transparency snapshots for comparison
    current_metrics = await _get_transparency_metrics(company_id, db)
    historical_metrics = await _get_historical_transparency_metrics(
        company_id, start_date, db
    )
    
    improvements = _calculate_improvements(current_metrics, historical_metrics)
    
    return {
        "success": True,
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "improvements": improvements
    }

async def _get_historical_transparency_metrics(
    company_id: UUID, 
    date: datetime, 
    db: Session
) -> Optional[Dict[str, Any]]:
    """Get transparency metrics from a specific date."""
    
    # Query transparency snapshots table (if exists) or calculate from historical data
    snapshot = db.query(TransparencySnapshot).filter(
        TransparencySnapshot.company_id == company_id,
        TransparencySnapshot.snapshot_date <= date
    ).order_by(TransparencySnapshot.snapshot_date.desc()).first()
    
    if snapshot:
        return {
            "transparency_to_mill_percentage": snapshot.mill_percentage,
            "transparency_to_plantation_percentage": snapshot.plantation_percentage,
            "total_purchase_orders": snapshot.total_pos,
            "traced_purchase_orders": snapshot.traced_pos
        }
    
    # Fallback: calculate from historical PO data
    return await _calculate_historical_metrics(company_id, date, db)

def _calculate_improvements(
    current: Dict[str, Any], 
    historical: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Calculate improvements between current and historical metrics."""
    
    if not historical:
        return []
    
    improvements = []
    
    # Mill transparency improvement
    mill_current = current.get("transparency_to_mill_percentage", 0)
    mill_historical = historical.get("transparency_to_mill_percentage", 0)
    mill_change = mill_current - mill_historical
    
    if mill_change > 0:
        improvements.append({
            "metric": "mill_transparency",
            "label": "Mill Transparency",
            "current_value": mill_current,
            "previous_value": mill_historical,
            "change": mill_change,
            "change_percentage": (mill_change / mill_historical * 100) if mill_historical > 0 else 0,
            "trend": "improving"
        })
    
    # Plantation transparency improvement
    plantation_current = current.get("transparency_to_plantation_percentage", 0)
    plantation_historical = historical.get("transparency_to_plantation_percentage", 0)
    plantation_change = plantation_current - plantation_historical
    
    if plantation_change > 0:
        improvements.append({
            "metric": "plantation_transparency",
            "label": "Plantation Transparency",
            "current_value": plantation_current,
            "previous_value": plantation_historical,
            "change": plantation_change,
            "change_percentage": (plantation_change / plantation_historical * 100) if plantation_historical > 0 else 0,
            "trend": "improving"
        })
    
    # PO tracing improvement
    traced_current = current.get("traced_purchase_orders", 0)
    traced_historical = historical.get("traced_purchase_orders", 0)
    traced_change = traced_current - traced_historical
    
    if traced_change > 0:
        improvements.append({
            "metric": "traced_orders",
            "label": "Traced Purchase Orders",
            "current_value": traced_current,
            "previous_value": traced_historical,
            "change": traced_change,
            "change_percentage": (traced_change / traced_historical * 100) if traced_historical > 0 else 0,
            "trend": "improving"
        })
    
    return improvements
```

**Step 2: Create Transparency Snapshots Model (1 hour)**

```python
# File: app/models/transparency.py
class TransparencySnapshot(Base):
    __tablename__ = "transparency_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_date = Column(DateTime, nullable=False)
    
    # Metrics at snapshot time
    mill_percentage = Column(Float, default=0.0)
    plantation_percentage = Column(Float, default=0.0)
    total_pos = Column(Integer, default=0)
    traced_pos = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    traced_volume = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")
    
    __table_args__ = (
        Index('ix_transparency_snapshots_company_date', 'company_id', 'snapshot_date'),
    )
```

**Step 3: Frontend Recent Improvements Component (1 hour)**

```typescript
// File: frontend/src/components/transparency/RecentImprovements.tsx
interface RecentImprovementsProps {
  companyId: string;
  className?: string;
}

export const RecentImprovements: React.FC<RecentImprovementsProps> = ({ 
  companyId, 
  className 
}) => {
  const [improvements, setImprovements] = useState<Improvement[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchImprovements();
  }, [companyId, period]);

  const fetchImprovements = async () => {
    try {
      setLoading(true);
      const response = await getRecentImprovements(companyId, period);
      setImprovements(response.data.improvements);
    } catch (error) {
      console.error('Error fetching improvements:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse h-32 bg-gray-200 rounded"></div>;
  }

  if (improvements.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-500" />
            <span>Recent Improvements</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-center py-4">
            No improvements detected in the last {period} days.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-500" />
            <span>Recent Improvements</span>
          </CardTitle>
          
          <select
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          {improvements.map((improvement, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div>
                <p className="font-medium text-green-800">{improvement.label}</p>
                <p className="text-sm text-green-600">
                  Improved by {improvement.change.toFixed(1)}% 
                  ({improvement.change_percentage.toFixed(1)}% increase)
                </p>
              </div>
              
              <div className="text-right">
                <p className="text-lg font-bold text-green-700">
                  {improvement.current_value.toFixed(1)}%
                </p>
                <p className="text-xs text-green-600">
                  from {improvement.previous_value.toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
```

### 2. Client-Specific Dashboard Data (3 hours)

#### File: `frontend/src/pages/TransparencyDashboard.tsx:124,129`

**Implementation:**

```typescript
// Add client filtering for consultant users
const [selectedClient, setSelectedClient] = useState<string>('all');
const [clientCompanies, setClientCompanies] = useState<Company[]>([]);

useEffect(() => {
  if (user?.role === 'consultant') {
    fetchClientCompanies();
  }
}, [user]);

const fetchClientCompanies = async () => {
  try {
    const response = await getConsultantClients();
    setClientCompanies(response.data.clients);
  } catch (error) {
    console.error('Error fetching client companies:', error);
  }
};

// Add client selector for consultants
const ClientSelector = () => {
  if (user?.role !== 'consultant') return null;
  
  return (
    <div className="mb-6">
      <label className="block text-sm font-medium mb-2">Select Client</label>
      <select
        value={selectedClient}
        onChange={(e) => setSelectedClient(e.target.value)}
        className="w-full border rounded-md px-3 py-2"
      >
        <option value="all">All Clients</option>
        {clientCompanies.map(client => (
          <option key={client.id} value={client.id}>
            {client.name}
          </option>
        ))}
      </select>
    </div>
  );
};
```

### 3. Product Router Optimization (1 hour)

#### File: `frontend/src/components/products/ProductsRouter.tsx:14`

**Implementation:**

```typescript
// Optimize with lazy loading and better organization
const ProductList = lazy(() => import('./ProductList'));
const ProductDetail = lazy(() => import('./ProductDetail'));
const ProductCreate = lazy(() => import('./ProductCreate'));

export const ProductsRouter: React.FC = () => {
  return (
    <Suspense fallback={<div className="animate-pulse h-64 bg-gray-200 rounded"></div>}>
      <Routes>
        <Route path="/" element={<ProductList />} />
        <Route path="/create" element={<ProductCreate />} />
        <Route path="/:id" element={<ProductDetail />} />
        <Route path="/:id/edit" element={<ProductCreate />} />
      </Routes>
    </Suspense>
  );
};
```

### 4. Document Metadata Enhancement (2 hours)

#### File: `frontend/src/components/documents/CertificateUpload.tsx:43`

**Implementation:**

```typescript
// Add metadata fields to upload form
const [metadata, setMetadata] = useState({
  tags: [],
  category: '',
  expiryDate: '',
  description: ''
});

const MetadataFields = () => (
  <div className="space-y-4 mt-4">
    <div>
      <label className="block text-sm font-medium mb-1">Category</label>
      <select
        value={metadata.category}
        onChange={(e) => setMetadata(prev => ({ ...prev, category: e.target.value }))}
        className="w-full border rounded-md px-3 py-2"
      >
        <option value="">Select category</option>
        <option value="certification">Certification</option>
        <option value="compliance">Compliance</option>
        <option value="quality">Quality Assurance</option>
        <option value="sustainability">Sustainability</option>
      </select>
    </div>
    
    <div>
      <label className="block text-sm font-medium mb-1">Expiry Date (Optional)</label>
      <input
        type="date"
        value={metadata.expiryDate}
        onChange={(e) => setMetadata(prev => ({ ...prev, expiryDate: e.target.value }))}
        className="w-full border rounded-md px-3 py-2"
      />
    </div>
    
    <div>
      <label className="block text-sm font-medium mb-1">Description</label>
      <textarea
        value={metadata.description}
        onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
        rows={3}
        className="w-full border rounded-md px-3 py-2"
        placeholder="Brief description of the document..."
      />
    </div>
  </div>
);
```

## 🧪 Testing Checklist

### Backend Tests
- [ ] Recent improvements calculation works correctly
- [ ] Historical data retrieval functions properly
- [ ] Transparency snapshots created and queried

### Frontend Tests
- [ ] Recent improvements display correctly
- [ ] Client filtering works for consultants
- [ ] Product router lazy loading functions
- [ ] Document metadata saves properly

## 📊 Success Metrics
- [ ] Recent improvements tracking functional
- [ ] Client-specific data filtering works
- [ ] Product router optimized and performant
- [ ] Document metadata enhancement complete
- [ ] All files remain under 400 lines

## ⏱️ Estimated Timeline
- **Recent Improvements:** 4 hours
- **Client-Specific Data:** 3 hours
- **Product Router:** 1 hour
- **Document Metadata:** 2 hours
- **Total:** 10 hours (1.5 days)
