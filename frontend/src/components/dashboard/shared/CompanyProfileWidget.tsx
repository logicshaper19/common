/**
 * Company Profile Widget - Shared component for all dashboards
 * Shows company information and settings access
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { 
  BuildingOfficeIcon, 
  CogIcon, 
  GlobeAltIcon,
  EnvelopeIcon,
  PhoneIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';

interface CompanyInfo {
  id: string;
  name: string;
  company_type: string;
  email: string;
  phone?: string;
  website?: string;
  address?: {
    street?: string;
    city?: string;
    state?: string;
    country?: string;
    postal_code?: string;
  };
  verification_status: 'verified' | 'pending' | 'unverified';
  created_at: string;
}

interface CompanyProfileWidgetProps {
  companyId: string;
  canManageSettings: boolean;
  className?: string;
}

export const CompanyProfileWidget: React.FC<CompanyProfileWidgetProps> = ({
  companyId,
  canManageSettings,
  className = ''
}) => {
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCompanyInfo();
  }, [companyId]);

  const loadCompanyInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/companies/${companyId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load company information');
      }

      const data = await response.json();
      setCompanyInfo(data);
    } catch (err) {
      console.error('Error loading company info:', err);
      setError(err instanceof Error ? err.message : 'Failed to load company information');
    } finally {
      setLoading(false);
    }
  };

  const getVerificationBadgeColor = (status: string) => {
    switch (status) {
      case 'verified': return 'green';
      case 'pending': return 'yellow';
      case 'unverified': return 'red';
      default: return 'gray';
    }
  };

  const getCompanyTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'brand': return 'blue';
      case 'processor': return 'purple';
      case 'originator': return 'green';
      case 'trader': return 'orange';
      case 'auditor': return 'indigo';
      case 'regulator': return 'red';
      default: return 'gray';
    }
  };

  const formatAddress = (address: CompanyInfo['address']) => {
    if (!address) return null;
    
    const parts = [
      address.street,
      address.city,
      address.state,
      address.country,
      address.postal_code
    ].filter(Boolean);
    
    return parts.length > 0 ? parts.join(', ') : null;
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center">
            <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Company Profile</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error || !companyInfo) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center">
            <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Company Profile</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="text-center py-8">
            <p className="text-red-600 mb-2">Failed to load company information</p>
            <Button onClick={loadCompanyInfo} variant="outline" size="sm">
              Retry
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Company Profile</h3>
          </div>
          {canManageSettings && (
            <Link to="/settings/company">
              <Button size="sm" variant="outline">
                <CogIcon className="h-4 w-4 mr-1" />
                Settings
              </Button>
            </Link>
          )}
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-4">
          {/* Company Name and Type */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <h4 className="text-xl font-semibold text-gray-900">{companyInfo.name}</h4>
              <Badge color={getCompanyTypeBadgeColor(companyInfo.company_type)}>
                {companyInfo.company_type.charAt(0).toUpperCase() + companyInfo.company_type.slice(1)}
              </Badge>
            </div>
            <div className="flex items-center space-x-2">
              <Badge color={getVerificationBadgeColor(companyInfo.verification_status)}>
                {companyInfo.verification_status}
              </Badge>
              <span className="text-sm text-gray-500">
                Member since {new Date(companyInfo.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-2">
            <div className="flex items-center text-sm text-gray-600">
              <EnvelopeIcon className="h-4 w-4 mr-2 text-gray-400" />
              <a href={`mailto:${companyInfo.email}`} className="hover:text-blue-600">
                {companyInfo.email}
              </a>
            </div>
            
            {companyInfo.phone && (
              <div className="flex items-center text-sm text-gray-600">
                <PhoneIcon className="h-4 w-4 mr-2 text-gray-400" />
                <a href={`tel:${companyInfo.phone}`} className="hover:text-blue-600">
                  {companyInfo.phone}
                </a>
              </div>
            )}
            
            {companyInfo.website && (
              <div className="flex items-center text-sm text-gray-600">
                <GlobeAltIcon className="h-4 w-4 mr-2 text-gray-400" />
                <a 
                  href={companyInfo.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="hover:text-blue-600"
                >
                  {companyInfo.website}
                </a>
              </div>
            )}
            
            {formatAddress(companyInfo.address) && (
              <div className="flex items-start text-sm text-gray-600">
                <MapPinIcon className="h-4 w-4 mr-2 text-gray-400 mt-0.5" />
                <span>{formatAddress(companyInfo.address)}</span>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          {canManageSettings && (
            <div className="pt-4 border-t border-gray-200">
              <div className="flex space-x-2">
                <Link to="/settings/company">
                  <Button size="sm" variant="outline">
                    Edit Profile
                  </Button>
                </Link>
                <Link to="/settings/verification">
                  <Button size="sm" variant="outline">
                    Verification
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
};

export default CompanyProfileWidget;
