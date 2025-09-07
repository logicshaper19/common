/**
 * Document Requirements Service
 * Manages document requirements and validation for PO confirmation workflow
 */

export interface DocumentRequirement {
  type: string;
  name: string;
  required: boolean;
  description?: string;
  accepted_formats?: string[];
  validation_rules?: Record<string, any>;
}

export interface DocumentStatus {
  type: string;
  name: string;
  required: boolean;
  uploaded: boolean;
  valid: boolean;
  document_id?: string;
  uploaded_at?: string;
}

export interface DocumentValidationStatus {
  all_required_uploaded: boolean;
  missing_documents: Array<{
    type: string;
    name: string;
    description: string;
  }>;
  invalid_documents: Array<{
    type: string;
    name: string;
    reason: string;
  }>;
  document_status: DocumentStatus[];
}

export interface DocumentRequirementsResponse {
  purchase_order_id: string;
  interface_type: string;
  requirements: DocumentRequirement[];
  validation_status: DocumentValidationStatus;
  can_confirm: boolean;
}

export interface DocumentValidationResponse {
  purchase_order_id: string;
  validation_status: DocumentValidationStatus;
  can_confirm: boolean;
  last_updated: string;
}

class DocumentRequirementsService {
  private baseUrl = '/api/v1/purchase-orders';

  /**
   * Get document requirements for a purchase order
   */
  async getDocumentRequirements(poId: string): Promise<DocumentRequirementsResponse> {
    const response = await fetch(`${this.baseUrl}/${poId}/document-requirements`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get document requirements: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get current document validation status
   */
  async getDocumentValidationStatus(poId: string): Promise<DocumentValidationResponse> {
    const response = await fetch(`${this.baseUrl}/${poId}/document-validation-status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get document validation status: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Check if all required documents are uploaded and valid
   */
  async canConfirmPurchaseOrder(poId: string): Promise<boolean> {
    try {
      const status = await this.getDocumentValidationStatus(poId);
      return status.can_confirm;
    } catch (error) {
      console.error('Error checking confirmation eligibility:', error);
      return false;
    }
  }

  /**
   * Get missing document types
   */
  async getMissingDocuments(poId: string): Promise<DocumentRequirement[]> {
    try {
      const requirements = await this.getDocumentRequirements(poId);
      return requirements.validation_status.missing_documents.map(missing => {
        const requirement = requirements.requirements.find(req => req.type === missing.type);
        return requirement || {
          type: missing.type,
          name: missing.name,
          required: true,
          description: missing.description
        };
      });
    } catch (error) {
      console.error('Error getting missing documents:', error);
      return [];
    }
  }

  /**
   * Get progress percentage for document uploads
   */
  async getDocumentProgress(poId: string): Promise<{
    total: number;
    completed: number;
    percentage: number;
    required_completed: number;
    required_total: number;
  }> {
    try {
      const requirements = await this.getDocumentRequirements(poId);
      const statuses = requirements.validation_status.document_status;
      
      const total = statuses.length;
      const completed = statuses.filter(status => status.uploaded && status.valid).length;
      const requiredStatuses = statuses.filter(status => status.required);
      const requiredTotal = requiredStatuses.length;
      const requiredCompleted = requiredStatuses.filter(status => status.uploaded && status.valid).length;
      
      return {
        total,
        completed,
        percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
        required_completed: requiredCompleted,
        required_total: requiredTotal
      };
    } catch (error) {
      console.error('Error calculating document progress:', error);
      return {
        total: 0,
        completed: 0,
        percentage: 0,
        required_completed: 0,
        required_total: 0
      };
    }
  }

  /**
   * Format document requirement for display
   */
  formatRequirement(requirement: DocumentRequirement): {
    title: string;
    description: string;
    formats: string;
    badge: 'required' | 'optional';
  } {
    return {
      title: requirement.name,
      description: requirement.description || `Upload ${requirement.name.toLowerCase()}`,
      formats: requirement.accepted_formats?.join(', ').toUpperCase() || 'PDF, JPG, PNG',
      badge: requirement.required ? 'required' : 'optional'
    };
  }

  /**
   * Get status color for document status
   */
  getStatusColor(status: DocumentStatus): 'success' | 'warning' | 'error' | 'neutral' {
    if (status.uploaded && status.valid) {
      return 'success';
    } else if (status.uploaded && !status.valid) {
      return 'error';
    } else if (status.required) {
      return 'warning';
    } else {
      return 'neutral';
    }
  }

  /**
   * Get status text for document status
   */
  getStatusText(status: DocumentStatus): string {
    if (status.uploaded && status.valid) {
      return 'Uploaded & Valid';
    } else if (status.uploaded && !status.valid) {
      return 'Uploaded - Invalid';
    } else if (status.required) {
      return 'Required - Missing';
    } else {
      return 'Optional - Not Uploaded';
    }
  }
}

export const documentRequirementsService = new DocumentRequirementsService();
