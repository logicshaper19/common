/**
 * Originator Router Component
 * Optimized routing with lazy loading for originator-specific features
 * Follows the same pattern as ProductsRouter for consistency
 */
import React, { Suspense, lazy } from 'react';
import { useAuth } from '../../contexts/AuthContext';

// Lazy load components for better performance
const OriginatorDashboard = lazy(() => import('../../pages/OriginatorDashboard'));
const FarmInformationManager = lazy(() => import('./FarmInformationManager'));
const CertificationManager = lazy(() => import('./CertificationManager'));
const OriginDataManager = lazy(() => import('./OriginDataManager'));

// Optimized loading fallback component
const OriginatorLoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-pulse space-y-4 w-full max-w-md">
      <div className="h-8 bg-gray-200 rounded"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
      <div className="h-32 bg-gray-200 rounded"></div>
    </div>
  </div>
);

interface OriginatorRouterProps {
  view?: 'dashboard' | 'farms' | 'certifications' | 'origin-data';
}

const OriginatorRouter: React.FC<OriginatorRouterProps> = ({ view = 'dashboard' }) => {
  const { user } = useAuth();

  // Check if user is an originator
  const isOriginator = React.useMemo(() => {
    if (!user) return false;
    
    const companyType = user?.company?.company_type;
    const sectorId = user?.sector_id;
    const tierLevel = user?.tier_level;
    
    // Check if company type indicates originator (legacy and new types)
    const isOriginatorType = companyType === 'originator' || 
                            companyType === 'plantation_grower' || 
                            companyType === 'smallholder_cooperative';
    
    // Check if sector/tier indicates originator (T6/T7 in palm oil)
    const isOriginatorTier = (sectorId === 'palm_oil' && (tierLevel === 6 || tierLevel === 7)) ||
                            (sectorId === 'apparel' && tierLevel === 6);
    
    // Check if user has originator permissions
    const hasOriginatorPermissions = user?.permissions?.includes('add_origin_data') ||
                                    user?.permissions?.includes('provide_farmer_data');
    
    return isOriginatorType || isOriginatorTier || hasOriginatorPermissions;
  }, [user]);

  // If not an originator, show access denied
  if (!isOriginator) {
    return (
      <div className="text-center py-12">
        <div className="max-w-md mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-yellow-100 rounded-full">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-yellow-800 mb-2">
              Originator Access Required
            </h3>
            <p className="text-yellow-700 text-sm">
              This section is only available to originator companies (plantations, farms, and primary producers). 
              Your current role and company type do not have access to originator-specific features.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const renderView = () => {
    switch (view) {
      case 'farms':
        return <FarmInformationManager companyId={user?.company?.id} />;
      case 'certifications':
        return <CertificationManager companyId={user?.company?.id} />;
      case 'origin-data':
        return <OriginDataManager companyId={user?.company?.id} />;
      case 'dashboard':
      default:
        return <OriginatorDashboard />;
    }
  };

  return (
    <Suspense fallback={<OriginatorLoadingFallback />}>
      {renderView()}
    </Suspense>
  );
};

export default OriginatorRouter;
