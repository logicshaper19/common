/**
 * Sector Context for managing sector-specific configurations and user tier information
 */
import React, { createContext, useContext, useEffect, useState, useMemo, useCallback, ReactNode } from 'react';
import { Sector, SectorConfig, SectorTier, UserSectorInfo } from '../types/sector';
import { useAuth } from './AuthContext';
import { sectorApi } from '../api/sector';

interface SectorContextType {
  currentSector: Sector | null;
  sectorConfig: SectorConfig | null;
  userTier: SectorTier | null;
  userSectorInfo: UserSectorInfo | null;
  availableSectors: Sector[];
  switchSector: (sectorId: string) => Promise<void>;
  refreshSectorConfig: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const SectorContext = createContext<SectorContextType | undefined>(undefined);

export const useSector = (): SectorContextType => {
  const context = useContext(SectorContext);
  if (context === undefined) {
    throw new Error('useSector must be used within a SectorProvider');
  }
  return context;
};

interface SectorProviderProps {
  children: ReactNode;
}

export const SectorProvider: React.FC<SectorProviderProps> = ({ children }) => {
  const [currentSector, setCurrentSector] = useState<Sector | null>(null);
  const [sectorConfig, setSectorConfig] = useState<SectorConfig | null>(null);
  const [userSectorInfo, setUserSectorInfo] = useState<UserSectorInfo | null>(null);
  const [availableSectors, setAvailableSectors] = useState<Sector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { user, isAuthenticated } = useAuth();

  const loadAvailableSectors = async () => {
    try {
      setLoading(true);
      setError(null);
      const sectors = await sectorApi.getSectors();
      setAvailableSectors(sectors);
    } catch (err) {
      console.error('Failed to load available sectors:', err);
      setError('Failed to load available sectors');
      // Don't block the app if sectors fail to load
      setAvailableSectors([]);
    } finally {
      setLoading(false);
    }
  };

  const loadUserSectorInfo = useCallback(async () => {
    try {
      const info = await sectorApi.getUserSectorInfo();
      setUserSectorInfo(info);

      // If user has sector info and we don't have the sector config yet, load it
      if (info.sectorId && !currentSector) {
        await loadSectorConfig(info.sectorId);
      }
    } catch (err) {
      console.error('Failed to load user sector info:', err);
      setError('Failed to load user sector information');
    }
  }, [currentSector]);

  // Load available sectors on mount (non-blocking)
  useEffect(() => {
    loadAvailableSectors();
  }, []);

  // Load user's sector configuration when user changes
  useEffect(() => {
    if (isAuthenticated && user) {
      // Always try to load user sector info (it might be available from backend even if not in user object)
      loadUserSectorInfo();

      // If user has sector info, load the sector config
      if (user.sectorId) {
        loadSectorConfig(user.sectorId);
      } else {
        // User doesn't have sector assigned yet, just clear loading
        setLoading(false);
      }
    } else {
      // Clear sector data if user is not authenticated
      setCurrentSector(null);
      setSectorConfig(null);
      setUserSectorInfo(null);
      setLoading(false);
    }
  }, [isAuthenticated, user, loadUserSectorInfo]);

  const loadSectorConfig = async (sectorId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const config = await sectorApi.getSectorConfig(sectorId);
      setSectorConfig(config);
      setCurrentSector(config.sector);
    } catch (err) {
      console.error('Failed to load sector config:', err);
      setError(`Failed to load sector configuration for ${sectorId}`);
      setSectorConfig(null);
      setCurrentSector(null);
    } finally {
      setLoading(false);
    }
  };

  const switchSector = async (sectorId: string) => {
    await loadSectorConfig(sectorId);
  };

  const refreshSectorConfig = async () => {
    if (currentSector) {
      await loadSectorConfig(currentSector.id);
    }
  };

  // Compute user's tier information
  const userTier = useMemo(() => {
    if (!sectorConfig || !userSectorInfo?.tierLevel) return null;
    return sectorConfig.tiers.find(t => t.level === userSectorInfo.tierLevel) || null;
  }, [sectorConfig, userSectorInfo]);

  const value: SectorContextType = {
    currentSector,
    sectorConfig,
    userTier,
    userSectorInfo,
    availableSectors,
    switchSector,
    refreshSectorConfig,
    loading,
    error
  };

  return (
    <SectorContext.Provider value={value}>
      {children}
    </SectorContext.Provider>
  );
};
