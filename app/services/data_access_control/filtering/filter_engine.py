"""
Data filtering engine for access control.
"""
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.data_access import DataSensitivityLevel, DataCategory
from ..domain.models import DataFilterContext, AccessDecision
from ..domain.enums import FilteringStrategy
from .field_classifier import FieldClassifier
from .sensitivity_analyzer import SensitivityAnalyzer
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataFilterEngine:
    """Engine for filtering sensitive data based on access permissions."""
    
    def __init__(self, db: Session):
        """Initialize data filter engine."""
        self.db = db
        self.field_classifier = FieldClassifier(db)
        self.sensitivity_analyzer = SensitivityAnalyzer(db)
    
    def filter_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        access_decision: AccessDecision,
        entity_type: str,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Filter data based on access decision and permissions.
        
        Args:
            data: Data to filter (single dict or list of dicts)
            access_decision: Access decision with filtering requirements
            entity_type: Type of entity being filtered
            requesting_company_id: Company requesting the data
            target_company_id: Company that owns the data
            
        Returns:
            Filtered data
        """
        if not access_decision.requires_filtering:
            logger.debug("No filtering required, returning original data")
            return data
        
        logger.info(
            f"Filtering {entity_type} data with strategy: {access_decision.filtering_strategy}"
        )
        
        # Handle single item vs list
        is_list = isinstance(data, list)
        data_items = data if is_list else [data]
        
        filtered_items = []
        for item in data_items:
            filtered_item = self._filter_single_item(
                item,
                access_decision,
                entity_type,
                requesting_company_id,
                target_company_id
            )
            filtered_items.append(filtered_item)
        
        result = filtered_items if is_list else filtered_items[0]
        
        logger.info(f"Filtered {len(data_items)} items")
        
        return result
    
    def _filter_single_item(
        self,
        item: Dict[str, Any],
        access_decision: AccessDecision,
        entity_type: str,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Filter a single data item."""
        
        # Create filter context
        context = DataFilterContext(
            original_data=item.copy(),
            requested_fields=list(item.keys()),
            field_sensitivity_map=self.field_classifier.classify_fields(item, entity_type)
        )
        
        # Apply filtering strategy
        if access_decision.filtering_strategy == FilteringStrategy.FIELD_LEVEL:
            filtered_data = self._apply_field_level_filtering(
                context, 
                access_decision,
                requesting_company_id,
                target_company_id
            )
        elif access_decision.filtering_strategy == FilteringStrategy.ENTITY_LEVEL:
            filtered_data = self._apply_entity_level_filtering(
                context,
                access_decision,
                requesting_company_id,
                target_company_id
            )
        elif access_decision.filtering_strategy == FilteringStrategy.AGGREGATION_ONLY:
            filtered_data = self._apply_aggregation_filtering(
                context,
                access_decision
            )
        else:
            filtered_data = item.copy()
        
        # Update context with results
        context.filtered_data = filtered_data
        context.filtering_applied = True
        context.filtered_fields = [
            field for field in context.original_data.keys()
            if field not in filtered_data
        ]
        
        return filtered_data
    
    def _apply_field_level_filtering(
        self,
        context: DataFilterContext,
        access_decision: AccessDecision,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Apply field-level filtering."""
        
        filtered_data = {}
        
        for field_name, field_value in context.original_data.items():
            field_sensitivity = context.field_sensitivity_map.get(
                field_name, 
                DataSensitivityLevel.PUBLIC
            )
            
            # Check if field should be included
            if self._should_include_field(
                field_name,
                field_sensitivity,
                access_decision,
                requesting_company_id,
                target_company_id
            ):
                # Apply field-specific transformations if needed
                transformed_value = self._transform_field_value(
                    field_name,
                    field_value,
                    field_sensitivity,
                    access_decision
                )
                filtered_data[field_name] = transformed_value
            else:
                logger.debug(f"Filtered out field: {field_name} (sensitivity: {field_sensitivity})")
        
        return filtered_data
    
    def _apply_entity_level_filtering(
        self,
        context: DataFilterContext,
        access_decision: AccessDecision,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Apply entity-level filtering."""
        
        # Calculate overall sensitivity of the entity
        overall_sensitivity = self.sensitivity_analyzer.calculate_entity_sensitivity(
            context.original_data,
            context.field_sensitivity_map
        )
        
        # Determine if entire entity should be filtered
        if self._should_filter_entire_entity(
            overall_sensitivity,
            access_decision,
            requesting_company_id,
            target_company_id
        ):
            # Return minimal representation
            return self._create_minimal_entity_representation(context.original_data)
        
        # Return full entity (but could still apply field-level filtering)
        return self._apply_field_level_filtering(
            context,
            access_decision,
            requesting_company_id,
            target_company_id
        )
    
    def _apply_aggregation_filtering(
        self,
        context: DataFilterContext,
        access_decision: AccessDecision
    ) -> Dict[str, Any]:
        """Apply aggregation-only filtering."""
        
        aggregated_data = {}
        
        # Only include aggregatable fields
        for field_name, field_value in context.original_data.items():
            if self._is_aggregatable_field(field_name, field_value):
                # Apply aggregation transformation
                aggregated_value = self._aggregate_field_value(field_name, field_value)
                aggregated_data[field_name] = aggregated_value
        
        return aggregated_data
    
    def _should_include_field(
        self,
        field_name: str,
        field_sensitivity: DataSensitivityLevel,
        access_decision: AccessDecision,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID]
    ) -> bool:
        """Determine if a field should be included in filtered data."""
        
        # Always include public fields
        if field_sensitivity == DataSensitivityLevel.PUBLIC:
            return True
        
        # Check if field is explicitly filtered
        if field_name in access_decision.filtered_fields:
            return False
        
        # Apply sensitivity-based filtering for cross-company access
        if target_company_id and target_company_id != requesting_company_id:
            # More restrictive for cross-company access
            if field_sensitivity in [DataSensitivityLevel.CONFIDENTIAL, DataSensitivityLevel.RESTRICTED]:
                return False
        
        # Check field-specific rules
        return self._check_field_specific_rules(field_name, field_sensitivity)
    
    def _check_field_specific_rules(
        self,
        field_name: str,
        field_sensitivity: DataSensitivityLevel
    ) -> bool:
        """Check field-specific filtering rules."""
        
        # Financial fields require higher permissions
        financial_fields = [
            'price', 'cost', 'total_amount', 'unit_price', 
            'profit_margin', 'discount', 'payment_terms'
        ]
        
        if field_name.lower() in financial_fields:
            return field_sensitivity != DataSensitivityLevel.RESTRICTED
        
        # Personal data fields
        personal_fields = [
            'email', 'phone', 'address', 'contact_person',
            'personal_id', 'tax_id'
        ]
        
        if field_name.lower() in personal_fields:
            return field_sensitivity in [DataSensitivityLevel.PUBLIC, DataSensitivityLevel.INTERNAL]
        
        # Default rule
        return True
    
    def _transform_field_value(
        self,
        field_name: str,
        field_value: Any,
        field_sensitivity: DataSensitivityLevel,
        access_decision: AccessDecision
    ) -> Any:
        """Transform field value based on sensitivity and access level."""
        
        # Apply transformations for sensitive fields
        if field_sensitivity == DataSensitivityLevel.CONFIDENTIAL:
            return self._apply_confidential_transformation(field_name, field_value)
        elif field_sensitivity == DataSensitivityLevel.RESTRICTED:
            return self._apply_restricted_transformation(field_name, field_value)
        
        return field_value
    
    def _apply_confidential_transformation(self, field_name: str, field_value: Any) -> Any:
        """Apply transformation for confidential fields."""
        
        # Mask email addresses
        if field_name.lower() in ['email', 'contact_email'] and isinstance(field_value, str):
            if '@' in field_value:
                local, domain = field_value.split('@', 1)
                return f"{local[:2]}***@{domain}"
        
        # Round financial values
        if field_name.lower() in ['price', 'cost', 'total_amount'] and isinstance(field_value, (int, float)):
            return round(field_value, -2)  # Round to nearest 100
        
        return field_value
    
    def _apply_restricted_transformation(self, field_name: str, field_value: Any) -> Any:
        """Apply transformation for restricted fields."""
        
        # Replace with placeholder for highly sensitive data
        if field_name.lower() in ['tax_id', 'personal_id', 'bank_account']:
            return "[RESTRICTED]"
        
        # Heavily mask contact information
        if field_name.lower() in ['phone', 'mobile'] and isinstance(field_value, str):
            return f"***-***-{field_value[-4:]}" if len(field_value) >= 4 else "[RESTRICTED]"
        
        return field_value
    
    def _should_filter_entire_entity(
        self,
        overall_sensitivity: DataSensitivityLevel,
        access_decision: AccessDecision,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID]
    ) -> bool:
        """Determine if entire entity should be filtered."""
        
        # Filter highly sensitive entities for cross-company access
        if (target_company_id and 
            target_company_id != requesting_company_id and
            overall_sensitivity == DataSensitivityLevel.RESTRICTED):
            return True
        
        return False
    
    def _create_minimal_entity_representation(self, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal representation of filtered entity."""
        
        minimal_fields = ['id', 'name', 'type', 'status']
        minimal_data = {}
        
        for field in minimal_fields:
            if field in original_data:
                minimal_data[field] = original_data[field]
        
        minimal_data['_filtered'] = True
        minimal_data['_reason'] = 'Entity filtered due to sensitivity level'
        
        return minimal_data
    
    def _is_aggregatable_field(self, field_name: str, field_value: Any) -> bool:
        """Check if field can be aggregated."""
        
        # Numeric fields are aggregatable
        if isinstance(field_value, (int, float)):
            return True
        
        # Count-based fields
        if field_name.lower() in ['count', 'quantity', 'total', 'sum']:
            return True
        
        return False
    
    def _aggregate_field_value(self, field_name: str, field_value: Any) -> Any:
        """Apply aggregation to field value."""
        
        # For single values, we can't really aggregate, so return ranges
        if isinstance(field_value, (int, float)):
            # Return range instead of exact value
            if field_value < 100:
                return "< 100"
            elif field_value < 1000:
                return "100-1000"
            elif field_value < 10000:
                return "1000-10000"
            else:
                return "> 10000"
        
        return field_value
