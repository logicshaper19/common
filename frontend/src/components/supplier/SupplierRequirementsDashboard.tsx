/**
 * Supplier Requirements Dashboard
 * Interface for suppliers to view and upload their tier-specific requirements
 */
import React, { useState, useEffect } from 'react';
import {
  DocumentIcon,
  MapPinIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CloudArrowUpIcon,
  InformationCircleIcon,
  BuildingOfficeIcon,
  TagIcon,
  StarIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import AnalyticsCard from '../ui/AnalyticsCard';
import { cn } from '../../lib/utils';

interface TierRequirement {
  name: string;
  type: 'DOCUMENT' | 'COORDINATE' | 'CERTIFICATION' | 'DATA_FIELD';
  description: string;
  is_mandatory: boolean;
  validation_rules: {
    file_types?: string[];
    max_file_size_mb?: number;
    coordinate_precision?: number;
    required_fields?: string[];
  };
}

interface CompanyProfile {
  company_type: string;
  sector_id: string;
  tier_level: number;
  transparency_weight: number;
  base_requirements: TierRequirement[];
  sector_specific_requirements: TierRequirement[];
}

interface SupplierRequirementsDashboardProps {
  companyType: string;
  sectorId: string;
  className?: string;
}

const SupplierRequirementsDashboard: React.FC<SupplierRequirementsDashboardProps> = ({
  companyType,
  sectorId,
  className,
}) => {
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, File>>({});
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  useEffect(() => {
    fetchRequirements();
  }, [companyType, sectorId]);

  const fetchRequirements = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/tier-requirements/profile/${companyType}/${sectorId}`);
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
      }
    } catch (error) {
      console.error('Failed to fetch requirements:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (requirementName: string, file: File) => {
    setUploadedFiles(prev => ({ ...prev, [requirementName]: file }));
    
    // Simulate upload progress
    setUploadProgress(prev => ({ ...prev, [requirementName]: 0 }));
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        const current = prev[requirementName] || 0;
        if (current >= 100) {
          clearInterval(interval);
          return prev;
        }
        return { ...prev, [requirementName]: current + 10 };
      });
    }, 100);
  };

  const getRequirementIcon = (type: string) => {
    switch (type) {
      case 'DOCUMENT':
      case 'CERTIFICATION':
        return DocumentIcon;
      case 'COORDINATE':
        return MapPinIcon;
      default:
        return InformationCircleIcon;
    }
  };

  const getRequirementStatus = (requirementName: string) => {
    if (uploadedFiles[requirementName]) {
      const progress = uploadProgress[requirementName] || 0;
      if (progress >= 100) {
        return 'completed';
      }
      return 'uploading';
    }
    return 'pending';
  };

  const renderRequirement = (requirement: TierRequirement) => {
    const Icon = getRequirementIcon(requirement.type);
    const status = getRequirementStatus(requirement.name);
    const progress = uploadProgress[requirement.name] || 0;

    return (
      <div key={requirement.name} className="border border-gray-200 rounded-lg p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start space-x-3">
            <Icon className="h-5 w-5 text-gray-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-900">{requirement.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{requirement.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge
              variant={requirement.is_mandatory ? 'primary' : 'secondary'}
              size="sm"
            >
              {requirement.is_mandatory ? 'Required' : 'Optional'}
            </Badge>
            {status === 'completed' && (
              <CheckCircleIcon className="h-5 w-5 text-green-600" />
            )}
            {status === 'pending' && requirement.is_mandatory && (
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
            )}
          </div>
        </div>

        {/* Validation Rules */}
        {requirement.validation_rules && (
          <div className="mb-3 text-xs text-gray-500">
            {requirement.validation_rules.file_types && (
              <span>Accepted: {requirement.validation_rules.file_types.join(', ')} • </span>
            )}
            {requirement.validation_rules.max_file_size_mb && (
              <span>Max size: {requirement.validation_rules.max_file_size_mb}MB • </span>
            )}
            {requirement.validation_rules.coordinate_precision && (
              <span>Precision: {requirement.validation_rules.coordinate_precision}° • </span>
            )}
          </div>
        )}

        {/* Upload Area */}
        <div className="space-y-2">
          {status === 'pending' && (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
              <CloudArrowUpIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-2">
                {requirement.type === 'COORDINATE' 
                  ? 'Upload coordinate file or enter coordinates manually'
                  : 'Click to upload or drag and drop'
                }
              </p>
              <input
                type="file"
                accept={requirement.validation_rules.file_types?.map(type => `.${type}`).join(',')}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    handleFileUpload(requirement.name, file);
                  }
                }}
                className="hidden"
                id={`upload-${requirement.name}`}
              />
              <label
                htmlFor={`upload-${requirement.name}`}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
              >
                Choose File
              </label>
            </div>
          )}

          {status === 'uploading' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Uploading {uploadedFiles[requirement.name]?.name}</span>
                <span className="text-gray-600">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {status === 'completed' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="h-4 w-4 text-green-600" />
                <span className="text-sm text-green-800">
                  {uploadedFiles[requirement.name]?.name} uploaded successfully
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-3">
              <div className="h-20 bg-gray-200 rounded"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!profile) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Requirements Not Found</h3>
            <p className="text-gray-600">
              Unable to load requirements for {companyType} in {sectorId} sector.
            </p>
          </div>
        </CardBody>
      </Card>
    );
  }

  const allRequirements = [...profile.base_requirements, ...profile.sector_specific_requirements];
  const mandatoryRequirements = allRequirements.filter(req => req.is_mandatory);
  const optionalRequirements = allRequirements.filter(req => !req.is_mandatory);
  const completedCount = allRequirements.filter(req => getRequirementStatus(req.name) === 'completed').length;
  const completionPercentage = Math.round((completedCount / allRequirements.length) * 100);

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Supplier Requirements</h2>
              <p className="text-sm text-gray-600 mt-1">
                Complete your tier-specific requirements for transparency and compliance
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">{completionPercentage}%</div>
              <div className="text-xs text-gray-500">Complete</div>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <AnalyticsCard
              name="Company Type"
              value={profile.company_type}
              icon={BuildingOfficeIcon}
              size="sm"
              showChange={false}
            />
            <AnalyticsCard
              name="Sector"
              value={profile.sector_id.replace('_', ' ')}
              icon={TagIcon}
              size="sm"
              showChange={false}
            />
            <AnalyticsCard
              name="Tier Level"
              value={`Tier ${profile.tier_level}`}
              icon={StarIcon}
              size="sm"
              showChange={false}
            />
            <AnalyticsCard
              name="Transparency Weight"
              value={`${(profile.transparency_weight * 100).toFixed(0)}%`}
              icon={ChartBarIcon}
              size="sm"
              showChange={false}
            />
          </div>

          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </CardBody>
      </Card>

      {/* Mandatory Requirements */}
      {mandatoryRequirements.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900">Mandatory Requirements</h3>
            <p className="text-sm text-gray-600">These requirements must be completed for compliance</p>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {mandatoryRequirements.map(renderRequirement)}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Optional Requirements */}
      {optionalRequirements.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900">Optional Requirements</h3>
            <p className="text-sm text-gray-600">Additional requirements to improve transparency score</p>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {optionalRequirements.map(renderRequirement)}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

export default SupplierRequirementsDashboard;
