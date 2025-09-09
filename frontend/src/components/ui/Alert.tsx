/**
 * Alert Component
 * A flexible alert component for displaying messages
 */
import React from 'react';
import { cn } from '../../lib/utils';
import { 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'default' | 'destructive' | 'warning' | 'success';
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ 
  children, 
  variant = 'default', 
  className 
}) => {
  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    destructive: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    success: 'bg-green-50 border-green-200 text-green-800'
  };

  const icons = {
    default: InformationCircleIcon,
    destructive: XCircleIcon,
    warning: ExclamationTriangleIcon,
    success: CheckCircleIcon
  };

  const Icon = icons[variant];

  return (
    <div className={cn(
      'relative w-full rounded-lg border p-4',
      variantClasses[variant],
      className
    )}>
      <div className="flex">
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="ml-3 flex-1">
          {children}
        </div>
      </div>
    </div>
  );
};

interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  children, 
  className 
}) => {
  return (
    <div className={cn('text-sm', className)}>
      {children}
    </div>
  );
};

export default Alert;
