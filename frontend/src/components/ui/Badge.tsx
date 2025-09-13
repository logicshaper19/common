/**
 * SEMA Design System - Badge Component
 * Reusable badge component for status indicators and labels
 */
import React, { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Badge variants
export type BadgeVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'error'
  | 'neutral'
  | 'outline';

// Badge sizes
export type BadgeSize = 'xs' | 'sm' | 'md' | 'lg';

// Badge props interface
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  removable?: boolean;
  onRemove?: () => void;
}

// Badge component
const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      className,
      variant = 'neutral',
      size = 'md',
      dot = false,
      removable = false,
      onRemove,
      children,
      ...props
    },
    ref
  ) => {
    // Base badge classes
    const baseClasses = [
      'inline-flex',
      'items-center',
      'font-medium',
      'rounded-full',
      'transition-colors',
      'duration-200',
    ];

    // Variant classes
    const variantClasses: Record<BadgeVariant, string[]> = {
      primary: [
        'bg-primary-100',
        'text-primary-800',
        'border-primary-200',
      ],
      secondary: [
        'bg-secondary-100',
        'text-secondary-800',
        'border-secondary-200',
      ],
      success: [
        'bg-success-100',
        'text-success-800',
        'border-success-200',
      ],
      warning: [
        'bg-warning-100',
        'text-warning-800',
        'border-warning-200',
      ],
      error: [
        'bg-error-100',
        'text-error-800',
        'border-error-200',
      ],
      neutral: [
        'bg-neutral-100',
        'text-neutral-800',
        'border-neutral-200',
      ],
      outline: [
        'bg-transparent',
        'text-neutral-700',
        'border-neutral-300',
      ],
    };

    // Size classes
    const sizeClasses: Record<BadgeSize, string[]> = {
      xs: ['px-1.5', 'py-0.5', 'text-xs'],
      sm: ['px-2', 'py-0.5', 'text-xs'],
      md: ['px-2.5', 'py-0.5', 'text-xs'],
      lg: ['px-3', 'py-1', 'text-sm'],
    };

    // Dot variant classes
    const dotClasses = dot ? ['pl-1.5'] : [];

    // Combine classes
    const badgeClasses = cn(
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      dotClasses,
      className
    );

    // Dot indicator
    const DotIndicator = () => (
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full mr-1.5',
          {
            'bg-primary-600': variant === 'primary',
            'bg-secondary-600': variant === 'secondary',
            'bg-success-600': variant === 'success',
            'bg-warning-600': variant === 'warning',
            'bg-error-600': variant === 'error',
            'bg-neutral-600': variant === 'neutral',
          }
        )}
      />
    );

    // Remove button
    const RemoveButton = () => (
      <button
        type="button"
        onClick={onRemove}
        className={cn(
          'ml-1 inline-flex items-center justify-center',
          'w-4 h-4 rounded-full',
          'hover:bg-black hover:bg-opacity-10',
          'focus:outline-none focus:bg-black focus:bg-opacity-10',
          'transition-colors duration-150'
        )}
      >
        <svg
          className="w-2.5 h-2.5"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    );

    return (
      <span ref={ref} className={badgeClasses} {...props}>
        {dot && <DotIndicator />}
        {children}
        {removable && <RemoveButton />}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
export { Badge };
