/**
 * SEMA Design System - Button Component
 * Reusable button component with multiple variants and sizes
 */
import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Button variants
export type ButtonVariant = 
  | 'primary' 
  | 'secondary' 
  | 'success' 
  | 'warning' 
  | 'error' 
  | 'ghost' 
  | 'outline'
  | 'link';

// Button sizes
export type ButtonSize = 'sm' | 'md' | 'lg';

// Button props interface
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

// Button component
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    // Base button classes
    const baseClasses = [
      'inline-flex',
      'items-center',
      'justify-center',
      'font-medium',
      'rounded-lg',
      'border',
      'transition-all',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'disabled:opacity-50',
      'disabled:cursor-not-allowed',
      'disabled:pointer-events-none',
    ];

    // Variant classes
    const variantClasses: Record<ButtonVariant, string[]> = {
      primary: [
        'bg-primary-600',
        'text-white',
        'border-primary-600',
        'hover:bg-primary-700',
        'hover:border-primary-700',
        'focus:ring-primary-500',
        'active:bg-primary-800',
      ],
      secondary: [
        'bg-white',
        'text-neutral-700',
        'border-neutral-300',
        'hover:bg-neutral-50',
        'hover:border-neutral-400',
        'focus:ring-primary-500',
        'active:bg-neutral-100',
      ],
      success: [
        'bg-success-600',
        'text-white',
        'border-success-600',
        'hover:bg-success-700',
        'hover:border-success-700',
        'focus:ring-success-500',
        'active:bg-success-800',
      ],
      warning: [
        'bg-warning-600',
        'text-white',
        'border-warning-600',
        'hover:bg-warning-700',
        'hover:border-warning-700',
        'focus:ring-warning-500',
        'active:bg-warning-800',
      ],
      error: [
        'bg-error-600',
        'text-white',
        'border-error-600',
        'hover:bg-error-700',
        'hover:border-error-700',
        'focus:ring-error-500',
        'active:bg-error-800',
      ],
      ghost: [
        'bg-transparent',
        'text-neutral-700',
        'border-transparent',
        'hover:bg-neutral-100',
        'hover:text-neutral-900',
        'focus:ring-primary-500',
        'active:bg-neutral-200',
      ],
      outline: [
        'bg-transparent',
        'text-primary-600',
        'border-primary-600',
        'hover:bg-primary-50',
        'hover:text-primary-700',
        'hover:border-primary-700',
        'focus:ring-primary-500',
        'active:bg-primary-100',
      ],
      link: [
        'bg-transparent',
        'text-primary-600',
        'border-transparent',
        'hover:text-primary-700',
        'hover:underline',
        'focus:ring-primary-500',
        'active:text-primary-800',
        'p-0',
        'h-auto',
      ],
    };

    // Size classes
    const sizeClasses: Record<ButtonSize, string[]> = {
      sm: ['px-3', 'py-1.5', 'text-sm', 'h-8'],
      md: ['px-4', 'py-2', 'text-sm', 'h-10'],
      lg: ['px-6', 'py-3', 'text-base', 'h-12'],
    };

    // Full width class
    const fullWidthClass = fullWidth ? 'w-full' : '';

    // Combine all classes
    const buttonClasses = cn(
      baseClasses,
      variantClasses[variant],
      variant !== 'link' ? sizeClasses[size] : [],
      fullWidthClass,
      className
    );

    // Loading spinner component
    const LoadingSpinner = () => (
      <svg
        className="animate-spin -ml-1 mr-2 h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    );

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <LoadingSpinner />}
        {!isLoading && leftIcon && (
          <span className="mr-2 flex-shrink-0">{leftIcon}</span>
        )}
        {children}
        {!isLoading && rightIcon && (
          <span className="ml-2 flex-shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
