import React from 'react';
import { Card, CardBody } from './Card';
import { cn } from '../../lib/utils';

export interface AnalyticsCardProps {
  name: string;
  value: string | number;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: React.ComponentType<{ className?: string }>;
  href?: string;
  onClick?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showChange?: boolean;
}

const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  name,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  href,
  onClick,
  className,
  size = 'md',
  showIcon = true,
  showChange = true,
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (href) {
      window.location.href = href;
    }
  };

  const isClickable = !!(onClick || href);

  const sizeClasses = {
    sm: {
      padding: 'p-4',
      valueText: 'text-2xl font-bold',
      nameText: 'text-xs font-medium',
      iconSize: 'w-4 h-4',
      changeText: 'text-xs',
      changePadding: 'px-1.5 py-0.5',
    },
    md: {
      padding: 'p-5',
      valueText: 'text-3xl font-bold',
      nameText: 'text-sm font-medium',
      iconSize: 'w-5 h-5',
      changeText: 'text-xs',
      changePadding: 'px-2 py-1',
    },
    lg: {
      padding: 'p-6',
      valueText: 'text-4xl font-bold',
      nameText: 'text-base font-medium',
      iconSize: 'w-6 h-6',
      changeText: 'text-sm',
      changePadding: 'px-3 py-1.5',
    },
  };

  const sizeConfig = sizeClasses[size];

  const getChangeColor = () => {
    switch (changeType) {
      case 'increase':
        return 'text-emerald-700 bg-emerald-50';
      case 'decrease':
        return 'text-red-700 bg-red-50';
      default:
        return 'text-neutral-700 bg-neutral-50';
    }
  };

  const getChangeIcon = () => {
    switch (changeType) {
      case 'increase':
        return '↗';
      case 'decrease':
        return '↘';
      default:
        return '→';
    }
  };

  return (
    <Card
      className={cn(
        'transition-all duration-200 border-neutral-100',
        isClickable && 'hover:shadow-lg hover:border-primary-200 cursor-pointer',
        className
      )}
      onClick={isClickable ? handleClick : undefined}
    >
      <CardBody className={sizeConfig.padding}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className={cn('text-neutral-500 mb-2', sizeConfig.nameText)}>
              {name}
            </p>
            <div className="flex items-baseline space-x-2">
              <p className={cn('text-neutral-900', sizeConfig.valueText)}>
                {value}
              </p>
              {showChange && change && (
                <div className="flex items-center">
                  <span
                    className={cn(
                      'font-medium rounded-full',
                      sizeConfig.changeText,
                      sizeConfig.changePadding,
                      getChangeColor()
                    )}
                  >
                    {getChangeIcon()} {change}
                  </span>
                </div>
              )}
            </div>
          </div>
          {showIcon && Icon && (
            <div className="flex-shrink-0 ml-3">
              <Icon className={cn('text-neutral-400', sizeConfig.iconSize)} />
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
};

export default AnalyticsCard;
