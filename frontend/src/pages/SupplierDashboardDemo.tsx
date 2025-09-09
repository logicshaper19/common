/**
 * Supplier Dashboard Demo Page
 * Demo page to showcase the supplier requirements dashboard
 */
import React from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import SupplierRequirementsDashboard from '../components/supplier/SupplierRequirementsDashboard';

const SupplierDashboardDemo: React.FC = () => {
  const [selectedDemo, setSelectedDemo] = React.useState<{
    companyType: string;
    sectorId: string;
    title: string;
  }>({
    companyType: 'originator',
    sectorId: 'palm_oil',
    title: 'Palm Oil Mill (Originator)'
  });

  const demoOptions = [
    {
      companyType: 'originator',
      sectorId: 'palm_oil',
      title: 'Palm Oil Mill (Originator)',
      description: 'Tier 4 - Highest transparency requirements including coordinates, licenses, and environmental assessments'
    },
    {
      companyType: 'processor',
      sectorId: 'palm_oil',
      title: 'Palm Oil Processor',
      description: 'Tier 3 - Manufacturing licenses, safety certificates, and processing documentation'
    },
    {
      companyType: 'brand',
      sectorId: 'palm_oil',
      title: 'Consumer Brand (Palm Oil)',
      description: 'Tier 2 - Brand certifications and supply chain documentation'
    },
    {
      companyType: 'trader',
      sectorId: 'palm_oil',
      title: 'Palm Oil Trader',
      description: 'Tier 1 - Basic trading licenses and transaction records'
    },
    {
      companyType: 'originator',
      sectorId: 'apparel',
      title: 'Cotton Farm (Apparel)',
      description: 'Tier 4 - BCI certification, farm coordinates, and sustainable farming practices'
    },
    {
      companyType: 'processor',
      sectorId: 'apparel',
      title: 'Textile Manufacturer',
      description: 'Tier 3 - Manufacturing certifications, worker safety, and environmental compliance'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">Supplier Requirements Dashboard</h1>
            <p className="text-lg text-gray-600 mt-2">
              Interactive demo showing tier-specific requirements for different company types and sectors
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Demo Selector */}
        <Card className="mb-8">
          <CardHeader>
            <h2 className="text-xl font-semibold text-gray-900">Choose a Supplier Type</h2>
            <p className="text-sm text-gray-600">
              Select different company types and sectors to see how requirements change based on tier levels
            </p>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {demoOptions.map((option) => (
                <button
                  key={`${option.companyType}-${option.sectorId}`}
                  onClick={() => setSelectedDemo(option)}
                  className={`text-left p-4 rounded-lg border-2 transition-all ${
                    selectedDemo.companyType === option.companyType && 
                    selectedDemo.sectorId === option.sectorId
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <h3 className="font-medium text-gray-900 mb-2">{option.title}</h3>
                  <p className="text-sm text-gray-600">{option.description}</p>
                  <div className="mt-3 flex items-center space-x-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                      {option.companyType}
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 capitalize">
                      {option.sectorId.replace('_', ' ')}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Current Selection Info */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
            <h2 className="text-2xl font-bold mb-2">
              {selectedDemo.title}
            </h2>
            <p className="text-blue-100 mb-4">
              Viewing requirements dashboard for a {selectedDemo.companyType} in the {selectedDemo.sectorId.replace('_', ' ')} sector
            </p>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-white rounded-full"></div>
                <span>Company Type: {selectedDemo.companyType.charAt(0).toUpperCase() + selectedDemo.companyType.slice(1)}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-white rounded-full"></div>
                <span>Sector: {selectedDemo.sectorId.replace('_', ' ').charAt(0).toUpperCase() + selectedDemo.sectorId.replace('_', ' ').slice(1)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Requirements Dashboard */}
        <SupplierRequirementsDashboard
          companyType={selectedDemo.companyType}
          sectorId={selectedDemo.sectorId}
        />

        {/* Information Panel */}
        <Card className="mt-8">
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900">How It Works</h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-3">🏢 For Buyers (L'Oréal)</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Add suppliers with basic info (name, email, company type, sector)</li>
                  <li>• Set data sharing permissions</li>
                  <li>• No need to collect requirements during addition</li>
                  <li>• Suppliers handle their own requirements upload</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-3">📋 For Suppliers</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Log into supplier dashboard after being added</li>
                  <li>• View tier-specific requirements based on company type</li>
                  <li>• Upload documents, coordinates, and certifications</li>
                  <li>• Track transparency score and compliance status</li>
                </ul>
              </div>
            </div>
            
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">🎯 Tier-Based System Benefits</h4>
              <p className="text-sm text-blue-800">
                Each company type has different transparency requirements and scoring weights:
                <strong> Originators (100%)</strong> → <strong>Processors (80%)</strong> → <strong>Brands (60%)</strong> → <strong>Traders (40%)</strong>
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default SupplierDashboardDemo;
