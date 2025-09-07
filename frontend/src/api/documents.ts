/**
 * API client for document management
 */
import { apiClient } from '../lib/api';

export interface Document {
  id: string;
  po_id?: string;
  company_id: string;
  uploaded_by_user_id: string;
  document_type: string;
  file_name: string;
  original_file_name: string;
  file_size?: number;
  mime_type?: string;
  storage_url: string;
  storage_provider: string;
  storage_key?: string;
  validation_status: 'pending' | 'valid' | 'invalid' | 'expired';
  validation_errors?: Record<string, any>;
  validation_metadata?: Record<string, any>;
  is_proxy_upload: boolean;
  on_behalf_of_company_id?: string;
  proxy_authorization_id?: string;
  document_category?: string;
  expiry_date?: string;
  issue_date?: string;
  issuing_authority?: string;
  compliance_regulations?: string[];
  tier_level?: number;
  sector_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ProxyRelationship {
  id: string;
  proxy_company_id: string;
  originator_company_id: string;
  authorized_by_user_id: string;
  relationship_type: string;
  authorized_permissions: string[];
  document_types_allowed?: string[];
  status: 'pending' | 'active' | 'suspended' | 'revoked';
  authorized_at?: string;
  expires_at?: string;
  revoked_at?: string;
  revoked_by_user_id?: string;
  sector_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateProxyRelationshipRequest {
  proxy_company_id: string;
  originator_company_id: string;
  relationship_type?: string;
  authorized_permissions: string[];
  document_types_allowed?: string[];
  sector_id?: string;
  notes?: string;
  expires_at?: string;
}

export interface DocumentsApiParams {
  po_id?: string;
  document_type?: string;
  company_id?: string;
  limit?: number;
  offset?: number;
}

class DocumentsApi {
  /**
   * Upload a document
   */
  async uploadDocument(formData: FormData): Promise<Document> {
    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Get documents with optional filters
   */
  async getDocuments(params: DocumentsApiParams = {}): Promise<DocumentListResponse> {
    const response = await apiClient.get('/documents/', { params });
    return response.data;
  }

  /**
   * Get a specific document by ID
   */
  async getDocument(documentId: string): Promise<Document> {
    const response = await apiClient.get(`/documents/${documentId}`);
    return response.data;
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/documents/${documentId}`);
    return response.data;
  }

  /**
   * Create a proxy relationship
   */
  async createProxyRelationship(data: CreateProxyRelationshipRequest): Promise<ProxyRelationship> {
    const response = await apiClient.post('/documents/proxy/relationships', data);
    return response.data;
  }

  /**
   * Get proxy relationships for current user's company
   */
  async getProxyRelationships(status?: string): Promise<ProxyRelationship[]> {
    const params = status ? { status } : {};
    const response = await apiClient.get('/documents/proxy/relationships', { params });
    return response.data;
  }

  /**
   * Update proxy relationship status
   */
  async updateProxyRelationshipStatus(
    relationshipId: string, 
    status: 'active' | 'suspended' | 'revoked'
  ): Promise<{ message: string }> {
    const formData = new FormData();
    formData.append('status', status);
    
    const response = await apiClient.put(
      `/documents/proxy/relationships/${relationshipId}/status`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Get documents for a specific PO
   */
  async getDocumentsForPO(poId: string): Promise<Document[]> {
    const response = await this.getDocuments({ po_id: poId });
    return response.documents;
  }

  /**
   * Get documents by type
   */
  async getDocumentsByType(documentType: string): Promise<Document[]> {
    const response = await this.getDocuments({ document_type: documentType });
    return response.documents;
  }

  /**
   * Check if user can upload as proxy for a company
   */
  async canUploadAsProxy(originatorCompanyId: string): Promise<boolean> {
    try {
      const relationships = await this.getProxyRelationships('active');
      return relationships.some(rel => 
        rel.originator_company_id === originatorCompanyId &&
        rel.authorized_permissions.includes('upload_documents')
      );
    } catch (error) {
      console.error('Error checking proxy permissions:', error);
      return false;
    }
  }

  /**
   * Get authorized mills for cooperative (proxy relationships where current company is proxy)
   */
  async getAuthorizedMills(): Promise<ProxyRelationship[]> {
    const relationships = await this.getProxyRelationships('active');
    return relationships.filter(rel => 
      rel.authorized_permissions.includes('upload_documents') ||
      rel.authorized_permissions.includes('upload_certificates')
    );
  }

  /**
   * Get document type information
   */
  getDocumentTypeInfo() {
    return {
      rspo_certificate: {
        label: 'RSPO Certificate',
        category: 'certificate',
        allowed_mime_types: ['application/pdf', 'image/jpeg', 'image/png'],
        max_size_mb: 10,
        description: 'RSPO certification documents'
      },
      catchment_polygon: {
        label: 'Catchment Area Polygon',
        category: 'map',
        allowed_mime_types: ['application/json', 'application/geo+json', 'application/zip'],
        max_size_mb: 5,
        description: 'Mill catchment area polygon data'
      },
      harvest_record: {
        label: 'Harvest Record',
        category: 'report',
        allowed_mime_types: ['application/pdf', 'application/vnd.ms-excel', 'text/csv'],
        max_size_mb: 10,
        description: 'Harvest records and production data'
      },
      audit_report: {
        label: 'Audit Report',
        category: 'audit',
        allowed_mime_types: ['application/pdf'],
        max_size_mb: 20,
        description: 'Third-party audit reports'
      },
      certification: {
        label: 'Certification',
        category: 'certificate',
        allowed_mime_types: ['application/pdf', 'image/jpeg', 'image/png'],
        max_size_mb: 10,
        description: 'General certification documents'
      },
      map_data: {
        label: 'Map Data',
        category: 'map',
        allowed_mime_types: ['application/json', 'application/geo+json', 'image/png', 'image/jpeg'],
        max_size_mb: 15,
        description: 'Geographic and mapping data'
      }
    };
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File, documentType: string): { valid: boolean; error?: string } {
    const typeInfo = this.getDocumentTypeInfo()[documentType as keyof ReturnType<typeof this.getDocumentTypeInfo>];
    
    if (!typeInfo) {
      return { valid: false, error: 'Invalid document type' };
    }

    // Check file size
    const maxSizeBytes = typeInfo.max_size_mb * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return { 
        valid: false, 
        error: `File too large. Maximum size is ${typeInfo.max_size_mb}MB` 
      };
    }

    // Check MIME type
    if (!typeInfo.allowed_mime_types.includes(file.type)) {
      return { 
        valid: false, 
        error: `Invalid file type. Allowed types: ${typeInfo.allowed_mime_types.join(', ')}` 
      };
    }

    return { valid: true };
  }
}

export const documentsApi = new DocumentsApi();
