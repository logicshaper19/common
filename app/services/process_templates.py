"""
Process Templates Service for automatic template application and management.
"""
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.transformation_versioning import TransformationProcessTemplate
from app.models.transformation import TransformationEvent, TransformationType
from app.schemas.transformation_versioning import (
    TransformationProcessTemplateCreate, TemplateUsageRequest
)

logger = get_logger(__name__)


class ProcessTemplateEngine:
    """Engine for processing and applying transformation templates."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_standard_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get pre-defined standard templates for common transformation types."""
        return {
            'HARVEST': {
                'template_name': 'Standard Palm Oil Harvest',
                'transformation_type': 'HARVEST',
                'company_type': 'plantation',
                'template_config': {
                    'required_fields': [
                        'farm_id', 'gps_coordinates', 'harvest_date', 
                        'yield_per_hectare', 'ffb_quality_grade'
                    ],
                    'optional_fields': [
                        'weather_conditions', 'harvest_method', 'worker_count',
                        'equipment_used', 'harvest_notes'
                    ],
                    'validation_rules': {
                        'yield_per_hectare': {'min': 10.0, 'max': 35.0},
                        'ffb_quality_grade': {'allowed_values': ['A', 'B', 'C']},
                        'gps_coordinates': {'required': True, 'format': 'lat_lng'}
                    },
                    'default_values': {
                        'harvest_method': 'manual',
                        'worker_count': 8,
                        'equipment_used': ['machete', 'collection_baskets']
                    }
                },
                'default_metrics': {
                    'yield_per_hectare': 25.0,
                    'oer_potential': 23.0,
                    'ffb_quality_grade': 'A',
                    'moisture_content': 16.0,
                    'free_fatty_acid': 2.0
                },
                'cost_estimates': {
                    'labor_cost_per_hectare': 150.0,
                    'fuel_cost_per_hectare': 25.0,
                    'equipment_cost_per_hectare': 50.0,
                    'total_cost_per_hectare': 225.0
                },
                'quality_standards': {
                    'min_yield_per_hectare': 20.0,
                    'max_moisture_content': 18.0,
                    'min_oer_potential': 20.0,
                    'max_free_fatty_acid': 3.0
                }
            },
            
            'MILLING': {
                'template_name': 'Standard Palm Oil Milling',
                'transformation_type': 'MILLING',
                'company_type': 'mill',
                'template_config': {
                    'required_fields': [
                        'extraction_rate', 'ffb_quantity', 'cpo_quantity',
                        'energy_consumed', 'water_consumed'
                    ],
                    'optional_fields': [
                        'processing_time_hours', 'equipment_used', 'maintenance_status',
                        'operator_notes', 'quality_control_tests'
                    ],
                    'validation_rules': {
                        'extraction_rate': {'min': 15.0, 'max': 30.0},
                        'ffb_quantity': {'min': 1.0, 'max': 1000.0},
                        'energy_consumed': {'min': 0.0, 'max': 10000.0}
                    },
                    'default_values': {
                        'processing_time_hours': 8.0,
                        'equipment_used': ['sterilizer', 'thresher', 'press', 'clarifier'],
                        'maintenance_status': 'operational'
                    }
                },
                'default_metrics': {
                    'extraction_rate': 23.0,
                    'cpo_ffa_level': 1.8,
                    'nut_fibre_boiler_ratio': 95.0,
                    'uptime_percentage': 96.0,
                    'energy_efficiency': 0.85
                },
                'cost_estimates': {
                    'energy_cost_per_tonne': 25.0,
                    'water_cost_per_tonne': 5.0,
                    'labor_cost_per_tonne': 15.0,
                    'maintenance_cost_per_tonne': 10.0,
                    'total_cost_per_tonne': 55.0
                },
                'quality_standards': {
                    'min_extraction_rate': 20.0,
                    'max_cpo_ffa': 2.5,
                    'min_boiler_ratio': 90.0,
                    'min_uptime_percentage': 90.0
                }
            },
            
            'REFINING': {
                'template_name': 'Standard Palm Oil Refining',
                'transformation_type': 'REFINING',
                'company_type': 'refinery',
                'template_config': {
                    'required_fields': [
                        'process_type', 'input_quantity', 'output_quantity',
                        'refining_loss', 'iv_value'
                    ],
                    'optional_fields': [
                        'chemicals_used', 'temperature_profile', 'pressure_profile',
                        'processing_time', 'quality_control_results'
                    ],
                    'validation_rules': {
                        'refining_loss': {'min': 0.5, 'max': 3.0},
                        'iv_value': {'min': 45.0, 'max': 60.0},
                        'input_quantity': {'min': 1.0, 'max': 500.0}
                    },
                    'default_values': {
                        'process_type': 'physical_refining',
                        'temperature_profile': '180-220°C',
                        'pressure_profile': '2-5 bar'
                    }
                },
                'default_metrics': {
                    'refining_loss': 1.0,
                    'iv_value': 52.0,
                    'olein_yield': 80.0,
                    'stearin_yield': 20.0,
                    'color_reduction': 95.0
                },
                'cost_estimates': {
                    'energy_cost_per_tonne': 30.0,
                    'chemical_cost_per_tonne': 20.0,
                    'labor_cost_per_tonne': 25.0,
                    'total_cost_per_tonne': 75.0
                },
                'quality_standards': {
                    'max_refining_loss': 1.5,
                    'iv_tolerance': 0.5,
                    'min_olein_yield': 75.0,
                    'min_color_reduction': 90.0
                }
            },
            
            'FRACTIONATION': {
                'template_name': 'Standard Palm Oil Fractionation',
                'transformation_type': 'FRACTIONATION',
                'company_type': 'refinery',
                'template_config': {
                    'required_fields': [
                        'fractionation_type', 'input_quantity', 'olein_quantity', 'stearin_quantity',
                        'fractionation_temperature', 'cooling_rate'
                    ],
                    'optional_fields': [
                        'crystallization_time', 'filtration_method', 'packaging_type',
                        'quality_control_tests', 'operator_notes'
                    ],
                    'validation_rules': {
                        'fractionation_temperature': {'min': 20.0, 'max': 35.0},
                        'cooling_rate': {'min': 0.1, 'max': 2.0},
                        'olein_yield': {'min': 70.0, 'max': 90.0}
                    },
                    'default_values': {
                        'fractionation_type': 'dry_fractionation',
                        'crystallization_time': 24.0,
                        'filtration_method': 'vacuum_filtration'
                    }
                },
                'default_metrics': {
                    'olein_yield': 80.0,
                    'stearin_yield': 20.0,
                    'fractionation_efficiency': 95.0,
                    'olein_iv': 58.0,
                    'stearin_iv': 35.0
                },
                'cost_estimates': {
                    'energy_cost_per_tonne': 35.0,
                    'labor_cost_per_tonne': 20.0,
                    'packaging_cost_per_tonne': 15.0,
                    'total_cost_per_tonne': 70.0
                },
                'quality_standards': {
                    'min_olein_yield': 75.0,
                    'min_fractionation_efficiency': 90.0,
                    'olein_iv_range': [55.0, 62.0],
                    'stearin_iv_range': [30.0, 40.0]
                }
            },
            
            'BLENDING': {
                'template_name': 'Standard Palm Oil Blending',
                'transformation_type': 'BLENDING',
                'company_type': 'manufacturer',
                'template_config': {
                    'required_fields': [
                        'blend_recipe', 'total_quantity', 'blend_ratio',
                        'target_specifications', 'blending_method'
                    ],
                    'optional_fields': [
                        'blending_temperature', 'mixing_time', 'quality_control_tests',
                        'packaging_requirements', 'batch_number'
                    ],
                    'validation_rules': {
                        'total_quantity': {'min': 0.1, 'max': 100.0},
                        'blend_ratio': {'sum_must_equal': 1.0},
                        'blending_temperature': {'min': 40.0, 'max': 80.0}
                    },
                    'default_values': {
                        'blending_method': 'mechanical_mixing',
                        'blending_temperature': 60.0,
                        'mixing_time': 30.0
                    }
                },
                'default_metrics': {
                    'blend_accuracy': 99.5,
                    'homogeneity': 98.0,
                    'color_consistency': 95.0,
                    'viscosity_consistency': 97.0
                },
                'cost_estimates': {
                    'energy_cost_per_tonne': 15.0,
                    'labor_cost_per_tonne': 10.0,
                    'packaging_cost_per_tonne': 20.0,
                    'total_cost_per_tonne': 45.0
                },
                'quality_standards': {
                    'min_blend_accuracy': 99.0,
                    'min_homogeneity': 95.0,
                    'min_color_consistency': 90.0,
                    'max_viscosity_variance': 5.0
                }
            }
        }
    
    def create_standard_templates(self) -> List[TransformationProcessTemplate]:
        """Create standard templates in the database."""
        created_templates = []
        standard_templates = self.get_standard_templates()
        
        for transformation_type, template_data in standard_templates.items():
            # Check if template already exists
            existing = self.db.query(TransformationProcessTemplate).filter(
                TransformationProcessTemplate.template_name == template_data['template_name']
            ).first()
            
            if not existing:
                template = TransformationProcessTemplate(
                    template_name=template_data['template_name'],
                    transformation_type=template_data['transformation_type'],
                    company_type=template_data['company_type'],
                    template_config=template_data['template_config'],
                    default_metrics=template_data['default_metrics'],
                    cost_estimates=template_data['cost_estimates'],
                    quality_standards=template_data['quality_standards'],
                    description=f"Standard {transformation_type.lower()} process template",
                    version="1.0",
                    is_standard=True,
                    is_active=True,
                    created_by_user_id=UUID('00000000-0000-0000-0000-000000000000')  # System user
                )
                
                self.db.add(template)
                created_templates.append(template)
        
        self.db.commit()
        logger.info(f"Created {len(created_templates)} standard templates")
        return created_templates
    
    def auto_apply_template(self, transformation_event: TransformationEvent) -> Dict[str, Any]:
        """Automatically apply the most appropriate template for a transformation event."""
        try:
            # Find the best matching template
            template = self._find_best_template(
                transformation_event.transformation_type,
                transformation_event.company_id
            )
            
            if not template:
                return {'applied': False, 'reason': 'No suitable template found'}
            
            # Apply template configuration
            applied_config = self._apply_template_to_transformation(template, transformation_event)
            
            # Update template usage statistics
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            self.db.commit()
            
            return {
                'applied': True,
                'template_id': str(template.id),
                'template_name': template.template_name,
                'applied_config': applied_config
            }
            
        except Exception as e:
            logger.error(f"Error auto-applying template: {e}")
            return {'applied': False, 'reason': str(e)}
    
    def _find_best_template(self, transformation_type: str, company_id: UUID) -> Optional[TransformationProcessTemplate]:
        """Find the best matching template for a transformation type and company."""
        # First, try to find a company-specific template
        company_template = self.db.query(TransformationProcessTemplate).filter(
            TransformationProcessTemplate.transformation_type == transformation_type,
            TransformationProcessTemplate.is_active == True,
            TransformationProcessTemplate.is_standard == False  # Company-specific
        ).first()
        
        if company_template:
            return company_template
        
        # Fall back to standard template
        standard_template = self.db.query(TransformationProcessTemplate).filter(
            TransformationProcessTemplate.transformation_type == transformation_type,
            TransformationProcessTemplate.is_active == True,
            TransformationProcessTemplate.is_standard == True
        ).first()
        
        return standard_template
    
    def _apply_template_to_transformation(self, template: TransformationProcessTemplate, 
                                        transformation_event: TransformationEvent) -> Dict[str, Any]:
        """Apply template configuration to a transformation event."""
        applied_config = {}
        
        # Apply template configuration
        if template.template_config:
            transformation_event.process_parameters = (
                transformation_event.process_parameters or {}
            ).update(template.template_config)
            applied_config['process_parameters'] = template.template_config
        
        # Apply default metrics
        if template.default_metrics:
            transformation_event.quality_metrics = (
                transformation_event.quality_metrics or {}
            ).update(template.default_metrics)
            applied_config['quality_metrics'] = template.default_metrics
        
        # Apply cost estimates
        if template.cost_estimates:
            transformation_event.efficiency_metrics = (
                transformation_event.efficiency_metrics or {}
            ).update(template.cost_estimates)
            applied_config['efficiency_metrics'] = template.cost_estimates
        
        # Apply quality standards
        if template.quality_standards:
            if not transformation_event.compliance_data:
                transformation_event.compliance_data = {}
            transformation_event.compliance_data.update(template.quality_standards)
            applied_config['compliance_data'] = template.quality_standards
        
        self.db.commit()
        return applied_config
    
    def validate_template_application(self, template_id: UUID, 
                                   transformation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that transformation data meets template requirements."""
        template = self.db.query(TransformationProcessTemplate).filter(
            TransformationProcessTemplate.id == template_id
        ).first()
        
        if not template:
            return {'valid': False, 'errors': ['Template not found']}
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_fields': [],
            'invalid_fields': []
        }
        
        # Check required fields
        if 'required_fields' in template.template_config:
            required_fields = template.template_config['required_fields']
            for field in required_fields:
                if field not in transformation_data:
                    validation_result['missing_fields'].append(field)
                    validation_result['valid'] = False
        
        # Check validation rules
        if 'validation_rules' in template.template_config:
            validation_rules = template.template_config['validation_rules']
            for field, rules in validation_rules.items():
                if field in transformation_data:
                    value = transformation_data[field]
                    
                    # Check min/max values
                    if 'min' in rules and value < rules['min']:
                        validation_result['invalid_fields'].append(f"{field} below minimum ({rules['min']})")
                        validation_result['valid'] = False
                    
                    if 'max' in rules and value > rules['max']:
                        validation_result['invalid_fields'].append(f"{field} above maximum ({rules['max']})")
                        validation_result['valid'] = False
                    
                    # Check allowed values
                    if 'allowed_values' in rules and value not in rules['allowed_values']:
                        validation_result['invalid_fields'].append(f"{field} not in allowed values ({rules['allowed_values']})")
                        validation_result['valid'] = False
        
        # Check sum validation (for blend ratios, etc.)
        if 'sum_must_equal' in template.template_config.get('validation_rules', {}):
            sum_rule = template.template_config['validation_rules']['sum_must_equal']
            if 'blend_ratio' in transformation_data:
                ratio_sum = sum(transformation_data['blend_ratio'].values())
                if abs(ratio_sum - sum_rule) > 0.01:  # Allow small floating point errors
                    validation_result['invalid_fields'].append(f"Blend ratio sum must equal {sum_rule}, got {ratio_sum}")
                    validation_result['valid'] = False
        
        return validation_result
    
    def get_template_recommendations(self, transformation_type: str, 
                                   company_type: str) -> List[Dict[str, Any]]:
        """Get template recommendations based on transformation type and company type."""
        templates = self.db.query(TransformationProcessTemplate).filter(
            TransformationProcessTemplate.transformation_type == transformation_type,
            TransformationProcessTemplate.is_active == True
        ).all()
        
        recommendations = []
        for template in templates:
            score = 0
            
            # Base score for matching transformation type
            score += 50
            
            # Bonus for matching company type
            if template.company_type == company_type:
                score += 30
            
            # Bonus for standard templates (more reliable)
            if template.is_standard:
                score += 20
            
            # Bonus for high usage (proven)
            if template.usage_count > 10:
                score += 10
            
            recommendations.append({
                'template_id': str(template.id),
                'template_name': template.template_name,
                'company_type': template.company_type,
                'is_standard': template.is_standard,
                'usage_count': template.usage_count,
                'score': score,
                'description': template.description
            })
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations


