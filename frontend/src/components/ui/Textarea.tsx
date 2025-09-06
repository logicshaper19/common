/**
 * SEMA Design System - Textarea Component
 * Reusable textarea component with validation states
 */
import React, { TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Textarea variants
export type TextareaVariant = 'default' | 'error' | 'success';

// Textarea sizes
export type TextareaSize = 'sm' | 'md' | 'lg';

// Textarea props interface
export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: TextareaVariant;
  size?: TextareaSize;
  label?: string;
  helperText?: string;
  errorMessage?: string;
  isRequired?: boolean;
}

// Textarea component
const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      label,
      helperText,
      errorMessage,
      isRequired,
      rows = 3,
      ...props
    },
    ref
  ) => {
    const hasError = variant === 'error' || !!errorMessage;
    const hasSuccess = variant === 'success';

    // Size classes
    const sizeClasses = {
      sm: 'px-2 py-1 text-sm',
      md: 'px-3 py-2 text-sm',
      lg: 'px-4 py-3 text-base',
    };

    // Variant classes
    const variantClasses = {
      default: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
      error: 'border-red-300 focus:border-red-500 focus:ring-red-500',
      success: 'border-green-300 focus:border-green-500 focus:ring-green-500',
    };

    const textareaClasses = cn(
      // Base styles
      'flex w-full rounded-md border bg-white text-gray-900 shadow-sm transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      'placeholder:text-gray-500',
      'resize-vertical',
      // Size styles
      sizeClasses[size],
      // Variant styles
      hasError ? variantClasses.error : hasSuccess ? variantClasses.success : variantClasses.default,
      className
    );

    return (
      <div className="space-y-1">
        {label && (
          <label className="block text-sm font-medium text-gray-700">
            {label}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        
        <textarea
          ref={ref}
          className={textareaClasses}
          rows={rows}
          {...props}
        />

        {(helperText || errorMessage) && (
          <p className={cn(
            'text-xs',
            hasError ? 'text-red-600' : 'text-gray-500'
          )}>
            {errorMessage || helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Textarea;
