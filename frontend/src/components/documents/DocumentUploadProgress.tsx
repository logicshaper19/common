/**
 * Document Upload Progress Component
 * Shows progress and status of document uploads within the confirmation workflow
 */
import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentIcon,
  ClockIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { documentsApi, Document } from '../../api/documents';

export interface DocumentRequirement {
  type: string;
  name: string;
  required: boolean;
  description?: string;
  acceptedFormats?: string[];
}

interface DocumentUploadProgressProps {
  poId: string;
  requirements: DocumentRequirement[];
  onDocumentStatusChange?: (allRequiredUploaded: boolean) => void;
  onUploadDocument?: (requirement: DocumentRequirement) => void;
}

interface DocumentStatus {
  requirement: DocumentRequirement;
  uploaded: boolean;
  document?: Document;
  uploading: boolean;
  error?: string;
}

export const DocumentUploadProgress: React.FC<DocumentUploadProgressProps> = ({
  poId,
  requirements,
  onDocumentStatusChange,
  onUploadDocument
}) => {
  const [documentStatuses, setDocumentStatuses] = useState<DocumentStatus[]>([]);
  const [loading, setLoading] = useState(true);

  // Initialize document statuses
  useEffect(() => {
    const initializeStatuses = () => {
      const statuses = requirements.map(req => ({
        requirement: req,
        uploaded: false,
        uploading: false
      }));
      setDocumentStatuses(statuses);
    };

    initializeStatuses();
    loadExistingDocuments();
  }, [requirements, poId]);

  // Load existing documents for this PO
  const loadExistingDocuments = async () => {
    try {
      setLoading(true);
      const response = await documentsApi.getDocuments({ po_id: poId });
      
      setDocumentStatuses(prevStatuses => 
        prevStatuses.map(status => {
          const existingDoc = response.documents.find(
            doc => doc.document_type === status.requirement.type
          );
          
          return {
            ...status,
            uploaded: !!existingDoc,
            document: existingDoc
          };
        })
      );
    } catch (error) {
      console.error('Failed to load existing documents:', error);
    } finally {
      setLoading(false);
    }
  };

  // Check if all required documents are uploaded
  useEffect(() => {
    const allRequiredUploaded = documentStatuses
      .filter(status => status.requirement.required)
      .every(status => status.uploaded);
    
    onDocumentStatusChange?.(allRequiredUploaded);
  }, [documentStatuses, onDocumentStatusChange]);

  // Handle document upload completion
  const handleDocumentUploaded = (requirement: DocumentRequirement, document: Document) => {
    setDocumentStatuses(prevStatuses =>
      prevStatuses.map(status =>
        status.requirement.type === requirement.type
          ? { ...status, uploaded: true, document, uploading: false, error: undefined }
          : status
      )
    );
  };

  // Handle upload start
  const handleUploadStart = (requirement: DocumentRequirement) => {
    setDocumentStatuses(prevStatuses =>
      prevStatuses.map(status =>
        status.requirement.type === requirement.type
          ? { ...status, uploading: true, error: undefined }
          : status
      )
    );
  };

  // Handle upload error
  const handleUploadError = (requirement: DocumentRequirement, error: string) => {
    setDocumentStatuses(prevStatuses =>
      prevStatuses.map(status =>
        status.requirement.type === requirement.type
          ? { ...status, uploading: false, error }
          : status
      )
    );
  };

  // Get status icon
  const getStatusIcon = (status: DocumentStatus) => {
    if (status.uploading) {
      return <ClockIcon className="h-5 w-5 text-blue-500 animate-pulse" />;
    }
    
    if (status.error) {
      return <XCircleIcon className="h-5 w-5 text-red-500" />;
    }
    
    if (status.uploaded) {
      return <CheckCircleIconSolid className="h-5 w-5 text-green-500" />;
    }
    
    if (status.requirement.required) {
      return <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />;
    }
    
    return <DocumentIcon className="h-5 w-5 text-neutral-400" />;
  };

  // Get status badge
  const getStatusBadge = (status: DocumentStatus) => {
    if (status.uploading) {
      return <Badge variant="primary">Uploading...</Badge>;
    }
    
    if (status.error) {
      return <Badge variant="error">Error</Badge>;
    }
    
    if (status.uploaded) {
      return <Badge variant="success">Uploaded</Badge>;
    }
    
    if (status.requirement.required) {
      return <Badge variant="warning">Required</Badge>;
    }
    
    return <Badge variant="neutral">Optional</Badge>;
  };

  // Calculate progress
  const totalRequired = documentStatuses.filter(s => s.requirement.required).length;
  const uploadedRequired = documentStatuses.filter(s => s.requirement.required && s.uploaded).length;
  const progressPercentage = totalRequired > 0 ? (uploadedRequired / totalRequired) * 100 : 100;

  if (loading) {
    return (
      <Card>
        <CardHeader title="Document Requirements" />
        <CardBody>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="flex items-center space-x-3">
                <div className="h-5 w-5 bg-neutral-200 rounded"></div>
                <div className="flex-1 h-4 bg-neutral-200 rounded"></div>
                <div className="h-6 w-16 bg-neutral-200 rounded"></div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader 
        title="Document Requirements"
        subtitle={`${uploadedRequired} of ${totalRequired} required documents uploaded`}
      />
      <CardBody>
        {/* Progress bar */}
        {totalRequired > 0 && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-neutral-600 mb-2">
              <span>Upload Progress</span>
              <span>{Math.round(progressPercentage)}%</span>
            </div>
            <div className="w-full bg-neutral-200 rounded-full h-2">
              <div 
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Document list */}
        <div className="space-y-4">
          {documentStatuses.map((status, index) => (
            <div 
              key={status.requirement.type}
              className="flex items-center justify-between p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50"
            >
              <div className="flex items-center space-x-3">
                {getStatusIcon(status)}
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-neutral-900">
                    {status.requirement.name}
                  </h4>
                  {status.requirement.description && (
                    <p className="text-xs text-neutral-500 mt-1">
                      {status.requirement.description}
                    </p>
                  )}
                  {status.error && (
                    <p className="text-xs text-red-600 mt-1">
                      Error: {status.error}
                    </p>
                  )}
                  {status.document && (
                    <p className="text-xs text-green-600 mt-1">
                      Uploaded: {status.document.original_file_name}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                {getStatusBadge(status)}
                
                {!status.uploaded && !status.uploading && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onUploadDocument?.(status.requirement)}
                  >
                    Upload
                  </Button>
                )}
                
                {status.uploaded && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onUploadDocument?.(status.requirement)}
                  >
                    Replace
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        {totalRequired > 0 && (
          <div className="mt-6 p-4 bg-neutral-50 rounded-lg">
            <div className="flex items-center space-x-2">
              {progressPercentage === 100 ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />
              )}
              <span className="text-sm font-medium text-neutral-900">
                {progressPercentage === 100 
                  ? 'All required documents uploaded' 
                  : `${totalRequired - uploadedRequired} required documents remaining`
                }
              </span>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};
