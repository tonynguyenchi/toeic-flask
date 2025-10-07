#!/usr/bin/env python3
"""
Migration script to add RBAC fields to existing User table
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db

def migrate_user_table():
    """Add RBAC fields to existing User table"""
    print("🔄 Migrating User table to add RBAC fields...")
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            new_columns = [
                ('first_name', 'VARCHAR(50)'),
                ('last_name', 'VARCHAR(50)'),
                ('phone', 'VARCHAR(20)'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('last_login', 'DATETIME'),
                ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                ('last_failed_login', 'DATETIME'),
                ('password_reset_token', 'VARCHAR(100)'),
                ('password_reset_expires', 'DATETIME')
            ]
            
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    print(f"   Adding column: {column_name}")
                    with db.engine.connect() as conn:
                        conn.execute(db.text(f'ALTER TABLE user ADD COLUMN {column_name} {column_type}'))
                        conn.commit()
                else:
                    print(f"   Column {column_name} already exists")
            
            # Set default values for existing users
            with db.engine.connect() as conn:
                conn.execute(db.text('UPDATE user SET is_active = 1 WHERE is_active IS NULL'))
                conn.execute(db.text('UPDATE user SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL'))
                conn.commit()
            
            print("✅ User table migration completed")
            return True
            
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")
            return False

if __name__ == "__main__":
    success = migrate_user_table()
    sys.exit(0 if success else 1)
