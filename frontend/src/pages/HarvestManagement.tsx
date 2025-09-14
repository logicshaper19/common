import React from 'react';
import HarvestManager from '../components/harvest/HarvestManager';
import { useAuth } from '../contexts/AuthContext';

const HarvestManagement: React.FC = () => {
  const { user } = useAuth();

  if (!user?.company?.id) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600">You need to be associated with a company to access harvest management.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <HarvestManager companyId={user.company.id} />
      </div>
    </div>
  );
};

export default HarvestManagement;
