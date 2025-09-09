/**
 * Deterministic Transparency Dashboard
 * 
 * Displays fast, auditable transparency metrics based on explicit user-created links.
 * Replaces complex scoring algorithms with clear, binary traced/not-traced states.
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Alert,
  AlertDescription,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui';
import { 
  RefreshCw, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Eye,
  Download,
  Info
} from 'lucide-react';
import { useDeterministicTransparency } from '../../hooks/useDeterministicTransparency';
import { useAuth } from '../../contexts/AuthContext';

interface DeterministicTransparencyDashboardProps {
  companyId?: string;
  className?: string;
}

export const DeterministicTransparencyDashboard: React.FC<DeterministicTransparencyDashboardProps> = ({
  companyId,
  className = ''
}) => {
  const { user } = useAuth();
  const {
    metrics,
    gaps,
    loading,
    error,
    fetchTransparencyMetrics,
    fetchTransparencyGaps,
    refreshTransparencyData,
    hasData,
    isFullyTraced,
    averageTransparency
  } = useDeterministicTransparency(companyId);

  const [refreshing, setRefreshing] = useState(false);
  const [selectedGapType, setSelectedGapType] = useState<'mill' | 'plantation' | undefined>(undefined);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshTransparencyData();
    } catch (err) {
      console.error('Failed to refresh transparency data:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleGapTypeChange = (gapType: 'mill' | 'plantation' | 'all') => {
    const type = gapType === 'all' ? undefined : gapType;
    setSelectedGapType(type);
    fetchTransparencyGaps(type);
  };

  useEffect(() => {
    if (hasData) {
      fetchTransparencyGaps();
    }
  }, [hasData, fetchTransparencyGaps]);

  if (loading && !hasData) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load transparency data: {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (!hasData) {
    return (
      <Alert className={className}>
        <Info className="h-4 w-4" />
        <AlertDescription>
          No transparency data available. Ensure you have confirmed purchase orders with batch relationships.
        </AlertDescription>
      </Alert>
    );
  }

  const getTransparencyStatus = (percentage: number) => {
    if (percentage >= 90) return { label: 'Excellent', color: 'bg-green-500', variant: 'default' as const };
    if (percentage >= 70) return { label: 'Good', color: 'bg-blue-500', variant: 'secondary' as const };
    if (percentage >= 50) return { label: 'Fair', color: 'bg-yellow-500', variant: 'outline' as const };
    return { label: 'Needs Improvement', color: 'bg-red-500', variant: 'destructive' as const };
  };

  const millStatus = getTransparencyStatus(metrics!.transparency_to_mill_percentage);
  const plantationStatus = getTransparencyStatus(metrics!.transparency_to_plantation_percentage);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Transparency Dashboard</h2>
          <p className="text-sm text-gray-600 mt-1">
            Deterministic metrics based on explicit supply chain relationships
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Data
        </Button>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Mill Transparency */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transparency to Mill</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics!.transparency_to_mill_percentage.toFixed(1)}%
            </div>
            <div className="flex items-center space-x-2 mt-2">
              <Progress 
                value={metrics!.transparency_to_mill_percentage} 
                className="flex-1"
              />
              <Badge variant={millStatus.variant}>{millStatus.label}</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {metrics!.traced_to_mill_volume.toLocaleString()} of {metrics!.total_volume.toLocaleString()} units traced
            </p>
          </CardContent>
        </Card>

        {/* Plantation Transparency */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transparency to Plantation</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics!.transparency_to_plantation_percentage.toFixed(1)}%
            </div>
            <div className="flex items-center space-x-2 mt-2">
              <Progress 
                value={metrics!.transparency_to_plantation_percentage} 
                className="flex-1"
              />
              <Badge variant={plantationStatus.variant}>{plantationStatus.label}</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {metrics!.traced_to_plantation_volume.toLocaleString()} of {metrics!.total_volume.toLocaleString()} units traced
            </p>
          </CardContent>
        </Card>

        {/* Overall Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Status</CardTitle>
            {isFullyTraced ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {averageTransparency.toFixed(1)}%
            </div>
            <div className="flex items-center space-x-2 mt-2">
              <Progress 
                value={averageTransparency} 
                className="flex-1"
              />
              <Badge variant={isFullyTraced ? 'default' : 'secondary'}>
                {isFullyTraced ? 'Fully Traced' : 'Partial'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {metrics!.traced_purchase_orders} of {metrics!.total_purchase_orders} purchase orders traced
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis */}
      <Tabs defaultValue="gaps" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="gaps">Transparency Gaps</TabsTrigger>
          <TabsTrigger value="methodology">Methodology</TabsTrigger>
        </TabsList>

        <TabsContent value="gaps" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Transparency Gaps</CardTitle>
                <div className="flex space-x-2">
                  <Button
                    variant={selectedGapType === undefined ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleGapTypeChange('all')}
                  >
                    All Gaps
                  </Button>
                  <Button
                    variant={selectedGapType === 'mill' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleGapTypeChange('mill')}
                  >
                    Mill Gaps
                  </Button>
                  <Button
                    variant={selectedGapType === 'plantation' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleGapTypeChange('plantation')}
                  >
                    Plantation Gaps
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {gaps.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Transparency Gaps</h3>
                  <p className="text-gray-600">
                    All purchase orders are fully traced through the supply chain.
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>PO Number</TableHead>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead>Gap Type</TableHead>
                      <TableHead>Trace Depth</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {gaps.map((gap) => (
                      <TableRow key={gap.po_id}>
                        <TableCell className="font-medium">{gap.po_number}</TableCell>
                        <TableCell>{gap.seller_company_name}</TableCell>
                        <TableCell>{gap.product_name}</TableCell>
                        <TableCell>
                          {gap.quantity.toLocaleString()} {gap.unit}
                        </TableCell>
                        <TableCell>
                          <Badge variant={gap.gap_type === 'not_traced_to_mill' ? 'secondary' : 'outline'}>
                            {gap.gap_type === 'not_traced_to_mill' ? 'Mill' : 'Plantation'}
                          </Badge>
                        </TableCell>
                        <TableCell>{gap.trace_depth}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="methodology" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Calculation Methodology</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Deterministic Approach:</strong> Transparency percentages are calculated using 
                  explicit supply chain relationships created by users, not algorithmic estimates.
                </AlertDescription>
              </Alert>

              <div className="space-y-3">
                <div>
                  <h4 className="font-medium">Transparency to Mill</h4>
                  <p className="text-sm text-gray-600">
                    Percentage of volume that can be traced through batch relationships to companies 
                    classified as "mill" or "processing_facility".
                  </p>
                </div>

                <div>
                  <h4 className="font-medium">Transparency to Plantation</h4>
                  <p className="text-sm text-gray-600">
                    Percentage of volume that can be traced through batch relationships to companies 
                    classified as "plantation_grower".
                  </p>
                </div>

                <div>
                  <h4 className="font-medium">Calculation Formula</h4>
                  <code className="text-sm bg-gray-100 p-2 rounded block">
                    transparency_percentage = (traced_volume / total_volume) × 100
                  </code>
                </div>

                <div>
                  <h4 className="font-medium">Data Sources</h4>
                  <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                    <li>Confirmed purchase orders</li>
                    <li>User-created batch relationships</li>
                    <li>Company type classifications</li>
                    <li>Batch transformation events</li>
                  </ul>
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-xs text-gray-500">
                  Last calculated: {new Date(metrics!.calculation_timestamp).toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DeterministicTransparencyDashboard;
