#!/bin/bash

# Setup script for Phase 3 migrations
# Creates migrations for all Phase 3 apps in the correct order

echo "Creating Phase 3 migrations for Disha LMS..."
echo ""

# Step 1: Create centers migrations (no dependencies except accounts/core)
echo "1. Creating centers app migrations..."
python manage.py makemigrations centers

# Step 2: Create students migrations (depends on centers)
echo ""
echo "2. Creating students app migrations..."
python manage.py makemigrations students

# Step 3: Create faculty migrations (depends on accounts, centers)
echo ""
echo "3. Creating faculty app migrations..."
python manage.py makemigrations faculty

# Step 4: Create subjects migrations (depends on centers)
echo ""
echo "4. Creating subjects app migrations..."
python manage.py makemigrations subjects

# Step 5: Create attendance migrations (depends on students, faculty, subjects)
echo ""
echo "5. Creating attendance app migrations..."
python manage.py makemigrations attendance

# Step 6: Run all migrations
echo ""
echo "6. Running all migrations..."
python manage.py migrate

echo ""
echo "✅ Phase 3 migrations complete!"
echo ""
echo "Next steps:"
echo "  1. Create test data via admin panel: http://127.0.0.1:8000/admin/"
echo "  2. Test attendance marking: http://127.0.0.1:8000/attendance/today/"
echo "  3. Test API endpoints: http://127.0.0.1:8000/api/docs/"
