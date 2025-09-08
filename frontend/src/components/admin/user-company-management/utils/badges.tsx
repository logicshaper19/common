/**
 * Badge utilities for user and company management
 */
import React from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import {
  UserRole,
  CompanyType,
  SubscriptionTier,
  ComplianceStatus,
} from '../../../../types/admin';

export function getRoleBadge(role: UserRole) {
  const styles = {
    admin: 'bg-red-100 text-red-800',
    buyer: 'bg-blue-100 text-blue-800',
    seller: 'bg-green-100 text-green-800',
    viewer: 'bg-gray-100 text-gray-800',
    support: 'bg-purple-100 text-purple-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[role]}`}>
      {role.charAt(0).toUpperCase() + role.slice(1)}
    </span>
  );
}

export function getCompanyTypeBadge(type: CompanyType) {
  const styles = {
    brand: 'bg-purple-100 text-purple-800',
    processor: 'bg-blue-100 text-blue-800',
    originator: 'bg-green-100 text-green-800',
    trader: 'bg-yellow-100 text-yellow-800',
    plantation: 'bg-emerald-100 text-emerald-800',
    manufacturer: 'bg-orange-100 text-orange-800',
  };

  const labels = {
    brand: 'Brand',
    processor: 'Processor',
    originator: 'Originator',
    trader: 'Trader',
    plantation: 'Plantation',
    manufacturer: 'Manufacturer',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[type]}`}>
      {labels[type]}
    </span>
  );
}

export function getSubscriptionBadge(tier: SubscriptionTier) {
  const styles = {
    free: 'bg-gray-100 text-gray-800',
    basic: 'bg-blue-100 text-blue-800',
    premium: 'bg-purple-100 text-purple-800',
    enterprise: 'bg-yellow-100 text-yellow-800',
  };

  const labels = {
    free: 'Free',
    basic: 'Basic',
    premium: 'Premium',
    enterprise: 'Enterprise',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[tier]}`}>
      {labels[tier]}
    </span>
  );
}

export function getComplianceBadge(status: ComplianceStatus) {
  const config = {
    compliant: {
      style: 'bg-green-100 text-green-800',
      icon: CheckCircleIcon,
      label: 'Compliant',
    },
    non_compliant: {
      style: 'bg-red-100 text-red-800',
      icon: XCircleIcon,
      label: 'Non-Compliant',
    },
    pending_review: {
      style: 'bg-yellow-100 text-yellow-800',
      icon: ClockIcon,
      label: 'Pending Review',
    },
    warning: {
      style: 'bg-orange-100 text-orange-800',
      icon: ExclamationTriangleIcon,
      label: 'Warning',
    },
  };

  const { style, icon: Icon, label } = config[status];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style}`}>
      <Icon className="h-3 w-3 mr-1" />
      {label}
    </span>
  );
}

export function getStatusIcon(isActive: boolean) {
  return isActive ? (
    <CheckCircleIcon className="h-5 w-5 text-green-500" />
  ) : (
    <XCircleIcon className="h-5 w-5 text-red-500" />
  );
}

export function getTwoFactorBadge(hasTwoFactor: boolean) {
  return hasTwoFactor ? (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
      <ShieldCheckIcon className="h-3 w-3 mr-1" />
      2FA Enabled
    </span>
  ) : (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
      2FA Disabled
    </span>
  );
}

export function getVerificationBadge(isVerified: boolean) {
  return isVerified ? (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
      <CheckCircleIcon className="h-3 w-3 mr-1" />
      Verified
    </span>
  ) : (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
      Unverified
    </span>
  );
}
