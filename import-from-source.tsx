import React from 'react';

// Import directly from source files (better for development)
// This bypasses any build issues and gives you direct access to the components

// You can import components like this:
// import { Button } from '../semamvp-1/sema-design-system/src/components/Button';
// import { Card } from '../semamvp-1/sema-design-system/src/components/Card';
// import { Badge } from '../semamvp-1/sema-design-system/src/components/Badge';

// Or create a local import helper
const DesignSystemPath = '../semamvp-1/sema-design-system/src';

// Example usage component
export default function SupplyChainDashboard() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Common Platform - Supply Chain Transparency
        </h1>
        
        {/* You can use regular HTML/CSS classes for now */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Purchase Orders Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Purchase Orders</h2>
              <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
                Active
              </span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total POs:</span>
                <span className="font-medium">24</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pending:</span>
                <span className="font-medium text-orange-600">8</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Confirmed:</span>
                <span className="font-medium text-green-600">16</span>
              </div>
            </div>
            <button className="w-full mt-4 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
              View All POs
            </button>
          </div>
          
          {/* Transparency Score Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Transparency Score</h2>
              <span className="bg-green-100 text-green-800 text-sm font-medium px-2.5 py-0.5 rounded">
                Good
              </span>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">85%</div>
              <p className="text-gray-600 text-sm">Supply Chain Visibility</p>
            </div>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>To Mill (TTM):</span>
                <span className="font-medium">92%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>To Plantation (TTP):</span>
                <span className="font-medium">78%</span>
              </div>
            </div>
            <button className="w-full mt-4 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors">
              View Details
            </button>
          </div>
          
          {/* Suppliers Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Suppliers</h2>
              <span className="bg-purple-100 text-purple-800 text-sm font-medium px-2.5 py-0.5 rounded">
                Network
              </span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Connected:</span>
                <span className="font-medium">12</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pending Invites:</span>
                <span className="font-medium text-orange-600">3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Onboarding:</span>
                <span className="font-medium text-blue-600">2</span>
              </div>
            </div>
            <button className="w-full mt-4 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition-colors">
              Manage Suppliers
            </button>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="mt-8 flex gap-4 flex-wrap">
          <button className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors font-medium">
            Create New PO
          </button>
          <button className="bg-gray-200 text-gray-800 px-6 py-3 rounded-md hover:bg-gray-300 transition-colors font-medium">
            Export Data
          </button>
          <button className="bg-green-600 text-white px-6 py-3 rounded-md hover:bg-green-700 transition-colors font-medium">
            Invite Supplier
          </button>
        </div>
      </div>
    </div>
  );
}
