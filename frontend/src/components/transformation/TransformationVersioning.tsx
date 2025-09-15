/**
 * Transformation Versioning Component
 * Provides comprehensive versioning, quality inheritance, cost tracking, and template management
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
import { 
  ClockIcon, 
  PlusIcon, 
  CheckIcon, 
  XMarkIcon,
  CalculatorIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon
} from '@heroicons/react/24/outline';

interface TransformationEvent {
  id: string;
  event_id: string;
  transformation_type: string;
  current_version: number;
  is_locked: boolean;
  created_at: string;
}

interface TransformationVersion {
  id: string;
  version_number: number;
  version_type: 'revision' | 'correction' | 'amendment';
  change_reason?: string;
  change_description?: string;
  approval_status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  created_by_user_id: string;
}

interface QualityInheritanceRule {
  id: string;
  transformation_type: string;
  input_quality_metric: string;
  output_quality_metric: string;
  inheritance_type: 'direct' | 'degraded' | 'enhanced' | 'calculated';
  degradation_factor?: number;
  enhancement_factor?: number;
  is_active: boolean;
}

interface TransformationCost {
  id: string;
  cost_category: string;
  cost_type: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  total_cost: number;
  currency: string;
  created_at: string;
}

interface ProcessTemplate {
  id: string;
  template_name: string;
  transformation_type: string;
  company_type: string;
  description?: string;
  version: string;
  is_standard: boolean;
  usage_count: number;
}

interface MonitoringEndpoint {
  id: string;
  facility_id: string;
  endpoint_name: string;
  endpoint_type: 'sensor' | 'api' | 'file_upload' | 'manual';
  is_active: boolean;
  last_data_received?: string;
  error_count: number;
}

interface TransformationVersioningProps {
  transformationEventId: string;
  onVersionChange?: (version: TransformationVersion) => void;
  onCostUpdate?: (costs: TransformationCost[]) => void;
  className?: string;
}

export const TransformationVersioning: React.FC<TransformationVersioningProps> = ({
  transformationEventId,
  onVersionChange,
  onCostUpdate,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('versions');
  const [transformationEvent, setTransformationEvent] = useState<TransformationEvent | null>(null);
  const [versions, setVersions] = useState<TransformationVersion[]>([]);
  const [qualityRules, setQualityRules] = useState<QualityInheritanceRule[]>([]);
  const [costs, setCosts] = useState<TransformationCost[]>([]);
  const [templates, setTemplates] = useState<ProcessTemplate[]>([]);
  const [monitoringEndpoints, setMonitoringEndpoints] = useState<MonitoringEndpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [newVersion, setNewVersion] = useState({
    version_type: 'revision' as const,
    change_reason: '',
    change_description: '',
    approval_required: false
  });

  const [newCost, setNewCost] = useState({
    cost_category: 'energy',
    cost_type: '',
    quantity: 0,
    unit: 'kWh',
    unit_cost: 0,
    currency: 'USD'
  });

  const [newTemplate, setNewTemplate] = useState({
    template_name: '',
    transformation_type: '',
    company_type: '',
    description: '',
    is_standard: false
  });

  const [newEndpoint, setNewEndpoint] = useState({
    facility_id: '',
    endpoint_name: '',
    endpoint_type: 'sensor' as const,
    endpoint_url: '',
    data_format: 'json',
    monitored_metrics: [] as string[],
    update_frequency: 60,
    auth_type: 'none' as const
  });

  useEffect(() => {
    loadData();
  }, [transformationEventId]);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadTransformationEvent(),
        loadVersions(),
        loadQualityRules(),
        loadCosts(),
        loadTemplates(),
        loadMonitoringEndpoints()
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadTransformationEvent = async () => {
    // Mock data - replace with actual API call
    setTransformationEvent({
      id: transformationEventId,
      event_id: 'TRANS-2024-001',
      transformation_type: 'MILLING',
      current_version: 3,
      is_locked: false,
      created_at: '2024-01-15T10:00:00Z'
    });
  };

  const loadVersions = async () => {
    // Mock data - replace with actual API call
    setVersions([
      {
        id: '1',
        version_number: 3,
        version_type: 'revision',
        change_reason: 'Updated efficiency metrics',
        change_description: 'Corrected energy consumption values based on actual readings',
        approval_status: 'approved',
        created_at: '2024-01-15T14:30:00Z',
        created_by_user_id: 'user-1'
      },
      {
        id: '2',
        version_number: 2,
        version_type: 'correction',
        change_reason: 'Data correction',
        change_description: 'Fixed input quantity calculation error',
        approval_status: 'approved',
        created_at: '2024-01-15T12:15:00Z',
        created_by_user_id: 'user-1'
      },
      {
        id: '3',
        version_number: 1,
        version_type: 'revision',
        change_reason: 'Initial creation',
        change_description: 'Initial transformation event creation',
        approval_status: 'approved',
        created_at: '2024-01-15T10:00:00Z',
        created_by_user_id: 'user-1'
      }
    ]);
  };

  const loadQualityRules = async () => {
    // Mock data - replace with actual API call
    setQualityRules([
      {
        id: '1',
        transformation_type: 'MILLING',
        input_quality_metric: 'ffb_quality',
        output_quality_metric: 'cpo_quality',
        inheritance_type: 'degraded',
        degradation_factor: 0.90,
        is_active: true
      },
      {
        id: '2',
        transformation_type: 'MILLING',
        input_quality_metric: 'ffb_moisture',
        output_quality_metric: 'cpo_moisture',
        inheritance_type: 'calculated',
        is_active: true
      }
    ]);
  };

  const loadCosts = async () => {
    // Mock data - replace with actual API call
    setCosts([
      {
        id: '1',
        cost_category: 'energy',
        cost_type: 'electricity',
        quantity: 1500,
        unit: 'kWh',
        unit_cost: 0.12,
        total_cost: 180,
        currency: 'USD',
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        id: '2',
        cost_category: 'labor',
        cost_type: 'operators',
        quantity: 8,
        unit: 'hours',
        unit_cost: 25,
        total_cost: 200,
        currency: 'USD',
        created_at: '2024-01-15T10:00:00Z'
      }
    ]);
  };

  const loadTemplates = async () => {
    // Mock data - replace with actual API call
    setTemplates([
      {
        id: '1',
        template_name: 'Standard Palm Oil Milling',
        transformation_type: 'MILLING',
        company_type: 'mill',
        description: 'Standard milling process template with industry benchmarks',
        version: '1.0',
        is_standard: true,
        usage_count: 45
      },
      {
        id: '2',
        template_name: 'High Efficiency Milling',
        transformation_type: 'MILLING',
        company_type: 'mill',
        description: 'Optimized milling process for high efficiency operations',
        version: '2.1',
        is_standard: false,
        usage_count: 12
      }
    ]);
  };

  const loadMonitoringEndpoints = async () => {
    // Mock data - replace with actual API call
    setMonitoringEndpoints([
      {
        id: '1',
        facility_id: 'MILL-001',
        endpoint_name: 'Energy Monitor',
        endpoint_type: 'sensor',
        is_active: true,
        last_data_received: '2024-01-15T15:45:00Z',
        error_count: 0
      },
      {
        id: '2',
        facility_id: 'MILL-001',
        endpoint_name: 'Quality Sensor API',
        endpoint_type: 'api',
        is_active: true,
        last_data_received: '2024-01-15T15:44:00Z',
        error_count: 2
      }
    ]);
  };

  const handleCreateVersion = async () => {
    try {
      setLoading(true);
      // API call to create version
      console.log('Creating version:', newVersion);
      // Reset form
      setNewVersion({
        version_type: 'revision',
        change_reason: '',
        change_description: '',
        approval_required: false
      });
      await loadVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create version');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCost = async () => {
    try {
      setLoading(true);
      // API call to create cost
      console.log('Creating cost:', newCost);
      // Reset form
      setNewCost({
        cost_category: 'energy',
        cost_type: '',
        quantity: 0,
        unit: 'kWh',
        unit_cost: 0,
        currency: 'USD'
      });
      await loadCosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create cost');
    } finally {
      setLoading(false);
    }
  };

  const handleUseTemplate = async (templateId: string) => {
    try {
      setLoading(true);
      // API call to use template
      console.log('Using template:', templateId);
      await loadTemplates();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to use template');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEndpoint = async () => {
    try {
      setLoading(true);
      // API call to create endpoint
      console.log('Creating endpoint:', newEndpoint);
      // Reset form
      setNewEndpoint({
        facility_id: '',
        endpoint_name: '',
        endpoint_type: 'sensor',
        endpoint_url: '',
        data_format: 'json',
        monitored_metrics: [],
        update_frequency: 60,
        auth_type: 'none'
      });
      await loadMonitoringEndpoints();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create endpoint');
    } finally {
      setLoading(false);
    }
  };

  const getApprovalStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getVersionTypeColor = (type: string) => {
    switch (type) {
      case 'revision': return 'bg-blue-100 text-blue-800';
      case 'correction': return 'bg-orange-100 text-orange-800';
      case 'amendment': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
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
        <Button onClick={loadData} className="mt-2" variant="outline">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Transformation Management</h2>
          <p className="text-gray-600">
            Event: {transformationEvent?.event_id} | Version: {transformationEvent?.current_version}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {transformationEvent?.is_locked && (
            <Badge variant="error">Locked</Badge>
          )}
          <Badge variant="outline">{transformationEvent?.transformation_type}</Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue={activeTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="versions" className="flex items-center space-x-2">
            <ClockIcon className="h-4 w-4" />
            <span>Versions</span>
          </TabsTrigger>
          <TabsTrigger value="quality" className="flex items-center space-x-2">
            <ChartBarIcon className="h-4 w-4" />
            <span>Quality</span>
          </TabsTrigger>
          <TabsTrigger value="costs" className="flex items-center space-x-2">
            <CalculatorIcon className="h-4 w-4" />
            <span>Costs</span>
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center space-x-2">
            <DocumentTextIcon className="h-4 w-4" />
            <span>Templates</span>
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center space-x-2">
            <CogIcon className="h-4 w-4" />
            <span>Monitoring</span>
          </TabsTrigger>
        </TabsList>

        {/* Versions Tab */}
        <TabsContent value="versions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Version History</span>
                <Button onClick={() => setActiveTab('versions')} size="sm">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  New Version
                </Button>
              </CardTitle>
            </CardHeader>
                <CardBody>
              <div className="space-y-4">
                {versions.map((version) => (
                  <div key={version.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Badge className={getVersionTypeColor(version.version_type)}>
                          {version.version_type}
                        </Badge>
                        <span className="font-medium">Version {version.version_number}</span>
                      </div>
                      <Badge className={getApprovalStatusColor(version.approval_status)}>
                        {version.approval_status}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{version.change_reason}</p>
                    {version.change_description && (
                      <p className="text-sm text-gray-500">{version.change_description}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">
                      {new Date(version.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
                </CardBody>
          </Card>
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quality Inheritance Rules</CardTitle>
            </CardHeader>
                <CardBody>
              <div className="space-y-4">
                {qualityRules.map((rule) => (
                  <div key={rule.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{rule.transformation_type}</span>
                      <Badge variant={rule.is_active ? "success" : "neutral"}>
                        {rule.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600">
                      {rule.input_quality_metric} → {rule.output_quality_metric}
                    </p>
                    <p className="text-sm text-gray-500">
                      Type: {rule.inheritance_type}
                      {rule.degradation_factor && ` | Factor: ${rule.degradation_factor}`}
                    </p>
                  </div>
                ))}
              </div>
                </CardBody>
          </Card>
        </TabsContent>

        {/* Costs Tab */}
        <TabsContent value="costs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Cost Tracking</span>
                <Button onClick={() => setActiveTab('costs')} size="sm">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Cost
                </Button>
              </CardTitle>
            </CardHeader>
                <CardBody>
              <div className="space-y-4">
                {costs.map((cost) => (
                  <div key={cost.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{cost.cost_type}</span>
                      <span className="text-lg font-bold">${cost.total_cost.toFixed(2)}</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {cost.quantity} {cost.unit} × ${cost.unit_cost} = ${cost.total_cost}
                    </p>
                    <p className="text-sm text-gray-500">
                      Category: {cost.cost_category} | Currency: {cost.currency}
                    </p>
                  </div>
                ))}
              </div>
                </CardBody>
          </Card>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Process Templates</span>
                <Button onClick={() => setActiveTab('templates')} size="sm">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  New Template
                </Button>
              </CardTitle>
            </CardHeader>
                <CardBody>
              <div className="space-y-4">
                {templates.map((template) => (
                  <div key={template.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{template.template_name}</span>
                      <div className="flex items-center space-x-2">
                        {template.is_standard && (
                          <Badge variant="outline">Standard</Badge>
                        )}
                        <Button
                          onClick={() => handleUseTemplate(template.id)}
                          size="sm"
                          variant="outline"
                        >
                          Use Template
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                    <p className="text-sm text-gray-500">
                      Type: {template.transformation_type} | Company: {template.company_type} | 
                      Version: {template.version} | Used: {template.usage_count} times
                    </p>
                  </div>
                ))}
              </div>
                </CardBody>
          </Card>
        </TabsContent>

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Real-time Monitoring</span>
                <Button onClick={() => setActiveTab('monitoring')} size="sm">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Endpoint
                </Button>
              </CardTitle>
            </CardHeader>
                <CardBody>
              <div className="space-y-4">
                {monitoringEndpoints.map((endpoint) => (
                  <div key={endpoint.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{endpoint.endpoint_name}</span>
                      <div className="flex items-center space-x-2">
                        <Badge variant={endpoint.is_active ? "success" : "neutral"}>
                          {endpoint.is_active ? "Active" : "Inactive"}
                        </Badge>
                        {endpoint.error_count > 0 && (
                          <Badge variant="error">
                            {endpoint.error_count} errors
                          </Badge>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">
                      Facility: {endpoint.facility_id} | Type: {endpoint.endpoint_type}
                    </p>
                    {endpoint.last_data_received && (
                      <p className="text-sm text-gray-500">
                        Last data: {new Date(endpoint.last_data_received).toLocaleString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
                </CardBody>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
