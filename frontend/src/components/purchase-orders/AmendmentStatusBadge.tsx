import React from 'react';
import Badge from '../ui/Badge';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  MinusCircleIcon 
} from '@heroicons/react/24/outline';

interface AmendmentStatusBadgeProps {
  status: 'none' | 'proposed' | 'approved' | 'rejected';
  className?: string;
  showIcon?: boolean;
}

export const AmendmentStatusBadge: React.FC<AmendmentStatusBadgeProps> = ({
  status,
  className = '',
  showIcon = true
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'none':
        return {
          variant: 'neutral' as const,
          label: 'No Amendments',
          icon: MinusCircleIcon
        };
      case 'proposed':
        return {
          variant: 'warning' as const,
          label: 'Amendment Proposed',
          icon: ClockIcon
        };
      case 'approved':
        return {
          variant: 'success' as const,
          label: 'Amendment Approved',
          icon: CheckCircleIcon
        };
      case 'rejected':
        return {
          variant: 'error' as const,
          label: 'Amendment Rejected',
          icon: XCircleIcon
        };
      default:
        return {
          variant: 'neutral' as const,
          label: 'Unknown Status',
          icon: MinusCircleIcon
        };
    }
  };

  const config = getStatusConfig();
  const IconComponent = config.icon;

  return (
    <Badge variant={config.variant} className={className}>
      <div className="flex items-center space-x-1">
        {showIcon && <IconComponent className="h-3 w-3" />}
        <span>{config.label}</span>
      </div>
    </Badge>
  );
};

export default AmendmentStatusBadge;
