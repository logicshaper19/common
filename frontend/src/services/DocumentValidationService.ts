/**
 * Document Validation Service
 * Following the critical issue fix: Implement missing frontend service
 */
import { apiClient } from '../lib/api';

export interface DocumentRequirement {
  type: string;
  name: string;
  description: string;
  is_required: boolean;
  sector_specific: boolean;
  tier_applicability?: number[];
  file_types_allowed: string[];
  max_file_size_mb: number;
  validation_rules?: {
    [key: string]: any;
  };
}

export interface DocumentValidationResult {
  is_valid: boolean;
  document_type: string;
  validation_status: 'valid' | 'invalid' | 'pending';
  errors: string[];
  warnings: string[];
  file_info: {
    name: string;
    size: number;
    type: string;
  };
}

export interface DocumentRequirementsResponse {
  requirements: DocumentRequirement[];
  interface_type: string;
  sector_id: string;
  tier_level: number;
  total_required: number;
  total_optional: number;
}

export interface DocumentValidationStatusResponse {
  all_required_uploaded: boolean;
  missing_documents: Array<{
    type: string;
    name: string;
    description: string;
  }>;
  document_status: Array<{
    type: string;
    name: string;
    is_required: boolean;
    is_uploaded: boolean;
    validation_status?: string;
    document_id?: string;
    uploaded_at?: string;
  }>;
  upload_progress: {
    required_uploaded: number;
    total_required: number;
    optional_uploaded: number;
    total_optional: number;
  };
}

class DocumentValidationService {
  private baseUrl = '/api/v1';

  /**
   * Get document requirements for a sector and tier level
   */
  static getRequirements(sectorId: string, tierLevel: number): DocumentRequirement[] {
    // Static requirements based on sector and tier
    // This is a fallback implementation - in production, this would come from the API
    const baseRequirements: DocumentRequirement[] = [
      {
        type: 'company_registration',
        name: 'Company Registration Certificate',
        description: 'Official company registration document',
        is_required: true,
        sector_specific: false,
        file_types_allowed: ['pdf', 'jpg', 'png'],
        max_file_size_mb: 10
      },
      {
        type: 'tax_certificate',
        name: 'Tax Registration Certificate',
        description: 'Valid tax registration certificate',
        is_required: true,
        sector_specific: false,
        file_types_allowed: ['pdf', 'jpg', 'png'],
        max_file_size_mb: 10
      }
    ];

    // Add sector-specific requirements
    if (sectorId === 'palm_oil') {
      baseRequirements.push(
        {
          type: 'rspo_certificate',
          name: 'RSPO Certificate',
          description: 'Valid RSPO certification document',
          is_required: false,
          sector_specific: true,
          tier_applicability: [4, 5], // Mills and plantations
          file_types_allowed: ['pdf'],
          max_file_size_mb: 5
        },
        {
          type: 'eudr_due_diligence_statement',
          name: 'EUDR Due Diligence Statement',
          description: 'EU Deforestation Regulation compliance statement',
          is_required: true,
          sector_specific: true,
          file_types_allowed: ['pdf'],
          max_file_size_mb: 5
        }
      );
    }

    if (sectorId === 'apparel') {
      baseRequirements.push(
        {
          type: 'bci_certificate',
          name: 'Better Cotton Initiative Certificate',
          description: 'Valid BCI certification',
          is_required: false,
          sector_specific: true,
          file_types_allowed: ['pdf'],
          max_file_size_mb: 5
        },
        {
          type: 'social_compliance_audit',
          name: 'Social Compliance Audit Report',
          description: 'Recent social compliance audit report',
          is_required: true,
          sector_specific: true,
          file_types_allowed: ['pdf'],
          max_file_size_mb: 10
        }
      );
    }

    // Filter by tier applicability
    return baseRequirements.filter(req => {
      if (!req.tier_applicability) return true;
      return req.tier_applicability.includes(tierLevel);
    });
  }

  /**
   * Validate documents against requirements
   */
  static validateDocuments(requirements: DocumentRequirement[], documents: any[]): {
    isValid: boolean;
    missingRequired: DocumentRequirement[];
    validDocuments: any[];
    invalidDocuments: any[];
  } {
    const requiredTypes = requirements
      .filter(req => req.is_required)
      .map(req => req.type);

    const uploadedTypes = documents.map(doc => doc.document_type);
    
    const missingRequired = requirements.filter(req => 
      req.is_required && !uploadedTypes.includes(req.type)
    );

    const validDocuments = documents.filter(doc => 
      doc.validation_status === 'valid'
    );

    const invalidDocuments = documents.filter(doc => 
      doc.validation_status === 'invalid'
    );

    const isValid = missingRequired.length === 0 && invalidDocuments.length === 0;

    return {
      isValid,
      missingRequired,
      validDocuments,
      invalidDocuments
    };
  }

  /**
   * Get document requirements from API
   */
  async getDocumentRequirements(poId: string): Promise<DocumentRequirementsResponse> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/confirmation/document-requirements`, {
        params: { po_id: poId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching document requirements:', error);
      throw error;
    }
  }

  /**
   * Get document validation status from API
   */
  async getDocumentValidationStatus(poId: string): Promise<DocumentValidationStatusResponse> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/confirmation/document-validation-status`, {
        params: { po_id: poId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching document validation status:', error);
      throw error;
    }
  }

  /**
   * Validate file before upload
   */
  static validateFileBeforeUpload(file: File, requirement: DocumentRequirement): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > requirement.max_file_size_mb) {
      errors.push(`File size (${fileSizeMB.toFixed(1)}MB) exceeds maximum allowed size (${requirement.max_file_size_mb}MB)`);
    }

    // Check file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (fileExtension && !requirement.file_types_allowed.includes(fileExtension)) {
      errors.push(`File type .${fileExtension} is not allowed. Allowed types: ${requirement.file_types_allowed.join(', ')}`);
    }

    // Check file name
    if (file.name.length > 255) {
      errors.push('File name is too long (maximum 255 characters)');
    }

    // Warnings for best practices
    if (fileSizeMB > requirement.max_file_size_mb * 0.8) {
      warnings.push('File size is close to the maximum limit');
    }

    if (file.name.includes(' ')) {
      warnings.push('Consider using underscores instead of spaces in file names');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Get upload progress summary
   */
  static getUploadProgress(requirements: DocumentRequirement[], documents: any[]): {
    requiredUploaded: number;
    totalRequired: number;
    optionalUploaded: number;
    totalOptional: number;
    overallProgress: number;
  } {
    const requiredRequirements = requirements.filter(req => req.is_required);
    const optionalRequirements = requirements.filter(req => !req.is_required);

    const uploadedTypes = documents
      .filter(doc => doc.validation_status === 'valid')
      .map(doc => doc.document_type);

    const requiredUploaded = requiredRequirements.filter(req => 
      uploadedTypes.includes(req.type)
    ).length;

    const optionalUploaded = optionalRequirements.filter(req => 
      uploadedTypes.includes(req.type)
    ).length;

    const totalRequired = requiredRequirements.length;
    const totalOptional = optionalRequirements.length;

    // Calculate overall progress (required documents weighted more heavily)
    const requiredProgress = totalRequired > 0 ? (requiredUploaded / totalRequired) : 1;
    const optionalProgress = totalOptional > 0 ? (optionalUploaded / totalOptional) : 1;
    
    // 80% weight for required, 20% for optional
    const overallProgress = (requiredProgress * 0.8) + (optionalProgress * 0.2);

    return {
      requiredUploaded,
      totalRequired,
      optionalUploaded,
      totalOptional,
      overallProgress: Math.round(overallProgress * 100)
    };
  }

  /**
   * Format file size for display
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get document type display name
   */
  static getDocumentTypeDisplayName(type: string): string {
    const displayNames: { [key: string]: string } = {
      'company_registration': 'Company Registration',
      'tax_certificate': 'Tax Certificate',
      'rspo_certificate': 'RSPO Certificate',
      'eudr_due_diligence_statement': 'EUDR Due Diligence Statement',
      'bci_certificate': 'BCI Certificate',
      'social_compliance_audit': 'Social Compliance Audit',
      'legal_harvest_permit': 'Legal Harvest Permit',
      'catchment_area_polygon': 'Catchment Area Polygon'
    };

    return displayNames[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}

export default DocumentValidationService;
