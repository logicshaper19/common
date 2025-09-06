/**
 * Password Strength Indicator Component
 * Shows password strength and provides helpful guidance
 */
import React from 'react';
import { cn } from '../../lib/utils';

interface PasswordStrengthIndicatorProps {
  password: string;
  showGuidance?: boolean;
  className?: string;
}

interface StrengthCheck {
  label: string;
  test: (password: string) => boolean;
  description: string;
}

const strengthChecks: StrengthCheck[] = [
  {
    label: 'At least 8 characters',
    test: (password) => password.length >= 8,
    description: 'Use at least 8 characters for better security'
  },
  {
    label: 'Contains uppercase letter',
    test: (password) => /[A-Z]/.test(password),
    description: 'Include at least one uppercase letter (A-Z)'
  },
  {
    label: 'Contains lowercase letter',
    test: (password) => /[a-z]/.test(password),
    description: 'Include at least one lowercase letter (a-z)'
  },
  {
    label: 'Contains number',
    test: (password) => /\d/.test(password),
    description: 'Include at least one number (0-9)'
  },
  {
    label: 'Contains special character',
    test: (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password),
    description: 'Include at least one special character (!@#$%^&*)'
  }
];

const PasswordStrengthIndicator: React.FC<PasswordStrengthIndicatorProps> = ({
  password,
  showGuidance = true,
  className
}) => {
  const passedChecks = strengthChecks.filter(check => check.test(password));
  const strengthPercentage = (passedChecks.length / strengthChecks.length) * 100;
  
  const getStrengthLevel = () => {
    if (strengthPercentage >= 100) return { label: 'Very Strong', color: 'success' };
    if (strengthPercentage >= 80) return { label: 'Strong', color: 'success' };
    if (strengthPercentage >= 60) return { label: 'Good', color: 'warning' };
    if (strengthPercentage >= 40) return { label: 'Fair', color: 'warning' };
    if (strengthPercentage >= 20) return { label: 'Weak', color: 'error' };
    return { label: 'Very Weak', color: 'error' };
  };

  const strength = getStrengthLevel();

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'success':
        return {
          bar: 'bg-success-500',
          text: 'text-success-700',
          bg: 'bg-success-50'
        };
      case 'warning':
        return {
          bar: 'bg-warning-500',
          text: 'text-warning-700',
          bg: 'bg-warning-50'
        };
      case 'error':
        return {
          bar: 'bg-error-500',
          text: 'text-error-700',
          bg: 'bg-error-50'
        };
      default:
        return {
          bar: 'bg-neutral-300',
          text: 'text-neutral-600',
          bg: 'bg-neutral-50'
        };
    }
  };

  const colors = getColorClasses(strength.color);

  if (!password) return null;

  return (
    <div className={cn('space-y-3', className)}>
      {/* Strength bar and label */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-neutral-700">
            Password Strength
          </span>
          <span className={cn('text-sm font-medium', colors.text)}>
            {strength.label}
          </span>
        </div>
        
        <div className="w-full bg-neutral-200 rounded-full h-2">
          <div
            className={cn('h-2 rounded-full transition-all duration-300', colors.bar)}
            style={{ width: `${strengthPercentage}%` }}
          />
        </div>
      </div>

      {/* Guidance checklist */}
      {showGuidance && (
        <div className={cn('rounded-lg p-3 border', colors.bg, 
          strength.color === 'success' ? 'border-success-200' :
          strength.color === 'warning' ? 'border-warning-200' :
          'border-error-200'
        )}>
          <h4 className="text-sm font-medium text-neutral-800 mb-2">
            Password Requirements:
          </h4>
          <ul className="space-y-1">
            {strengthChecks.map((check, index) => {
              const passed = check.test(password);
              return (
                <li key={index} className="flex items-center text-xs">
                  <div className={cn(
                    'w-4 h-4 rounded-full flex items-center justify-center mr-2 flex-shrink-0',
                    passed 
                      ? 'bg-success-100 text-success-600' 
                      : 'bg-neutral-100 text-neutral-400'
                  )}>
                    {passed ? (
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <span className={cn(
                    passed ? 'text-success-700' : 'text-neutral-600'
                  )}>
                    {check.label}
                  </span>
                </li>
              );
            })}
          </ul>
          
          {strengthPercentage < 100 && (
            <div className="mt-2 pt-2 border-t border-neutral-200">
              <p className="text-xs text-neutral-600">
                💡 <strong>Tip:</strong> Use a mix of letters, numbers, and symbols for a stronger password.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PasswordStrengthIndicator;