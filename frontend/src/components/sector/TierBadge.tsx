/**
 * Tier Badge Component
 * Displays user's tier level with appropriate styling
 */
import React from 'react';
import { useSector } from '../../contexts/SectorContext';
import { isSectorSystemEnabled } from '../../utils/featureFlags';

interface TierBadgeProps {
  className?: string;
  showLevel?: boolean;
  showDescription?: boolean;
}

export const TierBadge: React.FC<TierBadgeProps> = ({
  className = '',
  showLevel = true,
  showDescription = false
}) => {
  const { userTier, userSectorInfo } = useSector();

  // Don't render if sector system is not enabled
  if (!isSectorSystemEnabled()) {
    return null;
  }

  if (!userTier || !userSectorInfo) {
    return null;
  }

  // Color scheme based on tier level
  const getTierColors = (level: number) => {
    const colors = {
      1: 'bg-purple-100 text-purple-800 border-purple-200',
      2: 'bg-blue-100 text-blue-800 border-blue-200',
      3: 'bg-green-100 text-green-800 border-green-200',
      4: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      5: 'bg-orange-100 text-orange-800 border-orange-200',
      6: 'bg-red-100 text-red-800 border-red-200',
    };
    return colors[level as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const tierColors = getTierColors(userTier.level);

  return (
    <div className={`inline-flex items-center ${className}`}>
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${tierColors}`}>
        {showLevel && (
          <span className="mr-1">T{userTier.level}</span>
        )}
        {userTier.name}
        {userTier.isOriginator && (
          <span className="ml-1 text-xs">🌱</span>
        )}
      </span>
      {showDescription && userTier.description && (
        <span className="ml-2 text-xs text-gray-500">
          {userTier.description}
        </span>
      )}
    </div>
  );
};
