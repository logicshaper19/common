/**
 * SEMA Design System - Card Component
 * Reusable card component with header, body, and footer sections
 */
import React, { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

// Card props interface
export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

// Card component
const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'default',
      padding = 'md',
      children,
      ...props
    },
    ref
  ) => {
    // Base card classes
    const baseClasses = [
      'bg-white',
      'rounded-xl',
      'transition-shadow',
      'duration-200',
    ];

    // Variant classes
    const variantClasses: Record<string, string[]> = {
      default: ['border', 'border-neutral-200', 'shadow-sm'],
      outlined: ['border-2', 'border-neutral-300'],
      elevated: ['shadow-lg', 'hover:shadow-xl'],
    };

    // Padding classes
    const paddingClasses: Record<string, string> = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    // Combine classes
    const cardClasses = cn(
      baseClasses,
      variantClasses[variant],
      paddingClasses[padding],
      className
    );

    return (
      <div ref={ref} className={cardClasses} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card Header component
export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  (
    {
      className,
      title,
      subtitle,
      action,
      children,
      ...props
    },
    ref
  ) => {
    const headerClasses = cn(
      'flex items-center justify-between',
      'px-6 py-4',
      'border-b border-neutral-200',
      className
    );

    return (
      <div ref={ref} className={headerClasses} {...props}>
        <div className="min-w-0 flex-1">
          {title && (
            <h3 className="text-lg font-semibold text-neutral-900 truncate">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-neutral-500 mt-1">
              {subtitle}
            </p>
          )}
          {children}
        </div>
        {action && (
          <div className="ml-4 flex-shrink-0">
            {action}
          </div>
        )}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// Card Title component
export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  (
    {
      className,
      as: Component = 'h3',
      children,
      ...props
    },
    ref
  ) => {
    const titleClasses = cn(
      'text-lg font-semibold text-neutral-900',
      className
    );

    return (
      <Component ref={ref} className={titleClasses} {...props}>
        {children}
      </Component>
    );
  }
);

CardTitle.displayName = 'CardTitle';

// Card Body component
export interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const CardBody = forwardRef<HTMLDivElement, CardBodyProps>(
  (
    {
      className,
      padding = 'md',
      children,
      ...props
    },
    ref
  ) => {
    // Padding classes
    const paddingClasses: Record<string, string> = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    const bodyClasses = cn(
      paddingClasses[padding],
      className
    );

    return (
      <div ref={ref} className={bodyClasses} {...props}>
        {children}
      </div>
    );
  }
);

CardBody.displayName = 'CardBody';

// Card Footer component
export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  justify?: 'start' | 'center' | 'end' | 'between';
}

const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  (
    {
      className,
      justify = 'end',
      children,
      ...props
    },
    ref
  ) => {
    // Justify classes
    const justifyClasses: Record<string, string> = {
      start: 'justify-start',
      center: 'justify-center',
      end: 'justify-end',
      between: 'justify-between',
    };

    const footerClasses = cn(
      'flex items-center',
      'px-6 py-4',
      'border-t border-neutral-200',
      'bg-neutral-50',
      'rounded-b-xl',
      justifyClasses[justify],
      className
    );

    return (
      <div ref={ref} className={footerClasses} {...props}>
        {children}
      </div>
    );
  }
);

CardFooter.displayName = 'CardFooter';

// Export all components
export { Card, CardHeader, CardTitle, CardBody, CardFooter };
export default Card;
