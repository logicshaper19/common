"""
Application Constants
"""

# Palm oil farm specializations
PALM_OIL_SPECIALIZATIONS = [
    {"value": "fresh_fruit_bunches", "label": "Fresh Fruit Bunches (FFB)"},
    {"value": "oil_palm_seedlings", "label": "Oil Palm Seedlings"},
    {"value": "mixed_ffb_seedlings", "label": "Mixed FFB & Seedlings"},
    {"value": "organic_ffb", "label": "Organic Fresh Fruit Bunches"},
    {"value": "certified_sustainable", "label": "RSPO/Certified Sustainable FFB"},
    {"value": "high_yield_varieties", "label": "High-Yield Varieties (Tenera)"},
    {"value": "specialty_varieties", "label": "Specialty Palm Varieties"},
    {"value": "intercropping_systems", "label": "Intercropping Systems"},
    {"value": "research_development", "label": "Research & Development"},
    {"value": "other", "label": "Other"}
]

# Farm types for palm oil
PALM_OIL_FARM_TYPES = [
    {"value": "smallholder", "label": "Smallholder (< 50 hectares)"},
    {"value": "medium_scale", "label": "Medium Scale (50-500 hectares)"},
    {"value": "large_estate", "label": "Large Estate (> 500 hectares)"},
    {"value": "cooperative", "label": "Cooperative Farm"},
    {"value": "independent", "label": "Independent Plantation"},
    {"value": "company_owned", "label": "Company-Owned Estate"}
]

# Plantation types (existing)
PLANTATION_TYPES = [
    {"value": "smallholder", "label": "Smallholder"},
    {"value": "own_estate", "label": "Own Estate"},
    {"value": "mixed", "label": "Mixed Operations"}
]

# Certification types
CERTIFICATION_TYPES = [
    {"value": "rspo", "label": "RSPO (Roundtable on Sustainable Palm Oil)"},
    {"value": "mspo", "label": "MSPO (Malaysian Sustainable Palm Oil)"},
    {"value": "ispo", "label": "ISPO (Indonesian Sustainable Palm Oil)"},
    {"value": "organic", "label": "Organic Certification"},
    {"value": "fair_trade", "label": "Fair Trade"},
    {"value": "rainforest_alliance", "label": "Rainforest Alliance"},
    {"value": "iso_14001", "label": "ISO 14001 Environmental Management"},
    {"value": "non_gmo", "label": "Non-GMO Verified"},
    {"value": "other", "label": "Other Certification"}
]

# Farm status options
FARM_STATUS_OPTIONS = [
    {"value": "active", "label": "Active"},
    {"value": "inactive", "label": "Inactive"},
    {"value": "pending_verification", "label": "Pending Verification"},
    {"value": "suspended", "label": "Suspended"},
    {"value": "decommissioned", "label": "Decommissioned"}
]

# Compliance status options
COMPLIANCE_STATUS_OPTIONS = [
    {"value": "pending", "label": "Pending Review"},
    {"value": "verified", "label": "Verified Compliant"},
    {"value": "failed", "label": "Non-Compliant"},
    {"value": "exempt", "label": "Exempt"},
    {"value": "requires_update", "label": "Requires Update"}
]
