#!/usr/bin/env python3
"""
Migration script to add test_set field to ExamAttempt table
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import ExamAttempt

def migrate_exam_attempt_table():
    """Add test_set field to existing ExamAttempt table"""
    print("🔄 Migrating ExamAttempt table to add test_set field...")
    
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('exam_attempt')]
            
            if 'test_set' not in columns:
                print("   Adding column: test_set")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE exam_attempt ADD COLUMN test_set VARCHAR(50)'))
                    conn.commit()
            else:
                print("   Column test_set already exists")
            
            # Set default values for existing exam attempts
            with db.engine.connect() as conn:
                conn.execute(db.text("UPDATE exam_attempt SET test_set = 'Test 1' WHERE test_set IS NULL"))
                conn.commit()
            
            print("✅ ExamAttempt table migration completed")
            return True
            
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")
            return False

if __name__ == "__main__":
    success = migrate_exam_attempt_table()
    sys.exit(0 if success else 1)
