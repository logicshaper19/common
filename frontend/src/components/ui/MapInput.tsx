/**
 * Map Input Component for geographic coordinate selection
 * Provides interactive map for location input with coordinate validation
 */
import React, { useState, useEffect, useRef } from 'react';
import { MapPinIcon, GlobeAltIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { Coordinates, Location } from '../../types/confirmation';
import { cn } from '../../lib/utils';
import Button from './Button';
import Input from './Input';

interface MapInputProps {
  value?: Location;
  onChange: (location: Location) => void;
  label?: string;
  placeholder?: string;
  required?: boolean;
  error?: string;
  className?: string;
  disabled?: boolean;
}

const MapInput: React.FC<MapInputProps> = ({
  value,
  onChange,
  label,
  placeholder = 'Click on map or enter coordinates',
  required = false,
  error,
  className,
  disabled = false
}) => {
  const [isMapOpen, setIsMapOpen] = useState(false);
  const [coordinates, setCoordinates] = useState<Coordinates>(
    value?.coordinates || { latitude: 0, longitude: 0 }
  );
  const [address, setAddress] = useState(value?.address || '');
  const [isLoadingLocation, setIsLoadingLocation] = useState(false);
  const mapRef = useRef<HTMLDivElement>(null);

  // Update internal state when value changes
  useEffect(() => {
    if (value) {
      setCoordinates(value.coordinates);
      setAddress(value.address || '');
    }
  }, [value]);

  // Get current location from browser
  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by this browser');
      return;
    }

    setIsLoadingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newCoordinates: Coordinates = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        setCoordinates(newCoordinates);
        reverseGeocode(newCoordinates);
        setIsLoadingLocation(false);
      },
      (error) => {
        console.error('Error getting location:', error);
        alert('Unable to get current location');
        setIsLoadingLocation(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  };

  // Reverse geocoding to get address from coordinates
  const reverseGeocode = async (coords: Coordinates) => {
    try {
      // In a real implementation, you would use a geocoding service like:
      // - Google Maps Geocoding API
      // - OpenStreetMap Nominatim
      // - Mapbox Geocoding API
      
      // For demo purposes, we'll create a mock address
      const mockAddress = `${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`;
      setAddress(mockAddress);
      
      const location: Location = {
        coordinates: coords,
        address: mockAddress,
        country: 'Unknown', // Would be populated by real geocoding
      };
      
      onChange(location);
    } catch (error) {
      console.error('Geocoding error:', error);
    }
  };

  // Handle coordinate input changes
  const handleCoordinateChange = (field: 'latitude' | 'longitude', value: string) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;

    const newCoordinates = {
      ...coordinates,
      [field]: numValue
    };

    setCoordinates(newCoordinates);
    
    // Validate coordinates
    if (isValidCoordinates(newCoordinates)) {
      reverseGeocode(newCoordinates);
    }
  };

  // Validate coordinates
  const isValidCoordinates = (coords: Coordinates): boolean => {
    return (
      coords.latitude >= -90 &&
      coords.latitude <= 90 &&
      coords.longitude >= -180 &&
      coords.longitude <= 180
    );
  };

  // Handle map click (mock implementation)
  const handleMapClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (disabled) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Convert click position to coordinates (mock calculation)
    // In a real implementation, this would use the map library's methods
    const lat = 90 - (y / rect.height) * 180;
    const lng = (x / rect.width) * 360 - 180;
    
    const newCoordinates: Coordinates = {
      latitude: parseFloat(lat.toFixed(6)),
      longitude: parseFloat(lng.toFixed(6))
    };

    setCoordinates(newCoordinates);
    reverseGeocode(newCoordinates);
  };

  // Format coordinates for display
  const formatCoordinate = (value: number, type: 'lat' | 'lng'): string => {
    const direction = type === 'lat' 
      ? (value >= 0 ? 'N' : 'S')
      : (value >= 0 ? 'E' : 'W');
    return `${Math.abs(value).toFixed(6)}° ${direction}`;
  };

  return (
    <div className={cn('w-full', className)}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}

      {/* Current location display */}
      <div className="mb-3">
        <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border">
          <div className="flex items-center space-x-3">
            <MapPinIcon className="h-5 w-5 text-neutral-400" />
            <div>
              {address ? (
                <div>
                  <p className="text-sm font-medium text-neutral-900">{address}</p>
                  <p className="text-xs text-neutral-500">
                    {formatCoordinate(coordinates.latitude, 'lat')}, {formatCoordinate(coordinates.longitude, 'lng')}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-neutral-500">{placeholder}</p>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={getCurrentLocation}
              disabled={disabled || isLoadingLocation}
              isLoading={isLoadingLocation}
            >
              <GlobeAltIcon className="h-4 w-4" />
            </Button>
            
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsMapOpen(true)}
              disabled={disabled}
            >
              Select on Map
            </Button>
          </div>
        </div>
      </div>

      {/* Coordinate inputs */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <Input
          label="Latitude"
          type="number"
          value={coordinates.latitude.toString()}
          onChange={(e) => handleCoordinateChange('latitude', e.target.value)}
          placeholder="-90 to 90"
          disabled={disabled}
          step="0.000001"
          min="-90"
          max="90"
        />
        <Input
          label="Longitude"
          type="number"
          value={coordinates.longitude.toString()}
          onChange={(e) => handleCoordinateChange('longitude', e.target.value)}
          placeholder="-180 to 180"
          disabled={disabled}
          step="0.000001"
          min="-180"
          max="180"
        />
      </div>

      {/* Error message */}
      {error && (
        <p className="text-sm text-error-600 mt-1">{error}</p>
      )}

      {/* Map modal */}
      {isMapOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Backdrop */}
            <div 
              className="fixed inset-0 transition-opacity bg-neutral-500 bg-opacity-75"
              onClick={() => setIsMapOpen(false)}
            />

            {/* Modal */}
            <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-neutral-900">
                  Select Location
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMapOpen(false)}
                >
                  <XMarkIcon className="h-5 w-5" />
                </Button>
              </div>

              {/* Mock map */}
              <div 
                ref={mapRef}
                className="w-full h-96 bg-gradient-to-br from-green-100 to-blue-100 rounded-lg border-2 border-dashed border-neutral-300 flex items-center justify-center cursor-crosshair relative overflow-hidden"
                onClick={handleMapClick}
              >
                {/* Mock map background pattern */}
                <div className="absolute inset-0 opacity-20">
                  <div className="grid grid-cols-8 grid-rows-6 h-full w-full">
                    {Array.from({ length: 48 }).map((_, i) => (
                      <div key={i} className="border border-neutral-300" />
                    ))}
                  </div>
                </div>

                {/* Current marker */}
                {coordinates.latitude !== 0 || coordinates.longitude !== 0 ? (
                  <div 
                    className="absolute transform -translate-x-1/2 -translate-y-full"
                    style={{
                      left: `${((coordinates.longitude + 180) / 360) * 100}%`,
                      top: `${((90 - coordinates.latitude) / 180) * 100}%`
                    }}
                  >
                    <MapPinIcon className="h-8 w-8 text-error-500 drop-shadow-lg" />
                  </div>
                ) : null}

                {/* Instructions */}
                <div className="text-center">
                  <MapPinIcon className="h-12 w-12 text-neutral-400 mx-auto mb-2" />
                  <p className="text-neutral-600">Click anywhere on the map to set location</p>
                  <p className="text-sm text-neutral-500 mt-1">
                    Current: {formatCoordinate(coordinates.latitude, 'lat')}, {formatCoordinate(coordinates.longitude, 'lng')}
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-neutral-500">
                  Note: This is a demo map. In production, this would use a real mapping service.
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="secondary"
                    onClick={() => setIsMapOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => setIsMapOpen(false)}
                  >
                    Confirm Location
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapInput;
