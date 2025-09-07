/**
 * Compliance Page
 * Following the project plan: Complete compliance management interface
 */
import React from 'react';
import { ComplianceDashboard } from '../components/compliance/ComplianceDashboard';

export const CompliancePage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Compliance Management
        </h1>
        <p className="text-gray-600">
          Monitor and manage supply chain compliance across all purchase orders and regulations.
        </p>
      </div>
      
      <ComplianceDashboard />
    </div>
  );
};
