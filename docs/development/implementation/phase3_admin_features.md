# Phase 3: Admin Features Implementation

## 🎯 Objective
Implement admin override capabilities and enhance business relationship email service for operational flexibility.

## 📋 Implementation Items

### 1. Admin Override Capabilities (4 hours)

#### Files to Update:
- `app/api/documents.py:102`
- `app/services/document_storage.py:422`

#### Step 1: Admin Document Access Override (2 hours)

**File:** `app/api/documents.py`
**Update document access endpoint:**

```python
@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """Get document with admin override capability."""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has access
    has_access = False
    access_reason = "direct_access"
    
    # Normal access check
    if document.company_id == current_user.company_id:
        has_access = True
    
    # Admin override check
    elif current_user.role == "admin":
        has_access = True
        access_reason = "admin_override"
        
        # Log admin override action
        audit_service = AuditService(db)
        await audit_service.log_admin_action(
            admin_user_id=current_user.id,
            action_type="document_access_override",
            target_resource_type="document",
            target_resource_id=str(document_id),
            target_company_id=document.company_id,
            details={
                "document_name": document.filename,
                "original_company": document.company.name,
                "access_reason": "admin_override"
            }
        )
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        upload_date=document.upload_date,
        company_id=document.company_id,
        company_name=document.company.name,
        access_reason=access_reason
    )
```

#### Step 2: Admin Document Deletion Override (2 hours)

**File:** `app/services/document_storage.py`
**Update deletion service:**

```python
async def delete_document(
    self,
    document_id: UUID,
    user: User,
    deletion_reason: Optional[str] = None
) -> bool:
    """Delete document with admin override capability."""
    
    document = self.db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")
    
    # Check permissions
    can_delete = False
    deletion_type = "user_deletion"
    
    # Normal deletion check (user owns document)
    if document.uploaded_by_user_id == user.id:
        can_delete = True
    
    # Admin override check
    elif user.role == "admin":
        can_delete = True
        deletion_type = "admin_override_deletion"
        
        # Log admin override deletion
        audit_service = AuditService(self.db)
        await audit_service.log_admin_action(
            admin_user_id=user.id,
            action_type="document_deletion_override",
            target_resource_type="document",
            target_resource_id=str(document_id),
            target_company_id=document.company_id,
            details={
                "document_name": document.filename,
                "original_uploader": document.uploaded_by.full_name,
                "deletion_reason": deletion_reason or "No reason provided",
                "file_size": document.file_size
            }
        )
    
    if not can_delete:
        raise PermissionError("Insufficient permissions to delete document")
    
    try:
        # Delete from storage
        await self._delete_from_storage(document.file_path)
        
        # Delete from database
        self.db.delete(document)
        self.db.commit()
        
        logger.info(
            f"Document deleted successfully",
            document_id=str(document_id),
            deletion_type=deletion_type,
            admin_user_id=str(user.id) if deletion_type == "admin_override_deletion" else None
        )
        
        return True
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to delete document: {e}")
        raise
```

### 2. Audit Service Enhancement (2 hours)

**File:** `app/services/audit.py`
**Create admin action logging:**

```python
class AuditService:
    def __init__(self, db: Session):
        self.db = db
    
    async def log_admin_action(
        self,
        admin_user_id: UUID,
        action_type: str,
        target_resource_type: str,
        target_resource_id: str,
        target_company_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """Log admin override actions for audit trail."""
        
        audit_event = AuditEvent(
            id=uuid4(),
            event_type="admin_override",
            user_id=admin_user_id,
            company_id=target_company_id,
            resource_type=target_resource_type,
            resource_id=target_resource_id,
            action=action_type,
            details=details or {},
            severity="high",  # Admin overrides are high severity
            timestamp=datetime.utcnow()
        )
        
        self.db.add(audit_event)
        self.db.commit()
        
        # Also create notification for company if applicable
        if target_company_id:
            await self._notify_company_of_admin_action(
                target_company_id, action_type, details
            )
        
        return audit_event.id
    
    async def _notify_company_of_admin_action(
        self,
        company_id: UUID,
        action_type: str,
        details: Dict[str, Any]
    ):
        """Notify company users of admin actions on their resources."""
        
        # Get company admin users
        company_admins = self.db.query(User).filter(
            User.company_id == company_id,
            User.role.in_(["admin", "company_admin"])
        ).all()
        
        notification_service = NotificationService(self.db)
        
        for admin in company_admins:
            await notification_service.create_notification(
                user_id=admin.id,
                type="admin_action",
                title="Admin Action on Company Resource",
                message=f"Platform admin performed {action_type} on company resource",
                data={
                    "action_type": action_type,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
```

### 3. Business Relationship Email Service (Already Implemented)

**Status:** ✅ **COMPLETE**
**File:** `app/services/business_relationship.py:223`

The email service is already implemented with:
- Resend API integration
- HTML email templates
- Professional invitation emails
- Error handling and logging

**Verification:**
```python
# Email service already includes:
async def _send_invitation_email(self, invitation_request, pending_company, relationship):
    """Send professional invitation email using Resend API."""
    # Implementation complete with HTML templates and error handling
```

### 4. Frontend Admin Interface (2 hours)

**File:** `frontend/src/components/admin/AdminOverridePanel.tsx`
**Create admin override interface:**

```typescript
interface AdminOverridePanelProps {
  resourceType: 'document' | 'purchase_order' | 'company';
  resourceId: string;
  onOverrideComplete: () => void;
}

export const AdminOverridePanel: React.FC<AdminOverridePanelProps> = ({
  resourceType,
  resourceId,
  onOverrideComplete
}) => {
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  // Only show for admin users
  if (user?.role !== 'admin') {
    return null;
  }

  const handleOverride = async (action: string) => {
    try {
      setLoading(true);
      
      await performAdminOverride({
        resourceType,
        resourceId,
        action,
        reason: overrideReason
      });
      
      showToast({
        type: 'success',
        message: 'Admin override completed successfully'
      });
      
      setShowOverrideModal(false);
      onOverrideComplete();
    } catch (error) {
      showToast({
        type: 'error',
        message: 'Failed to perform admin override'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-l-4 border-red-500 bg-red-50 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Shield className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-sm font-medium text-red-800">
            Admin Override Available
          </span>
        </div>
        
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowOverrideModal(true)}
          className="border-red-300 text-red-700 hover:bg-red-100"
        >
          Override Access
        </Button>
      </div>
      
      <AdminOverrideModal
        isOpen={showOverrideModal}
        onClose={() => setShowOverrideModal(false)}
        resourceType={resourceType}
        onOverride={handleOverride}
        loading={loading}
        reason={overrideReason}
        onReasonChange={setOverrideReason}
      />
    </div>
  );
};
```

## 🧪 Testing Checklist

### Backend Tests
- [ ] Admin can access cross-company documents
- [ ] Admin can delete any document with proper logging
- [ ] Audit trail captures all admin actions
- [ ] Notifications sent to affected companies

### Frontend Tests
- [ ] Admin override panel only shows for admin users
- [ ] Override modal requires reason input
- [ ] Success/error states handled properly
- [ ] Audit actions logged correctly

## 📊 Success Metrics
- [ ] Admins can override document permissions
- [ ] All admin actions are audited and logged
- [ ] Companies notified of admin actions
- [ ] Email invitation system working
- [ ] All files remain under 400 lines

## ⏱️ Estimated Timeline
- **Admin Override Implementation:** 6 hours
- **Frontend Interface:** 2 hours
- **Testing & Integration:** 2 hours
- **Total:** 10 hours (1.5 days)
