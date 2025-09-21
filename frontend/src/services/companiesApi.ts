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
      console.log('🏢 Fetching business partners...');
      // Try to get suppliers from simple relationships
      const response = await apiClient.get('/simple/relationships/suppliers');
      console.log('🏢 Raw response:', response);
      
      // Transform the supplier response to company format
      const suppliers = response.data.suppliers || [];
      console.log('🏢 Suppliers array:', suppliers);
      
      const companies = suppliers.map((supplier: any) => ({
        id: supplier.company_id,
        name: supplier.company_name,
        email: supplier.email || '',
        company_type: supplier.company_type || 'unknown',
        address: '',
        industry_sector: '',
        industry_subcategory: '',
        created_at: supplier.first_transaction_date || '',
        updated_at: supplier.last_transaction_date || supplier.first_transaction_date || ''
      }));
      
      console.log('🏢 Transformed companies:', companies);
      
      // If no suppliers found, provide a fallback with all companies
      if (companies.length === 0) {
        console.log('⚠️ No business relationships found, falling back to all companies...');
        try {
          const fallbackResponse = await apiClient.get('/companies?for_supplier_selection=true');
          const allCompanies = fallbackResponse.data.data || [];
          console.log('🏢 Fallback companies:', allCompanies.length);
          return allCompanies;
        } catch (fallbackError) {
          console.error('❌ Error fetching fallback companies:', fallbackError);
          // Return empty array if both fail
          return [];
        }
      }
      
      return companies;
    } catch (error: any) {
      console.error('❌ Error fetching business partners:', error);
      
      // Fallback: try to get all companies if business relationships fail
      try {
        console.log('🔄 Falling back to all companies...');
        const fallbackResponse = await apiClient.get('/companies?for_supplier_selection=true');
        const allCompanies = fallbackResponse.data.companies || [];
        console.log('🏢 Fallback companies:', allCompanies.length);
        return allCompanies;
      } catch (fallbackError) {
        console.error('❌ Error fetching fallback companies:', fallbackError);
        console.error('❌ Error details:', error.response?.data || error.message);
        
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
  }
};
