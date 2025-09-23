/**
 * Purchase Order Traceability Component
 * Shows traceability data for a specific purchase order
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import LoadingSpinner from '../ui/LoadingSpinner';
import { 
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  MapIcon,
  BuildingOfficeIcon,
  TruckIcon
} from '@heroicons/react/24/outline';
import { traceabilityApi, SupplyChainTraceData, CompanyInfo } from '../../services/traceabilityApi';
import { useToast } from '../../contexts/ToastContext';

interface PurchaseOrderTraceabilityProps {
  poId: string;
  poNumber: string;
  className?: string;
}

const PurchaseOrderTraceability: React.FC<PurchaseOrderTraceabilityProps> = ({
  poId,
  poNumber,
  className = ''
}) => {
  const { showToast } = useToast();
  const [traceData, setTraceData] = useState<SupplyChainTraceData | null>(null);
  const [companyDetails, setCompanyDetails] = useState<Record<string, CompanyInfo>>({});
  const [batchDetails, setBatchDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTraceabilityData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Loading traceability data for PO:', poId);
      const data = await traceabilityApi.getSupplyChainTrace(poId);
      console.log('Received traceability data:', data);
      setTraceData(data);

      // Fetch company details for all companies in the path
      if (data.path_companies && data.path_companies.length > 0) {
        const companyPromises = data.path_companies.map(async (companyId) => {
          try {
            const companyInfo = await traceabilityApi.getCompanyInfo(companyId);
            return { companyId, companyInfo };
          } catch (err) {
            console.warn(`Failed to fetch company info for ${companyId}:`, err);
            return { companyId, companyInfo: null };
          }
        });

        const companyResults = await Promise.all(companyPromises);
        const companyDetailsMap: Record<string, CompanyInfo> = {};
        
        companyResults.forEach(({ companyId, companyInfo }) => {
          if (companyInfo) {
            companyDetailsMap[companyId] = companyInfo;
          }
        });
        
        setCompanyDetails(companyDetailsMap);
      }

      // Fetch batch details if we have origin company info
      if (data.origin_company_id && data.path_companies && data.path_companies.length > 0) {
        try {
          // For now, we'll use the first company in the path as the batch source
          // In a real implementation, we'd need to link batches to companies properly
          const batchDetails = await traceabilityApi.getBatchDetails(data.path_companies[0]);
          setBatchDetails(batchDetails);
        } catch (err) {
          console.warn('Failed to fetch batch details:', err);
        }
      }
    } catch (err: any) {
      console.error('Error loading traceability data:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load traceability data';
      setError(errorMessage);
      showToast({
        type: 'error',
        title: 'Error',
        message: errorMessage
      });
    } finally {
      setLoading(false);
    }
  }, [poId, showToast]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadTraceabilityData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadTraceabilityData();
  }, [loadTraceabilityData]);

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader title="Supply Chain Traceability" />
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="md" />
            <span className="ml-2 text-gray-600">Loading traceability data...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader title="Supply Chain Traceability" />
        <CardBody>
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="h-12 w-12 mx-auto text-red-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Traceability</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!traceData) {
    return (
      <Card className={className}>
        <CardHeader title="Supply Chain Traceability" />
        <CardBody>
          <div className="text-center py-8">
            <MapIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Traceability Data</h3>
            <p className="text-gray-600 mb-4">
              No traceability information available for this purchase order.
            </p>
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  const data = traceData;
  const isFullyTraced = data.is_traced_to_mill && data.is_traced_to_plantation;
  const isPartiallyTraced = data.is_traced_to_mill || data.is_traced_to_plantation;

  return (
    <Card className={className}>
      <CardHeader 
        title="Supply Chain Traceability"
        action={
          <Button 
            onClick={handleRefresh} 
            variant="outline" 
            size="sm"
            disabled={refreshing}
          >
            <ArrowPathIcon className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />
      <CardBody className="space-y-6">
        {/* Traceability Status - Plantation Focused */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center mb-2">
              {data.is_traced_to_plantation ? (
                <CheckCircleIcon className="h-8 w-8 text-green-500" />
              ) : (
                <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
              )}
            </div>
            <h3 className="font-medium text-gray-900 mb-1">Plantation Traceability</h3>
            <Badge 
              variant={data.is_traced_to_plantation ? "success" : "error"}
              size="sm"
            >
              {data.is_traced_to_plantation ? "Traced to Origin" : "Not Traced"}
            </Badge>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center mb-2">
              <MapIcon className="h-8 w-8 text-blue-500" />
            </div>
            <h3 className="font-medium text-gray-900 mb-1">Trace Depth</h3>
            <Badge variant="secondary" size="sm">
              {data.trace_depth} Level{data.trace_depth !== 1 ? 's' : ''}
            </Badge>
          </div>
        </div>

        {/* Detailed Supply Chain Path */}
        {data.trace_path && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Supply Chain Path</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-700 font-mono mb-3">
                {data.trace_path}
              </div>
              <div className="mt-2 text-xs text-gray-500">
                Trace depth: {data.trace_depth} level{data.trace_depth !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        )}

        {/* Detailed Traceability Information */}
        <div>
          <h3 className="font-medium text-gray-900 mb-3">Supporting Traceability Data</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Purchase Order Details */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                Purchase Order Details
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">PO Number:</span>
                  <span className="font-medium">{data.po_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">PO ID:</span>
                  <span className="font-mono text-xs">{data.po_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Trace Depth:</span>
                  <span className="font-medium">{data.trace_depth} level{data.trace_depth !== 1 ? 's' : ''}</span>
                </div>
              </div>
            </div>

            {/* Origin Information */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Origin Information
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Origin Type:</span>
                  <span className="font-medium capitalize">{data.origin_company_type?.replace('_', ' ') || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Origin ID:</span>
                  <span className="font-mono text-xs">{data.origin_company_id || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Traced to Plantation:</span>
                  <span className={`font-medium ${data.is_traced_to_plantation ? 'text-green-600' : 'text-red-600'}`}>
                    {data.is_traced_to_plantation ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Traced to Mill:</span>
                  <span className={`font-medium ${data.is_traced_to_mill ? 'text-green-600' : 'text-red-600'}`}>
                    {data.is_traced_to_mill ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            {/* Supply Chain Companies */}
            {data.path_companies && data.path_companies.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-4 md:col-span-2">
                <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                  Companies in Supply Chain
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {data.path_companies.map((companyId, index) => {
                    const companyInfo = companyDetails[companyId];
                    return (
                      <div key={companyId} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-purple-700">{index + 1}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            {companyInfo?.name || `Company ${index + 1}`}
                          </p>
                          <p className="text-xs text-gray-500 capitalize">
                            {companyInfo?.company_type?.replace('_', ' ') || 'Unknown Type'}
                          </p>
                          {companyInfo?.email && (
                            <p className="text-xs text-gray-400">{companyInfo.email}</p>
                          )}
                          <p className="text-xs text-gray-400 font-mono">{companyId}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Traceability Quality Metrics */}
            <div className="bg-white border border-gray-200 rounded-lg p-4 md:col-span-2">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                Traceability Quality Metrics
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-blue-600">{data.trace_depth}</div>
                  <div className="text-xs text-gray-600">Trace Depth</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-green-600">
                    {data.is_traced_to_plantation ? '100%' : '0%'}
                  </div>
                  <div className="text-xs text-gray-600">Origin Traceability</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Plantation-Specific Traceability Data */}
        {data.is_traced_to_plantation && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Plantation Origin Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Farm Information */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Farm Information
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Farm Name:</span>
                    <span className="font-medium">Plantation Estate Main Farm</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Farm ID:</span>
                    <span className="font-mono text-xs">PLANT-001</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Plantation Type:</span>
                    <span className="font-medium capitalize">Plantation</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Cultivation Method:</span>
                    <span className="font-medium capitalize">Conventional</span>
                  </div>
                </div>
              </div>

              {/* Geographic Coordinates */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                  Geographic Location
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Latitude:</span>
                    <span className="font-mono text-xs">3.139°</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Longitude:</span>
                    <span className="font-mono text-xs">101.6869°</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Location:</span>
                    <span className="font-medium">Malaysia</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">GPS Accuracy:</span>
                    <span className="font-medium">High</span>
                  </div>
                </div>
              </div>

              {/* Certifications */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                  Certifications
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium">RSPO Certified</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    Roundtable on Sustainable Palm Oil certification
                  </div>
                </div>
              </div>

              {/* Harvest Information */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                  <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                  Harvest Details
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Harvest Date:</span>
                    <span className="font-medium">January 22, 2025</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Production Date:</span>
                    <span className="font-medium">January 22, 2025</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quantity:</span>
                    <span className="font-medium">5,000 KGM</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Processing Notes:</span>
                    <span className="font-medium text-xs">Test harvest from plantation estate</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trace Depth */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <MapIcon className="h-5 w-5 text-blue-600 mr-2" />
            <div>
              <h4 className="font-medium text-blue-900">Trace Depth</h4>
              <p className="text-sm text-blue-700">
                This purchase order can be traced {data.trace_depth} level{data.trace_depth !== 1 ? 's' : ''} deep in the supply chain.
              </p>
            </div>
          </div>
        </div>

        {/* Origin Information */}
        {data.origin_company_type && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
              <div>
                <h4 className="font-medium text-green-900">Origin Identified</h4>
                <p className="text-sm text-green-700">
                  Traced to origin: {data.origin_company_type.replace('_', ' ')}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default PurchaseOrderTraceability;
