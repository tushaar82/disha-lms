#!/usr/bin/env python
"""
Quick setup script to create test data for Disha LMS.
Creates a center and links the center head user to it.
"""

import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.centers.models import Center, CenterHead

print("=" * 60)
print("SETTING UP TEST DATA")
print("=" * 60)

# Get a superuser for created_by field
superuser = User.objects.filter(is_superuser=True).first()
if not superuser:
    print("\n❌ No superuser found! Please create a superuser first:")
    print("   python manage.py createsuperuser")
    exit(1)

# Step 1: Create a center if none exists
centers = Center.objects.all()
if centers.count() == 0:
    print("\n1. Creating test center...")
    center = Center.objects.create(
        name="Mumbai Learning Center",
        code="MUM001",
        address="123 Main Street, Andheri",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        phone="+91-22-12345678",
        email="mumbai@dishalms.com",
        is_active=True,
        created_by=superuser,
        modified_by=superuser
    )
    print(f"   ✅ Created center: {center.name}")
else:
    center = centers.first()
    print(f"\n1. Using existing center: {center.name}")

# Step 2: Find center head user
center_head_users = User.objects.filter(role='center_head')
if center_head_users.count() == 0:
    print("\n2. ❌ No center head users found!")
    print("   Please create a user with role='center_head' in admin first")
    exit(1)

user = center_head_users.first()
print(f"\n2. Found center head user: {user.email}")

# Step 3: Create CenterHead profile
try:
    profile = user.center_head_profile
    print(f"\n3. ✅ Profile already exists: {profile.center.name}")
except:
    print("\n3. Creating CenterHead profile...")
    profile = CenterHead.objects.create(
        user=user,
        center=center,
        employee_id="CH001",
        joining_date=date.today(),
        is_active=True,
        created_by=superuser,
        modified_by=superuser
    )
    print(f"   ✅ Created profile linking {user.email} to {center.name}")

print("\n" + "=" * 60)
print("✅ SETUP COMPLETE!")
print("=" * 60)
print(f"\nYou can now login as: {user.email}")
print(f"And access: http://127.0.0.1:8000/students/")
print("\n" + "=" * 60)
