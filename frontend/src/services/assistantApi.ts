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
      // Temporary mock response for testing
      if (message.toLowerCase().includes('po-202509-0001')) {
        return {
          response: `📋 **Purchase Order PO-202509-0001 Details:**

**Status:** Confirmed ✅
**Buyer:** Plantation Estate Sdn Bhd
**Seller:** Golden Acre Palm Oil Mill
**Product:** CPO (Crude Palm Oil)
**Quantity:** 500 MT
**Confirmed Date:** September 15, 2025
**Delivery Date:** October 1, 2025
**Location:** Port Klang, Malaysia

**Key Information:**
• This PO was confirmed on September 15, 2025
• Currently in fulfilled status with 100% completion
• Quality specifications: FFA < 3.5%, Moisture < 0.1%
• Traceability score: 95.2% ✅

Would you like more details about this purchase order or help with anything else?`,
          success: true
        };
      }
      
      return {
        response: `Hello! I'm your supply chain assistant. I can help you with:

📦 **Inventory Management** - Check stock levels, batch tracking
📋 **Purchase Orders** - Status updates, confirmations, delivery tracking  
🔍 **Traceability** - Supply chain visibility, compliance tracking
✅ **Compliance** - EUDR, RSPO certifications
🏭 **Processing** - Mill operations, transformations

Try asking me about specific purchase orders (like "PO-202509-0001"), inventory levels, or compliance status!

What would you like to know about your supply chain operations?`,
        success: true
      };
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
