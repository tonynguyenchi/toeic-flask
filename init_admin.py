#!/usr/bin/env python3
"""
Initialize TOEIC Coach Admin System
This script sets up the RBAC system, organization hierarchy, and admin user.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import (
    init_rbac_data, init_org_data, init_admin_user,
    User, Role, UserRole, Year, Program, Group
)

def main():
    """Initialize the admin system"""
    print("🚀 Initializing TOEIC Coach Admin System...")
    
    with app.app_context():
        try:
            # Create all tables
            print("📊 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Initialize RBAC data
            print("👥 Setting up RBAC roles and permissions...")
            init_rbac_data()
            print("✅ RBAC system initialized")
            
            # Initialize organization data
            print("🏫 Setting up organization hierarchy...")
            init_org_data()
            print("✅ Organization structure created")
            
            # Create admin user
            print("👤 Creating admin user...")
            init_admin_user()
            print("✅ Admin user created")
            
            # Display summary
            print("\n" + "="*50)
            print("🎉 ADMIN SYSTEM INITIALIZATION COMPLETE!")
            print("="*50)
            
            # Show created roles
            roles = Role.query.all()
            print(f"\n📋 Created {len(roles)} roles:")
            for role in roles:
                print(f"   • {role.display_name} ({role.name})")
            
            # Show organization structure
            years = Year.query.all()
            print(f"\n🏫 Created {len(years)} academic years:")
            for year in years:
                programs = Program.query.filter_by(year_id=year.id).all()
                print(f"   • {year.name} ({len(programs)} programs)")
                for program in programs:
                    groups = Group.query.filter_by(program_id=program.id).all()
                    print(f"     - {program.name} ({len(groups)} groups)")
            
            # Show admin credentials
            admin_user = User.query.filter_by(email='admin@toeic.com').first()
            if admin_user:
                print(f"\n🔑 Admin Login Credentials:")
                print(f"   Username: {admin_user.username}")
                print(f"   Email: {admin_user.email}")
                print(f"   Password: admin123")
                print(f"   Role: Super Administrator")
            
            print(f"\n🌐 Access the admin panel at: http://localhost:5000/admin")
            print("="*50)
            
        except Exception as e:
            print(f"❌ Error during initialization: {str(e)}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
