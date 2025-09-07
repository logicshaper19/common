"""
Sector seeder service for initializing sector templates
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.sector import Sector, SectorTier, SectorProduct
from app.models.user import User
from app.models.company import Company
from app.services.sector_service import PALM_OIL_SECTOR_TEMPLATE, APPAREL_SECTOR_TEMPLATE


class SectorSeeder:
    """Service for seeding sector data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def seed_sector_template(self, template: Dict[str, Any]) -> bool:
        """Seed a complete sector template"""
        try:
            # Create sector
            sector_data = template["sector"]
            existing_sector = self.db.query(Sector).filter(Sector.id == sector_data["id"]).first()
            
            if not existing_sector:
                sector = Sector(**sector_data)
                self.db.add(sector)
                self.db.flush()  # Flush to get the sector in the session
                print(f"Created sector: {sector.name}")
            else:
                sector = existing_sector
                print(f"Sector already exists: {sector.name}")
            
            # Create tiers
            for tier_data in template["tiers"]:
                existing_tier = (
                    self.db.query(SectorTier)
                    .filter(
                        SectorTier.sector_id == tier_data["sector_id"],
                        SectorTier.level == tier_data["level"]
                    )
                    .first()
                )
                
                if not existing_tier:
                    tier = SectorTier(**tier_data)
                    self.db.add(tier)
                    print(f"Created tier: {tier.name} (Level {tier.level})")
                else:
                    print(f"Tier already exists: {existing_tier.name} (Level {existing_tier.level})")
            
            # Create products
            for product_data in template["products"]:
                existing_product = (
                    self.db.query(SectorProduct)
                    .filter(
                        SectorProduct.sector_id == product_data["sector_id"],
                        SectorProduct.name == product_data["name"]
                    )
                    .first()
                )
                
                if not existing_product:
                    product = SectorProduct(**product_data)
                    self.db.add(product)
                    print(f"Created product: {product.name}")
                else:
                    print(f"Product already exists: {existing_product.name}")
            
            self.db.commit()
            return True
            
        except IntegrityError as e:
            self.db.rollback()
            print(f"Error seeding sector template: {e}")
            return False
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error seeding sector template: {e}")
            return False
    
    async def seed_all_templates(self) -> Dict[str, bool]:
        """Seed all sector templates"""
        results = {}
        
        templates = {
            "palm_oil": PALM_OIL_SECTOR_TEMPLATE,
            "apparel": APPAREL_SECTOR_TEMPLATE
        }
        
        for template_name, template_data in templates.items():
            print(f"\nSeeding {template_name} sector template...")
            results[template_name] = await self.seed_sector_template(template_data)
        
        return results
    
    async def migrate_existing_users_to_sectors(self) -> Dict[str, int]:
        """Migrate existing users to the sector system"""
        # Default role to sector/tier mapping
        role_mapping = {
            "buyer": {"sector_id": "palm_oil", "tier_level": 1},
            "supplier": {"sector_id": "palm_oil", "tier_level": 4},
            "seller": {"sector_id": "palm_oil", "tier_level": 2},
            # Admin users keep their role but don't get sector assignment
        }
        
        migration_stats = {
            "users_migrated": 0,
            "companies_migrated": 0,
            "users_skipped": 0,
            "companies_skipped": 0
        }
        
        try:
            # Migrate users
            users = self.db.query(User).filter(User.sector_id.is_(None)).all()
            
            for user in users:
                if user.role in role_mapping:
                    mapping = role_mapping[user.role]
                    user.sector_id = mapping["sector_id"]
                    user.tier_level = mapping["tier_level"]
                    migration_stats["users_migrated"] += 1
                    print(f"Migrated user {user.email} to {mapping['sector_id']} tier {mapping['tier_level']}")
                else:
                    migration_stats["users_skipped"] += 1
                    print(f"Skipped user {user.email} with role {user.role}")
            
            # Migrate companies based on their users
            companies = self.db.query(Company).filter(Company.sector_id.is_(None)).all()
            
            for company in companies:
                # Find a user from this company to determine sector
                company_user = self.db.query(User).filter(
                    User.company_id == company.id,
                    User.sector_id.isnot(None)
                ).first()
                
                if company_user:
                    company.sector_id = company_user.sector_id
                    company.tier_level = company_user.tier_level
                    migration_stats["companies_migrated"] += 1
                    print(f"Migrated company {company.name} to {company.sector_id} tier {company.tier_level}")
                else:
                    migration_stats["companies_skipped"] += 1
                    print(f"Skipped company {company.name} - no sector users found")
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            print(f"Error during migration: {e}")
            raise
        
        return migration_stats
    
    async def create_electronics_sector_template(self) -> Dict[str, Any]:
        """Create electronics sector template for future use"""
        return {
            "sector": {
                "id": "electronics",
                "name": "Electronics & Minerals",
                "description": "Supply chain transparency for electronics and mineral extraction",
                "is_active": True,
                "regulatory_focus": ["Conflict Minerals", "Dodd-Frank", "UFLPA", "RMI"]
            },
            "tiers": [
                {
                    "sector_id": "electronics",
                    "level": 1,
                    "name": "OEM",
                    "description": "Original Equipment Manufacturers (Apple, Samsung)",
                    "is_originator": False,
                    "required_data_fields": ["conflict_minerals_policy", "supplier_standards"],
                    "permissions": ["create_po", "view_transparency", "audit_suppliers"]
                },
                {
                    "sector_id": "electronics",
                    "level": 2,
                    "name": "Assembly Supplier",
                    "description": "Electronics assembly (Foxconn)",
                    "is_originator": False,
                    "required_data_fields": ["assembly_certifications", "worker_conditions"],
                    "permissions": ["confirm_po", "link_component_inputs", "provide_assembly_data"]
                },
                {
                    "sector_id": "electronics",
                    "level": 3,
                    "name": "Component Supplier",
                    "description": "Makes microchips, batteries",
                    "is_originator": False,
                    "required_data_fields": ["component_specifications", "material_composition"],
                    "permissions": ["confirm_po", "link_material_inputs"]
                },
                {
                    "sector_id": "electronics",
                    "level": 4,
                    "name": "Raw Material Processor",
                    "description": "Processes cobalt, lithium",
                    "is_originator": False,
                    "required_data_fields": ["processing_certifications", "material_purity"],
                    "permissions": ["confirm_po", "link_mineral_inputs"]
                },
                {
                    "sector_id": "electronics",
                    "level": 5,
                    "name": "Miner/Smelter",
                    "description": "Extracts and processes minerals (originator)",
                    "is_originator": True,
                    "required_data_fields": ["mine_location", "conflict_free_certification", "extraction_method"],
                    "permissions": ["confirm_po", "add_origin_data"]
                }
            ],
            "products": [
                {
                    "sector_id": "electronics",
                    "name": "Cobalt Ore",
                    "category": "Raw Material",
                    "hs_code": "2605.00",
                    "applicable_tiers": [5, 4]
                },
                {
                    "sector_id": "electronics",
                    "name": "Lithium Carbonate",
                    "category": "Processed Material",
                    "hs_code": "2836.91",
                    "applicable_tiers": [4, 3]
                },
                {
                    "sector_id": "electronics",
                    "name": "Battery Cells",
                    "category": "Component",
                    "hs_code": "8507.60",
                    "applicable_tiers": [3, 2]
                },
                {
                    "sector_id": "electronics",
                    "name": "Electronic Devices",
                    "category": "Final Product",
                    "hs_code": "8517.12",
                    "applicable_tiers": [2, 1]
                }
            ]
        }


async def seed_sectors(db: Session) -> Dict[str, Any]:
    """Main function to seed all sector data"""
    seeder = SectorSeeder(db)
    
    print("Starting sector seeding process...")
    
    # Seed sector templates
    template_results = await seeder.seed_all_templates()
    
    # Migrate existing users
    print("\nMigrating existing users to sector system...")
    migration_stats = await seeder.migrate_existing_users_to_sectors()
    
    return {
        "template_results": template_results,
        "migration_stats": migration_stats
    }
