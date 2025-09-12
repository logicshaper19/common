/**
 * Smart Action Center - Contextual actions based on user role and current state
 * Provides intelligent recommendations and quick actions
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { 
  PlusIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowRightIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface SmartAction {
  id: string;
  title: string;
  description: string;
  type: 'primary' | 'secondary' | 'urgent' | 'suggestion';
  priority: 'high' | 'medium' | 'low';
  category: 'po' | 'supplier' | 'compliance' | 'transparency' | 'system';
  actionUrl?: string;
  actionHandler?: () => void;
  estimatedTime?: string;
  impact?: 'high' | 'medium' | 'low';
  requirements?: string[];
  deadline?: string;
}

interface SmartActionCenterProps {
  userRole: string;
  companyType: string;
  className?: string;
  maxActions?: number;
}

export const SmartActionCenter: React.FC<SmartActionCenterProps> = ({
  userRole,
  companyType,
  className = '',
  maxActions = 6
}) => {
  const [actions, setActions] = useState<SmartAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadSmartActions();
  }, [userRole, companyType]);

  const loadSmartActions = async () => {
    setLoading(true);
    
    try {
      // TODO: Replace with real API call that considers user context
      // const response = await fetch(`/api/v1/smart-actions?role=${userRole}&company_type=${companyType}`);
      
      // Mock smart actions based on role and company type
      const mockActions = generateSmartActions(userRole, companyType);
      setActions(mockActions);
    } catch (error) {
      console.error('Failed to load smart actions:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateSmartActions = (role: string, companyType: string): SmartAction[] => {
    const baseActions: SmartAction[] = [];

    // Brand-specific actions
    if (companyType === 'brand') {
      baseActions.push(
        {
          id: 'create-po',
          title: 'Create Purchase Order',
          description: 'Start a new purchase order with your suppliers',
          type: 'primary',
          priority: 'high',
          category: 'po',
          actionUrl: '/purchase-orders/create',
          estimatedTime: '5 min',
          impact: 'high'
        },
        {
          id: 'review-transparency',
          title: 'Review Transparency Gaps',
          description: '3 purchase orders need transparency verification',
          type: 'urgent',
          priority: 'high',
          category: 'transparency',
          actionUrl: '/transparency/gaps',
          estimatedTime: '15 min',
          impact: 'high',
          deadline: '2 days'
        },
        {
          id: 'onboard-supplier',
          title: 'Onboard New Supplier',
          description: 'Add a new supplier to your network',
          type: 'secondary',
          priority: 'medium',
          category: 'supplier',
          actionUrl: '/suppliers/onboard',
          estimatedTime: '10 min',
          impact: 'medium'
        }
      );
    }

    // Processor-specific actions
    if (companyType === 'processor') {
      baseActions.push(
        {
          id: 'confirm-pos',
          title: 'Confirm Pending Orders',
          description: '5 purchase orders awaiting your confirmation',
          type: 'urgent',
          priority: 'high',
          category: 'po',
          actionUrl: '/purchase-orders?status=pending',
          estimatedTime: '20 min',
          impact: 'high',
          deadline: '1 day'
        },
        {
          id: 'update-capacity',
          title: 'Update Production Capacity',
          description: 'Keep your capacity information current',
          type: 'suggestion',
          priority: 'medium',
          category: 'system',
          actionUrl: '/settings/capacity',
          estimatedTime: '5 min',
          impact: 'medium'
        }
      );
    }

    // Role-specific actions
    if (role === 'admin') {
      baseActions.push(
        {
          id: 'manage-team',
          title: 'Manage Team Access',
          description: 'Review and update team member permissions',
          type: 'secondary',
          priority: 'medium',
          category: 'system',
          actionUrl: '/team',
          estimatedTime: '10 min',
          impact: 'medium'
        }
      );
    }

    // Compliance actions (all companies)
    baseActions.push(
      {
        id: 'eudr-compliance',
        title: 'EUDR Compliance Check',
        description: 'Ensure your supply chain meets EUDR requirements',
        type: 'suggestion',
        priority: 'medium',
        category: 'compliance',
        actionUrl: '/compliance/eudr',
        estimatedTime: '30 min',
        impact: 'high',
        requirements: ['Supply chain data', 'Origin certificates']
      }
    );

    return baseActions;
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'primary':
        return <PlusIcon className="h-5 w-5" />;
      case 'urgent':
        return <ExclamationTriangleIcon className="h-5 w-5" />;
      case 'suggestion':
        return <LightBulbIcon className="h-5 w-5" />;
      default:
        return <BoltIcon className="h-5 w-5" />;
    }
  };

  const getActionColor = (type: string) => {
    switch (type) {
      case 'primary':
        return 'blue';
      case 'urgent':
        return 'red';
      case 'suggestion':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
      case 'medium':
        return <ClockIcon className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    }
  };

  const filteredActions = filter === 'all' 
    ? actions 
    : actions.filter(action => action.category === filter);

  const handleActionClick = (action: SmartAction) => {
    if (action.actionHandler) {
      action.actionHandler();
    } else if (action.actionUrl) {
      // TODO: Navigate to URL
      console.log(`Navigate to: ${action.actionUrl}`);
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BoltIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Smart Actions</h3>
            <Badge color="blue" size="sm" className="ml-2">
              {filteredActions.length}
            </Badge>
          </div>
          <div className="flex space-x-2">
            {['all', 'po', 'supplier', 'compliance'].map((category) => (
              <Button
                key={category}
                size="xs"
                variant={filter === category ? 'default' : 'outline'}
                onClick={() => setFilter(category)}
              >
                {category === 'all' ? 'All' : category.toUpperCase()}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardBody>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        ) : filteredActions.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircleIcon className="h-12 w-12 text-green-300 mx-auto mb-4" />
            <p className="text-gray-500">All caught up! No actions needed.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredActions.slice(0, maxActions).map((action) => (
              <div
                key={action.id}
                className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg bg-${getActionColor(action.type)}-50`}>
                      {getActionIcon(action.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-gray-900">{action.title}</h4>
                        {getPriorityIcon(action.priority)}
                        {action.deadline && (
                          <Badge color="red" size="xs">
                            Due in {action.deadline}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{action.description}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        {action.estimatedTime && (
                          <span>⏱️ {action.estimatedTime}</span>
                        )}
                        {action.impact && (
                          <span>📈 {action.impact} impact</span>
                        )}
                      </div>
                      {action.requirements && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Requirements:</p>
                          <div className="flex flex-wrap gap-1">
                            {action.requirements.map((req, index) => (
                              <Badge key={index} color="gray" size="xs">
                                {req}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant={action.type === 'urgent' ? 'default' : 'outline'}
                    onClick={() => handleActionClick(action)}
                  >
                    <ArrowRightIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default SmartActionCenter;
