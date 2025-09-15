/**
 * SEMA Design System - Label Component
 * Reusable label component for form inputs
 */
import React, { LabelHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Label props interface
export interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
  error?: boolean;
}

// Label component
const Label = forwardRef<HTMLLabelElement, LabelProps>(
  (
    {
      className,
      required = false,
      error = false,
      children,
      ...props
    },
    ref
  ) => {
    const labelClasses = cn(
      'block text-sm font-medium transition-colors duration-200',
      error ? 'text-error-600' : 'text-neutral-700',
      className
    );

    return (
      <label ref={ref} className={labelClasses} {...props}>
        {children}
        {required && <span className="text-error-500 ml-1">*</span>}
      </label>
    );
  }
);

Label.displayName = 'Label';

export default Label;
export { Label };
