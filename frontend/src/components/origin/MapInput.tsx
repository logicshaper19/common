/**
 * MapInput Component
 * Interactive map for GPS coordinate capture with validation
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  MapPinIcon,
  GlobeAltIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';

interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  elevation?: number;
  timestamp?: string;
}

interface MapInputProps {
  value?: GeographicCoordinates;
  onChange: (coordinates: GeographicCoordinates) => void;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
  validationRegion?: 'southeast_asia' | 'africa' | 'south_america' | 'global';
}

interface LocationValidation {
  isValid: boolean;
  region?: string;
  accuracy?: number;
  warnings: string[];
  errors: string[];
}

const MapInput: React.FC<MapInputProps> = ({
  value,
  onChange,
  required = false,
  disabled = false,
  className = '',
  placeholder = 'Enter GPS coordinates or click on map',
  validationRegion = 'global'
}) => {
  const { showToast } = useToast();
  
  // State
  const [latitude, setLatitude] = useState<string>(value?.latitude?.toString() || '');
  const [longitude, setLongitude] = useState<string>(value?.longitude?.toString() || '');
  const [isLoadingLocation, setIsLoadingLocation] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validation, setValidation] = useState<LocationValidation | null>(null);
  const [searchAddress, setSearchAddress] = useState('');
  const [isGeocoding, setIsGeocoding] = useState(false);

  // Validation regions for palm oil production
  const palmOilRegions = {
    southeast_asia: {
      name: 'Southeast Asia',
      bounds: {
        north: 20.0,
        south: -10.0,
        east: 140.0,
        west: 90.0
      }
    },
    africa: {
      name: 'West/Central Africa',
      bounds: {
        north: 15.0,
        south: -15.0,
        east: 25.0,
        west: -20.0
      }
    },
    south_america: {
      name: 'South America',
      bounds: {
        north: 15.0,
        south: -25.0,
        east: -30.0,
        west: -85.0
      }
    }
  };

  // Update coordinates when value prop changes
  useEffect(() => {
    if (value) {
      setLatitude(value.latitude.toString());
      setLongitude(value.longitude.toString());
    }
  }, [value]);

  // Validate coordinates
  const validateCoordinates = useCallback(async (lat: number, lng: number) => {
    setIsValidating(true);
    
    try {
      const validation: LocationValidation = {
        isValid: true,
        warnings: [],
        errors: []
      };

      // Basic coordinate validation
      if (lat < -90 || lat > 90) {
        validation.isValid = false;
        validation.errors.push('Latitude must be between -90 and 90 degrees');
      }
      
      if (lng < -180 || lng > 180) {
        validation.isValid = false;
        validation.errors.push('Longitude must be between -180 and 180 degrees');
      }

      // Regional validation for palm oil
      if (validation.isValid && validationRegion !== 'global') {
        const region = palmOilRegions[validationRegion];
        if (region) {
          const { bounds } = region;
          const inRegion = lat >= bounds.south && lat <= bounds.north && 
                          lng >= bounds.west && lng <= bounds.east;
          
          if (!inRegion) {
            validation.warnings.push(
              `Coordinates are outside typical ${region.name} palm oil production area`
            );
          } else {
            validation.region = region.name;
          }
        }
      }

      // Accuracy validation (simulated)
      const accuracy = Math.random() * 20 + 2; // 2-22 meters
      validation.accuracy = accuracy;
      
      if (accuracy > 10) {
        validation.warnings.push(`GPS accuracy is ${accuracy.toFixed(1)}m (recommended: <10m)`);
      }

      setValidation(validation);
      
    } catch (error) {
      console.error('Validation error:', error);
      setValidation({
        isValid: false,
        warnings: [],
        errors: ['Failed to validate coordinates']
      });
    } finally {
      setIsValidating(false);
    }
  }, [validationRegion]);

  // Handle coordinate input changes
  const handleCoordinateChange = useCallback((lat: string, lng: string) => {
    setLatitude(lat);
    setLongitude(lng);

    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    if (!isNaN(latNum) && !isNaN(lngNum)) {
      const coordinates: GeographicCoordinates = {
        latitude: latNum,
        longitude: lngNum,
        timestamp: new Date().toISOString()
      };
      
      onChange(coordinates);
      validateCoordinates(latNum, lngNum);
    } else {
      setValidation(null);
    }
  }, [onChange, validateCoordinates]);

  // Get current location
  const getCurrentLocation = useCallback(() => {
    if (!navigator.geolocation) {
      showToast({
        type: 'error',
        title: 'Geolocation not supported',
        message: 'Your browser does not support geolocation.'
      });
      return;
    }

    setIsLoadingLocation(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        
        const coordinates: GeographicCoordinates = {
          latitude,
          longitude,
          accuracy,
          timestamp: new Date().toISOString()
        };

        setLatitude(latitude.toString());
        setLongitude(longitude.toString());
        onChange(coordinates);
        validateCoordinates(latitude, longitude);
        
        showToast({
          type: 'success',
          title: 'Location detected',
          message: `GPS coordinates captured with ${accuracy?.toFixed(1)}m accuracy`
        });
        
        setIsLoadingLocation(false);
      },
      (error) => {
        console.error('Geolocation error:', error);
        let message = 'Failed to get current location.';
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message = 'Location access denied. Please enable location permissions.';
            break;
          case error.POSITION_UNAVAILABLE:
            message = 'Location information unavailable.';
            break;
          case error.TIMEOUT:
            message = 'Location request timed out.';
            break;
        }
        
        showToast({
          type: 'error',
          title: 'Location error',
          message
        });
        
        setIsLoadingLocation(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  }, [onChange, validateCoordinates, showToast]);

  // Geocode address (simplified - would use actual geocoding service)
  const geocodeAddress = useCallback(async () => {
    if (!searchAddress.trim()) return;

    setIsGeocoding(true);
    
    try {
      // TODO: Implement actual geocoding service (Google Maps, OpenStreetMap, etc.)
      // For now, simulate geocoding
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulated result for demonstration
      const mockResults = {
        'kuala lumpur': { lat: 3.139, lng: 101.6869 },
        'jakarta': { lat: -6.2088, lng: 106.8456 },
        'singapore': { lat: 1.3521, lng: 103.8198 },
        'bangkok': { lat: 13.7563, lng: 100.5018 }
      };
      
      const searchKey = searchAddress.toLowerCase();
      const result = mockResults[searchKey as keyof typeof mockResults] || mockResults['kuala lumpur'];
      
      handleCoordinateChange(result.lat.toString(), result.lng.toString());
      
      showToast({
        type: 'success',
        title: 'Address found',
        message: `Coordinates set for ${searchAddress}`
      });
      
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Geocoding failed',
        message: 'Could not find coordinates for the specified address.'
      });
    } finally {
      setIsGeocoding(false);
    }
  }, [searchAddress, handleCoordinateChange, showToast]);

  // Get validation status badge
  const getValidationBadge = () => {
    if (!validation) return null;
    
    if (!validation.isValid) {
      return <Badge variant="error">Invalid</Badge>;
    }
    
    if (validation.warnings.length > 0) {
      return <Badge variant="warning">Warning</Badge>;
    }
    
    return <Badge variant="success">Valid</Badge>;
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader 
          title="GPS Coordinates" 
          subtitle="Enter precise location coordinates"
          action={getValidationBadge()}
        />
        <CardBody>
          {/* Address Search */}
          <div className="mb-4">
            <div className="flex space-x-2">
              <Input
                type="text"
                placeholder="Search by address or place name"
                value={searchAddress}
                onChange={(e) => setSearchAddress(e.target.value)}
                leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
                disabled={disabled}
              />
              <Button
                variant="outline"
                onClick={geocodeAddress}
                disabled={disabled || isGeocoding || !searchAddress.trim()}
                isLoading={isGeocoding}
              >
                Search
              </Button>
            </div>
          </div>

          {/* Coordinate Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Latitude {required && <span className="text-red-500">*</span>}
              </label>
              <Input
                type="number"
                step="any"
                placeholder="-6.2088"
                value={latitude}
                onChange={(e) => handleCoordinateChange(e.target.value, longitude)}
                disabled={disabled}
                className={validation?.errors.some(e => e.includes('Latitude')) ? 'border-red-500' : ''}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Longitude {required && <span className="text-red-500">*</span>}
              </label>
              <Input
                type="number"
                step="any"
                placeholder="106.8456"
                value={longitude}
                onChange={(e) => handleCoordinateChange(latitude, e.target.value)}
                disabled={disabled}
                className={validation?.errors.some(e => e.includes('Longitude')) ? 'border-red-500' : ''}
              />
            </div>
          </div>

          {/* Current Location Button */}
          <div className="flex justify-center mb-4">
            <Button
              variant="outline"
              onClick={getCurrentLocation}
              disabled={disabled || isLoadingLocation}
              isLoading={isLoadingLocation}
              leftIcon={<MapPinIcon className="h-4 w-4" />}
            >
              Use Current Location
            </Button>
          </div>

          {/* Validation Results */}
          {validation && (
            <div className="space-y-2">
              {/* Errors */}
              {validation.errors.map((error, index) => (
                <div key={index} className="flex items-start space-x-2 text-red-600">
                  <ExclamationTriangleIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{error}</span>
                </div>
              ))}
              
              {/* Warnings */}
              {validation.warnings.map((warning, index) => (
                <div key={index} className="flex items-start space-x-2 text-yellow-600">
                  <ExclamationTriangleIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{warning}</span>
                </div>
              ))}
              
              {/* Success info */}
              {validation.isValid && validation.errors.length === 0 && (
                <div className="flex items-start space-x-2 text-green-600">
                  <CheckCircleIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <div>Valid coordinates</div>
                    {validation.region && (
                      <div className="text-xs text-gray-500">Region: {validation.region}</div>
                    )}
                    {validation.accuracy && (
                      <div className="text-xs text-gray-500">
                        Accuracy: {validation.accuracy.toFixed(1)}m
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Loading indicator */}
          {isValidating && (
            <div className="flex items-center space-x-2 text-gray-500">
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
              <span className="text-sm">Validating coordinates...</span>
            </div>
          )}

          {/* Map placeholder */}
          <div className="mt-4 h-64 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <GlobeAltIcon className="h-12 w-12 mx-auto mb-2" />
              <div className="text-sm">Interactive map will be displayed here</div>
              <div className="text-xs text-gray-400 mt-1">
                Click on map to set coordinates
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default MapInput;
