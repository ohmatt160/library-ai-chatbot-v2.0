"""
Database migration script to create borrow-related tables
Run this script to create the new tables in the database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.model import BorrowRequest, BorrowHistory, Notification

def create_borrow_tables():
    """Create the new borrow-related tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating borrow-related tables...")
        
        # Create tables
        db.create_all()
        
        print("[ok] Tables created successfully!")
        print("\nCreated tables:")
        print("  - borrow_requests")
        print("  - borrow_history")
        print("  - notifications")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("\nAll tables in database:")
        for table in tables:
            print(f"  - {table}")

if __name__ == '__main__':
    create_borrow_tables()
