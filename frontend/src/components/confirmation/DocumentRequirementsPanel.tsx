/**
 * Document Requirements Panel
 * Enhanced component for managing document requirements in PO confirmation workflow
 */
import React, { useState, useEffect } from 'react';
import {
  DocumentIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CloudArrowUpIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { DocumentUpload } from '../documents/DocumentUpload';
import { 
  documentRequirementsService,
  DocumentRequirement,
  DocumentStatus,
  DocumentValidationStatus
} from '../../services/documentRequirements';

interface DocumentRequirementsPanelProps {
  poId: string;
  onValidationChange?: (canConfirm: boolean, progress: any) => void;
  onDocumentUpload?: (documentType: string) => void;
  className?: string;
}

export const DocumentRequirementsPanel: React.FC<DocumentRequirementsPanelProps> = ({
  poId,
  onValidationChange,
  onDocumentUpload,
  className = ''
}) => {
  const [requirements, setRequirements] = useState<DocumentRequirement[]>([]);
  const [validationStatus, setValidationStatus] = useState<DocumentValidationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState<DocumentRequirement | null>(null);
  const [progress, setProgress] = useState({
    total: 0,
    completed: 0,
    percentage: 0,
    required_completed: 0,
    required_total: 0
  });

  // Load document requirements and status
  const loadDocumentData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [requirementsData, progressData] = await Promise.all([
        documentRequirementsService.getDocumentRequirements(poId),
        documentRequirementsService.getDocumentProgress(poId)
      ]);

      setRequirements(requirementsData.requirements);
      setValidationStatus(requirementsData.validation_status);
      setProgress(progressData);

      // Notify parent component
      if (onValidationChange) {
        onValidationChange(requirementsData.can_confirm, progressData);
      }
    } catch (err) {
      console.error('Error loading document data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load document requirements');
    } finally {
      setLoading(false);
    }
  };

  // Refresh validation status
  const refreshValidationStatus = async () => {
    try {
      const [statusData, progressData] = await Promise.all([
        documentRequirementsService.getDocumentValidationStatus(poId),
        documentRequirementsService.getDocumentProgress(poId)
      ]);

      setValidationStatus(statusData.validation_status);
      setProgress(progressData);

      if (onValidationChange) {
        onValidationChange(statusData.can_confirm, progressData);
      }
    } catch (err) {
      console.error('Error refreshing validation status:', err);
    }
  };

  useEffect(() => {
    if (poId) {
      loadDocumentData();
    }
  }, [poId]);

  // Handle document upload
  const handleUploadClick = (requirement: DocumentRequirement) => {
    setSelectedRequirement(requirement);
    setShowUploadModal(true);
    
    if (onDocumentUpload) {
      onDocumentUpload(requirement.type);
    }
  };

  // Handle upload completion
  const handleUploadComplete = async () => {
    setShowUploadModal(false);
    setSelectedRequirement(null);
    
    // Refresh status after upload
    await refreshValidationStatus();
  };

  // Get status for a specific requirement
  const getRequirementStatus = (requirement: DocumentRequirement): DocumentStatus | null => {
    return validationStatus?.document_status.find(status => status.type === requirement.type) || null;
  };

  // Render requirement item
  const renderRequirementItem = (requirement: DocumentRequirement) => {
    const status = getRequirementStatus(requirement);
    const formatted = documentRequirementsService.formatRequirement(requirement);
    const statusColor = status ? documentRequirementsService.getStatusColor(status) : 'neutral';
    const statusText = status ? documentRequirementsService.getStatusText(status) : 'Not checked';

    return (
      <div key={requirement.type} className="flex items-center justify-between p-4 border border-neutral-200 rounded-lg">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0 mt-1">
            {status?.uploaded && status?.valid ? (
              <CheckCircleIconSolid className="h-5 w-5 text-green-500" />
            ) : status?.uploaded && !status?.valid ? (
              <XCircleIcon className="h-5 w-5 text-red-500" />
            ) : requirement.required ? (
              <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />
            ) : (
              <DocumentIcon className="h-5 w-5 text-neutral-400" />
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-medium text-neutral-900">{formatted.title}</h4>
              <Badge variant={formatted.badge === 'required' ? 'warning' : 'neutral'} size="sm">
                {formatted.badge}
              </Badge>
            </div>
            
            <p className="text-xs text-neutral-500 mt-1">{formatted.description}</p>
            <p className="text-xs text-neutral-400 mt-1">Formats: {formatted.formats}</p>
            
            <div className="flex items-center space-x-2 mt-2">
              <Badge variant={statusColor} size="sm">
                {statusText}
              </Badge>
              {status?.uploaded_at && (
                <span className="text-xs text-neutral-400">
                  Uploaded {new Date(status.uploaded_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex-shrink-0">
          <Button
            variant={status?.uploaded && status?.valid ? 'secondary' : 'primary'}
            size="sm"
            onClick={() => handleUploadClick(requirement)}
          >
            <CloudArrowUpIcon className="h-4 w-4 mr-1" />
            {status?.uploaded ? 'Replace' : 'Upload'}
          </Button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <ClockIcon className="h-6 w-6 text-neutral-400 mr-2" />
            <span className="text-neutral-500">Loading document requirements...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <XCircleIcon className="h-6 w-6 text-red-500 mr-2" />
            <span className="text-red-600">{error}</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className={className}>
      {/* Progress Summary */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-neutral-900">Document Requirements</h3>
            <Badge variant={validationStatus?.all_required_uploaded ? 'success' : 'warning'}>
              {progress.required_completed}/{progress.required_total} Required
            </Badge>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {/* Progress bar */}
            <div>
              <div className="flex justify-between text-sm text-neutral-600 mb-1">
                <span>Overall Progress</span>
                <span>{progress.percentage}%</span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>
            </div>
            
            {/* Status summary */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-neutral-600">
                {progress.completed} of {progress.total} documents uploaded
              </span>
              {validationStatus?.all_required_uploaded ? (
                <span className="text-green-600 font-medium">Ready to confirm</span>
              ) : (
                <span className="text-amber-600 font-medium">
                  {progress.required_total - progress.required_completed} required documents missing
                </span>
              )}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Requirements List */}
      <Card>
        <CardHeader>
          <h4 className="text-md font-medium text-neutral-900">Document Checklist</h4>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {requirements.map(renderRequirementItem)}
          </div>
        </CardBody>
      </Card>

      {/* Upload Modal */}
      {showUploadModal && selectedRequirement && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-neutral-900 mb-4">
              Upload {selectedRequirement.name}
            </h3>
            
            <DocumentUpload
              poId={poId}
              documentType={selectedRequirement.type}
              required={selectedRequirement.required}
              onUploadComplete={handleUploadComplete}
              onUploadError={(error) => {
                console.error('Upload error:', error);
                setError(error);
              }}
            />
            
            <div className="flex justify-end space-x-3 mt-6">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowUploadModal(false);
                  setSelectedRequirement(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
