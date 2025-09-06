/**
 * Main Admin API Client
 * Provides a unified interface to all admin functionality
 */
import { ProductClient } from './clients/ProductClient';
import { UserClient } from './clients/UserClient';
import { CompanyClient } from './clients/CompanyClient';
import { TicketClient } from './clients/TicketClient';
import { AuditClient } from './clients/AuditClient';
import { SystemClient } from './clients/SystemClient';

// Re-export types for convenience
export * from '../../../types/admin';
export * from './base/types';

// Re-export individual clients for direct use
export { ProductClient, UserClient, CompanyClient, TicketClient, AuditClient, SystemClient };

/**
 * Main Admin API Client
 * Provides access to all admin functionality through specialized clients
 */
export class AdminApiClient {
  // Specialized clients for each domain
  public readonly products = new ProductClient();
  public readonly users = new UserClient();
  public readonly companies = new CompanyClient();
  public readonly tickets = new TicketClient();
  public readonly audit = new AuditClient();
  public readonly system = new SystemClient();

  // Legacy methods for backward compatibility
  // These delegate to the appropriate specialized clients

  // Product methods
  async getProducts(filters: any) {
    return this.products.getProducts(filters);
  }

  async getProduct(id: string) {
    return this.products.getProduct(id);
  }

  async createProduct(data: any) {
    return this.products.createProduct(data);
  }

  async updateProduct(id: string, data: any) {
    return this.products.updateProduct(id, data);
  }

  async deleteProduct(id: string) {
    return this.products.deleteProduct(id);
  }

  async validateProduct(data: any) {
    return this.products.validateProduct(data);
  }

  async bulkProductOperation(operation: any) {
    return this.products.bulkProductOperation(operation);
  }

  // User methods
  async getUsers(filters: any) {
    return this.users.getUsers(filters);
  }

  async getUser(id: string) {
    return this.users.getUser(id);
  }

  async createUser(data: any) {
    return this.users.createUser(data);
  }

  async updateUser(id: string, data: any) {
    return this.users.updateUser(id, data);
  }

  async deleteUser(id: string) {
    return this.users.deleteUser(id);
  }

  async bulkUserOperation(operation: any) {
    return this.users.bulkUserOperation(operation);
  }

  // Company methods
  async getCompanies(filters: any) {
    return this.companies.getCompanies(filters);
  }

  async getCompany(id: string) {
    return this.companies.getCompany(id);
  }

  async updateCompany(id: string, data: any) {
    return this.companies.updateCompany(id, data);
  }

  async bulkCompanyOperation(operation: any) {
    return this.companies.bulkCompanyOperation(operation);
  }

  // Ticket methods
  async getTickets(filters: any) {
    return this.tickets.getTickets(filters);
  }

  async getTicket(id: string) {
    return this.tickets.getTicket(id);
  }

  async createTicket(data: any) {
    return this.tickets.createTicket(data);
  }

  async updateTicket(id: string, data: any) {
    return this.tickets.updateTicket(id, data);
  }

  async addTicketMessage(id: string, data: any) {
    return this.tickets.addTicketMessage(id, data);
  }

  async bulkTicketOperation(operation: any) {
    return this.tickets.bulkTicketOperation(operation);
  }

  // Audit methods
  async getAuditLogs(filters: any) {
    return this.audit.getAuditLogs(filters);
  }

  async exportAuditLogs(request: any) {
    return this.audit.exportAuditLogs(request);
  }

  // System methods
  async getDashboardData() {
    return this.system.getDashboardData();
  }

  async getSystemHealth() {
    return this.system.getSystemHealth();
  }

  async getSystemConfigs() {
    return this.system.getSystemConfigs();
  }

  async updateSystemConfig(id: string, value: any) {
    return this.system.updateSystemConfig(id, value);
  }

  async getSystemAlerts() {
    return this.system.getSystemAlerts();
  }

  async acknowledgeAlert(id: string) {
    return this.system.acknowledgeAlert(id);
  }

  async getBackupStatus() {
    return this.system.getBackupStatus();
  }

  async createBackup(type: 'full' | 'incremental') {
    return this.system.createBackup(type);
  }
}

// Export singleton instance for backward compatibility
export const adminApi = new AdminApiClient();

// Default export
export default adminApi;

/**
 * Usage Examples:
 * 
 * // New modular approach (recommended)
 * import { adminApi } from '@/api/admin';
 * const products = await adminApi.products.getProducts(filters);
 * const users = await adminApi.users.getUsers(filters);
 * 
 * // Direct client usage
 * import { ProductClient } from '@/api/admin';
 * const productClient = new ProductClient();
 * const products = await productClient.getProducts(filters);
 * 
 * // Backward compatible (legacy)
 * import { adminApi } from '@/api/admin';
 * const products = await adminApi.getProducts(filters);
 */
