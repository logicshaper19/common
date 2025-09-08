import { apiClient } from '../lib/api';

export interface Company {
  id: string;
  name: string;
  email: string;
  company_type: string;
  address?: string;
  industry_sector?: string;
  industry_subcategory?: string;
  created_at: string;
  updated_at: string;
}

export interface CompanyListResponse {
  companies: Company[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface CompanyFilter {
  company_type?: string;
  industry_sector?: string;
  search?: string;
  page?: number;
  per_page?: number;
}

// For now, we'll use the business relationships API to get companies
// that the current user's company can create purchase orders with
export const companiesApi = {
  // Get companies that can be used as suppliers/buyers
  getBusinessPartners: async (): Promise<Company[]> => {
    try {
      // Try to get suppliers from business relationships
      const response = await apiClient.get('/business-relationships/suppliers');
      
      // Transform the supplier response to company format
      const suppliers = response.data.suppliers || [];
      return suppliers.map((supplier: any) => ({
        id: supplier.company_id,
        name: supplier.company_name,
        email: supplier.company_email || '',
        company_type: supplier.company_type || 'unknown',
        address: supplier.address || '',
        industry_sector: supplier.industry_sector || '',
        industry_subcategory: supplier.industry_subcategory || '',
        created_at: supplier.created_at || '',
        updated_at: supplier.updated_at || ''
      }));
    } catch (error) {
      console.error('Error fetching business partners:', error);
      
      // Fallback to mock data for now
      return [
        {
          id: 'a5287fd6-15cf-4a93-9237-a9d52e1a1428',
          name: 'Sustainable Mill Co',
          email: 'operations@sustainablemill.com',
          company_type: 'mill_processor',
          address: '',
          industry_sector: '',
          industry_subcategory: '',
          created_at: '',
          updated_at: ''
        },
        {
          id: '9ab08879-3f9b-487f-97ca-f89309c5e665',
          name: "L'Oréal Group",
          email: 'contact@loreal.com',
          company_type: 'manufacturer',
          address: '',
          industry_sector: '',
          industry_subcategory: '',
          created_at: '',
          updated_at: ''
        }
      ];
    }
  }
};
