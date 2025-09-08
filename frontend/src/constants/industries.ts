/**
 * Industry sector and subcategory constants
 */

export interface IndustryMapping {
  sector: string;
  subcategories: string[];
}

export const INDUSTRY_MAPPINGS: IndustryMapping[] = [
  {
    sector: 'Consumer Staples',
    subcategories: [
      'Personal Care & Cosmetics',
      'Household Products',
      'Food & Beverage',
      'Tobacco'
    ]
  },
  {
    sector: 'Consumer Discretionary',
    subcategories: [
      'Apparel & Footwear',
      'Luxury Goods',
      'Consumer Electronics',
      'Leisure Products'
    ]
  },
  {
    sector: 'Health Care',
    subcategories: [
      'Pharmaceuticals',
      'Biotechnology',
      'Medical Devices',
      'Health Care Services'
    ]
  },
  {
    sector: 'Industrials',
    subcategories: [
      'Aerospace & Defense',
      'Machinery',
      'Transportation',
      'Logistics & Freight'
    ]
  },
  {
    sector: 'Materials',
    subcategories: [
      'Chemicals',
      'Packaging',
      'Metals & Mining',
      'Paper & Forest Products'
    ]
  },
  {
    sector: 'Energy',
    subcategories: [
      'Oil & Gas',
      'Renewable Energy',
      'Coal'
    ]
  },
  {
    sector: 'Information Technology',
    subcategories: [
      'Software',
      'IT Services',
      'Semiconductors',
      'Hardware'
    ]
  },
  {
    sector: 'Financials',
    subcategories: [
      'Banking',
      'Insurance',
      'Asset Management',
      'Real Estate'
    ]
  },
  {
    sector: 'Utilities',
    subcategories: [
      'Electric',
      'Gas',
      'Water Utilities'
    ]
  },
  {
    sector: 'Communication Services',
    subcategories: [
      'Media',
      'Telecom',
      'Entertainment'
    ]
  },
  {
    sector: 'Real Estate',
    subcategories: [
      'Real Estate Investment',
      'Real Estate Services',
      'Real Estate Development'
    ]
  }
];

export const INDUSTRY_SECTORS = INDUSTRY_MAPPINGS.map(mapping => mapping.sector);

export const getSubcategoriesForSector = (sector: string): string[] => {
  const mapping = INDUSTRY_MAPPINGS.find(m => m.sector === sector);
  return mapping ? mapping.subcategories : [];
};

export const getAllSubcategories = (): string[] => {
  return INDUSTRY_MAPPINGS.flatMap(mapping => mapping.subcategories);
};
