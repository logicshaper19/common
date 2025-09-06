/**
 * SEMA Design System - Select Component
 * Reusable select component with validation states
 */
import React, { SelectHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Select variants
export type SelectVariant = 'default' | 'error' | 'success';

// Select sizes
export type SelectSize = 'sm' | 'md' | 'lg';

// Option interface
export interface SelectOption {
  label: string;
  value: string;
}

// Select props interface
export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  variant?: SelectVariant;
  size?: SelectSize;
  label?: string;
  helperText?: string;
  errorMessage?: string;
  isRequired?: boolean;
  options: SelectOption[];
}

// Select component
const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      label,
      helperText,
      errorMessage,
      isRequired,
      options,
      ...props
    },
    ref
  ) => {
    const hasError = variant === 'error' || !!errorMessage;
    const hasSuccess = variant === 'success';

    // Size classes
    const sizeClasses = {
      sm: 'h-8 px-2 text-sm',
      md: 'h-10 px-3 text-sm',
      lg: 'h-12 px-4 text-base',
    };

    // Variant classes
    const variantClasses = {
      default: 'border-neutral-300 focus:border-primary-500 focus:ring-primary-500',
      error: 'border-error-300 focus:border-error-500 focus:ring-error-500',
      success: 'border-success-300 focus:border-success-500 focus:ring-success-500',
    };

    const selectClasses = cn(
      // Base styles
      'flex w-full rounded-md border bg-white text-neutral-900 shadow-sm transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      'placeholder:text-neutral-500',
      // Size styles
      sizeClasses[size],
      // Variant styles
      hasError ? variantClasses.error : hasSuccess ? variantClasses.success : variantClasses.default,
      className
    );

    return (
      <div className="space-y-1">
        {label && (
          <label className="block text-sm font-medium text-neutral-700">
            {label}
            {isRequired && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        
        <select
          ref={ref}
          className={selectClasses}
          {...props}
        >
          <option value="">Select an option...</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {(helperText || errorMessage) && (
          <p className={cn(
            'text-xs',
            hasError ? 'text-error-600' : 'text-neutral-500'
          )}>
            {errorMessage || helperText}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export default Select;
