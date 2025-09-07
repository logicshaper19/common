import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  CloudArrowUpIcon, 
  DocumentIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { documentsApi } from '../../api/documents';

interface DocumentUploadProps {
  poId?: string;
  documentType: string;
  onBehalfOf?: string; // Company ID if uploading as proxy
  required?: boolean;
  onUploadComplete?: (document: any) => void;
  onUploadError?: (error: string) => void;
  className?: string;
}

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  document?: any;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  poId,
  documentType,
  onBehalfOf,
  required = false,
  onUploadComplete,
  onUploadError,
  className = ''
}) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    progress: 0
  });

  const getDocumentTypeInfo = (type: string) => {
    const typeInfo = {
      rspo_certificate: {
        label: 'RSPO Certificate',
        description: 'Upload RSPO certification documents (PDF, JPG, PNG)',
        acceptedTypes: '.pdf,.jpg,.jpeg,.png',
        maxSize: 10 * 1024 * 1024 // 10MB
      },
      catchment_polygon: {
        label: 'Catchment Area Polygon',
        description: 'Upload mill catchment area data (GeoJSON, ZIP)',
        acceptedTypes: '.json,.geojson,.zip',
        maxSize: 5 * 1024 * 1024 // 5MB
      },
      harvest_record: {
        label: 'Harvest Record',
        description: 'Upload harvest records and production data (PDF, Excel, CSV)',
        acceptedTypes: '.pdf,.xlsx,.xls,.csv',
        maxSize: 10 * 1024 * 1024 // 10MB
      },
      audit_report: {
        label: 'Audit Report',
        description: 'Upload third-party audit reports (PDF)',
        acceptedTypes: '.pdf',
        maxSize: 20 * 1024 * 1024 // 20MB
      }
    };
    return typeInfo[type as keyof typeof typeInfo] || {
      label: 'Document',
      description: 'Upload document',
      acceptedTypes: '.pdf',
      maxSize: 10 * 1024 * 1024
    };
  };

  const typeInfo = getDocumentTypeInfo(documentType);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // Validate file size
    if (file.size > typeInfo.maxSize) {
      const maxSizeMB = typeInfo.maxSize / (1024 * 1024);
      const error = `File too large. Maximum size is ${maxSizeMB}MB`;
      setUploadState({ status: 'error', progress: 0, error });
      onUploadError?.(error);
      return;
    }

    setUploadState({ status: 'uploading', progress: 0 });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', documentType);
      
      if (poId) {
        formData.append('po_id', poId);
      }
      
      if (onBehalfOf) {
        formData.append('on_behalf_of_company_id', onBehalfOf);
      }

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 200);

      const response = await documentsApi.uploadDocument(formData);

      clearInterval(progressInterval);
      
      setUploadState({
        status: 'success',
        progress: 100,
        document: response
      });

      onUploadComplete?.(response);

    } catch (error: any) {
      setUploadState({
        status: 'error',
        progress: 0,
        error: error.message || 'Upload failed'
      });
      onUploadError?.(error.message || 'Upload failed');
    }
  }, [documentType, poId, onBehalfOf, typeInfo.maxSize, onUploadComplete, onUploadError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: typeInfo.acceptedTypes.split(',').reduce((acc, type) => {
      acc[type.trim()] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxFiles: 1,
    disabled: uploadState.status === 'uploading' || uploadState.status === 'success'
  });

  const resetUpload = () => {
    setUploadState({ status: 'idle', progress: 0 });
  };

  const getStatusIcon = () => {
    switch (uploadState.status) {
      case 'uploading':
        return (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        );
      case 'success':
        return <CheckCircleIcon className="h-8 w-8 text-green-600" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />;
      default:
        return <CloudArrowUpIcon className="h-8 w-8 text-neutral-400" />;
    }
  };

  const getStatusMessage = () => {
    switch (uploadState.status) {
      case 'uploading':
        return `Uploading... ${uploadState.progress}%`;
      case 'success':
        return `✓ ${uploadState.document?.original_file_name} uploaded successfully`;
      case 'error':
        return `✗ ${uploadState.error}`;
      default:
        return isDragActive ? 'Drop file here...' : 'Click to upload or drag and drop';
    }
  };

  return (
    <div className={`document-upload ${className}`}>
      <div className="mb-3">
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          {typeInfo.label}
          {required && <span className="text-red-500 ml-1">*</span>}
          {onBehalfOf && (
            <span className="ml-2 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
              Uploading as proxy
            </span>
          )}
        </label>
        <p className="text-xs text-neutral-500">{typeInfo.description}</p>
      </div>

      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-primary-400 bg-primary-50' : 'border-neutral-300'}
          ${uploadState.status === 'uploading' ? 'pointer-events-none opacity-75' : ''}
          ${uploadState.status === 'success' ? 'border-green-300 bg-green-50' : ''}
          ${uploadState.status === 'error' ? 'border-red-300 bg-red-50' : ''}
          hover:border-primary-400 hover:bg-primary-50
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-3">
          {getStatusIcon()}
          
          <div>
            <p className="text-sm font-medium text-neutral-700">
              {getStatusMessage()}
            </p>
            
            {uploadState.status === 'idle' && (
              <p className="text-xs text-neutral-500 mt-1">
                {typeInfo.acceptedTypes.toUpperCase()} up to {Math.round(typeInfo.maxSize / (1024 * 1024))}MB
              </p>
            )}
          </div>

          {uploadState.status === 'uploading' && (
            <div className="w-full max-w-xs">
              <div className="bg-neutral-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadState.progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {(uploadState.status === 'success' || uploadState.status === 'error') && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                resetUpload();
              }}
              className="text-xs text-neutral-500 hover:text-neutral-700 underline"
            >
              Upload different file
            </button>
          )}
        </div>
      </div>

      {uploadState.status === 'success' && uploadState.document && (
        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <DocumentIcon className="h-4 w-4 text-green-600" />
              <span className="text-sm text-green-800">
                {uploadState.document.original_file_name}
              </span>
            </div>
            <span className="text-xs text-green-600">
              {new Date(uploadState.document.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
