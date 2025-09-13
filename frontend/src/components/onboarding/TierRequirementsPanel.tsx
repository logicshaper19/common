/**
 * Tier Requirements Panel Component
 * Displays tier-specific requirements for company types during supplier addition
 */
import React, { useState, useEffect } from 'react';
import {
  DocumentTextIcon,
  MapPinIcon,
  ShieldCheckIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { cn } from '../../lib/utils';

interface TierRequirement {
  type: string;
  name: string;
  description: string;
  is_mandatory: boolean;
  validation_rules: Record<string, any>;
  help_text?: string;
}

interface CompanyTypeProfile {
  company_type: string;
  tier_level: number;
  sector_id: string;
  transparency_weight: number;
  base_requirements: TierRequirement[];
  sector_specific_requirements: TierRequirement[];
}

interface TierRequirementsPanelProps {
  companyType: string;
  sectorId: string;
  onRequirementsLoaded?: (profile: CompanyTypeProfile) => void;
  className?: string;
}

const TierRequirementsPanel: React.FC<TierRequirementsPanelProps> = ({
  companyType,
  sectorId,
  onRequirementsLoaded,
  className
}) => {
  const [profile, setProfile] = useState<CompanyTypeProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedRequirement, setExpandedRequirement] = useState<string | null>(null);

  useEffect(() => {
    if (companyType && sectorId) {
      fetchTierRequirements();
    }
  }, [companyType, sectorId]);

  const fetchTierRequirements = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/tier-requirements/profile/${companyType}/${sectorId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch tier requirements');
      }

      const data = await response.json();
      setProfile(data);
      onRequirementsLoaded?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getRequirementIcon = (type: string) => {
    switch (type) {
      case 'document':
        return DocumentTextIcon;
      case 'coordinate':
        return MapPinIcon;
      case 'certification':
        return ShieldCheckIcon;
      default:
        return InformationCircleIcon;
    }
  };

  const getRequirementTypeColor = (type: string) => {
    switch (type) {
      case 'document':
        return 'blue';
      case 'coordinate':
        return 'green';
      case 'certification':
        return 'purple';
      default:
        return 'gray';
    }
  };

  const renderRequirement = (requirement: TierRequirement, index: number) => {
    const Icon = getRequirementIcon(requirement.type);
    const isExpanded = expandedRequirement === `${requirement.type}-${index}`;

    return (
      <div
        key={`${requirement.type}-${index}`}
        className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <Icon className="h-5 w-5 text-gray-500 mt-0.5" />
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h4 className="font-medium text-gray-900">{requirement.name}</h4>
                <Badge
                  variant={requirement.is_mandatory ? 'primary' : 'secondary'}
                  size="sm"
                >
                  {requirement.is_mandatory ? 'Required' : 'Optional'}
                </Badge>
                <Badge
                  variant="secondary"
                  size="sm"
                  className={cn(
                    'capitalize',
                    getRequirementTypeColor(requirement.type) === 'blue' && 'border-blue-200 text-blue-700',
                    getRequirementTypeColor(requirement.type) === 'green' && 'border-green-200 text-green-700',
                    getRequirementTypeColor(requirement.type) === 'purple' && 'border-purple-200 text-purple-700'
                  )}
                >
                  {requirement.type}
                </Badge>
              </div>
              <p className="text-sm text-gray-600 mt-1">{requirement.description}</p>
              
              {requirement.help_text && (
                <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
                  <div className="flex items-start space-x-2">
                    <InformationCircleIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>{requirement.help_text}</span>
                  </div>
                </div>
              )}

              {isExpanded && (
                <div className="mt-3 p-3 bg-gray-50 rounded border">
                  <h5 className="font-medium text-gray-900 mb-2">Validation Rules:</h5>
                  <div className="space-y-1 text-sm text-gray-600">
                    {Object.entries(requirement.validation_rules).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-mono text-xs">
                          {Array.isArray(value) ? value.join(', ') : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpandedRequirement(
              isExpanded ? null : `${requirement.type}-${index}`
            )}
            className="ml-2"
          >
            {isExpanded ? 'Less' : 'Details'}
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
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading tier requirements...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="flex items-center space-x-3 text-red-600 py-4">
            <ExclamationTriangleIcon className="h-6 w-6" />
            <div>
              <p className="font-medium">Failed to load requirements</p>
              <p className="text-sm text-red-500">{error}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTierRequirements}
            className="mt-3"
          >
            Retry
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (!profile) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-8 text-gray-500">
            <InformationCircleIcon className="h-12 w-12 mx-auto mb-3 text-gray-400" />
            <p>Select a company type and sector to view requirements</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  const allRequirements = [...profile.base_requirements, ...profile.sector_specific_requirements];
  const mandatoryCount = allRequirements.filter(req => req.is_mandatory).length;
  const optionalCount = allRequirements.length - mandatoryCount;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Tier {profile.tier_level} Requirements
            </h3>
            <p className="text-sm text-gray-600 capitalize">
              {profile.company_type} in {profile.sector_id.replace('_', ' ')} sector
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="secondary" size="sm">
              Transparency Weight: {(profile.transparency_weight * 100).toFixed(0)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardBody>
        <div className="mb-6">
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span>{mandatoryCount} Required</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span>{optionalCount} Optional</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircleIcon className="h-4 w-4 text-green-500" />
              <span>{allRequirements.length} Total</span>
            </div>
          </div>
        </div>

        {profile.base_requirements.length > 0 && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Base Requirements</h4>
            <div className="space-y-3">
              {profile.base_requirements.map((req, index) => renderRequirement(req, index))}
            </div>
          </div>
        )}

        {profile.sector_specific_requirements.length > 0 && (
          <div>
            <h4 className="font-medium text-gray-900 mb-3">
              {profile.sector_id.replace('_', ' ')} Sector Requirements
            </h4>
            <div className="space-y-3">
              {profile.sector_specific_requirements.map((req, index) => 
                renderRequirement(req, index + profile.base_requirements.length)
              )}
            </div>
          </div>
        )}

        {allRequirements.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <CheckCircleIcon className="h-12 w-12 mx-auto mb-3 text-green-400" />
            <p>No additional requirements for this company type</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default TierRequirementsPanel;
