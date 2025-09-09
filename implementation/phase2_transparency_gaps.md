# Phase 2: Transparency Gap Actions Implementation

## 🎯 Objective
Add actionable gap resolution features to make transparency data actionable rather than just informational.

## 📋 Current State Analysis

### Frontend (TransparencyDashboard.tsx:119)
- ✅ Gap display implemented
- ❌ No action buttons for gap resolution
- ❌ No gap tracking or status updates

## 🔧 Implementation Steps

### Step 1: Backend Gap Actions API (3 hours)

**File:** `app/api/transparency.py`
**Add gap action endpoints:**

```python
@router.post("/v2/companies/{company_id}/gaps/{gap_id}/actions")
async def create_gap_action(
    company_id: UUID,
    gap_id: str,
    action: GapActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create an action to resolve a transparency gap."""
    
    # Validate permissions
    if not await _can_access_company_data(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create gap action record
    gap_action = GapAction(
        id=uuid4(),
        gap_id=gap_id,
        company_id=company_id,
        action_type=action.action_type,
        target_company_id=action.target_company_id,
        message=action.message,
        created_by_user_id=current_user.id,
        status="pending",
        created_at=datetime.utcnow()
    )
    
    db.add(gap_action)
    db.commit()
    
    # Send notification based on action type
    await _send_gap_action_notification(gap_action, db)
    
    return {
        "success": True,
        "action_id": str(gap_action.id),
        "message": f"Gap action '{action.action_type}' created successfully"
    }

@router.get("/v2/companies/{company_id}/gap-actions")
async def get_gap_actions(
    company_id: UUID,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get gap actions for a company."""
    
    query = db.query(GapAction).filter(GapAction.company_id == company_id)
    
    if status:
        query = query.filter(GapAction.status == status)
    
    actions = query.order_by(GapAction.created_at.desc()).all()
    
    return {
        "success": True,
        "actions": [_gap_action_to_dict(action) for action in actions]
    }

@router.patch("/v2/companies/{company_id}/gap-actions/{action_id}")
async def update_gap_action(
    company_id: UUID,
    action_id: UUID,
    update: GapActionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update gap action status."""
    
    action = db.query(GapAction).filter(
        GapAction.id == action_id,
        GapAction.company_id == company_id
    ).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Gap action not found")
    
    action.status = update.status
    action.resolution_notes = update.resolution_notes
    action.resolved_at = datetime.utcnow() if update.status == "resolved" else None
    action.resolved_by_user_id = current_user.id if update.status == "resolved" else None
    
    db.commit()
    
    return {
        "success": True,
        "message": "Gap action updated successfully"
    }
```

### Step 2: Database Models (1 hour)

**File:** `app/models/transparency.py`
**Add gap action model:**

```python
class GapAction(Base):
    __tablename__ = "gap_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    gap_id = Column(String, nullable=False)  # Reference to gap identifier
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    action_type = Column(String, nullable=False)  # request_data, contact_supplier, mark_resolved
    target_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, resolved, cancelled
    
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    resolved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    target_company = relationship("Company", foreign_keys=[target_company_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])
```

### Step 3: Pydantic Schemas (30 minutes)

**File:** `app/schemas/transparency.py`
**Add gap action schemas:**

```python
class GapActionRequest(BaseModel):
    action_type: str  # request_data, contact_supplier, mark_resolved
    target_company_id: Optional[UUID] = None
    message: Optional[str] = None

class GapActionUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None

class GapActionResponse(BaseModel):
    id: UUID
    gap_id: str
    action_type: str
    target_company_name: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    created_by_name: str
    resolved_at: Optional[datetime] = None
    resolved_by_name: Optional[str] = None
    resolution_notes: Optional[str] = None
```

### Step 4: Frontend Gap Actions Component (2 hours)

**File:** `frontend/src/components/transparency/GapActionsPanel.tsx`
**Create new component:**

```typescript
interface GapActionsPanelProps {
  gap: TransparencyGap;
  onActionCreated: () => void;
}

export const GapActionsPanel: React.FC<GapActionsPanelProps> = ({ gap, onActionCreated }) => {
  const [showActionModal, setShowActionModal] = useState(false);
  const [actionType, setActionType] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleCreateAction = async (actionData: GapActionRequest) => {
    try {
      setLoading(true);
      await createGapAction(gap.company_id, gap.id, actionData);
      
      showToast({
        type: 'success',
        message: 'Gap action created successfully'
      });
      
      setShowActionModal(false);
      onActionCreated();
    } catch (error) {
      showToast({
        type: 'error',
        message: 'Failed to create gap action'
      });
    } finally {
      setLoading(false);
    }
  };

  const getActionButtons = () => {
    const buttons = [];
    
    if (gap.gap_type === 'not_traced_to_mill' || gap.gap_type === 'not_traced_to_plantation') {
      buttons.push(
        <Button
          key="request-data"
          size="sm"
          variant="outline"
          onClick={() => {
            setActionType('request_data');
            setShowActionModal(true);
          }}
          className="flex items-center space-x-1"
        >
          <Mail className="h-4 w-4" />
          <span>Request Data</span>
        </Button>
      );
      
      buttons.push(
        <Button
          key="contact-supplier"
          size="sm"
          variant="outline"
          onClick={() => {
            setActionType('contact_supplier');
            setShowActionModal(true);
          }}
          className="flex items-center space-x-1"
        >
          <Phone className="h-4 w-4" />
          <span>Contact Supplier</span>
        </Button>
      );
    }
    
    buttons.push(
      <Button
        key="mark-resolved"
        size="sm"
        variant="secondary"
        onClick={() => {
          setActionType('mark_resolved');
          setShowActionModal(true);
        }}
        className="flex items-center space-x-1"
      >
        <Check className="h-4 w-4" />
        <span>Mark Resolved</span>
      </Button>
    );
    
    return buttons;
  };

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {getActionButtons()}
      
      <GapActionModal
        isOpen={showActionModal}
        onClose={() => setShowActionModal(false)}
        actionType={actionType}
        gap={gap}
        onSubmit={handleCreateAction}
        loading={loading}
      />
    </div>
  );
};
```

### Step 5: Frontend Integration (1.5 hours)

**File:** `frontend/src/pages/TransparencyDashboard.tsx`
**Update gap display to include actions:**

```typescript
// Add to gap table rendering
<TableCell>
  <div className="flex items-center justify-between">
    <Badge variant={gap.gap_type === 'not_traced_to_mill' ? 'warning' : 'error'}>
      {gap.gap_type === 'not_traced_to_mill' ? 'Mill' : 'Plantation'}
    </Badge>
    
    <GapActionsPanel 
      gap={gap} 
      onActionCreated={() => {
        // Refresh gaps data
        fetchTransparencyGaps();
      }}
    />
  </div>
</TableCell>
```

### Step 6: API Service Integration (30 minutes)

**File:** `frontend/src/services/transparencyApi.ts`
**Add gap action methods:**

```typescript
export const createGapAction = async (
  companyId: string,
  gapId: string,
  action: GapActionRequest
): Promise<ApiResponse<any>> => {
  return apiClient.post(`/transparency/v2/companies/${companyId}/gaps/${gapId}/actions`, action);
};

export const getGapActions = async (
  companyId: string,
  status?: string
): Promise<ApiResponse<GapActionResponse[]>> => {
  const params = status ? { status } : {};
  return apiClient.get(`/transparency/v2/companies/${companyId}/gap-actions`, { params });
};

export const updateGapAction = async (
  companyId: string,
  actionId: string,
  update: GapActionUpdate
): Promise<ApiResponse<any>> => {
  return apiClient.patch(`/transparency/v2/companies/${companyId}/gap-actions/${actionId}`, update);
};
```

## 🧪 Testing Checklist

### Backend Tests
- [ ] Gap action creation with proper validation
- [ ] Action status updates work correctly
- [ ] Notifications sent for different action types
- [ ] Permission checks for company access

### Frontend Tests
- [ ] Action buttons display for appropriate gap types
- [ ] Action modal opens and submits correctly
- [ ] Gap data refreshes after action creation
- [ ] Loading and error states handled properly

## 📊 Success Metrics
- [ ] Users can create gap resolution actions
- [ ] Action tracking and status updates work
- [ ] Notifications sent to relevant parties
- [ ] Gap resolution workflow complete
- [ ] All files remain under 400 lines

## ⏱️ Estimated Timeline
- **Backend Implementation:** 4 hours
- **Frontend Components:** 3 hours
- **Integration & Testing:** 1 hour
- **Total:** 8 hours (1 day)
