"""
Universal Farm Management Service

This service handles farm-level traceability for ANY company type,
enabling brands, traders, processors, cooperatives, mills, and originators
to manage individual farms/plantations for regulatory compliance.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.location import Location
from app.models.batch import Batch
from app.models.batch_farm_contribution import BatchFarmContribution
from app.models.company import Company
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


class FarmManagementService:
    """Service for managing farm-level traceability for any company type"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _normalize_certifications(self, certifications) -> Dict[str, Any]:
        """
        Normalize certifications to always return a dictionary format.
        
        Args:
            certifications: Can be None, list, or dict
            
        Returns:
            Dict with normalized certification data
        """
        if not certifications:
            return {}
        
        if isinstance(certifications, list):
            # Convert list to dict format
            return {
                "certifications": certifications,
                "certification_count": len(certifications)
            }
        elif isinstance(certifications, dict):
            return certifications
        else:
            return {}
    
    def get_company_capabilities(self, company_id: UUID) -> Dict[str, Any]:
        """
        Determine what a company can do based on its type and farm structure
        
        Args:
            company_id: ID of the company to check
            
        Returns:
            Dict with company capabilities
        """
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        has_farms = self._has_farm_locations(company_id)
        farm_types = self._get_company_farm_types(company_id) if has_farms else []
        
        # Universal capabilities - ANY company type can have farms
        return {
            "company_id": str(company_id),
            "company_name": company.name,
            "company_type": company.company_type,
            "can_create_pos": company.company_type in ['brand', 'trader', 'processor', 'cooperative', 'mill', 'originator'],
            "can_confirm_pos": company.company_type in ['processor', 'originator', 'cooperative', 'mill'],
            "has_farm_structure": has_farms,
            "is_farm_capable": True,  # ANY company can have farms
            "farm_types": farm_types,
            "can_act_as_originator": has_farms or company.company_type == 'originator',
            "total_farms": self._count_company_farms(company_id),
            "total_farm_area_hectares": self._get_total_farm_area(company_id)
        }
    
    def get_company_farms(self, company_id: UUID, current_user: User = None) -> List[Dict[str, Any]]:
        """
        Get all farms for a company using universal access control
        
        Args:
            company_id: ID of the company
            current_user: Current user object (for access control)
            
        Returns:
            List of farm information
        """
        # If current_user is provided, use universal access control
        if current_user:
            from app.services.universal_access_control import UniversalAccessControl, AccessLevel
            
            access_control = UniversalAccessControl(self.db)
            decision = access_control.can_access_farm_data(current_user, company_id, AccessLevel.READ)
            
            if not decision.allowed:
                raise PermissionError(f"Access denied: {decision.reason}")
            
            # Log the access attempt
            access_control.log_access_attempt(current_user, "farm_data", company_id, decision)
        
        farms = self.db.query(Location).filter(
            and_(
                Location.company_id == company_id,
                Location.is_farm_location == True,
                Location.is_active == True
            )
        ).all()
        
        return [
            {
                "farm_id": str(farm.id),
                "farm_name": farm.name,
                "farm_type": farm.farm_type,
                "farm_size_hectares": float(farm.farm_size_hectares) if farm.farm_size_hectares else None,
                "specialization": farm.specialization,
                "coordinates": {
                    "latitude": float(farm.latitude) if farm.latitude else None,
                    "longitude": float(farm.longitude) if farm.longitude else None,
                    "accuracy_meters": float(farm.accuracy_meters) if farm.accuracy_meters else None
                },
                "farm_owner": farm.farm_owner_name,
                "established_year": farm.established_year,
                "registration_number": farm.registration_number,
                "certifications": self._normalize_certifications(farm.certifications),
                "compliance_data": farm.compliance_data or {},
                "location": {
                    "address": farm.address,
                    "city": farm.city,
                    "country": farm.country
                },
                "created_at": farm.created_at.isoformat()
            }
            for farm in farms
        ]
    
    def create_farm(
        self, 
        farm_data: Dict[str, Any], 
        company_id: UUID, 
        user_id: UUID
    ) -> Location:
        """
        Create a new farm/plantation location
        
        Args:
            farm_data: Farm information from the form
            company_id: ID of the company creating the farm
            user_id: ID of the user creating the farm
            
        Returns:
            Created Location object
        """
        # Validate required fields
        required_fields = ['farm_name', 'farm_size_hectares', 'establishment_year', 'owner_name']
        for field in required_fields:
            if not farm_data.get(field):
                raise ValueError(f"Required field '{field}' is missing")
        
        # Create the farm location
        farm = Location(
            name=farm_data['farm_name'],
            location_type='farm',
            is_farm_location=True,
            company_id=company_id,
            created_by_user_id=user_id,
            
            # Basic farm information
            farm_type=farm_data.get('plantation_type', 'smallholder'),
            farm_size_hectares=farm_data['farm_size_hectares'],
            established_year=farm_data['establishment_year'],
            registration_number=farm_data.get('registration_number'),
            specialization=farm_data.get('specialization'),
            farm_owner_name=farm_data.get('farm_owner_name') or farm_data['owner_name'],
            
            # Location information
            address=farm_data.get('address'),
            city=farm_data.get('city'),
            state_province=farm_data.get('state_province'),
            country=farm_data.get('country'),
            postal_code=farm_data.get('postal_code'),
            
            # GPS coordinates
            latitude=farm_data.get('gps_coordinates', {}).get('latitude'),
            longitude=farm_data.get('gps_coordinates', {}).get('longitude'),
            accuracy_meters=farm_data.get('accuracy_meters'),
            elevation_meters=farm_data.get('elevation_meters'),
            
            # Contact information
            farm_contact_info={
                'phone': farm_data.get('farm_contact_info', {}).get('phone'),
                'email': farm_data.get('farm_contact_info', {}).get('email'),
                'address': farm_data.get('farm_contact_info', {}).get('address')
            },
            
            # Certifications and compliance
            certifications=farm_data.get('certification_status', []),
            compliance_status=farm_data.get('compliance_status', 'pending'),
            
            # Status and notes
            is_active=farm_data.get('is_active', True),
            notes=farm_data.get('notes')
        )
        
        self.db.add(farm)
        self.db.commit()
        self.db.refresh(farm)
        
        logger.info(
            "Farm created successfully",
            farm_id=str(farm.id),
            farm_name=farm.name,
            company_id=str(company_id),
            user_id=str(user_id)
        )
        
        return farm
    
    def create_batch_with_farm_contributions(
        self, 
        batch_data: Dict[str, Any], 
        farm_contributions: List[Dict[str, Any]],
        company_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Create a batch with farm-level contributions
        
        Args:
            batch_data: Basic batch information
            farm_contributions: List of farm contributions
            company_id: ID of the company creating the batch
            user_id: ID of the user creating the batch
            
        Returns:
            Dict with batch creation result
        """
        # Create the batch
        batch = Batch(
            batch_id=batch_data["batch_id"],
            batch_type=batch_data.get("batch_type", "harvest"),
            company_id=company_id,
            product_id=batch_data["product_id"],
            quantity=batch_data["quantity"],
            unit=batch_data["unit"],
            production_date=batch_data["production_date"],
            location_name=batch_data.get("location_name"),
            location_coordinates=batch_data.get("location_coordinates"),
            origin_data=batch_data.get("origin_data"),
            certifications=batch_data.get("certifications"),
            created_by_user_id=user_id
        )
        
        self.db.add(batch)
        self.db.flush()  # Get the batch ID
        
        # Create farm contributions
        created_contributions = []
        total_contributed = 0
        
        for contribution in farm_contributions:
            farm_contribution = BatchFarmContribution(
                batch_id=batch.id,
                location_id=contribution["location_id"],
                quantity_contributed=contribution["quantity_contributed"],
                unit=contribution["unit"],
                contribution_percentage=contribution.get("contribution_percentage"),
                farm_data=contribution.get("farm_data", {}),
                compliance_status=contribution.get("compliance_status", "pending")
            )
            
            self.db.add(farm_contribution)
            created_contributions.append(farm_contribution)
            total_contributed += float(contribution["quantity_contributed"])
        
        # Verify total contributions match batch quantity
        if abs(total_contributed - float(batch.quantity)) > 0.001:
            raise ValueError(f"Total farm contributions ({total_contributed}) does not match batch quantity ({batch.quantity})")
        
        self.db.commit()
        
        return {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_id,
            "total_quantity": float(batch.quantity),
            "farm_contributions": len(created_contributions),
            "contributions": [
                {
                    "farm_id": str(contrib.location_id),
                    "quantity_contributed": float(contrib.quantity_contributed),
                    "contribution_percentage": float(contrib.contribution_percentage) if contrib.contribution_percentage else None,
                    "compliance_status": contrib.compliance_status
                }
                for contrib in created_contributions
            ]
        }
    
    def get_batch_farm_traceability(self, batch_id: UUID) -> Dict[str, Any]:
        """
        Get complete farm-level traceability for a batch
        
        Args:
            batch_id: ID of the batch
            
        Returns:
            Dict with complete farm traceability information
        """
        batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        # Get farm contributions
        contributions = self.db.query(BatchFarmContribution).filter(
            BatchFarmContribution.batch_id == batch_id
        ).all()
        
        farm_details = []
        for contrib in contributions:
            farm = contrib.location
            farm_details.append({
                "farm_id": str(farm.id),
                "farm_name": farm.name,
                "farm_type": farm.farm_type,
                "farm_owner": farm.farm_owner_name,
                "quantity_contributed": float(contrib.quantity_contributed),
                "contribution_percentage": float(contrib.contribution_percentage) if contrib.contribution_percentage else None,
                "coordinates": {
                    "latitude": float(farm.latitude) if farm.latitude else None,
                    "longitude": float(farm.longitude) if farm.longitude else None
                },
                "farm_size_hectares": float(farm.farm_size_hectares) if farm.farm_size_hectares else None,
                "specialization": farm.specialization,
                "certifications": self._normalize_certifications(farm.certifications),
                "compliance_status": contrib.compliance_status,
                "compliance_data": contrib.farm_data or {}
            })
        
        return {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_id,
            "total_quantity": float(batch.quantity),
            "unit": batch.unit,
            "production_date": batch.production_date.isoformat(),
            "company": batch.company.name,
            "company_type": batch.company.company_type,
            "farm_contributions": len(farm_details),
            "farms": farm_details,
            "regulatory_compliance": {
                "eudr_ready": all(farm["compliance_status"] == "verified" for farm in farm_details),
                "us_ready": all(farm["compliance_status"] == "verified" for farm in farm_details),
                "total_farms": len(farm_details),
                "verified_farms": len([f for f in farm_details if f["compliance_status"] == "verified"])
            }
        }
    
    def _has_farm_locations(self, company_id: UUID) -> bool:
        """Check if company has farm locations"""
        count = self.db.query(Location).filter(
            and_(
                Location.company_id == company_id,
                Location.is_farm_location == True,
                Location.is_active == True
            )
        ).count()
        return count > 0
    
    def _get_company_farm_types(self, company_id: UUID) -> List[str]:
        """Get unique farm types for a company"""
        farm_types = self.db.query(Location.farm_type).filter(
            and_(
                Location.company_id == company_id,
                Location.is_farm_location == True,
                Location.is_active == True,
                Location.farm_type.isnot(None)
            )
        ).distinct().all()
        
        return [farm_type[0] for farm_type in farm_types]
    
    def _count_company_farms(self, company_id: UUID) -> int:
        """Count total farms for a company"""
        return self.db.query(Location).filter(
            and_(
                Location.company_id == company_id,
                Location.is_farm_location == True,
                Location.is_active == True
            )
        ).count()
    
    def _get_total_farm_area(self, company_id: UUID) -> float:
        """Get total farm area in hectares for a company"""
        result = self.db.query(Location.farm_size_hectares).filter(
            and_(
                Location.company_id == company_id,
                Location.is_farm_location == True,
                Location.is_active == True,
                Location.farm_size_hectares.isnot(None)
            )
        ).all()
        
        return sum(float(area[0]) for area in result if area[0] is not None)
