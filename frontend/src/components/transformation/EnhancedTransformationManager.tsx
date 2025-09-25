/**
 * Enhanced Transformation Manager Component
 * Demonstrates all the working automatic functionality
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import Input from '../ui/Input';
import Label from '../ui/Label';
import Textarea from '../ui/Textarea';
import Select from '../ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { useAuth } from '../../contexts/AuthContext';
import { RoleSpecificTransformationForm } from './RoleSpecificTransformationForm';
import { 
  BoltIcon, 
  ChartBarIcon, 
  CogIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface TransformationEvent {
  id: string;
  event_id: string;
  transformation_type: string;
  company_id: string;
  facility_id: string;
  input_batches: any[];
  output_batches: any[];
  quality_metrics: any;
  efficiency_metrics: any;
  process_parameters: any;
  created_at: string;
}

interface QualityInheritanceResult {
  transformation_event_id: string;
  inherited_quality: any;
  input_batches_processed: number;
}

interface CostCalculationResult {
  transformation_event_id: string;
  cost_breakdown: any;
  calculated_at: string;
}

interface TemplateApplicationResult {
  applied: boolean;
  template_id?: string;
  template_name?: string;
  applied_config?: any;
  reason?: string;
}

interface MonitoringData {
  facility_id: string;
  data: any;
  timestamp: string;
}

interface FacilityHealth {
  facility_id: string;
  total_endpoints: number;
  healthy_endpoints: number;
  unhealthy_endpoints: number;
  overall_health: string;
  last_data_received: string;
}

interface EnhancedTransformationManagerProps {
  transformationEventId?: string;
  onTransformationUpdate?: (transformation: TransformationEvent) => void;
  className?: string;
}

export const EnhancedTransformationManager: React.FC<EnhancedTransformationManagerProps> = ({
  transformationEventId,
  onTransformationUpdate,
  className = ''
}) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('auto-features');
  const [transformation, setTransformation] = useState<TransformationEvent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allowedTransformationTypes, setAllowedTransformationTypes] = useState<Array<{label: string, value: string}>>([]);
  const [results, setResults] = useState<{
    qualityInheritance?: QualityInheritanceResult;
    costCalculation?: CostCalculationResult;
    templateApplication?: TemplateApplicationResult;
    monitoringData?: MonitoringData;
    facilityHealth?: FacilityHealth;
  }>({});

  // Form states for creating new transformations
  const [newTransformation, setNewTransformation] = useState({
    event_id: '',
    transformation_type: 'MILLING',
    company_id: '',
    facility_id: '',
    input_batches: [] as any[],
    output_batches: [] as any[],
    process_description: '',
    total_input_quantity: 0,
    auto_apply_template: true,
    auto_calculate_costs: true,
    auto_inherit_quality: true
  });

  useEffect(() => {
    if (transformationEventId) {
      loadTransformation();
    } else {
      // Load allowed transformation types for new transformations
      loadAllowedTransformationTypes();
    }
  }, [transformationEventId]);

  const loadAllowedTransformationTypes = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}/api/v1/transformation-dashboard/transformation-templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const allowedTypes = data.allowed_transformation_types || [];
        
        // Convert to the format expected by the Select component
        const typeOptions = allowedTypes.map((type: string) => ({
          label: type.charAt(0).toUpperCase() + type.slice(1).toLowerCase(),
          value: type
        }));
        
        setAllowedTransformationTypes(typeOptions);
        
        // Set the first allowed type as default if none is set
        if (typeOptions.length > 0 && newTransformation.transformation_type === 'MILLING') {
          setNewTransformation(prev => ({ ...prev, transformation_type: typeOptions[0].value }));
        }
      }
    } catch (error) {
      console.error('Error loading allowed transformation types:', error);
      // Fallback to default options if API fails
      setAllowedTransformationTypes([
        { label: 'Milling', value: 'MILLING' },
        { label: 'Refining', value: 'REFINING' },
        { label: 'Manufacturing', value: 'MANUFACTURING' }
      ]);
    }
  };

  const loadTransformation = async () => {
    if (!transformationEventId) return;
    
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      setTransformation({
        id: transformationEventId,
        event_id: 'TRANS-2024-001',
        transformation_type: 'MILLING',
        company_id: 'company-uuid',
        facility_id: 'MILL-001',
        input_batches: [
          { batch_id: 'batch-1', quantity: 1000, unit: 'MT' }
        ],
        output_batches: [
          { batch_id: 'batch-2', quantity: 200, unit: 'MT' },
          { batch_id: 'batch-3', quantity: 50, unit: 'MT' }
        ],
        quality_metrics: {
          ffb_quality: 0.95,
          moisture_content: 16.5
        },
        efficiency_metrics: {
          extraction_rate: 23.0,
          energy_consumption: 2500
        },
        process_parameters: {
          processing_time: 8.0,
          temperature: 75.0
        },
        created_at: '2024-01-15T10:00:00Z'
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transformation');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoQualityInheritance = async () => {
    if (!transformation) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/quality-inheritance/auto-calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          transformation_event_id: transformation.id
        })
      });
      
      const result: QualityInheritanceResult = await response.json();
      setResults(prev => ({ ...prev, qualityInheritance: result }));
      
      // Update transformation with inherited quality
      if (result.inherited_quality) {
        const updatedTransformation = {
          ...transformation,
          quality_metrics: {
            ...transformation.quality_metrics,
            ...result.inherited_quality
          }
        };
        setTransformation(updatedTransformation);
        onTransformationUpdate?.(updatedTransformation);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate quality inheritance');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoCostCalculation = async () => {
    if (!transformation) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/costs/auto-calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          transformation_event_id: transformation.id
        })
      });
      
      const result: CostCalculationResult = await response.json();
      setResults(prev => ({ ...prev, costCalculation: result }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate costs');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoTemplateApplication = async () => {
    if (!transformation) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/templates/auto-apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          transformation_event_id: transformation.id
        })
      });
      
      const result: TemplateApplicationResult = await response.json();
      setResults(prev => ({ ...prev, templateApplication: result }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply template');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompleteTransformation = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/transformation/create-complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          ...newTransformation,
          start_time: new Date().toISOString()
        })
      });
      
      const result = await response.json();
      
      if (result.transformation_event_id) {
        setTransformation({
          id: result.transformation_event_id,
          event_id: result.event_id,
          transformation_type: newTransformation.transformation_type,
          company_id: newTransformation.company_id,
          facility_id: newTransformation.facility_id,
          input_batches: newTransformation.input_batches,
          output_batches: newTransformation.output_batches,
          quality_metrics: {},
          efficiency_metrics: {},
          process_parameters: {},
          created_at: new Date().toISOString()
        });
        
        setResults(prev => ({
          ...prev,
          templateApplication: result.template_applied,
          costCalculation: { 
            transformation_event_id: result.transformation_event_id,
            cost_breakdown: result.cost_breakdown,
            calculated_at: new Date().toISOString()
          }
        }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create transformation');
    } finally {
      setLoading(false);
    }
  };

  const handleStartMonitoring = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/monitoring/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      const result = await response.json();
      console.log('Monitoring started:', result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start monitoring');
    } finally {
      setLoading(false);
    }
  };

  const handleGetMonitoringData = async () => {
    if (!transformation?.facility_id) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/monitoring/data/${transformation.facility_id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      const result: MonitoringData = await response.json();
      setResults(prev => ({ ...prev, monitoringData: result }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const handleGetFacilityHealth = async () => {
    if (!transformation?.facility_id) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/transformation-enhanced/monitoring/health/${transformation.facility_id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      const result: FacilityHealth = await response.json();
      setResults(prev => ({ ...prev, facilityHealth: result }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get facility health');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 bg-red-50 border border-red-200 rounded-lg ${className}`}>
        <p className="text-red-800">{error}</p>
        <Button onClick={() => setError(null)} className="mt-2" variant="outline">
          Dismiss
        </Button>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Enhanced Transformation Manager</h2>
          <p className="text-gray-600">
            {transformation ? `Event: ${transformation.event_id}` : 'Create new transformation with automatic features'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">Enhanced</Badge>
          <Badge variant="outline">{transformation?.transformation_type || 'New'}</Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue={activeTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="auto-features" className="flex items-center space-x-2">
            <BoltIcon className="h-4 w-4" />
            <span>Auto Features</span>
          </TabsTrigger>
          <TabsTrigger value="create" className="flex items-center space-x-2">
            <ArrowPathIcon className="h-4 w-4" />
            <span>Create</span>
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center space-x-2">
            <ChartBarIcon className="h-4 w-4" />
            <span>Monitoring</span>
          </TabsTrigger>
          <TabsTrigger value="results" className="flex items-center space-x-2">
            <CheckCircleIcon className="h-4 w-4" />
            <span>Results</span>
          </TabsTrigger>
        </TabsList>

        {/* Auto Features Tab */}
        <TabsContent value="auto-features" className="space-y-4">
          {transformation ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <ChartBarIcon className="h-5 w-5" />
                    <span>Quality Inheritance</span>
                  </CardTitle>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-gray-600 mb-4">
                    Automatically inherit quality metrics through transformation chains
                  </p>
                  <Button onClick={handleAutoQualityInheritance} className="w-full">
                    <BoltIcon className="h-4 w-4 mr-2" />
                    Auto Calculate
                  </Button>
                  {results.qualityInheritance && (
                    <div className="mt-4 p-3 bg-green-50 rounded-lg">
                      <p className="text-sm text-green-800">
                        Processed {results.qualityInheritance.input_batches_processed} input batches
                      </p>
                    </div>
                  )}
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CogIcon className="h-5 w-5" />
                    <span>Cost Calculation</span>
                  </CardTitle>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-gray-600 mb-4">
                    Automatically calculate costs based on transformation type and facility
                  </p>
                  <Button onClick={handleAutoCostCalculation} className="w-full">
                    <BoltIcon className="h-4 w-4 mr-2" />
                    Auto Calculate
                  </Button>
                  {results.costCalculation && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        Total Cost: ${results.costCalculation.cost_breakdown?.total_cost || 0}
                      </p>
                    </div>
                  )}
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <ArrowPathIcon className="h-5 w-5" />
                    <span>Template Application</span>
                  </CardTitle>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-gray-600 mb-4">
                    Automatically apply the most appropriate process template
                  </p>
                  <Button onClick={handleAutoTemplateApplication} className="w-full">
                    <BoltIcon className="h-4 w-4 mr-2" />
                    Auto Apply
                  </Button>
                  {results.templateApplication && (
                    <div className="mt-4 p-3 bg-purple-50 rounded-lg">
                      <p className="text-sm text-purple-800">
                        {results.templateApplication.applied ? 
                          `Applied: ${results.templateApplication.template_name}` :
                          `Failed: ${results.templateApplication.reason}`
                        }
                      </p>
                    </div>
                  )}
                </CardBody>
              </Card>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No transformation selected. Create a new one or select an existing transformation.</p>
            </div>
          )}
        </TabsContent>

        {/* Create Tab */}
        <TabsContent value="create" className="space-y-4">
          <RoleSpecificTransformationForm
            transformationType={newTransformation.transformation_type}
            onSave={handleCreateCompleteTransformation}
            onCancel={() => setActiveTab('auto-features')}
            className="w-full"
          />
        </TabsContent>

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <PlayIcon className="h-5 w-5" />
                  <span>Real-time Monitoring</span>
                </CardTitle>
              </CardHeader>
              <CardBody className="space-y-4">
                <Button onClick={handleStartMonitoring} className="w-full">
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Start Monitoring
                </Button>
                <Button onClick={handleGetMonitoringData} className="w-full" variant="outline">
                  <ChartBarIcon className="h-4 w-4 mr-2" />
                  Get Live Data
                </Button>
                <Button onClick={handleGetFacilityHealth} className="w-full" variant="outline">
                  <CogIcon className="h-4 w-4 mr-2" />
                  Check Health
                </Button>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Monitoring Status</CardTitle>
              </CardHeader>
              <CardBody>
                {results.monitoringData && (
                  <div className="space-y-2">
                    <h4 className="font-medium">Live Data</h4>
                    <div className="text-sm text-gray-600">
                      <p>Facility: {results.monitoringData.facility_id}</p>
                      <p>Data Points: {Object.keys(results.monitoringData.data).length}</p>
                      <p>Last Update: {new Date(results.monitoringData.timestamp).toLocaleString()}</p>
                    </div>
                  </div>
                )}
                
                {results.facilityHealth && (
                  <div className="space-y-2 mt-4">
                    <h4 className="font-medium">Facility Health</h4>
                    <div className="text-sm text-gray-600">
                      <p>Overall: <Badge variant={results.facilityHealth.overall_health === 'healthy' ? 'success' : 'error'}>
                        {results.facilityHealth.overall_health}
                      </Badge></p>
                      <p>Healthy Endpoints: {results.facilityHealth.healthy_endpoints}/{results.facilityHealth.total_endpoints}</p>
                      <p>Last Data: {new Date(results.facilityHealth.last_data_received).toLocaleString()}</p>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>
          </div>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          <div className="space-y-4">
            {results.qualityInheritance && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    <span>Quality Inheritance Results</span>
                  </CardTitle>
                </CardHeader>
                <CardBody>
                  <div className="space-y-2">
                    <p><strong>Input Batches Processed:</strong> {results.qualityInheritance.input_batches_processed}</p>
                    <p><strong>Inherited Quality Metrics:</strong></p>
                    <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                      {JSON.stringify(results.qualityInheritance.inherited_quality, null, 2)}
                    </pre>
                  </div>
                </CardBody>
              </Card>
            )}

            {results.costCalculation && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CheckCircleIcon className="h-5 w-5 text-blue-600" />
                    <span>Cost Calculation Results</span>
                  </CardTitle>
                </CardHeader>
                <CardBody>
                  <div className="space-y-2">
                    <p><strong>Total Cost:</strong> ${results.costCalculation.cost_breakdown?.total_cost || 0}</p>
                    <p><strong>Cost Breakdown:</strong></p>
                    <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                      {JSON.stringify(results.costCalculation.cost_breakdown, null, 2)}
                    </pre>
                  </div>
                </CardBody>
              </Card>
            )}

            {results.templateApplication && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CheckCircleIcon className="h-5 w-5 text-purple-600" />
                    <span>Template Application Results</span>
                  </CardTitle>
                </CardHeader>
                <CardBody>
                  <div className="space-y-2">
                    <p><strong>Applied:</strong> {results.templateApplication.applied ? 'Yes' : 'No'}</p>
                    {results.templateApplication.template_name && (
                      <p><strong>Template:</strong> {results.templateApplication.template_name}</p>
                    )}
                    {results.templateApplication.reason && (
                      <p><strong>Reason:</strong> {results.templateApplication.reason}</p>
                    )}
                    {results.templateApplication.applied_config && (
                      <div>
                        <p><strong>Applied Configuration:</strong></p>
                        <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                          {JSON.stringify(results.templateApplication.applied_config, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </CardBody>
              </Card>
            )}

            {!results.qualityInheritance && !results.costCalculation && !results.templateApplication && (
              <div className="text-center py-8">
                <p className="text-gray-500">No results yet. Use the automatic features to see results here.</p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
