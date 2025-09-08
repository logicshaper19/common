/**
 * Badge utilities for product catalog management
 */
import React from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { ProductCategory, ProductStatus } from '../../../../types/admin';

export function getCategoryBadge(category: ProductCategory) {
  const styles = {
    raw_material: 'bg-green-100 text-green-800',
    intermediate_product: 'bg-blue-100 text-blue-800',
    finished_product: 'bg-purple-100 text-purple-800',
    packaging: 'bg-yellow-100 text-yellow-800',
    service: 'bg-gray-100 text-gray-800',
    component: 'bg-orange-100 text-orange-800',
  };

  const labels = {
    raw_material: 'Raw Material',
    intermediate_product: 'Intermediate Product',
    finished_product: 'Finished Product',
    packaging: 'Packaging',
    service: 'Service',
    component: 'Component',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[category]}`}>
      {labels[category]}
    </span>
  );
}

export function getStatusBadge(status: ProductStatus) {
  const config = {
    active: {
      style: 'bg-green-100 text-green-800',
      icon: CheckCircleIcon,
      label: 'Active',
    },
    inactive: {
      style: 'bg-gray-100 text-gray-800',
      icon: XCircleIcon,
      label: 'Inactive',
    },
    pending_approval: {
      style: 'bg-yellow-100 text-yellow-800',
      icon: ClockIcon,
      label: 'Pending Approval',
    },
    deprecated: {
      style: 'bg-red-100 text-red-800',
      icon: ExclamationTriangleIcon,
      label: 'Deprecated',
    },
  };

  // Fallback to 'active' if status is undefined or not in config
  const statusConfig = config[status] || config.active;
  const { style, icon: Icon, label } = statusConfig;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style}`}>
      <Icon className="h-3 w-3 mr-1" />
      {label}
    </span>
  );
}

export function getValidationBadge(isValid: boolean, hasWarnings: boolean = false) {
  if (isValid && !hasWarnings) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        <CheckCircleIcon className="h-3 w-3 mr-1" />
        Valid
      </span>
    );
  }

  if (isValid && hasWarnings) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
        Valid (Warnings)
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
      <XCircleIcon className="h-3 w-3 mr-1" />
      Invalid
    </span>
  );
}

export function getCompositionBadge(canHaveComposition: boolean) {
  return canHaveComposition ? (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
      Composition
    </span>
  ) : null;
}

export function getUsageBadge(usageCount: number) {
  let style = 'bg-gray-100 text-gray-800';
  let label = 'Unused';

  if (usageCount > 100) {
    style = 'bg-green-100 text-green-800';
    label = 'High Usage';
  } else if (usageCount > 10) {
    style = 'bg-blue-100 text-blue-800';
    label = 'Medium Usage';
  } else if (usageCount > 0) {
    style = 'bg-yellow-100 text-yellow-800';
    label = 'Low Usage';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style}`}>
      {label} ({usageCount})
    </span>
  );
}
