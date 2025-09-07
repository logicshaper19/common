/**
 * Document Validation Service
 * Handles validation logic for document requirements in confirmation workflow
 */
import { DocumentRequirement } from '../components/documents/DocumentUploadProgress';
import { Document } from '../api/documents';

export interface ValidationResult {
  isValid: boolean;
  missingRequired: DocumentRequirement[];
  errors: string[];
  warnings: string[];
}

export interface SectorDocumentRequirements {
  [sectorId: string]: {
    [tierLevel: number]: DocumentRequirement[];
  };
}

// Define document requirements by sector and tier
export const SECTOR_DOCUMENT_REQUIREMENTS: SectorDocumentRequirements = {
  palm_oil: {
    4: [ // Mill (Tier 4 - Originator)
      {
        type: 'rspo_certificate',
        name: 'RSPO Certificate',
        required: true,
        description: 'Valid RSPO certification for sustainable palm oil production',
        acceptedFormats: ['PDF', 'JPG', 'PNG']
      },
      {
        type: 'catchment_polygon',
        name: 'Catchment Area Polygon',
        required: true,
        description: 'Geographic boundaries of the mill\'s catchment area',
        acceptedFormats: ['KML', 'SHP', 'GeoJSON', 'PDF']
      },
      {
        type: 'harvest_record',
        name: 'Harvest Records',
        required: false,
        description: 'Recent harvest documentation and quality records',
        acceptedFormats: ['PDF', 'XLS', 'XLSX', 'CSV']
      },
      {
        type: 'audit_report',
        name: 'Third-Party Audit Report',
        required: false,
        description: 'Independent sustainability audit report',
        acceptedFormats: ['PDF']
      }
    ],
    5: [ // Cooperative (Tier 5)
      {
        type: 'cooperative_license',
        name: 'Cooperative License',
        required: true,
        description: 'Valid cooperative operating license',
        acceptedFormats: ['PDF', 'JPG', 'PNG']
      },
      {
        type: 'member_list',
        name: 'Member Farmer List',
        required: true,
        description: 'List of member farmers and their farm details',
        acceptedFormats: ['PDF', 'XLS', 'XLSX', 'CSV']
      }
    ]
  },
  apparel: {
    6: [ // Cotton Farmer (Tier 6 - Originator)
      {
        type: 'bci_certificate',
        name: 'BCI Certificate',
        required: true,
        description: 'Better Cotton Initiative certification',
        acceptedFormats: ['PDF', 'JPG', 'PNG']
      },
      {
        type: 'farm_registration',
        name: 'Farm Registration',
        required: true,
        description: 'Official farm registration documents',
        acceptedFormats: ['PDF', 'JPG', 'PNG']
      },
      {
        type: 'harvest_record',
        name: 'Harvest Records',
        required: false,
        description: 'Cotton harvest documentation and quality records',
        acceptedFormats: ['PDF', 'XLS', 'XLSX', 'CSV']
      }
    ],
    5: [ // Ginner (Tier 5)
      {
        type: 'processing_license',
        name: 'Processing License',
        required: true,
        description: 'Valid cotton processing/ginning license',
        acceptedFormats: ['PDF', 'JPG', 'PNG']
      },
      {
        type: 'quality_certificate',
        name: 'Quality Certificate',
        required: false,
        description: 'Cotton quality and grade certification',
        acceptedFormats: ['PDF']
      }
    ]
  },
  electronics: {
    5: [ // Miner/Smelter (Tier 5 - Originator)
      {
        type: 'mining_license',
        name: 'Mining License',
        required: true,
        description: 'Valid mining operation license',
        acceptedFormats: ['PDF', 'JPG', 'PNG']
      },
      {
        type: 'conflict_minerals_report',
        name: 'Conflict Minerals Report',
        required: true,
        description: 'OECD due diligence report for conflict minerals',
        acceptedFormats: ['PDF']
      },
      {
        type: 'environmental_permit',
        name: 'Environmental Permit',
        required: true,
        description: 'Environmental impact assessment and permits',
        acceptedFormats: ['PDF']
      },
      {
        type: 'audit_report',
        name: 'Third-Party Audit Report',
        required: false,
        description: 'Independent responsible sourcing audit report',
        acceptedFormats: ['PDF']
      }
    ]
  }
};

export class DocumentValidationService {
  /**
   * Get document requirements for a specific sector and tier
   */
  static getRequirements(sectorId: string, tierLevel: number): DocumentRequirement[] {
    const sectorRequirements = SECTOR_DOCUMENT_REQUIREMENTS[sectorId];
    if (!sectorRequirements) {
      return [];
    }

    return sectorRequirements[tierLevel] || [];
  }

  /**
   * Validate documents against requirements
   */
  static validateDocuments(
    requirements: DocumentRequirement[],
    uploadedDocuments: Document[]
  ): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const missingRequired: DocumentRequirement[] = [];

    // Check each requirement
    for (const requirement of requirements) {
      const matchingDoc = uploadedDocuments.find(
        doc => doc.document_type === requirement.type
      );

      if (!matchingDoc) {
        if (requirement.required) {
          missingRequired.push(requirement);
          errors.push(`Missing required document: ${requirement.name}`);
        } else {
          warnings.push(`Optional document not uploaded: ${requirement.name}`);
        }
      } else {
        // Validate file format if specified
        if (requirement.acceptedFormats) {
          const fileExtension = this.getFileExtension(matchingDoc.original_file_name);
          const isValidFormat = requirement.acceptedFormats.some(
            format => format.toLowerCase() === fileExtension.toLowerCase()
          );

          if (!isValidFormat) {
            errors.push(
              `Invalid file format for ${requirement.name}. ` +
              `Expected: ${requirement.acceptedFormats.join(', ')}, ` +
              `Got: ${fileExtension}`
            );
          }
        }

        // Additional validation based on document type
        this.validateSpecificDocument(requirement, matchingDoc, errors, warnings);
      }
    }

    return {
      isValid: errors.length === 0 && missingRequired.length === 0,
      missingRequired,
      errors,
      warnings
    };
  }

  /**
   * Check if confirmation can proceed based on document validation
   */
  static canProceedWithConfirmation(
    requirements: DocumentRequirement[],
    uploadedDocuments: Document[]
  ): { canProceed: boolean; reason?: string } {
    const validation = this.validateDocuments(requirements, uploadedDocuments);

    if (!validation.isValid) {
      if (validation.missingRequired.length > 0) {
        return {
          canProceed: false,
          reason: `Missing required documents: ${validation.missingRequired.map(r => r.name).join(', ')}`
        };
      }

      if (validation.errors.length > 0) {
        return {
          canProceed: false,
          reason: `Document validation errors: ${validation.errors.join('; ')}`
        };
      }
    }

    return { canProceed: true };
  }

  /**
   * Get file extension from filename
   */
  private static getFileExtension(filename: string): string {
    const lastDotIndex = filename.lastIndexOf('.');
    return lastDotIndex !== -1 ? filename.substring(lastDotIndex + 1) : '';
  }

  /**
   * Perform document-specific validation
   */
  private static validateSpecificDocument(
    requirement: DocumentRequirement,
    document: Document,
    errors: string[],
    warnings: string[]
  ): void {
    // Add specific validation logic based on document type
    switch (requirement.type) {
      case 'rspo_certificate':
        this.validateRSPOCertificate(document, errors, warnings);
        break;
      case 'bci_certificate':
        this.validateBCICertificate(document, errors, warnings);
        break;
      case 'conflict_minerals_report':
        this.validateConflictMineralsReport(document, errors, warnings);
        break;
      // Add more specific validations as needed
    }
  }

  /**
   * Validate RSPO certificate
   */
  private static validateRSPOCertificate(
    document: Document,
    errors: string[],
    warnings: string[]
  ): void {
    // Check if document has RSPO-specific metadata
    if (document.validation_metadata?.certificate_type !== 'RSPO') {
      warnings.push('Document may not be a valid RSPO certificate');
    }

    // Check expiry date if available
    if (document.validation_metadata?.expiry_date) {
      const expiryDate = new Date(document.validation_metadata.expiry_date);
      const now = new Date();
      
      if (expiryDate < now) {
        errors.push('RSPO certificate has expired');
      } else if (expiryDate.getTime() - now.getTime() < 30 * 24 * 60 * 60 * 1000) {
        warnings.push('RSPO certificate expires within 30 days');
      }
    }
  }

  /**
   * Validate BCI certificate
   */
  private static validateBCICertificate(
    document: Document,
    errors: string[],
    warnings: string[]
  ): void {
    // Similar validation logic for BCI certificates
    if (document.validation_metadata?.certificate_type !== 'BCI') {
      warnings.push('Document may not be a valid BCI certificate');
    }
  }

  /**
   * Validate conflict minerals report
   */
  private static validateConflictMineralsReport(
    document: Document,
    errors: string[],
    warnings: string[]
  ): void {
    // Check if it's a proper OECD due diligence report
    if (!document.validation_metadata?.report_type ||
        !document.validation_metadata.report_type.includes('OECD')) {
      warnings.push('Document may not be a valid OECD due diligence report');
    }
  }
}
