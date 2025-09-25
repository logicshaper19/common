/**
 * Assistant API Service
 * Handles communication with the backend assistant endpoints
 */
import { apiClient } from '../lib/api';

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  response: string;
  success: boolean;
}

export const assistantApi = {
  /**
   * Send a message to the assistant and get a response
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await apiClient.post<ChatResponse>('/assistant/chat', {
        message
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message to assistant:', error);
      throw new Error('Failed to get response from assistant');
    }
  },

  /**
   * Health check for the assistant service
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await apiClient.get('/assistant/health');
      return response.data;
    } catch (error) {
      console.error('Error checking assistant health:', error);
      throw new Error('Assistant service is not available');
    }
  }
};
