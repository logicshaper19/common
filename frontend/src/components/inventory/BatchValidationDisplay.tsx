import React from 'react';
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  totalQuantity: number;
  utilizationByBatch: Record<string, number>;
}

interface BatchValidationDisplayProps {
  validation: ValidationResult;
  targetQuantity?: number;
  className?: string;
}

const BatchValidationDisplay: React.FC<BatchValidationDisplayProps> = ({
  validation,
  targetQuantity,
  className = ''
}) => {
  const { isValid, errors, warnings, totalQuantity } = validation;

  if (errors.length === 0 && warnings.length === 0) {
    return (
      <div className={`flex items-center space-x-2 text-green-600 ${className}`}>
        <CheckCircle className="h-4 w-4" />
        <span className="text-sm font-medium">Batch selection is valid</span>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center space-x-2 mb-2">
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm font-medium text-red-800">
              {errors.length} Error{errors.length !== 1 ? 's' : ''}
            </span>
          </div>
          <ul className="space-y-1">
            {errors.map((error, index) => (
              <li key={index} className="text-sm text-red-700 flex items-start space-x-2">
                <span className="text-red-400 mt-0.5">•</span>
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <span className="text-sm font-medium text-amber-800">
              {warnings.length} Warning{warnings.length !== 1 ? 's' : ''}
            </span>
          </div>
          <ul className="space-y-1">
            {warnings.map((warning, index) => (
              <li key={index} className="text-sm text-amber-700 flex items-start space-x-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-center space-x-2 mb-2">
          <Info className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-blue-800">Selection Summary</span>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-blue-600">Total Selected:</span>
            <span className="ml-2 font-medium text-blue-900">
              {totalQuantity.toFixed(3)} kg
            </span>
          </div>
          {targetQuantity && (
            <div>
              <span className="text-blue-600">Target:</span>
              <span className="ml-2 font-medium text-blue-900">
                {targetQuantity.toFixed(3)} kg
              </span>
            </div>
          )}
          {targetQuantity && (
            <div className="col-span-2">
              <span className="text-blue-600">Difference:</span>
              <span className={`ml-2 font-medium ${
                Math.abs(totalQuantity - targetQuantity) < 0.001 
                  ? 'text-green-600' 
                  : totalQuantity > targetQuantity 
                  ? 'text-amber-600' 
                  : 'text-red-600'
              }`}>
                {totalQuantity > targetQuantity ? '+' : ''}
                {(totalQuantity - targetQuantity).toFixed(3)} kg
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Validation Status */}
      <div className={`flex items-center space-x-2 ${
        isValid ? 'text-green-600' : 'text-red-600'
      }`}>
        {isValid ? (
          <CheckCircle className="h-4 w-4" />
        ) : (
          <XCircle className="h-4 w-4" />
        )}
        <span className="text-sm font-medium">
          {isValid ? 'Ready to confirm' : 'Please fix errors before confirming'}
        </span>
      </div>
    </div>
  );
};

export default BatchValidationDisplay;
