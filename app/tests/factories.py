"""
Test data factories for consistent test data generation.

This module provides factory functions for creating test data
with realistic values and proper relationships.
"""
import factory
from factory import fuzzy
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any, List, Optional

from app.models.company import Company
from app.models.user import User
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.transformation import TransformationEvent
from app.schemas.company import CompanyCreate
from app.schemas.user import UserCreate
from app.schemas.product import ProductCreate
from app.schemas.purchase_order import PurchaseOrderCreate


class CompanyFactory(factory.Factory):
    """Factory for creating test companies."""
    
    class Meta:
        model = CompanyCreate
    
    name = factory.Sequence(lambda n: f"Test Company {n}")
    email = factory.LazyAttribute(lambda obj: f"admin{obj.name.lower().replace(' ', '')}@test.com")
    password = "TestPassword123!"
    company_type = factory.Iterator([
        "plantation_grower", "mill_processor", "refinery_crusher", 
        "manufacturer", "trader", "brand"
    ])
    full_name = factory.LazyAttribute(lambda obj: f"{obj.name} Admin")
    role = "admin"
    company_email = factory.LazyAttribute(lambda obj: f"info@{obj.name.lower().replace(' ', '')}.com")
    website = factory.LazyAttribute(lambda obj: f"https://{obj.name.lower().replace(' ', '')}.com")
    phone = factory.LazyAttribute(lambda n: f"+1-555-{fuzzy.FuzzyText(length=3, chars='0123456789').fuzz()}-{fuzzy.FuzzyText(length=4, chars='0123456789').fuzz()}")
    address = factory.Faker('street_address')
    city = factory.Faker('city')
    state_province = factory.Faker('state')
    country = factory.Faker('country_code')
    postal_code = factory.Faker('postcode')


class UserFactory(factory.Factory):
    """Factory for creating test users."""
    
    class Meta:
        model = UserCreate
    
    email = factory.LazyAttribute(lambda obj: f"user{obj.full_name.lower().replace(' ', '')}@test.com")
    password = "TestPassword123!"
    full_name = factory.Faker('name')
    role = factory.Iterator(["admin", "user", "viewer"])
    company_id = factory.LazyFunction(lambda: str(uuid4()))


class ProductFactory(factory.Factory):
    """Factory for creating test products."""
    
    class Meta:
        model = ProductCreate
    
    name = factory.Iterator([
        "Fresh Fruit Bunches", "Crude Palm Oil", "Refined Palm Oil",
        "Palm Kernel Oil", "Beauty Products", "Cooking Oil"
    ])
    description = factory.LazyAttribute(lambda obj: f"High-quality {obj.name.lower()}")
    category = factory.Iterator(["raw_material", "semi_finished", "finished_good"])
    unit = factory.Iterator(["kg", "tonnes", "liters", "pieces"])
    common_product_id = factory.LazyAttribute(lambda obj: f"TEST-{obj.category.upper()}-{uuid4().hex[:8]}")
    material_breakdown = None
    price_per_unit = factory.LazyFunction(lambda: Decimal(str(round(fuzzy.FuzzyFloat(0.5, 10.0).fuzz(), 2))))
    supplier_id = factory.LazyFunction(lambda: str(uuid4()))


class PurchaseOrderFactory(factory.Factory):
    """Factory for creating test purchase orders."""
    
    class Meta:
        model = PurchaseOrderCreate
    
    seller_company_id = factory.LazyFunction(lambda: str(uuid4()))
    buyer_company_id = factory.LazyFunction(lambda: str(uuid4()))
    product_id = factory.LazyFunction(lambda: str(uuid4()))
    quantity = factory.LazyFunction(lambda: Decimal(str(round(fuzzy.FuzzyFloat(100, 10000).fuzz(), 2))))
    unit = factory.Iterator(["kg", "tonnes", "liters", "pieces"])
    price_per_unit = factory.LazyFunction(lambda: Decimal(str(round(fuzzy.FuzzyFloat(0.5, 50.0).fuzz(), 2))))
    delivery_date = factory.LazyFunction(lambda: (date.today() + timedelta(days=fuzzy.FuzzyInteger(1, 90).fuzz())).isoformat())
    delivery_location = factory.Faker('city')
    status = factory.Iterator(["pending", "confirmed", "shipped", "delivered", "cancelled"])
    notes = factory.Faker('text', max_nb_chars=200)


class BatchFactory(factory.Factory):
    """Factory for creating test batches."""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    batch_id = factory.LazyFunction(lambda: f"BATCH-{uuid4().hex[:8]}")
    product_id = factory.LazyFunction(lambda: str(uuid4()))
    quantity = factory.LazyFunction(lambda: Decimal(str(round(fuzzy.FuzzyFloat(100, 10000).fuzz(), 2))))
    unit = factory.Iterator(["kg", "tonnes", "liters", "pieces"])
    quality_grade = factory.Iterator(["A1", "A2", "B1", "B2", "C1", "C2"])
    certification_status = factory.Iterator(["certified", "pending", "expired"])
    created_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    updated_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())


class TransformationEventFactory(factory.Factory):
    """Factory for creating test transformation events."""
    
    class Meta:
        model = dict
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    transformation_type = factory.Iterator(["harvest", "milling", "refining", "manufacturing"])
    input_batch_id = factory.LazyFunction(lambda: str(uuid4()))
    company_id = factory.LazyFunction(lambda: str(uuid4()))
    facility_id = factory.LazyFunction(lambda: f"FACILITY-{uuid4().hex[:8]}")
    process_name = factory.Iterator([
        "Mechanical Extraction", "Physical Refining", "Chemical Refining",
        "Fractionation", "Deodorization", "Packaging"
    ])
    process_description = factory.Faker('text', max_nb_chars=500)
    start_time = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    end_time = factory.LazyFunction(lambda: (datetime.utcnow() + timedelta(hours=fuzzy.FuzzyInteger(1, 24).fuzz())).isoformat())
    status = factory.Iterator(["pending", "in_progress", "completed", "failed"])
    created_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    updated_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())


class TestDataFactory:
    """Main factory class for creating comprehensive test data."""
    
    @staticmethod
    def create_supply_chain_companies() -> List[Dict[str, Any]]:
        """Create a complete supply chain with all company types."""
        companies = []
        
        # Plantation
        plantation = CompanyFactory.build(
            name="Green Acres Plantation",
            company_type="plantation_grower",
            email="admin@greenacres.com"
        )
        companies.append(plantation)
        
        # Mill
        mill = CompanyFactory.build(
            name="Palm Oil Mill Ltd",
            company_type="mill_processor",
            email="admin@palmmill.com"
        )
        companies.append(mill)
        
        # Refinery
        refinery = CompanyFactory.build(
            name="Premium Refinery Co",
            company_type="refinery_crusher",
            email="admin@premiumrefinery.com"
        )
        companies.append(refinery)
        
        # Manufacturer
        manufacturer = CompanyFactory.build(
            name="Beauty Products Inc",
            company_type="manufacturer",
            email="admin@beautyproducts.com"
        )
        companies.append(manufacturer)
        
        # Trader
        trader = CompanyFactory.build(
            name="Global Trading Co",
            company_type="trader",
            email="admin@globaltrading.com"
        )
        companies.append(trader)
        
        # Brand
        brand = CompanyFactory.build(
            name="Sustainable Beauty Co",
            company_type="brand",
            email="admin@sustainablebeauty.com"
        )
        companies.append(brand)
        
        return companies
    
    @staticmethod
    def create_product_catalog() -> List[Dict[str, Any]]:
        """Create a comprehensive product catalog."""
        products = []
        
        # Raw materials
        raw_materials = [
            ("Fresh Fruit Bunches", "raw_material", "kg"),
            ("Palm Kernels", "raw_material", "kg"),
            ("Palm Kernel Shells", "raw_material", "kg")
        ]
        
        for name, category, unit in raw_materials:
            product = ProductFactory.build(
                name=name,
                category=category,
                unit=unit,
                common_product_id=f"RAW-{name.upper().replace(' ', '_')}-{uuid4().hex[:8]}"
            )
            products.append(product)
        
        # Semi-finished products
        semi_finished = [
            ("Crude Palm Oil", "semi_finished", "kg"),
            ("Palm Kernel Oil", "semi_finished", "kg"),
            ("Palm Stearin", "semi_finished", "kg")
        ]
        
        for name, category, unit in semi_finished:
            product = ProductFactory.build(
                name=name,
                category=category,
                unit=unit,
                common_product_id=f"SEMI-{name.upper().replace(' ', '_')}-{uuid4().hex[:8]}"
            )
            products.append(product)
        
        # Finished products
        finished_products = [
            ("Refined Palm Oil", "finished_good", "kg"),
            ("Cooking Oil", "finished_good", "liters"),
            ("Beauty Products", "finished_good", "pieces")
        ]
        
        for name, category, unit in finished_products:
            product = ProductFactory.build(
                name=name,
                category=category,
                unit=unit,
                common_product_id=f"FINISHED-{name.upper().replace(' ', '_')}-{uuid4().hex[:8]}"
            )
            products.append(product)
        
        return products
    
    @staticmethod
    def create_purchase_order_chain(companies: List[Dict], products: List[Dict]) -> List[Dict[str, Any]]:
        """Create a chain of purchase orders through the supply chain."""
        purchase_orders = []
        
        # Plantation to Mill
        po1 = PurchaseOrderFactory.build(
            seller_company_id=companies[0]["company_id"] if "company_id" in companies[0] else str(uuid4()),
            buyer_company_id=companies[1]["company_id"] if "company_id" in companies[1] else str(uuid4()),
            product_id=products[0]["id"] if "id" in products[0] else str(uuid4()),
            quantity=Decimal("1000.0"),
            unit="kg",
            price_per_unit=Decimal("0.5"),
            status="confirmed"
        )
        purchase_orders.append(po1)
        
        # Mill to Refinery
        po2 = PurchaseOrderFactory.build(
            seller_company_id=companies[1]["company_id"] if "company_id" in companies[1] else str(uuid4()),
            buyer_company_id=companies[2]["company_id"] if "company_id" in companies[2] else str(uuid4()),
            product_id=products[3]["id"] if "id" in products[3] else str(uuid4()),
            quantity=Decimal("200.0"),
            unit="kg",
            price_per_unit=Decimal("2.5"),
            status="confirmed"
        )
        purchase_orders.append(po2)
        
        # Refinery to Manufacturer
        po3 = PurchaseOrderFactory.build(
            seller_company_id=companies[2]["company_id"] if "company_id" in companies[2] else str(uuid4()),
            buyer_company_id=companies[3]["company_id"] if "company_id" in companies[3] else str(uuid4()),
            product_id=products[6]["id"] if "id" in products[6] else str(uuid4()),
            quantity=Decimal("100.0"),
            unit="kg",
            price_per_unit=Decimal("5.0"),
            status="confirmed"
        )
        purchase_orders.append(po3)
        
        return purchase_orders
    
    @staticmethod
    def create_transformation_events(companies: List[Dict], batches: List[Dict]) -> List[Dict[str, Any]]:
        """Create transformation events for the supply chain."""
        events = []
        
        # Harvest transformation
        harvest_event = TransformationEventFactory.build(
            transformation_type="harvest",
            company_id=companies[0]["company_id"] if "company_id" in companies[0] else str(uuid4()),
            input_batch_id=batches[0]["id"] if batches else str(uuid4()),
            process_name="Fresh Fruit Harvest",
            status="completed"
        )
        events.append(harvest_event)
        
        # Milling transformation
        milling_event = TransformationEventFactory.build(
            transformation_type="milling",
            company_id=companies[1]["company_id"] if "company_id" in companies[1] else str(uuid4()),
            input_batch_id=batches[1]["id"] if len(batches) > 1 else str(uuid4()),
            process_name="Mechanical Extraction",
            status="completed"
        )
        events.append(milling_event)
        
        # Refining transformation
        refining_event = TransformationEventFactory.build(
            transformation_type="refining",
            company_id=companies[2]["company_id"] if "company_id" in companies[2] else str(uuid4()),
            input_batch_id=batches[2]["id"] if len(batches) > 2 else str(uuid4()),
            process_name="Physical Refining",
            status="completed"
        )
        events.append(refining_event)
        
        # Manufacturing transformation
        manufacturing_event = TransformationEventFactory.build(
            transformation_type="manufacturing",
            company_id=companies[3]["company_id"] if "company_id" in companies[3] else str(uuid4()),
            input_batch_id=batches[3]["id"] if len(batches) > 3 else str(uuid4()),
            process_name="Product Formulation",
            status="completed"
        )
        events.append(manufacturing_event)
        
        return events


# Convenience functions for common test data creation
def create_test_company(**kwargs) -> Dict[str, Any]:
    """Create a single test company with optional overrides."""
    return CompanyFactory.build(**kwargs)


def create_test_user(**kwargs) -> Dict[str, Any]:
    """Create a single test user with optional overrides."""
    return UserFactory.build(**kwargs)


def create_test_product(**kwargs) -> Dict[str, Any]:
    """Create a single test product with optional overrides."""
    return ProductFactory.build(**kwargs)


def create_test_purchase_order(**kwargs) -> Dict[str, Any]:
    """Create a single test purchase order with optional overrides."""
    return PurchaseOrderFactory.build(**kwargs)


def create_test_batch(**kwargs) -> Dict[str, Any]:
    """Create a single test batch with optional overrides."""
    return BatchFactory.build(**kwargs)


def create_test_transformation_event(**kwargs) -> Dict[str, Any]:
    """Create a single test transformation event with optional overrides."""
    return TransformationEventFactory.build(**kwargs)


def create_complete_test_scenario() -> Dict[str, Any]:
    """Create a complete test scenario with all entities."""
    companies = TestDataFactory.create_supply_chain_companies()
    products = TestDataFactory.create_product_catalog()
    purchase_orders = TestDataFactory.create_purchase_order_chain(companies, products)
    batches = [BatchFactory.build() for _ in range(4)]
    transformation_events = TestDataFactory.create_transformation_events(companies, batches)
    
    return {
        "companies": companies,
        "products": products,
        "purchase_orders": purchase_orders,
        "batches": batches,
        "transformation_events": transformation_events
    }
