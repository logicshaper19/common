/**
 * API client for sector-related operations
 */
import { apiClient } from '../lib/api';
import { 
  Sector, 
  SectorConfig, 
  SectorTier, 
  SectorProduct, 
  UserSectorInfo 
} from '../types/sector';

class SectorApiClient {
  /**
   * Get all available sectors
   */
  async getSectors(activeOnly: boolean = true): Promise<Sector[]> {
    const response = await apiClient.get<Sector[]>('/sectors', {
      params: { active_only: activeOnly }
    });
    return response.data;
  }

  /**
   * Get a specific sector by ID
   */
  async getSector(sectorId: string): Promise<Sector> {
    const response = await apiClient.get<Sector>(`/sectors/${sectorId}`);
    return response.data;
  }

  /**
   * Get complete sector configuration (sector + tiers + products)
   */
  async getSectorConfig(sectorId: string): Promise<SectorConfig> {
    const response = await apiClient.get<SectorConfig>(`/sectors/${sectorId}/config`);
    return response.data;
  }

  /**
   * Get tier definitions for a sector
   */
  async getSectorTiers(sectorId: string): Promise<SectorTier[]> {
    const response = await apiClient.get<SectorTier[]>(`/sectors/${sectorId}/tiers`);
    return response.data;
  }

  /**
   * Get specific tier by sector and level
   */
  async getSectorTier(sectorId: string, tierLevel: number): Promise<SectorTier> {
    const response = await apiClient.get<SectorTier>(`/sectors/${sectorId}/tiers/${tierLevel}`);
    return response.data;
  }

  /**
   * Get products for a sector, optionally filtered by tier level
   */
  async getSectorProducts(sectorId: string, tierLevel?: number): Promise<SectorProduct[]> {
    const response = await apiClient.get<SectorProduct[]>(`/sectors/${sectorId}/products`, {
      params: tierLevel ? { tier_level: tierLevel } : {}
    });
    return response.data;
  }

  /**
   * Get current user's sector and tier information
   */
  async getUserSectorInfo(): Promise<UserSectorInfo> {
    const response = await apiClient.get<UserSectorInfo>('/users/me/sector-info');
    return response.data;
  }

  // Admin-only methods

  /**
   * Create a new sector (admin only)
   */
  async createSector(sectorData: Omit<Sector, 'id'>): Promise<Sector> {
    const response = await apiClient.post<Sector>('/sectors', sectorData);
    return response.data;
  }

  /**
   * Create a new tier for a sector (admin only)
   */
  async createSectorTier(sectorId: string, tierData: Omit<SectorTier, 'id' | 'sectorId'>): Promise<SectorTier> {
    const response = await apiClient.post<SectorTier>(`/sectors/${sectorId}/tiers`, {
      ...tierData,
      sector_id: sectorId
    });
    return response.data;
  }

  /**
   * Create a new product for a sector (admin only)
   */
  async createSectorProduct(sectorId: string, productData: Omit<SectorProduct, 'id' | 'sectorId'>): Promise<SectorProduct> {
    const response = await apiClient.post<SectorProduct>(`/sectors/${sectorId}/products`, {
      ...productData,
      sector_id: sectorId
    });
    return response.data;
  }
}

export const sectorApi = new SectorApiClient();
