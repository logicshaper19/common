/**
 * Sector Selector Component
 * Allows users to switch between different sectors
 */
import React from 'react';
import { useSector } from '../../contexts/SectorContext';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import { isSectorSystemEnabled } from '../../utils/featureFlags';

interface SectorSelectorProps {
  className?: string;
}

export const SectorSelector: React.FC<SectorSelectorProps> = ({ className = '' }) => {
  const {
    currentSector,
    availableSectors,
    switchSector,
    loading
  } = useSector();

  // Don't render if sector system is not enabled
  if (!isSectorSystemEnabled()) {
    return null;
  }

  const handleSectorChange = async (sectorId: string) => {
    if (sectorId !== currentSector?.id) {
      await switchSector(sectorId);
    }
  };

  if (loading || availableSectors.length === 0) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-8 bg-gray-200 rounded"></div>
      </div>
    );
  }

  // If only one sector is available, show it as a label
  if (availableSectors.length === 1) {
    return (
      <div className={`text-sm font-medium text-gray-700 ${className}`}>
        {currentSector?.name || availableSectors[0].name}
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <select
        value={currentSector?.id || ''}
        onChange={(e) => handleSectorChange(e.target.value)}
        className="appearance-none bg-white border border-gray-300 rounded-md px-3 py-2 pr-8 text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {!currentSector && (
          <option value="">Select Sector</option>
        )}
        {availableSectors.map((sector) => (
          <option key={sector.id} value={sector.id}>
            {sector.name}
          </option>
        ))}
      </select>
      <ChevronDownIcon className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
    </div>
  );
};
