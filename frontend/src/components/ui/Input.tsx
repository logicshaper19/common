/**
 * SEMA Design System - Input Component
 * Reusable input component with validation states and icons
 */
import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Input variants
export type InputVariant = 'default' | 'error' | 'success';

// Input sizes
export type InputSize = 'sm' | 'md' | 'lg';

// Input props interface
export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: InputVariant;
  size?: InputSize;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  label?: string;
  helperText?: string;
  errorMessage?: string;
  isRequired?: boolean;
}

// Input component
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      leftIcon,
      rightIcon,
      label,
      helperText,
      errorMessage,
      isRequired = false,
      id,
      ...props
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    
    // Determine actual variant based on error state
    const actualVariant = errorMessage ? 'error' : variant;

    // Base input classes
    const baseClasses = [
      'block',
      'w-full',
      'rounded-lg',
      'border',
      'bg-white',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-0',
      'disabled:bg-neutral-50',
      'disabled:text-neutral-500',
      'disabled:cursor-not-allowed',
      'placeholder:text-neutral-400',
    ];

    // Variant classes
    const variantClasses: Record<InputVariant, string[]> = {
      default: [
        'border-neutral-300',
        'text-neutral-900',
        'focus:border-primary-500',
        'focus:ring-primary-500',
      ],
      error: [
        'border-error-300',
        'text-neutral-900',
        'focus:border-error-500',
        'focus:ring-error-500',
      ],
      success: [
        'border-success-300',
        'text-neutral-900',
        'focus:border-success-500',
        'focus:ring-success-500',
      ],
    };

    // Size classes
    const sizeClasses: Record<InputSize, string[]> = {
      sm: ['px-3', 'py-1.5', 'text-sm'],
      md: ['px-3', 'py-2', 'text-sm'],
      lg: ['px-4', 'py-3', 'text-base'],
    };

    // Icon padding adjustments
    const iconPaddingClasses = {
      left: leftIcon ? (size === 'lg' ? 'pl-10' : 'pl-9') : '',
      right: rightIcon ? (size === 'lg' ? 'pr-10' : 'pr-9') : '',
    };

    // Combine input classes
    const inputClasses = cn(
      baseClasses,
      variantClasses[actualVariant],
      sizeClasses[size],
      iconPaddingClasses.left,
      iconPaddingClasses.right,
      className
    );

    // Icon wrapper classes
    const iconWrapperClasses = 'absolute inset-y-0 flex items-center pointer-events-none';
    const leftIconClasses = cn(iconWrapperClasses, 'left-0 pl-3');
    const rightIconClasses = cn('absolute inset-y-0 flex items-center right-0 pr-3');

    // Icon size based on input size
    const iconSize = size === 'lg' ? 'h-5 w-5' : 'h-4 w-4';

    return (
      <div className="w-full">
        {/* Label */}
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-neutral-700 mb-1"
          >
            {label}
            {isRequired && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}

        {/* Input container */}
        <div className="relative">
          {/* Left icon */}
          {leftIcon && (
            <div className={leftIconClasses}>
              <span className={cn('text-neutral-400', iconSize)}>
                {leftIcon}
              </span>
            </div>
          )}

          {/* Input field */}
          <input
            ref={ref}
            id={inputId}
            className={inputClasses}
            onPaste={(e) => {
              // Allow normal paste behavior - no intervention needed
            }}
            {...props}
          />

          {/* Right icon */}
          {rightIcon && (
            <div className={rightIconClasses}>
              <span className={cn('text-neutral-400', iconSize, 'pointer-events-auto')}>
                {rightIcon}
              </span>
            </div>
          )}
        </div>

        {/* Helper text or error message */}
        {(helperText || errorMessage) && (
          <p
            className={cn(
              'mt-1 text-xs',
              errorMessage ? 'text-error-600' : 'text-neutral-500'
            )}
          >
            {errorMessage || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
