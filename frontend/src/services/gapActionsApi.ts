/**
 * Gap Actions API Service
 * Handles API calls for transparency gap actions
 */
import { apiClient } from '../lib/api';
import { GapActionRequest } from '../components/transparency/GapActionsPanel';

export interface GapActionResponse {
  id: string;
  gap_id: string;
  action_type: string;
  target_company_name?: string;
  message?: string;
  status: string;
  created_at: string;
  created_by_name: string;
  resolved_at?: string;
  resolved_by_name?: string;
  resolution_notes?: string;
}

export interface GapActionUpdate {
  status: string;
  resolution_notes?: string;
}

export const gapActionsApi = {
  /**
   * Create a new gap action
   */
  createGapAction: async (
    companyId: string,
    gapId: string,
    action: GapActionRequest
  ): Promise<{ success: boolean; action_id: string; message: string }> => {
    const response = await apiClient.post(
      `/transparency/v2/companies/${companyId}/gaps/${gapId}/actions`,
      action
    );
    return response.data;
  },

  /**
   * Get gap actions for a company
   */
  getGapActions: async (
    companyId: string,
    status?: string
  ): Promise<{ success: boolean; actions: GapActionResponse[] }> => {
    const params = status ? { status } : {};
    const response = await apiClient.get(
      `/transparency/v2/companies/${companyId}/gap-actions`,
      { params }
    );
    return response.data;
  },

  /**
   * Update gap action status
   */
  updateGapAction: async (
    companyId: string,
    actionId: string,
    update: GapActionUpdate
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.put(
      `/transparency/v2/companies/${companyId}/gap-actions/${actionId}`,
      update
    );
    return response.data;
  }
};

export default gapActionsApi;
