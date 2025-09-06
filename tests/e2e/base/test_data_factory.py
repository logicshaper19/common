"""
Test data factory for creating and managing test data
"""
from typing import Dict, Any, List, Tuple
from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from tests.e2e.base.personas import PersonaDefinition


class TestDataFactory:
    """Factory for creating and managing test data."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._created_resources = []
    
    def create_persona_user(self, persona_def: PersonaDefinition) -> Tuple[Company, User]:
        """Create company and user for a persona."""
        company = Company(
            id=uuid4(),
            name=persona_def.company_name,
            company_type=persona_def.company_type,
            email=persona_def.email,
            description=persona_def.description
        )
        
        user = User(
            id=uuid4(),
            email=persona_def.email,
            hashed_password="$2b$12$test_password_hash",
            full_name=persona_def.name,
            role=persona_def.role,
            company_id=company.id,
            is_active=True
        )
        
        self.db_session.add(company)
        self.db_session.add(user)
        self.db_session.commit()
        
        self.db_session.refresh(company)
        self.db_session.refresh(user)
        
        self._created_resources.extend([
            ("user", user.id),
            ("company", company.id)
        ])
        
        return company, user
    
    def create_test_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a test product."""
        product_data = product_data.copy()
        if 'id' not in product_data:
            product_data['id'] = uuid4()
            
        product = Product(**product_data)
        
        self.db_session.add(product)
        self.db_session.commit()
        self.db_session.refresh(product)
        
        self._created_resources.append(("product", product.id))
        return product
    
    def create_purchase_order(self, po_data: Dict[str, Any]) -> PurchaseOrder:
        """Create a test purchase order."""
        po_data = po_data.copy()
        if 'id' not in po_data:
            po_data['id'] = uuid4()
            
        po = PurchaseOrder(**po_data)
        
        self.db_session.add(po)
        self.db_session.commit()
        self.db_session.refresh(po)
        
        self._created_resources.append(("purchase_order", po.id))
        return po
    
    def get_standard_products(self) -> List[Product]:
        """Create standard test products for supply chain."""
        products_data = [
            {
                "common_product_id": "FFB-TEST-001",
                "name": "Fresh Fruit Bunches (FFB)",
                "description": "Fresh palm fruit bunches for testing",
                "category": "raw_material",
                "can_have_composition": False,
                "default_unit": "KGM",
                "hs_code": "1207.10.00"
            },
            {
                "common_product_id": "CPO-TEST-001", 
                "name": "Crude Palm Oil (CPO)",
                "description": "Unrefined palm oil for testing",
                "category": "processed",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "1511.10.00"
            },
            {
                "common_product_id": "RBD-TEST-001",
                "name": "Refined Palm Oil",
                "description": "Refined, bleached, deodorized palm oil for testing",
                "category": "finished_good",
                "can_have_composition": True,
                "default_unit": "KGM",
                "hs_code": "1511.90.00"
            }
        ]
        
        products = []
        for product_data in products_data:
            product = self.create_test_product(product_data)
            products.append(product)
            
        return products
    
    def cleanup_all(self):
        """Clean up all created resources."""
        for resource_type, resource_id in reversed(self._created_resources):
            self.cleanup_resource(resource_type, resource_id)
        self._created_resources.clear()
    
    def cleanup_resource(self, resource_type: str, resource_id: UUID):
        """Clean up a specific resource."""
        try:
            if resource_type == "purchase_order":
                po = self.db_session.query(PurchaseOrder).get(resource_id)
                if po:
                    self.db_session.delete(po)
            elif resource_type == "user":
                user = self.db_session.query(User).get(resource_id)
                if user:
                    self.db_session.delete(user)
            elif resource_type == "company":
                company = self.db_session.query(Company).get(resource_id)
                if company:
                    self.db_session.delete(company)
            elif resource_type == "product":
                product = self.db_session.query(Product).get(resource_id)
                if product:
                    self.db_session.delete(product)
            
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            # Log but don't fail cleanup
            pass