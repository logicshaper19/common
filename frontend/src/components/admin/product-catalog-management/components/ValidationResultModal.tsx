/**
 * Product validation result modal component
 */
import React from 'react';
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { ProductValidationResult } from '../../../../types/admin';

interface ValidationResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  validationResult: ProductValidationResult | null;
}

export function ValidationResultModal({
  isOpen,
  onClose,
  validationResult,
}: ValidationResultModalProps) {
  if (!isOpen || !validationResult) return null;

  const getValidationIcon = (isValid: boolean, hasWarnings: boolean) => {
    if (isValid && !hasWarnings) {
      return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
    }
    if (isValid && hasWarnings) {
      return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />;
    }
    return <XCircleIcon className="h-6 w-6 text-red-500" />;
  };

  const getValidationStatus = (isValid: boolean, hasWarnings: boolean) => {
    if (isValid && !hasWarnings) return 'Valid';
    if (isValid && hasWarnings) return 'Valid with Warnings';
    return 'Invalid';
  };

  const getValidationColor = (isValid: boolean, hasWarnings: boolean) => {
    if (isValid && !hasWarnings) return 'text-green-800';
    if (isValid && hasWarnings) return 'text-yellow-800';
    return 'text-red-800';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">Validation Results</h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Overall Status */}
              <div className="flex items-center space-x-3">
                {getValidationIcon(validationResult.is_valid, validationResult.warnings.length > 0)}
                <div>
                  <h4 className={`text-lg font-medium ${getValidationColor(validationResult.is_valid, validationResult.warnings.length > 0)}`}>
                    {getValidationStatus(validationResult.is_valid, validationResult.warnings.length > 0)}
                  </h4>
                  <p className="text-sm text-gray-500">
                    Product validation completed
                  </p>
                </div>
              </div>

              {/* Errors */}
              {validationResult.errors.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-800 mb-3 flex items-center">
                    <XCircleIcon className="h-4 w-4 mr-2" />
                    Errors ({validationResult.errors.length})
                  </h4>
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <ul className="space-y-1">
                      {validationResult.errors.map((error, index) => (
                        <li key={index} className="text-sm text-red-700">
                          • {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Warnings */}
              {validationResult.warnings.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-yellow-800 mb-3 flex items-center">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                    Warnings ({validationResult.warnings.length})
                  </h4>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <ul className="space-y-1">
                      {validationResult.warnings.map((warning, index) => (
                        <li key={index} className="text-sm text-yellow-700">
                          • {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Success Message */}
              {validationResult.is_valid && validationResult.warnings.length === 0 && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3">
                  <p className="text-sm text-green-700">
                    ✓ Product validation passed successfully with no issues found.
                  </p>
                </div>
              )}

              {/* Validation Details */}
              {validationResult.details && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Validation Details</h4>
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                      {JSON.stringify(validationResult.details, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
