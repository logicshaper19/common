/**
 * Progress Component
 * A simple progress bar component
 */
import React from 'react';
import { cn } from '../../lib/utils';

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  className,
  size = 'md',
  variant = 'default'
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const variantClasses = {
    default: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500'
  };

  return (
    <div className={cn('w-full bg-gray-200 rounded-full overflow-hidden', sizeClasses[size], className)}>
      <div
        className={cn('h-full transition-all duration-300 ease-in-out', variantClasses[variant])}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

export default Progress;
