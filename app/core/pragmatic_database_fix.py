"""
Fix for pragmatic LangChain system to use PostgreSQL instead of MySQL.
This creates a PostgreSQL-compatible database manager for the pragmatic system.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Optional, Dict, Any

load_dotenv()

class PostgreSQLDatabaseManager:
    """PostgreSQL database manager for pragmatic LangChain system."""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_connection(self):
        """Get a database connection."""
        return self.engine.connect()
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a query and return results."""
        with self.get_connection() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result.fetchall()
    
    def get_certifications(self, company_id: str, expires_within_days: int = 30):
        """Get certifications for a company."""
        query = """
        SELECT 
            c.id,
            c.company_id,
            c.certification_type,
            c.issue_date,
            c.expiry_date,
            c.status,
            co.name as company_name,
            EXTRACT(DAYS FROM (c.expiry_date - CURRENT_DATE)) as days_until_expiry
        FROM certifications c
        JOIN companies co ON c.company_id = co.id
        WHERE c.company_id = :company_id
        AND c.expiry_date <= CURRENT_DATE + INTERVAL '%s days'
        ORDER BY c.expiry_date ASC
        """ % expires_within_days
        
        results = self.execute_query(query, {'company_id': company_id})
        
        # Convert to mock-like format for compatibility
        mock_certs = []
        for row in results:
            mock_cert = type('Cert', (), {
                'company_name': row.company_name,
                'certification_type': row.certification_type,
                'expiry_date': row.expiry_date,
                'days_until_expiry': int(row.days_until_expiry) if row.days_until_expiry else 0,
                'needs_renewal': row.days_until_expiry <= 30 if row.days_until_expiry else False
            })()
            mock_certs.append(mock_cert)
        
        metadata = {'total_count': len(mock_certs), 'expiring_soon': len([c for c in mock_certs if c.days_until_expiry <= 30])}
        return mock_certs, metadata
    
    def get_batches(self, company_id: str, product_type: str = None, status: str = None, min_quantity: float = 0):
        """Get batches for a company."""
        query = """
        SELECT 
            b.id as batch_id,
            b.quantity,
            b.status,
            b.transparency_score,
            p.name as product_name,
            co.name as company_name,
            array_agg(c.certification_type) as certifications
        FROM batches b
        JOIN products p ON b.product_id = p.id
        JOIN companies co ON b.company_id = co.id
        LEFT JOIN batch_certifications bc ON b.id = bc.batch_id
        LEFT JOIN certifications c ON bc.certification_id = c.id
        WHERE b.company_id = :company_id
        """
        
        params = {'company_id': company_id}
        
        if product_type:
            query += " AND p.name ILIKE :product_type"
            params['product_type'] = f'%{product_type}%'
        
        if status:
            query += " AND b.status = :status"
            params['status'] = status
        
        if min_quantity > 0:
            query += " AND b.quantity >= :min_quantity"
            params['min_quantity'] = min_quantity
        
        query += " GROUP BY b.id, b.quantity, b.status, b.transparency_score, p.name, co.name"
        
        results = self.execute_query(query, params)
        
        # Convert to mock-like format for compatibility
        mock_batches = []
        for row in results:
            mock_batch = type('Batch', (), {
                'batch_id': row.batch_id,
                'company_name': row.company_name,
                'product_name': row.product_name,
                'quantity': float(row.quantity) if row.quantity else 0.0,
                'transparency_score': float(row.transparency_score) if row.transparency_score else 0.0,
                'certifications': [cert for cert in row.certifications if cert] if row.certifications else []
            })()
            mock_batches.append(mock_batch)
        
        metadata = {'total_count': len(mock_batches), 'total_quantity': sum(b.quantity for b in mock_batches)}
        return mock_batches, metadata

def get_postgresql_database_manager():
    """Get a PostgreSQL database manager instance."""
    return PostgreSQLDatabaseManager()
