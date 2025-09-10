/**
 * Originator Features Demo Page
 * Comprehensive demonstration of all originator-specific features
 */
import React, { useState } from 'react';
import {
  MapPinIcon,
  ShieldCheckIcon,
  BeakerIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import MapInput from '../components/origin/MapInput';
import OriginatorConfirmationForm from '../components/origin/OriginatorConfirmationForm';
import FarmInformationManager from '../components/origin/FarmInformationManager';
import CertificationManager from '../components/origin/CertificationManager';
import { useToast } from '../contexts/ToastContext';

interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  elevation?: number;
  timestamp?: string;
}

const OriginatorFeaturesDemo: React.FC = () => {
  const { showToast } = useToast();
  
  // State for demo
  const [activeDemo, setActiveDemo] = useState<string>('overview');
  const [coordinates, setCoordinates] = useState<GeographicCoordinates>({
    latitude: -2.5489,
    longitude: 118.0149
  });

  // Demo sections
  const demoSections = [
    {
      id: 'overview',
      title: 'Overview',
      icon: <ChartBarIcon className="h-5 w-5" />,
      description: 'Complete originator feature overview'
    },
    {
      id: 'map-input',
      title: 'GPS Coordinates',
      icon: <MapPinIcon className="h-5 w-5" />,
      description: 'Interactive GPS coordinate capture'
    },
    {
      id: 'origin-form',
      title: 'Origin Data Capture',
      icon: <DocumentTextIcon className="h-5 w-5" />,
      description: 'Complete origin data form'
    },
    {
      id: 'farm-management',
      title: 'Farm Management',
      icon: <BuildingOfficeIcon className="h-5 w-5" />,
      description: 'Farm information management'
    },
    {
      id: 'certifications',
      title: 'Certifications',
      icon: <ShieldCheckIcon className="h-5 w-5" />,
      description: 'Certification management system'
    }
  ];

  // Handle origin data submission
  const handleOriginDataSubmit = (originData: any) => {
    console.log('Origin data submitted:', originData);
    showToast({
      type: 'success',
      title: 'Origin Data Captured',
      message: 'Complete origin information has been successfully captured and validated.'
    });
  };

  // Render demo content
  const renderDemoContent = () => {
    switch (activeDemo) {
      case 'map-input':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">GPS Coordinate Input</h2>
              <p className="text-gray-600">
                Interactive map component with GPS validation and regional detection.
              </p>
            </div>
            
            <MapInput
              value={coordinates}
              onChange={setCoordinates}
              required
              validationRegion="southeast_asia"
            />
            
            <Card>
              <CardHeader title="Current Coordinates" />
              <CardBody>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Latitude:</span> {coordinates.latitude}
                  </div>
                  <div>
                    <span className="font-medium">Longitude:</span> {coordinates.longitude}
                  </div>
                  {coordinates.accuracy && (
                    <div>
                      <span className="font-medium">Accuracy:</span> {coordinates.accuracy.toFixed(1)}m
                    </div>
                  )}
                  {coordinates.timestamp && (
                    <div>
                      <span className="font-medium">Captured:</span> {new Date(coordinates.timestamp).toLocaleString()}
                    </div>
                  )}
                </div>
              </CardBody>
            </Card>
          </div>
        );

      case 'origin-form':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Origin Data Capture Form</h2>
              <p className="text-gray-600">
                Comprehensive form for capturing all origin-related information.
              </p>
            </div>
            
            <OriginatorConfirmationForm
              purchaseOrderId="DEMO-PO-001"
              productType="Fresh Fruit Bunches"
              onSubmit={handleOriginDataSubmit}
              onCancel={() => {
                showToast({
                  type: 'info',
                  title: 'Demo Cancelled',
                  message: 'Origin data capture demo was cancelled.'
                });
              }}
            />
          </div>
        );

      case 'farm-management':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Farm Information Management</h2>
              <p className="text-gray-600">
                Complete farm data management with CRUD operations.
              </p>
            </div>
            
            <FarmInformationManager companyId="demo-company" />
          </div>
        );

      case 'certifications':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Certification Management</h2>
              <p className="text-gray-600">
                Comprehensive certification tracking with renewal alerts.
              </p>
            </div>
            
            <CertificationManager companyId="demo-company" />
          </div>
        );

      case 'overview':
      default:
        return (
          <div className="space-y-8">
            {/* Header */}
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Originator Features Demo
              </h1>
              <p className="text-lg text-gray-600 max-w-3xl mx-auto">
                Comprehensive demonstration of all originator-specific features including GPS coordinate capture, 
                origin data forms, farm management, and certification tracking.
              </p>
            </div>

            {/* Feature Status */}
            <Card>
              <CardHeader title="Implementation Status" subtitle="All originator features are fully implemented" />
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium text-green-800">GPS Coordinate Input</div>
                      <div className="text-sm text-green-600">Interactive map with validation</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium text-green-800">Origin Data Capture</div>
                      <div className="text-sm text-green-600">Complete form with validation</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium text-green-800">PO Confirmation Flow</div>
                      <div className="text-sm text-green-600">Enhanced with originator detection</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium text-green-800">Farm Management</div>
                      <div className="text-sm text-green-600">Complete CRUD operations</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium text-green-800">Certification Management</div>
                      <div className="text-sm text-green-600">Status tracking & renewal alerts</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    <div>
                      <div className="font-medium text-green-800">Originator Dashboard</div>
                      <div className="text-sm text-green-600">Specialized analytics & metrics</div>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Key Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader 
                  title="Core Capabilities" 
                  icon={<BeakerIcon className="h-5 w-5" />}
                />
                <CardBody>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>GPS coordinate input with accuracy validation</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Harvest date recording with freshness validation</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Farm identification and metadata tracking</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Batch number assignment and tracking</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Quality parameters (oil content, moisture, FFA)</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Certification management (RSPO, NDPE, ISPO, etc.)</span>
                    </li>
                  </ul>
                </CardBody>
              </Card>

              <Card>
                <CardHeader 
                  title="Enhanced Features" 
                  icon={<ChartBarIcon className="h-5 w-5" />}
                />
                <CardBody>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Regional detection and boundary validation</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Interactive map integration (placeholder)</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Current location detection</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Address geocoding capabilities</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Plantation type classification</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      <span>Cultivation methods tracking</span>
                    </li>
                  </ul>
                </CardBody>
              </Card>
            </div>

            {/* Integration Status */}
            <Card>
              <CardHeader title="Integration Status" />
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                      <span className="font-medium">Purchase Order Confirmation</span>
                    </div>
                    <Badge variant="success">Integrated</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                      <span className="font-medium">Navigation & Routing</span>
                    </div>
                    <Badge variant="success">Integrated</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                      <span className="font-medium">User Authentication</span>
                    </div>
                    <Badge variant="success">Integrated</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
                      <span className="font-medium">Real API Integration</span>
                    </div>
                    <Badge variant="warning">Mock Data</Badge>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Demo Sections</h2>
            <nav className="space-y-2">
              {demoSections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveDemo(section.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeDemo === section.id
                      ? 'bg-primary-50 text-primary-700 border border-primary-200'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {section.icon}
                  <div>
                    <div className="font-medium">{section.title}</div>
                    <div className="text-xs text-gray-500">{section.description}</div>
                  </div>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-8">
          {renderDemoContent()}
        </div>
      </div>
    </div>
  );
};

export default OriginatorFeaturesDemo;
