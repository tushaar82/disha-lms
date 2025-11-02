#!/usr/bin/env python
"""Debug script to check CenterHead profile setup."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.centers.models import CenterHead

print("=" * 60)
print("DEBUGGING CENTER HEAD PROFILES")
print("=" * 60)

# Check center head users
users = User.objects.filter(role='center_head')
print(f"\n1. Center Head Users: {users.count()}")
for u in users:
    print(f"   - Email: {u.email}")
    print(f"     Role: {u.role}")
    print(f"     is_center_head property: {u.is_center_head}")
    try:
        profile = u.center_head_profile
        print(f"     ✅ Has profile: {profile.center.name}")
    except Exception as e:
        print(f"     ❌ No profile: {e}")

# Check CenterHead profiles
profiles = CenterHead.objects.all()
print(f"\n2. CenterHead Profiles: {profiles.count()}")
for p in profiles:
    print(f"   - User: {p.user.email}")
    print(f"     Center: {p.center.name}")
    print(f"     Active: {p.is_active}")
    print(f"     Employee ID: {p.employee_id}")

# Check all users (for debugging)
all_users = User.objects.all()
print(f"\n3. All Users: {all_users.count()}")
for u in all_users:
    print(f"   - {u.email}: role={u.role}, is_center_head={u.is_center_head}")

print("\n" + "=" * 60)
print("DIAGNOSIS:")
print("=" * 60)

if users.count() == 0:
    print("❌ No users with role='center_head' found")
    print("   FIX: Create a user with role='center_head' in admin")
elif profiles.count() == 0:
    print("❌ No CenterHead profiles found")
    print("   FIX: Create a CenterHead profile in admin linking user to center")
elif users.count() != profiles.count():
    print(f"⚠️  Mismatch: {users.count()} center_head users but {profiles.count()} profiles")
    print("   FIX: Ensure each center_head user has a CenterHead profile")
else:
    print("✅ Setup looks correct!")
    print("   If you still see errors, check:")
    print("   1. Are you logged in as the correct user?")
    print("   2. Is the profile active (is_active=True)?")
    print("   3. Does the profile have a valid center?")

print("=" * 60)
