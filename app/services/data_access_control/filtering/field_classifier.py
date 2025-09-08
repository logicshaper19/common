"""
Field classification for data sensitivity analysis.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import re

from app.models.data_access import DataSensitivityLevel, DataClassification
from app.core.logging import get_logger

logger = get_logger(__name__)


class FieldClassifier:
    """Classifies data fields by sensitivity level."""
    
    def __init__(self, db: Session):
        """Initialize field classifier."""
        self.db = db
        self._load_classification_rules()
    
    def _load_classification_rules(self):
        """Load field classification rules from database."""
        # In a real implementation, this would load from database
        # For now, we'll use hardcoded rules
        
        self.sensitivity_patterns = {
            DataSensitivityLevel.PUBLIC: [
                r'^(id|name|type|status|category)$',
                r'^(created_at|updated_at|version)$',
                r'^(description|title|label)$',
            ],
            DataSensitivityLevel.INTERNAL: [
                r'^(quantity|unit|weight|dimensions)$',
                r'^(supplier_name|buyer_name|company_name)$',
                r'^(product_name|product_code|sku)$',
                r'^(delivery_date|expected_date)$',
            ],
            DataSensitivityLevel.CONFIDENTIAL: [
                r'^(price|cost|total_amount|unit_price)$',
                r'^(profit_margin|discount|markup)$',
                r'^(email|phone|contact_.*|address)$',
                r'^(payment_terms|credit_limit)$',
                r'^(contract_.*|agreement_.*)$',
            ],
            DataSensitivityLevel.RESTRICTED: [
                r'^(tax_id|personal_id|ssn|ein)$',
                r'^(bank_account|routing_number|iban)$',
                r'^(api_key|token|password|secret)$',
                r'^(internal_notes|confidential_.*|proprietary_.*)$',
                r'^(salary|compensation|bonus)$',
            ]
        }
        
        # Field-specific overrides
        self.field_overrides = {
            'po_number': DataSensitivityLevel.INTERNAL,
            'order_number': DataSensitivityLevel.INTERNAL,
            'tracking_number': DataSensitivityLevel.INTERNAL,
            'public_notes': DataSensitivityLevel.PUBLIC,
            'general_description': DataSensitivityLevel.PUBLIC,
        }
    
    def classify_fields(
        self, 
        data: Dict[str, Any], 
        entity_type: str
    ) -> Dict[str, DataSensitivityLevel]:
        """
        Classify all fields in a data object by sensitivity level.
        
        Args:
            data: Data object to classify
            entity_type: Type of entity (e.g., 'purchase_order', 'company')
            
        Returns:
            Dictionary mapping field names to sensitivity levels
        """
        classifications = {}
        
        for field_name, field_value in data.items():
            sensitivity = self.classify_single_field(field_name, field_value, entity_type)
            classifications[field_name] = sensitivity
        
        logger.debug(f"Classified {len(classifications)} fields for {entity_type}")
        
        return classifications
    
    def classify_single_field(
        self, 
        field_name: str, 
        field_value: Any, 
        entity_type: str
    ) -> DataSensitivityLevel:
        """
        Classify a single field by sensitivity level.
        
        Args:
            field_name: Name of the field
            field_value: Value of the field
            entity_type: Type of entity
            
        Returns:
            Sensitivity level of the field
        """
        # Check field-specific overrides first
        if field_name.lower() in self.field_overrides:
            return self.field_overrides[field_name.lower()]
        
        # Check database classifications
        db_classification = self._get_database_classification(field_name, entity_type)
        if db_classification:
            return db_classification
        
        # Apply pattern-based classification
        pattern_classification = self._classify_by_patterns(field_name)
        if pattern_classification:
            return pattern_classification
        
        # Apply content-based classification
        content_classification = self._classify_by_content(field_name, field_value)
        if content_classification:
            return content_classification
        
        # Apply entity-specific rules
        entity_classification = self._classify_by_entity_type(field_name, entity_type)
        if entity_classification:
            return entity_classification
        
        # Default to internal if no specific classification found
        return DataSensitivityLevel.INTERNAL
    
    def _get_database_classification(
        self, 
        field_name: str, 
        entity_type: str
    ) -> DataSensitivityLevel:
        """Get classification from database rules."""
        
        classification = self.db.query(DataClassification).filter(
            DataClassification.field_name == field_name,
            DataClassification.entity_type == entity_type,
            DataClassification.is_active == True
        ).first()
        
        if classification:
            return classification.sensitivity_level
        
        # Check for wildcard rules
        wildcard_classification = self.db.query(DataClassification).filter(
            DataClassification.field_name == field_name,
            DataClassification.entity_type == '*',
            DataClassification.is_active == True
        ).first()
        
        if wildcard_classification:
            return wildcard_classification.sensitivity_level
        
        return None
    
    def _classify_by_patterns(self, field_name: str) -> DataSensitivityLevel:
        """Classify field using regex patterns."""
        
        field_lower = field_name.lower()
        
        # Check patterns in order of sensitivity (most sensitive first)
        for sensitivity_level in [
            DataSensitivityLevel.RESTRICTED,
            DataSensitivityLevel.CONFIDENTIAL,
            DataSensitivityLevel.INTERNAL,
            DataSensitivityLevel.PUBLIC
        ]:
            patterns = self.sensitivity_patterns.get(sensitivity_level, [])
            
            for pattern in patterns:
                if re.match(pattern, field_lower):
                    return sensitivity_level
        
        return None
    
    def _classify_by_content(self, field_name: str, field_value: Any) -> DataSensitivityLevel:
        """Classify field based on its content."""
        
        if field_value is None:
            return None
        
        # Convert to string for analysis
        str_value = str(field_value).lower()
        
        # Check for email patterns
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', str_value):
            return DataSensitivityLevel.CONFIDENTIAL
        
        # Check for phone number patterns
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', str_value):
            return DataSensitivityLevel.CONFIDENTIAL
        
        # Check for currency patterns
        if re.search(r'\$\d+|\d+\.\d{2}', str_value):
            return DataSensitivityLevel.CONFIDENTIAL
        
        # Check for ID patterns (long numeric strings)
        if re.search(r'\b\d{9,}\b', str_value):
            return DataSensitivityLevel.RESTRICTED
        
        # Check for sensitive keywords in content
        sensitive_keywords = [
            'confidential', 'proprietary', 'secret', 'private',
            'internal only', 'restricted', 'classified'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in str_value:
                return DataSensitivityLevel.CONFIDENTIAL
        
        return None
    
    def _classify_by_entity_type(self, field_name: str, entity_type: str) -> DataSensitivityLevel:
        """Apply entity-specific classification rules."""
        
        entity_rules = {
            'purchase_order': {
                'po_number': DataSensitivityLevel.INTERNAL,
                'total_amount': DataSensitivityLevel.CONFIDENTIAL,
                'supplier_notes': DataSensitivityLevel.CONFIDENTIAL,
                'buyer_notes': DataSensitivityLevel.CONFIDENTIAL,
            },
            'company': {
                'company_name': DataSensitivityLevel.PUBLIC,
                'tax_id': DataSensitivityLevel.RESTRICTED,
                'revenue': DataSensitivityLevel.CONFIDENTIAL,
                'employee_count': DataSensitivityLevel.INTERNAL,
            },
            'user': {
                'username': DataSensitivityLevel.INTERNAL,
                'email': DataSensitivityLevel.CONFIDENTIAL,
                'role': DataSensitivityLevel.INTERNAL,
                'last_login': DataSensitivityLevel.INTERNAL,
            },
            'product': {
                'product_name': DataSensitivityLevel.PUBLIC,
                'cost': DataSensitivityLevel.CONFIDENTIAL,
                'supplier_cost': DataSensitivityLevel.RESTRICTED,
                'specifications': DataSensitivityLevel.INTERNAL,
            }
        }
        
        entity_specific_rules = entity_rules.get(entity_type, {})
        return entity_specific_rules.get(field_name.lower())
    
    def get_field_sensitivity_summary(
        self, 
        data: Dict[str, Any], 
        entity_type: str
    ) -> Dict[str, Any]:
        """Get a summary of field sensitivity levels."""
        
        classifications = self.classify_fields(data, entity_type)
        
        summary = {
            'total_fields': len(classifications),
            'by_sensitivity': {},
            'sensitive_field_count': 0,
            'public_field_count': 0,
        }
        
        # Count by sensitivity level
        for sensitivity in DataSensitivityLevel:
            count = sum(1 for level in classifications.values() if level == sensitivity)
            summary['by_sensitivity'][sensitivity.value] = count
        
        # Calculate aggregate metrics
        summary['sensitive_field_count'] = sum(
            count for level, count in summary['by_sensitivity'].items()
            if level in ['confidential', 'restricted']
        )
        
        summary['public_field_count'] = summary['by_sensitivity'].get('public', 0)
        
        # Calculate sensitivity ratio
        if summary['total_fields'] > 0:
            summary['sensitivity_ratio'] = summary['sensitive_field_count'] / summary['total_fields']
        else:
            summary['sensitivity_ratio'] = 0.0
        
        return summary
    
    def suggest_field_reclassification(
        self, 
        field_name: str, 
        current_level: DataSensitivityLevel,
        entity_type: str,
        field_value: Any = None
    ) -> Dict[str, Any]:
        """Suggest reclassification for a field."""
        
        # Re-classify the field
        suggested_level = self.classify_single_field(field_name, field_value, entity_type)
        
        suggestion = {
            'field_name': field_name,
            'current_level': current_level.value,
            'suggested_level': suggested_level.value,
            'needs_reclassification': current_level != suggested_level,
            'reasoning': []
        }
        
        if current_level != suggested_level:
            if suggested_level.value > current_level.value:
                suggestion['reasoning'].append(f"Field appears more sensitive than currently classified")
            else:
                suggestion['reasoning'].append(f"Field appears less sensitive than currently classified")
        
        return suggestion
