import React, { useState } from 'react';
import { DocumentUpload } from './DocumentUpload';
import { ShieldCheckIcon, CalendarIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';

interface CertificateUploadProps {
  poId?: string;
  types: string[]; // ['RSPO', 'NDPE', 'ISPO']
  required?: boolean;
  onBehalfOf?: string;
  onUploadComplete?: (document: any) => void;
  className?: string;
}

interface CertificateMetadata {
  certificateNumber?: string;
  certificateType?: string;
  validFrom?: string;
  validUntil?: string;
  certificationBody?: string;
  millName?: string;
  millCode?: string;
  // Enhanced metadata fields
  tags: string[];
  category: string;
  expiryDate: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  complianceStatus: 'pending' | 'approved' | 'rejected' | 'expired';
}

export const CertificateUpload: React.FC<CertificateUploadProps> = ({
  poId,
  types,
  required = false,
  onBehalfOf,
  onUploadComplete,
  className = ''
}) => {
  const [uploadedCertificates, setUploadedCertificates] = useState<any[]>([]);
  const [showMetadataForm, setShowMetadataForm] = useState<string | null>(null);
  const [certificateMetadata, setCertificateMetadata] = useState<CertificateMetadata>({
    tags: [],
    category: '',
    expiryDate: '',
    description: '',
    priority: 'medium',
    complianceStatus: 'pending'
  });

  const handleUploadComplete = (document: any) => {
    setUploadedCertificates(prev => [...prev, document]);
    setShowMetadataForm(document.id);
    onUploadComplete?.(document);
  };

  const handleMetadataSubmit = async (documentId: string) => {
    try {
      // TODO: Replace with actual API call
      // await documentsApi.updateDocumentMetadata(documentId, certificateMetadata);
      console.log('Updating document metadata:', documentId, certificateMetadata);

      // Update local state
      setUploadedCertificates(prev =>
        prev.map(cert =>
          cert.id === documentId
            ? { ...cert, metadata: certificateMetadata }
            : cert
        )
      );

      setShowMetadataForm(null);
      setCertificateMetadata({
        tags: [],
        category: '',
        expiryDate: '',
        description: '',
        priority: 'medium',
        complianceStatus: 'pending'
      });
    } catch (error) {
      console.error('Failed to update document metadata:', error);
    }
  };

  const getCertificateTypeOptions = () => {
    const options = {
      RSPO: [
        { value: 'IP', label: 'Identity Preserved (IP)' },
        { value: 'SG', label: 'Segregated (SG)' },
        { value: 'MB', label: 'Mass Balance (MB)' },
        { value: 'BC', label: 'Book & Claim (B&C)' }
      ],
      NDPE: [
        { value: 'NDPE_COMPLIANT', label: 'NDPE Compliant' },
        { value: 'NDPE_VERIFIED', label: 'NDPE Verified' }
      ],
      ISPO: [
        { value: 'ISPO_CERTIFIED', label: 'ISPO Certified' }
      ]
    };
    
    // Return options for the first type (can be extended for multiple types)
    return options[types[0] as keyof typeof options] || [];
  };

  const formatCertificateType = (type: string) => {
    const typeLabels = {
      'rspo_certificate': 'RSPO Certificate',
      'ndpe_certificate': 'NDPE Certificate', 
      'ispo_certificate': 'ISPO Certificate'
    };
    return typeLabels[type as keyof typeof typeLabels] || 'Certificate';
  };

  return (
    <div className={`certificate-upload ${className}`}>
      <div className="space-y-6">
        {types.map((type) => (
          <div key={type} className="certificate-type-section">
            <div className="flex items-center space-x-2 mb-4">
              <ShieldCheckIcon className="h-5 w-5 text-green-600" />
              <h3 className="text-lg font-medium text-neutral-900">
                {formatCertificateType(`${type.toLowerCase()}_certificate`)}
              </h3>
              {required && <span className="text-red-500">*</span>}
            </div>

            <DocumentUpload
              poId={poId}
              documentType={`${type.toLowerCase()}_certificate`}
              onBehalfOf={onBehalfOf}
              required={required}
              onUploadComplete={handleUploadComplete}
              className="mb-4"
            />

            {/* Show uploaded certificates for this type */}
            {uploadedCertificates
              .filter(cert => cert.document_type === `${type.toLowerCase()}_certificate`)
              .map((certificate) => (
                <div key={certificate.id} className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <ShieldCheckIcon className="h-6 w-6 text-green-600 flex-shrink-0" />
                      <div>
                        <h4 className="font-medium text-green-900">
                          {certificate.original_file_name}
                        </h4>
                        <p className="text-sm text-green-700">
                          Uploaded {new Date(certificate.created_at).toLocaleDateString()}
                        </p>
                        {certificate.validation_status === 'pending' && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mt-1">
                            Validation Pending
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => setShowMetadataForm(certificate.id)}
                      className="text-sm text-green-600 hover:text-green-800 underline"
                    >
                      Add Details
                    </button>
                  </div>

                  {/* Metadata Form */}
                  {showMetadataForm === certificate.id && (
                    <div className="mt-4 p-4 bg-white border border-green-200 rounded-lg">
                      <h5 className="font-medium text-neutral-900 mb-3">Certificate Details</h5>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Certificate Number
                          </label>
                          <input
                            type="text"
                            value={certificateMetadata.certificateNumber || ''}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              certificateNumber: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                            placeholder="e.g., RSPO-1234567"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Certificate Type
                          </label>
                          <select
                            value={certificateMetadata.certificateType || ''}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              certificateType: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="">Select type...</option>
                            {getCertificateTypeOptions().map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            <CalendarIcon className="h-4 w-4 inline mr-1" />
                            Valid From
                          </label>
                          <input
                            type="date"
                            value={certificateMetadata.validFrom || ''}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              validFrom: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            <CalendarIcon className="h-4 w-4 inline mr-1" />
                            Valid Until
                          </label>
                          <input
                            type="date"
                            value={certificateMetadata.validUntil || ''}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              validUntil: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            <BuildingOfficeIcon className="h-4 w-4 inline mr-1" />
                            Certification Body
                          </label>
                          <input
                            type="text"
                            value={certificateMetadata.certificationBody || ''}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              certificationBody: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                            placeholder="e.g., Control Union"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Mill Name
                          </label>
                          <input
                            type="text"
                            value={certificateMetadata.millName || ''}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              millName: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                            placeholder="e.g., Makmur Selalu Mill"
                          />
                        </div>

                        {/* Enhanced Metadata Fields */}
                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Category
                          </label>
                          <select
                            value={certificateMetadata.category}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              category: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="">Select category...</option>
                            <option value="certification">Certification</option>
                            <option value="compliance">Compliance</option>
                            <option value="quality">Quality Assurance</option>
                            <option value="sustainability">Sustainability</option>
                            <option value="audit">Audit Report</option>
                            <option value="legal">Legal Documentation</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Priority Level
                          </label>
                          <select
                            value={certificateMetadata.priority}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              priority: e.target.value as 'low' | 'medium' | 'high'
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="low">Low Priority</option>
                            <option value="medium">Medium Priority</option>
                            <option value="high">High Priority</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Compliance Status
                          </label>
                          <select
                            value={certificateMetadata.complianceStatus}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              complianceStatus: e.target.value as 'pending' | 'approved' | 'rejected' | 'expired'
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="pending">Pending Review</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                            <option value="expired">Expired</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-1">
                            Expiry Date (Optional)
                          </label>
                          <input
                            type="date"
                            value={certificateMetadata.expiryDate}
                            onChange={(e) => setCertificateMetadata(prev => ({
                              ...prev,
                              expiryDate: e.target.value
                            }))}
                            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>
                      </div>

                      {/* Description Field */}
                      <div className="mt-4">
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={certificateMetadata.description}
                          onChange={(e) => setCertificateMetadata(prev => ({
                            ...prev,
                            description: e.target.value
                          }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          placeholder="Brief description of the document and its purpose..."
                        />
                      </div>

                      {/* Tags Field */}
                      <div className="mt-4">
                        <label className="block text-sm font-medium text-neutral-700 mb-1">
                          Tags (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={certificateMetadata.tags.join(', ')}
                          onChange={(e) => setCertificateMetadata(prev => ({
                            ...prev,
                            tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
                          }))}
                          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                          placeholder="e.g., RSPO, sustainable, certified, mill"
                        />
                        {certificateMetadata.tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {certificateMetadata.tags.map((tag, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex justify-end space-x-3 mt-4">
                        <button
                          onClick={() => setShowMetadataForm(null)}
                          className="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-md hover:bg-neutral-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleMetadataSubmit(certificate.id)}
                          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                        >
                          Save Details
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
};
