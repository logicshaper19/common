"""
Sensitivity analysis for data access control.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.data_access import DataSensitivityLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


class SensitivityAnalyzer:
    """Analyzes data sensitivity for access control decisions."""
    
    def __init__(self, db: Session):
        """Initialize sensitivity analyzer."""
        self.db = db
    
    def calculate_entity_sensitivity(
        self,
        data: Dict[str, Any],
        field_sensitivity_map: Dict[str, DataSensitivityLevel]
    ) -> DataSensitivityLevel:
        """
        Calculate overall sensitivity level for an entity.
        
        Args:
            data: Entity data
            field_sensitivity_map: Map of field names to sensitivity levels
            
        Returns:
            Overall sensitivity level for the entity
        """
        if not field_sensitivity_map:
            return DataSensitivityLevel.OPERATIONAL
        
        # Get sensitivity levels of all fields
        sensitivity_levels = list(field_sensitivity_map.values())
        
        # Count fields by sensitivity
        sensitivity_counts = {
            DataSensitivityLevel.PUBLIC: 0,
            DataSensitivityLevel.OPERATIONAL: 0,
            DataSensitivityLevel.CONFIDENTIAL: 0,
            DataSensitivityLevel.RESTRICTED: 0,
        }
        
        for level in sensitivity_levels:
            sensitivity_counts[level] += 1
        
        total_fields = len(sensitivity_levels)
        
        # Determine overall sensitivity based on composition
        if sensitivity_counts[DataSensitivityLevel.RESTRICTED] > 0:
            # Any restricted field makes the entity restricted
            return DataSensitivityLevel.RESTRICTED
        
        if sensitivity_counts[DataSensitivityLevel.CONFIDENTIAL] > total_fields * 0.3:
            # More than 30% confidential fields makes entity confidential
            return DataSensitivityLevel.CONFIDENTIAL
        
        if sensitivity_counts[DataSensitivityLevel.CONFIDENTIAL] > 0:
            # Any confidential fields make entity at least confidential
            return DataSensitivityLevel.CONFIDENTIAL
        
        if sensitivity_counts[DataSensitivityLevel.OPERATIONAL] > total_fields * 0.5:
            # More than 50% internal fields makes entity internal
            return DataSensitivityLevel.OPERATIONAL
        
        # Default to public if mostly public fields
        return DataSensitivityLevel.PUBLIC
    
    def analyze_sensitivity_distribution(
        self,
        field_sensitivity_map: Dict[str, DataSensitivityLevel]
    ) -> Dict[str, Any]:
        """
        Analyze the distribution of sensitivity levels in data.
        
        Args:
            field_sensitivity_map: Map of field names to sensitivity levels
            
        Returns:
            Analysis of sensitivity distribution
        """
        if not field_sensitivity_map:
            return {
                'total_fields': 0,
                'distribution': {},
                'sensitivity_score': 0.0,
                'risk_level': 'low'
            }
        
        # Count by sensitivity level
        distribution = {
            'public': 0,
            'internal': 0,
            'confidential': 0,
            'restricted': 0
        }
        
        for sensitivity in field_sensitivity_map.values():
            distribution[sensitivity.value] += 1
        
        total_fields = len(field_sensitivity_map)
        
        # Calculate sensitivity score (0-1, higher = more sensitive)
        sensitivity_score = (
            distribution['internal'] * 0.25 +
            distribution['confidential'] * 0.5 +
            distribution['restricted'] * 1.0
        ) / total_fields if total_fields > 0 else 0.0
        
        # Determine risk level
        if sensitivity_score >= 0.7:
            risk_level = 'high'
        elif sensitivity_score >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'total_fields': total_fields,
            'distribution': distribution,
            'distribution_percentages': {
                level: (count / total_fields * 100) if total_fields > 0 else 0
                for level, count in distribution.items()
            },
            'sensitivity_score': sensitivity_score,
            'risk_level': risk_level,
            'has_restricted_data': distribution['restricted'] > 0,
            'has_confidential_data': distribution['confidential'] > 0,
        }
    
    def identify_high_risk_fields(
        self,
        data: Dict[str, Any],
        field_sensitivity_map: Dict[str, DataSensitivityLevel],
        threshold: DataSensitivityLevel = DataSensitivityLevel.CONFIDENTIAL
    ) -> List[Dict[str, Any]]:
        """
        Identify fields that pose high risk for data sharing.
        
        Args:
            data: Entity data
            field_sensitivity_map: Map of field names to sensitivity levels
            threshold: Minimum sensitivity level to consider high risk
            
        Returns:
            List of high-risk field information
        """
        high_risk_fields = []
        
        # Define sensitivity order for comparison
        sensitivity_order = {
            DataSensitivityLevel.PUBLIC: 0,
            DataSensitivityLevel.OPERATIONAL: 1,
            DataSensitivityLevel.CONFIDENTIAL: 2,
            DataSensitivityLevel.RESTRICTED: 3,
        }
        
        threshold_level = sensitivity_order[threshold]
        
        for field_name, sensitivity in field_sensitivity_map.items():
            if sensitivity_order[sensitivity] >= threshold_level:
                field_info = {
                    'field_name': field_name,
                    'sensitivity_level': sensitivity.value,
                    'field_value_type': type(data.get(field_name, None)).__name__,
                    'risk_factors': self._identify_field_risk_factors(
                        field_name, 
                        data.get(field_name), 
                        sensitivity
                    )
                }
                high_risk_fields.append(field_info)
        
        # Sort by sensitivity level (most sensitive first)
        high_risk_fields.sort(
            key=lambda x: sensitivity_order[DataSensitivityLevel(x['sensitivity_level'])],
            reverse=True
        )
        
        return high_risk_fields
    
    def _identify_field_risk_factors(
        self,
        field_name: str,
        field_value: Any,
        sensitivity: DataSensitivityLevel
    ) -> List[str]:
        """Identify specific risk factors for a field."""
        
        risk_factors = []
        
        # Sensitivity-based risks
        if sensitivity == DataSensitivityLevel.RESTRICTED:
            risk_factors.append("Contains highly sensitive/restricted data")
        elif sensitivity == DataSensitivityLevel.CONFIDENTIAL:
            risk_factors.append("Contains confidential business information")
        
        # Field name-based risks
        if any(keyword in field_name.lower() for keyword in ['password', 'secret', 'key', 'token']):
            risk_factors.append("Contains authentication/security credentials")
        
        if any(keyword in field_name.lower() for keyword in ['tax', 'ssn', 'personal_id']):
            risk_factors.append("Contains personally identifiable information")
        
        if any(keyword in field_name.lower() for keyword in ['price', 'cost', 'profit', 'revenue']):
            risk_factors.append("Contains sensitive financial information")
        
        # Value-based risks
        if field_value is not None:
            str_value = str(field_value)
            
            if len(str_value) > 1000:
                risk_factors.append("Contains large amount of data")
            
            # Check for patterns that indicate sensitive data
            import re
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', str_value):
                risk_factors.append("Contains email addresses")
            
            if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', str_value):
                risk_factors.append("Contains phone numbers")
        
        return risk_factors
    
    def calculate_sharing_risk_score(
        self,
        field_sensitivity_map: Dict[str, DataSensitivityLevel],
        requesting_company_id: str,
        target_company_id: str,
        relationship_strength: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate risk score for sharing data between companies.
        
        Args:
            field_sensitivity_map: Map of field names to sensitivity levels
            requesting_company_id: Company requesting the data
            target_company_id: Company that owns the data
            relationship_strength: Strength of business relationship (0-1)
            
        Returns:
            Risk assessment for data sharing
        """
        # Base risk calculation
        sensitivity_analysis = self.analyze_sensitivity_distribution(field_sensitivity_map)
        base_risk = sensitivity_analysis['sensitivity_score']
        
        # Adjust for relationship strength
        relationship_risk_adjustment = 1.0 - relationship_strength
        
        # Cross-company sharing inherently increases risk
        cross_company_risk = 0.3 if requesting_company_id != target_company_id else 0.0
        
        # Calculate final risk score
        final_risk_score = min(1.0, base_risk + relationship_risk_adjustment * 0.3 + cross_company_risk)
        
        # Determine risk level
        if final_risk_score >= 0.8:
            risk_level = 'critical'
        elif final_risk_score >= 0.6:
            risk_level = 'high'
        elif final_risk_score >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': final_risk_score,
            'risk_level': risk_level,
            'base_sensitivity_risk': base_risk,
            'relationship_risk_factor': relationship_risk_adjustment,
            'cross_company_risk_factor': cross_company_risk,
            'recommendations': self._generate_risk_recommendations(
                final_risk_score,
                sensitivity_analysis,
                relationship_strength
            )
        }
    
    def _generate_risk_recommendations(
        self,
        risk_score: float,
        sensitivity_analysis: Dict[str, Any],
        relationship_strength: float
    ) -> List[str]:
        """Generate recommendations based on risk assessment."""
        
        recommendations = []
        
        if risk_score >= 0.8:
            recommendations.append("Consider denying access or requiring manual approval")
            recommendations.append("Implement additional authentication measures")
        
        if risk_score >= 0.6:
            recommendations.append("Apply strict field-level filtering")
            recommendations.append("Require explicit consent for sensitive fields")
        
        if sensitivity_analysis['has_restricted_data']:
            recommendations.append("Remove or mask all restricted fields")
        
        if sensitivity_analysis['has_confidential_data']:
            recommendations.append("Apply confidential data transformations")
        
        if relationship_strength < 0.5:
            recommendations.append("Strengthen business relationship before sharing sensitive data")
            recommendations.append("Consider time-limited access permissions")
        
        if not recommendations:
            recommendations.append("Standard access controls are sufficient")
        
        return recommendations
