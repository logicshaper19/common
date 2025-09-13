"""
Service for seeding initial data into the database.
"""
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.product import Product
from app.core.logging import get_logger

logger = get_logger(__name__)


class SeedDataService:
    """Service for seeding initial data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def seed_palm_oil_products(self) -> None:
        """
        Seed palm oil products with proper HS codes and composition rules.
        """
        palm_oil_products = [
            # Raw Materials
            {
                "common_product_id": "FFB-001",
                "name": "Fresh Fruit Bunches (FFB)",
                "description": "Fresh palm fruit bunches harvested from oil palm trees",
                "category": "raw_material",
                "can_have_composition": False,
                "material_breakdown": None,
                "default_unit": "KGM",
                "hs_code": "1207.10.00",
                "origin_data_requirements": {
                    "required_fields": ["plantation_coordinates", "harvest_date", "plantation_certification"],
                    "optional_fields": ["variety", "age_of_trees", "yield_per_hectare"]
                }
            },
            {
                "common_product_id": "PKS-001",
                "name": "Palm Kernel Shells",
                "description": "Shells from palm kernels, used as biomass fuel",
                "category": "raw_material",
                "can_have_composition": False,
                "material_breakdown": None,
                "default_unit": "KGM",
                "hs_code": "1207.99.00",
                "origin_data_requirements": {
                    "required_fields": ["mill_location", "processing_date"],
                    "optional_fields": ["moisture_content", "calorific_value"]
                }
            },
            
            # Processed Products
            {
                "common_product_id": "CPO-001",
                "name": "Crude Palm Oil (CPO)",
                "description": "Unrefined palm oil extracted from fresh fruit bunches",
                "category": "processed",
                "can_have_composition": True,
                "material_breakdown": {
                    "palm_oil": 100.0
                },
                "default_unit": "KGM",
                "hs_code": "1511.10.00",
                "origin_data_requirements": {
                    "required_fields": ["mill_location", "extraction_date", "ffb_source"],
                    "optional_fields": ["free_fatty_acid", "moisture_content", "impurities"]
                }
            },
            {
                "common_product_id": "PKO-001",
                "name": "Palm Kernel Oil (PKO)",
                "description": "Oil extracted from palm kernels",
                "category": "processed",
                "can_have_composition": True,
                "material_breakdown": {
                    "palm_kernel_oil": 100.0
                },
                "default_unit": "KGM",
                "hs_code": "1513.21.00",
                "origin_data_requirements": {
                    "required_fields": ["mill_location", "extraction_date", "kernel_source"],
                    "optional_fields": ["free_fatty_acid", "moisture_content", "iodine_value"]
                }
            },
            {
                "common_product_id": "RBD-PO-001",
                "name": "Refined, Bleached, Deodorized Palm Oil (RBD PO)",
                "description": "Refined palm oil suitable for food applications",
                "category": "processed",
                "can_have_composition": True,
                "material_breakdown": {
                    "refined_palm_oil": 100.0
                },
                "default_unit": "KGM",
                "hs_code": "1511.90.00",
                "origin_data_requirements": {
                    "required_fields": ["refinery_location", "refining_date", "cpo_source"],
                    "optional_fields": ["peroxide_value", "color", "smoke_point"]
                }
            },
            {
                "common_product_id": "PFAD-001",
                "name": "Palm Fatty Acid Distillate (PFAD)",
                "description": "By-product from palm oil refining process",
                "category": "processed",
                "can_have_composition": True,
                "material_breakdown": {
                    "fatty_acids": 85.0,
                    "glycerides": 15.0
                },
                "default_unit": "KGM",
                "hs_code": "1511.90.00",
                "origin_data_requirements": {
                    "required_fields": ["refinery_location", "production_date"],
                    "optional_fields": ["acid_value", "saponification_value"]
                }
            },
            
            # Finished Goods / Blends
            {
                "common_product_id": "BLEND-001",
                "name": "Palm Oil Blend (80/20)",
                "description": "Blend of 80% palm oil and 20% palm kernel oil",
                "category": "finished_good",
                "can_have_composition": True,
                "material_breakdown": {
                    "palm_oil": 80.0,
                    "palm_kernel_oil": 20.0
                },
                "default_unit": "KGM",
                "hs_code": "1511.90.00",
                "origin_data_requirements": {
                    "required_fields": ["blending_facility", "blend_date", "component_sources"],
                    "optional_fields": ["blend_ratio_verification", "quality_parameters"]
                }
            },
            {
                "common_product_id": "STEARIN-001",
                "name": "Palm Stearin",
                "description": "Solid fraction of palm oil after fractionation",
                "category": "finished_good",
                "can_have_composition": True,
                "material_breakdown": {
                    "palm_stearin": 100.0
                },
                "default_unit": "KGM",
                "hs_code": "1511.90.00",
                "origin_data_requirements": {
                    "required_fields": ["fractionation_facility", "production_date", "palm_oil_source"],
                    "optional_fields": ["melting_point", "iodine_value", "slip_melting_point"]
                }
            },
            {
                "common_product_id": "OLEIN-001",
                "name": "Palm Olein",
                "description": "Liquid fraction of palm oil after fractionation",
                "category": "finished_good",
                "can_have_composition": True,
                "material_breakdown": {
                    "palm_olein": 100.0
                },
                "default_unit": "KGM",
                "hs_code": "1511.90.00",
                "origin_data_requirements": {
                    "required_fields": ["fractionation_facility", "production_date", "palm_oil_source"],
                    "optional_fields": ["cloud_point", "iodine_value", "pour_point"]
                }
            }
        ]
        
        # Check if products already exist
        existing_products = self.db.query(Product).filter(
            Product.common_product_id.in_([p["common_product_id"] for p in palm_oil_products])
        ).all()
        
        existing_ids = {p.common_product_id for p in existing_products}
        
        # Only seed products that don't exist
        new_products = [p for p in palm_oil_products if p["common_product_id"] not in existing_ids]
        
        if not new_products:
            logger.info("Palm oil products already seeded")
            return
        
        try:
            for product_data in new_products:
                product = Product(
                    id=uuid4(),
                    **product_data
                )
                self.db.add(product)
            
            self.db.commit()
            
            logger.info(
                "Palm oil products seeded successfully",
                new_products_count=len(new_products),
                total_products_count=len(palm_oil_products)
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to seed palm oil products", error=str(e))
            raise
    
    def create_default_admin(self) -> None:
        """
        Create a default admin user if none exists.
        """
        from app.models.user import User
        from app.models.company import Company
        from app.core.security import hash_password
        import os
        
        # Check if any super admin user exists
        existing_super_admin = self.db.query(User).filter(User.role == "super_admin").first()
        if existing_super_admin:
            logger.info("Super admin user already exists, skipping creation")
            return
        
        # Get admin configuration from settings
        from app.core.config import settings
        admin_email = settings.admin_email
        admin_password = settings.admin_password
        admin_name = settings.admin_name
        company_name = settings.admin_company_name
        
        try:
            # Create or get admin company
            company = self.db.query(Company).filter(Company.email == admin_email).first()
            if not company:
                company = Company(
                    name=company_name,
                    company_type="brand",
                    email=admin_email
                )
                self.db.add(company)
                self.db.flush()
                logger.info("Created admin company", company_name=company_name)
            
            # Create admin user
            hashed_password = hash_password(admin_password)
            admin_user = User(
                email=admin_email,
                hashed_password=hashed_password,
                full_name=admin_name,
                role="super_admin",
                is_active=True,
                company_id=company.id
            )
            
            self.db.add(admin_user)
            self.db.commit()
            
            logger.info(
                "Default super admin user created successfully",
                email=admin_email,
                company=company_name
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create default admin user", error=str(e))
            raise

    def seed_all_data(self) -> None:
        """
        Seed all initial data.
        """
        logger.info("Starting data seeding process")
        
        self.seed_palm_oil_products()
        self.create_default_admin()
        
        logger.info("Data seeding completed successfully")
